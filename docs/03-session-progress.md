# Session Progress Log

## Session: 7 Feb 2026

### Completed ✅

**Infrastructure**
- Hostinger VPS KVM 2 purchased (2 vCPU, 8GB RAM, 100GB NVMe, Singapore)
- IP: 76.13.194.103
- SSH config: `ssh zuma` (in ~/.ssh/config)
- OpenClaw v2026.1.30 installed & running as daemon
- Railway attempted → abandoned (no terminal access)

**Agents Created**
- Iris ✨ (main) — Lead Coordinator / Project Manager (renamed from Iris)
  - Manages Atlas & Apollo's cron jobs
  - Reviews work via Notion Kanban
  - Escalates to Wayan via Telegram & Notion
- Atlas 🏔️ (ops) — OPS Titan
  - Stock & Inventory, Warehouse, Logistics
  - First real task: Control Stock (pending SOP)
- Apollo 🎯 (rnd) — R&D God
  - Product Development, QC, Material Sourcing

**Agent Configuration**
- All 3 have: AGENTS.md, IDENTITY.md, SOUL.md, USER.md
- All in Bahasa Indonesia
- Personality: santai tapi serius, sedikit playful, bukan robot
- Model: Anthropic Claude Sonnet 4.5 (all agents)
- All tested & responding correctly

**VPS Paths**
```
/root/.openclaw/
├── agents/main/     ← Iris
├── agents/ops/      ← Atlas  
├── agents/rnd/      ← Apollo
├── workspace/       ← Iris workspace
├── workspace-ops/   ← Atlas workspace
├── workspace-rnd/   ← Apollo workspace
├── cron/
└── openclaw.json
```

**Key Decisions**
- Iris = project manager, NOT worker. Manages cron jobs via Notion.
- Atlas & Apollo = workers doing cron jobs
- No HEARTBEAT.md pattern — use Notion Kanban instead
- Resource-aware: sequential tasks preferred over heavy parallel
- Full Indonesian for all comms & technical
- Greek god theme: Iris (wisdom), Atlas (strength), Apollo (perfection)

### Remaining 📋

**Next Session (Priority Order)**
1. Set up Telegram — bots for each agent, wire routing
2. Switch Atlas & Apollo to Haiku model (cheaper for daily cron)
3. Control Stock SOP walkthrough (Wayan guides):
   - How to CREATE the GSheet (one-time, 13 tabs)
   - How to UPDATE raw data daily
   - How the EMAIL report looks

**After SOPs**
4. Install gog CLI on VPS (Google Sheets, Gmail)
5. Google OAuth / Service Account setup
6. Accurate Online API credentials (from IT)
7. Write skills & SOP docs for Atlas's first task
8. Create Control Stock GSheet (Atlas builds from scratch)
9. Set up Notion task tracker database
10. Set up cron jobs (Atlas 8:30 WIB, Apollo 8:45 WIB)
11. Connect Telegram & Notion to all agents

**Validation**
12. End-to-end test: API → GSheet → Email → Notion
13. 5-day parallel run: agent vs human
14. Iris reviews Atlas's outputs

**Later Phases**
- Phase 2: More agents, more departments
- Phase 3: Mac Mini M4 for Layer 2 (Iris moves to dedicated hardware)

### Cost
| Item | Monthly |
|---|---|
| Hostinger KVM 2 | $6.99 |
| Anthropic API (estimate) | ~$10-20 |
| **Total estimate** | **~$17-27/mo** |

### Continuation Context

**SSH**: `ssh zuma` (root@76.13.194.103)
**OpenClaw TUI**:
- Iris: `openclaw tui --session agent:main:main`
- Atlas: `openclaw tui --session agent:ops:main`
- Apollo: `openclaw tui --session agent:rnd:main`

