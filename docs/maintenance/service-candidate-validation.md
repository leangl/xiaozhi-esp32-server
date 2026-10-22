# Isolated service-policy candidate evidence

Date: 2026-10-21. This retains earlier implementation/rehearsal evidence. Final
implementation acceptance is now recorded in the archived OpenSpec change; it
is **not live cutover, a provider-quality test or a child-data certification**.
The original evaluation deployment and all its configuration/data remain intact.

Superseding network/build checkpoint: production dependency locks now pass, and
the complete application DNS/egress matrix **passes** on final locked images
after the user-approved local-interface discovery fix. The initial failure on
two pre-existing local-IP probes to 8.8.8.8:80 is retained as historical evidence.
Current OpenSpec state is **30/30, implemented and archived**, after the approved
CI fixture correction and passing regression/full-suite repeat. See
[the current report](service-network-and-locks.md),
`service-dependency-lock-validation.json` and `service-network-validation.json`.
The sections below retain the preceding permission-rehearsal evidence/image
identities; its old build/observation limitations are superseded where noted.

## Owned build inputs and artifacts

Owned source images, built locally from the reviewed official image origins:

| Image | Local image identity |
| --- | --- |
| `xiaozhi-policy/server-base:20261021` | `sha256:f19225fab54bf448cb8076e599a260a4935f55bdaeef29d0380ef900c3de2ed4` |
| `xiaozhi-policy/server:20261021` | `sha256:ab62f1d79f99a77cb4ec46f340e98fe802e7192a7a22b67806a4f2752052f205` |
| `xiaozhi-policy/manager:20261021` | `sha256:4d878489095ceebb9ba02add0f423b1c5e97ba6f39c15a511d0349df6569235c` |
| `xiaozhi-policy/gateway:20261021` | `sha256:239eecfb752004c8a23590f8120174461b46eba98c9e8b9e12b5bb22117b1e25` |
| Test-only `xiaozhi-policy/egress-observer:20261021` | `sha256:4c00e2d4f8400245b73ba63b8ae7ee2a3a069c93069e9f701bf60e39fe8c82f4` |

The hash-locked Python resolution targets Linux ARM64 / Python 3.10. Official
PyPI wheels were fetched without a package cache. The final 70 installed Python
components are recorded in `service-python-sbom.json`; this includes base tooling
as well as runtime dependencies. A real fresh build exposed the live
`portalocker` dependency, which was restored explicitly to the requirements and
lock rather than relying on an old upstream image to supply it.

Management frontend: 1,186 existing package resolutions moved from the mirror to
official npm without changing versions/integrities. The unused self-link was
removed. A fresh npm cache/build and Maven Central build succeeded. Gateway:
78 exact dependency resolutions/integrities, official npm, lifecycle scripts
disabled, source-only Docker COPY allowlist. Operator Spring profiles,
`.env`/`.config`, actual data and generated build directories are excluded from
the final image contexts and curated test snapshots. No actual deployment
configuration or credential was read to configure the running candidate.

An initial unused management build exposed a packaging omission: a tracked
`application-*` profile could enter the JAR. The ignore rule was corrected and
the image rebuilt **before any candidate launch**. The profile contents were
not inspected and that initial image was not published or started. Local build
cache is not claimed to be securely erased; no broad cache prune was performed.

`service-build-components.json` additionally records the owned voice image's
296 installed OS packages, the manager's 36 OS packages and 120 bundled Java
runtime JAR hashes, and the gateway's 78 npm package integrities. The manager JAR
contains zero operator `application-*.yml/yaml` profiles (checked by entry names,
not by opening any operator profile).

The manager was rebuilt after the separately approved binding-permission patch.
Its 36 installed OS package identities and all 120 bundled Java library hashes
were rechecked against the recorded inventory and match. The new JAR again has
zero operator profile entries. This rebuild changes application classes, not the
dependency-locking completion claim below.

At this earlier checkpoint OS/Maven locking was incomplete. It is now completed
for the reviewed production Linux ARM64 goal, with archive hashes and offline
execution; see the superseding report. Inventories are not formal attestations.
No image was pushed. Required explicit Docker base ARG warnings are not build
failures and no implicit fallback image is supplied.

## Historical permission-rehearsal checks (superseded where noted)

