# Telegram Bot Group/Channel Setup

How to make a Telegram bot (@Radislione_Hermes_bot, @Radislione_NovaBot, etc.) work in groups and channels. Covers what the user must do vs what the agent configures in Hermes.

## Key Concepts

| Type | Bot can read messages? | Admin required? |
|------|----------------------|-----------------|
| **DM** (direct message) | ✅ Always | No |
| **Group** (supergroup) | ✅ If privacy mode off | No (but admin for full features) |
| **Group** (with privacy mode on) | ✅ Only `/commands` and @mentions | No |
| **Channel** (broadcast) | ❌ Never without admin | ✅ YES, bot must be admin |
| **Channel** (as admin) | ✅ Can read all messages | Yes |

## Step-by-Step: Bot in Channel/Group

### 1. User adds bot to channel/group
- Channel: Settings → Administrators → Add admin → @bot_username
- Group: Just add member normally; privacy mode controls what bot sees

### 2. Agent verifies bot admin status

Use Michel's Telethon session to check:

```python
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

client = TelegramClient(SESSION, API_ID, API_HASH)
await client.start()

channel = await client.get_entity(CHANNEL_ID)  # e.g. -1002300386092
bot = await client.get_entity("Radislione_Hermes_bot")

participant = await client(GetParticipantRequest(channel, bot))
p = participant.participant
is_admin = isinstance(p, (ChannelParticipantAdmin, ChannelParticipantCreator))
```

### 3. Agent updates Hermes config.yaml

Set these values in the `telegram:` section of `/root/.hermes/config.yaml` (ALL three are required):

```yaml
telegram:
  allowed_channels: '-1002300386092'    # or comma-separated: '-1002300386092,-1001234567890'
  allow_from:
    - 322663922                          # Michel's user ID
    - -1002300386092                     # channel ID
  allowed_chats:
    - '-1002300386092'                   # channel ID (wrapped in quotes because negative)
```

Config takes effect immediately — no restart needed. The Hermes gateway re-reads config.yaml on each incoming message.

⚠️ **Don't omit `allow_from` or `allowed_chats`.** The bot needs all three to properly receive and respond in a channel.

### 4. Test

Send a message @-mentioning the bot in the channel. The bot should respond.

For channels specifically: even with admin, some bots need their Telegram webhook re-set after joining a new chat. Test and if it fails, verify the webhook is set.

## Hermes Config Values (Goetschi Labs)

| Key | Current value | Meaning |
|-----|--------------|---------|
| `home_channel.chat_id` | `322663922` | Michel's DM (primary delivery) |
| `telegram.allowed_channels` | `-1002300386092` | Goetschi Lab's channel |
| `telegram.allow_from` | `[322663922, -1002300386092]` | Approved senders |
| `telegram.allowed_chats` | `['-1002300386092']` | Chats bot monitors |
| `telegram.enabled` | `true` | Telegram gateway on |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Bot sees DMs but not group/channel msgs | `allowed_channels` not set in config.yaml | Agent: add chat_id to config |
| Bot sees DMs but not group/channel msgs | `allow_from` and/or `allowed_chats` missing | Agent: add all three fields (allowed_channels, allow_from, allowed_chats) |
| Bot doesn't respond in channel despite config | Bot not admin in channel | User: add bot as admin |
| Bot responds but says "interrupting task" | Bot was in another task, first response is interrupt | Wait for actual response on 2nd message |
| Multiple bots respond to one message | All bots in same channel with overlapping config | Consider removing extra bots or narrowing scope |