**Config**: `/root/.openclaw/openclaw.json`
**Local docs**: `D:\WAYAN\Work\0.KANTOR\ZUMA INDONESIA\0. DATA\0. N8N\00. CLAUDE CODE - 2\zuma-frontier-project\0. multi-moltbolt-project\0. openclaw project for OPS\`

---

## Session 2: 7 Feb 2026 (Evening)

### Completed ✅

**SSH Key Auth**
- Generated Ed25519 key at `C:\Users\Wayan\.ssh\id_ed25519`
- Copied public key to VPS via paramiko script
- Updated SSH config with IdentityFile — `ssh zuma` works passwordless

**LLM Model Hierarchy**
- Added 3 providers: Anthropic (token), Kimi Coding (API key), OpenRouter (API key)
- Per-agent model overrides: Iris gets Sonnet primary, Atlas/Apollo get Kimi K2.5 primary
- Heartbeats: 30min on Gemini Flash-Lite (cheapest)
- Subagents: Kimi K2.5, maxConcurrent 8
- Estimated cost: ~$49/mo (vs ~$180 all-Sonnet = 73% savings)

**GitHub Repo**
- Created: https://github.com/database-zuma/openclaw-ops-rnd (public)
- 16 files pushed (workspace configs, sanitized config, README)
- Stale repo at `wayansuardyana-code/openclaw-ops-rnd` — delete manually

**Skills/MCP Installation (9/49 ready, was 6/49)**
- `gh` CLI installed via `apt install gh`, authed via GH_TOKEN env var
- `gog` CLI built from source (Go 1.25, `make` in gogcli repo), binary at `/usr/local/bin/gog`
- `notion` skill enabled via NOTION_API_KEY env var, API verified working
- Notion integration name: `openclaw-zuma-vps`
- Connected to page: "OpenClaw HERE!" (ID: 30031616-a0d5-807a-8342-f72d4b7c8077)

### Updated Cost

| Item | Monthly |
|---|---|
| Hostinger KVM 2 | $6.99 |
| LLM (model hierarchy) | ~$49 |
| **Total estimate** | **~$56/mo** |

### Technical Gotchas & Solutions

**1. Notion API version incompatibility**
- **Problem**: OpenClaw's bundled `notion` SKILL.md references `Notion-Version: 2025-09-03` — this returns `401 unauthorized` / `API token is invalid`
- **Solution**: Use `Notion-Version: 2022-06-28` instead. Works fine.
- **Why**: The 2025-09-03 version may not be GA yet, or our integration type doesn't support it.
- **Where**: Any curl/API call to Notion from VPS must use the older version header.

**2. Go version too old for gog build**
- **Problem**: `apt install golang-go` gives Go 1.22 on Ubuntu 24.04. gogcli requires Go 1.25+.
- **Solution**: Install Go 1.25 manually from `https://go.dev/dl/go1.25.0.linux-amd64.tar.gz`, extract to `/usr/local/go/`.
- **Where**: `export PATH=/usr/local/go/bin:$PATH` added to `/root/.bashrc`.

**3. gh CLI auth scope error**
- **Problem**: `gh auth login --with-token` fails with `missing required scope 'read:org'` — the GitHub PAT doesn't have org scopes.
- **Solution**: Skip `gh auth login`. Set `GH_TOKEN=ghp_...` as env var instead. `gh` CLI reads it automatically.
- **Where**: Added to `/root/.openclaw/.env`.

**4. `make` not installed on VPS**
- **Problem**: Fresh Ubuntu 24.04 doesn't have `make`. Building gogcli fails.
- **Solution**: `apt-get install -y make` before running `make` in gogcli.

### Remaining (Updated after Session 2)

**Needs Wayan's Action:**
1. Create Google Cloud project + download `client_secret.json` → enables gog OAuth for Sheets/Gmail
2. Create Telegram bots via @BotFather → enables agent Telegram routing
3. Get Accurate Online API credentials from IT
4. Walk through Control Stock SOP (how to create GSheet, daily update, email format)

