# Draft: Hierarchical OpenClaw Architecture — Zuma Indonesia

> Complete notes from full planning session. All decisions, research, concerns, and solutions captured.
> 
> **PROJECT PRIORITY**: Layer 1 = 90% of the project (the real work).
> Layer 2 = bonus (cleaner analytics). Layer 3 = bonus (easier management).

---

## 1. THE BIG PICTURE

Zuma Indonesia (footwear brand) wants to replace repetitive human admin work with AI agents.
The hierarchy maps to the company org chart:

```
LAYER 3 — C-LEVEL ─────────────────────────────────────────
  1 Mac Mini M4 (to purchase)
  Jarvis (existing AI assistant, upgraded)
  For: CEO + Top Management
  Gets: consolidated reports, strategic insights, anomaly alerts
  Status: FUTURE — not in current scope

LAYER 2 — DEPARTMENT LEVEL ─────────────────────────────────
  2-3 Mac Mini M4s (to purchase)
  OpenClaw agents using HEARTBEAT.md (every 30 min)
  For: Department supervisors/overseers
  Does: monitor Layer 1, routine & on-demand reports, data analysis
  Self-healing: full auto-fix (SSH into Layer 1 VPS, restart, report after)

LAYER 1 — DIVISION LEVEL ──────────────────────────────────
  5-7 cheap VPS (~$5/mo each, 8GB RAM)
  OpenClaw agents using Cron jobs
  For: Individual divisions within departments
  Does: data pulling, processing, report generation — exactly as human admins do today
  Multi-agent: 1-2 agents per VPS Gateway where sensible
```

### Zuma Departments & Divisions

| Department | Divisions (each = Layer 1 agent) | Layer 2 Overseer |
|---|---|---|
| OPS (Operations) | Branch Ops, Warehouse, Logistics | Overseer-OPS |
| CEMES (Marketing) | Online Sales, Promo & Campaign, Content | Overseer-CEMES |
| FATAL (Finance) | Accounting, Tax, Budgeting | Overseer-FATAL |
| R&D | Product Development, QC | Shared overseer |
| HRGA | HR, General Affairs | Shared overseer |
| BD & Wholesale | Business Development, Wholesale | Shared overseer |

---

## 2. ALL DECISIONS MADE

### Architecture Decisions

| Decision | Choice | Why |
|---|---|---|
| Deployment model | Hybrid: cheap VPS (Layer 1) + Mac Mini M4 (Layer 2/3) | Balance cost, reliability, no single point of failure |
| Multi-agent per machine | YES — one Gateway hosts multiple agents | Cheaper, simpler. One Gateway = one process, agents just share it |
| Layer 1 scheduling | OpenClaw Cron (isolated sessions) | Exact timing, fresh context per run, no history buildup |
| Layer 2 scheduling | HEARTBEAT.md (every 30 min) | Context-aware, batches checks, only acts when needed |
| Communication bus | Telegram groups (one per department) | Simple, native OpenClaw support, humans can lurk and see everything |
| Structured tracking | Notion (greenfield, new workspace) | Task boards, report storage, management dashboards |
| LLM provider | Anthropic Claude | Haiku for Layer 1 (cheap, routine), Sonnet for Layer 2 (smart, analytical) |
| Data access | API-first — NO browser automation | Browser = crashes & lag. API = lightweight, reliable, fast |
| Overseer autonomy | Full auto-fix | Detect → restart via SSH → verify → report after the fact |
| Railway | DROPPED | Analytics agent moved to Mac Mini, saves $20+/mo |
| Layer 3 (Jarvis) | Future scope | Separate planning session later |
| Skills architecture | Reference-based (lightweight SKILL.md + external SOP docs) | Keeps context window lean |
| Context window mgmt | Isolated cron sessions + auto-compaction + memory flush | Prevents context exhaustion |
| Security | Sandboxing + tool restrictions + SSH keys + Telegram allowlists | Complex system needs defense in depth |

### Hardware Decisions

| Item | Spec | Status | Cost |
|---|---|---|---|
| Layer 1 VPS (5-7) | 8GB RAM, 100GB, cheap provider | To purchase | ~$25-35/mo total |
| Layer 2 Mac Mini (2-3) | M4, 16GB RAM | To purchase | ~$600-800 each, one-time |
| Layer 3 Mac Mini (1) | M4, 16GB RAM | To purchase (future) | ~$600-800, one-time |
| Existing Hostinger KVM 2 | Used for coding/building | Already owned | Separate from this system |

---

## 3. HOW THINGS WORK (technical details)

### Multi-Agent on Single Machine (KEY INSIGHT)

One OpenClaw Gateway = one Node.js process = one running program.
It can host MULTIPLE agents that each have their own:
- Personality (AGENTS.md)
- Memory (workspace files)
- Telegram bot account
- Task schedule (cron/heartbeat)
- Tools (allow/deny per agent)

But they SHARE the same computer's CPU, RAM, and network.

**Hotel analogy**: The building = Gateway. Each room = Agent. Don't build a new hotel for every guest.

**Parallelism works because agents are mostly WAITING** (for API responses, LLM responses).
Active computing = ~5% of time. 95% = waiting. So multiple agents barely compete for resources.

**Config for concurrency:**
```json5
{
  cron: { maxConcurrentRuns: 2 },        // 1-3 cron jobs can overlap
  agents: { defaults: { subagents: { maxConcurrent: 8 } } }  // sub-agent parallelism
}
```

### Cron Jobs (Layer 1 Workers)

- Built-in scheduler, persists across restarts
- Isolated sessions = fresh context per run = NO context window buildup
- Model overrides per job (cheap Haiku for routine, Sonnet for complex)
- Delivery: auto-announce results to Telegram group
- Timezone: `--tz "Asia/Jakarta"`
- Storage: `~/.openclaw/cron/jobs.json`

Example:
```bash
openclaw cron add \
  --name "Daily sales report" \
  --cron "30 10 * * *" \
  --tz "Asia/Jakarta" \
  --session isolated \
  --message "Pull sales data from Accurate API, process, generate report, post to group, update Notion." \
  --announce --channel telegram --to "<GROUP_CHAT_ID>"
```

### HEARTBEAT.md (Layer 2 Overseers)

- Runs every 30 min in main session
- Reads HEARTBEAT.md checklist
- If nothing needs attention → replies HEARTBEAT_OK (suppressed, no message sent)
- If something is wrong → alerts user via Telegram DM
- Active hours: configurable (e.g., 07:00-22:00 WIB)
- Context-aware: remembers recent conversations, can follow up naturally

### Self-Healing via SSH

Layer 2 (Mac Mini) can use OpenClaw's `exec` tool to run SSH commands:
```
ssh admin@vps1-ip "openclaw health --json"     → check if alive
ssh admin@vps1-ip "openclaw gateway --force &"  → restart if dead
ssh admin@vps1-ip "openclaw cron list"          → check scheduled jobs
```

Requirements:
- SSH key pairs (passwordless) from each Mac Mini → each VPS
- Restricted SSH user on VPS (can restart OpenClaw, not root)
- Layer 2 AGENTS.md includes VPS IPs and recovery procedures

