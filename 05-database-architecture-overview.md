# OpenClaw OPS — Database Architecture Overview

> For presenting to management. Concise explanation of what we built, why, and how it works.
> Last updated: 8 Feb 2026

---

## What Is This?

A **self-hosted PostgreSQL database** on our own VPS server that centralizes ALL of Zuma Indonesia's operational data from multiple sources into one place. This is the **data backbone** for our AI agent system (OpenClaw).

**Before**: Data scattered across Accurate Online (ERP), iSeller (POS), Google Sheets — each requiring manual login, manual export, manual analysis.

**After**: One database that automatically pulls data daily, structures it cleanly, and makes it ready for automated reports, dashboards, and AI-powered analysis.

---

## Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS Server (Hostinger KVM 2)              │
│                    IP: 76.13.194.120                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL 16.11 + pgvector                          │   │
│  │  Database: openclaw_ops                                │   │
│  │                                                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │   │
│  │  │ portal.* │ │  raw.*   │ │  core.*  │ │  mart.*  │ │   │
│  │  │ Master   │ │ Daily    │ │ Cleaned  │ │ Reports  │ │   │
│  │  │ Data     │ │ Raw Data │ │ Joined   │ │ Ready    │ │   │
│  │  │ ✅ Done  │ │ ✅ Ready │ │ ⬜ Later │ │ ⬜ Later │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────┐  ┌─────────────────┐                    │
│  │ PostgREST API  │  │ Backup (daily)  │                    │
│  │ REST interface │  │ 7-day retention │                    │
│  └────────────────┘  └─────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

**Monthly cost**: ~$10/month (Hostinger KVM 2 VPS)

---

## The 4-Layer Data Architecture

Data flows through 4 schemas (think: 4 stages), each with a specific purpose:

### Layer 1: `portal.*` — Master/Reference Data (DONE)

**What**: Company master data that rarely changes — product catalog, store list, pricing, capacity limits.

**Source**: Google Sheets (exported as CSV, loaded manually via DBeaver).

| Table | Rows | What It Contains |
|-------|------|-----------------|
| `portal.store` | 326 | All Zuma retail store locations (name, branch, area, category, targets) |
| `portal.kodemix` | 5,464 | Every product SKU variation (code, name, size, tier, series, gender, color) |
| `portal.hpprsp` | 935 | Product pricing — purchase price, tag price, retail selling price |
| `portal.stock_capacity` | 57 | Per-store stock limits (max display, max stock, storage) |

**Total**: 6,782 rows loaded and verified.

---

### Layer 2: `raw.*` — Daily Raw Data (READY, awaiting first pull)

**What**: Transactional data pulled automatically from Accurate Online API every day — stock levels and sales invoices.

**Source**: Accurate Online API (automated) + iSeller CSV (manual upload).

**Key design principle**: Every day's data gets a `snapshot_date` tag. We never delete old data — we just add today's snapshot next to yesterday's. This lets us see how stock/sales change over time.

| Table | Source | What It Contains |
|-------|--------|-----------------|
| `raw.accurate_stock_ddd` | Accurate API (DDD entity) | Daily stock snapshot — what's in each warehouse, how many pairs |
| `raw.accurate_stock_ljbb` | Accurate API (LJBB entity) | Same for LJBB entity |
| `raw.accurate_stock_mbb` | Accurate API (MBB entity) | Same for MBB entity |
| `raw.accurate_stock_ubb` | Accurate API (UBB entity) | Same for UBB entity |
| `raw.accurate_sales_ddd` | Accurate API (DDD entity) | Sales invoices — date, store, product, qty, price, tax, cost |
| `raw.accurate_sales_mbb` | Accurate API (MBB entity) | Same for MBB entity |
| `raw.accurate_sales_ubb` | Accurate API (UBB entity) | Same for UBB entity |
| `raw.iseller_sales` | iSeller CSV export | Online marketplace orders (Shopee, Tokopedia, etc.) |
| `raw.load_history` | System | Audit trail — tracks every data load (when, how many rows, success/fail) |

**Note**: LJBB has no sales data (only stock + finance reports), so no `raw.accurate_sales_ljbb`.

**Stock tables** have 10 columns each:
`id`, `kode_barang`, `nama_barang`, `nama_gudang`, `kuantitas`, `unit_price`, `vendor_price`, `snapshot_date`, `loaded_at`, `load_batch_id`