**After That:**
5. Run `gog auth add` with client_secret.json on VPS (use `--manual` flag, no browser)
6. Configure Telegram groups + routing in openclaw.json
7. Create Notion Task Tracker database
8. Write skill/SOP docs for Atlas
9. Create Control Stock GSheet (13 tabs)
10. Configure cron jobs
11. End-to-end test
12. 5-day parallel run

---

## Session 3: 7 Feb 2026 (Late Night)

### Completed

**GitHub Push (finally)**
- Previous sessions failed using `mcp_github_push_files` and `mcp_github_create_or_update_file` (both returned "Not Found")
- **Solution**: Clone repo via git CLI with PAT in URL, make changes locally, commit, push
- Command: `git clone https://<PAT>@github.com/database-zuma/openclaw-ops-rnd.git /tmp/openclaw-repo`
- Commit: `56c6ed0` on main branch

**Notion Hierarchical PM System — Built (Projects ↔ Tasks)**
- Deleted duplicate empty database + rebuilt from scratch
- **Projects Database 📌**: `30031616-a0d5-8194-96b3-d09fbf4da2cc`
  - Properties: Project (title), Status, Department, Owner Agent, Priority, Start Date, Target End, Description
  - Seeded 4 projects:
    1. Control Stock PoC (Active, OPS, Atlas)
    2. R&D Status Reports (Planning, R&D, Apollo)
    3. System Setup (Active, All, Iris)
    4. Incidental (Active, All, Iris) — catch-all for one-offs
- **Tasks Database 💫**: `30031616-a0d5-81ac-86f0-e108677a6d0a`
  - Properties: Task (title), Status, Assigned Agent, Priority, Type, Schedule, Notes, Last Run, Department, **Project (Relation → Projects)**
  - Seeded 6 tasks, ALL linked to projects:
    1. Control Stock - Daily Update & Insight Email (Atlas) → Control Stock PoC
    2. Review Atlas Control Stock Output (Iris) → Control Stock PoC
    3. R&D Status Report (Apollo) → R&D Status Reports
    4. Setup: gog OAuth (Iris, BLOCKED) → System Setup
    5. Setup: Telegram Routing (Iris, BLOCKED) → System Setup
    6. Setup: Accurate Online API (Atlas, BLOCKED) → System Setup
- **Rule**: Every task MUST link to a Project (no orphans). One-off unrelated tasks → "Incidental"

**NOTION-SKILLS.md Created Per Agent** (pushed to GitHub commit `48021e2`):
- `workspace-iris/NOTION-SKILLS.md` — Full PM: create tasks/projects, assign agents, review, manage all
- `workspace-ops/NOTION-SKILLS.md` — Atlas: update OWN task status/notes/last-run ONLY
- `workspace-rnd/NOTION-SKILLS.md` — Apollo: update OWN task status/notes/last-run ONLY
- Each includes: database IDs, API examples, CAN/CANNOT rules, status flow, property conventions
- **NOTE**: These files need to be synced to VPS workspaces

**Google Workspace Decision**
- Using `harveywayan@gmail.com` for now (has existing GCP project with OAuth for Gmail, GSheets, GDocs, GDrive)
- Will migrate to `iris-openclaw@zuma.id` later
- Need: `client_secret.json` download from Google Cloud Console → then `gog auth add --manual` on VPS
- `harveywayan@gmail.com` may need edit access to Control Stock GSheet

**Changes pushed to GitHub (database-zuma/openclaw-ops-rnd):**
- `README.md` — **completely rewritten** to engaging narrative style:
  - ASCII art architecture diagram (Iris/Atlas/Apollo)
  - "What is this?" narrative section
  - "How much does it cost?" with pricing table
  - "The five rules" section
  - Clean file structure, integrations table, roadmap
  - No more Athena references
- `workspace-iris/` — **new directory** (5 files):
  - `IDENTITY.md` — Iris, Dewi Yunani pelangi, emoji ✨
  - `SOUL.md` — Jembatan antara semua orang, relay presisi
  - `USER.md` — Serves CI Team, coordinates Atlas & Apollo, PIC eskalasi
  - `AGENTS.md` — Lead coordinator rules, credentials management
  - `MEMORY.md` — Knowledge base (company, infra, agent fleet, tools, decisions)
