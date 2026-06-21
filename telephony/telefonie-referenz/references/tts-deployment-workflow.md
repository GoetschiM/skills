# TTS-Audio Deployment Playbook (CT112 → CT117)

Dieses Reference dokumentiert den Workflow für TTS-Audio-Bereitstellung
auf dem Telefonie-Container CT117, der kein edge-tts installiert hat.

## Standard-Workflow

```
CT112 (edge-tts)  ──TTS→  .mp3  ──ffmpeg→  .alaw + .ulaw
     │
     │ pct pull 112 /tmp/... → Proxmox Host
     │ pct push 117 /tmp/... → CT117
     ▼
CT117 (Asterisk)  1. find / -name "apollo_notify.*" -delete   ← KRITISCH!
                   2. cp → /usr/share/asterisk/sounds/apollo_notify.alaw
                   3. chown asterisk:asterisk
                   4. Call-File → Context: nova-local, Extension: s
```

## ⚠️ WICHTIG: Sound-Index Reload nach Deploy (KRITISCH — 07.06.2026)
- Nach Deploy von Sound-Dateien: `asterisk -rx "core reload"` AUSFÜHREN!
- `dialplan reload` reicht NICHT — der Sound-Index wird nur mit `core reload` aktualisiert
- **Symptom:** `core show sound <name>` → "not found in index", obwohl Datei existiert
- Der Call wird ANSWERED, aber Playback-Schritt wird übersprungen → nur Hangup in CDR
- **Immer prüfen:** `asterisk -rx "core show sound apollo_notify"` nach Deploy

## ⚠️ WICHTIG: Alte Sound-Dateien restlos entfernen

Bevor neue Sounds deployt werden, **MÜSSEN** alle alten Dateien gelöscht werden:

```bash
# Alte apollo_notify Dateien aus ALLEN Verzeichnissen löschen
find / -name "apollo_notify.*" -delete 2>/dev/null || true

# Bestätigen dass wirklich keine mehr da sind
find / -name "apollo_notify.*" 2>/dev/null   # → sollte leer sein!
```

**Warum?** (Erfahrung vom 07.06.2026):
- `/var/lib/asterisk/sounds/` hatte eine 1.3MB alte `apollo_notify.wav` vom 5. Juni
- Meine neuen 109KB `.alaw` in `/usr/share/asterisk/sounds/` wurden ignoriert
- Asterisk bevorzugt die grössere/ältere Datei in `/var/lib/asterisk/sounds/`
- Michel hörte die alte "Hallo, hier ist NOVA"-Ansage statt meiner neuen
  
**MERKE:** `find / -name "apollo_notify.*" -delete` vor jedem Sound-Deploy!

## TTS-Text-Richtlinien (07.06.2026)

- **Ansagen müssen NEUTRAL sein** — KEINEN Agentennamen hardcoden!
- ❌ FALSCH: "Hallo, hier ist NOVA" / "Hallo Michel, hier ist NOVA"
- ✅ RICHTIG: "Hallo. Das ist ein Testanruf. Das System funktioniert."
- ✅ RICHTIG: "Hallo. Der Statusbericht ist fertig. Ich fasse kurz zusammen."
- **Begründung:** Mehrere Agenten nutzen denselben Sound-Namen `apollo_notify`. Wer zuletzt deployed, überschreibt den Sound.
- Falls ein Name nötig → via dynamischen Platzhalter `{AGENT_NAME}` im Text-Template, niemals hardcoden
- Kurze, klare Sätze
- Hochdeutsch/Schriftdeutsch — NIEMALS Schweizerdeutsch!

## Vollständiges Script (als Referenz)

