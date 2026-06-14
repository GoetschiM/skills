# Dograh Asterisk ARI Integration — Source Analysis

## Source Confirmation

Dograh **does have** a complete Asterisk ARI (Asterisk REST Interface) telephony provider.
Verified from the GitHub repo: `api/services/telephony/providers/ari/`

## File Structure

```
ari/
├── __init__.py        # Provider registration, UI metadata, config schemas
├── config.py          # ARIConfigurationRequest/Response Pydantic schemas
├── provider.py        # ARIProvider class — main implementation
├── serializers.py     # Re-exports pipecat's AsteriskFrameSerializer
├── strategies.py      # ARIBridgeSwapStrategy + ARIHangupStrategy
└── transport.py       # Creates pipecat transport from ARI config

ari_manager.py         # Standalone WebSocket event listener process
                       # (at api/services/telephony/ari_manager.py)
```

## What the ARI Provider Does

### Outbound Calls (`initiate_call`)
- Creates an ARI channel via `POST /ari/channels`
- Supports `PJSIP/extension` and `SIP/extension` formats
- Places channel into Stasis app with `workflow_run_id` in appArgs
- Records channel info in Redis for event correlation

### Inbound Calls (ari_manager)
- Standalone process connects to ARI WebSocket events API
- Listens for `StasisStart` and `StasisEnd` events
- Creates inbound workflow runs from Stasis event data
- Manages bridge creation on new calls
- Handles reconnection with exponential backoff (1s → 300s max)

### Audio Streaming (transport.py)
- Uses pipecat's `AsteriskFrameSerializer` for μ-law RTP
- ExternalMedia bridge channels for bidirectional audio
- Creates WebSocket transport for audio pipeline

### Call Transfers (strategies.py)
- `ARIBridgeSwapStrategy`: Adds destination channel, removes external media, hangs up media channel
- Full transfer context management via Redis

### Hangup (strategies.py)
- `ARIHangupStrategy`: Proper channel teardown via `DELETE /ari/channels/{id}`
- Handles 404 (already gone) gracefully

## Configuration Schema

```python
class ARIConfigurationRequest(BaseModel):
    provider: Literal["ari"] = "ari"
    ari_endpoint: str        # e.g., http://asterisk:8088
    app_name: str            # Stasis app name registered in Asterisk
    app_password: str        # ARI user password
    ws_client_name: str      # websocket_client.conf connection name
    from_numbers: List[str]  # SIP extensions for outbound calls
```

## Provider Registration (__init__.py)

The provider registers itself in Dograh's registry with a `ProviderSpec`:
- `name: "ari"`
- `provider_cls: ARIProvider`
- `transport_factory: create_transport`
- `transport_sample_rate: 8000`
- UI metadata includes fields for `ari_endpoint`, `app_name`, `app_password`, `ws_client_name`, `from_numbers`

## UI Visibility

The ARI provider has full UI metadata defined in `__init__.py` under `_UI_METADATA`:
```python
_UI_METADATA = ProviderUIMetadata(
    display_name="Asterisk ARI",
    docs_url="https://docs.dograh.com/integrations/telephony/asterisk-ari",
    fields=[...]
)
```

## Requirements from Asterisk Side

1. `ari.conf` — ARI enabled with user/password
2. `extensions.conf` — Stasis application in dialplan: `same => n,Stasis(dograh)`
3. `websocket_client.conf` — Connection for externalMedia (name must match `ws_client_name`)
4. `http.conf` — HTTP server enabled for ARI API
5. PJSIP endpoints configured for outbound calls
6. `ari_manager.py` runs as separate process (auto-started via Docker)

## Architecture Flow

```
Phone → PJSIP → Asterisk
                  │
            StasisStart event
                  │
                  ▼
         ari_manager.py (WebSocket listener)
                  │
                  ▼
            POST /ari/channels/externalMedia
                  │
                  ▼
         pipecat transport → STT → LLM → TTS
                  │
                  ▼
            Bridge playback → Audio to caller
```

## Comparison with Current Asterisk Pipeline

| Aspect | Current Pipeline (ExternalMedia) | Dograh ARI |
|--------|-----------------------------------|------------|
| STT | faster-whisper (custom code) | Configurable via pipecat |
| LLM | Direct API calls | Dograh workflow engine |
| TTS | edge-tts/gTTS | Configurable TTS provider |
| VAD | Custom SimpleVAD | Pipecat built-in |
| Workflow | Custom Python state machine | Visual drag & drop |
| Transfer | Manual bridge ops | Built-in bridge swap |
| Recording | Custom | Auto-recording + transcripts |
| Tools/MCP | Manual | Built-in MCP native support |
