# OpenClaw OPS — Database Schema Reference

> **Database**: `openclaw_ops` on PostgreSQL 16.11 + pgvector
> **VPS**: `76.13.194.120` (ssh postgresql)
> **Access**: DBeaver via SSH tunnel (see 00-SETUP-GUIDE.md for connection guide)
> **Last updated**: 8 Feb 2026 (Session 9 — table rename + ALTER migration)

---

## TABLE OF CONTENTS

1. [Schema Overview](#1-schema-overview)
2. [Naming Convention](#2-naming-convention)
3. [Portal Schema — Reference/Master Data](#3-portal-schema)
4. [Raw Schema — Staging/Transactional Data](#4-raw-schema)
5. [Core Schema — Normalized Data (NOT YET BUILT)](#5-core-schema)
6. [Mart Schema — Reporting Views (NOT YET BUILT)](#6-mart-schema)
7. [Database Users & Permissions](#7-database-users--permissions)
8. [Data Flow](#8-data-flow)
9. [Indexes](#9-indexes)
10. [SKU Code Join Keys](#10-sku-code-join-keys)
11. [Store Name Join Keys](#11-store-name-join-keys)
12. [Maintenance Queries](#12-maintenance-queries)

---

## 1. SCHEMA OVERVIEW

```
openclaw_ops
├── portal.*   ← Reference/master data (from Google Sheets CSVs)     ✅ LOADED (6,782 rows)
├── raw.*      ← Staging data (from Accurate API + iSeller CSV)      ✅ DESIGNED, ⬜ EMPTY
├── core.*     ← Normalized star schema (dim_ + fact_ tables)        ⬜ NOT BUILT
└── mart.*     ← Reporting views (denormalized, dashboard-ready)     ⬜ NOT BUILT
```

| Schema | Purpose | Source | Status | Total Rows |
|--------|---------|--------|--------|------------|
| `portal` | Company master data (products, stores, pricing, capacity) | Google Sheets CSV export | ✅ Loaded | 6,782 |
| `raw` | Raw transactional data, daily snapshots, append-only | Accurate Online API + iSeller CSV | ✅ Designed | 0 (awaiting data) |
| `core` | Normalized star schema with proper foreign keys | Derived from portal + raw | ⬜ Not built | — |
| `mart` | Denormalized reporting views, flat & readable | Derived from core | ⬜ Not built | — |

---

## 2. NAMING CONVENTION

**Pattern**: `{schema}.{source}_{type}_{entity}`

```
       schema    source    type    entity
         ↓        ↓        ↓        ↓
       raw  .  accurate _ sales  _ mbb
```

| Level | What It Tells You | Examples |
|-------|-------------------|----------|
| Schema | Data layer (raw/core/mart) | `raw.*`, `core.*`, `mart.*` |
| Source | Where data came from | `accurate_`, `iseller_` |
| Type | What kind of data | `sales_`, `stock_` |
| Entity | Which business unit | `ddd`, `mbb`, `ubb`, `ljbb` |

**Why this works**:
- Schema already = layer, so no need to repeat `raw_` in table name
- Alphabetical grouping: all `accurate_sales_*` cluster together
- Scales: new source = `raw.tokopedia_sales`, `raw.shopee_orders`
- `portal.*` — schema IS the source, no prefix needed

---

## 3. PORTAL SCHEMA

> **Source**: Google Sheets "Portal Data" CSV exports
> **Update frequency**: When HQ updates master data (infrequent)
> **Loaded**: 8 Feb 2026, batch `portal_init_20260208`

### 3.1 portal.store (326 rows)

Store/branch master data — all Zuma retail locations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `nama_department_old` | text | YES | Legacy department name |
| `nama_accurate` | text | YES | Store name in Accurate Online (ERP) |
| `nama_iseller` | text | YES | Store name in iSeller (POS) |
| `branch` | text | YES | Branch region (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali) |
| `area` | text | YES | Geographic area within branch |
| `category` | text | YES | Store category (RETAIL, NON-RETAIL, EVENT) |
| `stock_filter` | text | YES | Stock filter grouping |
| `as_name` | text | YES | Area Supervisor name |
| `bm_name` | text | YES | Branch Manager name |
| `max_display` | text | YES | Maximum display pairs |
| `max_stock` | text | YES | Maximum stock pairs |
| `monthly_target` | text | YES | Monthly sales target |
| `storage` | text | YES | Storage capacity |

**Notes**: No primary key constraint. `nama_accurate` is the de facto unique identifier.

---

### 3.2 portal.kodemix (5,464 rows)

Product SKU master — every product variation (kode mix = SKU code + size).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `kode_mix_size` | text | **NOT NULL** | Full SKU code with size (e.g., "M1CA01-40") |
| `kode_mix` | text | **NOT NULL** | SKU code without size (e.g., "M1CA01") |
| `version` | text | YES | Product version |
| `kode_besar` | text | **NOT NULL** | Parent product code (= API `kode_produk`) |
| `kode` | text | YES | Article code (= `kode_besar` minus last 3 chars) |
| `tipe` | text | YES | Product type |
| `nama_barang` | text | YES | Product name |
| `nama_variant` | text | YES | Variant name |
| `ukuran` | text | YES | Size |
| `tier_lama` | text | YES | Old tier classification |
| `gender` | text | YES | Gender (LADIES, MEN, BABY, BOYS, GIRLS) |
| `seri` | text | YES | Series code |
| `series` | text | YES | Series name (SLIDE, AIRMOVE, STRIPE, LUNA, etc.) |
| `v` | text | YES | Version flag |
| `totalpairs_hook` | text | YES | Total pairs per hook |
| `assortment_lama` | text | YES | Old assortment grouping |
| `gender_2` | text | YES | Secondary gender classification |
| `status` | text | YES | Product status (ACTIVE, DISCONTINUED, etc.) |
| `tier_baru` | text | YES | New tier classification (TIER 1-8) |
| `article` | text | YES | Article code |
| `size` | text | YES | Numeric size |
| `color` | text | YES | Color name |
| `assortment` | text | YES | Current assortment grouping |
| `count_by_assortment` | text | YES | Count within assortment |
| `group_warna` | text | YES | Color group |
| `no_urut` | text | YES | Sort order |
| `id` | serial | **NOT NULL** | Auto-increment primary key |

**Primary key**: `id` (serial)
**Unique-ish**: `kode_mix_size` (should be unique, no constraint enforced)

---

### 3.3 portal.hpprsp (935 rows)

Product pricing & RSP (Retail Selling Price) data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `no` | text | YES | Row number |
| `kode` | text | **NOT NULL** (PK) | Product code (unique, = article code) |
| `nama_barang` | text | YES | Product name |
| `tipe` | text | YES | Product type |
| `series` | text | YES | Product series |
| `gender` | text | YES | Gender |
| `tier` | text | YES | Tier classification |
| `season` | text | YES | Season/launch period |
| `launching_sales` | text | YES | Launch sales date |
| `limit_age` | text | YES | Product age limit |
| `assortment` | text | YES | Assortment grouping |
| `ukuran` | text | YES | Size range |
| `status` | text | YES | Product status |
| `v` | text | YES | Version |
| `supplier` | text | YES | Supplier name |
| `harga_beli` | numeric | YES | Purchase price (Rp) |
| `price_taq` | numeric | YES | Tag price (Rp) |
| `rsp` | numeric | YES | Retail selling price (Rp) |
| `mg_disney` | text | YES | Disney licensing flag |

**Primary key**: `kode`

---

### 3.4 portal.stock_capacity (57 rows)

Store stock capacity limits per location.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `stock_location` | text | **NOT NULL** (PK) | Store/location identifier |
| `branch` | text | YES | Branch region |
| `area` | text | YES | Area |
| `category` | text | YES | Store category |
| `as_name` | text | YES | Area Supervisor |
| `bm_name` | text | YES | Branch Manager |
| `max_display` | integer | YES | Maximum display pairs |
| `max_stock` | integer | YES | Maximum total stock pairs |
| `storage` | integer | YES | Storage capacity pairs |

**Primary key**: `stock_location`

---

## 4. RAW SCHEMA

> **Source**: Accurate Online API (stock + sales) + iSeller CSV (marketplace sales)
> **Update frequency**: Daily (automated via Atlas agent, once pipeline is built)
> **Design**: Append-only with `snapshot_date` — each day's data is a new batch
> **Status**: ✅ Tables created & altered (8 Feb 2026), ⬜ 0 rows (awaiting first API pull)

### 4.1 Stock Tables (4 tables, identical structure)

Tables: `raw.accurate_stock_ddd`, `raw.accurate_stock_ljbb`, `raw.accurate_stock_mbb`, `raw.accurate_stock_ubb`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | bigint | **NOT NULL** (PK) | `nextval(...)` | Auto-increment primary key |
| `kode_barang` | text | **NOT NULL** | — | Product code (= `portal.kodemix.kode_besar`) |
| `nama_barang` | text | YES | — | Product name |
| `nama_gudang` | text | YES | — | Warehouse/location name |
| `kuantitas` | **integer** | **NOT NULL** | — | Stock quantity (whole numbers) |
| `unit_price` | numeric(15,2) | YES | — | Master selling price from API |
| `vendor_price` | numeric(15,2) | YES | — | Purchase/vendor price from API |
| `snapshot_date` | date | **NOT NULL** | — | Date of this snapshot |
| `loaded_at` | timestamptz | **NOT NULL** | `now()` | When data was loaded |
| `load_batch_id` | text | YES | — | Batch identifier for ETL tracking |

**Primary key**: `id` (BIGSERIAL)
**Indexes**: `kode_barang`, `snapshot_date`
**Update pattern**: `DELETE WHERE snapshot_date = today` then `INSERT` (daily snapshot replacement)

**Entity mapping:**
| Table | Accurate Entity | Description |
|-------|----------------|-------------|
| `raw.accurate_stock_ddd` | DDD | DDD administrative entity stock |
| `raw.accurate_stock_ljbb` | LJBB | LJBB administrative entity stock |
| `raw.accurate_stock_mbb` | MBB | MBB administrative entity stock |
| `raw.accurate_stock_ubb` | UBB | UBB administrative entity stock |

---

### 4.2 Sales Tables (3 tables, identical structure)

Tables: `raw.accurate_sales_ddd`, `raw.accurate_sales_mbb`, `raw.accurate_sales_ubb`

> **Note**: No `raw.accurate_sales_ljbb` — LJBB has no sales data (only stock + finance).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | bigint | **NOT NULL** (PK) | `nextval(...)` | Auto-increment primary key |
| `tanggal` | date | **NOT NULL** | — | Transaction date |
| `nama_departemen` | text | YES | — | Department/store name (short form) |
| `nama_pelanggan` | text | YES | — | Customer name |
| `nomor_invoice` | text | YES | — | Invoice number |
| `kode_produk` | text | **NOT NULL** | — | Product code (= `portal.kodemix.kode_besar`) |
| `nama_barang` | text | YES | — | Product name |
| `satuan` | text | YES | — | Unit of measure |
| `kuantitas` | numeric | **NOT NULL** | — | Quantity sold |
| `harga_satuan` | numeric | YES | — | Unit price (Rp) |
| `total_harga` | numeric | YES | — | Total price (Rp) |
| `bpp` | numeric | YES | `0` | Cost of goods (Rp) |
| `nama_gudang` | text | YES | — | Warehouse that fulfilled the sale |
| `vendor_price` | numeric(15,2) | YES | — | Purchase price for margin analysis |
| `dpp_amount` | numeric(15,2) | YES | — | Tax base amount (DPP) |
| `tax_amount` | numeric(15,2) | YES | — | PPN tax amount |
| `snapshot_date` | date | **NOT NULL** | — | Date of this data snapshot |
| `loaded_at` | timestamptz | **NOT NULL** | `now()` | When data was loaded |
| `load_batch_id` | text | YES | — | Batch identifier |

**Primary key**: `id` (BIGSERIAL)
**Unique constraint**: `(nomor_invoice, kode_produk, tanggal, snapshot_date)` — prevents duplicate invoice line items
**Indexes**: `kode_produk`, `tanggal`, `snapshot_date`, `load_batch_id`, `nama_gudang`
**Update pattern**: `INSERT ... ON CONFLICT DO UPDATE` (upsert on unique constraint)

---

### 4.3 raw.iseller_sales (0 rows)

iSeller POS/marketplace sales data — manual CSV upload by Wayan.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `order_number` | text | YES | Order ID |
| `order_date` | timestamptz | YES | Order timestamp |
| `customer_name` | text | YES | Customer |
| `customer_email` | text | YES | Customer email |
| `customer_phone` | text | YES | Customer phone |
| `payment_method` | text | YES | Payment method |
| `payment_status` | text | YES | Payment status |
| `fulfillment_status` | text | YES | Fulfillment status |
| `shipping_method` | text | YES | Shipping method |
| `shipping_address` | text | YES | Delivery address |
| `shipping_city` | text | YES | City |
| `shipping_province` | text | YES | Province |
| `shipping_postal_code` | text | YES | Postal code |
| `item_sku` | text | YES | Product SKU |
| `item_name` | text | YES | Product name |
| `item_variant` | text | YES | Variant |
| `item_quantity` | numeric | YES | Quantity |
| `item_price` | numeric | YES | Unit price |
| `item_discount` | numeric | YES | Discount amount |
| `item_total` | numeric | YES | Line total |
| `order_subtotal` | numeric | YES | Order subtotal |
| `order_discount` | numeric | YES | Order-level discount |
| `order_shipping` | numeric | YES | Shipping cost |
| `order_tax` | numeric | YES | Tax amount |
| `order_total` | numeric | YES | Grand total |
| `channel` | text | YES | Sales channel (Shopee, Tokopedia, etc.) |
| `notes` | text | YES | Order notes |
| `snapshot_date` | date | YES | Snapshot date |
| `loaded_at` | timestamptz | YES | Load timestamp |
| `load_batch_id` | text | YES | Batch ID |

**30+ columns** matching iSeller CSV export format.

---

### 4.4 raw.load_history (4 rows)

ETL audit trail — tracks every data load operation.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | serial | **NOT NULL** (PK) | Auto-increment ID |
| `loaded_at` | timestamptz | YES | When the load happened |
| `source` | text | YES | Data source (e.g., "portal_csv", "accurate_api") |
| `entity` | text | YES | Entity loaded (e.g., "store", "accurate_stock_ddd") |
| `data_type` | text | YES | Type (e.g., "reference", "stock", "sales") |
| `batch_id` | text | YES | Batch identifier (e.g., "portal_init_20260208") |
| `date_from` | date | YES | Data range start |
| `date_to` | date | YES | Data range end |
| `rows_loaded` | integer | YES | Number of rows loaded |
| `status` | text | YES | Load status ("success", "failed", "partial") |
| `error_message` | text | YES | Error details if failed |

**Primary key**: `id`
**Current data**: 4 rows from initial portal CSV import.

---

## 5. CORE SCHEMA (NOT YET BUILT)

> **Purpose**: Normalized star schema — cleaned, deduplicated, joined across portal + raw.
> **When**: After portal & raw pipelines are stable.

Planned tables:
| Table | Type | Description |
|-------|------|-------------|
| `core.dim_product` | Dimension | Unified product master (joined from kodemix + hpprsp) |
| `core.dim_store` | Dimension | Unified store master (from portal.store + stock_capacity) with alias mapping |
| `core.dim_warehouse` | Dimension | Warehouse/entity master |
| `core.dim_date` | Dimension | Date dimension table |
| `core.fact_stock` | Fact | Daily stock snapshots (union of all `raw.accurate_stock_*`) |
| `core.fact_sales` | Fact | Sales transactions (union of all `raw.accurate_sales_*` + iseller_sales) |

**Key join rules for core tables**:
- Product joins: use `trim(lower(kode_besar))` or `trim(lower(kode_produk))` — NEVER kodemix/kodemix_size
- Store joins: use `trim(lower(nama_accurate))` + alias mapping table for spelling variants
- See sections 10 & 11 for details

---

## 6. MART SCHEMA (NOT YET BUILT)

> **Purpose**: Pre-built views for specific use cases — ready-to-consume data.
> **When**: After core.* is built.

Planned views:
| View | Description |
|------|-------------|
| `mart.report_control_stock` | Daily stock control dashboard (FF%, FB%, depth) |
| `mart.report_tier_summary` | Stock summary by tier (TIER 1-8) |
| `mart.report_depth_alert` | Items below minimum stock depth threshold |
| `mart.report_sales_daily` | Daily sales summary by store/product |
| `mart.report_stock_vs_capacity` | Current stock vs max capacity per location |

---

## 7. DATABASE USERS & PERMISSIONS

| User | Can Login | Permissions | Used By |
|------|-----------|-------------|---------|
| `openclaw_app` | YES | **OWNER** of all 4 schemas. Full CRUD. | Atlas, Apollo agents (direct psql) |
| `nocodb_reader` | YES | SELECT only on portal + raw schemas. | Legacy. Can repurpose for read-only team access. |
| `postgrest_auth` | YES | Authenticator role (switches to agent/anon) | PostgREST service |
| `postgrest_anon` | NO | SELECT on `mart` schema only | Unauthenticated API requests |
| `postgrest_agent` | NO | SELECT/INSERT/UPDATE on `raw` + `core`, SELECT on `mart` | Authenticated agent API requests |

**Password locations**: All in local `.env` file (NEVER in .md files).

---

## 8. DATA FLOW

```
Google Sheets (Portal CSVs)
  ├── portal_store.csv       ──→  portal.store (326 rows)
  ├── portal_kodemix.csv     ──→  portal.kodemix (5,464 rows)
  ├── portal_hpprsp.csv      ──→  portal.hpprsp (935 rows)
  └── portal_stock.csv       ──→  portal.stock_capacity (57 rows)

Accurate Online API (per entity)
  ├── DDD stock report       ──→  raw.accurate_stock_ddd
  ├── DDD sales invoices     ──→  raw.accurate_sales_ddd
  ├── LJBB stock report      ──→  raw.accurate_stock_ljbb     (LJBB has NO sales)
  ├── MBB stock/sales        ──→  raw.accurate_stock_mbb / raw.accurate_sales_mbb
  └── UBB stock/sales        ──→  raw.accurate_stock_ubb / raw.accurate_sales_ubb

iSeller CSV (manual upload)
  └── order-detail-*.csv     ──→  raw.iseller_sales

All loads tracked in          ──→  raw.load_history

FUTURE:
  portal.* + raw.*            ──→  core.* (normalized joins)
  core.*                      ──→  mart.* (reporting views)
  mart.*                      ──→  GSheet dashboards + Email reports
```

---

## 9. INDEXES

### Raw Stock Tables (`raw.accurate_stock_*`)

| Index Name | Column | All 4 tables? |
|------------|--------|---------------|
| `accurate_stock_{entity}_pkey` | `id` (PK) | YES |
| `idx_accurate_stock_{entity}_kode` | `kode_barang` | YES |
| `idx_accurate_stock_{entity}_snapshot` | `snapshot_date` | YES |

### Raw Sales Tables (`raw.accurate_sales_*`)

| Index Name | Column | All 3 tables? |
|------------|--------|---------------|
| `accurate_sales_{entity}_pkey` | `id` (PK) | YES |
| `uq_accurate_sales_{entity}` | `(nomor_invoice, kode_produk, tanggal, snapshot_date)` UNIQUE | YES |
| `idx_accurate_sales_{entity}_kode` | `kode_produk` | YES |
| `idx_accurate_sales_{entity}_tanggal` | `tanggal` | YES |
| `idx_accurate_sales_{entity}_snapshot` | `snapshot_date` | YES |
| `idx_accurate_sales_{entity}_batch` | `load_batch_id` | YES |
| `idx_accurate_sales_{entity}_gudang` | `nama_gudang` | YES |

### Other Tables

| Table | Indexed Columns |
|-------|-----------------|
| `raw.iseller_sales` | `item_sku`, `order_date`, `snapshot_date` |
| `raw.load_history` | `id` (PK), `batch_id` |
| `portal.kodemix` | `id` (PK), `kode_mix_size` (NOT NULL), `kode_mix` (NOT NULL) |
| `portal.hpprsp` | `kode` (PK) |
| `portal.stock_capacity` | `stock_location` (PK) |

---

## 10. SKU CODE JOIN KEYS

> **CRITICAL**: Never use `kodemix` or `kodemix_size` as join keys — they only exist in GSheet, not in Accurate or iSeller.

### Proven mappings (verified with real data):

```
API kode_produk / kode_barang  =  portal.kodemix.kode_besar   (100% match, size-level)
Strip last 3 chars             =  portal.kodemix.kode          (article-level)
                               =  portal.hpprsp.kode           (99% match — 932/935)
```

### Example:
```
API code:     L1CAV222Z38        (size-level SKU)
kode_besar:   L1CAV222Z38        ← exact match in portal.kodemix
Article:      L1CAV222            ← strip last 3 chars (Z38 = size)
kode:         L1CAV222            ← matches portal.kodemix.kode (6 rows, all sizes)
hpprsp.kode:  L1CAV222            ← matches portal.hpprsp.kode (1 row, pricing)
```

### SQL join pattern:
```sql
-- Size-level join (1:1)
FROM raw.accurate_sales_ddd s
JOIN portal.kodemix k ON trim(lower(s.kode_produk)) = trim(lower(k.kode_besar))

-- Article-level join (1:many sizes)
FROM raw.accurate_sales_ddd s
JOIN portal.hpprsp h ON trim(lower(left(s.kode_produk, length(s.kode_produk) - 3))) = trim(lower(h.kode))
```

---

## 11. STORE NAME JOIN KEYS

Store names have THREE types of mismatches between API data and portal master data:

| Type | Example | Fix |
|------|---------|-----|
| **A — Case difference** | `'ZUMA GALAXY MALL'` vs `'Zuma Galaxy Mall'` | `trim(lower())` |
| **B — Abbreviation** | `'Zuma MOI'` vs `'ZUMA MALL OF INDONESIA (MOI)'` | Alias mapping table |
| **C — Short vs full name** | `'Zuma Mega Mall'` vs `'Zuma Mega Mall Manado'` | Alias mapping table |

**For `core.dim_store` later**: use `trim(lower(nama_accurate))` as store_key + build alias/mapping table for Types B & C.

---

## 12. MAINTENANCE QUERIES

### Check table sizes
```sql
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
       n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname IN ('portal', 'raw', 'core', 'mart')
ORDER BY schemaname, tablename;
```

### Check recent loads
```sql
SELECT * FROM raw.load_history ORDER BY loaded_at DESC LIMIT 10;
```

### Check data freshness per raw table
```sql
SELECT 'raw.accurate_stock_ddd' as table_name, MAX(snapshot_date) as latest FROM raw.accurate_stock_ddd
UNION ALL
SELECT 'raw.accurate_stock_ljbb', MAX(snapshot_date) FROM raw.accurate_stock_ljbb
UNION ALL
SELECT 'raw.accurate_stock_mbb', MAX(snapshot_date) FROM raw.accurate_stock_mbb
UNION ALL
SELECT 'raw.accurate_stock_ubb', MAX(snapshot_date) FROM raw.accurate_stock_ubb
UNION ALL
SELECT 'raw.accurate_sales_ddd', MAX(snapshot_date) FROM raw.accurate_sales_ddd
UNION ALL
SELECT 'raw.accurate_sales_mbb', MAX(snapshot_date) FROM raw.accurate_sales_mbb
UNION ALL
SELECT 'raw.accurate_sales_ubb', MAX(snapshot_date) FROM raw.accurate_sales_ubb
UNION ALL
SELECT 'raw.iseller_sales', MAX(snapshot_date) FROM raw.iseller_sales;
```

### Verify portal data integrity
```sql
SELECT 'kodemix missing kode_mix' as check, COUNT(*) as issues FROM portal.kodemix WHERE kode_mix IS NULL
UNION ALL
SELECT 'hpprsp missing kode', COUNT(*) FROM portal.hpprsp WHERE kode IS NULL
UNION ALL
SELECT 'stock_capacity missing location', COUNT(*) FROM portal.stock_capacity WHERE stock_location IS NULL;
```

---

## CHANGELOG

| Date | Change |
|------|--------|
| 8 Feb 2026 (Session 7) | Initial schema creation — portal.* loaded, raw.* designed |
| 8 Feb 2026 (Session 9) | **RENAME**: `raw.ddd_sales` → `raw.accurate_sales_ddd` (all 7 tables renamed to `{source}_{type}_{entity}` convention). **ADD**: `id BIGSERIAL PK` to all 7 tables. **ADD**: 4 new sales columns (`nama_gudang`, `vendor_price`, `dpp_amount`, `tax_amount`). **ADD**: 2 new stock columns (`unit_price`, `vendor_price`). **CHANGE**: stock `kuantitas` from numeric → integer. **ADD**: UNIQUE constraint on sales `(nomor_invoice, kode_produk, tanggal, snapshot_date)`. **ADD**: missing indexes for consistency across all tables. **DROP**: `raw.whs_stock`, `raw.whs_sales` (no WHS entity in API). |

---

*This document is the single source of truth for the openclaw_ops database structure. Update it whenever schema changes are made.*
