## 1. Baseline and explicit service inventory

- [x] 1.1 Record the implementation commit, owned edit roots, current image identities, applicable test commands and known pre-existing failures; do not restart the evaluation stack.
- [x] 1.2 Publish a path-level inventory of provider adapters/SDK imports and YAML/SQL presets, including operator evidence and remove/retain/review decisions for each integration named in the design.
- [x] 1.3 Trace the remaining specific network seams: Java previews/summaries/SMS, Python connection context/plugins, external memory/MCP/context URLs, model/download subprocesses, redirects and environment proxy settings; add their destinations to the inventory.
- [x] 1.4 Capture synthetic account/device/history/API/WS/MQTT fixtures and executed SQL/locale hashes; keep credentials and conversation bodies out of audit artifacts.

## 2. Service configuration validation

- [x] 2.1 Implement a small reviewed service/endpoint policy at existing Python provider and Java configuration seams; test allowed, removed, unknown, normalized/aliased and redirect destinations before secrets/data are sent.
- [x] 2.2 Apply validation consistently to YAML startup, API create/update/import, assistant/template selection, model previews, summary generation and snapshot restore; failed updates must preserve prior configuration.
- [x] 2.3 Apply destination validation to retained remote tool/context/MCP and external-memory requests; add redaction tests for rejected settings and errors.
- [x] 2.4 Test ordinary-user model/voice selectors against the permitted catalog, preserving ownership checks and keeping provider credentials server-side.

## 3. AI adapter and mandatory model cleanup

- [x] 3.1 Remove disallowed ASR adapters and unused service SDK imports; use the existing approved cloud-ASR seam with a local protocol-compatible test endpoint and verify startup without SenseVoice files.
- [x] 3.2 Remove disallowed LLM/VLLM and intent presets/vendor branches; retain generic interfaces and test that compatible custom base URLs cannot reactivate removed services.
- [x] 3.3 Remove disallowed TTS adapters and voice presets; verify retained TTS framing/voice selection with deterministic local audio fixtures.
- [x] 3.4 Review memory backends for remote operator dependencies; remove disallowed integrations while preserving independent no-memory/report-only paths and stored memory data.
- [x] 3.5 Prune unused Python packages/eager plugin imports, disable model auto-downloads and add actionable readiness checks; verify supported providers do not import removed SDKs.

## 4. SMS and optional tool/context cleanup

- [x] 4.1 Remove Aliyun SMS client/Maven dependency/settings; provide an unavailable SMS path compatible with dependency injection and guard SMS-only registration/recovery before verification-code side effects.
- [x] 4.2 Verify password registration/login, local CAPTCHA and existing non-SMS flows with the SMS feature disabled; do not weaken password recovery or add a vendor.
- [x] 4.3 Remove automatic PConline IP lookup and its prompt/context assumptions; test absent location on device connection without outbound attempts or retry loops.
- [x] 4.4 Remove disallowed weather/news/search plugin implementations/defaults and all active advertisement/schema references; test stale calls return unavailable while time/exit/device tools still work.

## 5. Forward-only data and compatibility migration

- [x] 5.1 Add migration tests for both a fresh database and an existing synthetic database with removed providers, templates, voices, plugin settings and historical snapshots.
- [x] 5.2 Add forward-only catalog/config migration with explicit unavailable legacy references and redacted remediation reporting; preserve IDs/history/audio references and old Liquibase bytes/checksums.
- [x] 5.3 Invalidate configuration caches through a controlled upgrade path; verify repeated upgrade and approved replacement preserve user choices and do not resurrect removed entries.
- [x] 5.4 Test two-user authorization and legacy API/device/WS/gateway fixture compatibility, including rejection on restore/import of removed integrations.

## 6. Independent builds and coordinated deployment artifacts