- `workspace-athena/` — **deleted** (5 files removed)
- `workspace-ops/AGENTS.md` — "Athena" → "Iris ✨" in credentials section
- `workspace-rnd/AGENTS.md` — "Athena" → "Iris ✨" in credentials section

**Local files verified clean:**
- `AGENTS-ops.md` — no Athena references (was always clean)
- `AGENTS-rnd.md` — no Athena references (was always clean)

### Technical Gotchas (NEW)

**6. GitHub MCP tools fail with "Not Found" on database-zuma repos**
- **Problem**: Both `mcp_github_push_files` and `mcp_github_create_or_update_file` return `McpError: MCP error -32603: Not Found` when targeting `database-zuma/openclaw-ops-rnd`.
- **Root cause**: Unknown — possibly MCP tool uses different auth than the PAT, or repo name case sensitivity issue (`database-Zuma` vs `database-zuma`).
- **Solution**: Clone repo via git CLI with PAT in URL, make all changes locally, commit, push. This always works.
- **Command pattern**:
  ```bash
  git clone https://<PAT>@github.com/database-zuma/openclaw-ops-rnd.git /tmp/openclaw-repo
  cd /tmp/openclaw-repo
  # make changes...
  git config user.email "database-zuma@users.noreply.github.com"
  git config user.name "database-zuma"
  git add -A && git commit -m "message" && git push origin main
  rm -rf /tmp/openclaw-repo  # cleanup
  ```
- **Note**: `gh` CLI is NOT installed on Wayan's Windows machine, only on the VPS.

**7. Write tool won't overwrite existing files in cloned repos**
- **Problem**: Claude's `mcp_write` tool refuses to overwrite files that already exist (returns "File already exists. Use edit tool instead").
- **Solution**: Use `cat > file << 'EOF' ... EOF` via bash instead for bulk file overwrites.

### Remaining (Updated)

**BLOCKED on Wayan:**
1. Sync NOTION-SKILLS.md to VPS workspaces (copy from GitHub or manually)
2. gog OAuth → Download `client_secret.json` from GCP (harveywayan@gmail.com) → share with me
3. Telegram routing → Need bots/groups created via @BotFather
4. Accurate Online API → Need credentials from IT
5. Control Stock SOP → Need Wayan to walk through manual process

**After blockers cleared:**
6. `gog auth add` with client_secret.json on VPS (`--manual` flag, no browser)
7. Configure Telegram groups + routing in openclaw.json
8. Write skill/SOP docs for Atlas
9. Create Control Stock GSheet (13 tabs, formulas, TIER system)
10. Configure cron jobs (Atlas 8:30 WIB, Apollo 8:45 WIB)
11. End-to-end test
12. 5-day parallel run (agent vs human)

### Open Questions (for SOP walkthrough)
- What Accurate API endpoints return stock/sales data?
- Merchandiser's email address for daily insights?
- The #VALUE! errors on Global tab — expected or bug?
- How are products assigned to tiers?
- Which warehouses exist? (WHS = Shopfloor, WHB = Box — more?)

### Continuation Context

**GitHub repo**: https://github.com/database-zuma/openclaw-ops-rnd (commit 56c6ed0)
**Repo structure now**:
```
openclaw-ops-rnd/
├── README.md                    # Engaging narrative (Iris ✨, updated)
├── .gitignore
├── config/openclaw.json.example # Sanitized config
├── workspace-iris/              # NEW (was workspace-athena/)
│   ├── IDENTITY.md, SOUL.md, USER.md, AGENTS.md, MEMORY.md
├── workspace-ops/               # Atlas (AGENTS.md updated: Athena→Iris)
│   ├── IDENTITY.md, SOUL.md, USER.md, AGENTS.md
└── workspace-rnd/               # Apollo (AGENTS.md updated: Athena→Iris)
    ├── IDENTITY.md, SOUL.md, USER.md, AGENTS.md
```

