# OpenClaw OPS & R&D - Zuma Indonesia

Hierarchical AI agent system for **Zuma Indonesia** (footwear company). Three Greek god-themed agents handle Operations and R&D department automation via cron jobs, Notion Kanban, and Telegram.

All agent communication is in **Bahasa Indonesia**.

## Architecture

```
+-----------------------------------------------------------+
|                   VPS Hostinger KVM 2                      |
|              2 vCPU | 8GB RAM | 100GB SSD                  |
|                  Singapore Region                          |
+-----------------------------------------------------------+
|                                                            |
|   +------------------------------------------------+      |
|   |       Athena - Lead Coordinator                 |      |
|   |       Claude Sonnet 4.5 (primary)               |      |
|   |       Role: PM / Reviewer                       |      |
|   |       Reviews, coordinates, escalates           |      |
|   +-------------------+-------------------+--------+      |
|                       |                   |                |
|           +-----------v-----+  +----------v----------+    |
|           | Atlas            |  | Apollo               |    |
|           | OPS Worker       |  | R&D Worker           |    |
|           | Kimi K2.5        |  | Kimi K2.5            |    |
|           |                  |  |                      |    |
|           | Stock & Inventory|  | Product Development  |    |
|           | Warehouse        |  | QC & Quality         |    |
|           | Logistics        |  | Material Sourcing    |    |
|           +------------------+  +----------------------+    |
|                                                            |
+------------------------------------------------------------+
```

## Model Hierarchy & Fallbacks

Cost-optimized multi-provider setup with automatic failover:

| Agent | Primary | Fallback 1 | Fallback 2 | Heartbeat |
|-------|---------|------------|------------|-----------|
| **Athena** (PM) | `anthropic/claude-sonnet-4-5` | `kimi-coding/k2p5` | `openrouter/deepseek/deepseek-chat` | `gemini-2.5-flash-lite` |
| **Atlas** (OPS) | `kimi-coding/k2p5` | `openrouter/deepseek/deepseek-chat` | `anthropic/claude-sonnet-4-5` | `gemini-2.5-flash-lite` |
| **Apollo** (R&D) | `kimi-coding/k2p5` | `openrouter/deepseek/deepseek-chat` | `anthropic/claude-sonnet-4-5` | `gemini-2.5-flash-lite` |

**Cost breakdown (per 1M tokens):**

| Model | Input | Output | Used For |
|-------|-------|--------|----------|
| Claude Sonnet 4.5 | $3.00 | $15.00 | Athena primary - complex reasoning, reviews |
| Kimi K2.5 | $0.60 | $2.50 | Worker primary - data processing, tool calls |
| DeepSeek V3.2 | $0.13 | $0.40 | Fallback - ultra cheap safety net |
| Gemini Flash-Lite | $0.10 | $0.40 | Heartbeats only - alive pings |

**Estimated monthly cost: ~$49** (vs ~$180 if all agents used Sonnet)

## Agents

### Athena - Lead Coordinator

- **Role:** Project Manager. Reviews Atlas & Apollo output. Does NOT do tasks herself.
- **Manages:** Cron job scheduling via Notion Kanban
- **Escalation:** Fixes errors or escalates to Wayan via Telegram
- **Model:** Sonnet 4.5 (needs intelligence for review & coordination)

### Atlas - OPS Worker

- **Department:** Stock & Inventory, Warehouse, Logistics
- **Key Task:** Daily stock depth analysis -> email insights to Merchandiser
- **Rule:** DATA MOVER only. Pulls raw data -> pastes to GSheet -> formulas calculate -> reads results -> sends report
- **Model:** Kimi K2.5 (cheap, capable for repetitive data tasks)

### Apollo - R&D Worker

- **Department:** Product Development, Quality Control, Material Sourcing
- **Key Task:** Track product timelines, QC reports, material sourcing status
- **Rule:** Same DATA MOVER pattern as Atlas
- **Model:** Kimi K2.5

## File Structure

