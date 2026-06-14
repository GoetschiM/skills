# Delivery Targets for Cron Alerts

The `deliver` parameter in `cronjob` specifies where alert messages are sent. For `no_agent=True` cronjobs, the script's stdout is delivered verbatim to the configured target.

## Finding Available Targets

Use `send_message action=list` — returns all available targets:

```
Telegram:
  telegram:Michel G (dm)
  telegram:Goetschi Lab's (group)
```

## Setting Delivery in Cronjob

| Action | Command Pattern |
|--------|----------------|
| Create with target | `cronjob action=create deliver="telegram:Goetschi Lab's (group)"` |
| Update target | `cronjob action=update job_id=abc123 deliver="telegram:..."` |
| Fan out | `cronjob action=create deliver="all"` |

## Delivery Behavior (no_agent=True)

- **Empty stdout** → silent (nothing sent)
- **Non-empty stdout** → verbatim alert message
- **Non-zero exit + no output** → error notification

## Calling Pattern

```
1. send_message action=list              # find targets
2. cronjob action=create ... deliver=X  # set target
```