| Check | Result / limit |
| --- | --- |
| Python complete offline suite | 217 passed, 5 skipped; no live-provider flag. Includes managed auxiliary slots and partial-device initialization regressions. Two old import/config prerequisite skips and three absent-key LLM skips are not passes. |
| Java expanded offline suite, permission-fix repeat | 339 executed, 337 passed, one failure and one error matching the recorded pre-change masking/MyBatis baseline defects. Two old live-context test classes excluded. |
| Binding permission regression / nearest slice | Before patch: 14 tests, 11 failed. After patch: 14/14 passed; controller, OTA and serialization regressions bring the focused slice to 22/22. |
| Java catalog/selection/snapshot focused slice | 108/108 passed, including noncanonical provider-type rejection. |
| Fresh and synthetic upgrade MySQL migration | Repeated passes, including digest-pinned test images; IDs, two-family assignments/history/audio/snapshots and historical Liquibase bytes/checksums preserved; retry/cache/replacement verified. Latest `/private/tmp/xiaozhi-policy-migration-tea8r7bz/report.md`. |
| Web tests/build | 14 Node contracts, 13 snapshot contracts, 53 Vitest tests and production build passed using fresh official-npm inputs. |
| Relevant mobile selectors/contracts | 20 passed; no native/DCloud build or framework migration. |
| Build input and npm-lock policy | 14 Python and 7 Node tests passed. |
| Service reintroduction gate | Deliberately reintroduced SDK, endpoint, mirror and unknown dependency-source fixtures rejected. |
| Gateway wire/unit fixture | 15 passed, including actual MQTT CONNECT/CONNACK, local WS, AES/UDP round trip and exact fixed-marker acceptance with arbitrary-query rejection. |
| English guard / protected assets | Zero unreviewed/stale exceptions; all 118 historical SQL/locale hashes match. CRLF-aware whitespace check passes without rewriting unrelated line endings. |

## Managed candidate results and blockers

Payload-free machine results are in `service-candidate-results.json`; public
fixture code hashes are in `service-fixtures-manifest.json`.

- API initial run: 19 passed / 3 failed across 89 real HTTP requests. Registration,
  login, normal-user selectors, assistant/device creation, history/audio storage,
  one-time playback, removed-provider writes and removed snapshot restoration
  checks passed. The first history-ownership check stopped on a legitimate
  denied-access code 401 absent from the fixture's expected-code list; after
  correcting that list, all ten ownership reads/rejections passed in a separate
  guarded replay. These initial results remain historical evidence, not the
  current clean rerun.
- **Both confirmed binding authorization defects are fixed with explicit user
  approval.** Initially both cross-user requests returned success; their
  pre-patch business bodies matched baseline HEAD after comment/whitespace
  removal. Both service paths now require a nonempty, existing agent owned by
  the binding user before any device lookup, activation-cache access, insert or
  cache invalidation. Missing/foreign agents share `NO_PERMISSION`; absent users
  get `USER_NOT_LOGIN`. The existing empty-code error and successful device
  fields/cache invalidation remain unchanged. No administrator bypass or new
  permission model was introduced, and no broader authorization audit is claimed.
- Full permission-fix rerun against a **fresh synthetic database: 22 passed,
  zero failed, 94 real HTTP requests**. Both forbidden bindings leave no device
  row. The legitimate owner can then manually bind the same MAC and activate
  using the exact same unconsumed code. Existing selectors, account/login,
  history/audio isolation and removed-provider/snapshot rejection pass too.
- Authenticated direct WS: 20 incoming Opus packets, ASR/STT/chat/TTS, six decoded
  non-silent outgoing packets / 5,760 output PCM samples; ordered text/start/stop.
- Signed MQTT + UDP/AES: the same 20 inputs / 19,200 input samples and six valid
  outputs / 5,760 samples, plus actual MQTT subscription, control barriers,
  device MCP replies and encrypted UDP framing. A repeat also passed.
- Both managed transports were repeated after the permission patch. Final
  shared-fake lifetime: exactly two ASR, two streamed chat, two TTS and two
  post-disconnect title requests; 38,400 total ASR samples and **zero invalid HTTP
  contracts**. Titles use a separately constrained Java non-streaming fixture;
  standalone voice tests still reject that path. No fake is real AI.

Integration fixes were made at the responsible boundary and regression-tested:
manager returns an auxiliary SLM slot (validated as an LLM, not a new factory),
and may omit unchanged VAD/ASR slots in private responses (managed/partial origin
is now preserved through initialization). RAG metadata uses the reviewed local
tool boundary. Authentication was not disabled: the client signs the known
synthetic key, supplies the existing User-Agent contract, and fixture SQL enables
optional JSON ping for ordering barriers.

The first MQTT rehearsal failed the strict sample-count check because its plain
WS URL omitted `?from=mqtt_gateway`; without that existing marker the server
decoded the 16-byte gateway envelope as Opus. The policy now accepts exactly that
marker on the same reviewed targets, still rejecting other queries/redirects.
Corrected full turns passed without changing audio frames or AES. An additional
Java non-streaming request was traced to `ConnectionHandler`'s post-disconnect
title daemon and explicitly covered by the title fake, not ignored as success.

## Runtime topology and observed egress boundary