### OpenClaw Rescue Bot Pattern

For extra reliability, each VPS can run a SECOND Gateway on a different port.
This "rescue bot" can restart the main Gateway if it crashes:
```bash
openclaw --profile main gateway --port 18789      # main
openclaw --profile rescue gateway --port 19001    # rescue (lightweight, monitors main)
```

---

## 4. THE THREE CRITICAL CONCERNS (and solutions)

### CONCERN A: Skills.md & Context Window

**Problem**: Layer 1 agents need detailed step-by-step SOPs to do tasks exactly as human employees.
These SOPs can be very long. Loading everything into SKILL.md wastes context window.

**Solution: Reference-Based Skills Architecture**

```
skills/
├── pull-sales-data/
│   ├── SKILL.md              ← TINY: just name + description + "read docs/ for steps"
│   └── docs/
│       └── sop-sales-pull.md ← FULL SOP: only loaded when skill is invoked
│
├── generate-tax-invoice/
│   ├── SKILL.md              ← TINY
│   └── docs/
│       └── sop-tax-invoice.md ← FULL SOP
```

SKILL.md (always in context, ~24 tokens):
```markdown
---
name: pull-sales-data
description: Pull and reconcile daily sales data from Accurate Online + iSeller
---
When invoked, read the full procedure from `{baseDir}/docs/sop-sales-pull.md`.
Follow each step exactly. Do not skip steps. Report results to Telegram group.
```

**Token math:**
- 10 skills × 24 tokens = 240 tokens overhead (tiny ✅)
- vs. 10 skills × 2000 tokens = 20,000 tokens (massive waste ❌)
- Full SOP only loaded on-demand when skill is triggered via `read` tool

### CONCERN B: Chat History Fills Context Window

**Problem**: When user/Layer 2 chats with Layer 1 agent, conversation history fills
200K context window quickly. Performance degrades.

**Solution: Three-layer defense**

1. **Isolated cron sessions** (Layer 1 scheduled tasks):
   - Each cron run = fresh session = zero history = no buildup
   - This covers 90% of Layer 1 work (scheduled tasks)

2. **Auto-compaction** (for interactive chats):
   - OpenClaw detects when context is filling up
   - Triggers silent memory flush (saves important facts to memory/YYYY-MM-DD.md)
   - Then summarizes older conversation, keeps recent messages
   - Config: `compaction.reserveTokensFloor: 20000` (reserves 20K tokens for new messages)

3. **Smart memory instructions in AGENTS.md**:
   ```markdown
   ## Memory Rules
   - After each task, write key results to memory/YYYY-MM-DD.md
   - If anyone says "remember X", write it to MEMORY.md immediately
   - Keep MEMORY.md curated and under 2000 words
   - If a conversation is getting long, suggest: "Let me save context and start fresh"
   ```

4. **Vector memory search**:
   - OpenClaw has built-in semantic search over memory files
   - Agent can `memory_search` for relevant past context without loading everything
   - Hybrid BM25 + vector search (finds exact terms AND semantic matches)

### CONCERN C: Security & Reliability at Scale

**Problem**: 8-11 OpenClaw instances across multiple machines. Complex = risky.

**Solution: Defense in depth**

| Layer | Security Measure |
|---|---|
| **Network** | SSH key auth only (no passwords), Telegram allowlists, VPS firewall rules |
| **OpenClaw** | Per-agent tool allow/deny, sandboxing (Docker), workspace isolation |
| **Data** | API keys in `.env` files (never in prompts), per-agent auth profiles |
| **Recovery** | Rescue bot pattern, Layer 2 auto-fix via SSH, Gateway health checks |
| **Monitoring** | `openclaw health --json`, Telegram group visibility, Notion audit trail |

**Per-agent tool restrictions (critical for Layer 1):**
```json5
{
  agents: {
    list: [{
      id: "sales-agent",
      tools: {
        allow: ["exec", "read", "write", "edit", "cron"],
        deny: ["browser", "canvas", "nodes"],  // NO browser = no crashes, no unnecessary tools
      }
    }]
  }
}
```

**Reliability matrix:**
| What fails | What happens | Recovery |
|---|---|---|
| VPS goes down | Layer 2 detects silence in TG group | SSH restart, alert user |
| Gateway crashes | Rescue bot detects, restarts main | Automatic |
| Mac Mini loses power | VPS Layer 1 agents continue independently | Manual (or UPS) |
| LLM API outage | Model failover chain: Haiku → Sonnet → Opus | Automatic via OpenClaw |
| Context window full | Auto-compaction + memory flush | Automatic |
| Agent produces bad data | Layer 2 cross-checks results between agents | Alert + human review |

---

## 5. DATA SOURCES & ACCESS

### Current State (what humans do)
Admins log into web dashboards via browser, manually pull/download data,
combine in Excel/GSheets, process, generate reports.

### Target State (what agents will do)
Agents call APIs directly (no browser), process data, store in Supabase,
generate reports, post to Telegram + Notion.

| Source | Type | API Status | Priority |
|---|---|---|---|
| Accurate Online | ERP (sales, inventory, accounting, tax) | ✅ REST API exists, HMAC-SHA256 auth, reference project in codebase | HIGH — first to set up |
| Ginee | Marketplace aggregator (Shopee, Tokped, Lazada) | ✅ API available | HIGH |
| iSeller | POS system | ✅ Likely has API | MEDIUM |
| Google Sheets | Manual data (FF%, FB%, Sales Targets) | ✅ Free API | MEDIUM |
| Supabase | Central database | ✅ Already working (jarvis.sales_3mo, jarvis.stock_current) | DONE |
| Notion | Task management, reports | ✅ API available, skill on ClawHub | To set up |

### Key Zuma Metrics (from Jarvis context)
| Metric | Threshold | Who Cares |
|---|---|---|
| FF (Full Floor) % | Alert if < 70% | Virra (OPS) |
| FB (Full Box) % | Alert if < 80% | Virra (OPS) |
| Stock Minus | Alert if < 0 | Galuh, Nabila |
| Sales MTD vs Target | Alert if < 95% | Branch Managers |
| Product performance | Top/bottom by series, revenue ranking | Production Planning Meeting |
| Marketplace channel mix | Shopee vs Tokped vs Lazada | Online Sales team |

---

## 6. COST ESTIMATES

### Monthly Recurring
| Item | Cost |
|---|---|
| 5-7 cheap VPS (Layer 1) | $25-35 |
| Claude Haiku API (5-7 Layer 1 agents, ~50 cron runs/day each) | $10-20 |
| Claude Sonnet API (2-3 Layer 2 overseers, ~48 heartbeats/day each) | $15-30 |
| Notion (free tier) | $0 |
| Telegram | $0 |
| Mac Mini electricity (3-4 units) | ~$5-10 |
| **Total monthly** | **$55-95/mo** |

### One-Time Purchases
| Item | Cost |
|---|---|
| 3-4 Mac Mini M4 (16GB) @ $600-800 each | $1,800-3,200 |
| Total one-time | **$1,800-3,200** |

