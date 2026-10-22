# Full-module deployment architecture

![Full-module deployment architecture](images/deploy2.png)

The Python engine handles device WebSocket conversations on port 8000. The Vue
management frontend and Java API use port 8002; Java stores accounts, devices and
history in MySQL and uses Redis for cached state. Python obtains managed settings
from Java using the server authentication secret. Full-module OTA uses port 8002;
vision uses HTTP 8003. Port 8001 belongs to frontend development.

The historical diagram also includes optional gateway, MCP and voiceprint paths.
It does not approve their external services. Parent-wrapper and MQTT/UDP gateway
coordination remain separate work; this guide changes neither component.

<!-- Compatibility anchors for existing links and bookmarks. -->
<a id="方式一docker运行全模块"></a>

## Method 1: Full-module Docker candidate

Read [source builds and remaining release gates](docker-build.md). Build the
Python base, server and management image from the same checkout. The old
one-command installer is retired; `docker-setup.sh` performs no deployment action.
There is no upstream prebuilt server fallback or mandatory ASR model mount.

Keep `main/xiaozhi-server/docker-compose_all.yml` in the checkout. Supply:

- `SERVER_IMAGE`, `SERVER_BASE_IMAGE` and `WEB_IMAGE` identifying your source-built
  candidate artifacts; use unique tags and record their image IDs/digests.
- Reviewed `NODE_IMAGE`, `MAVEN_IMAGE`, `RUNTIME_IMAGE`, `MYSQL_IMAGE` and
  `REDIS_IMAGE` digests. Explicit npm-registry approval and a reviewed lockfile are
  prerequisites for the management build.
- `CANDIDATE_DATA_DIR` pointing to a new candidate configuration directory and a
  new disposable `CANDIDATE_DB_PASSWORD`. Do not reuse production credentials.

Use a new Compose project name. The template allocates project-scoped MySQL,
Redis and upload volumes and binds only loopback ports 18000, 18002 and 18003.
Choose spare port overrides if those are occupied. Do not attach live volumes,
reuse a running project name, or run cleanup against existing containers.
These instructions prepare a rehearsal; starting it requires separate approval.

## Managed configuration

In an authorized disposable rehearsal, initialize the management database with
the forward migrations. Preserve historical SQL bytes/checksums and user/device/
history identities when testing a copied database. Verify repeat migration,
legacy selections and snapshot restore before considering promotion.

Register synthetic accounts only. The first registered account becomes the
superadministrator; later accounts have ordinary permissions. Verify two-user
device/history isolation. Password registration/login and local CAPTCHA remain
supported. SMS registration/recovery must return unavailable without pretending
to send or store a sent verification code.

As superadministrator, open **Parameter Management**, find `server.secret`, and
provision its value into the new candidate private configuration through an
operator-controlled secret channel. Keep it out of source, reports and build
arguments. The managed Compose topology uses this non-secret connection setting:

```yaml
manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  # Provision secret outside source control; do not reuse a production value.
```

Select approved ASR, LLM and TTS offerings and explicit model/voice settings.
Supported implementation types and cloud/loopback origins are listed in
[server configuration](Deployment.md#project-configuration). Ordinary users
select permitted offerings without receiving platform provider credentials.
Removed providers stay unavailable until an operator makes an approved choice;
the upgrade does not transfer credentials or conversations to a substitute.

Loopback AI endpoints inside a container must refer to a fixture reachable in
that container's network namespace. A Compose service alias, LAN address or
external OpenAI-compatible gateway is not an approved loopback destination.
Coordinate the fixture topology before rehearsal; do not bypass validation.

## Device endpoints and rehearsal evidence

The host can reach the candidate console at `http://127.0.0.1:18002` and the
WebSocket endpoint at `ws://127.0.0.1:18000/xiaozhi/v1/`. Configure `server.ota` and
`server.websocket` for the chosen test clients. A physical ESP32 needs a separate
approved device-reachable endpoint; the template does not expose LAN ports.

Verify account/CAPTCHA, binding, provider changes, direct WS audio turns,
history/summary, snapshot restore and removed-feature outcomes. Record externally
observed outbound attempts, including blocked requests. Use synthetic local
ASR/LLM/TTS fixtures and keep live-provider flags off. A Java startup log proves
neither a working voice turn nor registry/service independence. Gateway MQTT/UDP
acceptance needs its own authorized coordinated rehearsal.

<a id="方式二本地源码运行全模块"></a>

## Method 2: Full-module local source candidate

Use a disposable checkout, Python 3.10, JDK 21, Maven 3.9 and Node 20 with separate
MySQL/Redis instances. Use the current checked-in Maven Central settings, official
PyPI and a reviewed npm lockfile. Do not alter global repositories or existing
environments. See [the build guide](docker-build.md) for unresolved locks, package
sources and model provenance. Do not copy old SenseVoice files into this profile.

Keep database/Redis credentials and the management secret in new private runtime
configuration, outside the build context. Do not edit a working deployment's
resource files or environment. Build static frontend assets for deployment;
`npm run serve` is a development server. Tests and network-isolated rehearsal
must precede a live startup.

## Backups, upgrade and rollback

Before cutover, verify recovery from a matched backup of DB, uploads/audio,
history, Redis-dependent state, configuration and old image digests. Rehearse
against disposable copies with spare ports and separate volumes. Failed rehearsal
leaves the original environment unchanged. Get explicit approval before any live
restart, promotion or real-provider call.

Rollback restores compatible application artifacts and data together while
preserving later writes separately. Keep removed-service egress blocked even for
old images. See [the rollback checklist](docker-build.md#rehearsal-and-rollback).