- [x] 6.1 Replace Aliyun Python/Maven/plugin repositories and backend image proxies in Dockerfiles, CI, supported setup scripts and examples with reviewed official sources; retain TLS verification.
- [x] 6.2 Produce pinned dependency inputs, a dependency/SBOM record and owned backend images from clean caches; verify no mandatory local-model download or upstream prebuilt-image assumption remains.
- [x] 6.3 Prepare and review the exact parent-wrapper/gateway diff and owned edit roots before applying it: replace image references, remove mandatory SenseVoice mount/download, keep localhost exposure and coordinate service secrets without touching production keys.
- [x] 6.4 With explicit scope approval, rehearse coordinated wrapper/gateway builds on separate ports/volumes and verify direct WS plus MQTT/UDP voice framing with local AI fakes. Keep the original evaluation deployment intact.

## 7. Runtime proof and handoff

- [x] 7.1 Build the external DNS/egress test harness and run startup, account/CAPTCHA, binding, provider changes, both transport turns, history/summary, snapshot restore and removed-feature scenarios; fail even blocked disallowed/unknown attempts.
- [x] 7.2 Run focused Python tests in addition to the existing smoke target, Java tests, management-web unit tests and relevant mobile selector tests; separate pre-existing failures and untested paths from new regressions.
- [x] 7.3 Add CI gates for SDK/dependency/preset/endpoint/mirror reintroduction and narrow inert-history/doc exceptions; verify a deliberately reintroduced fixture makes the gate fail.
- [x] 7.4 Publish the observed destination report, removed-feature matrix, configuration/backup/upgrade/rollback instructions and real-provider selection gate. No paid calls or live cutover without explicit approval.
- [x] 7.5 Review the three capability specs against evidence and obtain approval before declaring the service-removal change implemented; record the user-selected translation-first order and preserve its completed verification snapshot.

## Historical implementation checkpoint (2026-10-21, before final review)

29/30 tasks are complete. The supported profile, configuration boundaries,
forward migration, focused regressions and candidate artifacts are implemented.
With explicit user approval, both pre-existing device-binding permission defects
were fixed at the service boundary. The fresh API rerun passes 22/22 scenarios
(94 HTTP requests), and both managed transports pass again. The focused device
slice passes 22/22; the expanded Java suite has only its two recorded baseline
defects (337/339 pass).
Production Linux ARM64 OS/Maven inputs are now hash-locked before offline
installation/build; locked images preserve component identities. The full
application scenario matrix was externally observed through startup tracing,
nonforwarding DNS and an exact namespace firewall. Its initial failure exposed
two pre-existing UDP connects to 8.8.8.8:80 in get_local_ip(). With explicit user
approval, local interface discovery replaced that probe; nine regressions and
the full 226-test Python suite pass (five known skips). A fresh locked-image
candidate passes the complete API/voice/summary/removed-feature matrix with
zero unapproved attempts, DNS forwards/rejections or unexpected firewall drops.
Task 7.1 is complete; final review/owner acceptance remains open. See
service-dependency-lock-validation.json and service-network-validation.json.
See `docs/maintenance/service-removal-progress.md` and the replacement matrix for
exact scope, test outcomes and remaining gates. Existing runtime/data are untouched.
Optional paid replacements, including SMS, require an explicit operator choice;
none was silently provisioned or called.

## Historical final review checkpoint (2026-10-21, before CI correction)

The owner authorized final review and conditional closure without touching the
evaluation deployment, and selected sync-before-archive. That approval remains
conditional on a clean review; no main specs were written or change archived.

All 11 requirements and 14 scenarios in the three delta specs were reviewed
against their implementation boundaries and retained evidence:

| Capability | Review evidence and outcome |
| --- | --- |
| `approved-backend-services` | Exact-origin Java/Python policy, guarded clients with no redirect/proxy fallback, provider/config/selection/snapshot validation, server-side credentials, unavailable SMS/context/tools, and two-family API/voice/history evidence match the four requirements/six scenarios. No new runtime blocker found. |
| `compatible-service-migration` | Forward-only SQL and `ServicePolicyUpgrade`, cache invalidation ordering, fresh/two-family retry/replacement proof, preserved historical hashes, binding ownership guards, both transport contracts and matched-backup rollback instructions match the three requirements/four scenarios. No new migration/protocol blocker found. |
| `independent-backend-build` | Locked official-source builds, explicit local VAD/readiness, SBOM/component preservation, passing full DNS/egress observation and negative controls support the four requirements/four scenarios. The CI workflow reproduction below is a new final-verification blocker, not an exception accepted for closure. |