### Compared to Human Cost
These agents replace repetitive work across 5-7 divisions.
Even one admin salary in Indonesia = ~$300-600/mo.
System pays for itself in month 1.

---

## 7. PHASED ROLLOUT

Mac Mini NOT yet purchased. Plan must be phased.

### Phase 0: Foundation (NOW — no hardware needed)
- [ ] Set up API access: Accurate Online, Ginee, iSeller, Google Sheets
- [ ] Create Telegram group(s) + bots via @BotFather
- [ ] Design Notion workspace structure
- [ ] Document SOPs: how admins currently do each task step-by-step
- [ ] Design reference-based skills architecture (SKILL.md + docs/)
- [ ] Buy first 1-2 cheap VPS

### Phase 1: Proof of Concept (Week 1-2, 1 VPS)
- [ ] Install OpenClaw on first VPS
- [ ] Build ONE agent (e.g., Agent-Sales for OPS department)
- [ ] Create skills with reference SOP docs
- [ ] Set up cron jobs, Telegram delivery, Notion updates
- [ ] Validate end-to-end: data pull → process → report → Telegram + Notion
- [ ] USER watches TG group manually (temporary overseer)

### Phase 2: Expand Layer 1 (Week 2-4, add VPS)
- [ ] Add remaining Layer 1 agents (3-5 more across departments)
- [ ] Multi-agent routing on VPS where sensible
- [ ] All agents post to department Telegram groups + Notion
- [ ] Tune schedules, optimize token costs
- [ ] Test security: sandboxing, tool restrictions

### Phase 3: Layer 2 — Overseers (When Mac Minis purchased)
- [ ] Set up 2-3 Mac Mini M4 as department overseers
- [ ] Configure HEARTBEAT.md per department
- [ ] SSH keys from Mac Minis → all VPS
- [ ] Enable self-healing loop (auto-restart crashed agents)
- [ ] Layer 2 generates routine + on-demand reports
- [ ] Cross-agent data analysis (e.g., sales up but stock down = risk flag)

### Phase 4: Layer 3 — Jarvis/C-Level (Future)
- [ ] Upgrade Jarvis to read from Layer 1+2 output
- [ ] Dedicated Mac Mini for Layer 3
- [ ] C-level dashboard: "How is Zuma doing?" → reads all departments
- [ ] Separate planning session for this phase

---

## 8. NEW: GOOGLE WORKSPACE & DATA VALIDATION CONCERNS

### 8A. Layer 1 MUST Have Google Workspace Access

Every Layer 1 agent needs:
- **Google Sheets**: reading/writing spreadsheet data (most admin work happens here)
- **Google Docs**: generating reports, documentation
- **Google Drive**: accessing shared files, storing outputs
- **Gmail**: sending reports, receiving data from external systems
- **Supabase**: central database for processed data
- **Notion**: updating cron job task status (done / ongoing / failed + breakdown reason)

**Tool: `gog` (Google Workspace CLI for OpenClaw)**
- Official skill available on ClawHub (originally bundled with OpenClaw)
- One binary: `brew install steipete/tap/gogcli`
- Supports: Gmail, Calendar, Drive, Contacts, Tasks, Sheets, Docs, Slides, People
- OAuth-based: `gog auth add you@gmail.com --services gmail,sheets,drive,docs`
- JSON output for scripting: `gog sheets read <spreadsheetId> --range 'A1:Z100' --json`
- Can read cells, write cells, export as PDF/CSV/XLSX
- `{baseDir}` in SKILL.md can reference `gog` commands

**Notion Task Status Schema (Layer 1 must update this):**
| Field | Options |
|---|---|
| Task Name | e.g., "Daily Sales Pull - OPS" |
| Agent | VPS-1/Agent-Sales |
| Status | ✅ Done, 🔄 Ongoing, ❌ Failed |
| Failure Reason | e.g., "Accurate API timeout", "GSheet permission denied" |
| Last Run | Timestamp |
| Duration | How long the task took |
| Next Run | Cron schedule |

### 8B. THE CORE STRUGGLE: GSheet Data Processing & Validation

