# OpenClaw OPS & R&D

> Three AI agents run Zuma Indonesia's operations while you sleep.

```
           ✨ Iris
          Coordinator
        reviews everything
        dispatches tasks
        escalates problems
              |
     +--------+--------+
     |                  |
  🏔️ Atlas          🎯 Apollo
  OPS Worker        R&D Worker
  stock, warehouse  products, QC
  logistics         materials
```

## What is this?

Zuma Indonesia makes shoes. ~1,400 SKUs, multiple warehouses, daily stock movements.

Three AI agents — themed after Greek gods — handle the repetitive data work:

**Iris ✨** is the coordinator. She doesn't do tasks herself. She reviews Atlas and Apollo's output, catches mistakes, and escalates to humans when something's wrong. Named after the goddess who carried messages between gods and mortals — because that's literally her job.

**Atlas 🏔️** is the OPS muscle. Every morning he pulls fresh data from the ERP, dumps it into Google Sheets, lets the formulas crunch, reads the results, and emails the merchandiser: *"These 47 articles have less than 3 months of stock. Here's what to order."* Named after the Titan who carried the world — because he carries all the inventory data.

**Apollo 🎯** handles R&D. Product timelines, QC reports, material sourcing status. He tracks what's late, what's over budget, and who hasn't confirmed. Named after the god of precision — because if a defect rate goes from 2% to 4%, that's a crisis, not a rounding error.

## How much does it cost?

~$56/month total. $49 LLM + $7 VPS.

| Model | $/1M input | $/1M output | Who uses it |
|-------|-----------|------------|-------------|
| Claude Sonnet 4.5 | $3.00 | $15.00 | Iris (needs intelligence for reviews) |
| Kimi K2.5 | $0.60 | $2.50 | Atlas & Apollo (cheap, good for data tasks) |
| DeepSeek V3.2 | $0.13 | $0.40 | Fallback (ultra-cheap safety net) |
| Gemini Flash-Lite | $0.10 | $0.40 | Heartbeats only (alive pings) |

If all three agents ran on Sonnet, it'd be ~$180/month. The trick: workers don't need expensive models for repetitive data moves.

## The five rules

1. **Agents are data movers, not calculators.** They pull raw data, paste it into Google Sheets. GSheet formulas do all the math. This is intentional — formulas are auditable, agents aren't.

2. **All communication in Bahasa Indonesia.** Reports go to department PICs (Person In Charge), not to the developer. The merchandiser doesn't care about your API calls.

3. **Max 2 revision attempts.** If Iris asks Atlas to redo something twice and it's still wrong, she escalates to Wayan. No infinite loops.

4. **No browsers.** VPS has 2 CPU cores. Headless Chrome would eat it alive. Everything is CLI: `gog` for Google Workspace, `curl` for APIs, Notion API for task tracking.

5. **Sequential, not parallel.** 2 cores means one thing at a time. Atlas runs at 8:30 WIB, Apollo at 8:45. Simple.

## Runs on

| What | Where |
|------|-------|
| VPS | Hostinger KVM 2 — 2 vCPU, 8GB RAM, 100GB SSD, Singapore |
| Platform | [OpenClaw](https://docs.openclaw.ai/) v2026.1.30 |
| OS | Ubuntu 24.04 |
| Task tracking | Notion Kanban |
| Communication | Telegram (bot per agent) |
| Data engine | Google Sheets (formulas do the math) |
| Email | Gmail via gog CLI |
| ERP | Accurate Online API |

## File structure

```
openclaw-ops-rnd/
├── README.md                          # You are here
├── .gitignore
├── config/
│   └── openclaw.json.example          # Sanitized config (no real keys)
├── workspace-iris/                    # Iris ✨ — Coordinator
│   ├── IDENTITY.md                    # Name, creature, vibe, emoji
│   ├── SOUL.md                        # Personality, principles
│   ├── USER.md                        # Who she serves
│   ├── AGENTS.md                      # Job description & rules
│   └── MEMORY.md                      # Knowledge base
├── workspace-ops/                     # Atlas 🏔️ — OPS Worker
│   ├── IDENTITY.md / SOUL.md / USER.md / AGENTS.md
└── workspace-rnd/                     # Apollo 🎯 — R&D Worker
    ├── IDENTITY.md / SOUL.md / USER.md / AGENTS.md
```

On the VPS (`/root/.openclaw/`), there's also:
- `openclaw.json` — live config with real API keys
- `.env` — credentials (NEVER in git)
- `agents/*/agent/auth-profiles.json` — per-agent LLM auth

## Integrations

| Tool | Purpose | Status |
|------|---------|--------|
| Notion | Kanban task management | ✅ Connected |
| GitHub | Config backup | ✅ Working |
| Telegram | Agent ↔ human communication | Bot created, routing pending |
| Google Sheets (gog) | Data storage & formula engine | CLI installed, OAuth pending |
| Gmail (gog) | Email reports to PICs | CLI installed, OAuth pending |
| Accurate Online | ERP data source | Credentials pending |

## Roadmap

| Phase | What | Status |
|-------|------|--------|
| **1** | Atlas daily stock analysis → email insight to merchandiser | In Progress |
| **2** | Apollo R&D reports + expand OPS tasks | Planned |
| **3** | Layer 2 oversight agent on Mac Mini M4 | Future |
| **4** | Jarvis — C-level assistant | Future |

## Quick start

```bash
# SSH into VPS
ssh root@76.13.194.103

# Talk to agents
openclaw tui --session agent:main:main    # Iris ✨
openclaw tui --session agent:ops:main     # Atlas 🏔️
openclaw tui --session agent:rnd:main     # Apollo 🎯

# Check status
openclaw models status
openclaw skills list
```

## Security

No secrets in this repo. All API keys, tokens, and passwords live in `.env` files on the VPS (gitignored). Auth profiles are stored in `~/.openclaw/agents/<id>/agent/auth-profiles.json` (not committed).

---

**Zuma Indonesia** — Indonesian footwear manufacturer. Built with [OpenClaw](https://docs.openclaw.ai/).
