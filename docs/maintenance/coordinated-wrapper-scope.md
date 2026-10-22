# Approved coordinated wrapper/gateway candidate scope

Review and approval date: 2026-10-21. The user explicitly approved this narrow
extension to the parent wrapper and sibling gateway for an isolated rehearsal.
It does not authorize changing the running evaluation deployment, real `.env`,
gateway configuration, database, audio uploads or firmware.

## Exact proposed files and transformations

Root: `/Users/leandroglossman/Projects/xiaozhi-server-local`.

| File | Proposed change |
| --- | --- |
| `compose.service-policy.yaml` (new) | Standalone candidate project using owned source-built voice/manager/gateway images, separate named volumes, synthetic configuration and different localhost-only ports. No upstream voice image or mandatory SenseVoice mount. Never include the evaluation `compose.yaml`. |
| `Gateway.candidate.Dockerfile` (new) | Reviewed digest-pinned official Node input, `npm ci --ignore-scripts` with official registry and the new lock; preserve unprivileged runtime. |
| `README.service-policy.md` (new) | Exact synthetic setup/rehearsal/cleanup and matched-backup rollback gates. No automatic deployment. |
| `gateway/app.js` | Replace the implicit public endpoint fallback with required explicit `PUBLIC_IP`; validate configured outbound voice URLs before WebSocket construction, disable redirects and redact rejected URL errors. No MQTT/UDP/audio framing change. |
| `gateway/utils/config-manager.js` | Validate candidate server pools before activation; invalid reload preserves last valid configuration. No dumping credentials or complete URLs. |
| `gateway/utils/service-policy.js` (new) | Exact supported outbound targets: loopback and the candidate-owned internal `voice` service; no arbitrary cloud aliases. This is source-controlled policy, not a user-supplied allow-all environment variable. |
| `gateway/package-lock.json` (new) | Resolve existing package ranges through official npm without lifecycle scripts; record exact transitive versions/integrities. No package upgrade requested beyond resolving the currently unlocked inputs. |
| `gateway/tools/service-policy.test.js` (new) | Synthetic endpoint/reload/error/protocol checks without deployment keys or live providers. |

`compose.yaml`, `bootstrap.mjs`, `Gateway.Dockerfile`, actual `.env`, actual
`gateway-config.json`, `data/`, `models/`, `runtime/`, existing volumes and
existing containers remain untouched. Build/rehearsal must use the candidate
files explicitly; source approval does not authorize live cutover.

Before applying, review the concrete candidate diff against this table. If
implementation needs another file, service origin or mutation, ask again. A
fresh-cache build and externally observed DNS/connection test remain separate
acceptance evidence; neither a lockfile nor offline mocks certify egress.

Rehearsal compatibility note: the exact `?from=mqtt_gateway` marker is permitted
on the same reviewed `/xiaozhi/v1/` targets. It is existing envelope metadata,
not a new service origin, arbitrary query exception or audio-framing change.
