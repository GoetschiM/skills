# Nextcloud Talk API v1 — Quirks & Behaviour (empirisch ermittelt)

## Base URL

```
POST/GET http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}
```

## Headers (PFLICHT)

- `OCS-APIRequest: true` — ohni dä git's en 404
- `Content-Type: application/x-www-form-urlencoded` — für POST
- `Accept: */*`

## Auth

- HTTP Basic Auth: `curl -u "benutzer:passwort"`
- Benutzer-Kürzel (username), nöd Display-Name!

## Chat Send (POST)

```bash
POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}
  message=@Hermes Hallo!
```

- **Response**: 201 Created bei Erfolg (nöd 200!)
- **Format**: XML
- **Sonderzeiche**: @Mentions werde intern als `{mention-user1}` kodiert — s'API erwartet aber `@Hermes` im message-Text

## Chat Receive (GET)

```bash
GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}?lookIntoFuture=0&limit=100
```

### Parameter

| Parameter | Werte | Effekt |
|-----------|-------|--------|
| `lookIntoFuture` | `0` | Normali Abfrag: git die letzte Messages zrugg |
| `lookIntoFuture` | `1` | Long-Poll: blockiert bis nöii Messages da sind (Timeout ~30s) |
| `limit` | 1-100 | Maximali Anzahl Messages pro Abfrag |
| `lastKnownMessageId` | Integer | **TRICKY!** Siehe unten |

### `lastKnownMessageId` Verhalten (GEGEN die Intuition!)

- **Erwartet**: `lastKnownMessageId=36` gibt Messages mit **ID > 36** (nöieri)
- **Realität**: `lastKnownMessageId=36` gibt Messages mit **ID <= 36** (älteri/glichi)

Das heisst: `lastKnownMessageId=x` filtert **älteri/glichi** Messages = exkludiert nöii.

**Konsequenz**: Für Polling niemals `lastKnownMessageId` verwende! Stattdesse:
1. Immer alli letzte Messages hole (ohne Parameter)
2. Lokal di nöii Messages mit vorherigem `last_message_id` vergliche
3. Nur Messages verarbeite wo ID > last_message_id hei

### XML-Response Struktur

```xml
<?xml version="1.0"?>
<ocs>
  <meta>
    <status>ok</status>
    <statuscode>200</statuscode>
    <message>OK</message>
  </meta>
  <data>
    <element>
      <id>40</id>
      <actorType>users</actorType>
      <actorId>michel</actorId>
      <actorDisplayName>Michel G.</actorDisplayName>
      <message>Hallo @{mention-user1}! Test vom Gateway</message>
      <messageParameters>
        <element>
          <parameterType>user</parameterType>
          <parameterId>Hermes</parameterId>
          <name>Hermes</name>
        </element>
      </messageParameters>
      <timestamp>1717043200</timestamp>
    </element>
  </data>
</ocs>
```

### Mention-Parsing (WICHTIG!)

**`<message>`**-Text enthalt `{mention-user1}` **statt** `@Hermes`!

Die Mapping-Information isch in **`<messageParameters>`**:
```xml
<messageParameters>
  <element>
    <parameterType>user</parameterType>
    <parameterId>Hermes</parameterId>   <!-- Username -->
    <name>Hermes</name>                 <!-- Display-Name -->
  </element>
</messageParameters>
```

**Fix:** `<messageParameters>` parsiere und `{mention-*}` durch `@` + `name` ersetze.

## Room Verwaltung (v4 API)

```bash
# Room erstelle
POST /ocs/v2.php/apps/spreed/api/v4/room
  roomType=3&roomName=Hermes-Lab

# Room löschen
DELETE /ocs/v2.php/apps/spreed/api/v4/room/{token}

# User zum Room hinzuefuege
POST /ocs/v2.php/apps/spreed/api/v4/room/{token}/participants
  newParticipant=Hermes

# Response 200 OK, Format XML
```

## Timeouts

- **normali Polls**: 30-60s bis Response — Nextcloud PHP isch träg
- **Long-Poll** (lookIntoFuture=1): hät Verbindig offe bis nöii Message oder 30s Timeout
- **HTTPX Default-Timeouts sind z'churz** — immer `timeout=30` setze

## Fehler-Codes

| Status | Bedeutung |
|--------|-----------|
| 200 | OK (GET) |
| 201 | Created (POST Nachricht) |
| 400 | Bad Request (fehlende Parameter) |
| 404 | Room nöd gfunde oder Header fehlt |
| 412 | Room isch gschlosse oder neme verfügbar |
