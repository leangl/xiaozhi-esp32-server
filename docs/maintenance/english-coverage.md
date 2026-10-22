# English translation coverage

This report is the completed **pre-service-removal translation snapshot**. Later
authorized functional changes are tracked in [service-removal progress](service-removal-progress.md).
The private pre-change archive/hash there preserves that snapshot; translation
structure-only comparison tools must not misclassify intentional provider removal
as a translation regression. The residual-language and historical-hash guards
remain applicable to subsequent changes.

Status: **translation implemented; planned verification executed, baseline defects documented**.
Both exact residual-text gates pass with zero unexplained lines and zero stale
exceptions. This is not a claim that every integration/build has been tested or
that runtime dependencies have been removed. All 29 OpenSpec tasks are recorded
as executed; the change awaits review and has not been archived or deployed.

The user selected translation first on 2026-10-20. Source baseline:
`eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b`. The service-independence change
remains pending. Existing services, provider configuration, firmware and running
containers are not changed by this work.

## Inventory and protected data

- [Machine-readable per-file inventory](english-inventory.json) records every
  tracked/new first-party path, module, binary classification and residual
  Chinese line/hash without reproducing complete source strings.
- [Original baseline](english-baseline.json) records the initial module counts
  and SHA256 hashes of 118 historical migration/Chinese locale files.
- [Terminology](english-glossary.md) defines consistent English names.
- English SQL references are maintained under [migrations](migrations/).
- Any residual-text exceptions must be exact, explained and checked; the initial
  source inventory is **not** an exception allowlist.

| Area | Baseline files with Chinese text | Review status |
| --- | ---: | --- |
| Python voice server | 179 | Maintainer prose translated across core, providers, plugins, tests, config and benchmark tools; language/contract data explained |
| Java management API and resources | 412 | Source prose translated; 108 migration companions complete; compilation, generated API contract and isolated integration verified |
| Web management console | 130 | Maintained source prose translated; localized content preserved; compiled generator explicitly excluded by user |
| Mobile management console | 78 | Maintained source prose translated; locale/legal/configuration originals preserved with English notes |
| Digital-human test tools | 28 | First-party source/docs translated; 8 offline regression checks pass; vendor notices have English companions |
| Documentation | 37 | 35 Markdown files translated; 31 screenshots/diagrams reviewed with adjacent English explanations |
| Root/build/GitHub files | 10 | Comments/help translated; original author attribution preserved |

The separate MQTT gateway was explicitly added by the user on 2026-10-20.
Its maintained source/docs are translated and its seven offline differential
checks pass; see [gateway scope](gateway-scope.md). No gateway service was restarted.
The upstream manifest has 1,396 exact reviewed exceptions; the gateway has 15
source-line exceptions. These include unchanged historical/locale data, language
fixtures, legal/vendor originals, proper names, exact compatibility literals,
asset aliases and the one user-approved compiled generator bundle. No maintained
source directory has a blanket exemption.

The compiled `main/manager-web/public/generator/assets/index-Guo1hQ-y.js`
has no rebuild source in this checkout. The user explicitly approved keeping it
unchanged. Its exact content hash and English reading notes are in the reviewed
exception manifest; this is not an exemption for maintained application source.

## Verification baseline

- Mobile Node snapshot/voice/device tests: **20 passed** before translation.
- Web Node snapshot/API/contract tests: **22 passed** before translation.
- Host Python has no `pytest`; Python suites were subsequently compared in isolated containers below.
- Host Maven is unavailable; Java suites were subsequently compared in isolated containers below.
- Native mobile packages: not built; no DCloud account or signing operation.

## Checks executed during implementation

- Isolated Python 3.10.22 unit subset: 69 passed, 1 skipped on both HEAD and
  translated source. Runs used temporary source copies, empty configuration,
  pytest 8.4.2, pytest-asyncio 0.26.0 and freezegun 1.5.5, with networking disabled.
  This is not a paid-provider/live test.
- Full isolated Python suite: **84 passed, 5 skipped, 1 failed** on both HEAD and
  translated source. The same pre-existing Edge TTS test attempts a real Bing
  speech connection despite mock mode; the container's disabled network blocks
  it. No network was enabled to make that test pass.
- Web Node snapshot/API/contract tests: 27 passed, including 5 new translation
  contract checks. Agent syntax review covered 109 JavaScript/Vue script blocks.
