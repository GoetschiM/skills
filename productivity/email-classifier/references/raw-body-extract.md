# Raw MIME Body Extraction (Gmail)

**Wann nötig:** Wenn `gmail get <id>` en leere Body zruggit (`body: ""`), z.B. bi:
- UniFi Security-Mails (Threat Detected, Admin Accessed)
- System-Notification-Mails mit dynamischem Content
- HTML-only Mails wo vom API nid parsed werde

## Python Snippet (execute_code tauglich)

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email import policy
from email.parser import BytesParser
import base64

TOKEN_PATH = '/root/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
if not creds.valid:
    creds.refresh(Request())
service = build('gmail', 'v1', credentials=creds)

msg = service.users().messages().get(
    userId='me', id='MSG_ID', format='raw'
).execute()
raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
mime_msg = BytesParser(policy=policy.default).parsebytes(raw)

body = ''
if mime_msg.is_multipart():
    for part in mime_msg.walk():
        if part.get_content_type().startswith('text/plain'):
            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
            break
        elif not body and part.get_content_type().startswith('text/html'):
            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
else:
    body = mime_msg.get_payload(decode=True).decode('utf-8', errors='replace')
```

## Terminal-Version

```bash
python3 -c "
import json, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email import policy
from email.parser import BytesParser

TOKEN_PATH = '/root/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
if not creds.valid:
    creds.refresh(Request())
service = build('gmail', 'v1', credentials=creds)
msg = service.users().messages().get(userId='me', id='MSG_ID', format='raw').execute()
raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
mime_msg = BytesParser(policy=policy.default).parsebytes(raw)
body = ''
if mime_msg.is_multipart():
    for part in mime_msg.walk():
        if part.get_content_type().startswith('text/plain'):
            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
            break
else:
    body = mime_msg.get_payload(decode=True).decode('utf-8', errors='replace')
print('=== FULL BODY ===')
print(body[:3000])
print('=== END ===')
"
```

## Known Senders with Empty Body

| Sender | Typ | Bemerkung |
|--------|-----|-----------|
| `no-reply@notifications.ui.com` | UniFi Security | Threat + Admin Access |
| `calendar-notification@google.com` | Kalender | Snippet gnueg (kurz) |
