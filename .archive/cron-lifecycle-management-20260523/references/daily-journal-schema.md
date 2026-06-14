# 🌅 Daily Journal — Notion DB Schema (22.05.2026)

Replaced the old Morgen/Abend Briefing Calls (deleted 22.05.). Hermes writes two entries per day into a shared Notion DB that all agents (Apollo, Hermes, NOVA) use.

## DB Info

- **Name:** 🌅Tägliches Journal
- **DB ID:** `36881c83f6d981429139ff70a8410bba`
- **DS ID:** `36881c83-f6d9-8153-9e16-000b81fb4dd1`
- **URL:** https://www.notion.so/36881c83f6d981429139ff70a8410bba

## Properties

| Field | Type | Description |
|-------|------|-------------|
| Titel | title | "DD.MM.YYYY – Hermes Morgen-Plan" or "DD.MM.YYYY – Hermes Abend-Recap" |
| Wer | select | Hermes, Apollo, Nova |
| Datum | date | YYYY-MM-DD |
| Status | status | Nicht begonnen, In Arbeit, Abgeschlossen |
| Gelerntes | rich_text | Morning: context/starting knowledge. Evening: what was newly learned |
| Rückschlüsse | rich_text | Morning: plans/steps. Evening: conclusions + what worked |
| Erfolge | rich_text | Morning: goals for the day. Evening: ✅ achievements |
| Verbesserungen | rich_text | Morning: what to watch for. Evening: 🔧 what to improve next time |
| Tags | multi_select | Apollo, NOVA, Infrastruktur, Trading, Kommunikation, Entwicklung |

## Cron Schedule

| Cron | Time (CH) | Action |
|------|-----------|--------|
| Hermes Journal Morgen | 06:30 Mo-Fr | Create entry for today with plans/goals. Check Jira tickets first. |
| Hermes Journal Abend | 19:00 Mo-Fr | Find today's entry and update with recap. Check session_search + Jira. |

## Style Rules

- **Sehr usfüehrlich und detailliert** — Michel wants rich, thorough entries, not bullet-point summaries
- **Morning:** Check Jira for open tickets, scan current tasks, write concrete plans per ticket/topic
- **Evening:** Check session_search for today's work, check Jira ticket status, write what was learned/fixed/improved
- **Tags:** Select relevant tags based on today's work topics
- **Status:** Morning = "Nicht begonnen" or "In Arbeit". Evening = "Abgeschlossen"
- **Language:** Hochdeutsch for all rich_text fields (Convention: all non-chat content in Hochdeutsch)