**Sales tables** have 19 columns each:
`id`, `tanggal`, `nama_departemen`, `nama_pelanggan`, `nomor_invoice`, `kode_produk`, `nama_barang`, `satuan`, `kuantitas`, `harga_satuan`, `total_harga`, `bpp`, `nama_gudang`, `vendor_price`, `dpp_amount`, `tax_amount`, `snapshot_date`, `loaded_at`, `load_batch_id`

---

### Layer 3: `core.*` — Cleaned & Joined Data (PLANNED)

**What**: Takes raw data and master data, cleans them, joins them into a proper "star schema" — the standard approach for analytics databases.

**Why needed**: Raw data has messy store names (e.g., "Zuma MOI" vs "ZUMA MALL OF INDONESIA (MOI)"), product codes that need enrichment with pricing/tier info, etc. Core schema solves all of this.

| Planned Table | Purpose |
|---------------|---------|
| `core.dim_product` | Unified product master — SKU + pricing + tier in one row |
| `core.dim_store` | Unified store master — with alias mapping for name variants |
| `core.dim_warehouse` | Warehouse dimension |
| `core.dim_date` | Calendar dimension (for reporting by week/month/quarter) |
| `core.fact_sales` | All sales from all entities in one table, enriched with product/store info |
| `core.fact_stock` | All stock from all entities in one table, enriched |

---

### Layer 4: `mart.*` — Ready-to-Use Reports (PLANNED)

**What**: Pre-built views that answer specific business questions. These feed into GSheet dashboards and automated email reports.

| Planned View | Business Question |
|--------------|-------------------|
| `mart.report_control_stock` | "What's the current stock health per store?" (fill-fill %, fullbook %, depth) |
| `mart.report_tier_summary` | "How is stock distributed across product tiers?" |
| `mart.report_depth_alert` | "Which stores are running low on specific products?" |
| `mart.report_sales_daily` | "What sold today, where, and how much?" |
| `mart.report_stock_vs_capacity` | "Which stores are over/under their stock capacity limits?" |

---

## Complete Data Flowchart

### Full Pipeline: Source → Raw → Core → Mart → Output

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                              EXTERNAL DATA SOURCES                                          ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐               ║
║   │   ACCURATE ONLINE   │   │   GOOGLE SHEETS     │   │     iSELLER         │               ║
║   │   (ERP System)      │   │   (Portal Data)     │   │   (POS System)      │               ║
║   │                     │   │                     │   │                     │               ║
║   │  4 entities:        │   │  4 spreadsheets:    │   │  1 export:          │               ║
║   │  • DDD              │   │  • Store list       │   │  • Order details    │               ║
║   │  • LJBB             │   │  • Product catalog  │   │    (Shopee,         │               ║
║   │  • MBB              │   │  • Pricing (HPPRSP) │   │     Tokopedia,      │               ║
║   │  • UBB              │   │  • Stock capacity   │   │     TikTok, etc.)   │               ║
║   └────────┬────────────┘   └────────┬────────────┘   └────────┬────────────┘               ║
║            │                         │                         │                             ║
╚════════════╪═════════════════════════╪═════════════════════════╪═════════════════════════════╝
             │                         │                         │
             │ REST API                │ CSV Export               │ CSV Export
             │ (automated daily)       │ (manual, infrequent)     │ (manual, weekly)
             │ HMAC-SHA256 auth        │ via DBeaver              │ via DBeaver
             │                         │                         │
             ▼                         ▼                         ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                        DATABASE: openclaw_ops (PostgreSQL 16.11)                             ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  SCHEMA: raw.*  —  Raw / Staging Layer                                    ✅ READY  │    ║