```python
#!/usr/bin/env python3
"""TTS generieren und auf CT117 deployen — via Proxmox Host"""
import subprocess, sys, os, shlex

TEXT = "Hallo. Das ist ein Testanruf."  # ← NEUTRAL halten — kein Agentenname!
PROXMOX_HOST = "10.0.60.10"
PROXMOX_PASS = "Riotstar_PROXMOX_13"

# 1. TTS auf CT112 (wo edge-tts installiert ist)
subprocess.run([sys.executable, "-m", "edge_tts",
    "--voice", "de-DE-SeraphinaMultilingualNeural",
    "--rate", "+30%",
    "--text", TEXT,
    "--write-media", "/tmp/nova_audio.mp3"
], check=True, capture_output=True)

# 2. Konvertieren
subprocess.run(["ffmpeg", "-y", "-i", "/tmp/nova_audio.mp3", "-ar", "8000",
    "-ac", "1", "-sample_fmt", "s16", "/tmp/nova_audio.wav"], check=True)
subprocess.run(["ffmpeg", "-y", "-i", "/tmp/nova_audio.wav", "-f", "alaw",
    "/tmp/nova_audio.alaw"], check=True)
subprocess.run(["ffmpeg", "-y", "-i", "/tmp/nova_audio.wav", "-f", "mulaw",
    "/tmp/nova_audio.ulaw"], check=True)

# 3. Über Proxmox kopieren via sshpass
ssh_cmd = f"sshpass -p {shlex.quote(PROXMOX_PASS)} ssh -o StrictHostKeyChecking=no root@{PROXMOX_HOST}"
subprocess.run(f"{ssh_cmd} \"pct pull 112 /tmp/nova_audio.alaw /tmp/nova_audio.alaw\"", shell=True)
subprocess.run(f"{ssh_cmd} \"pct pull 112 /tmp/nova_audio.ulaw /tmp/nova_audio.ulaw\"", shell=True)
subprocess.run(f"{ssh_cmd} \"pct push 117 /tmp/nova_audio.alaw /tmp/nova_audio.alaw\"", shell=True)
subprocess.run(f"{ssh_cmd} \"pct push 117 /tmp/nova_audio.ulaw /tmp/nova_audio.ulaw\"", shell=True)

# 4. Auf CT117 als apollo_notify deployen + Call-File
subprocess.run(f"""{ssh_cmd} "pct exec 117 -- bash -c '
  # AUCH im de/ Verzeichnis deployen (wegen defaultlanguage=de)
  mkdir -p /usr/share/asterisk/sounds/de
  cp /tmp/nova_audio.alaw /usr/share/asterisk/sounds/apollo_notify.alaw
  cp /tmp/nova_audio.ulaw /usr/share/asterisk/sounds/apollo_notify.ulaw
  cp /tmp/nova_audio.alaw /usr/share/asterisk/sounds/de/apollo_notify.alaw
  cp /tmp/nova_audio.ulaw /usr/share/asterisk/sounds/de/apollo_notify.ulaw
  chown -R asterisk:asterisk /usr/share/asterisk/sounds/apollo_notify.* /usr/share/asterisk/sounds/de/apollo_notify.*
  chmod 644 /usr/share/asterisk/sounds/apollo_notify.* /usr/share/asterisk/sounds/de/apollo_notify.*
  cat > /var/spool/asterisk/outgoing/nova_call.call << \\"'\\''CALLC'\\"'\\''
Channel: PJSIP/0796459743@salt-trunk
Context: nova-local
Extension: s
Priority: 1
CallerID: "System"     # ← neutral, kein Agentenname!
MaxRetries: 2
RetryTime: 60
WaitTime: 120
CALLC
  chown asterisk:asterisk /var/spool/asterisk/outgoing/nova_call.call
  echo Call deployed
' "''", shell=True)

print("✅ Audio deployed, Call initiated!")
```

## Proxmox Shell Kommandos (zum schnellen Kopieren)