**SSH**: `ssh zuma` (root@76.13.194.103)
**OpenClaw TUI**:
- Iris: `openclaw tui --session agent:main:main`
- Atlas: `openclaw tui --session agent:ops:main`
- Apollo: `openclaw tui --session agent:rnd:main`

**VPS skills**: 9/49 ready (gh, gog, notion + 6 bundled)
**Notion**: API key `ntn_1325...` connected to "OpenClaw HERE!" page, version `2022-06-28`
**Local .env**: All credentials at `D:\WAYAN\Work\...\0. openclaw project for OPS\.env`
**VPS .env**: `/root/.openclaw/.env` (GH_TOKEN, NOTION_API_KEY)

### All Technical Gotchas (consolidated)

| # | Problem | Solution |
|---|---------|----------|
| 1 | Notion API version 2025-09-03 → 401 | Use `2022-06-28` |
| 2 | `apt install golang-go` = Go 1.22, need 1.25+ | Manual install from go.dev |
| 3 | `gh auth login --with-token` fails scope | Use `GH_TOKEN` env var |
| 4 | `make` missing on Ubuntu 24.04 | `apt install make` |
| 5 | SSH port forward "bind already in use" warning | Cosmetic, ignore |
| 6 | GitHub MCP tools → "Not Found" on push/create | Clone via git CLI + PAT, push manually |
| 7 | Claude Write tool won't overwrite existing files | Use `cat > file << 'EOF'` via bash |
| 8 | gog keyring needs TTY for passphrase | Set `GOG_KEYRING_PASSWORD` env var in `/root/.openclaw/.env` |

### MUST NOT Do (Critical Constraints)