**The Problem (user's exact concern):**
Most admin work is GSheet work. OpenClaw agents need SQL & Python to process data,
but NOBODY in the office knows SQL or Python. So nobody can verify:
- Is the data processed correctly?
- Are the calculations right?
- Did the agent make an error?

This is a TRUST problem, not just a technical problem.

### 8C. BRAINSTORM: 5 SOLUTIONS

**SOLUTION 1: "Work IN GSheets, not OUTSIDE GSheets" (RECOMMENDED)**

Instead of: Agent reads GSheet → processes in Python → writes result back
Do this: Agent reads GSheet → writes GSheet FORMULAS → GSheet calculates

```
What agent writes to cell C2:     =SUM(B2:B50)
What agent writes to cell D2:     =C2/COUNTA(B2:B50)
What agent writes to cell E2:     =IF(C2<TARGET,"⚠️ Below Target","✅ On Track")
```

Why this works:
- Humans can CLICK on any cell and see the formula
- Humans already understand GSheet formulas
- The GSheet IS the verification — if formula is wrong, anyone can spot it
- No Python/SQL knowledge needed to audit
- Agent uses `gog` CLI to write formulas, not computed values

For complex calculations that CAN'T be GSheet formulas:
- Agent writes the complex result to one cell
- Agent ALSO writes a simplified GSheet formula that approximates the same result
- If the two numbers differ significantly → flagged as "needs human review"

**SOLUTION 2: "Show Your Work" — Plain Language Audit Trail**

Agent documents every step in plain Indonesian/English:
```
📊 Laporan Penjualan Harian — 7 Feb 2026

Langkah 1: Tarik data dari Accurate Online
  → 1,234 transaksi ditemukan (1 Jan - 7 Feb 2026)

Langkah 2: Filter hanya bulan Februari
  → 456 transaksi

Langkah 3: Hitung total revenue
  → Rp 45.678.000 (jumlah kolom F, baris 2-457)

Langkah 4: Hitung rata-rata per transaksi
  → Rp 100.171 (total ÷ jumlah transaksi = 45.678.000 ÷ 456)

Langkah 5: Bandingkan dengan target
  → Target: Rp 50.000.000 → Pencapaian: 91.4% → ⚠️ Below Target
```

Non-technical staff can sanity-check:
- "Does 1,234 transactions sound right for that period?"
- "Is Rp 45 juta reasonable for February sales?"
- "The math: 45,678,000 ÷ 456 = 100,171? Let me check with calculator."

**SOLUTION 3: "Parallel Run" — Agent vs Human Side-by-Side**

For Phase 1 (first 2-4 weeks):
- Agent does the task AND human does the same task
- Compare results
- If they match consistently → agent is validated
- If they differ → investigate why, fix the agent

This is the GOLD STANDARD for validation. Costs extra human time upfront,
but builds trust. After validation period, human stops doing the task.

**SOLUTION 4: "Layer 2 Cross-Checks Layer 1"**

Layer 2 (using smarter Sonnet model) spot-checks Layer 1's work:
```
Overseer HEARTBEAT.md:
- Pick 1 random report from Layer 1 agents
- Pull the raw data myself
- Recalculate the key figures independently
- If my numbers match Layer 1's numbers → ✅
- If they don't match → alert Wayan with details of discrepancy
```

This is like having a supervisor audit a random sample of employee work.
Not every report, just enough to maintain trust.

**SOLUTION 5: "Template-Driven Processing" — The Safety Net**

Pre-build GSheet templates with formulas already set up by someone who
knows what they're doing (you + Wayan, with AI help to set them up ONCE).

Agent's job becomes simpler:
1. Pull raw data from API
2. Paste raw data into the designated input range of the template
3. Template formulas automatically calculate everything
4. Agent reads the output range and generates the report

The formulas are fixed and audited once. Agent just fills in the raw data.
If the formulas are right and the raw data is right → output is right.

### 8D. RECOMMENDED APPROACH: Combine Solutions 1 + 2 + 3 + 5

| Phase | Approach | Why |
|---|---|---|
| Phase 0 | Build GSheet templates with pre-set formulas (Solution 5) | One-time setup, auditable by anyone |
| Phase 1 | Agent fills templates + parallel run with human (Solution 3) | Build trust, catch errors |
| Phase 1+ | Agent shows work in plain language (Solution 2) | Ongoing transparency |
| Phase 2+ | Agent writes GSheet formulas for new/dynamic reports (Solution 1) | Scalable, self-documenting |
| Phase 3+ | Layer 2 spot-checks random reports (Solution 4) | Automated quality control |

### 8E. SECURITY WARNING: ClawHub Skills

⚠️ CRITICAL: Snyk security audit (Feb 2026) found 13.4% of ClawHub skills
contain security issues. 341 malicious skills found including credential theft.

**Rules for our system:**
- ONLY use the official `gog` skill (verified, by OpenClaw maintainer)
- READ every third-party skill's SKILL.md before installing
- Prefer writing our OWN skills in workspace/skills/ over installing from ClawHub
- Enable sandboxing for any skill that runs exec commands
- Never store API keys in SKILL.md files

---

## 9. CORE PATTERN: AGENT = DATA MOVER, NOT DATA CALCULATOR

**The fundamental design principle for Layer 1:**

```
Agent MOVES data:   API → GSheet (raw data tab)
GSheet CALCULATES:  Formulas in template do all math
Agent READS results: GSheet summary tab → formatted report
Agent REPORTS:      Telegram group + Notion status update
```

Why: Nobody in the office knows SQL/Python. But everyone understands GSheet formulas.
By keeping calculations IN GSheets, the entire team can verify, audit, and fix errors.

**Agent needs only 4 operations:**
1. `gog sheets clear` → wipe old data from raw tab
2. `gog sheets write` → paste new raw data
3. `gog sheets read` → read calculated results from summary tab
4. Format + send report to Telegram

**Template approach:** Build each GSheet template ONCE with pre-set formulas.
Agent's job is just to fill the raw data input. Formulas are audited once, work forever.

**For complex analysis beyond GSheet formulas:**
- Agent calculates in Python AND writes equivalent GSheet formula
- If both results match → confident
- If mismatch → flagged for human review
- Layer 2 randomly spot-checks reports

**Validation timeline:**
- Phase 1 (weeks 1-4): Agent + human run in parallel, compare results
- Phase 2+: Agent runs independently, Layer 2 spot-checks
- Ongoing: plain-language audit trail with every report

---

## 10. APPROVAL WORKFLOW: Do → Review → Approve

**The core operational loop (confirmed by user):**

```
Layer 1 does job → updates Notion (Done + attachment link)
  → Layer 2 checks Notion → clicks link → reviews output
    → If wrong: Layer 2 tells Layer 1 to revise (via TG group) → Layer 1 redoes
    → If right: Layer 2 approves in Notion
      → Layer 2 sends email to human PIC (e.g., Galuh)
        → Email: summary + GSheet link + "Reply Approve to confirm"
          → Human replies "Approve" → Layer 2 detects reply → marks task ✅✅ APPROVED in Notion
```

**Notion task status lifecycle:**
⏳ Scheduled → 🔄 In Progress → 📋 Done by Agent → ❌ Revision (if needed) →
✅ L2 Approved → 📧 Pending Human Approval → ✅✅ APPROVED (final)

**Email approval via `gog gmail send` + `gog gmail search`:**
- Layer 2 sends structured email in Indonesian to PIC
- Contains: task summary, key metrics, GSheet link, Notion link
- PIC replies "Approve" or sends revision notes
- Layer 2 heartbeat monitors inbox every 30 min for replies
- Full audit trail: Notion + email + Telegram group

**Why this works for non-technical team:**
- Email-based approval (everyone knows email)
- Human is ALWAYS the final gatekeeper
- No SQL/Python knowledge needed to approve
- Three-level verification: Agent does → AI reviews → Human approves

---

## 11. PHASE 1 PROOF OF CONCEPT: Stock & Inventory Check

**Chosen first task**: Daily stock & inventory check (FF%/FB% + stock levels + threshold alerts)
**Why first**: Done daily, high repetition, clear thresholds, template already exists, maps to existing CEO alert requirements
**Team**: OPS / Warehouse
**Template**: Exists — structured GSheet with tabs, formulas, standard format (details pending from user)
**Alert thresholds** (from Jarvis docs):
- FF (Full Floor) < 70% → alert Virra (OPS)
- FB (Full Box) < 80% → alert Virra (OPS)
- Stock Minus < 0 → alert Galuh + Nabila
- Sales MTD < 95% target → alert Branch Manager

**Generic agent flow (specific GSheet details to be filled in later):**
1. Agent pulls stock data from Accurate Online API (or iSeller API)
2. Agent clears raw data tab in template GSheet
3. Agent writes fresh stock data to raw data tab
4. GSheet formulas calculate: FF%, FB%, stock levels, alerts
5. Agent reads summary/alert tab
6. If any threshold breached → immediate alert to relevant person via Telegram
7. Agent posts daily summary to department Telegram group
8. Agent updates Notion task status: done/failed + details

**Status**: ✅ GSheet analyzed — see section 13 below for full structure.

---

## 11. ORACLE REVIEW: CRITICAL GAPS IDENTIFIED

### 🔴 CRITICAL (will cause production incidents)
1. **Silent failures**: Agents that crash send no notification. Fix: heartbeat records to Supabase, Layer 2 checks staleness.
2. **Partial data writes**: Half-done API pulls produce wrong GSheet totals. Fix: atomic writes (pull all → write all at once), sync cursors in Supabase.
3. **No escalation path**: Revision loops can be infinite. Fix: max 2 revisions, then 🔴 ESCALATED to human.
4. **GSheet write collisions**: Multiple agents writing same spreadsheet = data loss. Fix: each division gets own GSheet file entirely.
5. **Skills.md editing needs Git**: No rollback if Layer 2's SSH edit breaks things. Fix: Git repo for all workspaces, Layer 2 pushes to Git, Layer 1 pulls.

### 🟡 HIGH (will cause pain within weeks)
6. **Email approval bottleneck**: PIC on vacation = pipeline frozen. Fix: 48h timeout, escalate to backup PIC.
7. **Telegram message flooding**: 10+ agents posting = noise. Fix: categorize (🟢 routine → logs group, 🟡🔴 → main group).
8. **No test environment**: Skills.md changes run on production immediately. Fix: test_mode flag per agent.
9. **API key rotation**: Keys expire, need updating on all VPS. Fix: centralize credentials, never in skills.md.
10. **Google Sheets API quota**: 300 req/min per project. Fix: batch writes, stagger crons.

### 🟢 INSIGHTS
- VPS consolidation safe: 3 VPS instead of 5-7 (agents are I/O bound, not CPU bound). Saves $10-20/mo.
- Cron staggering: 3-4 hour gaps between runs to allow full revision cycle.
- Timezone: standardize ALL crons to UTC with WIB comments.
- Separate Notion integration tokens per layer (doubles rate limit).
- Each row written to GSheet should include `last_updated_by` (agent name) + `last_updated_at` (timestamp).
- UPS ($30-50) for Mac Minis to prevent power-loss crashes.
- Disable macOS auto-updates on Layer 2 machines.
- `sudo pmset -a disablesleep 1` on Mac Minis.

### ORACLE'S VERDICT
"The architecture is fundamentally sound. The agent-as-data-mover philosophy and
human-in-the-loop approval are correct choices. The main gaps are operational
resilience (what happens when things fail) and observability (how do you know
things failed). Fix those, and this system will run reliably."

---

## 12. REMAINING OPEN QUESTIONS

- [x] VPS provider preference → Hostinger KVM 2 ($6.99/mo)
- [x] Which agent/department should be Phase 1 PoC → Atlas (OPS), Control Stock
- [x] Google Workspace OAuth → harveywayan@gmail.com, gog CLI (✅ working)
- [x] Telegram group structure → pending @BotFather setup
- [x] Budget → ~$56/mo approved (VPS $7 + LLM ~$49)
- [ ] Exact Accurate API endpoints for stock/sales data
- [ ] Merchandiser's email address for daily insights
- [ ] The #VALUE! errors on Global tab — expected or bug?
- [ ] How are products assigned to tiers? Lookup table or manual?
- [ ] Which warehouses exist? (WHS = Shopfloor, WHB = Box — more?)
- [ ] Which of the 36 tabs are actively used vs obsolete?

---

## 14. SESSION 4–5 ARCHITECTURE EVOLUTION (8 Feb 2026)

### MAJOR DECISION: Self-Hosted PostgreSQL Data Architecture

**Previous**: Agent = Data Mover. Accurate API → GSheet (raw data tabs) → GSheet formulas calculate → Agent reads results → Email.

**Session 4 decision**: Move to Supabase-first (SQL as brain instead of GSheet formulas).

**Session 5 decision (lost sessions)**: Self-host PostgreSQL on dedicated KVM 2 VPS instead of Supabase. Full control, no external dependency, DBeaver for monitoring (NocoDB tried then removed).

**Current**: Agent = Data Mover + Report Builder. Accurate API → **Self-hosted PostgreSQL** (raw tables) → **SQL views auto-calculate** → Agent reads views → Mirrors flat summary to GSheet dashboard → Email (summary table + GSheet link).

### Why Self-Hosted Instead of Supabase

| Supabase | Self-Hosted PostgreSQL |
|----------|----------------------|
| Shared project with zuma-branch-superapp | Dedicated DB, no conflict |
| 8GB disk limit (Pro plan, 3.32GB already used) | 100GB NVMe, all for agents |
| Outstanding invoices / billing issues | $7/mo flat, no surprises |
| Limited control over extensions | pgvector installed, full admin |
| No NocoDB-like UI for non-SQL monitoring | DBeaver (local) via SSH tunnel for DB management |

### Database Configuration (LIVE)

| Property | Value |
|----------|-------|
| VPS | KVM 2 — `76.13.194.120` (`ssh postgresql`) |
| PostgreSQL | 16.11 + pgvector |
| Database | `openclaw_ops` |
| Schemas | `portal` (reference), `raw` (staging), `core` (normalized — TBD), `mart` (reporting — TBD) |
| REST API | PostgREST 14.3 on port 3000, proxied via nginx at `/api/` with API key auth |
| Monitoring | DBeaver (local via SSH tunnel) — NocoDB was removed 8 Feb 2026 |
| Backup | Daily pg_dump 03:00 WIB (7d), weekly pg_dumpall Sunday (4wk) |
| Security | UFW (port 5432 → Agent VPS only), fail2ban, 5 DB users with least-privilege |

### Portal Schema — Reference/Dimension Data (✅ Loaded)

| Table | Rows | Source | Purpose |
|-------|------|--------|---------|
| `portal.store` | 326 | CSV import | Store/branch master (names, branch, area, capacity, targets) |
| `portal.kodemix` | 5,464 | CSV import | Product SKU master (kode_mix, tier, gender, series, assortment, status) |
| `portal.hpprsp` | 935 | CSV import | Product pricing (harga_beli, price_taq, rsp, tier, season) |
| `portal.stock_capacity` | 57 | CSV import | Store stock capacity limits (max_display, max_stock, storage) |

### Raw Schema — Staging Tables (✅ Designed, ⬜ Empty)

| Table | Entity | Key Columns |
|-------|--------|-------------|
| `raw.accurate_stock_ddd` | DDD stock | id, kode_barang, nama_gudang, kuantitas, unit_price, vendor_price, snapshot_date |
| `raw.accurate_sales_ddd` | DDD sales | id, tanggal, kode_produk, kuantitas, harga_satuan, total_harga, bpp, nama_gudang, vendor_price, dpp_amount, tax_amount |
| `raw.accurate_stock_ljbb` | LJBB stock | Same as accurate_stock_ddd |
| `raw.accurate_stock_mbb` / `raw.accurate_sales_mbb` | MBB | Stock + sales (same patterns) |
| `raw.accurate_stock_ubb` / `raw.accurate_sales_ubb` | UBB | Stock + sales (same patterns) |
| `raw.iseller_sales` | iSeller POS | 30+ cols matching iSeller CSV format |
| `raw.load_history` | ETL audit trail | source, batch_id, rows_loaded, status, error_message |

### Core + Mart Schemas (⬜ NOT YET BUILT — needs SOP walkthrough)

| Schema | Planned Tables | Purpose |
|--------|---------------|---------|
| `core.*` | `dim_product`, `dim_store`, `dim_warehouse`, `fact_stock`, `fact_sales` | Normalized star schema with proper FKs |
| `mart.*` | `v_control_stock`, `v_tier_summary`, `v_depth_alert` | Denormalized reporting views for email + GSheet |

### Three Agent Data Skill Types

| Skill Type | Responsibility | Tools Used |
|-----------|---------------|------------|
| **Data Mover** | Pull from Accurate API → Insert to PostgreSQL raw tables | `curl` + `psql` or PostgREST API |
| **Data Processor** | SQL views auto-calculate (agent doesn't act) | PostgreSQL (automatic) |
| **Report Builder** | Read SQL views → mirror to GSheet + compose email | `gog sheets` + `gog gmail` |

### GSheet Role Change

| Before | After |
|--------|-------|
| Calculator (formulas do math) | **Dashboard** (display layer only) |
| Updated daily with raw data + formulas | Updated daily with **flat summary data** from PostgreSQL views |
| Critical path (if broken, no email) | **Not critical** (email works from PostgreSQL alone) |
| Wayan monitors weekly | GSheet link included in daily email |

### Email Format (Decided)

Each daily email contains:
1. **Inline summary table** — key metrics, TIER alerts, top 10 MUST-PO items
2. **Link to GSheet dashboard** — for full details / drill-down
3. Written in Bahasa Indonesia, addressed to PIC (not Wayan)

### Monitoring Architecture (Decided)

| Check Type | Tool | Frequency |
|-----------|------|-----------|
| Quick (5 sec) | Notion task status | Per-run (auto) |
| Medium (30 sec) | GSheet Monitor tab | Weekly (manual) |
| Deep (2 min) | DBeaver (browse data, run queries, visual table editor) | As needed |
| Emergency | Telegram alert | Auto on failure |

Agent runs validation SQL after every data load:
- Row count check (did we get data?)
- Null check (data quality)
- Freshness check (today's data?)
- Delta check (>20% drift from yesterday = suspicious)

---

## 10. USER CONTEXT

- **Person**: Wayan — non-IT person, needs clear explanations
- **Role**: Technology lead / digital transformation at Zuma
- **Company**: Zuma Indonesia — footwear brand (sandals, shoes: SLIDE, AIRMOVE, STRIPE, LUNA series)
- **Locations**: Multiple retail branches (Tabanan, Lippo Batu, Bali area, Jatim)
- **Departments**: Branch/OPS, CEMES (Marketing), FATAL (Finance), R&D, HRGA, BD & Wholesale, Online Sales
- **Current pain**: Human admins spend hours on repetitive data pulling/processing/reporting
- **Core struggle**: Most work is GSheet-based, nobody knows SQL/Python to verify agent calculations
- **Existing infra**: Supabase, Jarvis AI (Telegram + Web UI), Railway, Hostinger KVM 2 VPS
- **OpenClaw experience**: Uses OpenClaw on Hostinger for coding — experiences lag/crashes from browser tool
- **Mac Mini M4**: Planning to purchase (not yet bought)
- **Data access**: Currently browser/manual login — confirmed: switching to API-first
- **Budget**: Cost-conscious, prefers cheap VPS
- **Autonomy**: Full auto-fix for overseers
- **CEO vision** (from Jarvis docs): "Jarvis cuma perlu tahu: Siapa yang harus di-follow up hari ini, dan kenapa."

---

## 13. PHASE 1 POC: CONTROL STOCK GSHEET — FULL ANALYSIS

### GSheet Details
- **Name**: Control Stock
- **Spreadsheet ID**: `1qInTrRUOUi2983vefS8doS5Pt3jC2yftQAG99yYlVOE`
- **URL**: https://docs.google.com/spreadsheets/d/1qInTrRUOUi2983vefS8doS5Pt3jC2yftQAG99yYlVOE/edit
- **PIC**: Merchandiser (person responsible for reviewing the output)

### Tab Structure (13 tabs total)

| Tab | Role | Key Data |
|---|---|---|
| **PO** | Purchase Order tracking | ~1397 SKU rows. Cols: TIER, CODE, TYPE, GENDER, P/S, SUDAH PO, Done PO 1-6, TGL PO, STATUS PO, Keterangan, JML RCV 1-10, TOTAL RCV, SISA PO, STATUS, TGL RCV 1-10. Header shows % completion per tier (14.87% overall) |
| **Global** | Summary dashboard | WHS (Warehouse Shopfloor) vs WHB (Warehouse Box) by tier. Cols per warehouse: Box(@12), Protol, Total(pair), %. Shows totals + percentages. Has #VALUE! errors in lower section (broken references?) |
| **WH BOX** | Warehouse Box raw data | Raw data from Accurate |
| **DATA AWAL** | Initial/baseline stock data | Raw data from Accurate — the starting point |
| **Update Stock** | Stock update entries | Raw data from Accurate — daily updates |
| **Summary Kode MIX** | Summary across all tiers | Aggregated view |
| **forNotionIntegrator** | Already designed for Notion integration! | Pre-built for automation — investigate |
| **TIER 1 KODE MIX** | Tier 1 (highest priority) product breakdown | Calculated from raw data |
| **TIER 2 KODE MIX** | Tier 2 product breakdown | Calculated from raw data |
| **TIER 3 KODE MIX** | Tier 3 product breakdown | Calculated from raw data |
| **TIER 4** | Tier 4 product breakdown | Calculated from raw data |
| **TIER 5** | Tier 5 product breakdown | Calculated from raw data |
| **TIER 8** | Tier 8 (lowest priority) product breakdown | Calculated from raw data |

### TIER System
- **Tiers = Product Priority/Importance**
- Tier 1 = highest priority / best sellers
- Tier 5/8 = lowest priority
- Products are classified by tier, and each tier gets its own KODE MIX breakdown tab
- The Global tab aggregates across all tiers

### Data Flow
```
Accurate Online (ERP)
  → CSV export (manual today)
    → DATA AWAL, Update Stock, WH BOX tabs (raw data)
      → Formulas calculate across sheets
        → TIER 1/2/3/4/5/8 KODE MIX tabs (per-tier analysis)
          → Global tab (summary dashboard)
          → PO tab (purchase order tracking)
```

### PO Tab Columns (Row 6 = header):
| Col | Header | Description |
|---|---|---|
| A | TIER | Product tier (0-5, 8) |
| B | CODE | SKU code (e.g., SJ2AWG9, M1ON03) |
| C | TYPE | Full product name (e.g., "LADIES WEDGES 9 AQUA HAZE") |
| D | GENDER | LADIES, MEN, BABY, BOYS, GIRLS |
| E | P/S | Priority/Standard flag (P, S, or -) |
| F | SUDAH PO | Already ordered qty |
| G-L | Done PO 1-6 | PO batch quantities |
| M | TGL PO | PO date |
| N | STATUS PO | PO status |
| O | Keterangan | Notes |
| P-Y | JML RCV 1-10 | Received quantities (10 batches) |
| Z | TOTAL RCV | Total received |
| AA | SISA PO | Remaining PO (ordered - received) |
| AB | STATUS | Receiving status |
| AC-AL | TGL RCV 1-10 | Receiving dates |
| AM-AO | Column 1-3 | Extra columns |

### Global Tab Structure:
- Row 2-3: Headers — T (Tier), WHS (Box@12, Protol, Total pair, %), WHB (Box@12, Protol, Total pair, %), WH? (more warehouses?)
- Row 4-9: Data per tier (1, 2, 3, 4, 5, 8)
- Row 10: Totals — e.g., WHS Total: 10,858 Box@12, 20,815 Protol, 97,677 Total pair
- Row 11: 21.31% (overall percentage)
- Row 12: 1,954 (some metric)
- Row 13-21: Second section (same structure but with #VALUE! errors)

### WHAT THE AGENT MUST DO (confirmed by user):

**TWO-PHASE APPROACH: One-time setup + daily refresh + insight**

#### ONE-TIME SETUP (done once):
- Agent creates the full Control Stock GSheet from scratch
- All 13 tabs with correct structure, formulas, TIER breakdowns
- Replicates the existing template (or uses the existing file as the template)
- After this, the GSheet template is FIXED — formulas don't change

#### DAILY CRON JOB:
1. **Pull from Accurate API**: Stock data + Sales velocity data (both from same ERP)
2. **Update raw data tabs only**: Clear + refill DATA AWAL, Update Stock, WH BOX
3. **Formulas auto-recalculate**: TIER KODE MIX tabs + Global + PO — no agent action needed
4. **Agent reads calculated results**: Read TIER tabs, Global summary, PO status
5. **Analyze inventory depth**:
   - Calculate: months of availability = current stock ÷ avg monthly sales rate
   - Flag items with < 3 months stock → 🔴 MUST PO
   - Identify: articles to ORDER MORE (fast sellers + low stock)
   - Identify: articles to ORDER LESS (slow sellers + high stock)
6. **Send deep insight EMAIL to Merchandiser PIC**:
   - NOT just raw data — actionable insights and recommendations
   - "Article M1CA01 MEN CLASSIC 1: 1.2 months left, selling 500/month → PO 1500 NOW"
   - "Article SJ2ASD1 LADIES SOLID 1: 14 months stock, selling 20/month → STOP ordering"
   - Tier-by-tier breakdown of which items need attention
   - Top 10 MUST-PO items sorted by urgency
   - Top 10 OVER-STOCKED items sorted by excess

### Pattern: Agent = Data Mover + Analyst
- **Data Mover part**: Pull from Accurate API → clear raw tabs → write fresh data (same as original plan)
- **Analyst part**: Read calculated results → compute months-of-availability → generate recommendations → email insight
- **GSheet = Calculator**: Formulas handle all TIER breakdowns, Global summary, PO tracking (same as original plan)
- **Email = Primary output**: Deep insight email to Merchandiser (NOT just Telegram alert)
- **Telegram = Secondary**: Quick summary/notification to department group

### Key Differences from Original Plan:
| Original Plan | Updated Scope |
|---|---|
| Agent fills a generic template | Agent uses EXISTING Control Stock GSheet (specific, 13 tabs) |
| GSheet formulas do ALL math | GSheet formulas do tier/global math. Agent does inventory depth analysis ON TOP. |
| Report to Telegram group | Primary: deep insight EMAIL to Merchandiser. Secondary: Telegram summary |
| Simple threshold alerts (FF%, FB%) | Sophisticated: months-of-availability, order-more/order-less recommendations |
| Generic stock check | Specific: Control Stock with TIER system, KODE MIX, PO tracking |
| One-shot daily task | One-time GSheet setup + daily data refresh + analysis + email |

### Decisions Made:
- ✅ Sales averaging period: **Last 3 months** (responsive to seasonal fashion trends)
- ✅ File approach: **Agent creates brand new GSheet from scratch** (original file is reference only)
- ✅ forNotionIntegrator tab: **Prepared but not connected yet** — agent can use this structure
- ✅ Current data input: **CSV export from Accurate → manual paste** (agent replaces this with API)
- ✅ Daily job: **Update raw data tabs only** + read results + analyze + email (NOT recreate whole file daily)

### Remaining Open Questions:
- [ ] What Accurate API endpoints return stock data? (which report/query?)
- [ ] What Accurate API endpoints return sales velocity data?
- [ ] Does the Merchandiser want the email in Indonesian or English?
- [ ] What's the Merchandiser's email address?
- [ ] The #VALUE! errors on Global tab — are these expected or a bug?
- [ ] How are products assigned to tiers? Lookup table or manual?
- [ ] Which warehouses exist? (WHS = Shopfloor, WHB = Box — are there more?)

---

## 15. SCHEMA DATA STRATEGY & ROADMAP (8 Feb 2026 — Wayan's Master Plan)

> **PURPOSE OF THIS VPS PostgreSQL**: This is the **first PoC** of OpenClaw VPS #1 (Iris, Atlas, & Apollo).
> The goal is to give these OpenClaw agents a **clear & reliable data source from the start**.
> Without clean, structured, accessible data in PostgreSQL — the agents can't do their jobs.

### Schema-by-Schema Strategy

#### `portal.*` — Reference/Master Data
| Aspect | Current State | Future State |
|--------|--------------|--------------|
| **Now** | Manual CSV upload by Wayan via DBeaver | Automated pull from GSheet sources |
| **Why manual for now** | Portal data rarely changes (store list, product master, pricing) | — |
| **Future automation** | Python script on VPS, OR Google Apps Script, OR similar | Script checks GSheet source → compares with PostgreSQL → appends new rows OR truncate & re-upload entire table |
| **Update pattern** | Per-table, one by one (not all at once) | Same — each portal table has its own GSheet source, updated independently |
| **Priority** | LOW urgency (data is stable), but must be automated eventually | Before Phase 2 expansion |
| **Decision needed** | Which method: Python on VPS vs Apps Script vs other | TBD |

#### `raw.*` — Staging/Transactional Data (THE TOUGH ONE)
| Aspect | Current State | Future State |
|--------|--------------|--------------|
| **Now** | Tables designed, 0 rows, no API connected | Reliable automated daily pulls from Accurate Online API |
| **Why this is critical** | Raw data = the foundation. If raw data is wrong/missing, everything downstream fails | — |
| **Must get right from day 1** | API connection, authentication, entity mapping, error handling, data validation | — |
| **API Credentials** | ✅ ALL 4 entities have working API tokens (in local `.env.ddd`, `.env.mbb`, `.env.ubb`, `.env.ljbb`) | Tokens say "never expires" — already production-tested against Supabase |
| **Automation** | Atlas (OPS agent) runs daily cron → calls Accurate API → inserts into raw.* tables | Snapshot-based: each pull = new `snapshot_date`, append-only |
| **Validation** | Row count check, null check, freshness check, delta check (>20% drift = suspicious) | Agent logs validation results in `raw.load_history` |
| **Reference code** | `D:\...\accurate-online-tool\0. real-data_accurate\` — working Python scripts | `daily_sync_api.py` (sales), `pull_inventory_stock.py` (stock) |
| **Priority** | **HIGHEST** — this is the critical path for the entire PoC | Must work before anything else |

#### Accurate API Pull Strategy (Wayan's Decision — 8 Feb 2026)

> **IMPORTANT**: This is the definitive pull strategy. Do not deviate without discussing with Wayan.
> Table column design is NOT decided yet — this section covers ONLY the pull method & entity mapping.

##### Entity Data Availability

| Entity | Stock Data | Sales Data | Finance Data | Notes |
|--------|-----------|------------|-------------|-------|
| **DDD** | ✅ Yes | ✅ Yes | — | Main retail brand (Dream Dare Discover) |
| **LJBB** | ✅ Yes | ❌ **NO SALES** | ✅ Yes | LJBB only has stock + finance. **No `raw.ljbb_sales` table should exist.** |
| **MBB** | ✅ Yes (planned) | ✅ Yes | — | Stock pull planned, not active yet |
| **UBB** | ✅ Yes (planned) | ✅ Yes | — | Stock pull planned, not active yet |

##### Stock Pull Strategy

| Aspect | Detail |
|--------|--------|
| **Method** | Official REST API (`item/detail.do` → `detailWarehouseData[]`) |
| **Auth** | HMAC-SHA256 with permanent API token (no cookies needed) |
| **Current state** | Already runs daily on Railway for **DDD & LJBB** → Supabase |
| **Expansion** | Will add **MBB & UBB** stock pulls (same method) |
| **Script** | `pull_inventory_stock.py` — production tested |
| **Pattern** | Truncate & reload (current snapshot, not historical) |
| **Speed** | Reasonable — one `detail.do` call per item, 8 req/sec rate limit |

##### Sales Pull Strategy (TWO-PHASE)

| Phase | Method | Speed | Auth | Use Case |
|-------|--------|-------|------|----------|
| **Phase 1: Historical bulk load** | Report Export API ("workaround") | ⚡ FAST — entire years in minutes | DSI/USI session cookies (from browser inspect → Network tab) | One-time download of 2022 → 7 Feb 2026 |
| **Phase 2: Daily incremental** | Official REST API (`sales-invoice/detail.do`) | 🐢 SLOW — but automated | HMAC-SHA256 with permanent API token | Daily pull of yesterday's data (e.g., on 9 Feb pull 8 Feb data) |

**Why two phases?**
- The Report Export (workaround) is incredibly fast — can download 2022-2026 in minutes
- BUT it requires browser session cookies that expire → can't automate via cron
- The Official API is slow (one API call per invoice) → impractical for years of history
- BUT it uses permanent tokens → perfect for daily automated pulls of small date ranges

**Historical load already done:**
- 2022 → 7 Feb 2026 downloaded via workaround for **DDD, MBB, UBB**
- LJBB has no sales data

**Daily automated pull (the target):**
- Every day, pull **yesterday's** sales data using Official API
- Entities: **DDD, MBB, UBB** only (not LJBB)
- Script: `daily_sync_api.py` — pulls last N days, upserts into database
- Speed is acceptable for 1 day of data (~few minutes per entity)

##### Existing VPS Raw Tables (CORRECT as-is)

| Table | Entity | Data Type | Exists? | Correct? |
|-------|--------|-----------|---------|----------|
| `raw.accurate_stock_ddd` | DDD | Stock | ✅ | ✅ |
| `raw.accurate_sales_ddd` | DDD | Sales | ✅ | ✅ |
| `raw.accurate_stock_ljbb` | LJBB | Stock | ✅ | ✅ |
| `raw.accurate_stock_mbb` | MBB | Stock | ✅ | ✅ |
| `raw.accurate_sales_mbb` | MBB | Sales | ✅ | ✅ |
| `raw.accurate_stock_ubb` | UBB | Stock | ✅ | ✅ |
| `raw.accurate_sales_ubb` | UBB | Sales | ✅ | ✅ |
| `raw.iseller_sales` | iSeller | Sales | ✅ | ✅ |
| `raw.load_history` | All | Audit | ✅ | ✅ |
| ~~`raw.accurate_sales_ljbb`~~ | LJBB | Sales | ❌ | ✅ **Correct — should NOT exist. LJBB has no sales data.** |
| ~~`raw.whs_stock`~~ | WHS | Stock | ❌ | ✅ **DROPPED — no WHS entity in API.** |
| ~~`raw.whs_sales`~~ | WHS | Sales | ❌ | ✅ **DROPPED — no WHS entity in API.** |

##### What's Been Decided (Session 9 — 8 Feb 2026)
- **Table naming convention** — `{source}_{type}_{entity}` (e.g., `raw.accurate_sales_mbb`) ✅ APPLIED
- **Table column format** — ✅ DECIDED & APPLIED. Sales: 19 cols (original 14 + id + nama_gudang + vendor_price + dpp_amount + tax_amount). Stock: 10 cols (original 7 + id + unit_price + vendor_price). See `04-database-schema-reference.md`.
- **Snapshot vs append strategy** — Stock: `DELETE WHERE snapshot_date = today` then `INSERT` (daily replacement). Sales: `INSERT ON CONFLICT DO UPDATE` (upsert on unique constraint).
- **Unique constraints** — Sales: `(nomor_invoice, kode_produk, tanggal, snapshot_date)` ✅ APPLIED

##### Still NOT Decided
- **Where to run scripts** — Agent VPS? DB VPS? Wayan's local machine?
- **Cron schedule** — what time daily? staggered across entities?

#### `raw.iseller_sales` — iSeller POS Data
| Aspect | Current State | Future State |
|--------|--------------|--------------|
| **Now** | Table designed, 0 rows | Manual CSV upload by Wayan via DBeaver |
| **Why manual** | iSeller requires browser login to download CSV — no API yet | — |
| **Future automation** | When Mac Mini M4 arrives → install OpenClaw Layer 2 agent | Layer 2 agent on Mac Mini has browser access → downloads iSeller CSV daily → uploads to PostgreSQL via DBeaver or psql |
| **Timeline** | Manual until Mac Mini M4 purchased & configured | Part of Layer 2 setup (Phase 3) |
| **Priority** | MEDIUM — works fine as manual process for now | Automate when Mac Mini arrives |

#### `core.*` — Normalized Star Schema
| Aspect | Plan |
|--------|------|
| **Status** | ⬜ NOT BUILT — will figure out later |
| **Purpose** | Normalized dim/fact tables (dim_product, dim_store, dim_warehouse, fact_stock, fact_sales) with proper foreign keys |
| **When** | After portal & raw pipelines are solid and validated |
| **Depends on** | Portal tables verified correct, raw tables receiving daily data reliably |
| **Priority** | LOW for now — portal + raw first |

#### `mart.*` — Reporting Views
| Aspect | Plan |
|--------|------|
| **Status** | ⬜ NOT BUILT — will figure out later |
| **Purpose** | Denormalized views for email reports & GSheet dashboard (v_control_stock, v_tier_summary, v_depth_alert) |
| **When** | After core.* is designed and populated |
| **Depends on** | core.* tables exist and are correct |
| **Priority** | LOW for now — portal + raw + core first |

### Priority Order (Crystal Clear)

```
1. 🔴 raw.*  — Connect Accurate API, get daily data flowing RELIABLY (CRITICAL PATH)
2. 🟡 portal.* — Verify columns match CSV/GSheet, then automate the pull
3. 🟡 raw.iseller_sales — Manual CSV upload by Wayan (works for now)
4. ⚪ core.* — Design normalized schema (LATER, after raw is solid)
5. ⚪ mart.* — Design reporting views (LATER, after core is solid)
```

### Key Principle
> **"Give the agents clean & reliable data from the start."**
> If the data in PostgreSQL is wrong, incomplete, or stale — every agent output (emails, reports, alerts) will be garbage.
> That's why raw.* (Accurate API) is priority #1 — it's the hardest and most important.
