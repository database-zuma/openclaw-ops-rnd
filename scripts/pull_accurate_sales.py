#!/usr/bin/env python3
"""
Pull daily sales data from Accurate Online API -> PostgreSQL.

Ported from Supabase version to psycopg2 for self-hosted PostgreSQL (openclaw_ops).
Supports 3 entities: DDD, MBB, UBB (LJBB excluded - no sales data).

ALL API OPERATIONS ARE READ-ONLY (GET requests only).
Database writes: UPSERT (INSERT ... ON CONFLICT) per entity.

Strategy:
- Daily sync (3 days default): Use Official API with token (automated, no cookies)
- Covers late entries or corrections from past 2 days
- Small dataset = fast API calls
- Upserts existing data to stay current

Usage:
    python pull_accurate_sales.py ddd              # DDD sales last 3 days
    python pull_accurate_sales.py mbb              # MBB sales last 3 days
    python pull_accurate_sales.py ubb              # UBB sales last 3 days
    python pull_accurate_sales.py all              # All 3 entities

    # Options
    python pull_accurate_sales.py ddd --days 5     # Custom days
    python pull_accurate_sales.py ddd --dry-run    # Preview without uploading
    python pull_accurate_sales.py all --pg-host 76.13.194.120
    python pull_accurate_sales.py ddd --env-dir /path/to/envs
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
from datetime import datetime, timedelta
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

# Entity configuration (3 entities — LJBB excluded, no sales data)
ENTITIES = {
    "ddd": {
        "name": "DDD",
        "env_file": ".env.ddd",
        "pg_table": "raw.accurate_sales_ddd",
        "api_host": "https://zeus.accurate.id",
    },
    "mbb": {
        "name": "MBB",
        "env_file": ".env.mbb",
        "pg_table": "raw.accurate_sales_mbb",
        "api_host": "https://iris.accurate.id",
    },
    "ubb": {
        "name": "UBB",
        "env_file": ".env.ubb",
        "pg_table": "raw.accurate_sales_ubb",
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

    def get_invoices(
        self, start_date: datetime, end_date: datetime, page: int = 1
    ) -> dict:
        """Get sales invoices for date range (READ-ONLY GET request)"""
        params = {
            "sp.page": page,
            "sp.pageSize": 100,
            "filter.transDate.op": "BETWEEN",
            "filter.transDate.val[0]": start_date.strftime("%d/%m/%Y"),
            "filter.transDate.val[1]": end_date.strftime("%d/%m/%Y"),
        }
        return self._api_call("/accurate/api/sales-invoice/list.do", params=params)

    def get_invoice_detail(self, invoice_id: int) -> dict:
        """Get invoice details with line items (READ-ONLY GET request)"""
        return self._api_call(f"/accurate/api/sales-invoice/detail.do?id={invoice_id}")


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
      2. Entity-specific .env file (.env.ddd, .env.mbb, etc.)

    Args:
        entity_key: Entity key (ddd, mbb, ubb)
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


def flatten_invoice(invoice: dict) -> list:
    """Convert invoice detail to flat rows for PostgreSQL."""
    rows = []

    invoice_number = invoice.get("number", "")
    trans_date = invoice.get("transDate", "")

    # Customer
    customer_obj = invoice.get("customer", {})
    customer_name = (
        customer_obj.get("name", "") if isinstance(customer_obj, dict) else ""
    )

    # Branch
    branch_name = invoice.get("branchName", "")

    # Line items
    for item in invoice.get("detailItem", []):
        if not isinstance(item, dict):
            continue

        item_obj = item.get("item", {}) or {}
        unit_obj = item.get("itemUnit", {}) or {}
        dept_obj = item.get("department", {}) or {}

        quantity = item.get("quantity", 0)
        if quantity <= 0:
            continue

        # Convert date DD/MM/YYYY to YYYY-MM-DD
        tanggal = trans_date
        if "/" in str(trans_date):
            parts = trans_date.split("/")
            tanggal = f"{parts[2]}-{parts[1]}-{parts[0]}"

        # BPP fallback strategy:
        # 1. Try unitCost (transaction cost) - NOT AVAILABLE in API
        # 2. Try averageCost (average cost) - NOT AVAILABLE in API
        # 3. Try item.cost (master cost) - Available but may be 0 or outdated
        # 4. Default to 0
        # NOTE: API does not return actual transaction costs for security reasons
        bpp_value = (
            item.get("unitCost", 0)
            or item.get("averageCost", 0)
            or item_obj.get("cost", 0)
            or 0
        )

        # Get warehouse info for this line item
        warehouse_obj = item.get("warehouse", {}) or {}

        row = {
            "tanggal": tanggal,
            "nama_departemen": dept_obj.get("name", "") or branch_name or "UNKNOWN",
            "nama_pelanggan": customer_name or "UMUM",
            "nomor_invoice": invoice_number,
            "kode_produk": item_obj.get("no", ""),
            "nama_barang": item_obj.get("name", ""),
            "satuan": unit_obj.get("name", "") or "PAIR",
            "kuantitas": int(quantity),
            "harga_satuan": round(item.get("unitPrice", 0), 2),
            "total_harga": round(item.get("totalPrice", 0), 2),
            "bpp": round(bpp_value, 2),
            # 4 NEW COLUMNS:
            "nama_gudang": warehouse_obj.get("name", ""),
            "vendor_price": round(item_obj.get("vendorPrice", 0) or 0, 2),
            "dpp_amount": round(item.get("dppAmount", 0) or 0, 2),
            "tax_amount": round(item.get("tax1Amount", 0) or 0, 2),
        }

        if row["kode_produk"]:
            rows.append(row)

    return rows


def sync_entity(
    entity_key: str,
    days: int = 3,
    dry_run: bool = False,
    pg_host_override: str = None,
    env_dir: Path = None,
) -> bool:
    """
    Sync sales data for an entity using Official API -> PostgreSQL.

    Args:
        entity_key: Entity code (ddd, mbb, ubb)
        days: Number of days to sync (default 3)
        dry_run: If True, preview data without uploading
        pg_host_override: Override PG_HOST from CLI
        env_dir: Directory containing entity .env files

    Returns:
        True if successful
    """
    entity = ENTITIES.get(entity_key)
    if not entity:
        print(f"Unknown entity: {entity_key}")
        return False

    table = entity["pg_table"]

    print(f"\n{'=' * 60}")
    print(f"  {entity['name']} DAILY SALES SYNC (Official API -> PostgreSQL)")
    print(f"{'=' * 60}")

    # Load Accurate API credentials
    try:
        api_token, signature_secret = load_entity_credentials(
            entity_key, entity, env_dir
        )
    except ValueError as e:
        print(f"  {e}")
        return False

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    print(f"Entity: {entity['name']}")
    print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)"
    )
    print(f"Target: {table}")

    # Connect to Accurate API
    print(f"\nConnecting to Accurate Online API...")
    client = AccurateAPIClient(api_token, signature_secret, entity["api_host"])

    try:
        db_info = client.connect()
        database = db_info.get("database", {})
        db_name = database.get("alias") or database.get("name") or "Unknown"
        host = database.get("host", "Unknown")
        print(f"  Connected: {db_name}")
        print(f"  Host: {host}")
    except Exception as e:
        print(f"  Connection failed: {e}")
        return False

    # Fetch invoices
    print(f"\nFetching invoices...")
    all_invoices = []
    page = 1

    while True:
        try:
            response = client.get_invoices(start_date, end_date, page)
            if not response.get("s"):
                print(f"  API error: {response}")
                break

            invoices = response.get("d", [])
            all_invoices.extend(invoices)

            if len(invoices) < 100:
                break
            page += 1
            print(
                f"  Page {page - 1}: {len(invoices)} invoices (total: {len(all_invoices)})"
            )

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

    print(f"  Found {len(all_invoices)} invoices")

    if not all_invoices:
        print("  No invoices found for this period")
        return True  # Not an error, just no data

    # Fetch details and flatten
    print(f"\nFetching invoice details...")
    all_rows = []
    total = len(all_invoices)

    for idx, inv in enumerate(all_invoices, 1):
        if idx % 20 == 0 or idx == total:
            print(f"  Progress: {idx}/{total} ({idx * 100 // total}%)")

        try:
            detail = client.get_invoice_detail(inv.get("id"))
            if detail.get("s"):
                rows = flatten_invoice(detail.get("d", {}))
                all_rows.extend(rows)
            time.sleep(0.125)  # Rate limit: 8 req/sec
        except Exception as e:
            print(f"  Error on invoice {inv.get('number')}: {e}")

    if not all_rows:
        print("  No line items extracted")
        return True

    # Convert to DataFrame for summary
    df = pd.DataFrame(all_rows)

    # Summary
    print(f"\n{'=' * 60}")
    print("SALES SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total line items: {len(df):,}")
    print(f"Unique invoices: {df['nomor_invoice'].nunique():,}")
    print(f"Unique products: {df['kode_produk'].nunique():,}")
    print(f"Total quantity: {df['kuantitas'].sum():,}")
    print(f"Total sales: Rp {df['total_harga'].sum():,.0f}")
    print(f"\nBy department:")
    for dept in df["nama_departemen"].unique():
        dept_df = df[df["nama_departemen"] == dept]
        print(
            f"  - {dept}: {len(dept_df):,} items, Rp {dept_df['total_harga'].sum():,.0f}"
        )

    # Sample data
    print(f"\nFirst 5 records:")
    print(df.head(5).to_string(index=False))

    if dry_run:
        print(f"\n[DRY RUN] Would upload to PostgreSQL:")
        print(f"  Table: {table}")
        print(f"  Rows: {len(df)}")
        return True

    # --- PostgreSQL UPSERT ---
    snapshot_date = datetime.now().strftime("%Y-%m-%d")
    batch_id = f"accurate_sales_{entity_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn = None

    try:
        print(f"\nConnecting to PostgreSQL...")
        conn = get_pg_connection(pg_host_override)

        print(f"Upserting to {table} (snapshot: {snapshot_date})...")

        with conn.cursor() as cur:
            # UPSERT: INSERT ... ON CONFLICT
            insert_sql = f"""
                INSERT INTO {table} (tanggal, nama_departemen, nama_pelanggan, nomor_invoice,
                                     kode_produk, nama_barang, satuan, kuantitas, harga_satuan,
                                     total_harga, bpp, nama_gudang, vendor_price, dpp_amount,
                                     tax_amount, snapshot_date, load_batch_id)
                VALUES %s
                ON CONFLICT (nomor_invoice, kode_produk, tanggal, snapshot_date)
                DO UPDATE SET
                    nama_departemen = EXCLUDED.nama_departemen,
                    nama_pelanggan = EXCLUDED.nama_pelanggan,
                    nama_barang = EXCLUDED.nama_barang,
                    satuan = EXCLUDED.satuan,
                    kuantitas = EXCLUDED.kuantitas,
                    harga_satuan = EXCLUDED.harga_satuan,
                    total_harga = EXCLUDED.total_harga,
                    bpp = EXCLUDED.bpp,
                    nama_gudang = EXCLUDED.nama_gudang,
                    vendor_price = EXCLUDED.vendor_price,
                    dpp_amount = EXCLUDED.dpp_amount,
                    tax_amount = EXCLUDED.tax_amount,
                    load_batch_id = EXCLUDED.load_batch_id,
                    loaded_at = now()
            """

            values = [
                (
                    row["tanggal"],
                    row["nama_departemen"],
                    row["nama_pelanggan"],
                    row["nomor_invoice"],
                    row["kode_produk"],
                    row["nama_barang"],
                    row["satuan"],
                    row["kuantitas"],
                    row["harga_satuan"],
                    row["total_harga"],
                    row["bpp"],
                    row["nama_gudang"],
                    row["vendor_price"],
                    row["dpp_amount"],
                    row["tax_amount"],
                    snapshot_date,
                    batch_id,
                )
                for row in all_rows
            ]

            execute_values(cur, insert_sql, values, page_size=500)
            print(f"  Upserted {len(values):,} records")

            # Log to load_history
            cur.execute(
                """
                INSERT INTO raw.load_history (source, entity, data_type, batch_id, date_from, date_to, rows_loaded, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    "accurate_api",
                    entity_key,
                    "sales",
                    batch_id,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    len(all_rows),
                    "success",
                ),
            )

        conn.commit()
        print(f"  Upload complete: {len(df):,} records -> {table}")
        return True

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
                            "sales",
                            batch_id,
                            start_date.strftime("%Y-%m-%d"),
                            end_date.strftime("%Y-%m-%d"),
                            0,
                            "error",
                            str(e)[:500],
                        ),
                    )
                    conn.commit()
            except Exception:
                pass  # Best-effort error logging

        # Save to CSV as fallback
        csv_file = (
            SCRIPT_DIR
            / f"{entity['name']}_sales_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        df.to_csv(csv_file, index=False)
        print(f"  Saved fallback CSV: {csv_file}")
        return False

    finally:
        if conn:
            conn.close()


def sync_all_entities(
    days: int = 3,
    dry_run: bool = False,
    pg_host_override: str = None,
    env_dir: Path = None,
):
    """Sync sales for all 3 entities (DDD, MBB, UBB)."""
    results = {}

    for entity_key in ["ddd", "mbb", "ubb"]:
        try:
            success = sync_entity(
                entity_key,
                days=days,
                dry_run=dry_run,
                pg_host_override=pg_host_override,
                env_dir=env_dir,
            )
            results[entity_key] = success
        except Exception as e:
            print(f"\n  Error syncing {entity_key}: {e}")
            results[entity_key] = False

    # Final summary
    print(f"\n\n{'=' * 60}")
    print("FINAL SUMMARY - ALL ENTITIES")
    print(f"{'=' * 60}")
    for entity_key, success in results.items():
        entity_name = ENTITIES[entity_key]["name"]
        status = "SUCCESS" if success else "FAILED"
        print(f"  {entity_name}: {status}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Pull daily sales data from Accurate Online -> PostgreSQL (READ-ONLY)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pull_accurate_sales.py ddd              # DDD sales last 3 days
  python pull_accurate_sales.py all              # All 3 entities
  python pull_accurate_sales.py mbb --days 5     # Custom days
  python pull_accurate_sales.py ddd --dry-run    # Preview only
  python pull_accurate_sales.py all --pg-host 76.13.194.120
""",
    )
    parser.add_argument(
        "entity",
        choices=["ddd", "mbb", "ubb", "all"],
        help='Entity to sync (or "all" for all 3 entities)',
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Days to sync (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview data without uploading to PostgreSQL",
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

    start_time = datetime.now()
    print(f"{'=' * 60}")
    print(f"  DAILY SALES SYNC - ACCURATE API -> POSTGRESQL")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")

    try:
        if args.entity == "all":
            results = sync_all_entities(
                days=args.days,
                dry_run=args.dry_run,
                pg_host_override=args.pg_host,
                env_dir=env_dir,
            )
            all_success = all(results.values())
        else:
            all_success = sync_entity(
                args.entity,
                days=args.days,
                dry_run=args.dry_run,
                pg_host_override=args.pg_host,
                env_dir=env_dir,
            )

        # Duration
        duration = datetime.now() - start_time
        print(f"\nDuration: {duration}")
        print("Done!")

        sys.exit(0 if all_success else 1)

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
