# independent-backend-build Specification

## Purpose

Make backend artifacts buildable from reviewed sources without China-based package mirrors, cloud-build accounts, image proxies, or implicit model downloads, and provide bounded evidence of runtime independence.

## Requirements

### Requirement: Independent artifact production

Supported backend builds SHALL use recorded approved registries and pinned dependency/model identities without accounts or services from removed operators. Fresh builds MUST NOT rely on warmed local caches to hide an otherwise required removed endpoint. Backend images SHALL be built from the reviewed source; upstream prebuilt images alone are not proof of compliance.

#### Scenario: Fresh isolated build
- **GIVEN** an empty dependency cache and only approved registry access
- **WHEN** Python, Java, management-client assets, and the coordinated gateway build are produced
- **THEN** all build inputs and artifact digests are recorded and no removed mirror, proxy, or model-host request is attempted

### Requirement: No mandatory legacy local model

An approved cloud-ASR deployment SHALL start and process a turn without the previous default local model or its auto-download service. Missing approved configuration SHALL produce a clear readiness/configuration failure rather than downloading a default model or falling back to a removed provider.

#### Scenario: Empty model cache
- **GIVEN** a backend image without SenseVoice model files and configured local ASR test endpoint
- **WHEN** the voice service starts and receives a synthetic utterance
- **THEN** the test ASR is used without model downloads or loading unused local-model SDKs

### Requirement: Network evidence covers actual execution

Verification SHALL record externally observed DNS and outbound connection attempts for fresh startup, account operations, direct WebSocket conversation, MQTT/UDP gateway conversation, history, and removed-feature failure paths. Tests MUST fail on attempted removed/unreviewed destinations, including blocked attempts, not merely successful connections. Reports SHALL distinguish test-fake coverage from approved live-provider coverage and from untested paths.

#### Scenario: Hidden provider fallback
- **GIVEN** an otherwise passing test suite and a fallback attempting an unapproved external service
- **WHEN** the network-isolated integration suite executes that path
- **THEN** the gate fails and identifies the destination and scenario without leaking payloads or credentials

### Requirement: Dependency drift is detected

CI SHALL reject reintroduction of removed service SDKs, endpoints, active presets, build mirrors, and unreviewed automatic download behavior. Historical inert records and factual documentation references SHALL have narrow, justified exceptions rather than a blanket exemption for entire source directories.

#### Scenario: Removed service reintroduced
- **GIVEN** a change adding a removed SDK dependency or active endpoint
- **WHEN** the dependency/configuration checks run
- **THEN** the change fails before a deployable compliant artifact is accepted
