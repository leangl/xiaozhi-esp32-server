## Purpose

Upgrade existing deployments away from removed services without rewriting database history, destroying family conversation data, changing device protocols, or silently changing the provider receiving data.

## ADDED Requirements

### Requirement: Forward-only legacy handling

Upgrades SHALL preserve executed migration files/checksums and existing users, device ownership, conversations, audio references, and memories. Forward migrations SHALL make removed models/templates/plugins non-selectable, report affected assistants, and require an explicit approved replacement before those affected capabilities resume. Configuration caches SHALL be invalidated consistently.

#### Scenario: Assistant references removed provider
- **GIVEN** a database containing an assistant assigned to a removed model and existing conversation history
- **WHEN** the upgrade and readiness checks run
- **THEN** history and ownership remain intact, the removed choice is unavailable, and the assistant reports which setting needs replacement without network fallback
- **AND** selecting an approved replacement restores the capability without changing the assistant identity

#### Scenario: Repeated migration
- **GIVEN** a previously upgraded database
- **WHEN** the migration/readiness process runs again
- **THEN** it does not duplicate records, overwrite user choices, or invalidate historical checksums

### Requirement: Protocol compatibility

The existing HTTP API response structure/error codes, device identity fields, direct WebSocket framing, and MQTT/UDP gateway framing SHALL remain compatible except for explicit unavailable/rejected outcomes for removed integrations. Ordinary-user authorization MUST remain enforced.

#### Scenario: Existing synthetic clients
- **GIVEN** clients using the pre-change account, device, history, WebSocket, and gateway contracts
- **WHEN** they connect using approved configuration
- **THEN** their successful workflows remain compatible and another user's device or history remains inaccessible

### Requirement: Reversible rollout

Deployment instructions SHALL require an isolated rehearsal and a verified database/volume/configuration backup before replacing the running environment. Rollback SHALL restore compatible application artifacts and data together; it MUST NOT automatically route traffic back to removed services. No live cutover or paid-provider request is implicit in automated verification.

#### Scenario: Rehearsal fails
- **GIVEN** a failed upgrade rehearsal using copied data and separate ports/volumes
- **WHEN** rollout is evaluated
- **THEN** the original deployment remains unchanged and the failed candidate cannot be promoted as verified