The 1,222 public source files match the previous passing Python/voice snapshot
byte-for-byte. All 19 build-input hashes, 16 fixture-code hashes and 118 protected
historical SQL/locale hashes match. Current policy self-tests, dependency-lock
tests (17), DNS fixture (7), report aggregation (6), build policy (14), npm lock
(7), English and strict OpenSpec validation pass. The previously recorded full
Python/Java/frontend/migration/network results remain scoped evidence, not newly
executed cloud calls or a blanket production/security certification.

### Blocking finding: Python CI configuration fixture

`.github/workflows/test.yml:54-57` creates `PYTEST_CONFIG_FILE` only under the
runner temporary directory, then collects `tests/config tests/core`. Import-time
logging still calls `config/settings.py:17-20`, which requires the separate
`data/.config.yaml` path. A clean public-source, network-disabled reproduction
fails while collecting `test_optional_service_policy.py` with
`FileNotFoundError: Cannot find data/.config.yaml`, before running tests.
This is introduced by the changed CI test selection/preparation, not one of the
two documented pre-existing Java failures.

A diagnostic positive control changed only disposable fixture preparation:
place the synthetic config at `data/.config.yaml` and point `PYTEST_CONFIG_FILE`
at that same file. The focused command then passes **140 tests, one known skip**.
Neither product code nor the repository workflow was changed by this review.
The narrow follow-up is to fix CI fixture preparation, add its regression proof,
and repeat that job before completing task 7.5. The passing runtime network
report is not invalidated; it used a correctly prepared isolated fixture.

The evaluation services retain their container/image/start identities and all
five remain healthy. No candidate resources were created beyond auto-removed,
network-disabled diagnostic containers. No real configuration, key or data was
used. Task 7.5 stays unchecked; do not sync/archive until the new blocker is fixed.

## Final acceptance and closure (2026-10-21)

The user explicitly authorized correcting only CI fixture preparation, adding
the regression, repeating verification and then syncing/archiving if it passed,
without changing the evaluation deployment. The recorded CI blocker is resolved;
all **30/30 tasks are complete** for this change's defined implementation scope.

The Python CI step now creates its synthetic `data/.config.yaml` and directs
`PYTEST_CONFIG_FILE` to the same path required by logging. Parent directories are
created, and exclusive creation rejects an existing configuration instead of
overwriting it. No runtime configuration loader, provider, migration or protocol
code was changed by this correction.

The new `SourceSurfaces.test_python_ci_prepares_the_config_required_by_logging`
executes the actual workflow preparation in an empty temporary directory. It
failed against the old workflow and now passes, including the no-overwrite check.
The build-policy suite passes **15/15**. A network-disabled public-source
container parsed and ran the actual updated YAML step: **140 passed, one known
skip**. The same fixture then passed the complete offline Python suite:
**226 passed, five known skips**. No live-provider flags or credentials were used.

Repeated policy self-tests, 17 dependency-lock tests, seven DNS-fixture tests,
six report-aggregation tests, seven npm-lock tests, English guards and strict
OpenSpec validation pass. All 1,222 public application source files still match
the reviewed runtime-test snapshot; the 19 build-input and 16 fixture hashes
match, so the passing full API/WS/MQTT/summary/DNS-egress evidence remains current
without rebuilding or restarting applications. Previous failed network evidence
and the two documented pre-existing Java failures remain visible; neither is
misrepresented as a new passing test or silently erased.

The review of all three capabilities (11 requirements, 14 scenarios) is accepted
for the defined supported profile. Their main specs were synchronized with the
reviewed delta content and validated before archive. The owner's translation-first
sequence and completed English verification snapshot remain unchanged, including
all 118 protected migration/locale hashes and the documented compiled-generator
exception. There are no remaining implementation blockers within this change.

Closure is not live-cutover approval, a real-provider/model-quality result, a
complete authorization audit or child-data/legal certification. Explicit provider
selection, real secrets, production model provenance, matched backups and a
separately authorized rollout remain deployment gates. The existing evaluation
services/configuration/data stay untouched. No commit, push or firmware operation
is included in this closure.
