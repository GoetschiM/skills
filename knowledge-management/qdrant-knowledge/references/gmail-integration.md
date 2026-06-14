# Gmail-Document-RAG Integration

## Übersicht

PDF-Anhänge aus Gmail automatisch extrahieren, via Document-RAG Pipeline in Qdrant indexieren und Original in Minio speichern.

```
Gmail API → MIME-Parsing → PDF-Datei → pymupdf → Chunking → Embedding → Qdrant + Minio
```

## Token-Location

Auf Hermes-156 liegen die Google OAuth-Tokens **nicht** unter dem Standard-Pfad, sondern unter:

```
/opt/data/home/.hermes/google_token.json
/opt/data/home/.hermes/google_client_secret.json
```

Die google-workspace Scripts erwarten sie unter `/root/.hermes/`. **Workaround: Symlink**

```bash
ln -sf /opt/data/home/.hermes/google_token.json /root/.hermes/google_token.json
ln -sf /opt/data/home/.hermes/google_client_secret.json /root/.hermes/google_client_secret.json
```

> **Warum dieser Pfad?** Hermes läuft als root, aber der User-Home (wo Apollo/Nova die Tokens ablegt) ist `/opt/data/home/`. Beide Agenten teilen sich die Credentials über den Symlink.

## Pipeline: gmail_to_qdrant.py

Das Script `scripts/gmail_to_qdrant.py` ist das Herzstück:

```python
# 1. Gmail API → Message mit format="raw" abrufen
# 2. Base64-decode → MIME-Parsing (email stdlib)
# 3. PDF-Attachments extrahieren (Content-Disposition check)
# 4. Via qdrant_knowledge.py store file → Qdrant + Minio
```

### Nutzung

```bash
export QDRANT_API_KEY="..."  # Pflicht!
python3 scripts/gmail_to_qdrant.py <GMAIL_MESSAGE_ID> [kategorie]
```

### Gmail-Nachrichten mit PDF finden

```bash
GAPI="python3 /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py"

# PDF-Mails der letzten 30 Tage
$GAPI gmail search "has:attachment filename:pdf newer_than:30d"

# Ungelesene PDF-Mails
$GAPI gmail search "has:attachment filename:pdf is:unread"
```

### Batch-Verarbeitung aller PDF-Mails

```bash
GAPI="python3 /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
for id in $($GAPI gmail search "has:attachment filename:pdf newer_than:1d" --max 50 | python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)]"); do
  python3 scripts/gmail_to_qdrant.py "$id" rechnungen
done
```

## API-Besonderheiten

### Gmail API `get` vs Attachments

Der `gmail get` Befehl liefert nur den HTML-Body. Attachments sind NICHT im body-Feld enthalten — sie müssen über `format="raw"` und MIME-Parsing extrahiert werden:

```python
# Raw MIME abrufen
msg = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
raw = base64.urlsafe_b64decode(msg["raw"])

# MIME parsen
import email
mime_msg = email.message_from_bytes(raw, policy=email.policy.default)

# Attachments extrahieren
for part in mime_msg.walk():
    if part.get_content_maintype() == "multipart": continue
    filename = part.get_filename()
    if filename and part.get_payload(decode=True):
        # → Speichern & verarbeiten
```

### Token-Refresh

```bash
# Check auth status
python3 /root/.hermes/skills/productivity/google-workspace/scripts/setup.py --check

# Falls abgelaufen: Token erased sich automatisch via google-auth
# Falls nicht: Token löschen und neu auth (siehe google-workspace Skill)
```

## Automatischer Cronjob

Auf Hermes-156 läuft ein Cronjob `Gmail-PDF-Tages-Scan` täglich um 08:00 UTC:

```
Skills: productivity/google-workspace, knowledge-management/qdrant-knowledge
Schedule: 0 8 * * * (täglich 08:00 UTC)
Deliver: origin (nur bei Änderung)
```

Der Cronjob scannt nach PDF-Mails der letzten 24h, verarbeitet sie automatisch und markiert sie als gelesen. Stille Läufe (keine neuen PDFs) liefern keine Nachricht.

> ⚠️ **User-Preference:** Maximal 1x täglich. Kein 30-Minuten-Scan — das wäre Spam. Die Pipeline soll Dokumente sammeln, nicht permanent pollen.