- Full web Vitest: 52 passed and the same one timezone-sensitive date assertion
  failed on both source trees in Buenos Aires time; all 53 passed on both in UTC.
  Production builds pass on both after reviewed `v-code-diff` dependency
  initialization, with the same four warning categories. No product code or lock
  changed for validation. See [frontend verification](frontend-translation-validation.md).
- Mobile snapshot/voice/device tests: 20 passed; syntax checks covered 86 modules.
  H5 builds and post-generation type-checks pass on both source trees. Fresh-copy
  type-check first reports the same 42 missing auto-import declarations; building
  generates identical declarations and resolves them. Polling avoids the shared
  host watcher `EMFILE` limit. No native/signing/DCloud build is claimed.
- Digital-human offline regression checks: 8 passed, including JS/inline syntax,
  Python structure, queue/config behavior, DOM IDs, interpolation and fixtures.
- Java token review: 295 changed Java files, 1,598 changed strings, no non-string
  token or placeholder changes. Eleven flagged string sites were reviewed
  individually as descriptions, examples, test labels or fallback prompt values.
- Java compilation: **316 application files and 23 test files compile** with
  Maven 3.9.11/JDK 21 in temporary containers. Expanded offline Java tests:
  **144 passed, 1 failed, 1 errored** on both HEAD and translated source, including
  the validation-only Springdoc test. The same original defects are the
  `SensitiveDataUtilsTest` long-string masking assertion and the
  `CorrectWordFileServiceImplTest` missing MyBatis lambda cache. Separately,
  **all 5 existing application integration tests pass** on both source trees
  with fresh internal MySQL/Redis fixtures. See [Java verification](java-translation-validation.md).
- Generated Springdoc descriptions: 127 paths and 157 schemas on both versions;
  normalized API contracts match. All 1,202 descriptive values are English and
  13 multilingual examples are retained. No business endpoint was invoked by
  the OpenAPI harness; it does not replace authorization testing.
- Gateway post-translation offline checks: **7 passed**. They do not start the
  bridge or read live configuration. Token review preserves 11,200 tokens except
  99 diagnostic prose parts; the 15 Chinese wire/speech lines remain unchanged.
- Seven changed YAML files parse and preserve key/non-text-default structure.
- All 118 protected hashes remain unchanged. Fresh baseline/current migrations
  produce identical schemas, 497 seed rows and 107 migration checksums; no-op
  upgrade and repeated upgrade preserve exact synthetic user edits and ledger
  fields. See [migration verification](migration-translation-validation.md).
  No native build or paid-provider integration run is claimed.
- English coverage checks are configured in read-only GitHub Actions workflows
  in both repositories. Their CLI checks passed locally; no remote CI run,
  staging, commit, push or deployment was performed.

## Verification limitations and review handoff

- No translation-specific regression was found in the executed comparisons.
  This is **not** an all-green upstream suite: the two Java defects, one
  network-dependent Python test and one local-timezone web assertion remain
  explicitly reported. Fixing those existing defects is separate work.
- Mobile H5 and generated types were tested, not native Android/iOS packaging.
  No mobile `prepare` hook, account creation or signing was used.
- Live AI/voice provider behavior, model semantic quality and production
  authorization were not exercised by this translation validation.
- Disposable MySQL/Redis containers and their internal test network were removed
  after verification. Existing services and data remain untouched. Source
  changes are uncommitted; review/acceptance, archival and deployment are separate.

## Commands

```sh
node tools/english-audit.mjs scan
node tools/english-audit.mjs check-protected
node tools/english-audit.mjs self-test
# Fails while any non-exempt technical prose remains:
node tools/english-audit.mjs check
python3 tools/translation-compatibility.py
python3 tools/translation-contracts.py
node tools/java-translation-check.mjs --self-test
node tools/java-translation-check.mjs --summary
node --test tools/digital-human-translation.test.mjs
node --test tools/gateway-translation.test.mjs
node tools/gateway-english-audit.mjs --self-test
node tools/gateway-english-audit.mjs
```

Binary diagrams/screenshots require a reviewed English equivalent or complete
adjacent English explanation; a successful text scan alone cannot certify them.
The coverage inventory for the upstream repository does not silently include the
separate gateway checkout; its scope and baseline are recorded independently.
