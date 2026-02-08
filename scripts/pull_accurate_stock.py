#!/usr/bin/env python3
"""
Pull current inventory/stock data from Accurate Online API -> PostgreSQL.

Ported from Supabase version to psycopg2 for self-hosted PostgreSQL (openclaw_ops).
Supports 4 entities: DDD, LJBB, MBB, UBB.

ALL API OPERATIONS ARE READ-ONLY (GET requests only).
Database writes: DELETE today's snapshot + INSERT new snapshot per entity.

Usage:
    python pull_accurate_stock.py ddd              # DDD inventory
    python pull_accurate_stock.py ljbb             # LJBB inventory
    python pull_accurate_stock.py mbb              # MBB inventory
    python pull_accurate_stock.py ubb              # UBB inventory
    python pull_accurate_stock.py all              # All 4 entities

    # Options
    python pull_accurate_stock.py ddd --dry-run    # Preview without uploading
    python pull_accurate_stock.py ljbb --local-only --output ljbb_stock.xlsx
    python pull_accurate_stock.py all --pg-host 76.13.194.120
"""

import os
import sys
import time
import argparse
import hashlib
import hmac
import requests
from requests.exceptions import (
    ConnectionError,
    Timeout,
    RequestException,
    ChunkedEncodingError,
)
from urllib3.exceptions import ProtocolError
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # Base delay in seconds (exponential backoff: 2, 4, 8)

# Script directory (for locating .env files)
SCRIPT_DIR = Path(__file__).parent

# Entity configuration (all 4 Accurate entities)
ENTITIES = {
    "ddd": {
        "name": "DDD",
        "env_file": ".env.ddd",
        "pg_table": "raw.accurate_stock_ddd",
        "api_host": "https://zeus.accurate.id",
    },
    "ljbb": {
        "name": "LJBB",
        "env_file": ".env.ljbb",
        "pg_table": "raw.accurate_stock_ljbb",
        "api_host": None,  # Auto-discover
    },
    "mbb": {
        "name": "MBB",
        "env_file": ".env.mbb",
        "pg_table": "raw.accurate_stock_mbb",
        "api_host": "https://iris.accurate.id",
    },
    "ubb": {
        "name": "UBB",
        "env_file": ".env.ubb",
        "pg_table": "raw.accurate_stock_ubb",
        "api_host": "https://zeus.accurate.id",
    },
}


