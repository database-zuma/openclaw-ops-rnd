# Hierarchical OpenClaw Agent System — Zuma Indonesia

## TL;DR

> **Quick Summary**: Deploy a 3-layer OpenClaw AI agent hierarchy for Zuma Indonesia that automates repetitive admin data work across departments. Layer 1 (VPS workers) pulls data from APIs, fills GSheet templates, and generates reports on cron schedules. Layer 2 (Mac Mini overseers) reviews output, requests revisions, and routes email approvals to human PICs. Layer 3 (Jarvis/C-level) is excluded from this plan.
> 
> **Deliverables**:
> - 3 VPS with Layer 1 worker agents configured (multi-agent per Gateway)
> - Phase 1 proof-of-concept: Stock & Inventory Check agent (daily FF%/FB% + alerts)
> - GSheet template system (agent = data mover, GSheet = calculator)
> - Telegram group structure + Notion task tracking workspace
> - Reference-based skills architecture (SKILL.md + SOP docs)
> - 2 Mac Mini M4 Layer 2 overseers with HEARTBEAT.md, SSH self-healing, email approval workflow
> - Git-based workspace versioning for all agent workspaces
> - Security hardening (sandboxing, tool restrictions, SSH keys, credential isolation)
>
> **Estimated Effort**: XL (multi-phase rollout over 6-8 weeks)
> **Parallel Execution**: YES — 3 waves within each phase
> **Critical Path**: Phase 0 Foundation → Phase 1 PoC → Phase 2 Expand → Phase 3 Overseers

---

## Context

### Original Request
Wayan wants to automate repetitive admin data work across Zuma Indonesia's departments using a hierarchical OpenClaw agent system. Layer 1 division-level workers handle cron-based data processing. Layer 2 department-level overseers review and approve. The company's admin staff spend hours daily on manual data pulling, GSheet processing, and report generation.

### Interview Summary
**Key Discussions**:
- **Agent = Data Mover**: Agents pull from APIs and paste raw data into pre-built GSheet templates. GSheet formulas do all calculations. This solves the "nobody knows SQL/Python" verification problem — everyone can click a cell and see the formula.
- **Reference-based skills**: Tiny SKILL.md (~24 tokens) + full SOP docs loaded on-demand. Keeps context window lean.
- **Approval workflow**: Layer 1 does → Notion update → Layer 2 reviews → revision or approve → email to human PIC → PIC replies "Approve" → final status in Notion.
- **Self-healing**: Layer 2 SSHs into Layer 1 VPS for health checks, restarts, skills.md fixes. Git-based for rollback.
- **Phase 1 PoC**: Stock & Inventory Check (daily FF%/FB% + stock alerts). Template exists but structure details pending from team.
- **Layer 3 (Jarvis)**: Explicitly deferred to separate planning session.

**Research Findings**:
- OpenClaw multi-agent: 1 Gateway = 1 process = multiple agents with isolated workspaces. Agents are I/O-bound (~5% CPU, 95% waiting), so 2-3 agents per VPS is safe.
- `gog` CLI: Google Workspace CLI supporting Gmail, Sheets, Drive, Docs. OAuth-based. JSON output for scripting.
- ClawHub security: Snyk audit found 13.4% of skills contain security issues. Only use verified skills or write custom.
- Accurate Online API: REST API with HMAC-SHA256 auth. Reference implementation exists in Jarvis codebase.
- Existing Supabase tables: `jarvis.sales_3mo`, `jarvis.stock_current` — can bootstrap Phase 1 data.

### Oracle Review (10 Gaps — All Addressed)
1. **Silent failures** → heartbeat records to Supabase, Layer 2 checks staleness
2. **Partial data writes** → atomic writes (pull all → write all at once), sync cursors
3. **Infinite revision loops** → max 2 attempts, then escalate to human
4. **GSheet write collisions** → each division gets own GSheet file entirely
5. **Skills.md needs Git** → Git repo for all workspaces, push/pull workflow
6. **Email approval bottleneck** → 48h timeout, escalate to backup PIC
7. **Telegram flooding** → categorize messages (routine → logs group, alerts → main group)
8. **No test environment** → test_mode flag per agent, dry-run capability
9. **API key rotation** → centralized .env, never in skills.md
10. **GSheet API quota** → batch writes, stagger crons by 15+ min

---

## Work Objectives

### Core Objective
Deploy a production-ready hierarchical OpenClaw system where Layer 1 agents autonomously execute daily admin data tasks (pull → fill template → report → notify) and Layer 2 overseers review, revise, and route human approvals — replacing manual admin work across Zuma Indonesia's departments.

### Concrete Deliverables
- 3 configured VPS with OpenClaw Gateways running Layer 1 worker agents
- 1 fully functional Stock & Inventory Check agent (Phase 1 PoC)
- GSheet template for stock/inventory with pre-set formulas
- Telegram bot accounts + department group structure
- Notion workspace with task tracking database
- Reference-based skills architecture with SOP documents
- 2 Mac Mini M4 configured as Layer 2 overseers
- SSH key infrastructure (Mac Mini → VPS)
- Git repositories for agent workspace versioning
- Security hardening (sandboxing, tool restrictions, credential isolation)

### Definition of Done
- [ ] Phase 1 agent runs daily cron job, pulls stock data, fills GSheet template, reports to Telegram, updates Notion — for 5 consecutive days without manual intervention
- [ ] Layer 2 overseer detects intentionally-broken Layer 1 output, requests revision, receives corrected output within same cron window
- [ ] Human PIC receives approval email, replies "Approve", Notion status updates to APPROVED
- [ ] All agent workspaces are Git-versioned with working push/pull
- [ ] Layer 2 can SSH into Layer 1, check health, restart Gateway, and edit skills.md

### Must Have
- API-first data access (no browser automation — causes VPS crashes)
- Agent = Data Mover pattern (GSheet formulas do all calculations)
- Isolated cron sessions (fresh context per run)
- Max 2 revision attempts before human escalation
- Separate GSheet files per division (no write collisions)
- SSH key auth only (no passwords)
- API keys in .env files only (never in SKILL.md, AGENTS.md, or prompts)
- Timezone standardized: all crons in `Asia/Jakarta` (WIB)
- `last_updated_by` + `last_updated_at` metadata on every GSheet row write

### Must NOT Have (Guardrails)
- ❌ NO browser automation on any agent (tool denied in config)
- ❌ NO third-party ClawHub skills without full source code review
- ❌ NO API keys in SKILL.md, AGENTS.md, or any file that enters LLM prompt
- ❌ NO multiple agents writing to the same GSheet file
- ❌ NO infinite revision loops (max 2 then escalate)
- ❌ NO Layer 3 / Jarvis implementation (future scope)
- ❌ NO hard-coded cron times without timezone specification
- ❌ NO skills.md edits without Git commit + push (must be rollback-able)
- ❌ NO root SSH access from Layer 2 to Layer 1 (restricted user only)
- ❌ NO macOS auto-updates on Mac Mini Layer 2 machines
- ❌ NO over-engineering: start simple, prove Phase 1 works, then expand

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> This is NOT conditional — it applies to EVERY task, regardless of test strategy.
>
> **FORBIDDEN** — acceptance criteria that require:
> - "User manually tests..." / "User visually confirms..."
> - "User interacts with..." / "Ask user to verify..."
> - ANY step where a human must perform an action
>
> **ALL verification is executed by the agent** using tools (Bash, interactive_bash, curl, etc.).
>
> **Exception — Tasks 16 and 34**: These tasks require human participation as *test subjects* (not as verifiers). In Task 16, a human admin performs their normal manual stock check so the agent can compare results. In Task 34, a human PIC replies to an approval email. The *comparison, logging, and verification* is still done by the agent — the human is an input to the test, not the tester.

### Test Decision
- **Infrastructure exists**: NO (this is a greenfield infrastructure project)
- **Automated tests**: NO (infrastructure/config project — not a code project)
- **Agent-Executed QA**: YES — MANDATORY for all tasks. Each task verified by the executing agent using CLI commands, API calls, and log inspection.

### Agent-Executed QA Approach

| Deliverable Type | Verification Method |
|---|---|
| VPS setup / OpenClaw install | SSH + `openclaw health --json` + `openclaw cron list` |
| GSheet template | `gog sheets read` to verify formulas + cell values |
| Telegram bot | Send test message, verify delivery in group |
| Notion workspace | Notion API call to verify database schema + test entry |
| Cron job execution | `openclaw cron list` + wait for execution + check Telegram + check Notion |
| SSH connectivity | `ssh -o ConnectTimeout=5 admin@vps-ip "echo OK"` |
| Git workspace | `git log --oneline -5` + `git status` on agent workspace |
| Skills architecture | `openclaw` invoke skill + verify SOP doc loaded |
| HEARTBEAT.md | Wait for heartbeat cycle + verify HEARTBEAT_OK or alert |

---

## Execution Strategy

### Parallel Execution Waves

