# Google Calendar — Cron Event Patterns

## Calendar ID
`5f1b8749aab8428064bae6888bff9aa3e43de14191aa3382d068ec868ea742a4@group.calendar.google.com`
(Goetschi Lab's Calendar — where all HERMES cron events live)

## Auth
Token: `/root/.hermes/google_token.json`
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file('/root/.hermes/google_token.json')
service = build('calendar', 'v3', credentials=creds)
```

## Common operations

### List recurring events
```python
events_result = service.events().list(
    calendarId=CAL_ID,
    timeMin="2026-05-01T00:00:00Z",
    timeMax="2026-07-01T23:59:59Z",
    singleEvents=False,  # Returns recurring event master copies, not individual instances
    maxResults=250
).execute()
```

### Create recurring event
```python
event = {
    'summary': 'HERMES: Cron Name',
    'start': {'dateTime': '2026-05-22T06:55:00+02:00', 'timeZone': 'Europe/Zurich'},
    'end': {'dateTime': '2026-05-22T07:05:00+02:00', 'timeZone': 'Europe/Zurich'},
    'recurrence': ['RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;INTERVAL=1'],
    'description': 'Optional description',
    'transparency': 'transparent'  # Don't show as "busy"
}
service.events().insert(calendarId=CAL_ID, body=event).execute()
```

### Delete event
```python
service.events().delete(calendarId=CAL_ID, eventId=event_id).execute()
```

## RRULE reference

| Schedule | RRULE |
|----------|-------|
| Daily | `FREQ=DAILY;INTERVAL=1` |
| Every 2 days | `FREQ=DAILY;INTERVAL=2` |
| Weekdays | `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;INTERVAL=1` |
| Weekdays (no INTERVAL) | `FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,TU,WE,TH,FR` |
| Sundays | `FREQ=WEEKLY;BYDAY=SU;INTERVAL=1` |
| Multiple per day (weekdays, with expiry) | `FREQ=WEEKLY;UNTIL=20270601T000000Z;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8,12,16;BYMINUTE=0` |

## CH timezone conversion

| CH Local Time | UTC (summer CEST = UTC+2) | UTC (winter CET = UTC+1) |
|---------------|---------------------------|---------------------------|
| 06:00 | 04:00 | 05:00 |
| 06:30 | 04:30 | 05:30 |
| 06:55 | 04:55 | 05:55 |
| 08:00 | 06:00 | 07:00 |
| 16:00 | 14:00 | 15:00 |
| 19:55 | 17:55 | 18:55 |
| 20:00 | 18:00 | 19:00 |

**Use `Europe/Zurich` as timezone!** The Calendar API handles DST automatically when you specify the timezone. Just write CH local time in the `dateTime` field and set `timeZone: 'Europe/Zurich'`.

## Pitfalls

1. **Can't update recurring event's RRULE** — must delete old event + create new one. The Google Calendar API does not allow patching the `recurrence` field on existing events.
2. **Events persist in query after delete** — after calling `events().delete()`, the event may still appear in the next `events().list()` response for some seconds (consistency delay). Always re-fetch the list.
3. **Summary matching**: Calendar stores events with their exact summary string. Matching by substring is safer than exact match since API can add IDs.
4. **Duplicate detection**: Before creating, list all events and check if summary already exists with matching RRULE. Otherwise you'll get duplicates.
5. **HERMES: prefix required**: All HERMES cron calendar events MUST have `HERMES: ` prefix in the summary for discoverability.
