# OpenClaw OPS Setup Guide — Zuma Indonesia

> **What is this?** Complete reference for the OpenClaw AI agent system on Hostinger VPS.
> Documents actual current config: agents, LLMs, skills, credentials, file structure.
>
> **Target reader**: Wayan (System Developer, CI Team)
> **Last updated**: 8 Feb 2026

---

## TABLE OF CONTENTS

1. [The Big Picture](#1-the-big-picture)
2. [Architecture](#2-architecture)
3. [VPS & Infrastructure](#3-vps--infrastructure)
4. [Agent Configuration](#4-agent-configuration)
5. [LLM Model Hierarchy](#5-llm-model-hierarchy)
6. [Skills & MCP Status](#6-skills--mcp-status)
7. [Credentials & Security](#7-credentials--security)
8. [OpenClaw Configuration Reference](#8-openclaw-configuration-reference)
9. [GitHub Repository](#9-github-repository)
10. [Notion Integration](#10-notion-integration)
11. [Phase 1 Roadmap — Control Stock PoC](#11-phase-1-roadmap)
12. [Future Phases](#12-future-phases)
13. [Quick Reference](#13-quick-reference)
14. [Technical Gotchas & Solutions](#14-technical-gotchas--solutions)
15. [Troubleshooting](#15-troubleshooting)
16. [Files in This Folder](#16-files-in-this-folder)

---

## 1. THE BIG PICTURE

```
YOU (Wayan) tell AI agents what to do once.
They do it every day, automatically, forever.

WHAT THEY DO:
  Pull data from Accurate Online (ERP) --> Paste into Google Sheets -->
  Formulas calculate --> Agent reads results --> Sends insight email to PIC

FIRST AGENT (proof of concept):
  "Control Stock" — daily inventory monitoring
  Tells Merchandiser: which products to order more, which to stop ordering
```

### The 3-Layer Hierarchy

```
LAYER 3 (FUTURE)
  Jarvis — CEO dashboard, C-level insights
  -----------------------------------------------

LAYER 2 (FUTURE — Mac Mini M4)
  Department Overseers
  Check Layer 1's work every 30 min
  Review, approve, or send back for revision
  Send approval emails to human PICs
  -----------------------------------------------

LAYER 1.5 — COORDINATOR (VPS)              <-- LIVE
  Iris (Lead Coordinator / PM)
  Manages Atlas & Apollo via Notion Kanban
  Reviews results, escalates to Wayan if needed
  -----------------------------------------------

LAYER 1 — DIVISION WORKERS (VPS)           <-- LIVE
  Atlas (OPS) — Stock, Warehouse, Logistics
  Apollo (R&D) — Product Dev, QC, Materials
  Do repetitive data tasks on cron schedule
```

**Rule #1**: Agent = Data MOVER, not Data Calculator.
Agent pulls raw data → PostgreSQL stores & calculates → GSheet displays flat results.

---

## 2. ARCHITECTURE

### Data Flow (Daily — Phase 1) — SELF-HOSTED POSTGRESQL

```
+-------------------+
|  Accurate Online   | (ERP - stock, sales, accounting)
|  REST API          |
+---------+---------+
          | Atlas pulls via API (no browser!)
          v
+---------+---------+         +---------------------------+
|  KVM 2 (Agents)    |         |  KVM 2 (Database)          |
|  76.13.194.103     |         |  76.13.194.120              |
|                    |         |                             |
|  Atlas agent:      |         |  PostgreSQL 16 + pgvector   |
|  1. Pull data ──────────────>|  DB: openclaw_ops           |
|  2. Insert via     |  psql/  |  ├─ raw.* (staging)         |
|     PostgREST API  |  HTTP   |  ├─ core.* (normalized)     |
|  3. SQL views ◄──────────── |  └─ mart.* (views)          |
|     auto-calc      |         |                             |
|  4. Read view results        |  PostgREST (REST API :3000) |
|  5. Mirror to GSheet         |  NocoDB (dashboard :8080)   |
|  6. Send email     |         |  nginx (proxy :80)          |
|  7. Update Notion  |         +---------------------------+
+-+--------+-------+-+
  |        |       |
  v        v       v
+------+ +------+ +------+
|GSheet| |Email | |Notion|
|(dash)| |(PIC) | |(log) |
+------+ +------+ +------+
  │         │
  │    summary table
  │    + GSheet link
  │
  └── flat summary data
      (mirrored from
       PostgreSQL views)
```

**Key principle**: PostgreSQL = brain (all calculations via SQL views). GSheet = dashboard (flat display). Email = delivery (summary + GSheet link). NocoDB = Wayan's monitoring UI.

### Database 4-Schema Design

| Layer | Schema | Purpose | Tables (Live) |
|-------|--------|---------|---------------|
| **Reference** | `portal.*` | Master/dimension data (products, stores, pricing, capacity) | `portal.store` (326 rows), `portal.kodemix` (5,464), `portal.hpprsp` (935), `portal.stock_capacity` (57) |
| **Staging** | `raw.*` | Raw API data from Accurate/iSeller, partitioned by entity | `raw.ddd_stock`, `raw.ddd_sales`, `raw.ljbb_stock`, `raw.mbb_stock`, `raw.mbb_sales`, `raw.ubb_stock`, `raw.ubb_sales`, `raw.iseller_sales`, `raw.load_history` |
| **Normalized** | `core.*` | `dim_` (dimensions) + `fact_` (facts), proper FKs | ⬜ Not built yet |
| **Reporting** | `mart.*` | Denormalized views, flat & readable | ⬜ Not built yet |

### Portal Schema — Reference Data (✅ Loaded)

| Table | Rows | Purpose | Key Columns |
|-------|------|---------|-------------|
| `portal.store` | 326 | Store/branch master data | `nama_accurate`, `nama_iseller`, `branch`, `area`, `category`, `max_display`, `max_stock`, `monthly_target` |
| `portal.kodemix` | 5,464 | Product SKU master (sizes, tiers, series) | `kode_mix`, `kode_besar`, `tier_baru`, `gender`, `seri`, `series`, `assortment`, `status` |
| `portal.hpprsp` | 935 | Product pricing & RSP data | `kode`, `nama_barang`, `tier`, `season`, `harga_beli`, `price_taq`, `rsp` |
| `portal.stock_capacity` | 57 | Store stock capacity limits | `stock_location`, `branch`, `max_display`, `max_stock`, `storage` |

### Raw Schema — Staging Tables (✅ Designed, ⬜ Empty — awaiting Accurate API)

| Table | Source Entity | Key Columns |
|-------|--------------|-------------|
| `raw.ddd_stock` | DDD warehouse stock | `kode_barang`, `nama_barang`, `nama_gudang`, `kuantitas`, `snapshot_date` |
| `raw.ddd_sales` | DDD warehouse sales | `tanggal`, `kode_produk`, `nama_barang`, `kuantitas`, `harga_satuan`, `total_harga`, `bpp` |
| `raw.ljbb_stock` | LJBB warehouse stock | Same pattern as ddd_stock |
| `raw.mbb_stock` | MBB warehouse stock | Same pattern as ddd_stock |
| `raw.mbb_sales` | MBB warehouse sales | Same pattern as ddd_sales |
| `raw.ubb_stock` | UBB warehouse stock | Same pattern as ddd_stock |
| `raw.ubb_sales` | UBB warehouse sales | Same pattern as ddd_sales |
| `raw.iseller_sales` | iSeller POS data | TBD — iSeller API format |
| `raw.load_history` | ETL audit trail | `source`, `entity`, `data_type`, `batch_id`, `rows_loaded`, `status`, `error_message` |

### Three Agent Data Skill Types

| Skill | What | Tools |
|-------|------|-------|
| **Data Mover** | Accurate API → PostgreSQL raw tables | `curl` + PostgREST API / `psql` |
| **Data Processor** | SQL views auto-calculate | PostgreSQL (no agent action needed) |
| **Report Builder** | Read SQL views → mirror to GSheet + compose email | `gog sheets` + `gog gmail` |

### Communication Flow

```
+--------------------------------------------------------+
|                   TELEGRAM GROUPS (pending setup)        |
|                                                         |
|  "Zuma OPS Agents"     <-- alerts, important reports    |
|  "Zuma OPS Logs"       <-- routine/verbose output       |
|  "Zuma Agent Alerts"   <-- critical alerts only         |
+--------------------------------------------------------+

+--------------------------------------------------------+
|                    NOTION (✅ LIVE)                      |
|                                                         |
|  Page: "OpenClaw HERE!" (connected)                     |
|  📌 Projects DB ↔ 💫 Tasks DB (hierarchical PM)        |
|  Queued → Running → Done → Failed → Escalated          |
+--------------------------------------------------------+

+--------------------------------------------------------+
|              SELF-HOSTED POSTGRESQL (KVM 2: DB VPS)      |
|                                                         |
|  IP: 76.13.194.120 | SSH: ssh postgresql                |
|  New schema dedicated to agent data processing           |
|  SQL views = all calculations (replaces GSheet formulas) |
+--------------------------------------------------------+
```

---

## 3. VPS & INFRASTRUCTURE

### Two VPS Setup

| | KVM 2 — Agents | KVM 2 — Database |
|--|:-:|:-:|
| **Purpose** | OpenClaw agents (Iris, Atlas, Apollo) | PostgreSQL + PostgREST + NocoDB |
| **IP** | `76.13.194.103` | `76.13.194.120` |
| **SSH alias** | `ssh zuma` | `ssh postgresql` |
| **OS** | Ubuntu 24.04.3 LTS | Ubuntu 24.04.3 LTS |
| **RAM** | 8 GB | 8 GB |
| **Storage** | 100 GB NVMe | 100 GB NVMe |
| **CPU** | 2 cores | 2 cores |
| **Firewall** | SSH only | SSH + PostgreSQL(KVM2 only) + HTTP/HTTPS |

### Agent VPS Software (76.13.194.103)

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | v22.22.0 | OpenClaw runtime |
| npm | 10.9.4 | Package manager |
| OpenClaw | 2026.1.30 | AI agent framework |
| Go | 1.25.0 | Built gog CLI (at `/usr/local/go/bin`) |
| gh | 2.45.0 | GitHub CLI |
| gog | 0.9.0 | Google Workspace CLI |
| psql | 16.x | PostgreSQL client (connects to DB VPS) |

### Database VPS Software (76.13.194.120)

| Software | Version | Purpose | Port |
|----------|---------|---------|------|
| PostgreSQL | 16.11 | Database engine | 5432 (KVM2 only) |
| pgvector | 0.6.0 | Vector similarity search extension | — |
| PostgREST | 14.3 | Auto REST API from PostgreSQL | 3000 (localhost) |
| NocoDB | latest | Spreadsheet-like monitoring dashboard | 8080 (localhost) |
| nginx | 1.24.x | Reverse proxy + API key auth | 80, 443 |
| fail2ban | active | Brute-force protection | — |
| Docker | 29.2.1 | Runs NocoDB container | — |

### Database VPS Security

| Layer | What |
|-------|------|
| **Firewall (UFW)** | Port 22 (SSH), 80/443 (HTTP/S) open to all. Port 5432 (PostgreSQL) open to KVM2 only |
| **SSH** | Key-only auth. Password login disabled. Root = prohibit-password |
| **PostgreSQL** | `openclaw_app` can connect from KVM2 IP only. `nocodb_reader` from Docker/localhost only |
| **PostgREST** | Listens on localhost:3000 only. Exposed via nginx with API key |
| **nginx API key** | All `/api/` requests require `X-API-Key` header |
| **fail2ban** | Auto-blocks repeated failed SSH attempts |

### SSH Access

SSH config at `C:\Users\Wayan\.ssh\config`:

```
Host zuma
    HostName 76.13.194.103
    User root
    IdentityFile ~/.ssh/id_ed25519

Host postgresql
    HostName 76.13.194.120
    User root
    IdentityFile ~/.ssh/id_ed25519
```

Connect: `ssh zuma` (agents) or `ssh postgresql` (database)

DB VPS root password: see `VPS_DB_PASS` in `.env` (SSH key auth preferred, password as fallback)

Agent VPS → DB VPS connectivity verified (both psql direct and PostgREST API).

### Database Credentials

> **All passwords in `.env` file** — never in .md files (they get sent to LLM prompts)

| User | Permissions | Used By | `.env` Key |
|------|-------------|---------|------------|
| `openclaw_app` | Full owner of raw/core/mart/portal schemas | Atlas, Apollo (direct psql) | `PG_PASS_APP` |
| `nocodb_reader` | SELECT only on all schemas | NocoDB dashboard | `PG_PASS_NOCODB` |
| `postgrest_auth` | Authenticator (switches roles) | PostgREST service | `PG_PASS_POSTGREST` |
| `postgrest_anon` | (no login) SELECT on mart schema only | Unauthenticated API | — |
| `postgrest_agent` | (no login) SELECT/INSERT/UPDATE on raw+core, SELECT on mart | Authenticated agent API | — |

**API Key** (for nginx): see `POSTGREST_API_KEY` in `.env`
**JWT Secret** (for PostgREST): see `POSTGREST_JWT_SECRET` in `.env`

### Agent → Database Connection Examples

```bash
# Direct PostgreSQL (from KVM2 / Atlas / Apollo)
PGPASSWORD="$PG_PASS_APP" psql -h 76.13.194.120 -U openclaw_app -d openclaw_ops

# REST API via PostgREST (from anywhere)
curl -H "X-API-Key: $POSTGREST_API_KEY" http://76.13.194.120/api/

# Health check
curl http://76.13.194.120/health
```

### Backup Strategy (DBA Training)

| Schedule | What | Retention |
|----------|------|-----------|
| Daily 03:00 WIB | `pg_dump openclaw_ops` → gzipped | 7 days |
| Weekly Sunday 03:00 WIB | `pg_dumpall` → gzipped | 4 weeks |
| Hostinger | VPS-level auto-backup (if enabled) | Per plan |

Backup location: `/root/backups/` on DB VPS
Backup script: `/root/backups/backup.sh`
Cron: `0 3 * * * /root/backups/backup.sh`

### Resource Warning

Each VPS has only **2 CPU cores**. Avoid heavy parallel load. Sequential preferred.

### NocoDB Dashboard Access

| Property | Value |
|----------|-------|
| URL (direct) | `http://76.13.194.120:8080/dashboard` |
| URL (nginx) | `http://76.13.194.120/nocodb/` |
| SuperAdmin email | see `NOCODB_ADMIN_EMAIL` in `.env` |
| SuperAdmin password | see `NOCODB_ADMIN_PASS` in `.env` |
| Data Source | "OpenClaw Ops" → connection "OpenClaw Ops DB" |
| Database | `openclaw_ops` |
| Schemas exposed | `core`, `mart`, `raw` |
| DB user | `nocodb_reader` (password: see `PG_PASS_NOCODB` in `.env`) |
| Permissions | Allow Data Write/Edit: ✅ | Allow Schema Change: ❌ |
| Status | ✅ Connected, test successful. Portal + raw tables visible. No tables in core/mart yet. |

---

## 4. AGENT CONFIGURATION

### 3 Agents

| Agent ID | Name | Role | Workspace |
|----------|------|------|-----------|
| `main` | Iris ✨ | Lead Coordinator / PM | `/root/.openclaw/workspace/` |
| `ops` | Atlas 🏔️ | OPS Worker (Stock, Warehouse, Logistics) | `/root/.openclaw/workspace-ops/` |
| `rnd` | Apollo 🎯 | R&D Worker (Product Dev, QC, Materials) | `/root/.openclaw/workspace-rnd/` |

### Access Commands

```bash
openclaw tui --session agent:main:main    # Iris
openclaw tui --session agent:ops:main     # Atlas
openclaw tui --session agent:rnd:main     # Apollo
```

### Workspace Files (Each Agent Has)

| File | Purpose |
|------|---------|
| `IDENTITY.md` | Agent name, persona, emoji |
| `SOUL.md` | Core principles, personality, boundaries |
| `USER.md` | Who they serve, PICs, communication style |
| `AGENTS.md` | Role definition, tasks, rules, credentials management |
| `MEMORY.md` | Knowledge base (Iris only for now) |
| `BOOTSTRAP.md` | OpenClaw boot instructions |
| `HEARTBEAT.md` | Heartbeat config |
| `TOOLS.md` | Available tools reference |
| `.gitignore` | Blocks .env, memory/, *.log |

### Agent Personalities

**Iris ✨ — Lead Coordinator**
- Persona: Dewi Yunani pembawa pesan para dewa — penghubung antara dunia manusia dan Olympus
- Emoji: ✨
- Role: Reviews and approves Atlas & Apollo's work, coordinates cross-department, manages cron jobs via Notion, escalates to Wayan
- Does NOT do worker tasks — she's a reviewer/coordinator
- Reports to: CI Team (Nisa, Wayan, Wafi), Bu Dini Tri Mart (Ops Manager)

**Atlas 🏔️ — OPS Worker**
- Persona: Titan Yunani yang memikul beban dunia
- Emoji: 🏔️
- Role: Pull stock data from Accurate API, fill GSheets, analyze inventory depth, send insight emails
- DATA MOVER — never calculates, GSheet formulas do all math
- PICs: Mas Bagus (Merchandiser), Mbak Virra (Allocation), Bu Dini (Ops Manager), Mbak Citra/Sari (Purchasing), Galuh/Nabila (Inventory), Mbak Fifi (Branch)

**Apollo 🎯 — R&D Worker**
- Persona: Dewa Yunani cahaya, seni, dan kesempurnaan
- Emoji: 🎯
- Role: Track product timelines, monitor material sourcing, process QC reports, compile cost breakdowns
- DATA MOVER — same rules as Atlas
- PICs: Mbak Dewi (R&D Manager), Mbak Desyta (Product Designer Supervisor), Yuda (Product Designer)

### Universal Agent Rules

1. **DATA MOVER** — Pull raw data, paste to GSheet. Never calculate manually.
2. Always **clear raw data tabs completely** before writing new data.
3. Always add `last_updated_by` (agent name) and `last_updated_at` (WIB timestamp).
4. Follow SOP exactly — no shortcuts, no improvisation.
5. Max **2 revision attempts**. After 2, escalate.
6. **Never use browser** — CLI tools only (gog, curl, gh).
7. Write to memory after every task.
8. **All communication in Bahasa Indonesia**.
9. Update Notion status after every task.

---

## 5. LLM MODEL HIERARCHY

### 3 Providers

| Provider | Auth Mode | Purpose |
|----------|-----------|---------|
| Anthropic | Token (OAuth via Anthropic account on VPS) | Premium — Claude Sonnet 4.5 |
| Kimi Coding | API key | Budget coding — K2.5 ($3.10/M tokens) |
| OpenRouter | API key | Budget fallback — DeepSeek V3.2 ($0.53/M) + Gemini Flash-Lite ($0.50/M) |

### Per-Agent Model Hierarchy

| Agent | Primary | Fallback 1 | Fallback 2 | Heartbeat |
|-------|---------|------------|------------|-----------|
| Iris | `anthropic/claude-sonnet-4-5` ($18/M) | `kimi-coding/k2p5` ($3.10/M) | `openrouter/deepseek/deepseek-chat` ($0.53/M) | `gemini-2.5-flash-lite` ($0.50/M) |
| Atlas | `kimi-coding/k2p5` ($3.10/M) | `openrouter/deepseek/deepseek-chat` ($0.53/M) | `anthropic/claude-sonnet-4-5` (emergency) | `gemini-2.5-flash-lite` |
| Apollo | `kimi-coding/k2p5` ($3.10/M) | `openrouter/deepseek/deepseek-chat` ($0.53/M) | `anthropic/claude-sonnet-4-5` (emergency) | `gemini-2.5-flash-lite` |

**Why?** Iris (PM) needs smart reasoning = Sonnet primary. Atlas & Apollo (workers) do repetitive data tasks = Kimi is enough. Sonnet only for emergencies.

### Model Aliases

| Alias | Model |
|-------|-------|
| `sonnet` | `anthropic/claude-sonnet-4-5` |
| `kimi` | `kimi-coding/k2p5` |
| `deepseek` | `openrouter/deepseek/deepseek-chat` |
| `flash-lite` | `openrouter/google/gemini-2.5-flash-lite` |

Switch in chat: `/model kimi`, `/model sonnet`, etc.

### Other Settings

| Setting | Value |
|---------|-------|
| Heartbeat interval | Every 30 min |
| Heartbeat model | `gemini-2.5-flash-lite` (cheapest) |
| Subagent model | `kimi-coding/k2p5` |
| Subagent maxConcurrent | 8 |
| Agent maxConcurrent | 4 |
| Compaction mode | safeguard |

### Cost Estimate

| Item | Monthly |
|------|---------|
| VPS Hostinger KVM 2 — Agents (76.13.194.103) | ~$7 |
| VPS Hostinger KVM 2 — Database (76.13.194.120) | ~$7 |
| LLM costs (estimated) | ~$49 |
| **Total Phase 1** | **~$63/month** |

vs All-Sonnet: ~$187/month (**70% savings**)

---

## 6. SKILLS & MCP STATUS

### Currently Ready (9/49)

| Skill | How Installed | Purpose | Auth Status |
|-------|---------------|---------|-------------|
| 🐙 `github` | `apt install gh` + GH_TOKEN env | GitHub: issues, PRs, CI, API | ✅ Authed (database-zuma) |
| 🎮 `gog` | Built from source (Go 1.25) | Google: Gmail, Sheets, Drive, Docs | ✅ OAuth'd (harveywayan@gmail.com) |
| 📝 `notion` | NOTION_API_KEY env var | Notion: pages, databases, blocks | ✅ Verified working |
| 📦 `clawhub` | Bundled | Skill store installer | ✅ Ready |
| 📦 `mcporter` | Bundled | MCP server manager | ✅ Ready |
| 📦 `skill-creator` | Bundled | Create custom agent skills | ✅ Ready |
| 🧵 `tmux` | Bundled | Remote-control tmux sessions | ✅ Ready |
| 🌤️ `weather` | Bundled | Weather forecasts (no API key) | ✅ Ready |
| 📦 `bluebubbles` | Bundled | iMessage plugin (not needed) | ✅ Ready |

### Key Pending

| What | Blocker | Priority |
|------|---------|----------|
| Telegram routing | Need bot groups + chat IDs | MEDIUM |
| Accurate Online API | Need credentials from IT | HIGH |

### How Each Skill Was Installed

**gh CLI (GitHub):**
```bash
apt-get install -y gh
echo 'GH_TOKEN=ghp_...' >> /root/.openclaw/.env
# Note: Don't use `gh auth login --with-token` — see Gotcha #3
```

**gog CLI (Google Workspace):**
```bash
# Ubuntu 24.04 apt Go is 1.22, too old. Need 1.25+ (see Gotcha #2)
wget https://go.dev/dl/go1.25.0.linux-amd64.tar.gz
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.25.0.linux-amd64.tar.gz
export PATH=/usr/local/go/bin:$PATH  # Also in /root/.bashrc

apt-get install -y make
git clone https://github.com/steipete/gogcli.git /tmp/gogcli
cd /tmp/gogcli && make
cp bin/gog /usr/local/bin/gog
rm -rf /tmp/gogcli /tmp/go1.25.0.linux-amd64.tar.gz
```

**Notion:**
```bash
echo 'NOTION_API_KEY=ntn_...' >> /root/.openclaw/.env
# That's it — no binary needed
```

### gog OAuth Setup — ✅ COMPLETED

| Property | Value |
|----------|-------|
| Email | `harveywayan@gmail.com` |
| GCP Project | `harvey-wayan-ai` |
| Client name | `openclaw-zuma` |
| Services | docs, drive, gmail, sheets |
| Credentials file | `/root/.config/gogcli/credentials-openclaw-zuma.json` |
| Keyring file | `/root/.config/gogcli/keyring` (encrypted) |
| Keyring passphrase | Set via `GOG_KEYRING_PASSWORD` env var in `.env` |
| Future migration | `iris-openclaw@zuma.id` (later) |

**For non-interactive/cron use**: `GOG_KEYRING_PASSWORD` must be set in environment (value in `.env`, added to `/root/.openclaw/.env` on VPS). See Gotcha #8.

**Verified working**:
- `gog auth list` — shows account + services
- `gog sheets metadata <id>` — reads GSheet tab info
- `gog gmail search 'in:inbox'` — reads inbox

---

## 7. CREDENTIALS & SECURITY

### Where Credentials Live

**Local (Wayan's PC):**
```
D:\...\0. openclaw project for OPS\.env
Contains: VPS_PASS, KIMI_API_KEY, OPENROUTER_API_KEY, GITHUB_PAT, NOTION_API_KEY
```

**VPS — Shared:**
```
/root/.openclaw/.env              <-- Real credentials (GH_TOKEN, NOTION_API_KEY, GOG_KEYRING_PASSWORD)
/root/.openclaw/.env.template     <-- Reference template (no real values)
```

**VPS — LLM Auth (same for all 3 agents):**
```
/root/.openclaw/agents/main/agent/auth-profiles.json  <-- Iris
/root/.openclaw/agents/ops/agent/auth-profiles.json   <-- Atlas
/root/.openclaw/agents/rnd/agent/auth-profiles.json   <-- Apollo
```

Auth profiles structure:
```json
{
  "profiles": {
    "anthropic:anthropic_api_key_zuma": { "type": "token", "provider": "anthropic" },
    "openrouter:zuma": { "type": "api_key", "provider": "openrouter" },
    "kimi-coding:zuma": { "type": "api_key", "provider": "kimi-coding" }
  }
}
```

**VPS — Per-agent env:**
```
/root/.openclaw/workspace/.env          <-- Iris-specific
/root/.openclaw/workspace-ops/.env      <-- Atlas-specific
/root/.openclaw/workspace-rnd/.env      <-- Apollo-specific
```

### Security Rules

| Rule | Why |
|------|-----|
| Never put credentials in .md files | .md files get sent to LLM prompts — secrets leak |
| Never push .env to GitHub | Already in .gitignore |
| Never share auth-profiles.json | Contains actual API keys/tokens |
| New credentials → ask Wayan first | Central control |

---

## 8. OPENCLAW CONFIGURATION REFERENCE

Main config: `/root/.openclaw/openclaw.json`

### Key Sections

**Agent Defaults (applies to Iris, overridden by Atlas/Apollo):**
```json
"agents": {
  "defaults": {
    "model": {
      "primary": "anthropic/claude-sonnet-4-5",
      "fallbacks": ["kimi-coding/k2p5", "openrouter/deepseek/deepseek-chat"]
    },
    "compaction": { "mode": "safeguard" },
    "maxConcurrent": 4,
    "subagents": { "model": "kimi-coding/k2p5", "maxConcurrent": 8 },
    "heartbeat": { "every": "30m", "model": "openrouter/google/gemini-2.5-flash-lite" }
  }
}
```

**Worker Override (Atlas & Apollo):**
```json
{
  "id": "ops",
  "workspace": "/root/.openclaw/workspace-ops",
  "agentDir": "/root/.openclaw/agents/ops/agent",
  "model": {
    "primary": "kimi-coding/k2p5",
    "fallbacks": ["openrouter/deepseek/deepseek-chat", "anthropic/claude-sonnet-4-5"]
  }
}
```

**Gateway:**
```json
"gateway": { "port": 18789, "mode": "local", "bind": "loopback", "auth": { "mode": "token" } }
```

**Telegram (enabled, not fully configured):**
```json
"channels": { "telegram": { "enabled": true, "groupPolicy": "allowlist", "streamMode": "partial" } }
```

### Check Commands

```bash
openclaw models status                  # All agents
openclaw models status --agent ops      # Specific agent
openclaw skills list                    # All skills
openclaw skills info <skill-name>       # Skill details
```

---

## 9. GITHUB REPOSITORY

| Property | Value |
|----------|-------|
| Repo | https://github.com/database-zuma/openclaw-ops-rnd |
| Visibility | Public |
| Account | `database-zuma` |
| Auth on VPS | GH_TOKEN env var |

**Note:** Stale repo at `wayansuardyana-code/openclaw-ops-rnd` exists — delete manually.

---

## 10. NOTION INTEGRATION

| Property | Value |
|----------|-------|
| Integration name | `openclaw-zuma-vps` |
| API key location | VPS: `/root/.openclaw/.env` (NOTION_API_KEY) |
| Connected page | "OpenClaw HERE!" |
| Page ID | `30031616-a0d5-807a-8342-f72d4b7c8077` |
| API version to use | **`2022-06-28`** (NOT 2025-09-03 — see Gotcha #1) |
| Status | ✅ Verified working |

### Notion PM Structure — ✅ Created (Hierarchical: Projects → Tasks)

```
📌 Projects (container)          💫 Tasks (work items)
├── Control Stock PoC    ←─────── Daily Update, Review Output
├── R&D Status Reports   ←─────── R&D Status Report
├── System Setup         ←─────── gog OAuth, Telegram, Accurate API
└── Incidental           ←─────── (one-off unrelated tasks)
         ↑ Relation: Tasks.Project → Projects ↑
```

**Projects Database 📌**: `30031616-a0d5-8194-96b3-d09fbf4da2cc`

| Field | Type | Options |
|-------|------|---------|
| Project (title) | Title | |
| Status | Select | Planning, Active, On Hold, Completed, Archived |
| Department | Select | OPS, R&D, All, Cross-Department |
| Owner Agent | Select | Atlas, Apollo, Iris, Layer 2 |
| Priority | Select | High, Medium, Low |
| Start Date / Target End | Date | |
| Description | Rich Text | |

**Tasks Database 💫**: `30031616-a0d5-81ac-86f0-e108677a6d0a`

| Field | Type | Options |
|-------|------|---------|
| Task (title) | Title | |
| Status | Select | Queued, Running, Done, Failed, Escalated, Cancelled |
| Assigned Agent | Select | Atlas, Apollo, Iris |
| Priority | Select | High, Medium, Low |
| Type | Select | Cron, Manual, Review, Setup |
| Schedule | Rich Text | e.g. "Daily 08:30 WIB" |
| Notes | Rich Text | |
| Last Run | Date | |
| Department | Select | OPS, R&D, All |
| **Project** | **Relation** | **→ Projects DB (WAJIB, no orphan tasks)** |

**Seeded projects (4):**

| Project | ID | Status |
|---------|----|--------|
| Control Stock PoC | `30031616-a0d5-8110-9daa-f5ebf2d4ec34` | Active |
| R&D Status Reports | `30031616-a0d5-81fe-a1ee-d157080795df` | Planning |
| System Setup | `30031616-a0d5-81f5-ad9e-e13a4adf3833` | Active |
| Incidental | `30031616-a0d5-814f-8642-f983282b15e5` | Active |

**Agent Notion permissions:**
- Iris ✨: Full PM (create/assign/review tasks & projects)
- Atlas 🏔️ / Apollo 🎯: Update OWN task status/notes/last-run only

**Skills**: `NOTION-SKILLS.md` in each workspace (GitHub + needs sync to VPS).

Already shared with `openclaw-zuma-vps` integration (auto-inherited from parent page).

---

## 11. PHASE 1 ROADMAP

### Control Stock PoC — Atlas's First Task

**Goal:** Atlas pulls inventory data daily, fills GSheet, analyzes stock depth, emails Merchandiser.

### Done ✅

| # | Task |
|---|------|
| 1 | VPS setup + SSH key auth |
| 2 | OpenClaw installed, gateway running |
| 3 | 3 agents configured with full personality MDs |
| 4 | LLM model hierarchy (3 providers, per-agent overrides) |
| 5 | Auth profiles for all 3 agents |
| 6 | GitHub repo at database-zuma/openclaw-ops-rnd |
| 7 | `gh` CLI installed + authed |
| 8 | `gog` CLI built + installed (binary ready) |
| 9 | `gog` OAuth completed (harveywayan@gmail.com, 4 services) |
| 10 | `gog` keyring fix for non-interactive use (GOG_KEYRING_PASSWORD) |
| 11 | GSheet + Gmail verified working via gog |
| 12 | Notion skill enabled + API verified |
| 13 | Telegram plugin enabled (bot token set) |
| 14 | Athena → Iris ✨ rename (all VPS + GitHub files) |
| 15 | README rewritten (engaging narrative style) |
| 16 | Notion PM databases created (Projects + Tasks, 4 projects, 6 tasks) |
| 17 | NOTION-SKILLS.md synced to all 3 VPS workspaces |
| 18 | DB VPS (KVM 2) purchased & provisioned (76.13.194.120) |
| 19 | PostgreSQL 16 + pgvector installed & running |
| 20 | Database `openclaw_ops` created with 4 schemas (raw, core, mart, portal) |
| 21 | 5 DB users created (openclaw_app, nocodb_reader, postgrest_auth, postgrest_anon, postgrest_agent) |
| 22 | 9 raw tables designed (ddd_stock/sales, ljbb_stock, mbb_stock/sales, ubb_stock/sales, iseller_sales, load_history) |
| 23 | 4 portal reference tables loaded (store=326, kodemix=5464, hpprsp=935, stock_capacity=57) |
| 24 | PostgREST 14.3 installed & running (REST API for agents) |
| 25 | NocoDB running in Docker (spreadsheet-like monitoring dashboard) |
| 26 | nginx configured (PostgREST proxy at /api/ with API key, NocoDB at /nocodb/, health check) |
| 27 | UFW firewall configured (PostgreSQL port 5432 open to Agent VPS only) |
| 28 | fail2ban active for SSH protection |
| 29 | Backup script + daily cron at 03:00 WIB (pg_dump daily 7d retention, pg_dumpall weekly 4wk) |
| 30 | Agent VPS → DB VPS connectivity verified (psql direct + PostgREST API) |
| 31 | New OAuth client secret created on GCP (****7pcH, Feb 7 2026) |
| 32 | GSheet formula strategy RESOLVED — Supabase/PostgreSQL handles all calculations, GSheet is dashboard only |

### Pending ⬜

| # | Task | Blocker | Priority |
|---|------|---------|----------|
| 1 | Telegram groups + routing config | Wayan creates bots/groups | MEDIUM |
| 2 | Accurate Online API credentials | Ask IT/admin | HIGH |
| 3 | Control Stock SOP walkthrough | Wayan guides | HIGH |
| 4 | Design core.* tables (normalized star schema) | Needs SOP walkthrough | HIGH |
| 5 | Design mart.* views (reporting layer) | Needs core.* tables | HIGH |
| 6 | Write skill/SOP docs for Atlas (3 skill types) | Needs SOP + DB design | HIGH |
| 7 | Set up cron jobs (Atlas 8:30 WIB, Apollo 8:45 WIB) | Needs tasks defined | MEDIUM |
| 8 | Share GSheet edit access with harveywayan@gmail.com | GSheet owner action | HIGH |
| 9 | End-to-end test | Needs everything above | HIGH |
| 10 | 5-day parallel run (agent vs human) | Needs e2e passing | HIGH |

### Control Stock GSheet Reference

| Property | Value |
|----------|-------|
| Spreadsheet ID | `1qInTrRUOUi2983vefS8doS5Pt3jC2yftQAG99yYlVOE` |
| Title | Control Stock |
| Locale | en_GB |
| TimeZone | Asia/Bangkok |
| Total tabs | **36** (discovered via `gog sheets metadata`) |
| Largest tab | source_sell through (mtd) — 25,427 rows |
| PO tab rows | ~1,397 |

**Tab categories:**
- **Core**: PO, Global, WH BOX, DATA AWAL, Update Stock, Summary Kode MIX, forNotionIntegrator
- **TIER (old)**: TIER 1, TIER 2, TIER 3, TIER 5, TIER 8, TIER 1 KODE MIX, TIER 2 KODE MIX, TIER 3 KODE MIX, TIER 4
- **TIER (new)**: TIER 1 (NEW), TIER 2 (NEW), TIER 3 (NEW), Hitung Tier, All Tier, All Tier Value
- **Product lines**: KIDS, SERIES, BABY, Freya & Kim, Slide Max
- **Source data**: source_sell through (mtd)
- **Meeting/Misc**: Meeting TIER 1 261024, T1 Sort, Pivot Table 6, CATATAN, Sheet38, Sheet40, Sheet54, tidak dipakai deck

---

## 12. FUTURE PHASES

**Phase 2 — Expand Layer 1**: More agents on VPS. CEMES (sales), FATAL (accounting). Each agent owns its own GSheets.

**Phase 3 — Layer 2 Overseers**: Mac Mini M4. Sonnet model. Reviews Layer 1 via Notion every 30 min. SSH into VPS to fix issues.

**Phase 4 — Jarvis (Layer 3)**: C-level dashboard. Cross-department insights.

---

## 13. QUICK REFERENCE

```bash
# SSH
ssh zuma

# Agent TUI
openclaw tui --session agent:main:main    # Iris
openclaw tui --session agent:ops:main     # Atlas
openclaw tui --session agent:rnd:main     # Apollo

# Status
openclaw models status
openclaw skills list
```

### VPS File Paths
```
/root/.openclaw/
├── openclaw.json                          <-- Main config
├── .env                                   <-- Shared credentials
├── agents/{main,ops,rnd}/agent/auth-profiles.json
├── workspace/                             <-- Iris
├── workspace-ops/                         <-- Atlas
├── workspace-rnd/                         <-- Apollo
└── cron/                                  <-- Not configured yet
```

### Local File Paths
```
D:\...\0. openclaw project for OPS\
├── 00-SETUP-GUIDE.md              <-- THIS FILE
├── 01-architecture-draft.md       <-- Planning notes
├── 02-work-plan.md                <-- 36-task work plan
├── 03-session-progress.md         <-- Progress log + gotchas
├── .env                           <-- Credentials (gitignored)
```

---

## 14. TECHNICAL GOTCHAS & SOLUTIONS

Check here before debugging — these are problems we already solved.

### #1: Notion API Version Incompatibility
- **Problem**: SKILL.md says use `Notion-Version: 2025-09-03` → returns `401 unauthorized`
- **Fix**: Use `Notion-Version: 2022-06-28` instead
- **Impact**: All Notion API calls from VPS must use the older header

### #2: Go Too Old for gog Build
- **Problem**: `apt install golang-go` = Go 1.22. gogcli needs 1.25+
- **Fix**: Manual install from https://go.dev/dl/go1.25.0.linux-amd64.tar.gz → `/usr/local/go/`
- **Post-fix**: `export PATH=/usr/local/go/bin:$PATH` in `/root/.bashrc`

### #3: gh CLI Auth Scope Error
- **Problem**: `gh auth login --with-token` fails — PAT missing `read:org` scope
- **Fix**: Don't use `gh auth login`. Set `GH_TOKEN=ghp_...` as env var. `gh` reads it automatically.

### #4: `make` Not on Fresh Ubuntu
- **Problem**: `make` not installed by default on Ubuntu 24.04
- **Fix**: `apt-get install -y make`

### #5: SSH Port Forwarding Warning
- **Problem**: `bind [127.0.0.1]:18789: Address already in use` on SSH connect
- **Impact**: Warning only — SSH works fine. Gateway port already bound.
- **Fix**: Ignore, or remove `LocalForward` from SSH config if not needed

### #6: GitHub MCP Tools Fail with "Not Found"
- **Problem**: `mcp_github_push_files` and `mcp_github_create_or_update_file` return `McpError: MCP error -32603: Not Found` when targeting `database-zuma/openclaw-ops-rnd`.
- **Root cause**: Unknown — possibly auth issue with MCP tool, or repo owner case sensitivity (`database-Zuma` vs `database-zuma`).
- **Fix**: Clone repo via git CLI with PAT in URL, make changes locally, commit, push:
  ```bash
  git clone https://<PAT>@github.com/database-zuma/openclaw-ops-rnd.git /tmp/openclaw-repo
  cd /tmp/openclaw-repo
  # make changes...
  git config user.email "database-zuma@users.noreply.github.com"
  git config user.name "database-zuma"
  git add -A && git commit -m "message" && git push origin main
  rm -rf /tmp/openclaw-repo  # cleanup
  ```
- **Note**: `gh` CLI is installed on VPS but NOT on Wayan's Windows machine.

### #7: Claude Write Tool Won't Overwrite Existing Files
- **Problem**: Claude's `mcp_write` tool refuses to overwrite files that already exist in a git clone (returns "File already exists. Use edit tool instead").
- **Fix**: Use `cat > file << 'EOF' ... EOF` via bash for bulk file overwrites in temp directories.

### #8: gog Keyring Needs TTY for Passphrase
- **Problem**: `gog auth list` fails with `no TTY available for keyring file backend password prompt; set GOG_KEYRING_PASSWORD`
- **Root cause**: gog encrypts OAuth tokens in a keyring file. On headless VPS / cron jobs, there's no TTY to prompt for the passphrase.
- **Fix**: Set `GOG_KEYRING_PASSWORD=openclaw-zuma-2026` as environment variable in `/root/.openclaw/.env`
- **For cron**: Ensure cron jobs source the `.env` file before running gog commands, or export the var in the cron script.

---

## 15. TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| SSH asks for password | Check `~/.ssh/id_ed25519`, verify SSH config IdentityFile |
| Can't access GSheet | Verify `GOG_KEYRING_PASSWORD` env var is set (Gotcha #8) |
| Notion 401 error | Use `Notion-Version: 2022-06-28` (Gotcha #1) |
| Model fallback loop | `openclaw models status` — check API key validity |
| Gateway port in use | `lsof -i :18789`, kill process, restart |
| Agent wrong data | Check SOP, verify API → GSheet column mapping |
| Telegram silent | Verify bot token, allowedChatIds, bot in group |
| VPS slow | `htop` — 2 cores, don't run parallel |
| `gog` not found | Check `/usr/local/bin/gog` or `export PATH` |
| GitHub MCP push fails | Use git clone + PAT approach (Gotcha #6) |

---

## 16. FILES IN THIS FOLDER

```
0. openclaw project for OPS/
├── 00-SETUP-GUIDE.md              <-- THIS FILE
├── 01-architecture-draft.md       <-- Planning decisions & research
├── 02-work-plan.md                <-- 36-task work plan
├── 03-session-progress.md         <-- Session log + technical gotchas
├── .env                           <-- Credentials (NEVER push)
├── .gitignore
├── AGENTS-ops.md                  <-- Atlas AGENTS.md backup
├── AGENTS-rnd.md                  <-- Apollo AGENTS.md backup
```

---

## CRITICAL CONSTRAINTS

| Constraint | Details |
|------------|---------|
| No Railway | Abandoned — Hostinger VPS |
| No browser | Crashes VPS. CLI only |
| No keys in .md | Gets sent to LLM prompts |
| No shared GSheets | Each agent owns its own |
| Timezone always | `Asia/Jakarta` (WIB) |
| Max 2 revisions | Then escalate |
| Bahasa Indonesia | All agent communication |
| No secrets in git | .env only |
| Sequential preferred | 2 CPU cores |

---

## WHAT TO DO NEXT

```
✅ Google Sheets & Gmail UNLOCKED (gog OAuth'd, verified working)
✅ DB VPS fully operational (PostgreSQL + PostgREST + NocoDB)
✅ Portal reference data loaded (store, kodemix, hpprsp, stock_capacity)
✅ Raw staging tables designed (9 tables, awaiting real data)
✅ GSheet formula strategy RESOLVED (PostgreSQL = brain, GSheet = dashboard)

BLOCKED ON WAYAN:
1. Get Accurate Online API credentials from IT
   → Can't fill raw.* tables without API access

2. Walk through Control Stock SOP (36 tabs):
   a. Which tabs are "raw data" vs "formula" vs obsolete?
   b. How the EMAIL report looks
   c. What data comes from Accurate API vs manual entry?
   → Can't design core.* and mart.* without understanding the business logic

3. Share Control Stock GSheet edit access with harveywayan@gmail.com
   → Currently 403 Forbidden on write

4. Create Telegram bots/groups via @BotFather
   → Not critical-path but needed before E2E

AFTER BLOCKERS CLEARED:
5. Design core.* tables (dim_product, fact_stock, etc.)
6. Design mart.* views (v_control_stock, v_tier_summary, v_depth_alert)
7. Write Atlas skill/SOP docs (Data Mover, Data Processor, Report Builder)
8. Configure cron jobs → E2E test → 5-day parallel run
```

---

*Reflects actual system state as of 8 Feb 2026. Historical decisions in 01-architecture-draft.md, 36-task plan in 02-work-plan.md.*