class AccurateAPIClient:
    """Simple Accurate API client using HMAC-SHA256 authentication (READ-ONLY)"""

    def __init__(self, api_token: str, signature_secret: str, api_host: str = None):
        self.api_token = api_token
        self.signature_secret = signature_secret
        self.api_host = api_host.rstrip("/") if api_host else None
        self.session = requests.Session()

    def _generate_signature(self, timestamp: str) -> str:
        """Generate HMAC-SHA256 signature (hex encoded)"""
        # Signature = HMAC-SHA256(timestamp) using signature_secret
        signature = hmac.new(
            self.signature_secret.encode("utf-8"),
            timestamp.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _build_headers(self) -> dict:
        """Build authentication headers"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp)
        return {
            "Authorization": f"Bearer {self.api_token}",
            "X-Api-Timestamp": timestamp,
            "X-Api-Signature": signature,
            "Accept": "application/json",
        }

    def connect(self) -> dict:
        """Validate token and get database host (POST for auth only, not editing data)"""
        url = "https://account.accurate.id/api/api-token.do"
        headers = self._build_headers()

        response = self.session.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("s"):
            # Get host from response (nested in d.database.host)
            db_info = data.get("d", {})
            database = db_info.get("database", {})
            host = database.get("host", "")
            if host:
                self.api_host = host
            return db_info
        else:
            raise Exception(f"Token validation failed: {data}")

    def _api_call(self, endpoint: str, params: dict = None, timeout: int = 60) -> dict:
        """Make authenticated API call (GET requests only - READ-ONLY)"""
        if not self.api_host:
            raise Exception("Not connected. Call connect() first.")

        url = f"{self.api_host}{endpoint}"
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                headers = (
                    self._build_headers()
                )  # Refresh headers each attempt (new timestamp)
                response = self.session.get(
                    url, headers=headers, params=params, timeout=timeout
                )
                response.raise_for_status()
                return response.json()

            except (
                ConnectionError,
                Timeout,
                ConnectionResetError,
                ChunkedEncodingError,
                ProtocolError,
            ) as e:
                # Retry on connection-related errors (including RemoteDisconnected)
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE ** (
                        attempt + 1
                    )  # Exponential backoff: 2, 4, 8
                    print(
                        f"    Connection error, retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(delay)
                continue

            except RequestException as e:
                # Check if it's a connection-related error wrapped in RequestException
                if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY_BASE ** (attempt + 1)
                        print(
                            f"    Connection error, retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        time.sleep(delay)
                    continue
                # Other request errors (4xx, 5xx) - don't retry
                raise e

        # All retries exhausted
        raise last_error or Exception(f"Failed after {MAX_RETRIES} retries")


def get_pg_connection(pg_host_override: str = None):
    """
    Create PostgreSQL connection using environment variables.

    Connection priority:
      1. --pg-host CLI override
      2. PG_HOST env var
      3. Default: localhost (assumes SSH tunnel)

    Returns:
        psycopg2 connection object
    """
    host = pg_host_override or os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DATABASE", "openclaw_ops")
    user = os.getenv("PG_USER", "openclaw_app")
    password = os.getenv("PG_PASSWORD")

    if not password:
        raise ValueError(
            f"PG_PASSWORD is required. Set it in environment or .env file.\n"
            f"  Connection: {user}@{host}:{port}/{database}"
        )

    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            dbname=database,
            user=user,
            password=password,
            connect_timeout=10,
        )
        conn.autocommit = False
        print(f"  PG connected: {user}@{host}:{port}/{database}")
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(
            f"PostgreSQL connection failed:\n"
            f"  Host: {host}:{port}\n"
            f"  Database: {database}\n"
            f"  User: {user}\n"
            f"  Error: {e}"
        ) from e


def load_entity_credentials(entity_key: str, entity: dict, env_dir: Path = None):
    """
    Load Accurate API credentials for a specific entity.

    Priority:
      1. Environment variables (ACCURATE_API_TOKEN / {ENTITY}_ACCURATE_API_TOKEN)
      2. Entity-specific .env file (.env.ddd, .env.ljbb, etc.)

    Args:
        entity_key: Entity key (ddd, ljbb, mbb, ubb)
        entity: Entity config dict
        env_dir: Directory containing entity .env files (default: script dir)

    Returns:
        Tuple of (api_token, signature_secret)
    """
    entity_upper = entity_key.upper()
    env_dir = env_dir or SCRIPT_DIR

    # Try shared env vars first
    api_token = os.getenv("ACCURATE_API_TOKEN")
    signature_secret = os.getenv("ACCURATE_SIGNATURE_SECRET")

    # Try entity-specific env vars
    if not api_token:
        api_token = os.getenv(f"{entity_upper}_ACCURATE_API_TOKEN")
    if not signature_secret:
        signature_secret = os.getenv(f"{entity_upper}_ACCURATE_SIGNATURE_SECRET")

    # Fallback: entity .env file
    if not api_token or not signature_secret:
        env_file_path = env_dir / entity["env_file"]
        if env_file_path.exists():
            load_dotenv(env_file_path, override=True)
            if not api_token:
                api_token = os.getenv("ACCURATE_API_TOKEN")
            if not signature_secret:
                signature_secret = os.getenv("ACCURATE_SIGNATURE_SECRET")

    if not api_token or not signature_secret:
        raise ValueError(
            f"Missing credentials for {entity['name']}.\n"
            f"Set ACCURATE_API_TOKEN and ACCURATE_SIGNATURE_SECRET,\n"
            f"or provide {entity['env_file']} in {env_dir}"
        )

    return api_token, signature_secret


def pull_inventory_stock(
    entity_key: str,
    dry_run: bool = False,
    local_only: bool = False,
    output_file: str = None,
    pg_host_override: str = None,
    env_dir: Path = None,
) -> pd.DataFrame:
    """
    Pull current inventory/stock data from Accurate Online API (READ-ONLY).

    Args:
        entity_key: Entity key (ddd, ljbb, mbb, ubb)
        dry_run: If True, preview data without uploading to PostgreSQL
        local_only: If True, save to Excel only (no PostgreSQL upload)
        output_file: Custom Excel filename (optional)
        pg_host_override: Override PG_HOST from CLI
        env_dir: Directory containing entity .env files

    Returns:
        DataFrame with stock data
    """
    entity = ENTITIES[entity_key]
    table = entity["pg_table"]

    print(f"\n{'=' * 60}")
    print(f"Pulling {entity['name']} Inventory Stock")
    print(f"{'=' * 60}")

    # Load Accurate API credentials
    api_token, signature_secret = load_entity_credentials(entity_key, entity, env_dir)

    print(f"Entity: {entity['name']}")
    print(f"API Host: {entity['api_host']}")

    # Initialize Accurate client
    print("\nConnecting to Accurate Online API...")
    client = AccurateAPIClient(api_token, signature_secret, entity["api_host"])
    client.connect()
    print("  Connected (READ-ONLY mode)")

    # Pull inventory data
    print("\nFetching inventory data (GET requests only)...")
    all_stock = []
    page = 1
    total_items = 0

    while True:
        print(f"  Page {page}...", end="", flush=True)

        # Get items list (100 per page) - READ-ONLY GET request
        response = client._api_call(
            "/accurate/api/item/list.do", params={"sp.page": page, "sp.pageSize": 100}
        )

        items = response.get("d", [])
        if not items:
            print(" (no more items)")
            break

        print(f" {len(items)} items", flush=True)

        # For each item, get detail with warehouse data
        for idx, item in enumerate(items, 1):
            item_id = item.get("id")

            # Get item detail (contains detailWarehouseData) - READ-ONLY GET request
            detail_response = client._api_call(
                f"/accurate/api/item/detail.do?id={item_id}"
            )
            detail = detail_response.get("d", {})

            # Extract warehouse data
            warehouse_data = detail.get("detailWarehouseData", [])

            for wh in warehouse_data:
                all_stock.append(
                    {
                        "kode_barang": detail.get("no", ""),
                        "nama_barang": detail.get("name", ""),
                        "nama_gudang": wh.get("warehouseName", ""),
                        "kuantitas": int(wh.get("balance", 0)),
                        "unit_price": round(detail.get("unitPrice", 0) or 0, 2),
                        "vendor_price": round(detail.get("vendorPrice", 0) or 0, 2),
                    }
                )

            # Rate limiting (max 8 req/sec, so 0.125s delay)
            time.sleep(0.125)

            # Progress indicator
            if idx % 10 == 0:
                print(f"    Processed {idx}/{len(items)} items...", flush=True)

        total_items += len(items)

        # Check if more pages
        if len(items) < 100:
            break

        page += 1
        time.sleep(0.2)  # Extra delay between pages

    print(f"\n  Total items processed: {total_items}")
    print(f"  Total stock records: {len(all_stock)}")

    # Create DataFrame
    df = pd.DataFrame(all_stock)

    if df.empty:
        print("\n  No stock data retrieved - skipping upload.")
        return df

    # Sort by warehouse, then product code
    df = df.sort_values(["nama_gudang", "kode_barang"]).reset_index(drop=True)

    # Summary
    print(f"\n{'=' * 60}")
    print("INVENTORY SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total stock records: {len(df):,}")
    print(f"Unique products: {df['kode_barang'].nunique():,}")
    print(f"Unique warehouses: {df['nama_gudang'].nunique():,}")
    print(f"Total quantity: {df['kuantitas'].sum():,}")
    print(f"\nWarehouses:")
    for wh in df["nama_gudang"].unique():
        wh_df = df[df["nama_gudang"] == wh]
        print(f"  - {wh}: {len(wh_df):,} records, {wh_df['kuantitas'].sum():,} units")

    # Sample data
    print(f"\nFirst 5 records:")
    print(df.head(5).to_string(index=False))

    # Save to Excel if requested
    if local_only or output_file:
        output_dir = Path("xlsx auto pull - inventory")
        output_dir.mkdir(exist_ok=True)

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{entity['name']}_stock_{timestamp}.xlsx"

        output_path = output_dir / output_file
        df.to_excel(output_path, index=False)
        print(f"\n  Saved to: {output_path}")

        if local_only:
            print("\n(Skipped PostgreSQL upload - local only mode)")
            return df

    # Upload to PostgreSQL (unless dry-run)
    if dry_run:
        print("\n(Dry run - no upload to PostgreSQL)")
        return df

    # --- PostgreSQL upload ---
    snapshot_date = datetime.now().strftime("%Y-%m-%d")
    batch_id = f"accurate_stock_{entity_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn = None

    try:
        print(f"\nConnecting to PostgreSQL...")
        conn = get_pg_connection(pg_host_override)

        print(f"Uploading to {table} (snapshot: {snapshot_date})...")

        with conn.cursor() as cur:
            # Delete existing data for today's snapshot
            cur.execute(
                f"DELETE FROM {table} WHERE snapshot_date = %s", (snapshot_date,)
            )
            deleted = cur.rowcount
            if deleted > 0:
                print(f"  Deleted {deleted:,} existing records for {snapshot_date}")

            # Insert new data
            insert_sql = f"""
                INSERT INTO {table} (kode_barang, nama_barang, nama_gudang, kuantitas,
                                     unit_price, vendor_price, snapshot_date, load_batch_id)
                VALUES %s
            """
            values = [
                (
                    row["kode_barang"],
                    row["nama_barang"],
                    row["nama_gudang"],
                    row["kuantitas"],
                    row["unit_price"],
                    row["vendor_price"],
                    snapshot_date,
                    batch_id,
                )
                for row in all_stock
            ]

            execute_values(cur, insert_sql, values, page_size=500)
            print(f"  Inserted {len(values):,} records")

            # Log to load_history
            cur.execute(
                """
                INSERT INTO raw.load_history (source, entity, data_type, batch_id, date_from, date_to, rows_loaded, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    "accurate_api",
                    entity_key,
                    "stock",
                    batch_id,
                    snapshot_date,
                    snapshot_date,
                    len(all_stock),
                    "success",
                ),
            )

        conn.commit()
        print(f"  Upload complete: {len(df):,} records -> {table}")

    except Exception as e:
        print(f"\n  PostgreSQL upload failed: {e}")
        if conn:
            try:
                conn.rollback()
                # Attempt to log failure
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO raw.load_history (source, entity, data_type, batch_id, date_from, date_to, rows_loaded, status, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            "accurate_api",
                            entity_key,
                            "stock",
                            batch_id,
                            snapshot_date,
                            snapshot_date,
                            0,
                            "error",
                            str(e)[:500],
                        ),
                    )
                    conn.commit()
            except Exception:
                pass  # Best-effort error logging
        raise
    finally:
        if conn:
            conn.close()

    return df


