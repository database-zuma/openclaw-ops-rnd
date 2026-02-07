# NOTION-SKILLS.md — Konvensi Notion untuk Apollo 🎯

Kamu adalah **worker R&D**. Kamu update status task kamu sendiri di Notion setelah setiap job.

## Database IDs

| Database | ID | Akses Kamu |
|----------|----|------------|
| **Tasks** | `30031616-a0d5-81ac-86f0-e108677a6d0a` | Baca + Update (task milik kamu saja) |
| **Projects** | `30031616-a0d5-8194-96b3-d09fbf4da2cc` | Baca saja |

## API Info

| Property | Value |
|----------|-------|
| Notion-Version | `2022-06-28` (WAJIB, jangan pakai versi lain) |
| Auth | Bearer token dari env var `NOTION_API_KEY` |
| Base URL | `https://api.notion.com/v1` |

## Yang BOLEH Kamu Lakukan

### Tasks Database
- ✅ **Update status task MILIK KAMU** — Queued → Running → Done / Failed
- ✅ **Update "Last Run"** — set tanggal/waktu setelah selesai
- ✅ **Update "Notes"** — tambah catatan hasil kerja, error log, dll
- ✅ **Query task milik kamu** — filter by Assigned Agent = "Apollo"

### Projects Database
- ✅ **Baca project info** — untuk context task kamu

## Yang TIDAK BOLEH Kamu Lakukan

- ❌ **Jangan buat task baru** — itu tugas Iris ✨
- ❌ **Jangan buat project baru** — itu tugas Iris ✨
- ❌ **Jangan update task agent lain** (Atlas) — bukan urusanmu
- ❌ **Jangan hapus task/project** — archive pun nggak boleh
- ❌ **Jangan ubah Project relation** — Iris yang assign
- ❌ **Jangan ubah Assigned Agent** — Iris yang assign
- ❌ **Jangan ubah Priority atau Type** — Iris yang set
- ❌ **Jangan set status "Escalated"** — itu hak Iris

## Status yang Boleh Kamu Set

| Dari | Ke | Kapan |
|------|----|-------|
| Queued | Running | Saat mulai kerjakan task |
| Running | Done | Saat task selesai sukses |
| Running | Failed | Saat task gagal (WAJIB tulis alasan di Notes) |

**Kamu TIDAK boleh set**: Queued, Escalated, Cancelled — itu domain Iris.

## Wajib Setiap Task Selesai

1. Update Status → Done atau Failed
2. Update Last Run → waktu sekarang (WIB)
3. Update Notes → hasil kerja atau error message
4. Kalau Failed → tulis alasan spesifik di Notes

## Contoh API Call

### Query Task Milik Kamu
```bash
curl -X POST 'https://api.notion.com/v1/databases/30031616-a0d5-81ac-86f0-e108677a6d0a/query' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "filter": {
      "and": [
        {"property": "Assigned Agent", "select": {"equals": "Apollo"}},
        {"property": "Status", "select": {"equals": "Queued"}}
      ]
    }
  }'
```

### Update Task Selesai
```bash
curl -X PATCH 'https://api.notion.com/v1/pages/TASK_PAGE_ID' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "properties": {
      "Status": {"select": {"name": "Done"}},
      "Last Run": {"date": {"start": "2026-02-07T08:45:00+07:00"}},
      "Notes": {"rich_text": [{"text": {"content": "R&D report sent. 3 products behind timeline flagged. Email to Mbak Dewi."}}]}
    }
  }'
```

### Update Task Gagal
```bash
curl -X PATCH 'https://api.notion.com/v1/pages/TASK_PAGE_ID' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "properties": {
      "Status": {"select": {"name": "Failed"}},
      "Last Run": {"date": {"start": "2026-02-07T08:45:00+07:00"}},
      "Notes": {"rich_text": [{"text": {"content": "GAGAL: Accurate API return empty response untuk data QC batch 7."}}]}
    }
  }'
```

## Project IDs (Reference Only — Read, Don't Modify)

| Project | ID |
|---------|-----|
| R&D Status Reports | `30031616-a0d5-81fe-a1ee-d157080795df` |
| System Setup | `30031616-a0d5-81f5-ad9e-e13a4adf3833` |
| Incidental | `30031616-a0d5-814f-8642-f983282b15e5` |
