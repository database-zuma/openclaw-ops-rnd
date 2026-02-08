#!/usr/bin/env python3
"""
Historical Sales Report Export - Accurate Online Report API
Ports original_pull_ddd_report.py to write to VPS PostgreSQL.

Downloads sales reports via Report Export API (fast workaround),
cleans data, and inserts into raw.accurate_sales_{entity}.

Missing columns vs official API: nama_gudang, vendor_price, dpp_amount, tax_amount
These will be NULL for historical data. Daily cron fills all 19 cols going forward.

Usage:
    python pull_historical_sales.py ddd --start 2024-01-01 --end 2026-02-08
    python pull_historical_sales.py mbb --start 2024-01-01 --end 2026-02-08
    python pull_historical_sales.py ubb --start 2024-01-01 --end 2026-02-08
    python pull_historical_sales.py all --start 2022-01-01 --end 2026-02-08
    python pull_historical_sales.py ddd --start 2024-01-01 --end 2026-02-08 --dry-run

Chunks into 90-day windows to avoid report size limits.
"""

import os
import sys
import time
import json
import argparse
import traceback
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from io import BytesIO
from dotenv import load_dotenv

ENTITY_CONFIGS = {
    "ddd": {"name": "DDD", "table": "raw.accurate_sales_ddd"},
    "mbb": {"name": "MBB", "table": "raw.accurate_sales_mbb"},
    "ubb": {"name": "UBB", "table": "raw.accurate_sales_ubb"},
}

REPORT_PLAN_ID = "ViewSalesByItemDetailReport"


class AccurateReportExporter:
    def __init__(self, dsi, usi, report_host, report_id):
        self.dsi = dsi
        self.usi = usi
        self.report_host = report_host
        self.report_id = report_id
        self.session = requests.Session()
        self.session.cookies.set("_dsi", dsi)
        self.session.cookies.set("_usi", usi)

    def execute_report(self, start_date_str, end_date_str):
        url = f"{self.report_host}/accurate/report/execute-report.do"
        report_input = {
            "param": {
                "startDate": start_date_str,
                "endDate": end_date_str,
                "selectedBranch": [{"name": "[Semua Cabang]", "id": None}],
                "currentUserRole": [],
            },
            "filter": [],
            "subSelection": 0,
            "selection": [],
        }
        data = {
            "id": self.report_id,
            "planId": REPORT_PLAN_ID,
            "reportInput": json.dumps(report_input),
            "cacheId": "",
            "pageIndex": "0",
            "_usi": self.usi,
            "_dsi": self.dsi,
        }
        print(f"   Executing report...")
        resp = self.session.post(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            timeout=120,
        )
        if resp.status_code != 200:
            raise Exception(
                f"Report exec failed: {resp.status_code} - {resp.text[:500]}"
            )
        result = resp.json()
        if not result.get("s"):
            raise Exception(
                f"Report exec failed: {result.get('d', result.get('m', 'Unknown'))}"
            )
        cache_id = result.get("cacheId") or result.get("d", {}).get("cacheId")
        if not cache_id:
            raise Exception(f"No cacheId: {result}")
        print(f"   Cache ID: {cache_id}")
        return cache_id

    def export_report(self, cache_id, export_type="xls"):
        url = f"{self.report_host}/accurate/report/export-report.do"
        data = {
            "_usi": self.usi,
            "_dsi": self.dsi,
            "cacheId": cache_id,
            "exportType": export_type,
            "name": "",
        }
        print(f"   Downloading report...")
        resp = self.session.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=300,
        )
        if resp.status_code != 200:
            raise Exception(f"Export failed: {resp.status_code}")
        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct:
            raise Exception(f"Export failed: {resp.json()}")
        print(f"   Downloaded {len(resp.content):,} bytes")
        return resp.content

    def download_sales_report(self, start_date, end_date):
        start_str = start_date.strftime("%d/%m/%Y")
        end_str = end_date.strftime("%d/%m/%Y")
        print(f"   Period: {start_str} to {end_str}")
        cache_id = self.execute_report(start_str, end_str)
        time.sleep(2)
        excel_content = self.export_report(cache_id, "xls")
        print(f"   Parsing Excel...")
        df = pd.read_excel(BytesIO(excel_content), engine="openpyxl")
        print(f"   Raw rows: {len(df):,}")
        return df