```
═══ PHASE 0: FOUNDATION (Week 0-1) ═══════════════════════════
Wave 0A (Start Immediately — no dependencies):
├── Task 1: Purchase & provision first VPS
├── Task 2: Set up Google Workspace OAuth credentials
├── Task 3: Create Telegram bots via @BotFather
└── Task 4: Design Notion workspace structure

Wave 0B (After Wave 0A):
├── Task 5: Design GSheet template for Stock & Inventory Check
├── Task 6: Document SOP: how stock check is done manually today
└── Task 7: Set up Git repo for agent workspaces

═══ PHASE 1: PROOF OF CONCEPT (Week 1-3) ═════════════════════
Wave 1A (After Phase 0):
├── Task 8: Install OpenClaw on VPS-1
├── Task 9: Install gog CLI + configure Google OAuth on VPS-1
└── Task 10: Create Notion task tracking database

Wave 1B (After Wave 1A):
├── Task 11: Build Stock Agent — AGENTS.md + skills + SOP docs
├── Task 12: Create stock GSheet template with formulas
└── Task 13: Configure Telegram group (OPS department)

Wave 1C (After Wave 1B):
├── Task 14: Configure cron job for daily stock check
├── Task 15: End-to-end test: cron → API → GSheet → Telegram → Notion
└── Task 16: 5-day parallel run (agent + human side-by-side)

═══ PHASE 2: EXPAND LAYER 1 (Week 3-5) ═══════════════════════
Wave 2A (After Phase 1 validated):
├── Task 17: Provision VPS-2 and VPS-3
├── Task 18: Install OpenClaw + gog on VPS-2 and VPS-3
└── Task 19: Create department Telegram groups + logs groups

Wave 2B (After Wave 2A):
├── Task 20: Build CEMES (Marketing) agents — online sales + marketplace data
├── Task 21: Build FATAL (Finance) agents — accounting + tax reports
└── Task 22: Build additional OPS agents (logistics, branch ops)

Wave 2C (After Wave 2B):
├── Task 23: Configure all cron jobs with staggered timing
├── Task 24: Security hardening: sandboxing + tool restrictions
├── Task 25: Git-version all agent workspaces
└── Task 26: Implement Telegram message categorization (routine vs alerts)

═══ PHASE 3: LAYER 2 OVERSEERS (Week 5-8, after Mac Mini purchase) ═
Wave 3A (After Mac Minis purchased):
├── Task 27: Set up Mac Mini M4 #1 (Overseer-OPS)
├── Task 28: Set up Mac Mini M4 #2 (Overseer-CEMES/FATAL)
└── Task 29: SSH key infrastructure (Mac Minis → all VPS)

Wave 3B (After Wave 3A):
├── Task 30: Build Overseer-OPS — HEARTBEAT.md + review workflow
├── Task 31: Build Overseer-CEMES/FATAL — HEARTBEAT.md + review workflow
└── Task 32: Configure email approval workflow via gog gmail

Wave 3C (After Wave 3B):
├── Task 33: Test revision loop: intentionally break Layer 1 → Layer 2 detects → revises
├── Task 34: Test email approval: Layer 2 sends → PIC replies → Notion updates
├── Task 35: Test self-healing: kill Layer 1 Gateway → Layer 2 detects → SSH restart
└── Task 36: Production burn-in: 1 week of full autonomous operation
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|---|---|---|---|
| 1 | None | 8 | 2, 3, 4 |
| 2 | None | 9, 12 | 1, 3, 4 |
| 3 | None | 13 | 1, 2, 4 |
| 4 | None | 10 | 1, 2, 3 |
| 5 | None | 12 | 1, 6, 7 |
| 6 | None | 11 | 5, 7 |
| 7 | None | 25 | 5, 6 |
| 8 | 1 | 11, 14 | 9, 10 |
| 9 | 2, 8 | 11 | 10 |
| 10 | 4 | 15 | 8, 9 |
| 11 | 6, 8, 9 | 14 | 12, 13 |
| 12 | 2, 5 | 14 | 11, 13 |
| 13 | 3 | 14 | 11, 12 |
| 14 | 11, 12, 13 | 15 | None |
| 15 | 14, 10 | 16 | None |
| 16 | 15 | 17 | None |
| 17 | 16 | 18 | 19 |
| 18 | 17 | 20, 21, 22 | 19 |
| 19 | 3, 16 | 26 | 17, 18 |
| 20 | 18 | 23 | 21, 22 |
| 21 | 18 | 23 | 20, 22 |
| 22 | 16 (VPS-1 already has OpenClaw) | 23 | 20, 21 |
| 23 | 20, 21, 22 | 26 | 24, 25 |
| 24 | 18 | 36 | 23, 25 |
| 25 | 7, 18 | 36 | 23, 24 |
| 26 | 19, 23 | 36 | 24, 25 |
| 27 | Mac Mini purchased | 29, 30 | 28 |
| 28 | Mac Mini purchased | 29, 31 | 27 |
| 29 | 27, 28 | 30, 31, 35 | None |
| 30 | 29 | 33, 34 | 31 |
| 31 | 29 | 33, 34 | 30 |
| 32 | 2, 30 or 31 | 34 | 30, 31 |
| 33 | 30, 31 | 36 | 34 |
| 34 | 32, 30 or 31 | 36 | 33 |
| 35 | 29, 30 or 31 | 36 | 33, 34 |
| 36 | 33, 34, 35 | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|---|---|---|
| 0A | 1, 2, 3, 4 | delegate_task(category="quick", load_skills=[], run_in_background=false) — simple setup tasks |
| 0B | 5, 6, 7 | delegate_task(category="unspecified-low", load_skills=[], run_in_background=false) — document + design tasks |
| 1A | 8, 9, 10 | delegate_task(category="unspecified-high", load_skills=[], run_in_background=false) — server config |
| 1B | 11, 12, 13 | delegate_task(category="deep", load_skills=[], run_in_background=false) — core agent design |
| 1C | 14, 15, 16 | delegate_task(category="deep", load_skills=[], run_in_background=false) — integration + validation |
| 2A-C | 17-26 | delegate_task(category="unspecified-high", load_skills=[], run_in_background=false) — expansion |
| 3A-C | 27-36 | delegate_task(category="deep", load_skills=[], run_in_background=false) — overseer setup |

---

## TODOs

---

### ═══ PHASE 0: FOUNDATION (Week 0-1) ═══

---

- [ ] 1. Purchase & Provision First VPS

  **What to do**:
  - Purchase a cheap VPS from Contabo (or Hetzner/Hostinger — user's choice)
  - Spec: 4 vCPU, 8GB RAM, 100GB SSD, Ubuntu 22.04 LTS
  - Set up basic server: update packages, create non-root user `openclaw-admin`, configure UFW firewall
  - Install Node.js 20 LTS (required for OpenClaw)
  - Install Python 3.11+ (needed for `gog` and potential data processing)
  - Configure SSH key authentication, disable password login
  - Set timezone to `Asia/Jakarta`
  - Record VPS IP, SSH port, credentials in secure location

  **Must NOT do**:
  - Do NOT use root account for OpenClaw operations
  - Do NOT enable password-based SSH login
  - Do NOT install unnecessary services

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
    - No special skills needed — standard server provisioning
  - **Skills Evaluated but Omitted**:
    - `playwright`: No browser needed for server setup
    - `git-master`: No git operations in this task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0A (with Tasks 2, 3, 4)
  - **Blocks**: Task 8 (OpenClaw install needs VPS)
  - **Blocked By**: None (can start immediately)

  **References**:
  - **External References**:
    - Contabo VPS pricing: https://contabo.com/en/vps/ — cheapest option ~$5-7/mo for 8GB
    - OpenClaw system requirements: Node.js 20+, npm/yarn
  - **Pattern References**:
    - Oracle recommendation (draft section 11): 3 VPS instead of 5-7, agents are I/O bound
  
  **WHY Each Reference Matters**:
  - Contabo pricing: confirms budget estimate of $25-35/mo for 3 VPS
  - Oracle consolidation advice: fewer VPS = less ops burden, agents barely use CPU

  **Acceptance Criteria**:

  ```
  Scenario: VPS is accessible and configured
    Tool: Bash (ssh)
    Preconditions: VPS purchased, IP known
    Steps:
      1. ssh -o ConnectTimeout=10 openclaw-admin@<VPS_IP> "echo CONNECTION_OK"
      2. Assert: output contains "CONNECTION_OK"
      3. ssh openclaw-admin@<VPS_IP> "node --version"
      4. Assert: output contains "v20" or higher
      5. ssh openclaw-admin@<VPS_IP> "python3 --version"
      6. Assert: output contains "3.11" or higher
      7. ssh openclaw-admin@<VPS_IP> "timedatectl | grep 'Time zone'"
      8. Assert: output contains "Asia/Jakarta"
      9. ssh openclaw-admin@<VPS_IP> "sudo ufw status | grep -c ALLOW"
      10. Assert: output is >= 1 (SSH allowed)
    Expected Result: VPS accessible, Node.js 20+, Python 3.11+, WIB timezone, firewall active
    Evidence: Terminal output captured

  Scenario: Password login disabled
    Tool: Bash (ssh)
    Steps:
      1. ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no openclaw-admin@<VPS_IP> "echo FAIL" 2>&1
      2. Assert: connection refused or "Permission denied"
    Expected Result: Password auth is disabled
    Evidence: Error output captured
  ```

  **Commit**: NO (infrastructure task, no code files)

---

- [ ] 2. Set Up Google Workspace OAuth Credentials

  **What to do**:
  - Log into Google Cloud Console with Zuma's Google Workspace admin account
  - Create a new GCP project: "Zuma-OpenClaw-Agents"
  - Enable APIs: Google Sheets API, Google Drive API, Gmail API, Google Docs API
  - Create OAuth 2.0 Client ID (Desktop application type)
  - Download `client_secret.json`
  - Store securely — this will be deployed to each VPS
  - Create a service account as backup auth method for Sheets-only access
  - Document: which Google account owns this project, how to rotate credentials

  **Must NOT do**:
  - Do NOT share client_secret.json in any Git repo or chat message
  - Do NOT put OAuth tokens in SKILL.md or AGENTS.md

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: Could use browser to set up GCP console, but user should do this manually for security

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0A (with Tasks 1, 3, 4)
  - **Blocks**: Tasks 9, 12 (gog CLI needs OAuth credentials)
  - **Blocked By**: None

  **References**:
  - **External References**:
    - `gog` CLI auth docs: https://gogcli.sh — `gog auth add you@gmail.com --services gmail,sheets,drive,docs`
    - Google Cloud Console: https://console.cloud.google.com/
  - **Documentation References**:
    - Draft section 8A: Layer 1 MUST have Google Workspace access — Sheets, Docs, Drive, Gmail
  
  **WHY Each Reference Matters**:
  - `gog` auth requires OAuth credentials from a GCP project — this task creates those credentials
  - The same credentials are reused on every VPS, so set up once correctly

  **Acceptance Criteria**:

  ```
  Scenario: OAuth credentials file exists and is valid JSON
    Tool: Bash
    Preconditions: GCP project created, OAuth client configured
    Steps:
      1. Verify client_secret.json exists in secure storage location
      2. Parse JSON: assert "installed" or "web" key exists
      3. Assert "client_id" field is non-empty
      4. Assert "client_secret" field is non-empty
    Expected Result: Valid OAuth credentials ready for deployment
    Evidence: JSON structure verified (secrets redacted in output)

  Scenario: Required APIs are enabled
    Tool: Bash (gcloud CLI or curl)
    Steps:
      1. gcloud services list --enabled --project=zuma-openclaw-agents
      2. Assert: output contains "sheets.googleapis.com"
      3. Assert: output contains "drive.googleapis.com"
      4. Assert: output contains "gmail.googleapis.com"
    Expected Result: All 4 required APIs enabled
    Evidence: API list captured
  ```

  **Commit**: NO (credential setup, no code files)

---

- [ ] 3. Create Telegram Bots via @BotFather

  **What to do**:
  - Create Telegram bots for each Layer 1 agent division:
    - `@ZumaOPS_StockBot` — OPS/Warehouse stock & inventory
    - `@ZumaOPS_LogisticsBot` — OPS/Logistics
    - `@ZumaOPS_BranchBot` — OPS/Branch operations
    - `@ZumaCEMES_SalesBot` — CEMES/Online sales
    - `@ZumaFATAL_AccountBot` — FATAL/Accounting
  - Create Telegram bots for Layer 2 overseers:
    - `@ZumaOverseer_OPSBot` — oversees OPS division agents
    - `@ZumaOverseer_CEMESBot` — oversees CEMES + FATAL
  - For each bot: save bot token securely, set bot description/about
  - Create Telegram groups:
    - `Zuma OPS Agents` — main group (OPS department)
    - `Zuma OPS Logs` — routine/low-priority logs
    - `Zuma CEMES Agents` — main group (CEMES/Marketing)
    - `Zuma FATAL Agents` — main group (FATAL/Finance)
    - `Zuma Agent Alerts` — cross-department critical alerts only
  - Add relevant bots + human PICs to each group
  - Record all bot tokens + group chat IDs

  **Must NOT do**:
  - Do NOT put bot tokens in any file that enters LLM prompts
  - Do NOT create more bots than needed for Phase 1 initially (start with StockBot only)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0A (with Tasks 1, 2, 4)
  - **Blocks**: Task 13 (Telegram group configuration)
  - **Blocked By**: None

  **References**:
  - **External References**:
    - Telegram BotFather: https://t.me/BotFather
    - OpenClaw Telegram config: `~/.openclaw/openclaw.json` → `telegram.botToken`, `telegram.allowedChatIds`
  - **Documentation References**:
    - Draft section 1: Department/division mapping table
    - Oracle gap #7: Telegram message flooding — split into main + logs groups

  **WHY Each Reference Matters**:
  - BotFather creates bot tokens needed for OpenClaw's Telegram integration
  - Oracle gap #7 solution: separate routine logs from alerts prevents group noise

  **Acceptance Criteria**:

  ```
  Scenario: Phase 1 bot is functional
    Tool: Bash (curl)
    Preconditions: @ZumaOPS_StockBot created via BotFather
    Steps:
      1. curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getMe"
      2. Assert: response.ok == true
      3. Assert: response.result.username == "ZumaOPS_StockBot"
      4. curl -s "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
           -d "chat_id=<OPS_GROUP_ID>&text=Test message from Stock Agent"
      5. Assert: response.ok == true
    Expected Result: Bot exists and can send messages to OPS group
    Evidence: API response bodies captured

  Scenario: Bot token is not exposed in any prompt-facing file
    Tool: Bash (grep)
    Steps:
      1. grep -r "BOT_TOKEN_VALUE" workspace/skills/ workspace/AGENTS.md 2>/dev/null
      2. Assert: zero matches
    Expected Result: No bot tokens in LLM-facing files
    Evidence: grep output (empty = pass)
  ```

  **Commit**: NO (Telegram setup, no code files)

---

- [ ] 4. Design Notion Workspace Structure

  **What to do**:
  - Create a new Notion workspace: "Zuma AI Agents"
  - Create database: **Agent Task Tracker** with fields:
    - Task Name (title): e.g., "Daily Stock Check - OPS"
    - Agent (select): VPS-1/Stock-Agent, VPS-2/Sales-Agent, etc.
    - Status (select): ⏳ Scheduled, 🔄 In Progress, 📋 Done by Agent, ❌ Revision Needed, ✅ L2 Approved, 📧 Pending Human Approval, ⏰ Approval Timeout, ✅✅ APPROVED, 🔴 ESCALATED
    - Failure Reason (text): e.g., "Accurate API timeout"
    - Revision Count (number): tracks how many revisions (max 2)
    - Last Run (date): timestamp of last execution
    - Duration (number): seconds to complete
    - Next Run (text): cron schedule in human-readable format
    - Output Link (URL): link to GSheet report or file
    - Reviewed By (select): Overseer-OPS, Overseer-CEMES, etc.
    - Approved By (text): human PIC name
    - Approval Date (date): when human approved
  - Create database: **Agent Health** with fields:
    - Agent Name, VPS/Machine, Last Heartbeat (date), Status (Online/Offline/Error), Uptime (text)
  - Create views: "Today's Tasks", "Needs Review", "Escalated", "Completed"
  - Obtain Notion API integration token (one per layer for doubled rate limit per Oracle advice)
  - Record database IDs for API access

  **Must NOT do**:
  - Do NOT over-design Notion — start minimal, iterate
  - Do NOT put Notion API token in SKILL.md

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0A (with Tasks 1, 2, 3)
  - **Blocks**: Task 10 (Notion database needs to exist)
  - **Blocked By**: None

  **References**:
  - **Documentation References**:
    - Draft section 8A: Notion Task Status Schema (fields defined)
    - Draft section 10: Full approval workflow lifecycle
    - Oracle gap #6: Email approval bottleneck — add 48h timeout status
  
  **WHY Each Reference Matters**:
  - Draft section 8A has the exact field definitions for the task tracker
  - Oracle gap #6: need "⏰ Approval Timeout" status for 48h escalation

  **Acceptance Criteria**:

  ```
  Scenario: Task Tracker database exists and has correct schema
    Tool: Bash (curl to Notion API)
    Preconditions: Notion workspace created, API token obtained
    Steps:
      1. curl -s "https://api.notion.com/v1/databases/<DB_ID>" \
           -H "Authorization: Bearer <NOTION_TOKEN>" \
           -H "Notion-Version: 2022-06-28"
      2. Assert: response.properties contains "Task Name" (title type)
      3. Assert: response.properties contains "Status" (select type)
      4. Assert: response.properties.Status.select.options includes "ESCALATED"
      5. Assert: response.properties contains "Revision Count" (number type)
    Expected Result: Database schema matches design
    Evidence: API response body captured

  Scenario: Can create and update a task entry
    Tool: Bash (curl to Notion API)
    Steps:
      1. POST /v1/pages — create entry with Task Name "Test Task", Status "Scheduled"
      2. Assert: response.id is non-empty
      3. PATCH /v1/pages/{id} — update Status to "Done by Agent"
      4. Assert: response.properties.Status.select.name == "Done by Agent"
    Expected Result: CRUD operations work on task tracker
    Evidence: API responses captured
  ```

  **Commit**: NO (Notion setup, no code files)

---

- [ ] 5. Design GSheet Template for Stock & Inventory Check

  **What to do**:
  - Create a GSheet: "Zuma Stock Check — [TEMPLATE]"
  - Tab 1: `raw_data` — where agent pastes stock data from Accurate/iSeller API
    - Columns: SKU, Product Name, Series, Size, Color, Warehouse Qty, Floor Qty, Box Qty, Last Updated
    - This tab is CLEARED and REFILLED by agent each run
  - Tab 2: `calculations` — formulas that compute metrics from raw_data
    - FF% = Floor Qty / Total Qty (per branch)
    - FB% = Box Qty / Total Qty (per branch)
    - Stock Minus items (where any qty < 0)
    - Total SKU count, branch-by-branch breakdown
  - Tab 3: `summary` — human-readable dashboard
    - Overall FF%, FB% per branch
    - Alert flags: 🔴 if FF < 70%, 🟡 if FF 70-80%, 🟢 if FF > 80%
    - Stock Minus list (auto-filtered)
    - Last updated timestamp
  - Tab 4: `alerts` — auto-generated alert list
    - Rows where thresholds are breached
    - Formulas: `=IF(FF%<0.7, "🔴 FF Below 70%", "")`, etc.
  - Add metadata row: `last_updated_by` (agent name), `last_updated_at` (timestamp)
  - Make template shareable with agent's Google account

  **Must NOT do**:
  - Do NOT hard-code branch names — use data validation dropdowns or dynamic references
  - Do NOT have agent write calculated values — only raw data and formulas
  - Do NOT create complex macros — stick to standard GSheet formulas

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []
    - No special skills — GSheet design is a documentation/design task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0B (with Tasks 6, 7)
  - **Blocks**: Task 12 (template must exist for agent to fill)
  - **Blocked By**: None (data schema comes from API docs + existing Supabase `jarvis.stock_current` table, not from VPS)

  **References**:
  - **Documentation References**:
    - Draft section 9: Core Pattern — Agent = Data Mover, GSheet = Calculator
    - Draft section 11 (Phase 1 PoC): Stock & Inventory Check agent flow
    - Draft section 5: Key Zuma Metrics — FF%, FB%, Stock Minus thresholds
  - **Pattern References**:
    - `D:\WAYAN\Work\0.KANTOR\ZUMA INDONESIA\0. DATA\0. N8N\00. CLAUDE CODE\CLAUDE.md` lines referencing Jarvis data: `jarvis.stock_current`, alert thresholds
  
  **WHY Each Reference Matters**:
  - Draft section 9 defines the fundamental pattern: agent writes raw, GSheet calculates
  - Alert thresholds (FF<70%, FB<80%) are hard requirements from CEO vision
  - Existing Supabase `jarvis.stock_current` schema hints at what columns the API returns

  **Acceptance Criteria**:

  ```
  Scenario: GSheet template has correct tab structure
    Tool: Bash (gog CLI)
    Preconditions: GSheet created, gog CLI configured
    Steps:
      1. gog sheets read <SPREADSHEET_ID> --range "raw_data!A1:A1" --json
      2. Assert: response is valid (tab exists)
      3. gog sheets read <SPREADSHEET_ID> --range "calculations!A1:A1" --json
      4. Assert: response is valid
      5. gog sheets read <SPREADSHEET_ID> --range "summary!A1:A1" --json
      6. Assert: response is valid
      7. gog sheets read <SPREADSHEET_ID> --range "alerts!A1:A1" --json
      8. Assert: response is valid
    Expected Result: All 4 tabs exist
    Evidence: gog CLI output captured

  Scenario: Formulas calculate correctly from sample data
    Tool: Bash (gog CLI)
    Steps:
      1. gog sheets write <ID> --range "raw_data!A2:I6" --values '<5 rows of test stock data>'
      2. Wait 3 seconds for GSheet recalculation
      3. gog sheets read <ID> --range "summary!B2" --json
      4. Assert: FF% value is calculated (not empty, not #REF!)
      5. gog sheets read <ID> --range "alerts!A2:C10" --json
      6. Assert: if test data has FF<70%, alert row exists
    Expected Result: Formulas produce correct calculations from raw data
    Evidence: Input data + calculated output captured
  ```

  **Commit**: NO (GSheet design, no code files)

---

- [ ] 6. Document SOP: How Stock Check Is Done Manually Today

  **What to do**:
  - Interview Wayan / OPS team: What exact steps does the admin follow for daily stock check?
  - Document in markdown: `workspace/skills/stock-check/docs/sop-stock-check.md`
  - Include:
    - Which system to log into (Accurate? iSeller? Both?)
    - What data to pull (which report, what filters, what date range)
    - Where to paste the data (which GSheet, which tab)
    - What to look for in the results (which numbers matter)
    - Who to alert and when (thresholds, contact persons)
    - How often (daily? what time?)
  - Use plain language (Indonesian is fine for internal SOP)
  - This document becomes the agent's SOP that SKILL.md references

  **Must NOT do**:
  - Do NOT invent steps — document what humans ACTUALLY do today
  - Do NOT write the SOP in technical jargon — write as if explaining to a new employee

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []
    - Writing skill is inherent in this category

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0B (with Tasks 5, 7)
  - **Blocks**: Task 11 (Agent needs SOP to know what to do)
  - **Blocked By**: None (can start immediately if Wayan provides info)

  **References**:
  - **Documentation References**:
    - Draft section 11: Phase 1 PoC — Stock & Inventory Check flow
    - Draft section 5: Data Sources — Accurate Online, iSeller, GSheets
    - `D:\WAYAN\Work\0.KANTOR\ZUMA INDONESIA\0. DATA\0. N8N\00. CLAUDE CODE\CLAUDE.md` — Jarvis context has department PICs (Virra for OPS, Galuh/Nabila for stock)
  
  **WHY Each Reference Matters**:
  - Draft section 11 has the generic agent flow (pull → clear → write → read → report)
  - Jarvis context has actual PIC names and alert routing rules

  **Acceptance Criteria**:

  ```
  Scenario: SOP document is complete and actionable
    Tool: Bash (file inspection)
    Steps:
      1. cat workspace/skills/stock-check/docs/sop-stock-check.md
      2. Assert: file exists and is non-empty
      3. Assert: contains section for "data source" (which system to pull from)
      4. Assert: contains section for "steps" (numbered steps)
      5. Assert: contains section for "thresholds" (FF%, FB%, Stock Minus)
      6. Assert: contains section for "who to alert" (PIC names)
      7. Assert: word count > 200 (not just a stub)
    Expected Result: Comprehensive SOP ready for agent consumption
    Evidence: File contents captured
  ```

  **Commit**: YES
  - Message: `docs(skills): add stock check SOP for Phase 1 agent`
  - Files: `workspace/skills/stock-check/docs/sop-stock-check.md`

---

- [ ] 7. Set Up Git Repo for Agent Workspaces

  **What to do**:
  - Create a private Git repository: `zuma-openclaw-workspaces`
  - Structure:
    ```
    zuma-openclaw-workspaces/
    ├── vps-1/
    │   ├── skills/
    │   ├── AGENTS.md
    │   └── .env.example
    ├── vps-2/
    │   ├── skills/
    │   ├── AGENTS.md
    │   └── .env.example
    ├── vps-3/
    │   ├── skills/
    │   ├── AGENTS.md
    │   └── .env.example
    ├── overseer-ops/
    │   ├── HEARTBEAT.md
    │   ├── AGENTS.md
    │   └── .env.example
    ├── overseer-cemes/
    │   ├── HEARTBEAT.md
    │   ├── AGENTS.md
    │   └── .env.example
    └── shared/
        └── templates/  ← shared SOP templates
    ```
  - Add `.gitignore`: exclude `.env`, `memory/`, `*.log`, `node_modules/`
  - Create `README.md` with: repo purpose, how to clone to VPS, how to pull updates
  - Set up deploy keys: each VPS and Mac Mini gets read-only access to pull workspace updates
  - Layer 2 gets write access to push skills.md fixes

  **Must NOT do**:
  - Do NOT commit .env files (contain API keys)
  - Do NOT commit memory/ directories (contain conversation history)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
    - `git-master`: Git repo setup, branch structure, deploy keys

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0B (with Tasks 5, 6)
  - **Blocks**: Task 25 (all workspaces need Git versioning)
  - **Blocked By**: None

  **References**:
  - **Documentation References**:
    - Oracle gap #5: Skills.md editing needs Git — no rollback without version control
    - Draft section 3: Self-healing via SSH — Layer 2 pushes skills fixes
  
  **WHY Each Reference Matters**:
  - Oracle explicitly flagged: without Git, a bad skills.md edit from Layer 2 SSH can break an agent with no rollback path

  **Acceptance Criteria**:

  ```
  Scenario: Git repo is initialized with correct structure
    Tool: Bash (git)
    Steps:
      1. git clone <repo-url> /tmp/test-clone
      2. ls /tmp/test-clone/vps-1/skills/
      3. Assert: directory exists
      4. ls /tmp/test-clone/vps-1/AGENTS.md
      5. Assert: file exists
      6. cat /tmp/test-clone/.gitignore
      7. Assert: contains ".env"
      8. Assert: contains "memory/"
    Expected Result: Repo structure matches design
    Evidence: Directory listing captured

  Scenario: .env files are not tracked
    Tool: Bash (git)
    Steps:
      1. echo "SECRET=test" > /tmp/test-clone/vps-1/.env
      2. git -C /tmp/test-clone status
      3. Assert: .env does NOT appear in untracked files
    Expected Result: Sensitive files are gitignored
    Evidence: git status output captured
  ```

  **Commit**: YES (this IS the first commit of the new repo)
  - Message: `init: scaffold zuma-openclaw-workspaces repo structure`
  - Files: All scaffold files

---

### ═══ PHASE 1: PROOF OF CONCEPT (Week 1-3) ═══

---

- [ ] 8. Install OpenClaw on VPS-1

  **What to do**:
  - SSH into VPS-1
  - Install OpenClaw: `npm install -g openclaw` (or per official docs)
  - Configure `~/.openclaw/openclaw.json`:
    - Set LLM provider: Anthropic Claude
    - Set default model: `claude-3-5-haiku-20241022` (cheap for Layer 1 routine tasks)
    - Set fallback model: `claude-sonnet-4-20250514` (for complex tasks)
    - Set Telegram bot token for StockBot
    - Set allowed chat IDs (OPS group only for Phase 1)
    - Set cron config: `maxConcurrentRuns: 1` (single agent in Phase 1)
    - Set timezone: `Asia/Jakarta`
    - Enable sandboxing if available
    - Set tool restrictions: allow `exec`, `read`, `write`, `edit`, `cron`; deny `browser`, `canvas`
  - Clone workspace from Git repo: `git clone <repo> ~/workspace`
  - Symlink or configure OpenClaw to use `~/workspace/vps-1/` as agent workspace
  - Test: `openclaw health --json` returns healthy status
  - Set up OpenClaw as systemd service for auto-restart on crash
  - Set up rescue bot on port 19001 (secondary Gateway to monitor main)

  **Must NOT do**:
  - Do NOT enable browser tool
  - Do NOT use GPT models (cost + consistency — stick with Claude)
  - Do NOT run OpenClaw as root

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1A (with Tasks 9, 10)
  - **Blocks**: Tasks 11, 14 (agent needs OpenClaw running)
  - **Blocked By**: Task 1 (VPS must exist)

  **References**:
  - **External References**:
    - OpenClaw installation: https://docs.openclaw.ai/ — installation and configuration
    - OpenClaw config reference: `~/.openclaw/openclaw.json` schema
    - Draft section 3: Multi-agent config, cron config, rescue bot pattern
    - Draft section 4: Security — tool allow/deny per agent, sandboxing
  
  **WHY Each Reference Matters**:
  - OpenClaw docs have the exact JSON schema for openclaw.json configuration
  - Draft section 3 has the rescue bot pattern (secondary Gateway on port 19001)
  - Draft section 4 has the exact tool allow/deny list

  **Acceptance Criteria**:

  ```
  Scenario: OpenClaw is installed and healthy
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "openclaw --version"
      2. Assert: version number returned (not "command not found")
      3. ssh openclaw-admin@<VPS_IP> "openclaw health --json"
      4. Assert: JSON response with status "healthy" or "ok"
    Expected Result: OpenClaw installed and running
    Evidence: Health check JSON captured

  Scenario: Gateway starts and stays running
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "systemctl status openclaw-main"
      2. Assert: "active (running)"
      3. Wait 30 seconds
      4. ssh openclaw-admin@<VPS_IP> "systemctl status openclaw-main"
      5. Assert: still "active (running)" (not crashed)
    Expected Result: Gateway is stable as systemd service
    Evidence: systemctl output captured

  Scenario: Rescue bot is running on separate port
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "systemctl status openclaw-rescue"
      2. Assert: "active (running)"
      3. ssh openclaw-admin@<VPS_IP> "curl -s http://localhost:19001/health"
      4. Assert: response indicates healthy
    Expected Result: Rescue bot monitors main Gateway
    Evidence: Health check output captured

  Scenario: Browser tool is denied
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "cat ~/.openclaw/openclaw.json | python3 -c 'import json,sys; c=json.load(sys.stdin); print(c[\"agents\"][\"list\"][0][\"tools\"][\"deny\"])'"
      2. Assert: output contains "browser"
    Expected Result: Browser tool explicitly denied in config
    Evidence: Config snippet captured
  ```

  **Commit**: YES
  - Message: `config(vps-1): add OpenClaw configuration for stock agent`
  - Files: `vps-1/.openclaw/openclaw.json` (in Git workspace repo)
  - Pre-commit: `openclaw health --json`

---

- [ ] 9. Install gog CLI + Configure Google OAuth on VPS-1

  **What to do**:
  - Install `gog` CLI on VPS-1
    - For Linux: download binary from https://github.com/steipete/gogcli/releases
    - Make executable: `chmod +x gog && sudo mv gog /usr/local/bin/`
  - Copy `client_secret.json` from Task 2 to VPS-1 (via scp, not Git)
  - Run OAuth flow: `gog auth add zuma-agent@company.com --services gmail,sheets,drive,docs`
    - This opens a browser URL — copy URL, complete OAuth on local machine, paste code back
  - Test each service:
    - `gog sheets read <test-spreadsheet-id> --range "A1:A1" --json`
    - `gog gmail send --to test@test.com --subject "Test" --body "Agent test"`
    - `gog drive list --limit 5 --json`
  - Store OAuth tokens in `~/.config/gog/` (default location, NOT in workspace)

  **Must NOT do**:
  - Do NOT store client_secret.json in Git
  - Do NOT put OAuth tokens in SKILL.md or AGENTS.md
  - Do NOT give agent access to all Gmail — scope to specific labels/senders

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1A (with Tasks 8, 10)
  - **Blocks**: Task 11 (agent needs gog to access GSheets)
  - **Blocked By**: Tasks 2 (OAuth credentials), 8 (VPS with OpenClaw)

  **References**:
  - **External References**:
    - `gog` CLI docs: https://gogcli.sh
    - `gog` GitHub: https://github.com/steipete/gogcli — releases page for Linux binary
  - **Documentation References**:
    - Draft section 8A: gog auth command syntax, supported services

  **WHY Each Reference Matters**:
  - gog CLI is the ONLY way Layer 1 agents access Google Workspace (no browser)
  - Draft section 8A has the exact auth command and service list

  **Acceptance Criteria**:

  ```
  Scenario: gog CLI binary is installed and functional
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "gog --version"
      2. Assert: version string returned (not "command not found")
      3. If gog binary does not exist for Linux: THIS IS A CRITICAL BLOCKER — fall back to direct Google Sheets API via curl
    Expected Result: gog CLI installed on Linux VPS
    Evidence: Version string captured
    Failure Indicators: "command not found", "no such file", or binary execution error

  Scenario: gog CLI can read a GSheet
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "gog sheets read <TEMPLATE_SPREADSHEET_ID> --range 'raw_data!A1:A1' --json"
      2. Assert: JSON response with cell value (not auth error)
    Expected Result: GSheet read works from VPS
    Evidence: API response captured

  Scenario: gog CLI can send a Gmail
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "gog gmail send --to wayan@zumagroup.com --subject 'Agent Test' --body 'This is a test from OpenClaw stock agent'"
      2. Assert: no error in output
      3. Verify: email received (check via gog gmail search or manual)
    Expected Result: Gmail sending works from VPS
    Evidence: Send output captured
  ```

  **Commit**: NO (credential deployment, no code files)

---

- [ ] 10. Create Notion Task Tracking Database (Populate with Phase 1 Tasks)

  **What to do**:
  - Using the Notion workspace from Task 4, create initial task entries:
    - "Daily Stock Check — OPS/Warehouse" — Agent: VPS-1/Stock-Agent, Status: ⏳ Scheduled, Cron: "30 8 * * * (8:30 WIB daily)"
  - Install or configure Notion API access on VPS-1:
    - Store Notion integration token in `.env` on VPS-1
    - Test: agent can read and update task entries via Notion API
  - Create a helper script or skill doc that shows the agent how to update Notion:
    - After cron job completes → update status to "Done by Agent" + attach output link
    - If cron job fails → update status to "❌ Failed" + failure reason

  **Must NOT do**:
  - Do NOT put Notion API token in SKILL.md

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1A (with Tasks 8, 9)
  - **Blocks**: Task 15 (end-to-end test needs Notion)
  - **Blocked By**: Task 4 (Notion workspace must exist)

  **References**:
  - **Documentation References**:
    - Draft section 8A: Notion Task Status Schema
    - Draft section 10: Approval workflow lifecycle
  - **External References**:
    - Notion API: https://developers.notion.com/reference

  **WHY Each Reference Matters**:
  - Draft section 8A defines the exact fields the agent must update
  - Draft section 10 defines the status lifecycle (Scheduled → In Progress → Done → Approved)

  **Acceptance Criteria**:

  ```
  Scenario: Agent can update Notion task status
    Tool: Bash (curl to Notion API from VPS)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "curl -s -X PATCH 'https://api.notion.com/v1/pages/<TASK_PAGE_ID>' \
           -H 'Authorization: Bearer <NOTION_TOKEN>' \
           -H 'Content-Type: application/json' \
           -H 'Notion-Version: 2022-06-28' \
           -d '{\"properties\":{\"Status\":{\"select\":{\"name\":\"In Progress\"}}}}'"
      2. Assert: response contains updated status
      3. Query the page again and verify status changed
    Expected Result: VPS can update Notion entries
    Evidence: API responses captured
  ```

  **Commit**: NO (Notion configuration, no code files)

---

- [ ] 11. Build Stock Agent — AGENTS.md + Skills + SOP Docs

  **What to do**:
  - Create `vps-1/AGENTS.md` — the Stock Agent's personality and instructions:
    ```markdown
    # Stock & Inventory Agent — OPS/Warehouse

    You are the Stock & Inventory Agent for Zuma Indonesia OPS department.
    Your job is to pull stock data, fill GSheet templates, and report results.

    ## Core Rules
    - You are a DATA MOVER. You pull raw data and paste it into GSheets.
    - You do NOT calculate anything — GSheet formulas do all math.
    - Always clear the raw_data tab before writing new data.
    - Always add last_updated_by (your name) and last_updated_at (timestamp) metadata.
    - If a cron job fails, update Notion status to Failed with the error reason.
    - Never skip steps in the SOP. Follow each step exactly.

    ## Memory Rules
    - After each task, write key results to memory/YYYY-MM-DD.md
    - Keep MEMORY.md under 2000 words
    - If context is getting long, save and start fresh

    ## Tools Available
    - exec: run gog CLI commands, API calls
    - read/write/edit: manage workspace files
    - cron: manage your schedule

    ## Tools DENIED
    - browser: NEVER use browser (causes crashes)
    ```
  - Create `vps-1/skills/stock-check/SKILL.md`:
    ```markdown
    ---
    name: daily-stock-check
    description: Pull stock data from Accurate/iSeller, fill GSheet template, report to Telegram, update Notion
    ---
    When invoked, read the full procedure from `{baseDir}/docs/sop-stock-check.md`.
    Follow each step exactly. Do not skip steps.
    After completion, update Notion task status and report to Telegram group.
    ```
  - Copy the SOP from Task 6 into `vps-1/skills/stock-check/docs/sop-stock-check.md`
  - Create `.env` on VPS-1 with:
    - `ACCURATE_API_KEY`, `ACCURATE_SECRET`, `ACCURATE_BASE_URL`
    - `NOTION_TOKEN`, `NOTION_TASK_DB_ID`
    - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OPS_GROUP_ID`
    - `STOCK_GSHEET_ID` (from Task 5)
  - Configure agent in `openclaw.json` agents list

  **Must NOT do**:
  - Do NOT put API keys in AGENTS.md or SKILL.md
  - Do NOT write calculation logic in the agent — only data movement
  - Do NOT give this agent access to GSheets from other departments

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
    - Deep category for careful, thorough agent design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1B (with Tasks 12, 13)
  - **Blocks**: Task 14 (cron job needs working agent)
  - **Blocked By**: Tasks 6 (SOP), 8 (OpenClaw installed), 9 (gog configured)

  **References**:
  - **Pattern References**:
    - Draft section 4A: Reference-based skills architecture — SKILL.md + docs/ pattern with exact code examples
    - Draft section 9: Core Pattern — Agent = Data Mover — the 4 gog operations
    - Draft section 3: Multi-agent config — agents.list[] in openclaw.json
  - **Documentation References**:
    - Draft section 11: Phase 1 PoC agent flow (8 steps)
    - Task 6 output: SOP document
  - **External References**:
    - OpenClaw agent workspace docs: https://docs.openclaw.ai/ — AGENTS.md format, skills structure

  **WHY Each Reference Matters**:
  - Draft section 4A has the exact SKILL.md template with `{baseDir}` reference pattern
  - Draft section 9 defines the 4 gog operations (clear → write → read → report) that are the agent's ENTIRE job
  - Draft section 3 has the openclaw.json agents.list[] format for multi-agent config

  **Acceptance Criteria**:

  ```
  Scenario: Agent workspace files exist and are valid
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "cat ~/workspace/vps-1/AGENTS.md"
      2. Assert: contains "DATA MOVER"
      3. Assert: contains "browser" in denied section
      4. ssh openclaw-admin@<VPS_IP> "cat ~/workspace/vps-1/skills/stock-check/SKILL.md"
      5. Assert: contains "daily-stock-check"
      6. Assert: contains "{baseDir}/docs/sop-stock-check.md"
      7. ssh openclaw-admin@<VPS_IP> "cat ~/workspace/vps-1/skills/stock-check/docs/sop-stock-check.md"
      8. Assert: file exists and word count > 200
    Expected Result: All agent workspace files correctly structured
    Evidence: File contents captured

  Scenario: No API keys in prompt-facing files
    Tool: Bash (ssh + grep)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "grep -r 'ACCURATE_API_KEY\|NOTION_TOKEN\|BOT_TOKEN' ~/workspace/vps-1/AGENTS.md ~/workspace/vps-1/skills/ 2>/dev/null"
      2. Assert: zero matches (empty output)
    Expected Result: No secrets in LLM-facing files
    Evidence: grep output captured (empty = pass)
  ```

  **Commit**: YES
  - Message: `feat(agent): add Stock Agent workspace — AGENTS.md, skills, SOP docs`
  - Files: `vps-1/AGENTS.md`, `vps-1/skills/stock-check/SKILL.md`, `vps-1/skills/stock-check/docs/sop-stock-check.md`
  - Pre-commit: grep for API keys in committed files (must be zero)

---

- [ ] 12. Create Stock GSheet Template with Formulas (Production Copy)

  **What to do**:
  - Take the template design from Task 5 and create the PRODUCTION GSheet
  - Share with the agent's Google account (from gog OAuth setup)
  - Verify formulas work with sample data:
    - Write 5 rows of test stock data to `raw_data` tab
    - Check `calculations` tab — FF%, FB% calculated correctly
    - Check `summary` tab — alerts triggered for below-threshold values
    - Check `alerts` tab — flagged items appear
  - Record the production Spreadsheet ID
  - Add to VPS-1 `.env` as `STOCK_GSHEET_ID`

  **Must NOT do**:
  - Do NOT modify the template after validation — lock formulas
  - Do NOT share with edit access to accounts that don't need it

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1B (with Tasks 11, 13)
  - **Blocks**: Task 14 (cron job writes to this GSheet)
  - **Blocked By**: Tasks 2 (OAuth), 5 (template design)

  **References**:
  - **Documentation References**:
    - Task 5 output: GSheet template design (tabs, columns, formulas)
    - Draft section 9: Agent = Data Mover pattern

  **Acceptance Criteria**:

  ```
  Scenario: Production GSheet accessible from VPS via gog
    Tool: Bash (ssh + gog)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "gog sheets read <PROD_GSHEET_ID> --range 'raw_data!A1:I1' --json"
      2. Assert: header row matches expected columns (SKU, Product Name, Series, etc.)
      3. ssh openclaw-admin@<VPS_IP> "gog sheets read <PROD_GSHEET_ID> --range 'summary!A1:A1' --json"
      4. Assert: summary tab accessible
    Expected Result: Production GSheet is ready and accessible from VPS
    Evidence: Column headers and tab access confirmed
  ```

  **Commit**: NO (GSheet is in Google, not Git)

---

- [ ] 13. Configure Telegram Group (OPS Department)

  **What to do**:
  - Add `@ZumaOPS_StockBot` to the "Zuma OPS Agents" group (from Task 3)
  - Configure OpenClaw Telegram settings:
    - `telegram.botToken` in openclaw.json
    - `telegram.allowedChatIds` = [OPS group chat ID]
    - `telegram.allowedUserIds` = [Wayan's Telegram user ID, other authorized users]
  - Test: send a message from agent to group
  - Configure message formatting:
    - Routine reports: plain text, sent to OPS group
    - Alerts (threshold breached): bold/emoji, sent to both OPS group + Alerts group
  - Set up the "Zuma OPS Logs" group for routine/verbose output

  **Must NOT do**:
  - Do NOT allow unknown users to chat with the bot
  - Do NOT flood the main group with verbose logs

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1B (with Tasks 11, 12)
  - **Blocks**: Task 14 (cron needs Telegram delivery)
  - **Blocked By**: Task 3 (bots and groups must exist)

  **References**:
  - **Documentation References**:
    - Oracle gap #7: Telegram flooding — split routine vs alert messages
    - Draft section 3: Cron `--announce --channel telegram --to "<GROUP_CHAT_ID>"`

  **Acceptance Criteria**:

  ```
  Scenario: Bot can post to OPS group
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "curl -s 'https://api.telegram.org/bot<TOKEN>/sendMessage' \
           -d 'chat_id=<OPS_GROUP_ID>&text=🤖 Stock Agent online. Phase 1 test.'"
      2. Assert: response.ok == true
    Expected Result: Message appears in OPS Telegram group
    Evidence: API response + message visible in group

  Scenario: Unauthorized user cannot interact with bot
    Tool: Bash (curl)
    Steps:
      1. Send message from unauthorized user to bot
      2. Assert: bot does not respond (allowedChatIds enforced)
    Expected Result: Bot ignores unauthorized interactions
    Evidence: No response from bot
  ```

  **Commit**: YES
  - Message: `config(telegram): configure OPS department group for stock agent`
  - Files: updated `openclaw.json` (Telegram section)

---

- [ ] 14. Configure Cron Job for Daily Stock Check

  **What to do**:
  - Add cron job via OpenClaw CLI:
    ```bash
    openclaw cron add \
      --name "Daily Stock & Inventory Check" \
      --cron "30 8 * * *" \
      --tz "Asia/Jakarta" \
      --session isolated \
      --message "Execute skill: daily-stock-check. Pull stock data from Accurate API, clear and fill GSheet template, read summary, report to Telegram group, update Notion task status. If any threshold is breached (FF<70%, FB<80%, Stock<0), send immediate alert." \
      --announce --channel telegram --to "<OPS_GROUP_CHAT_ID>"
    ```
  - Verify cron is registered: `openclaw cron list`
  - Set model override for this job: Haiku (cheap, routine task)
  - Add a test cron that runs in 5 minutes to verify the full pipeline works
  - After test passes, remove test cron, keep production cron

  **Must NOT do**:
  - Do NOT use UTC without timezone specification
  - Do NOT schedule overlapping cron jobs on same agent in Phase 1

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1C)
  - **Blocks**: Task 15 (E2E test)
  - **Blocked By**: Tasks 11, 12, 13 (agent, GSheet, Telegram must be ready)

  **References**:
  - **Documentation References**:
    - Draft section 3: Cron job syntax — `openclaw cron add` with all flags
    - Draft section 11: Phase 1 PoC flow — the 8-step agent flow
    - Oracle gap #10: GSheet API quota — stagger crons by 15+ min
  
  **WHY Each Reference Matters**:
  - Draft section 3 has the exact CLI syntax including timezone and announce flags
  - Oracle gap #10: even with 1 agent, establish the stagger pattern for future expansion

  **Acceptance Criteria**:

  ```
  Scenario: Cron job is registered with correct schedule
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "openclaw cron list --json"
      2. Assert: output contains job named "Daily Stock & Inventory Check"
      3. Assert: schedule is "30 8 * * *"
      4. Assert: timezone is "Asia/Jakarta"
      5. Assert: session is "isolated"
    Expected Result: Cron job correctly configured
    Evidence: Cron list JSON captured

  Scenario: Test cron executes successfully
    Tool: Bash (ssh + wait)
    Steps:
      1. Add test cron for 5 minutes from now
      2. Wait for execution time + 5 min buffer
      3. Check Telegram group for report message
      4. Check Notion task for status update
      5. Check GSheet for fresh data
    Expected Result: Full pipeline executes: API → GSheet → Telegram → Notion
    Evidence: Telegram message + Notion status + GSheet data timestamps
  ```

  **Commit**: NO (cron is stored in OpenClaw's internal storage, not Git)

---

- [ ] 15. End-to-End Test: Full Pipeline Validation

  **What to do**:
  - Trigger the stock check manually: `openclaw cron run "Daily Stock & Inventory Check"`
  - Verify each step of the pipeline:
    1. ✅ Agent pulls data from Accurate API (check agent logs)
    2. ✅ Agent clears `raw_data` tab in GSheet (check with `gog sheets read`)
    3. ✅ Agent writes fresh stock data to `raw_data` tab
    4. ✅ GSheet formulas calculate FF%, FB%, alerts (check `summary` tab)
    5. ✅ Agent reads `summary` tab and `alerts` tab
    6. ✅ Agent posts report to Telegram OPS group
    7. ✅ Agent updates Notion task status to "Done by Agent"
    8. ✅ Agent includes output link (GSheet URL) in Notion
  - If any step fails: fix and retest
  - Test with intentionally bad data to verify alert thresholds
  - Verify metadata: `last_updated_by` and `last_updated_at` present in GSheet

  **Must NOT do**:
  - Do NOT skip validation steps
  - Do NOT declare success on partial pipeline completion

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
    - Deep category for thorough validation requiring careful attention

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1C)
  - **Blocks**: Task 16 (parallel run needs working pipeline)
  - **Blocked By**: Tasks 14, 10 (cron + Notion must be ready)

  **References**:
  - **Documentation References**:
    - Draft section 11: 8-step agent flow for stock check
    - Draft section 9: Core Pattern — 4 gog operations
    - Oracle gap #2: Partial data writes — verify atomic write behavior

  **Acceptance Criteria**:

  ```
  Scenario: Full pipeline executes without errors
    Tool: Bash (ssh + gog + curl)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "openclaw cron run 'Daily Stock & Inventory Check' 2>&1"
      2. Wait 120 seconds for completion
      3. gog sheets read <GSHEET_ID> --range "raw_data!A2:A2" --json
      4. Assert: cell is non-empty (data was written)
      5. gog sheets read <GSHEET_ID> --range "summary!B2" --json
      6. Assert: FF% value is a number between 0 and 100
      7. Check Telegram OPS group for new message (within last 5 minutes)
      8. Assert: message contains "Stock" and date
      9. curl Notion API — query task page
      10. Assert: status is "Done by Agent"
      11. Assert: Output Link field contains GSheet URL
    Expected Result: All 8 pipeline steps completed successfully
    Evidence: GSheet data, Telegram message, Notion status — all captured

  Scenario: Alert triggers when threshold breached
    Tool: Bash (ssh + gog)
    Steps:
      1. Write test data to raw_data where FF% < 70%
      2. Wait for GSheet recalculation
      3. Trigger stock check cron manually
      4. Check Telegram for alert message
      5. Assert: message contains "🔴" or "Below" or alert indicator
    Expected Result: Threshold breach triggers alert in Telegram
    Evidence: Alert message captured

  Scenario: Metadata present on GSheet writes
    Tool: Bash (gog)
    Steps:
      1. gog sheets read <GSHEET_ID> --range "raw_data!J1:K1" --json
      2. Assert: headers include "last_updated_by" and "last_updated_at"
      3. gog sheets read <GSHEET_ID> --range "raw_data!J2:K2" --json
      4. Assert: values are non-empty (agent name + timestamp)
    Expected Result: Every write includes agent attribution
    Evidence: Metadata cells captured
  ```

  **Commit**: NO (testing, no code changes)

---

- [ ] 16. 5-Day Parallel Run: Agent vs Human Side-by-Side

  **What to do**:
  - For 5 consecutive business days:
    - Agent runs daily stock check at 8:30 WIB via cron
    - Human admin performs the same stock check manually (as they do today)
    - Compare results at end of each day
  - Create comparison log:
    - Day 1: Agent FF% = X%, Human FF% = Y%, Match: YES/NO
    - Day 2: ... etc.
  - If mismatch: investigate root cause (API data? formula error? timing difference?)
  - Fix any issues found, re-validate
  - After 5 days of matching results → Phase 1 PoC is VALIDATED
  - Human admin can stop doing the task manually

  **Must NOT do**:
  - Do NOT skip the parallel run — this builds TRUST with the team
  - Do NOT declare validation success with fewer than 5 matching days

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []
    - Writing category: this task is about documenting comparison results

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential — gate between Phase 1 and Phase 2
  - **Blocks**: Task 17 (expansion requires validated PoC)
  - **Blocked By**: Task 15 (E2E must pass first)

  **References**:
  - **Documentation References**:
    - Draft section 8C: Solution 3 — Parallel Run (agent vs human side-by-side)
    - Draft section 8D: Phase 1 uses parallel run for trust-building

  **Acceptance Criteria**:

  ```
  Scenario: 5-day comparison log is complete
    Tool: Bash (file check)
    Steps:
      1. cat validation/parallel-run-log.md
      2. Assert: 5 date entries exist
      3. Assert: each entry has Agent result + Human result + Match status
      4. Assert: all 5 days show "Match: YES" (or issues documented and resolved)
    Expected Result: Agent matches human output for 5 consecutive days
    Evidence: Comparison log file captured
  ```

  **Commit**: YES
  - Message: `docs(validation): add 5-day parallel run comparison log`
  - Files: `validation/parallel-run-log.md`

---

### ═══ PHASE 2: EXPAND LAYER 1 (Week 3-5) ═══

---

- [ ] 17. Provision VPS-2 and VPS-3

  **What to do**:
  - Purchase 2 additional VPS (same spec as VPS-1: 4 vCPU, 8GB RAM, 100GB SSD, Ubuntu 22.04)
  - Apply same setup as Task 1: non-root user, SSH key auth, firewall, Node.js, Python, timezone
  - VPS-2: hosts CEMES (Marketing) agents — online sales, marketplace data
  - VPS-3: hosts FATAL (Finance) agents — accounting, tax
  - Additional OPS agents (logistics, branch ops) go on VPS-1 (multi-agent)

  **Must NOT do**:
  - Do NOT reuse VPS-1's SSH keys — generate fresh keys per machine

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2A (with Tasks 18, 19)
  - **Blocks**: Task 18 (OpenClaw install)
  - **Blocked By**: Task 16 (Phase 1 must be validated)

  **Acceptance Criteria**:
  - Same as Task 1, applied to VPS-2 and VPS-3

  **Commit**: NO (infrastructure)

---

- [ ] 18. Install OpenClaw + gog on VPS-2 and VPS-3

  **What to do**:
  - Repeat Tasks 8 and 9 for VPS-2 and VPS-3
  - Same OpenClaw config pattern but with different agent IDs
  - Same gog OAuth setup (same Google account, already authorized)
  - Set up systemd services + rescue bots on each

  **Must NOT do**:
  - Do NOT copy `.openclaw/` directory between machines — configure fresh

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (VPS-2 and VPS-3 can be set up simultaneously)
  - **Parallel Group**: Wave 2A
  - **Blocks**: Tasks 20, 21, 22 (agents need OpenClaw)
  - **Blocked By**: Task 17 (VPS must exist)

  **Acceptance Criteria**:
  - Same as Tasks 8 + 9, applied to VPS-2 and VPS-3

  **Commit**: YES
  - Message: `config(vps-2,vps-3): add OpenClaw configuration for CEMES and FATAL agents`
  - Files: `vps-2/AGENTS.md`, `vps-3/AGENTS.md`, configs

---

- [ ] 19. Create Department Telegram Groups + Logs Groups

  **What to do**:
  - Create remaining groups from Task 3 plan:
    - "Zuma CEMES Agents" + "Zuma CEMES Logs"
    - "Zuma FATAL Agents" + "Zuma FATAL Logs"
  - Add relevant bots and human PICs to each group
  - Configure allowedChatIds on VPS-2 and VPS-3

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2A (with Tasks 17, 18)
  - **Blocks**: Task 26
  - **Blocked By**: Tasks 3, 16 (Phase 1 validation gates Phase 2)

  **Acceptance Criteria**:
  - Same pattern as Task 13, for CEMES and FATAL groups

  **Commit**: NO (Telegram setup)

---

- [ ] 20. Build CEMES (Marketing) Agents

  **What to do**:
  - Build agents for VPS-2:
    - **Online Sales Agent**: Pulls marketplace data from Ginee API, fills sales GSheet templates
    - **Campaign Agent**: Tracks promo performance metrics
  - Create AGENTS.md, skills, SOP docs following same pattern as Task 11
  - Create GSheet templates for each agent's domain (same template-driven pattern)
  - Configure cron jobs staggered 15+ min apart from each other AND from VPS-1 crons

  **Must NOT do**:
  - Do NOT have CEMES agents write to OPS department GSheets
  - Do NOT copy-paste AGENTS.md from VPS-1 — write domain-specific instructions

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2B (with Tasks 21, 22)
  - **Blocks**: Task 23 (cron scheduling)
  - **Blocked By**: Task 18

  **References**:
  - **Documentation References**:
    - Draft section 5: Data Sources — Ginee (marketplace aggregator)
    - Task 11 output: Stock Agent pattern to follow
  - **Pattern References**:
    - `vps-1/AGENTS.md` — follow same structure for CEMES agents

  **Acceptance Criteria**:
  - Same pattern as Tasks 11-15, adapted for CEMES domain
  - Verify: Ginee API data → GSheet → Telegram → Notion pipeline works

  **Commit**: YES
  - Message: `feat(agent): add CEMES marketing agents — online sales + campaign`
  - Files: `vps-2/AGENTS.md`, `vps-2/skills/*/`

---

- [ ] 21. Build FATAL (Finance) Agents

  **What to do**:
  - Build agents for VPS-3:
    - **Accounting Agent**: Pulls financial data from Accurate Online, fills accounting GSheet templates
    - **Tax Agent**: Generates tax-related reports and invoices
  - Same pattern as Task 11 and Task 20
  - Finance data requires extra attention to accuracy — add double-check step in SOP

  **Must NOT do**:
  - Do NOT allow finance agents to modify OPS or CEMES data
  - Do NOT skip the double-check step for financial calculations

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2B (with Tasks 20, 22)
  - **Blocks**: Task 23
  - **Blocked By**: Task 18

  **Acceptance Criteria**:
  - Same pattern as Tasks 11-15, adapted for FATAL domain
  - Extra: verify financial calculations have double-check mechanism

  **Commit**: YES
  - Message: `feat(agent): add FATAL finance agents — accounting + tax`
  - Files: `vps-3/AGENTS.md`, `vps-3/skills/*/`

---

- [ ] 22. Build Additional OPS Agents (Logistics, Branch Ops)

  **What to do**:
  - Add agents to VPS-1 (multi-agent on same Gateway):
    - **Logistics Agent**: Tracks shipments, delivery status
    - **Branch Ops Agent**: Branch performance reports, attendance data
  - Update VPS-1 `openclaw.json` agents list to include new agents
  - Create separate skills directories for each agent
  - Each agent gets its own GSheet files (no collisions per Oracle gap #4)
  - Stagger cron schedules: Stock at 8:30, Logistics at 9:00, Branch at 9:30

  **Must NOT do**:
  - Do NOT exceed `maxConcurrentRuns: 2` on VPS-1

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2B (with Tasks 20, 21)
  - **Blocks**: Task 23
  - **Blocked By**: Task 16 (Phase 1 validated — VPS-1 already has OpenClaw from Task 8)

  **Acceptance Criteria**:
  - Verify multi-agent works: `openclaw cron list` shows all 3 OPS agents with staggered times
  - Verify isolation: each agent has own GSheet, own skills directory

  **Commit**: YES
  - Message: `feat(agent): add logistics + branch ops agents to VPS-1 multi-agent`
  - Files: `vps-1/skills/logistics/`, `vps-1/skills/branch-ops/`

---

- [ ] 23. Configure All Cron Jobs with Staggered Timing

  **What to do**:
  - Map all agent cron schedules with 15+ minute gaps:
    - VPS-1: Stock 8:30, Logistics 9:00, Branch 9:30 WIB
    - VPS-2: Online Sales 8:45, Campaign 9:15 WIB
    - VPS-3: Accounting 8:15, Tax 10:00 WIB
  - Leave 3-4 hour gaps between first run and potential revision window
  - All use `--tz "Asia/Jakarta"` and `--session isolated`
  - Document full schedule in a shared reference file

  **Must NOT do**:
  - Do NOT schedule overlapping crons that hit the same GSheet API project
  - Do NOT forget timezone on any cron job

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2C (with Tasks 24, 25, 26)
  - **Blocks**: Task 26
  - **Blocked By**: Tasks 20, 21, 22

  **Acceptance Criteria**:

  ```
  Scenario: All cron jobs have staggered schedules
    Tool: Bash (ssh to each VPS)
    Steps:
      1. For each VPS: openclaw cron list --json
      2. Parse all job times
      3. Assert: no two jobs on same VPS start within 15 min of each other
      4. Assert: all jobs have timezone "Asia/Jakarta"
    Expected Result: Zero scheduling conflicts
    Evidence: Combined cron schedule captured
  ```

  **Commit**: YES
  - Message: `docs: add master cron schedule for all Layer 1 agents`
  - Files: `shared/cron-schedule.md`

---

- [ ] 24. Security Hardening: Sandboxing + Tool Restrictions

  **What to do**:
  - For each VPS, verify and enforce:
    - Tool allow/deny lists are correctly configured per agent
    - `browser` tool is DENIED on all Layer 1 agents
    - Sandboxing is enabled if OpenClaw supports Docker-based isolation
    - Each agent can only access its own GSheet files (not other departments)
    - `.env` files have proper file permissions (600, owner only)
    - Firewall rules: only SSH (from known IPs) and HTTPS outbound
  - Test: attempt to use denied tool via agent → verify it's blocked
  - Document security posture for each VPS

  **Must NOT do**:
  - Do NOT open unnecessary ports
  - Do NOT give agents access to tools they don't need

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2C (with Tasks 23, 25, 26)
  - **Blocks**: Task 36 (production readiness)
  - **Blocked By**: Task 18

  **Acceptance Criteria**:

  ```
  Scenario: Denied tools are actually blocked
    Tool: Bash (ssh)
    Steps:
      1. Attempt to invoke browser tool via agent
      2. Assert: tool invocation fails with "denied" or "not allowed" message
    Expected Result: Tool restrictions enforced
    Evidence: Error message captured
  ```

  **Commit**: YES
  - Message: `security: harden tool restrictions and sandboxing on all VPS`
  - Files: updated openclaw.json configs

---

- [ ] 25. Git-Version All Agent Workspaces

  **What to do**:
  - For each VPS, ensure workspace is a Git clone of `zuma-openclaw-workspaces`
  - Set up automated pull mechanism: agents pull latest workspace on Gateway start
  - Verify each VPS can pull from Git repo (deploy key access)
  - Create initial commit with all current workspace files
  - Test rollback: break a SKILL.md, git revert, verify agent works again

  **Must NOT do**:
  - Do NOT give Layer 1 VPS write (push) access to Git — read-only for Layer 1
  - Do NOT commit .env or memory/ files

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2C
  - **Blocks**: Task 36
  - **Blocked By**: Tasks 7, 18

  **Acceptance Criteria**:

  ```
  Scenario: VPS workspace is Git-versioned and can pull
    Tool: Bash (ssh + git)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "git -C ~/workspace status"
      2. Assert: "On branch main" or similar (not "fatal: not a git repo")
      3. ssh openclaw-admin@<VPS_IP> "git -C ~/workspace pull"
      4. Assert: "Already up to date" or successful pull
    Expected Result: All VPS workspaces are Git-managed
    Evidence: git status + git pull output captured

  Scenario: Rollback works
    Tool: Bash (ssh + git)
    Steps:
      1. Break a SKILL.md file (write garbage)
      2. git revert HEAD
      3. Verify SKILL.md is restored
    Expected Result: Can recover from bad edits via Git
    Evidence: git revert output + restored file content
  ```

  **Commit**: YES
  - Message: `ops: verify git versioning on all VPS workspaces`

---

- [ ] 26. Implement Telegram Message Categorization

  **What to do**:
  - Update all agents' AGENTS.md to include message routing rules:
    - 🟢 Routine reports → department Logs group (low noise)
    - 🟡 Warnings (approaching threshold) → department Main group
    - 🔴 Critical alerts (threshold breached) → Main group + Alerts group
    - ❌ Failures → Main group + Alerts group
  - Configure cron `--announce` to use appropriate group based on result
  - Test: routine report goes to logs only, alert goes to main + alerts

  **Must NOT do**:
  - Do NOT send routine reports to the main group
  - Do NOT send critical alerts only to the logs group

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2C
  - **Blocks**: Task 36
  - **Blocked By**: Tasks 19, 23

  **Acceptance Criteria**:

  ```
  Scenario: Routine report goes to Logs group only
    Tool: Bash (curl to Telegram API)
    Steps:
      1. Trigger a normal (no-alert) cron run
      2. Check Logs group for message
      3. Assert: message present in Logs group
      4. Check Main group
      5. Assert: no routine message in Main group
    Expected Result: Message routing works correctly
    Evidence: Messages in correct groups verified
  ```

  **Commit**: YES
  - Message: `config: implement Telegram message categorization (routine vs alerts)`
  - Files: updated AGENTS.md files

---

### ═══ PHASE 3: LAYER 2 OVERSEERS (Week 5-8) ═══

---

- [ ] 27. Set Up Mac Mini M4 #1 (Overseer-OPS)

  **What to do**:
  - Mac Mini M4 (16GB RAM) — purchased and on-site
  - Install: macOS updates, then LOCK updates: System Preferences → Software Update → uncheck auto
  - Disable sleep: `sudo pmset -a disablesleep 1`
  - Install Homebrew, Node.js 20, Python 3.11+, OpenClaw, gog CLI
  - Set timezone to `Asia/Jakarta`
  - Configure OpenClaw for Layer 2:
    - Model: `claude-sonnet-4-20250514` (smarter model for oversight)
    - Heartbeat interval: 30 min
    - Active hours: 07:00-22:00 WIB
  - Connect to UPS ($30-50 backup battery) to prevent power-loss crashes
  - Set up as always-on machine (auto-login, auto-start OpenClaw on boot)

  **Must NOT do**:
  - Do NOT use Haiku for Layer 2 — needs Sonnet-level intelligence for review tasks
  - Do NOT leave macOS auto-updates enabled (causes unexpected restarts)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3A (with Task 28)
  - **Blocks**: Tasks 29, 30
  - **Blocked By**: Mac Mini purchase (external dependency)

  **Acceptance Criteria**:

  ```
  Scenario: Mac Mini is configured and OpenClaw running
    Tool: Bash (local or ssh)
    Steps:
      1. openclaw health --json
      2. Assert: healthy status
      3. pmset -g | grep disablesleep
      4. Assert: disablesleep = 1
      5. openclaw config show | grep model
      6. Assert: model is claude-sonnet or higher
    Expected Result: Mac Mini ready for Layer 2 oversight
    Evidence: Health check + config output captured
  ```

  **Commit**: YES
  - Message: `config(overseer-ops): set up Mac Mini M4 for OPS department oversight`
  - Files: `overseer-ops/AGENTS.md`, `overseer-ops/HEARTBEAT.md`

---

- [ ] 28. Set Up Mac Mini M4 #2 (Overseer-CEMES/FATAL)

  **What to do**:
  - Same as Task 27 but for CEMES and FATAL departments
  - This overseer monitors VPS-2 (CEMES) and VPS-3 (FATAL)
  - May host 2 overseer agents (one per department) on same Gateway

  **Recommended Agent Profile**: Same as Task 27

  **Parallelization**: Same as Task 27 (Wave 3A, parallel with Task 27)

  **Acceptance Criteria**: Same pattern as Task 27

  **Commit**: YES
  - Message: `config(overseer-cemes-fatal): set up Mac Mini M4 for CEMES+FATAL oversight`
  - Files: `overseer-cemes/AGENTS.md`, `overseer-cemes/HEARTBEAT.md`

---

- [ ] 29. SSH Key Infrastructure (Mac Minis → All VPS)

  **What to do**:
  - Generate SSH key pairs on each Mac Mini (ed25519)
  - Deploy public keys to ALL VPS `openclaw-admin` authorized_keys
  - Create restricted SSH user on each VPS: `openclaw-overseer` with limited permissions:
    - Can run: `openclaw health`, `openclaw cron`, `openclaw gateway`, `git pull`
    - Cannot: install packages, modify system files, access root
  - Test connectivity from each Mac Mini to each VPS
  - Document SSH connection map

  **Must NOT do**:
  - Do NOT use password authentication
  - Do NOT give overseers root access on VPS

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (depends on both Mac Minis)
  - **Blocks**: Tasks 30, 31, 35
  - **Blocked By**: Tasks 27, 28

  **Acceptance Criteria**:

  ```
  Scenario: Mac Mini can SSH to all VPS
    Tool: Bash (from Mac Mini)
    Steps:
      1. ssh -o ConnectTimeout=5 openclaw-overseer@<VPS_1_IP> "echo OK"
      2. Assert: "OK"
      3. Repeat for VPS-2 and VPS-3
    Expected Result: All SSH connections work
    Evidence: Connection outputs captured

  Scenario: Overseer SSH user is restricted
    Tool: Bash (ssh)
    Steps:
      1. ssh openclaw-overseer@<VPS_IP> "sudo apt update" 2>&1
      2. Assert: permission denied or not authorized
      3. ssh openclaw-overseer@<VPS_IP> "openclaw health --json"
      4. Assert: health check works (allowed command)
    Expected Result: Restricted user can only run OpenClaw commands
    Evidence: Permission denied + health check output captured
  ```

  **Commit**: NO (SSH infrastructure, no code files)

---

- [ ] 30. Build Overseer-OPS — HEARTBEAT.md + Review Workflow

  **What to do**:
  - Create `overseer-ops/AGENTS.md`:
    - Role: Review OPS Layer 1 agents' output, request revisions, send approval emails
    - Can SSH into VPS-1 for health checks, restarts, skills fixes
    - Monitors Notion task tracker for "Done by Agent" status
    - Reviews GSheet output by clicking Notion links
    - Max 2 revision attempts, then escalate to 🔴 ESCALATED
  - Create `overseer-ops/HEARTBEAT.md`:
    ```markdown
    ## Every 30 Minutes
    1. Check Notion "Needs Review" view — any tasks with status "Done by Agent"?
       - If YES: click Output Link, review GSheet data, check:
         - Is raw_data tab populated? (not empty)
         - Do summary metrics look reasonable? (FF% 0-100%, not #REF!)
         - Are any alerts correctly flagged?
       - If looks good → update Notion to "L2 Approved" → send approval email to PIC
       - If looks wrong → update Notion to "Revision Needed" → message Layer 1 in TG group
    2. Check Agent Health in Notion — any agents offline > 30 min?
       - If YES: SSH health check → restart if needed → update Notion
    3. Check for approval email replies — any PIC replied "Approve"?
       - If YES: update Notion to "✅✅ APPROVED"
    4. Check for escalated tasks > 48h without approval
       - If YES: send reminder to backup PIC
    ```
  - Configure heartbeat in openclaw.json: interval 30 min, active hours 07:00-22:00 WIB

  **Must NOT do**:
  - Do NOT let overseer modify GSheet data directly — only review
  - Do NOT skip the max-2-revision guardrail

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3B (with Tasks 31, 32)
  - **Blocks**: Tasks 33, 34
  - **Blocked By**: Task 29

  **References**:
  - **Documentation References**:
    - Draft section 3: HEARTBEAT.md behavior — runs in main session, HEARTBEAT_OK when nothing to do
    - Draft section 10: Full approval workflow — Do → Review → Approve
    - Oracle gap #3: Max 2 revisions then escalate
    - Oracle gap #6: 48h email timeout → escalate to backup PIC

  **Acceptance Criteria**:

  ```
  Scenario: HEARTBEAT.md causes review cycle
    Tool: Bash (from Mac Mini)
    Steps:
      1. Create a Notion task with status "Done by Agent" and output link to test GSheet
      2. Wait for next heartbeat cycle (max 30 min)
      3. Check Notion task status
      4. Assert: status changed to "L2 Approved" (if data looks good)
      5. Check PIC email inbox
      6. Assert: approval request email received
    Expected Result: Overseer reviews and processes completed tasks
    Evidence: Notion status change + email captured

  Scenario: Revision loop with max 2 attempts
    Tool: Bash (from Mac Mini)
    Steps:
      1. Create a Notion task with bad data (empty GSheet)
      2. Wait for heartbeat review
      3. Assert: status changed to "Revision Needed", Telegram message sent to Layer 1
      4. Simulate Layer 1 revision (still bad)
      5. Assert: 2nd revision requested
      6. Simulate 2nd bad revision
      7. Assert: status changed to "ESCALATED"
    Expected Result: Max 2 revisions enforced, then escalation
    Evidence: Notion status transitions + Telegram messages captured
  ```

  **Commit**: YES
  - Message: `feat(overseer): add OPS overseer — HEARTBEAT.md + review workflow`
  - Files: `overseer-ops/AGENTS.md`, `overseer-ops/HEARTBEAT.md`

---

- [ ] 31. Build Overseer-CEMES/FATAL — HEARTBEAT.md + Review Workflow

  **What to do**:
  - Same pattern as Task 30 but for CEMES and FATAL departments
  - Monitors VPS-2 (CEMES) and VPS-3 (FATAL) agents
  - May be 2 separate overseer agents on same Mac Mini Gateway

  **Recommended Agent Profile**: Same as Task 30

  **Parallelization**: Wave 3B (parallel with Tasks 30, 32)

  **Acceptance Criteria**: Same pattern as Task 30, adapted for CEMES/FATAL

  **Commit**: YES
  - Message: `feat(overseer): add CEMES/FATAL overseer — HEARTBEAT.md + review workflow`
  - Files: `overseer-cemes/AGENTS.md`, `overseer-cemes/HEARTBEAT.md`

---

- [ ] 32. Configure Email Approval Workflow via gog gmail

  **What to do**:
  - Install gog CLI on both Mac Minis (if not already)
  - Configure Gmail OAuth for overseers (same credentials, different machine)
  - Create email templates (in Indonesian):
    ```
    Subject: [Persetujuan Dibutuhkan] Laporan Stock Harian — {date}
    
    Halo {PIC_name},

    Laporan stock harian sudah selesai diproses oleh AI Agent.

    📊 Ringkasan:
    - FF%: {ff_percent}
    - FB%: {fb_percent}
    - Item Below Threshold: {alert_count}

    📎 Link GSheet: {gsheet_url}
    📋 Link Notion: {notion_url}

    Mohon balas email ini dengan "Approve" jika laporan sudah benar,
    atau balas dengan catatan revisi jika ada koreksi.

    Terima kasih,
    Zuma AI Overseer
    ```
  - Configure HEARTBEAT.md to:
    - Send approval emails via `gog gmail send`
    - Monitor inbox for replies via `gog gmail search --query "from:{PIC_email} subject:Persetujuan newer_than:1d"`
    - Parse reply: "Approve" → update Notion, other text → log as feedback
  - Set up 48h timeout: if no reply in 48h → escalate to backup PIC

  **Must NOT do**:
  - Do NOT send emails to all PICs at once — only to the relevant PIC for each task
  - Do NOT auto-approve if PIC doesn't reply (always escalate, never assume)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3B (with Tasks 30, 31)
  - **Blocks**: Task 34
  - **Blocked By**: Tasks 2 (OAuth), 30 or 31 (overseer agents exist)

  **References**:
  - **Documentation References**:
    - Draft section 10: Email approval workflow — full lifecycle
    - Oracle gap #6: 48h timeout escalation
  - **External References**:
    - gog gmail commands: `gog gmail send`, `gog gmail search`

  **Acceptance Criteria**:

  ```
  Scenario: Approval email sent and reply detected
    Tool: Bash (gog CLI from Mac Mini)
    Steps:
      1. gog gmail send --to wayan@zumagroup.com --subject "[Test] Persetujuan" --body "Test approval email"
      2. Assert: email sent successfully
      3. Wait for reply (or simulate reply)
      4. gog gmail search --query "from:wayan@zumagroup.com subject:Persetujuan newer_than:1d" --json
      5. Assert: reply found
      6. Assert: reply body contains "Approve" or revision text
    Expected Result: Email round-trip works
    Evidence: Sent email + search results captured
  ```

  **Commit**: YES
  - Message: `feat(email): configure approval email workflow with gog gmail`
  - Files: `shared/templates/approval-email.md`

---

- [ ] 33. Test Revision Loop: Break Layer 1 → Layer 2 Detects → Revises

  **What to do**:
  - Intentionally corrupt Layer 1 output:
    - Write bad data to stock GSheet (empty cells, wrong format)
    - Set Notion status to "Done by Agent"
  - Wait for Layer 2 heartbeat to detect the bad output
  - Verify: Layer 2 changes Notion to "Revision Needed" + sends TG message to Layer 1
  - Layer 1 reruns (triggered by TG message or manual cron run)
  - Verify: corrected output appears
  - Test escalation: make Layer 1 produce bad output twice → verify ESCALATED status

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3C (with Tasks 34, 35)
  - **Blocks**: Task 36
  - **Blocked By**: Tasks 30, 31

  **Acceptance Criteria**: Covered in Task 30's scenarios (revision loop test)

  **Commit**: NO (testing task)

---

- [ ] 34. Test Email Approval: Full Round-Trip

  **What to do**:
  - End-to-end test of approval workflow:
    1. Layer 1 completes task → Notion "Done by Agent"
    2. Layer 2 reviews → approves → Notion "L2 Approved" → sends email to PIC
    3. PIC receives email with summary + links
    4. PIC replies "Approve"
    5. Layer 2 detects reply → Notion "✅✅ APPROVED"
  - Test with actual PIC (Wayan or designated person)
  - Test timeout: don't reply for 48h (or simulate) → verify escalation

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3C (with Tasks 33, 35)
  - **Blocks**: Task 36
  - **Blocked By**: Tasks 32, 30 or 31

  **Acceptance Criteria**: Full approval lifecycle verified

  **Commit**: NO (testing task)

---

- [ ] 35. Test Self-Healing: Kill Layer 1 Gateway → Layer 2 Detects → SSH Restart

  **What to do**:
  - Intentionally stop OpenClaw Gateway on VPS-1: `systemctl stop openclaw-main`
  - Wait for Layer 2 heartbeat to detect offline agent (via Notion health check or Telegram silence)
  - Verify: Layer 2 SSHs into VPS-1, checks health, restarts Gateway
  - Verify: Gateway comes back online, cron jobs resume
  - Test rescue bot: kill main Gateway, verify rescue bot restarts it (before Layer 2 even notices)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3C (with Tasks 33, 34)
  - **Blocks**: Task 36
  - **Blocked By**: Tasks 29, 30 or 31

  **Acceptance Criteria**:

  ```
  Scenario: Layer 2 detects and restarts crashed Layer 1
    Tool: Bash (ssh from Mac Mini)
    Steps:
      1. ssh openclaw-admin@<VPS_IP> "systemctl stop openclaw-main"
      2. Wait for heartbeat cycle (max 30 min)
      3. Check Mac Mini overseer logs for detection
      4. Assert: overseer detected offline agent
      5. ssh openclaw-admin@<VPS_IP> "systemctl status openclaw-main"
      6. Assert: "active (running)" — overseer restarted it
    Expected Result: Automatic recovery from Layer 1 crash
    Evidence: Overseer logs + systemctl status captured
  ```

  **Commit**: NO (testing task)

---

- [ ] 36. Production Burn-In: 1 Week of Full Autonomous Operation

  **What to do**:
  - Let the entire system run autonomously for 1 full business week (5 days)
  - Monitor (but don't intervene):
    - All Layer 1 cron jobs execute daily
    - Layer 2 reviews and processes outputs
    - Approval emails sent and processed
    - No unexpected crashes or data errors
  - Keep a daily log:
    - Day 1-5: All jobs ran? Alerts triggered? Revisions needed? Emails sent? Crashes?
  - Acceptance: 5 days with < 2 unplanned manual interventions
  - After burn-in: system is PRODUCTION READY

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []
    - Writing category: documenting daily observations

  **Parallelization**:
  - **Can Run In Parallel**: NO (final gate)
  - **Blocks**: None (this is the final task)
  - **Blocked By**: Tasks 33, 34, 35 (all tests must pass)

  **Acceptance Criteria**:

  ```
  Scenario: 5-day autonomous operation log
    Tool: Bash (file check)
    Steps:
      1. cat validation/burn-in-log.md
      2. Assert: 5 daily entries exist
      3. Assert: each day has: jobs_ran, alerts, revisions, emails, crashes fields
      4. Assert: total unplanned_interventions < 2
    Expected Result: System operates autonomously for full business week
    Evidence: Burn-in log file captured
  ```

  **Commit**: YES
  - Message: `docs(validation): add production burn-in log — system validated`
  - Files: `validation/burn-in-log.md`

---

## Commit Strategy

| After Task | Message | Key Files | Verification |
|---|---|---|---|
| 6 | `docs(skills): add stock check SOP` | `sop-stock-check.md` | File exists, >200 words |
| 7 | `init: scaffold workspace repo` | All scaffold files | Correct directory structure |
| 8 | `config(vps-1): OpenClaw config` | `openclaw.json` | `openclaw health` passes |
| 11 | `feat(agent): Stock Agent workspace` | AGENTS.md, skills/ | Files valid, no secrets |
| 13 | `config(telegram): OPS group` | Updated config | Bot can post to group |
| 16 | `docs(validation): parallel run log` | `parallel-run-log.md` | 5 matching days |
| 18 | `config(vps-2,3): OpenClaw configs` | AGENTS.md, configs | Health checks pass |
| 20-22 | `feat(agent): department agents` | AGENTS.md, skills/ per dept | Pipelines work |
| 23 | `docs: master cron schedule` | `cron-schedule.md` | No conflicts |
| 24 | `security: harden all VPS` | Updated configs | Denied tools blocked |
| 26 | `config: Telegram categorization` | Updated AGENTS.md | Messages route correctly |
| 27-28 | `config(overseer): Mac Mini setup` | AGENTS.md, HEARTBEAT.md | Health checks pass |
| 30-31 | `feat(overseer): review workflow` | HEARTBEAT.md | Review cycle works |
| 32 | `feat(email): approval workflow` | Email templates | Round-trip works |
| 36 | `docs(validation): burn-in log` | `burn-in-log.md` | <2 interventions in 5 days |

---

## Success Criteria

### Phase 1 Success (Minimum Viable)
- [ ] Stock Agent runs daily at 8:30 WIB for 5 consecutive days
- [ ] Agent output matches human output (parallel run validation)
- [ ] Reports appear in Telegram OPS group
- [ ] Notion task tracker shows "Done" status with correct timestamps

### Phase 2 Success
- [ ] 3 VPS with 5-7 agents running across OPS, CEMES, FATAL departments
- [ ] All cron jobs staggered with no GSheet API quota issues
- [ ] Each department has its own Telegram group with categorized messages
- [ ] All workspaces Git-versioned with working pull mechanism

### Phase 3 Success
- [ ] Layer 2 reviews Layer 1 output via Notion + GSheet links
- [ ] Revision loop works (bad output → revision request → corrected output)
- [ ] Email approval workflow completes end-to-end
- [ ] Self-healing works (crashed Layer 1 → auto-restart via SSH)
- [ ] 5-day burn-in with <2 manual interventions

### Final Checklist
- [ ] All "Must Have" items present
- [ ] All "Must NOT Have" items absent
- [ ] Zero API keys in prompt-facing files
- [ ] All agents use isolated cron sessions
- [ ] All GSheet writes include metadata (agent name + timestamp)
- [ ] All VPS firewalls configured
- [ ] macOS auto-updates disabled on Mac Minis
- [ ] Sleep disabled on Mac Minis
- [ ] UPS connected to Mac Minis