```bash
# Von CT112 nach CT117 kopieren
pct pull 112 /tmp/nova_audio.alaw /tmp/nova_audio.alaw
pct pull 112 /tmp/nova_audio.ulaw /tmp/nova_audio.ulaw
pct push 117 /tmp/nova_audio.alaw /tmp/nova_audio.alaw
pct push 117 /tmp/nova_audio.ulaw /tmp/nova_audio.ulaw

# Sound mit Sprache-Unterstützung deployen (defaultlanguage=de!)
pct exec 117 -- mkdir -p /usr/share/asterisk/sounds/de
pct exec 117 -- cp /tmp/nova_audio.alaw /usr/share/asterisk/sounds/apollo_notify.alaw
pct exec 117 -- cp /tmp/nova_audio.ulaw /usr/share/asterisk/sounds/apollo_notify.ulaw
pct exec 117 -- cp /tmp/nova_audio.alaw /usr/share/asterisk/sounds/de/apollo_notify.alaw
pct exec 117 -- cp /tmp/nova_audio.ulaw /usr/share/asterisk/sounds/de/apollo_notify.ulaw
pct exec 117 -- chown -R asterisk:asterisk /usr/share/asterisk/sounds/apollo_notify.* /usr/share/asterisk/sounds/de/apollo_notify.*
pct exec 117 -- chmod 644 /usr/share/asterisk/sounds/apollo_notify.* /usr/share/asterisk/sounds/de/apollo_notify.*

# Sound-Index reloaden (KRITISCH!)
pct exec 117 -- asterisk -rx "core reload"

# Call-File erstellen (mit neuem Context: nova-api)
pct exec 117 -- bash -c 'cat > /var/spool/asterisk/outgoing/nova_call.call << "EOF"
Channel: PJSIP/0796459743@salt-trunk
Context: nova-api           # ← NEU: jetzt Context nova-api, nicht mehr nova-local!
Extension: s
Priority: 1
CallerID: "System"   # ← neutral!
MaxRetries: 2
RetryTime: 60
WaitTime: 120
EOF'
pct exec 117 -- chown asterisk:asterisk /var/spool/asterisk/outgoing/nova_call.call
```

## Fehlerdiagnose nach Call

```bash
# 0. Sound-Index prüfen (KRITISCH — nach Deploy prüfen!)
pct exec 117 -- asterisk -rx 'core show sound apollo_notify'
# → Sollte: "DETAILS: Sound apollo_notify" zeigen, nicht "not found in index"
# → Wenn "not found": pct exec 117 -- asterisk -rx "core reload"
#   (dialplan reload reicht NICHT!)

# 1. Läuft Asterisk?
pct exec 117 -- asterisk -rx 'core show version'

# 2. Trunk registered?
pct exec 117 -- asterisk -rx 'pjsip show registrations'

# 3. Welche Kontexte gibt's?
pct exec 117 -- asterisk -rx 'dialplan show' | grep "^\["

# 4. Aktive Channels?
pct exec 117 -- asterisk -rx 'core show channels'

# 5. Letzte CDRs — HIER steckt die Antwort!
pct exec 117 -- tail -5 /var/log/asterisk/cdr-csv/Master.csv
#   → Application-Spalte zeigt was passiert ist:
#     "Playback(apollo_notify)" = Sound gefunden ✅
#     "Hangup" = Sound NICHT gefunden ❌ (Prüfe de/ Verzeichnis, Sound-Index, oder alte Dateien)

# 6. Logs während Call
pct exec 117 -- tail -50 /var/log/asterisk/full

# 7. Sound vorhanden? (BEIDE Pfade prüfen!)
pct exec 117 -- ls -la /usr/share/asterisk/sounds/apollo_notify.*
pct exec 117 -- ls -la /usr/share/asterisk/sounds/de/apollo_notify.*
# → Datei MUSS in BEIDEN Pfaden liegen (defaultlanguage=de!)

# 8. Format prüfen
pct exec 117 -- file /usr/share/asterisk/sounds/apollo_notify.alaw
# Sollte: "CCITT G.711 a-law" zeigen — wenn nur "data" ist Format evtl. fehlerhaft
```
