-- ============================================================
-- CORE SCHEMA - As VIEWS (Real-time, no materialization)
-- Uses actual columns from portal schema
-- ============================================================

-- Drop old tables if exist
DROP TABLE IF EXISTS core.fact_sales CASCADE;
DROP TABLE IF EXISTS core.fact_stock CASCADE;
DROP TABLE IF EXISTS core.dim_product CASCADE;
DROP TABLE IF EXISTS core.dim_store CASCADE;
DROP TABLE IF EXISTS core.dim_warehouse CASCADE;
DROP TABLE IF EXISTS core.dim_date CASCADE;

-- ============================================================
-- DIMENSION VIEWS
-- ============================================================

-- dim_product: Unified product master
-- Joins kodemix + hpprsp on kode (article code)
CREATE OR REPLACE VIEW core.dim_product AS
WITH product_base AS (
    SELECT DISTINCT ON (TRIM(LOWER(k.kode_besar)))
        TRIM(LOWER(k.kode_besar)) as kode_besar,
        TRIM(LOWER(k.kode)) as kode,
        k.nama_barang,
        k.tipe,
        k.series,
        k.gender,
        COALESCE(k.tier_baru, k.tier_lama) as tier,
        k.ukuran,
        k.color,
        k.assortment,
        k.status,
        h.season,
        h.supplier,
        h.harga_beli,
        h.price_taq,
        h.rsp
    FROM portal.kodemix k
    LEFT JOIN portal.hpprsp h ON TRIM(LOWER(k.kode)) = TRIM(LOWER(h.kode))
    ORDER BY TRIM(LOWER(k.kode_besar)), k.no_urut
)
SELECT * FROM product_base;

-- dim_store: Unified store master
CREATE OR REPLACE VIEW core.dim_store AS
WITH store_base AS (
    SELECT DISTINCT ON (TRIM(LOWER(COALESCE(NULLIF(nama_accurate,''), nama_department_old))))
        TRIM(LOWER(COALESCE(NULLIF(nama_accurate,''), nama_department_old))) as store_name,
        nama_department_old,
        nama_accurate,
        nama_iseller,
        branch,
        area,
        category,
        max_display,
        max_stock,
        storage,
        monthly_target
    FROM portal.store
    ORDER BY TRIM(LOWER(COALESCE(NULLIF(nama_accurate,''), nama_department_old))), 
             monthly_target DESC NULLS LAST
)
SELECT * FROM store_base;

-- dim_warehouse: Warehouse lookup
CREATE OR REPLACE VIEW core.dim_warehouse AS
SELECT * FROM (VALUES 
    ('DDD', 'Dream Dare Discover (HQ)', 'Headquarters'),
    ('LJBB', 'Lembaga Jaminan Berbasis Bina', 'Branch'),
    ('MBB', 'Maju Bersama Berdikari', 'Branch'),
    ('UBB', 'Usaha Bersama Berdikari', 'Branch')
) AS t(warehouse_code, warehouse_name, entity_type);

-- dim_date: Calendar dimension
CREATE OR REPLACE VIEW core.dim_date AS
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER as date_key,
    d as full_date,
    EXTRACT(YEAR FROM d) as year,
    EXTRACT(QUARTER FROM d) as quarter,
    EXTRACT(MONTH FROM d) as month,
    TO_CHAR(d, 'Month') as month_name,
    EXTRACT(WEEK FROM d) as week,
    EXTRACT(DAY FROM d) as day,
    TO_CHAR(d, 'Day') as day_name,
    EXTRACT(ISODOW FROM d) > 5 as is_weekend,
    FALSE as is_holiday
FROM generate_series('2022-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- ============================================================
-- FACT VIEWS (Latest snapshot only)
-- ============================================================

-- fact_sales_ddd: DDD sales with joins
CREATE OR REPLACE VIEW core.fact_sales_ddd AS
SELECT 
    s.nomor_invoice,
    s.tanggal as transaction_date,
    TO_CHAR(s.tanggal, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_produk)) as kode_produk_raw,
    p.kode_besar as kode_produk_clean,
    TRIM(LOWER(s.nama_departemen)) as store_name_raw,
    st.store_name as store_name_clean,
    s.nama_barang,
    s.kuantitas::INTEGER as quantity,
    s.harga_satuan as unit_price,
    s.total_harga as total_amount,
    s.bpp as cost_of_goods,
    s.vendor_price,
    s.dpp_amount,
    s.tax_amount,
    s.snapshot_date,
    s.loaded_at
FROM raw.accurate_sales_ddd s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_produk)) = p.kode_besar
LEFT JOIN core.dim_store st ON TRIM(LOWER(s.nama_departemen)) = st.store_name
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_sales_ddd);