```
openclaw-ops-rnd/
|-- README.md
|-- .gitignore
|-- config/
|   |-- openclaw.json.example      # Sanitized config (no real keys)
|   |-- .env.template              # Credential template
|-- workspace-athena/              # Athena workspace files
|   |-- AGENTS.md                  # Job description & rules
|   |-- IDENTITY.md                # Name, creature, vibe, emoji
|   |-- SOUL.md                    # Personality, principles, boundaries
|   |-- USER.md                    # Who she serves, PIC contacts
|   |-- MEMORY.md                  # Knowledge base & decision log
|-- workspace-ops/                 # Atlas workspace files
|   |-- AGENTS.md / IDENTITY.md / SOUL.md / USER.md
|-- workspace-rnd/                 # Apollo workspace files
    |-- AGENTS.md / IDENTITY.md / SOUL.md / USER.md
```

**On VPS** (`/root/.openclaw/`):

```
|-- openclaw.json                  # Live config (with real keys)
|-- .env                           # Shared credentials (NEVER in git)
|-- .env.template                  # Credential reference
|-- agents/
|   |-- main/agent/                # Athena auth & sessions
|   |-- ops/agent/                 # Atlas auth & sessions
|   |-- rnd/agent/                 # Apollo auth & sessions
|-- workspace/                     # Athena live workspace
|-- workspace-ops/                 # Atlas live workspace
|-- workspace-rnd/                 # Apollo live workspace
```

## Setup

### Prerequisites

- VPS with 4GB+ RAM (we use Hostinger KVM 2 - 8GB)
- [OpenClaw](https://docs.openclaw.ai/) installed
- API keys: Anthropic, Kimi (Moonshot AI), OpenRouter

### Quick Start

```bash
# 1. Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw onboard

# 2. Add worker agents
openclaw agents add ops
openclaw agents add rnd

# 3. Copy workspace files from this repo
cp workspace-athena/* /root/.openclaw/workspace/
cp workspace-ops/* /root/.openclaw/workspace-ops/
cp workspace-rnd/* /root/.openclaw/workspace-rnd/

# 4. Configure (edit with your real API keys)
cp config/openclaw.json.example /root/.openclaw/openclaw.json

# 5. Add auth profiles
openclaw models auth paste-token --provider anthropic
openclaw models auth paste-token --provider openrouter
openclaw models auth paste-token --provider kimi-coding

# 6. Set up credentials
cp config/.env.template /root/.openclaw/.env
nano /root/.openclaw/.env   # Fill in real values

# 7. Start
openclaw gateway run

# 8. Talk to agents
openclaw tui --session agent:main:main    # Athena
openclaw tui --session agent:ops:main     # Atlas
openclaw tui --session agent:rnd:main     # Apollo
```

## Security

- **No secrets in this repo.** All API keys, tokens, and passwords live in `.env` files (gitignored).
- **Auth profiles** stored in `~/.openclaw/agents/<id>/agent/auth-profiles.json` (not committed).
- **`.gitignore`** blocks: `.env`, `auth-profiles.json`, `*.pem`, `*.key`, `credentials.json`

## Tools & Integrations

| Tool | Purpose | Status |
|------|---------|--------|
| **Notion** | Kanban task management for cron jobs | Pending |
| **Telegram** | Agent communication & escalation | Bot created, routing pending |
| **Google Sheets** (gog CLI) | Data storage & formula engine | Pending |
| **Gmail** (gog CLI) | Email reports to PICs | Pending |
| **Accurate Online API** | ERP data source (stock, sales, products) | Pending |

## Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **1** | Atlas Control Stock PoC (daily stock analysis to email) | In Progress |
| **2** | Apollo R&D reports + more OPS tasks | Planned |
| **3** | Layer 2 oversight on Mac Mini M4 | Future |
| **4** | Jarvis C-level assistant | Future |

## Company

**Zuma Indonesia** - Indonesian footwear manufacturer. ~1,397 SKUs across multiple warehouses. ERP: Accurate Online.

---

*Built with [OpenClaw](https://docs.openclaw.ai/) v2026.1.30*