# MEMORY.md — Knowledge Base Iris ✨

## Fakta Penting

### Perusahaan
- Zuma Indonesia — perusahaan sepatu
- ~1,397 SKU aktif
- ERP: Accurate Online
- Kantor pusat timezone: WIB (UTC+7)

### Infrastruktur
- VPS: Hostinger KVM 2 (2 vCPU, 8GB RAM, 100GB SSD, Singapore)
- OS: Ubuntu 24.04
- OpenClaw: v2026.1.30

### Agent Fleet
- Iris ✨ (main) — Koordinator, Claude Sonnet primary
- Atlas 🏔️ (ops) — OPS worker, Kimi K2.5 primary
- Apollo 🎯 (rnd) — R&D worker, Kimi K2.5 primary

### Tools Aktif
- GitHub CLI (gh) — repo management
- Google Workspace CLI (gog) — Sheets, Gmail, Drive (OAuth pending)
- Notion API — task management (connected)
- Telegram Bot — communication (routing pending)

### Data Sources
- Accurate Online API — ERP (credentials pending)
- Google Sheets — Control Stock workbook (ID: 1qInTrRUOUi2983vefS8doS5Pt3jC2yftQAG99yYlVOE)

## Keputusan yang Sudah Dibuat

1. Agent komunikasi dalam Bahasa Indonesia, BUKAN English
2. Laporan dialamatkan ke PIC departemen, BUKAN ke Wayan
3. GSheet formulas yang menghitung — agent cuma data mover
4. Notion Kanban untuk task tracking (bukan HEARTBEAT.md)
5. Max 2 revisi per task, setelah itu eskalasi
6. Sequential processing preferred (VPS cuma 2 CPU cores)
7. Emoji: Iris ✨, Atlas 🏔️, Apollo 🎯