-- fact_sales_mbb: MBB sales with joins
CREATE OR REPLACE VIEW core.fact_sales_mbb AS
SELECT 
    s.nomor_invoice,
    s.tanggal as transaction_date,
    TO_CHAR(s.tanggal, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_produk)) as kode_produk_raw,
    p.kode_besar as kode_produk_clean,
    TRIM(LOWER(s.nama_departemen)) as store_name_raw,
    st.store_name as store_name_clean,
    s.nama_barang,
    s.kuantitas::INTEGER as quantity,
    s.harga_satuan as unit_price,
    s.total_harga as total_amount,
    s.bpp as cost_of_goods,
    s.vendor_price,
    s.dpp_amount,
    s.tax_amount,
    s.snapshot_date,
    s.loaded_at
FROM raw.accurate_sales_mbb s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_produk)) = p.kode_besar
LEFT JOIN core.dim_store st ON TRIM(LOWER(s.nama_departemen)) = st.store_name
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_sales_mbb);

-- fact_sales_ubb: UBB sales with joins
CREATE OR REPLACE VIEW core.fact_sales_ubb AS
SELECT 
    s.nomor_invoice,
    s.tanggal as transaction_date,
    TO_CHAR(s.tanggal, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_produk)) as kode_produk_raw,
    p.kode_besar as kode_produk_clean,
    TRIM(LOWER(s.nama_departemen)) as store_name_raw,
    st.store_name as store_name_clean,
    s.nama_barang,
    s.kuantitas::INTEGER as quantity,
    s.harga_satuan as unit_price,
    s.total_harga as total_amount,
    s.bpp as cost_of_goods,
    s.vendor_price,
    s.dpp_amount,
    s.tax_amount,
    s.snapshot_date,
    s.loaded_at
FROM raw.accurate_sales_ubb s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_produk)) = p.kode_besar
LEFT JOIN core.dim_store st ON TRIM(LOWER(s.nama_departemen)) = st.store_name
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_sales_ubb);

-- fact_stock_ddd: DDD stock with joins
CREATE OR REPLACE VIEW core.fact_stock_ddd AS
SELECT 
    s.snapshot_date,
    TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_barang)) as kode_barang_raw,
    p.kode_besar as kode_barang_clean,
    s.nama_gudang,
    s.kuantitas::INTEGER as quantity,
    s.unit_price,
    s.vendor_price,
    s.loaded_at
FROM raw.accurate_stock_ddd s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_ddd);

-- fact_stock_ljbb: LJBB stock with joins
CREATE OR REPLACE VIEW core.fact_stock_ljbb AS
SELECT 
    s.snapshot_date,
    TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_barang)) as kode_barang_raw,
    p.kode_besar as kode_barang_clean,
    s.nama_gudang,
    s.kuantitas::INTEGER as quantity,
    s.unit_price,
    s.vendor_price,
    s.loaded_at
FROM raw.accurate_stock_ljbb s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_ljbb);

-- fact_stock_mbb: MBB stock with joins
CREATE OR REPLACE VIEW core.fact_stock_mbb AS
SELECT 
    s.snapshot_date,
    TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_barang)) as kode_barang_raw,
    p.kode_besar as kode_barang_clean,
    s.nama_gudang,
    s.kuantitas::INTEGER as quantity,
    s.unit_price,
    s.vendor_price,
    s.loaded_at
FROM raw.accurate_stock_mbb s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_mbb);

-- fact_stock_ubb: UBB stock with joins
CREATE OR REPLACE VIEW core.fact_stock_ubb AS
SELECT 
    s.snapshot_date,
    TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER as date_key,
    TRIM(LOWER(s.kode_barang)) as kode_barang_raw,
    p.kode_besar as kode_barang_clean,
    s.nama_gudang,
    s.kuantitas::INTEGER as quantity,
    s.unit_price,
    s.vendor_price,
    s.loaded_at
FROM raw.accurate_stock_ubb s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_ubb);

-- ============================================================
-- UNIFIED FACT VIEWS (All entities combined)
-- ============================================================

-- fact_sales_all: All sales entities combined
CREATE OR REPLACE VIEW core.fact_sales_all AS
SELECT 'DDD' as entity, * FROM core.fact_sales_ddd
UNION ALL
SELECT 'MBB' as entity, * FROM core.fact_sales_mbb
UNION ALL
SELECT 'UBB' as entity, * FROM core.fact_sales_ubb;

-- fact_stock_all: All stock entities combined
CREATE OR REPLACE VIEW core.fact_stock_all AS
SELECT 'DDD' as entity, * FROM core.fact_stock_ddd
UNION ALL
SELECT 'LJBB' as entity, * FROM core.fact_stock_ljbb
UNION ALL
SELECT 'MBB' as entity, * FROM core.fact_stock_mbb
UNION ALL
SELECT 'UBB' as entity, * FROM core.fact_stock_ubb;