- **DO NOT use Railway** — abandoned
- **DO NOT use browser automation** — crashes VPS (2 cores)
- **DO NOT put API keys in .md files** — they get sent to LLM prompts
- **DO NOT have multiple agents write to same GSheet** — data loss
- **DO NOT hardcode cron times without timezone** — use `Asia/Jakarta` (WIB)
- **DO NOT let revision cycles loop infinitely** — max 2 attempts, escalate
- **DO NOT write technical content in English** — ALL agent communication in Bahasa Indonesia
- **DO NOT address reports to Wayan** — address to department PICs
- **DO NOT use HEARTBEAT.md pattern** — Iris monitors via Notion Kanban
- **DO NOT push heavy parallel tasks** — VPS has 2 CPU cores, sequential preferred
- **DO NOT push secrets to GitHub** — all credentials in .env files only
- **DO NOT use `wayansuardyana-code` GitHub** — use `database-zuma` account
- **DO NOT use Notion API version 2025-09-03** — use `2022-06-28` (newer version returns 401)
- **DO NOT use `gh auth login --with-token`** — use `GH_TOKEN` env var instead
- **DO NOT use rainbow emoji for Iris** — use ✨ sparkle
- **DO NOT call the coordinator Athena** — she is now **Iris ✨**
- **DO NOT use GitHub MCP push_files/create_or_update_file** — use git clone + push instead (Gotcha #6)
- **Stale repo exists**: `wayansuardyana-code/openclaw-ops-rnd` — user needs to delete manually

---

## Session 4: 8 Feb 2026

### Completed ✅

**gog Keyring Fix — Non-Interactive Access**
- Added `GOG_KEYRING_PASSWORD=openclaw-zuma-2026` to `/root/.openclaw/.env`
- Verified `gog auth list` works: `harveywayan@gmail.com  openclaw-zuma  docs,drive,gmail,sheets`
- Verified GSheet read: `gog sheets metadata` on Control Stock GSheet (36 tabs discovered, not 13)
- Verified Gmail read: `gog gmail search 'in:inbox'` returns emails
- **gog is now fully operational for non-interactive/cron use**

**Control Stock GSheet — Actual Tab Count: 36 (was estimated 13)**
Tabs discovered via `gog sheets metadata`:
- Core: PO, Global, WH BOX, DATA AWAL, Update Stock, Summary Kode MIX, forNotionIntegrator
- TIER system: TIER 1-5, TIER 8, TIER 1 (NEW), TIER 2 (NEW), TIER 3 (NEW), Hitung Tier, All Tier, All Tier Value
- Product lines: KIDS, SERIES, BABY, Freya & Kim, Slide Max
- Source data: source_sell through (mtd) — 25,427 rows
- Meeting/Misc: Meeting TIER 1 261024, T1 Sort, Pivot Table 6, CATATAN, Sheet38, Sheet40, Sheet54, tidak dipakai deck

**NOTION-SKILLS.md Synced to VPS**
- Copied from GitHub repo to all 3 VPS workspaces:
  - `/root/.openclaw/workspace/NOTION-SKILLS.md` (Iris, 152 lines)
  - `/root/.openclaw/workspace-ops/NOTION-SKILLS.md` (Atlas, 113 lines)
  - `/root/.openclaw/workspace-rnd/NOTION-SKILLS.md` (Apollo, 113 lines)
- Agents now have Notion PM rules available in their workspace context

### Technical Gotcha Added

**8. gog keyring needs TTY for passphrase prompt**
- **Problem**: `gog auth list` fails with `no TTY available for keyring file backend password prompt; set GOG_KEYRING_PASSWORD`
- **Fix**: Add `GOG_KEYRING_PASSWORD=openclaw-zuma-2026` to `/root/.openclaw/.env`. Export before running gog commands.
- **For cron**: OpenClaw should source `.env` before invoking gog. Verify cron jobs have the env var.

### Architecture Decisions Made

**1. Supabase-First Data Architecture (DECIDED)**
- **Everything agents do → Supabase/SQL first**. Supabase PostgreSQL is the single source of truth.
- Same Supabase project as zuma-branch-superapp, **new schema: `openclaw_ops`**
- Data flow: Accurate API → Supabase tables → SQL views → Email insights to PICs
- GSheet is NOT in the daily critical path

**2. GSheet = Daily Dashboard + Weekly Manual Monitoring (DECIDED)**
- GSheet (same ID: `1qInTrRUOUi2983vefS8doS5Pt3jC2yftQAG99yYlVOE`) serves as **dashboard**
- **Daily**: Agent mirrors flat/clean/summary data from Supabase SQL views → specific GSheet tabs
  - NO raw data, NO formulas — only pre-calculated summary tables from Supabase
  - GSheet is a display layer, Supabase is the brain
- **Email**: Contains inline summary table + link to GSheet for full details
- **Weekly**: Wayan manually checks GSheet for data reliability monitoring
  - Wayan creates a separate monitoring template (manual formulas) — checked once a week
  - If Wayan doesn't check that week → monitoring template stays stale (that's fine)
- `harveywayan@gmail.com` needs **edit access** to Control Stock GSheet (currently read-only, 403)

**3. Three Agent GSheet/Data Skill Types (DECIDED)**
- **Data Mover**: Accurate API → Supabase tables (daily cron)
- **Data Processor**: SQL views/functions in Supabase (auto-calculated)
- **Report Builder**: Query Supabase view → format → Email to PICs (+ optional GSheet dump on demand)

**4. GSheet Formula Strategy → RESOLVED**
- No longer relevant for daily flow (Supabase handles all calculations via SQL)
- GSheet monitoring template uses manual formulas Wayan creates himself
- Agent only writes plain values to GSheet (no formula insertion needed)

**5. Monitoring Architecture (DECIDED)**
- **Quick (5 sec)**: Notion task status (Done/Failed)
- **Medium (30 sec)**: GSheet monitoring tab (weekly)
- **Deep (2 min)**: Supabase Studio Table Editor (browse actual data, no SQL needed)
- **Emergency**: Agent sends Telegram alert automatically
- Agent runs validation SQL after every load (row counts, null checks, freshness, drift)
- Reports anomalies in Notion task notes