def clean_report_data(df):
    column_mapping = {
        "Tanggal": "tanggal",
        "Nama Departemen": "nama_departemen",
        "Nama Pelanggan": "nama_pelanggan",
        "Kode #": "kode_produk",
        "Nomor #": "nomor_invoice",
        "Nama Barang": "nama_barang",
        "Satuan": "satuan",
        "Kuantitas": "kuantitas",
        "@Harga": "harga_satuan",
        "Total Harga": "total_harga",
        "BPP": "bpp",
    }
    renamed = {}
    for excel_col, db_col in column_mapping.items():
        for col in df.columns:
            if excel_col.lower() in str(col).lower():
                renamed[col] = db_col
                break
    if renamed:
        df = df.rename(columns=renamed)
    needed = list(column_mapping.values())
    available = [c for c in needed if c in df.columns]
    if available:
        df = df[available].copy()

    # Forward-fill sparse columns (report uses grouped format)
    for col in ["tanggal", "nama_departemen", "nama_pelanggan", "nomor_invoice"]:
        if col in df.columns:
            df[col] = df[col].ffill()

    if "kode_produk" in df.columns:
        df = df[df["kode_produk"].notna() & (df["kode_produk"] != "")]
    if "kuantitas" in df.columns:
        df["kuantitas"] = pd.to_numeric(df["kuantitas"], errors="coerce").fillna(0)
        df = df[df["kuantitas"] != 0]
    if "tanggal" in df.columns:
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
        df = df[df["tanggal"].notna()]
        df["tanggal"] = df["tanggal"].dt.strftime("%Y-%m-%d")

    for col in ["kuantitas", "harga_satuan", "total_harga", "bpp"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["harga_satuan", "total_harga", "bpp"]:
        if col in df.columns:
            df[col] = df[col].round(2)
    if "kuantitas" in df.columns:
        df["kuantitas"] = df["kuantitas"].astype(int)

    if "satuan" in df.columns:
        df["satuan"] = df["satuan"].fillna("PAIR")
    if "nama_pelanggan" in df.columns:
        df["nama_pelanggan"] = df["nama_pelanggan"].fillna("UMUM")
    if "nama_departemen" in df.columns:
        df["nama_departemen"] = df["nama_departemen"].fillna("UNKNOWN")

    print(f"   Cleaned rows: {len(df):,}")
    return df


def insert_to_postgres(
    df, table, pg_host, pg_port, pg_db, pg_user, pg_pass, snapshot_date, batch_id
):
    if df.empty:
        print("   No data to insert")
        return 0

    conn = psycopg2.connect(
        host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_pass
    )
    cur = conn.cursor()

    # nama_gudang, vendor_price, dpp_amount, tax_amount will be NULL (not in report)
    cols = [
        "tanggal",
        "nama_departemen",
        "nama_pelanggan",
        "nomor_invoice",
        "kode_produk",
        "nama_barang",
        "satuan",
        "kuantitas",
        "harga_satuan",
        "total_harga",
        "bpp",
        "snapshot_date",
        "loaded_at",
        "load_batch_id",
    ]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for _, r in df.iterrows():
        rows.append(
            (
                r.get("tanggal"),
                r.get("nama_departemen"),
                r.get("nama_pelanggan"),
                r.get("nomor_invoice"),
                r.get("kode_produk"),
                r.get("nama_barang"),
                r.get("satuan"),
                int(r.get("kuantitas", 0)),
                float(r.get("harga_satuan", 0)),
                float(r.get("total_harga", 0)),
                float(r.get("bpp", 0)),
                snapshot_date,
                now,
                batch_id,
            )
        )

    col_str = ", ".join(cols)

    insert_sql = f"""
        INSERT INTO {table} ({col_str})
        VALUES %s
        ON CONFLICT (nomor_invoice, kode_produk, tanggal, snapshot_date)
        DO UPDATE SET
            kuantitas = EXCLUDED.kuantitas,
            harga_satuan = EXCLUDED.harga_satuan,
            total_harga = EXCLUDED.total_harga,
            bpp = EXCLUDED.bpp,
            loaded_at = EXCLUDED.loaded_at,
            load_batch_id = EXCLUDED.load_batch_id
    """

    batch_size = 1000
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        execute_values(cur, insert_sql, batch)
        total += len(batch)
        print(f"   Inserted: {total:,}/{len(rows):,}")

    conn.commit()
    cur.close()
    conn.close()
    return total


def log_load(
    pg_host, pg_port, pg_db, pg_user, pg_pass, table, batch_id, rows, status, error=None
):
    try:
        conn = psycopg2.connect(
            host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_pass
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO raw.load_history (table_name, load_batch_id, rows_loaded, status, error_message, loaded_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """,
            (table, batch_id, rows, status, error),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"   Warning: Could not log to load_history: {e}")


def run_entity(entity, start_date, end_date, dry_run, env_dir):
    cfg = ENTITY_CONFIGS[entity]
    table = cfg["table"]
    name = cfg["name"]

    # Load entity env
    env_file = os.path.join(env_dir, f".env.{entity}")
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)

    # Load PG env
    pg_env = os.path.join(env_dir, ".env")
    if os.path.exists(pg_env):
        load_dotenv(pg_env, override=True)

    dsi = os.getenv("ACCURATE_DSI")
    usi = os.getenv("ACCURATE_USI")
    report_host = os.getenv("ACCURATE_REPORT_HOST", "https://zeus-report.accurate.id")
    report_id = os.getenv("ACCURATE_REPORT_ID")

    if not dsi or not usi or dsi == "PASTE_YOUR_DSI_COOKIE_HERE":
        print(
            f"ERROR: No cookies for {name}. Update .env.{entity} with ACCURATE_DSI and ACCURATE_USI"
        )
        return False

    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_db = os.getenv("PG_DATABASE", os.getenv("PG_DB", "openclaw_ops"))
    pg_user = os.getenv("PG_USER", "openclaw_app")
    pg_pass = os.getenv("PG_PASSWORD", os.getenv("PG_PASS", ""))

    exporter = AccurateReportExporter(dsi, usi, report_host, report_id)
    batch_id = f"historical_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    snapshot_date = datetime.now().strftime("%Y-%m-%d")

    # Chunk into 90-day windows
    current_start = start_date
    total_rows = 0
    chunk_num = 0

    while current_start < end_date:
        chunk_num += 1
        current_end = min(current_start + timedelta(days=89), end_date)

        print(f"\n{'=' * 60}")
        print(
            f"  {name} - Chunk {chunk_num}: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}"
        )
        print(f"{'=' * 60}")

        try:
            df = exporter.download_sales_report(current_start, current_end)
            if df.empty:
                print(f"   No data for this period")
                current_start = current_end + timedelta(days=1)
                continue

            df = clean_report_data(df)

            if dry_run:
                print(f"   DRY RUN - would insert {len(df):,} rows")
                if not df.empty:
                    print(f"   Sample:")
                    print(df.head(3).to_string())
            else:
                inserted = insert_to_postgres(
                    df,
                    table,
                    pg_host,
                    pg_port,
                    pg_db,
                    pg_user,
                    pg_pass,
                    snapshot_date,
                    batch_id,
                )
                total_rows += inserted
                print(f"   Chunk done: {inserted:,} rows")

        except Exception as e:
            print(f"   ERROR on chunk {chunk_num}: {e}")
            log_load(
                pg_host,
                pg_port,
                pg_db,
                pg_user,
                pg_pass,
                table,
                batch_id,
                0,
                "error",
                str(e),
            )
            traceback.print_exc()

        current_start = current_end + timedelta(days=1)
        time.sleep(1)

    if not dry_run and total_rows > 0:
        log_load(
            pg_host,
            pg_port,
            pg_db,
            pg_user,
            pg_pass,
            table,
            batch_id,
            total_rows,
            "success",
        )

    print(f"\n{'=' * 60}")
    print(f"  {name} COMPLETE: {total_rows:,} total rows inserted")
    print(f"{'=' * 60}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Historical sales report export to PostgreSQL"
    )
    parser.add_argument(
        "entity", choices=["ddd", "mbb", "ubb", "all"], help="Entity to pull"
    )
    parser.add_argument(
        "--start", type=str, required=True, help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Download + clean only, no insert"
    )
    parser.add_argument(
        "--env-dir",
        type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Directory with .env files",
    )
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")

    entities = ["ddd", "mbb", "ubb"] if args.entity == "all" else [args.entity]

    print(f"Historical Sales Export")
    print(f"Entities: {[ENTITY_CONFIGS[e]['name'] for e in entities]}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE INSERT'}")

    for entity in entities:
        run_entity(entity, start_date, end_date, args.dry_run, args.env_dir)


if __name__ == "__main__":
    main()
