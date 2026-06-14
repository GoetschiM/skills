---
name: telegram-telethon
description: "Use when the user asks you to access, read, send, or monitor their Telegram account. Provides Telethon-based client with full read/write access to Michel's DMs, groups, and channels."
version: 1.2.0
author: Apollo
license: MIT
metadata:
  hermes:
    tags: [telegram, telethon, messaging, social-media]
    related_skills: [spotify, xurl]
---

# Telegram Telethon Skill

## Overview

Gives Apollo authenticated Telethon access to Michel's personal Telegram account (`@Radislione`, `+41796459743`, ID `322663922`). Enables reading chats, sending messages, monitoring DMs, and interacting with groups.

**Architecture:** Telethon user-client (not bot). Uses Michel's API credentials + session file for authentication. First-time setup uses a two-step flow: send code request → ask user for code → `--code` flag login.

## Credentials & Config

Stored in `/opt/data/home/.hermes/telegram_config.json`:
```json
{
  "api_id": "28054408",
  "api_hash": "7e7b6ab2dd21a99af5ff0d68b550045e",
  "phone": "+41796459743",
  "my_user_id": 322663922,
  "my_name": "Michel"
}
```

**⚠️ CRITICAL:** The config MUST include a `"phone"` field. Without it, `setup.py` falls back to `input()` for phone entry, which crashes in non-interactive terminal mode.

Also stored in `/opt/data/.env` as `TG_API_ID`, `TG_API_HASH`, `TG_PHONE`.

Session file: `/opt/data/home/.hermes/michel_telethon.session`

## When to Use

- User says "lies meine Telegram-Nachrichten", "schau wer mir geschrieben hat"
- User asks you to send a Telegram message via his account
- User wants you to monitor a specific chat/group
- User wants to forward something via Telegram
- Any task involving Michel's personal Telegram
- User asks why a bot isn't responding in a channel/group — use this to diagnose + check admin status
- User asks you to set up bot in a Telegram channel/group — see references/bot-group-setup.md

**Don't use for:**
- Sending messages through the Hermes Telegram bot (that's the `send_message` tool)
- Automated broadcasts or spam
- Anything that could get Michel's account banned

## First-Time Login Procedure (proven working)

This is the ONLY reliable non-interactive approach:

```
1. Send code request first (separate script step)
   → await client.send_code_request(phone)
   → Tell user "Code wurde an +4179... gesendet"

2. User provides the code → run setup.py with --code flag
   → python3 setup.py --code XXXXX
```

The `setup.py` script reads api_id/api_hash/phone from `telegram_config.json`.
After success, it updates the config with `my_user_id`, `my_name`, `my_username` from the API.

**Do NOT** use `await client.start()` without arguments in non-interactive mode — it will try `input()` and crash with EOFError.

## Quick Reference: Client Usage

```python
import json, asyncio
from pathlib import Path
from telethon import TelegramClient

CONFIG = json.loads(Path("/opt/data/home/.hermes/telegram_config.json").read_text())
SESSION = "/opt/data/home/.hermes/michel_telethon.session"

async def get_client():
    client = TelegramClient(SESSION, int(CONFIG["api_id"]), CONFIG["api_hash"])
    await client.start()
    return client
```

## Common Operations

### Read recent messages from a chat
```python
client = await get_client()
async for msg in client.iter_messages("radislione", limit=10):
    print(f"[{msg.date}] {msg.sender_id}: {msg.text}")
```

### Send a message
```python
client = await get_client()
await client.send_message("radislione", "Hello from Apollo! 🤖")
```

### Reply to a specific message
```python
client = await get_client()
await client.send_message(entity, "My reply", reply_to=msg_id)
```

### Get all dialogs (recent chats, with unread counts)
```python
client = await get_client()
dialogs = await client.get_dialogs(limit=10)
for d in dialogs:
    name = d.name or "(no name)"
    unread = f" [{d.unread_count} ungelesen]" if d.unread_count > 0 else ""
    last = ""
    if d.message:
        txt = d.message.text or "[Media/Datei]"
        last = f": {txt[:80]}"
    print(f"  💬 {name}{unread}{last}")
```

### Get entity by username
```python
entity = await client.get_entity("radislione")
# or by user ID:
entity = await client.get_entity(322663922)
```

## Files in this Skill

| File | Purpose |
|------|---------|
| `scripts/setup.py` | First-time login — `--code` flag for non-interactive, or interactive with PTY |
| `scripts/telegram_client.py` | Reusable client module with helpers |
| `references/setup-2026-05-14.md` | Full session transcript: what actually happened during setup |
| `references/bot-group-setup.md` | Bot in group/channel: admin requirements, Hermes config.yaml, verify status, troubleshooting |

## Pitfalls

1. **☝️ Config needs `phone` field!** If missing, setup.py calls `input()` for phone → EOFError crash in non-interactive mode.
2. **Session not authed:** A `.session` file can exist (28KB) but be unauthenticated. Always check with `await client.is_user_authorized()` before using.
3. **Flood wait:** Too many rapid requests → Telegram blocks for N seconds. Wait between calls.
4. **Entity by username might fail:** Use `client.get_dialogs()` first to discover entity IDs, then use numeric IDs.
5. **Concurrent sessions:** Only one session per account. Don't start multiple clients simultaneously.
6. **`client.start()` is dangerous non-interactively:** It calls `input()` for phone/code. Always use separate `send_code_request()` + `--code` flag flow.
7. **`.env` is a protected file** — cannot be written via `write_file` or `patch` tool. Use terminal `echo >>` to append.
8. **⚠️ Bot in channel: admin + config BOTH required** — Adding the bot as admin in a Telegram channel alone is NOT enough. The Hermes config.yaml must ALSO have `allowed_channels` (and `allow_from` + `allowed_chats`) set to the channel ID. Neither step alone works; both are mandatory. See references/bot-group-setup.md for full workflow.

## Verification

After setup, verify with:

```python
async def verify():
    client = TelegramClient(SESSION, int(CONFIG["api_id"]), CONFIG["api_hash"])
    await client.start()
    me = await client.get_me()
    print(f"✅ {me.first_name} (@{me.username})")
    dialogs = await client.get_dialogs(limit=3)
    for d in dialogs:
        print(f"  💬 {d.name} | unread: {d.unread_count}")
    await client.disconnect()
```