║  │  ─────────────────────────────────────────────────────────────────────────────────── │    ║
║  │                                                                                      │    ║
║  │  FROM ACCURATE API:                          FROM iSELLER CSV:                       │    ║
║  │  ┌───────────────────────────────────┐       ┌──────────────────────┐                │    ║
║  │  │ STOCK (daily snapshot)            │       │ raw.iseller_sales    │                │    ║
║  │  │ ┌─ raw.accurate_stock_ddd        │       │ (30+ cols)           │                │    ║
║  │  │ ├─ raw.accurate_stock_ljbb       │       │ online marketplace   │                │    ║
║  │  │ ├─ raw.accurate_stock_mbb        │       │ orders               │                │    ║
║  │  │ └─ raw.accurate_stock_ubb        │       └──────────────────────┘                │    ║
║  │  │    (10 cols each)                 │                                                │    ║
║  │  │                                   │       ┌──────────────────────┐                │    ║
║  │  │ SALES (daily incremental)         │       │ raw.load_history     │                │    ║
║  │  │ ┌─ raw.accurate_sales_ddd        │       │ (audit trail)        │                │    ║
║  │  │ ├─ raw.accurate_sales_mbb        │       │ tracks every load    │                │    ║
║  │  │ └─ raw.accurate_sales_ubb        │       └──────────────────────┘                │    ║
║  │  │    (19 cols each)                 │                                                │    ║
║  │  │    ⚠ No LJBB sales (no data)     │                                                │    ║
║  │  └───────────────────────────────────┘                                                │    ║
║  └──────────────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  SCHEMA: portal.*  —  Reference / Master Data Layer                      ✅ LOADED  │    ║
║  │  ─────────────────────────────────────────────────────────────────────────────────── │    ║
║  │                                                                                      │    ║
║  │  FROM GOOGLE SHEETS CSV:                                                             │    ║
║  │  ┌──────────────────────┐  ┌──────────────────────┐                                  │    ║
║  │  │ portal.store         │  │ portal.kodemix       │                                  │    ║
║  │  │ (326 rows)           │  │ (5,464 rows)         │                                  │    ║
║  │  │ store locations      │  │ product SKU master   │                                  │    ║
║  │  │ branch, area, target │  │ code, tier, series   │                                  │    ║
║  │  └──────────────────────┘  └──────────────────────┘                                  │    ║
║  │  ┌──────────────────────┐  ┌──────────────────────┐                                  │    ║
║  │  │ portal.hpprsp        │  │ portal.stock_capacity│                                  │    ║
║  │  │ (935 rows)           │  │ (57 rows)            │                                  │    ║
║  │  │ product pricing      │  │ per-store capacity   │                                  │    ║
║  │  │ buy/tag/retail price │  │ max display/stock    │                                  │    ║
║  │  └──────────────────────┘  └──────────────────────┘                                  │    ║
║  └──────────────────────────────────────────────────────────────────────────────────────┘    ║
║           │                              │                                                   ║
║           │  ┌───────────────────────────┐│                                                   ║
║           │  │ JOIN & CLEAN              ││                                                   ║
║           │  │ • trim(lower()) all keys  ││                                                   ║
║           │  │ • store alias mapping     ││                                                   ║
║           │  │ • product enrichment      ││                                                   ║
║           │  │ • deduplication           ││                                                   ║
║           └──┤                           │┘                                                   ║
║              └─────────────┬─────────────┘                                                   ║
║                            ▼                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  SCHEMA: core.*  —  Normalized / Star Schema Layer                     ⬜ PLANNED  │    ║
║  │  ─────────────────────────────────────────────────────────────────────────────────── │    ║
║  │                                                                                      │    ║
║  │  DIMENSIONS (lookup tables):                 FACTS (measurements):                   │    ║
║  │  ┌──────────────────────┐                    ┌──────────────────────┐                │    ║
║  │  │ core.dim_product     │◄──── joins ───────►│ core.fact_sales      │                │    ║
║  │  │ (kodemix + hpprsp)   │                    │ (all 3 entities +    │                │    ║
║  │  │ unified product info │                    │  iseller, unified)   │                │    ║
║  │  └──────────────────────┘                    └──────────────────────┘                │    ║
║  │  ┌──────────────────────┐                    ┌──────────────────────┐                │    ║
║  │  │ core.dim_store       │◄──── joins ───────►│ core.fact_stock      │                │    ║
║  │  │ (store + capacity +  │                    │ (all 4 entities,     │                │    ║
║  │  │  alias mapping)      │                    │  unified)            │                │    ║
║  │  └──────────────────────┘                    └──────────────────────┘                │    ║
║  │  ┌──────────────────────┐                                                            │    ║
║  │  │ core.dim_warehouse   │                                                            │    ║
║  │  │ core.dim_date        │                                                            │    ║
║  │  └──────────────────────┘                                                            │    ║
║  └──────────────────────────────────────────────────────────────────────────────────────┘    ║
║                            │                                                                 ║
║                            │  Aggregate, filter, calculate                                   ║
║                            ▼                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  SCHEMA: mart.*  —  Reporting / Dashboard Layer                        ⬜ PLANNED  │    ║
║  │  ─────────────────────────────────────────────────────────────────────────────────── │    ║
║  │                                                                                      │    ║
║  │  ┌────────────────────────────┐  ┌────────────────────────────┐                      │    ║
║  │  │ mart.report_control_stock  │  │ mart.report_sales_daily    │                      │    ║
║  │  │ (stock health per store)   │  │ (daily sales by store)     │                      │    ║
║  │  └────────────────────────────┘  └────────────────────────────┘                      │    ║
║  │  ┌────────────────────────────┐  ┌────────────────────────────┐                      │    ║
║  │  │ mart.report_tier_summary   │  │ mart.report_depth_alert    │                      │    ║
║  │  │ (stock by tier)            │  │ (low stock warnings)       │                      │    ║
║  │  └────────────────────────────┘  └────────────────────────────┘                      │    ║
║  │  ┌────────────────────────────┐                                                      │    ║
║  │  │ mart.report_stock_capacity │                                                      │    ║
║  │  │ (stock vs max capacity)    │                                                      │    ║
║  │  └────────────────────────────┘                                                      │    ║
║  └──────────────────────────────────────────────────────────────────────────────────────┘    ║
║                            │                                                                 ║
╚════════════════════════════╪═════════════════════════════════════════════════════════════════╝
                             │
                             │  PostgREST API / Direct query
                             ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                              OUTPUT / CONSUMERS                                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐               ║
║   │   GOOGLE SHEETS     │   │   EMAIL REPORTS     │   │   AI AGENTS         │               ║
║   │   (Dashboards)      │   │   (Automated)       │   │   (OpenClaw)        │               ║
║   │                     │   │                     │   │                     │               ║
║   │  • Stock control    │   │  • Daily summary    │   │  Atlas (OPS)        │               ║
║   │  • Sales dashboard  │   │  • Low stock alerts │   │  Apollo (R&D)       │               ║
║   │  • Tier analysis    │   │  • Weekly reports   │   │  Iris (Coordinator) │               ║
║   └─────────────────────┘   └─────────────────────┘   └─────────────────────┘               ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

### Simplified Flow (one-liner per path)

```
Google Sheets CSV  ──(manual)──→  portal.*  ──────────────────────┐
                                                                    ├──→  core.*  ──→  mart.*  ──→  GSheets / Email / AI
Accurate API       ──(auto)───→  raw.accurate_*  ────────────────┘                                  Dashboards  Reports  Agents
iSeller CSV        ──(manual)──→  raw.iseller_sales  ────────────┘
```

### Feed Method Summary

| Source | Target Tables | Method | Frequency | Who/What Runs It |
|--------|---------------|--------|-----------|-----------------|
| Google Sheets | `portal.store`, `portal.kodemix`, `portal.hpprsp`, `portal.stock_capacity` | CSV export → DBeaver upload | When HQ updates data (rare) | Wayan (manual) |
| Accurate API (DDD) | `raw.accurate_stock_ddd`, `raw.accurate_sales_ddd` | Python script → REST API → INSERT | Daily (cron) | Atlas agent (automated) |
| Accurate API (LJBB) | `raw.accurate_stock_ljbb` | Python script → REST API → INSERT | Daily (cron) | Atlas agent (automated) |
| Accurate API (MBB) | `raw.accurate_stock_mbb`, `raw.accurate_sales_mbb` | Python script → REST API → INSERT | Daily (cron) | Atlas agent (automated) |
| Accurate API (UBB) | `raw.accurate_stock_ubb`, `raw.accurate_sales_ubb` | Python script → REST API → INSERT | Daily (cron) | Atlas agent (automated) |
| iSeller POS | `raw.iseller_sales` | CSV download → DBeaver upload | Weekly (manual) | Wayan (manual, until Mac Mini arrives) |
| System | `raw.load_history` | Auto-logged by every load script | Every load | Automatic |
| raw.* + portal.* | `core.dim_*`, `core.fact_*` | SQL transforms (views or INSERT) | After raw loads | Automatic (planned) |
| core.* | `mart.report_*` | SQL views (real-time) | On-demand query | Automatic (planned) |

---

## Naming Convention

We use a consistent naming pattern across all tables:

```
{schema}.{source}_{type}_{entity}

Example: raw.accurate_sales_mbb
         ↑      ↑       ↑     ↑
         │      │       │     └── MBB business entity
         │      │       └── sales data
         │      └── from Accurate Online API
         └── raw data layer
```

This means:
- All sales tables group together alphabetically
- All stock tables group together alphabetically
- You can instantly tell the source system and business entity from the name

