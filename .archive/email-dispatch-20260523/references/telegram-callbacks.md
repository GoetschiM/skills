# Telegram Inline Keyboard Callback Mechanism (dispatch_approval.py)

## Two-Bot Architecture (CRITICAL)

Hermes has TWO Telegram bot connections:

| Bot | ID | Token Location | Purpose |
|-----|----|----------------|---------|
| @Radislione_Hermes_bot | 8719158254 | Telethon session | Main Hermes chat — `send_message` tool, group chats |
| @Radislione_NovaBot | 8955190926 | `.env` → `TELEGRAM_BOT_TOKEN` | Bot API — inline keyboard dispatch approvals |

**Consequence**: Inline keyboard messages sent via the Bot API appear in @Radislione_NovaBot's DM with Michel, NOT in the Hermes chat. Michel cannot click those buttons from the Hermes chat.

**Mitigation**: The dispatch cron job polls @Radislione_NovaBot every 15 minutes for callbacks. For real-time interaction, prefer text-based approval commands (`approve` / `reject` / `ticket`) in the main Hermes chat.

## Callback Data Format (max 64 bytes)

| Prefix | Format | Meaning |
|--------|--------|---------|
| `a` | `a|{short_id}|{sender[:12]}` | Approve |
| `r` | `r|{short_id}|{sender[:12]}` | Reject |
| `i` | `i|{short_id}` | Info (DB link) |
| `t` | `t|{short_id}|{sender[:12]}` | Create GL Jira ticket |

- `short_id` = first 16 hex chars of Notion UUID (no dashes)
- Total callback_data string must be ≤ 64 bytes (Telegram API limit)

## Offset Management

File: `dispatch_cb_offset.txt`

```
getUpdates call → receive updates → save max(update_id) + 1 → next call starts from saved offset
```

Without offset tracking, `getUpdates` can:
- Return old callbacks that were already processed
- Skip new callbacks (if `offset` is set too high)
- Cause infinite loops of re-processing

## Callback Processing Flow

1. `poll_callbacks()` at start of each dispatch run
2. Load saved `offset` from file (0 if absent)
3. `GET /getUpdates?offset={offset}&allowed_updates=["callback_query"]`
4. Extract `callback_query` objects
5. `answerCallbackQuery(callback_query_id)` — acknowledge immediately (removes loading state)
6. Look up `page_id` from `short_id` via `dispatch_notion_idmap.json`
7. Update Notion DB: Status → Approved/Rejected, Action → Ticket if applicable
8. On success: send confirmation Telegram message
9. Save `max(update_ids) + 1` back to offset file

## Security Detection

Topics with these keywords get a custom button layout (📋 GL-Ticket as primary):

- `threat`, `detected`, `security`, `alert`, `warning`, `intrusion`
- `admin accessed`, `login attempt`, `brute force`, `malware`
- `vulnerability`, `breach`, `compromise`, `unauthorized`
- `suspend`, `suspicious`, `unusual`, `critical`, `attack`

The `is_security_alert()` function checks both `subject` and `snippet` for these.
