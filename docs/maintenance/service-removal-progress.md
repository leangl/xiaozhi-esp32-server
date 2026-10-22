# External service removal: implementation evidence

Started 2026-10-20 after the English-translation change. This document records
incremental evidence, not a claim of complete service independence.

## Baseline and ownership

Git baseline remains `eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b`. The completed
translation is uncommitted and must be preserved. A private pre-change source
archive was created at
`/private/tmp/xiaozhi-service-removal-prechange-20261020.tar`, SHA256
`0c4eac069c043baad59dff512999819272d1f7d74a932d2b06c4df88de2a7edc`.
It contains Git-tracked/non-ignored source, not a production database backup.
Do not publish the archive or use it as authorization to restore running data.

Owned edit root: this upstream checkout. The sibling gateway and new parent
candidate files were subsequently approved in the exact scope recorded in
`coordinated-wrapper-scope.md`; the original parent deployment remains outside
the mutation scope.
No running evaluation service is restarted or reconfigured by source edits.

Observed running image identities (read-only inventory):

| Service | Image identity |
| --- | --- |
| Voice | `sha256:265fb3dbadba2c493e4661c2481e9815ae6b7cb40e4c0bad3227cade3a1c5ca9` |
| Management | `sha256:3c33729aa4aea32b3024deb9ecda3b36fe5783920a62eeef7f8273a285bf313c` |
| Gateway | `sha256:f7d8e51ae5aa78911071be4171a4da338f8813bb691bad7cdca26138c77a01c5` |
| MySQL | `sha256:0f51e63e537a1f176423fa03ef559aabe6fa4372a53160a44bc7e75da7d15364` |
| Redis | `sha256:ae471bdc20de180beed36e347d170ec0bdf8faa327959ea1f24692f22b05b955` |

These are rollback/inventory evidence only, not compliant candidate artifacts.

Existing checks and baseline defects are recorded in
[English coverage](english-coverage.md), [Java validation](java-translation-validation.md),
[frontend validation](frontend-translation-validation.md) and
[migration validation](migration-translation-validation.md). Do not reinterpret
their translation-only results as proof of the service-removal change.

The [replacement matrix](service-replacement-matrix.md) records explicit
remove/retain/review decisions, evidence limitations and future activation gates.
The generated [source inventory](service-inventory.json) is a review aid, not a
traffic report or blanket allowlist.

Initial OpenSpec checkpoint: **6/30 tasks completed** (1.1, 1.2, 2.1, 4.1, 4.2, 4.3).
This is the initial boundary/SMS/location slice, not the complete provider cleanup.

## Completed slices

### No implicit IP location or weather

- `core/utils/util.py:get_ip_info` is an inert compatibility shim returning `{}`.
  It does not import an HTTP client, consult retired cache data, log device IPs,
  or make a replacement geolocation request.
- `PromptManager` does not reuse retired location/weather caches or schedule
  automatic weather work. Existing template placeholders render absent context;
  configured dynamic context remains separate work, not implicitly approved.
- Focused offline tests: **7 passed** in Python 3.10.22 with networking disabled,
  covering public/private/IPv6/empty IPs, prompt rendering and connection context.

```sh
python -m pytest tests/core/utils/test_removed_location.py
```

### SMS and ordinary account flows

- Removed the Aliyun SMS adapter, Maven SDK and SDK-only Okio override. The only
  SMS implementation is non-network `UnavailableSmsService`.
- SMS send/recovery reject before CAPTCHA/code/rate-limit side effects; stale
  stored SMS codes cannot authorize recovery. A legacy mandatory-SMS registration
  flag fails explicitly rather than silently falling back to weaker verification.
- Retired `aliyun.sms.*` values remain inert in storage, are omitted from the
  editable settings list, and are rejected on save/update/direct setting writes.
  Enabling SMS is rejected until an approved replacement exists. Public settings
  report SMS unavailable. Forward migration of the legacy flag remains pending.
- Eight focused SMS/password/CAPTCHA tests plus four existing settings/security
  checks pass: **12/12**, with no database, Redis or provider connection.

```sh
mvn -DskipTests=false -Dtest=UnavailableSmsTest,SysParamsServiceImplTest,ShiroConfigTest test
```

### Compatible-provider endpoint boundary

- Python `config/service_policy.py` and Java `ApprovedServicePolicy` use exact
  reviewed cloud hosts/roles and explicit loopback origins. Unknown/LAN/public
  hosts, removed-service aliases, misleading authorities, URL credentials,
  sensitive AI query keys and insecure remote origins are rejected with redacted
  errors. Adding a deployment hostname requires a reviewed policy change.
- Applied to Python OpenAI-compatible ASR/LLM/VLLM/TTS and Ollama, and the Java
  compatible LLM service used for previews/summaries. Native vendor adapters,
  arbitrary tools/context/MCP and API write/restore paths remain separate work.
- These clients explicitly disable environment/system proxy fallback and redirects;
  TLS verification remains enabled. Unsupported vendor-specific thinking switches
  were removed from the generic LLM adapter. No new recipient is selected silently.
- Focused Python boundary/location suite: **46 passed**. Java boundary cases:
  **30 passed**, for **42/42** with the SMS/settings/security checks. Mock transports
  prove before-send rejection at these seams; they do not prove deployment-wide
  egress independence. Test containers had networking disabled as a second boundary.