---

## Security & Access Control

| User Role | What They Can Do | Who Uses It |
|-----------|-----------------|-------------|
| `openclaw_app` | Full access — read, write, delete, create | AI agents (Atlas, Apollo) |
| `nocodb_reader` | Read-only access to portal + raw data | Team members who need to view data |
| `postgrest_agent` | Write to raw/core, read everything | API-based agent access |
| `postgrest_anon` | Read-only on mart (reports) only | Public dashboards |

**All passwords stored locally** in `.env` file — never committed to code repositories.

---

## Data Integrity Safeguards

| Safeguard | What It Prevents |
|-----------|-----------------|
| **Primary keys** (BIGSERIAL `id`) | Every row has a unique identifier |
| **UNIQUE constraints** on sales | Can't accidentally insert the same invoice line twice |
| **NOT NULL constraints** on key columns | Can't insert rows with missing critical data (date, product code, quantity) |
| **Indexes** on frequently queried columns | Fast lookups by product code, date, store name |
| **load_history audit trail** | Complete record of every data load — when, how many rows, success or failure |
| **snapshot_date** on every row | Know exactly which day's data you're looking at |

---

## Current Status (8 Feb 2026 - 20:30 WIB)

| Component | Status | Details |
|-----------|--------|---------|
| VPS Server | ✅ Running | PostgreSQL 16.11 on Hostinger KVM 2 (76.13.194.120) |
| Portal data (master) | ✅ Loaded | 6,782 rows across 4 tables |
| **Raw stock data** | ✅ **COMPLETE** | **1,648,679 total rows** across 4 entities |
| - accurate_stock_ddd | ✅ Done | 1,376,832 records |
| - accurate_stock_ljbb | ✅ Done | 17,412 records |
| - accurate_stock_mbb | ✅ Done | 202,455 records |
| - accurate_stock_ubb | ✅ Done | 51,980 records |
| **Raw sales data** | ⏳ **IN PROGRESS** | Historical 2022-2026 being loaded (workaround method) |
| - accurate_sales_ddd | ⏳ 61% | ~59,000/96,768 rows inserted |
| - accurate_sales_mbb | ⏳ 14% | ~6,000/41,925 rows inserted |
| - accurate_sales_ubb | ⏳ Started | Just begun |
| Daily automation (cron) | ✅ Set up | Stock 03:00, Sales 05:00 WIB — starts tomorrow |
| Core schema | ⬜ Pending | Build after raw data complete |
| Mart views | ⬜ Pending | Build after core is done |
| Backups | ✅ Running | Daily at 02:00, 7-day retention |

---

## What's Next (Immediate)

1. **✅ DONE** — Port Python scripts to VPS PostgreSQL
2. **✅ DONE** — Test first stock pull (all 4 entities complete!)
3. **⏳ IN PROGRESS** — Bulk-load 2022-2026 sales data (running on VPS, ~3 hours remaining)
4. **✅ DONE** — Set up daily cron (Stock 03:00, Sales 05:00 WIB, backup 02:00)
5. **⏳ NEXT** — Wait for historical sales to complete, then build core schema
6. **⏳ NEXT** — Build mart views for Control Stock PoC
7. **⏳ NEXT** — Set up Iris → Atlas monitoring via Telegram

---

## Active Processes on VPS (Running 24/7)

**DB VPS (76.13.194.120):**
- Historical sales pull: DDD, MBB, UBB (2022-2026) — ETA ~3 hours
- Cron jobs start: Tomorrow 02:00 (backup), 03:00 (stock), 05:00 (sales)

**Agent VPS (76.13.194.103):**
- OpenClaw Gateway running
- Iris (main agent) configured — Telegram pending connection
- Atlas (ops agent) will monitor cron jobs once Telegram connected

**Local (Wayan's PC):**
- Currently rate-limited (Anthropic), resumes in ~1.5 hours
- All heavy processing moved to VPS — safe to shutdown

---

## Why This Matters

**Without this database**: Every analysis requires manually logging into Accurate, exporting Excel files, copy-pasting into Google Sheets, and hand-building reports. This takes hours per report, and the data is already stale by the time you finish.

**With this database**: AI agents pull fresh data every day automatically. Reports generate themselves. Alerts fire when stock is low. All data is in one place, properly structured, historically tracked, and ready for any analysis — past, present, or future.

---

*Document maintained by Wayan (Database & AI Team). For technical details, see `04-database-schema-reference.md`.*
