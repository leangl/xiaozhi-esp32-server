# English maintenance terminology

Use these terms consistently in translated first-party source and documentation.
Protocol field names, existing class names, persisted identifiers and proper
product names are not renamed simply to match this glossary.

| Term | Meaning in this project |
| --- | --- |
| agent | A configured assistant profile, not a separately running autonomous process. |
| management console | The web/mobile interface for configuring assistants and devices. |
| management API | The Java HTTP service supplying configuration and management operations. |
| voice server | The Python service processing live device conversations. |
| gateway | The separate MQTT/UDP-to-WebSocket bridge. |
| device binding | Associate an activated physical device with its owner's assistant. |
| activation code | The temporary code used to bind a device; not a provider API key. |
| provider | An interchangeable implementation for ASR, LLM, TTS or another capability. |
| voice | A selectable speech-synthesis voice; use "voice ID" for its stable identifier. |
| speech recognition / ASR | Convert captured speech into text. |
| speech synthesis / TTS | Convert response text into spoken audio. |
| voice activity detection / VAD | Distinguish speech from silence; not transcription. |
| wake word | A spoken phrase that activates interaction. |
| conversation context | Messages supplied to the model for the active dialogue. |
| memory | Selected information retained or retrieved across conversations. |
| conversation history | Persisted transcript/audio records, distinct from model context. |
| snapshot | A versioned assistant configuration, not a database backup. |
| firmware update | Install device firmware; do not use "configuration" interchangeably. |
| pairing / provisioning | Initial device/network setup; specify which operation is intended. |

Retain Chinese language examples and locale values where they exercise actual
language support. Add English explanations rather than changing those inputs.
Do not translate secrets, model names, numeric codes, endpoint paths or SQL keys.