The approved standalone parent `compose.service-policy.yaml` creates only project
`xiaozhi-policy-rehearsal` resources labelled
`xiaozhi.validation=service-policy-rehearsal-20261021`. It uses fresh MySQL/Redis,
upload and voice volumes. Manager, voice, gateway and test-only AI fakes share a
network namespace and explicit loopback service endpoints. The backend bridge is
internal; it is not connected to the original evaluation network or data.

On this Docker installation, publishing the requested loopback ports on an
internal-only bridge produced empty actual port mappings. No additional outbound
network was attached to work around that. Rehearsal clients instead run inside
the candidate network namespace. The wrapper's declared localhost bindings are
not evidence that host connectivity works here.

The external `strace` harness passed its 45 Linux tests, including synthetic
secret non-disclosure. On the actual current standalone voice-smoke process it
observed 116 relevant calls / 83 numeric IP attempts in the final repeat, zero denials or parse
errors, and child exit zero. The smoke exercised real Opus -> PCM -> approved
ASR/chat/TTS adapters -> Opus against strictly checked local HTTP fakes. This is
protocol/framing proof, not actual transcription/AI quality. The payload-free
aggregate is recorded in `service-egress-observation.json` (an earlier repeat
also passed, with 115/82 and 118/85 calls/attempts; scheduling changes these counts).

The observed destinations for that smoke were exactly loopback (`127.0.0.1` and
`::1`) on dynamic fixture ports. The explicit broad-loopback test mode allows
non-DNS ports only, not arbitrary 127/8 or cloud destinations. Unknown/blocked
numeric attempts and unresolved sends fail. DNS-question/operator names, all
management/gateway processes/scenarios, `sendmmsg`, `io_uring` and trace-escaping
code were **not covered by that earlier smoke**. Internal networking is defense
in depth, not proof that an unobserved attempt never occurred. The full witness
in the superseding network report closes task 7.1.

## Cleanup and capability review

The initial five synthetic volumes were removed to force a fresh database for
the permission-fix repeat. After retaining payload-free evidence, all six
labelled candidate containers, their internal network and the five replacement
synthetic volumes were removed. No evaluation volume was removed. All five
original evaluation services remain healthy, with unchanged container IDs,
image IDs and start times in the read-only checks. No live stack was restarted.

| OpenSpec capability | Evidence / acceptance state |
| --- | --- |
| `approved-backend-services` | Provider/configuration boundaries, ordinary accounts, selectors, binding permissions and both voice transports pass against local fakes. The full DNS/egress gate passes on locked images after the approved local-IP fix. Live operators/model quality remain untested. |
| `compatible-service-migration` | Fresh/upgrade/retry/replacement preservation proofs and current API/protocol/ownership fixtures pass after the approved binding fix. Matched-backup rollback instructions exist, no real rollout occurred. |
| `independent-backend-build` | Owned official-source images, Python/npm/OS/Maven locks, preserved component records and the complete externally observed synthetic DNS/egress matrix pass. Production platform/goal limits remain documented. |

OpenSpec is now **30/30, implemented and archived**. All three capability specs
were reviewed and synchronized; the final CI fixture regression was fixed and
verified with explicit user approval. The initial failed network report remains
under `previousRun`. Implementation acceptance is scoped to this cleanup;
production/provider readiness and live cutover remain separately gated.

## Before a real-provider or deployment trial

1. Preserve the binding regression gate in future builds. These two fixes and
   synthetic tests do not establish complete cross-family production security.
2. Retain the archived review and passing local-IP/network/CI evidence when
   selecting release artifacts; do not equate implementation closure with rollout.
3. Explicitly select reviewed real ASR/LLM/TTS models/voices/endpoints, retention
   and credentials. No provider account, paid call or new data recipient was
   provisioned by this cleanup. Removed optional SMS/weather/news/search/voice
   cloning are unavailable rather than silently substituted.
4. Review affected saved assistants/templates in the remediation catalog and
   choose replacements explicitly. Keep old snapshots inert; no auto-restore of
   retired providers. Missing selections/readiness must fail before a turn.
5. Obtain a separate live-cutover approval and matched backups under the owner's
   control: DB/Liquibase state, uploaded audio, relevant Redis/config state,
   provisioned model files, source and all image identities. The private source
   archive in `service-removal-progress.md` is not a data backup.
6. A rollback restores source/images/config/data as a matched set, preserving
   post-cutover writes separately first. Reinstating old code does not authorize
   contacting retired providers; keep network restrictions and unavailable
   features until explicitly approved replacements are restored.

The change was archived only after explicit approval and passing final checks.
No commit, push, firmware change or live-stack restart occurred. The new gateway lock is ignored by the existing sibling
Git rules and will need deliberate inclusion when the owner later requests a
focused commit; it has not been staged here.
