## Why

The backend must run and build without accounts, endpoints, downloads, or credentials from China-based external service operators. Today those dependencies extend beyond AI adapters into SMS, plugins, IP lookup, seeded configuration, model downloads, and package mirrors.

## What Changes

- Maintain a reviewed service/dependency inventory with operator evidence, scope, call sites, and remove/replace/retain decisions; geography is not inferred from domain suffix or author nationality.
- **BREAKING**: Remove unsupported service adapters, SDKs, provider presets, plugin defaults, and automatic fallbacks; existing configurations referencing them become explicitly unavailable rather than silently rerouted.
- Keep the existing provider interfaces and available service-neutral adapters; require explicit approved endpoint configuration for cloud ASR/LLM/TTS. Use local fakes for automated tests, not paid requests.
- Remove Aliyun SMS integration while preserving ordinary account/password registration; make SMS-only flows explicitly unavailable until a separately approved replacement exists.
- Remove mandatory IP geolocation and China-based weather/news/search integrations. Optional removed capabilities report unavailable without network calls; they do not block core conversation.
- Remove China-based build mirrors, image proxies, and automatic model-fetch dependencies. Produce owned, pinned images from reviewed sources rather than assuming the current upstream image contents are clean.
- Add forward-only configuration/data migration, dependency/configuration gates, and externally observed network tests for the supported backend paths.

## Capabilities

### New Capabilities

- `approved-backend-services`: Explicit permitted services, rejected configurations, no removed-provider fallback, and usable core account/device/conversation flows.
- `independent-backend-build`: Reproducible backend builds, approved dependency/model sources, and testable network independence.
- `compatible-service-migration`: Non-destructive upgrades and actionable handling of legacy provider references.

### Modified Capabilities

None; this newly initialized OpenSpec project has no existing capability specifications.

## Impact

Targets `main/xiaozhi-server`, `main/manager-api`, backend build/CI files, backend deployment examples, and required configuration selectors in `manager-web`/`manager-mobile`. Parent `compose.yaml`, bootstrap and MQTT gateway are integration seams requiring explicit coordinated implementation; they are not silently edited by this repo-local change.

Excluded: mobile framework replacement/removal of DCloud, cloud infrastructure provisioning, firmware flashing, wholesale removal of software based on contributors' nationality, and translation (completed first by the user's explicit choice). Locally executed libraries/models are classified separately from remote services: remove unused service SDKs; do not automatically rewrite self-contained libraries such as Druid/Hutool solely because of origin. The current SenseVoice/FunASR default must no longer be required for startup/build; no replacement model or paid provider is chosen without approval.

Execution approval (2026-10-21): the user approved the exact coordinated candidate
scope in `docs/maintenance/coordinated-wrapper-scope.md`, including sibling
gateway source guards/lock/tests and new parent candidate files. This authorizes
preparing and testing a separately named synthetic stack, not editing the
evaluation Compose/configuration, reading real secrets, or live cutover.

Permission-fix approval (2026-10-21): the user explicitly authorized fixing the
two confirmed device-binding authorization defects and repeating the isolated
tests without touching the current deployment. Scope is the service-level
agent-ownership check on manual/activation binding, relevant regression tests,
candidate rebuild/rehearsal and evidence updates; not a wider authorization audit
or live deployment.

Local-IP fix approval (2026-10-21): the user explicitly authorized replacing
`get_local_ip()`'s external routing probe with local interface discovery, adding
regression coverage and rebuilding/repeating only the isolated candidate. This
does not approve any external endpoint exception or evaluation deployment change.