def pull_all_entities(
    dry_run: bool = False, pg_host_override: str = None, env_dir: Path = None
):
    """Pull inventory for all 4 entities (DDD, LJBB, MBB, UBB)."""
    results = {}

    for entity_key in ["ddd", "ljbb", "mbb", "ubb"]:
        try:
            df = pull_inventory_stock(
                entity_key,
                dry_run=dry_run,
                pg_host_override=pg_host_override,
                env_dir=env_dir,
            )
            results[entity_key] = {"status": "success", "records": len(df)}
        except Exception as e:
            print(f"\n  Error pulling {entity_key}: {e}")
            results[entity_key] = {"status": "error", "error": str(e)}

    # Final summary
    print(f"\n\n{'=' * 60}")
    print("FINAL SUMMARY - ALL ENTITIES")
    print(f"{'=' * 60}")
    for entity_key, result in results.items():
        entity_name = ENTITIES[entity_key]["name"]
        if result["status"] == "success":
            print(f"  {entity_name}: {result['records']:,} records")
        else:
            print(f"  {entity_name}: FAILED - {result['error']}")


def main():
    parser = argparse.ArgumentParser(
        description="Pull inventory/stock data from Accurate Online -> PostgreSQL (READ-ONLY)"
    )
    parser.add_argument(
        "entity",
        choices=["ddd", "ljbb", "mbb", "ubb", "all"],
        help='Entity to sync (or "all" for all 4 entities)',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview data without uploading to PostgreSQL",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Save to Excel only, skip PostgreSQL upload",
    )
    parser.add_argument(
        "--output", type=str, help="Custom Excel filename (for --local-only)"
    )
    parser.add_argument(
        "--pg-host",
        type=str,
        default=None,
        help="Override PG_HOST (default from env or localhost)",
    )
    parser.add_argument(
        "--env-dir",
        type=str,
        default=None,
        help="Directory containing entity .env files (default: script dir)",
    )

    args = parser.parse_args()

    # Load PG credentials from .env at script dir level
    pg_env_path = SCRIPT_DIR / ".env"
    if pg_env_path.exists():
        load_dotenv(pg_env_path, override=False)

    # Resolve env-dir for entity credential files
    env_dir = Path(args.env_dir) if args.env_dir else SCRIPT_DIR

    try:
        if args.entity == "all":
            pull_all_entities(
                dry_run=args.dry_run, pg_host_override=args.pg_host, env_dir=env_dir
            )
        else:
            pull_inventory_stock(
                args.entity,
                dry_run=args.dry_run,
                local_only=args.local_only,
                output_file=args.output,
                pg_host_override=args.pg_host,
                env_dir=env_dir,
            )

        print("\nDone!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
