# Optional server VAD and device-owned turn boundaries

Two VAD choices are supported. Existing configurations still select **SileroVAD**;
no assistant, default, running container, or firmware is changed automatically.

| Choice | Turn boundary | Server model |
| --- | --- | --- |
| `SileroVAD` (`type: silero`) | Existing server speech/silence detection, or the existing manual protocol | Explicit local Silero ONNX artifact required |
| `DeviceVAD` (`type: device`) | Explicit device `listen/start` and `listen/stop` only | None; Silero/ONNX inference is not initialized for this choice |

Device VAD does not move speech recognition to the toy. The device decides *when
the question ends*; the configured ASR, LLM, and TTS still process the question.

## Standalone configuration

Merge this into the server's private YAML when deploying the updated code:

```yaml
selected_module:
  VAD: DeviceVAD
VAD:
  DeviceVAD:
    type: device
    max_audio_duration_ms: 60000
```

Other selected modules/credentials remain unchanged. Select `SileroVAD` to keep
server-side detection. A VAD strategy must still be explicitly selected; deleting
the VAD selection or setting it to `null` is not a supported way to disable it.

## Managed configuration

The forward-only `202610220001` migration adds a `device` provider and the enabled,
**non-default** model `VAD_DeviceVAD`. It inserts missing catalog rows only and
does not rewrite existing rows, selections, history, credentials, or defaults.
The existing management UI/API selects this model through `vadModelId`, just
like Silero; no new mobile API field or firmware setting is introduced.

After updating both manager and voice code, an administrator can select Device
VAD in Model Configuration / VAD as the global default. Where the existing VAD
feature is exposed for an assistant, it can instead be selected for that
assistant. The global choice controls startup: a global Silero selection still
requires its artifact even if one assistant later selects Device VAD. Use a
global Device VAD selection to start without a server VAD model. An assistant
that explicitly selects Silero still needs its configured local artifact.

Model configuration carries `{"type":"device","max_audio_duration_ms":60000}`.
The maximum duration accepts integers or integer strings emitted by the existing
editor, from 1000 to 300000 ms inclusive. Changes of selected model or its VAD
settings are detected even when the implementation type remains unchanged.

## Device protocol and limits

1. Send `{"type":"listen","state":"start","mode":"manual"}`.
2. Send the existing audio frames (direct WebSocket or MQTT/UDP gateway).
3. Send `{"type":"listen","state":"stop"}` when the device VAD detects the
   end of the question, or when the user releases a push-to-talk button.

`manual` describes **explicit protocol boundaries**, not how the toy's button
works. It supports both local end-of-speech detection and hold-to-talk.

The server buffers only an open turn, including its silent portions. It drains
already queued PCM before submitting the question to ASR. Duplicate starts do
not erase speech, duplicate/empty stops do not submit twice, audio outside a turn
is discarded, and abort cancels the buffered question. A new question needs a
new start. Automatic/realtime listen modes are rejected by closing the connection
rather than silently buffering audio that has no trustworthy end boundary.

Each incoming PCM frame checks both elapsed turn time and total PCM duration
(16 kHz, mono, 16 bit). Exceeding the configured maximum discards the incomplete
turn and closes the connection; it does not submit a truncated question. This
is not a silence detector or an idle timer: with no incoming audio the existing
connection timeout still applies. Queue-drain failure also discards/closes
instead of transcribing an incomplete question. Server-side automatic VAD
interruption is unavailable in this mode; explicit device abort remains usable.

## Rollout and recovery

This change is source-only until explicitly deployed. No live migration, Docker
restart, firmware flash, API key import, or paid AI call is part of implementation.
New manager and voice versions must both support `device` before it is selected;
an older voice backend rejects that unknown provider instead of falling back.

To restore server VAD, provision the reviewed Silero artifact and select Silero
again. Before reverting to older code, replace every global/assistant Device VAD
selection first. Keep the additive migration in the ledger; do not edit or delete
executed historical migrations. Database/image rollback still requires matched
backups if changes have actually been deployed.

## Implementation verification (2026-10-22)

- Python: 263 passed, 5 existing skips; 36 focused device/catalog cases cover
  no-model startup, mode validation, bounds, queue ordering, duplicate/empty
  controls, abort, cross-turn packet isolation and both audio ingress routes.
- Java: 46 focused catalog/selection/configuration tests passed.
- Fresh and upgrade MySQL/Liquibase rehearsals passed using disposable databases;
  existing identities/history/audio/snapshots and historical checksums survived,
  including repeated migration and explicit replacement checks.
- Two complete standalone WebSocket conversations passed, one per VAD strategy,
  against strict local ASR/LLM/TTS fakes: each consumed 20 Opus packets / 19200
  PCM samples and returned 6 non-silent Opus packets / 5760 decoded PCM samples.
  The unchanged historical wire harness still validates/copies its public Silero
  fixture for both cases; Device VAD's generated runtime configuration does not
  reference it. Independent factory/startup regressions prove that Device VAD
  needs neither an ONNX path nor a Silero inference-runtime import.
- The build-policy, reviewed-service, English and 118 protected-history/locale
  hash gates passed. No live AI provider, physical toy, mobile build, firmware
  flash, or current-deployment rollout is claimed by these synthetic checks.
