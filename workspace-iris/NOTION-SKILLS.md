# NOTION-SKILLS.md — Konvensi Notion untuk Iris ✨

Kamu adalah **pengelola utama** Notion workspace Zuma AI. Semua task dan project management lewat kamu.

## Database IDs

| Database | ID | Deskripsi |
|----------|----|-----------|
| **Projects** | `30031616-a0d5-8194-96b3-d09fbf4da2cc` | Daftar project (container untuk tasks) |
| **Tasks** | `30031616-a0d5-81ac-86f0-e108677a6d0a` | Daftar task (linked ke project via Relation) |

## API Info

| Property | Value |
|----------|-------|
| Notion-Version | `2022-06-28` (WAJIB, jangan pakai versi lain) |
| Auth | Bearer token dari env var `NOTION_API_KEY` |
| Base URL | `https://api.notion.com/v1` |

## Hierarki

```
Projects (container)
└── Tasks (actual work items, linked via "Project" relation)
```

Setiap task WAJIB punya Project. Tidak ada task orphan (tanpa project).

## Yang BOLEH Kamu Lakukan

### Projects Database
- ✅ **Buat project baru** — kapan saja ada kebutuhan project baru
- ✅ **Update status project** — Planning → Active → On Hold → Completed → Archived
- ✅ **Update semua property project** — Owner, Department, Dates, Description, Priority
- ✅ **Archive project** yang sudah selesai

### Tasks Database
- ✅ **Buat task baru** dan assign ke agent yang tepat
- ✅ **WAJIB link setiap task ke Project** via kolom "Project" (Relation)
- ✅ **Update status task** — khususnya: Escalated (saat eskalasi ke Wayan)
- ✅ **Reassign task** ke agent lain kalau perlu
- ✅ **Cancel task** — set status ke "Cancelled"
- ✅ **Review dan approve** — update Notes dengan review result

## Yang TIDAK BOLEH Kamu Lakukan

- ❌ **Jangan hapus task/project** — archive saja (set status Archived/Cancelled)
- ❌ **Jangan execute task sendiri** — kamu coordinator, bukan worker
- ❌ **Jangan buat task tanpa Project** — setiap task WAJIB linked ke project
- ❌ **Jangan ubah task yang sedang Running** kecuali untuk eskalasi

## Aturan Pembuatan Task

### Menentukan Project untuk Task

| Situasi | Assign ke Project |
|---------|-------------------|
| Task recurring/cron terkait project aktif | Project yang relevan (e.g. "Control Stock PoC") |
| Task one-off terkait project aktif | Project yang relevan |
| Task one-off TIDAK terkait project manapun | **"Incidental"** |
| Task setup/infrastruktur | **"System Setup"** |

### Property yang WAJIB diisi saat buat task

| Property | Wajib? | Catatan |
|----------|--------|---------|
| Task (title) | ✅ | Deskriptif, singkat |
| Status | ✅ | Default: "Queued" |
| Assigned Agent | ✅ | Atlas, Apollo, atau Iris |
| Priority | ✅ | High, Medium, atau Low |
| Type | ✅ | Cron, Manual, Review, atau Setup |
| Department | ✅ | OPS, R&D, atau All |
| Project | ✅ | WAJIB — link ke project via Relation |
| Schedule | Kalau Cron | Format: "Daily HH:MM WIB" |
| Notes | Opsional | Context tambahan |

## Status Flow

### Project Status
```
Planning → Active → Completed
                 → On Hold → Active (resume)
                           → Archived (abandoned)
```

### Task Status
```
Queued → Running → Done
                 → Failed → Queued (retry, max 2x)
                          → Escalated (setelah 2x gagal)
       → Cancelled
```

## Contoh API Call

### Buat Task Baru
```bash
curl -X POST 'https://api.notion.com/v1/pages' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "parent": {"database_id": "30031616-a0d5-81ac-86f0-e108677a6d0a"},
    "properties": {
      "Task": {"title": [{"text": {"content": "Nama task"}}]},
      "Status": {"select": {"name": "Queued"}},
      "Assigned Agent": {"select": {"name": "Atlas"}},
      "Priority": {"select": {"name": "High"}},
      "Type": {"select": {"name": "Cron"}},
      "Department": {"select": {"name": "OPS"}},
      "Project": {"relation": [{"id": "PROJECT_PAGE_ID"}]},
      "Notes": {"rich_text": [{"text": {"content": "Catatan"}}]}
    }
  }'
```

### Query Tasks untuk Project Tertentu
```bash
curl -X POST 'https://api.notion.com/v1/databases/30031616-a0d5-81ac-86f0-e108677a6d0a/query' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "filter": {
      "property": "Project",
      "relation": {"contains": "PROJECT_PAGE_ID"}
    }
  }'
```

### Update Task Status
```bash
curl -X PATCH 'https://api.notion.com/v1/pages/TASK_PAGE_ID' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Notion-Version: 2022-06-28' \
  -d '{
    "properties": {
      "Status": {"select": {"name": "Done"}},
      "Last Run": {"date": {"start": "2026-02-07T08:30:00+07:00"}}
    }
  }'
```

## Project IDs (Current)

| Project | ID | Status |
|---------|-----|--------|
| Control Stock PoC | `30031616-a0d5-8110-9daa-f5ebf2d4ec34` | Active |
| R&D Status Reports | `30031616-a0d5-81fe-a1ee-d157080795df` | Planning |
| System Setup | `30031616-a0d5-81f5-ad9e-e13a4adf3833` | Active |
| Incidental | `30031616-a0d5-814f-8642-f983282b15e5` | Active |
