# Hermes Call REST API — Setup (23.05.2026)

## Architecture
Hermes (10.0.60.156) runs a FastAPI server (port 5002) as a systemd service.
Any agent on the network can POST to trigger an outgoing call.

Flow: Agent → POST /call → edge-tts TTS → ffmpeg convert → paramiko SFTP → Asterisk → Salt-Trunk → Michel

## Source code
- `/opt/call-api/hermes-call-api.py` — Full FastAPI application
- `/etc/systemd/system/hermes-call-api.service` — systemd unit

## Service management
```bash
systemctl status hermes-call-api
systemctl restart hermes-call-api
journalctl -u hermes-call-api -n 50 --no-pager
```

## Test result
- 23.05.2026 18:18 — First test call via REST API: SUCCESS (2.7s processing time)
- Voice: de-DE-KillianNeural (Hermes), text: "Hallo Michel, hier ist Hermes..."
- Asterisk result: OK

## Dependencies (all pre-installed)
- fastapi, uvicorn, paramiko, edge-tts, ffmpeg

## Voice convention (CRITICAL)
- ALL calls MUST be Hochdeutsch. NEVER de-CH voices.
- Hermes → de-DE-KillianNeural (male)
- Apollo → de-DE-FlorianMultilingualNeural (male)
- Nova → de-DE-SeraphinaMultilingualNeural (female)
- Fallback → de-DE-ConradNeural (male)

## Qdrant
- Entry fcd6e8aa-26a: API documentation
- Entry 7a5f80c1-4dd: Code repo details

## Skill
- telephony/hermes-call-api — Created 23.05.2026
