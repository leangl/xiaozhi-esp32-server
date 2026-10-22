# Separate gateway translation scope

The checkout at `../gateway` is a separate repository. The user explicitly
authorized including its translation on 2026-10-20. Its clean baseline is
`93f026ad3a9a5572c9cf6ce651dd8fcf46fd2419`; maintained-source translation and its
seven offline differential checks are complete. No gateway
deployment or restart is authorized by this translation.

| Repository-relative file | Initial Han-bearing lines | Surface to translate |
| --- | ---: | --- |
| `app.js` | 170 | Bridge lifecycle, MQTT/UDP/WS handling, diagnostics and management API comments |
| `mqtt-protocol.js` | 106 | MQTT framing/parser and packet encoding documentation |
| `utils/call-manager.js` | 37 | Call state, matching, wake-up and timeout documentation |
| `utils/config-manager.js` | 13 | Configuration loading/watch diagnostics and comments |
| `utils/mqtt_config_v2.js` | 17 | Authentication/client-ID validation documentation and diagnostics |
| `package.json` | 1 | Package description |
| `README.md` | 16 | Bridge overview, deployment link and management API authentication instructions |

Any subsequent edit must preserve MQTT topic/field names, packet bytes, AES
framing and key handling, UDP sequence/timestamps, WebSocket authentication
format, API routes/status codes and call-state transitions. Human-readable wire
errors must be checked for consumers before translation. Test source copies
without starting a second bridge against deployed devices, and do not print
tokens, signature keys or live configuration values.

Baseline tests and local deployment wrappers live outside this upstream change.
The gateway has its own exact exception manifest and standalone CI guard under
`tools/english-audit.mjs`. Fifteen Chinese wire/speech lines are retained with
English meanings and consumer evidence in `TRANSLATION_NOTES.md`. Syntax,
token preservation, packet framing, credentials and call-state checks pass;
live networking/audio has not been tested or represented as completed.