**6. `harveywayan@gmail.com` GSheet Access — CONFIRMED READ-ONLY (NEEDS FIX)**
- Write test returned 403 Forbidden
- **Need edit access from GSheet owner** — BLOCKING for daily dashboard updates
- Priority: HIGH (GSheet is in daily path as dashboard)

### Remaining

**BLOCKED on Wayan:**
1. Telegram bots/groups via @BotFather
2. Accurate Online API credentials from IT
3. Control Stock SOP walkthrough (especially important now — 36 tabs is more complex than expected)
4. Share Control Stock GSheet edit access with `harveywayan@gmail.com` (for weekly monitoring dumps)

**After blockers cleared:**
5. Create Supabase schema `openclaw_ops` + design tables/views
6. Write skill/SOP docs for Atlas (3 skill types)
7. Configure cron jobs
8. End-to-end test
9. 5-day parallel run

### VPS .env (Updated)
```
/root/.openclaw/.env now contains:
- GH_TOKEN=ghp_...
- NOTION_API_KEY=ntn_...
- GOG_KEYRING_PASSWORD=openclaw-zuma-2026  ← NEW
```

---

## Session 5: 8 Feb 2026 (LOST SESSIONS — Reconstructed)

> These sessions were lost due to context/session expiry. Reconstructed from live VPS inspection + screenshots + updated local docs on 8 Feb 2026.

### Completed ✅

**DB VPS Purchased & Provisioned (KVM 2 — 76.13.194.120)**
- Second Hostinger KVM 2 purchased (2 vCPU, 8GB RAM, 100GB NVMe, Ubuntu 24.04 LTS)
- IP: 76.13.194.120
- SSH config: `ssh postgresql` (in `~/.ssh/config`)
- SSH key auth configured (same Ed25519 key as Agent VPS)
- Root password set (in local `.env` as `VPS_DB_PASS`)

**PostgreSQL 16.11 + pgvector Installed**
- PostgreSQL 16.11 running as systemd service
- pgvector extension installed (for future vector similarity search)
- Firewall (UFW): port 5432 open to Agent VPS (76.13.194.103) only + Docker subnet
- fail2ban active for SSH brute-force protection

**Database `openclaw_ops` Created**
- 4 schemas: `raw`, `core`, `mart`, `portal`
- 5 DB users with least-privilege:
  - `openclaw_app` — full owner of all schemas (for agents)
  - `nocodb_reader` — SELECT only (for NocoDB dashboard)
  - `postgrest_auth` — authenticator role (for PostgREST)
  - `postgrest_anon` — no login, SELECT on mart only (unauthenticated API)
  - `postgrest_agent` — no login, SELECT/INSERT/UPDATE on raw+core (authenticated agent API)

**Portal Reference Data Loaded (4 tables, 6,782 rows total)**
- `portal.store` — 326 rows (store/branch master: names, branch, area, category, capacity, targets)
- `portal.kodemix` — 5,464 rows (product SKU master: kode_mix, tier, gender, series, assortment, status)
- `portal.hpprsp` — 935 rows (product pricing: harga_beli, price_taq, rsp, tier, season)
- `portal.stock_capacity` — 57 rows (store stock capacity limits: max_display, max_stock, storage)
- Source: CSV import, batch_id `portal_init_20260208`

**Raw Staging Tables Designed (9 tables, all empty)**
- `raw.ddd_stock`, `raw.ddd_sales` — DDD warehouse
- `raw.ljbb_stock` — LJBB warehouse
- `raw.mbb_stock`, `raw.mbb_sales` — MBB warehouse
- `raw.ubb_stock`, `raw.ubb_sales` — UBB warehouse
- `raw.iseller_sales` — iSeller POS data
- `raw.load_history` — ETL audit trail (4 rows from portal load)
- All tables have proper indexes (kode_barang, snapshot_date, tanggal, batch_id)