```sh
python -m pytest tests/config/test_service_policy.py tests/core/utils/test_removed_location.py
mvn -DskipTests=false -Dtest=ApprovedServicePolicyTest,UnavailableSmsTest,SysParamsServiceImplTest,ShiroConfigTest test
```

Cloud role evidence: [OpenAI speech contract](https://developers.openai.com/api/docs/guides/speech-to-text)
and [Google's compatible endpoint](https://ai.google.dev/gemini-api/docs/openai).
This permits implementation/testing of the interface, not live paid use or a
child-data/legal compliance certification. Model choice and credentials remain
explicit deployment settings; independent compatible servers can use loopback.

### Build-source preparation (partial)

- Docker base dependency resolution now uses only official PyPI, with isolated
  pip configuration and no trusted-host/TLS bypass.
- Maven POM repositories/plugins use official Central. Checked-in `.mvn` settings
  also mirror transitive POM repository declarations to Central.
- Setup/Compose/CI image proxies, pinned inputs, clean-cache builds, SBOM and owned
  candidate images remain pending. No compliant-image claim is made from these edits.

## Regression checkpoint

- Python core/config subset after this slice: **115 passed, 1 skipped**. The
  skipped provider-factory module has an existing import-time configuration
  prerequisite; it is not called a pass. No live-provider flag was enabled.
- Expanded Java offline suite: **183 tests, 181 passed, 1 failed, 1 errored**.
  The two failures match the pre-change masking assertion and MyBatis lambda-cache
  defects recorded in the translation baseline. The focused new suites pass.
- Residual-language guard: zero unreviewed/stale entries. Three retired
  location/weather fallback exceptions were removed explicitly; Chinese locale
  dictionaries remain unchanged. All **118** historical/locale hashes still match.
- No wrapper/gateway edits, running-service restart, account/key import, paid
  request, deployment, commit or push was performed.

## Owner choices before optional replacements

The approved plan removes optional hosted integrations without choosing a new
paid operator. The user's replacement goal is recorded, but a specific SMS
operator/account remains an explicit choice; no SMS vendor will be selected or
contacted silently. Weather/news/search replacements likewise must not recover
their old network defaults. Remaining safe implementation work is the catalog
and configuration migration, consistent API write/restore enforcement and the
provider/package removal, followed by independent build/egress proofs.

## Remaining gates

Provider/catalog policy, AI adapter cleanup, SMS/tools, forward migration,
independent builds and externally observed egress proofs remain pending unless
separately recorded below. No paid provider, key, account or live cutover is
selected by this source-only work. Optional services without an approved
replacement must report unavailable, never silently forward family data.

## Superseding checkpoint: 2026-10-21

The sections above preserve the first implementation slice as historical
evidence; their pending statements are not the current completion list. See
[candidate validation](service-candidate-validation.md), the updated
[replacement/trace matrix](service-replacement-matrix.md), and the OpenSpec task
file for current state.

Implemented since that slice: restricted AI adapter/dependency profile, explicit
startup readiness, consistent Java/Python create/load/selection/restore/runtime
boundaries, retained optional tool/MCP/context checks, removed advertisements and
stale-call results, forward-only idempotent catalog remediation/cache handling,
official build-source cleanup, pinned Python/npm inputs and source-built owned
images. No saved credential was routed to a replacement provider automatically.
Fresh and two-family upgrade fixtures preserve identities/history/audio and the
old Liquibase ledger. The complete Python suite and expanded Java suite, web,
mobile and policy regressions are separately counted in the evidence report.

The user approved and the team prepared the sibling gateway changes and three
new parent candidate files. The isolated candidate uses only synthetic inputs,
new labelled resources and an internal network, leaving the evaluation stack
untouched. Authenticated WS and signed MQTT+UDP/AES managed turns plus both
post-disconnect titles passed against strict local fakes. The initial API run
exposed two baseline binding permission defects; after explicit user approval,
the service now checks agent ownership before device/cache access on both paths.
The new 14-test regression suite reproduced 11 failures before the patch and
passes completely afterward (22/22 including nearby device tests). A full fresh
API repeat passes 22/22 scenarios across 94 HTTP requests, including no forbidden
device insertion and subsequent owner use of the same activation code. Both
managed voice transports and both titles passed again with zero fake-contract
errors. The expanded Java suite passes 337/339; only the two documented baseline
masking/MyBatis defects remain. Candidate containers/network/synthetic volumes
are removed; the original services and data remain unchanged. OpenSpec is now
30/30, implemented and archived. The later [network/build checkpoint](service-network-and-locks.md)
completes production OS/Maven archive locking and externally observes startup,
the full API, both voice transports, title/memory persistence and removed-feature
paths through DNS plus syscalls and an exact namespace firewall. The initial
network gate exposed two pre-existing get_local_ip UDP probes to 8.8.8.8:80.
After explicit user approval, local interface discovery replaced the probe;
nine regressions and the 226-test Python suite pass (five known skips). A fresh
candidate with final locked images passes all functional and network gates,
with zero unapproved attempts or unexpected firewall drops. Tasks 7.1 and 7.5 are
complete after the approved CI fixture correction, passing regression/full-suite
repeat, and final three-capability review. The initial failing report is
retained as historical evidence. All synthetic resources/raw traces were removed and the original
services remain unchanged. The three main specs are synchronized and the change
is archived at `openspec/changes/archive/2026-10-21-remove-chinese-service-dependencies`.
No commit, push or live cutover occurred.