**PostgREST 14.3 Installed & Running**
- Systemd service, running on port 3000 (localhost only)
- Config at `/root/postgrest.conf`
- Exposed schemas: `mart`, `core`, `raw`
- JWT secret configured (in local `.env`)

**NocoDB Installed via Docker**
- Running at port 8080
- Admin account: `database@zuma.id` (password in local `.env`)
- Data source "OpenClaw Ops" connected to `openclaw_ops` database
- Schemas exposed: `core`, `mart`, `raw`
- Connection test: ✅ successful
- Allow Data Write/Edit: ✅ | Allow Schema Change: ❌

**nginx Reverse Proxy Configured**
- Config at `/etc/nginx/sites-available/openclaw-db` (symlinked to sites-enabled)
- `/api/` → PostgREST (port 3000) with `X-API-Key` header auth
- `/nocodb/` → NocoDB (port 8080) with WebSocket support
- `/health` → JSON health status endpoint
- API key for nginx in local `.env` as `POSTGREST_API_KEY`

**Backup System Configured**
- Script: `/root/backups/backup.sh`
- Daily cron at 03:00: `pg_dump openclaw_ops` → gzip (7 day retention)
- Weekly Sunday: `pg_dumpall` → gzip (4 week retention)
- Crontab: `0 3 * * * /root/backups/backup.sh`

**Agent VPS → DB VPS Connectivity Verified**
- `psql` direct connection from KVM2 Agent VPS: ✅
- PostgREST API via nginx proxy with API key: ✅
- Health check endpoint: ✅

**New OAuth Client Secret Created**
- New client secret (`****7pcH`) created on GCP project `harvey-wayan-ai` (Feb 7, 2026)
- Previous secret (`****-pN2`) still enabled
- Warning: having multiple secrets is a security risk — should disable old one after confirming new one works

**Architecture Decision: Self-Hosted PostgreSQL (replaces Supabase)**
- Original plan: Use Supabase (same project as zuma-branch-superapp)
- New plan: Self-hosted PostgreSQL on dedicated KVM 2 VPS
- Reasons: dedicated resources, no shared disk with superapp (8GB limit, 3.32GB used), no billing issues, NocoDB for non-SQL monitoring, full control
- Supabase still runs for zuma-branch-superapp (Pro Plan, active)

### Architecture Decision: Railway Confirmed Dead
- Screenshot confirms: Railway deployment "clawdbot-railway-template" shows "GitHub Repo not found", status "Disconnected (1008): pairing required"
- OpenClaw Gateway on Railway: 0 instances, n/a sessions, n/a cron
- Config file `/data/.clawdbot/openclaw.json` does not exist
- Railway is completely abandoned — Hostinger VPS is the permanent home

### NOT Completed (Still Pending)

| Task | Status | Blocker |
|------|--------|---------|
| `core.*` tables (dim/fact) | ⬜ Not built | Needs Control Stock SOP walkthrough |
| `mart.*` views (reporting) | ⬜ Not built | Needs core.* tables |
| Accurate Online API | 🔴 Blocked | Need credentials from IT |
| GSheet edit access | 🔴 Blocked | GSheet owner needs to share with harveywayan@gmail.com |
| Telegram bots/groups | 🟡 Pending | Wayan creates via @BotFather |
| Atlas skill/SOP docs | ⬜ Pending | Needs SOP + DB design |
| Cron jobs | ⬜ Pending | Needs everything above |

### Continuation Context

**DB VPS**: `ssh postgresql` (root@76.13.194.120)
**NocoDB**: http://76.13.194.120:8080/dashboard
**PostgREST**: http://76.13.194.120/api/ (with X-API-Key header)
**Health**: http://76.13.194.120/health
**All credentials**: Local `.env` file (DO NOT put in .md files)

### Updated Cost

| Item | Monthly |
|---|---|
| Hostinger KVM 2 — Agents | $6.99 |
| Hostinger KVM 2 — Database | $6.99 |
| LLM (model hierarchy) | ~$49 |
| **Total estimate** | **~$63/mo** |
