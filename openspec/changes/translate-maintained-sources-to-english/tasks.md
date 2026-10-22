## 1. Dependency and coverage baseline

- [x] 1.1 Record the user-selected translation-first order (2026-10-20), pin current baseline `eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b`, and preserve the separately pending service-removal change.
- [x] 1.2 Create the tracked first-party text/path/asset inventory and `docs/maintenance/english-coverage.md`, with status for every maintained module and guide rather than a blanket directory exemption.
- [x] 1.3 Capture migration-file hashes, Chinese locale values, prompt placeholders, API/tool/error identifiers and WS/MQTT fixtures; run existing tests and record baseline failures before edits.
- [x] 1.4 Establish an English terminology glossary and exact residual-text exception categories for locales, multilingual fixtures, immutable history/legal text and compatibility literals.

## 2. Python voice engine and tools

- [x] 2.1 Translate comments/docstrings/developer diagnostics in connection, WebSocket/HTTP handlers and configuration/auth/cache code; compare import/compile tests and wire fixtures.
- [x] 2.2 Translate surviving ASR/LLM/TTS/memory/intent/tool provider prose and tests, preserving provider IDs, function names, argument schemas and placeholder formatting.
- [x] 2.3 Translate prompt/context/config instructions while retaining Chinese linguistic examples/weekday data and language-specific constraints as reviewed locale data; test template rendering and tool extraction.
- [x] 2.4 Translate surviving plugin descriptions and script/test instructions; keep multilingual test inputs and add English explanations rather than deleting those cases.

## 3. Java API and database readability

- [x] 3.1 Translate JavaDoc/comments/OpenAPI descriptions and internal diagnostics in security/user/device/config/model modules without changing codes, routes, SQL keys or access checks.
- [x] 3.2 Translate agent/history/memory/snapshot/tool and shared utility prose, plus test names and configuration comments; verify Java tests and generated API descriptions.
- [x] 3.3 Preserve historical Liquibase bytes and create complete linked English companion references for their Chinese comments/seed descriptions under `docs/maintenance/migrations/`.
- [x] 3.4 Translate maintainer-facing prose in new seeds/configuration while preserving locale bundles and user-authored stored data; verify fresh and upgrade migration checksums and data contracts.

## 4. Web, mobile and digital-human sources

- [x] 4.1 Translate web source comments, developer diagnostics, validation/help prose and tests; extract genuinely localized inline UI strings into existing locale dictionaries with English and Chinese values preserved.
- [x] 4.2 Translate mobile source/config/build comments, technical diagnostics and snapshot-test descriptions without porting uni-app or changing permission/network/auth semantics.
- [x] 4.3 Translate digital-human runtime/bridge/wake-word/configuration and test instructions, preserving language-specific model metadata and speech fixtures.
- [x] 4.4 Check web/mobile i18n loaders, Chinese dictionaries, Java default/Chinese bundles and language IDs against baseline; remove no language solely to satisfy the scan.

## 5. Documentation, scripts and first-party assets

- [x] 5.1 Make root/module README entry points, architecture/development guides and API explanations English-readable; consolidate existing English variants and provide redirects/link maps for moved pages.
- [x] 5.2 Translate every surviving deployment, configuration, testing, firmware-integration and troubleshooting guide; mark removed-provider guides retired with English migration notes instead of recommending obsolete integrations.
- [x] 5.3 Translate root/build/CI/setup script comments/help and configuration examples without changing their actions; verify shell syntax, JSON/YAML parsing and supported commands.
- [x] 5.4 Provide reviewed English equivalents or complete adjacent explanations for all required Chinese-only first-party screenshots/diagrams; update Chinese path names and references safely or document compatible aliases.
- [x] 5.5 Preserve required original license/attribution notices and external identifiers, adding linked non-authoritative English explanations where needed; do not modify vendored or model binaries.

## 6. Coverage guard and compatibility proof

- [x] 6.1 Implement a repeatable tracked-content/path Han-text scan with narrow reasoned exceptions and stale-exception detection; test intentional locale fixtures pass and a new Chinese technical comment fails.
- [x] 6.2 Run relevant Python suites, Java tests, web unit tests, mobile snapshot tests/type-check and digital-human import/config checks; document unavailable platform build tooling rather than claiming unrun native builds pass.
- [x] 6.3 Verify unchanged migration hashes, locale values/fallback/interpolation, protocol fixtures, tool/API identifiers and template constraints; review translations for meaning, not only scan success.
- [x] 6.4 Validate documentation links, English companion coverage, screenshots/diagrams and glossary consistency; fail completion on untranslated non-exempt maintainer prose.

## 7. Separate gateway seam and final review

- [x] 7.1 Prepare a path-level translation list for the separately checked-out `../gateway` and request/confirm that repository's edit scope before changing it; otherwise report the exclusion explicitly.
- [x] 7.2 When authorized, translate gateway comments/docs/diagnostics in its own change slice and run its baseline transport/authentication tests, preserving all MQTT/UDP/WS fields and framing.
- [x] 7.3 Publish the completed module/guide coverage report with exact residual exceptions, all executed/unexecuted checks and the English glossary; do not claim excluded surfaces are translated.
- [x] 7.4 Review the design acceptance checklist and hand off for approval. Keep deployment separate; rollback translation-only slices without reverting service independence or touching user data.

## Verification handoff (2026-10-20)

Maintained-source translation is implemented in upstream and the authorized
gateway checkout. Both exact residual-text guards pass with zero unexplained
lines and zero stale exceptions; all 118 protected hashes are unchanged.
The compiled generator is an explicit user-approved exception, not an omitted
maintained module. Runtime/provider removal remains a separate pending change.

All 29 planned tasks have now been executed. Generated OpenAPI contracts match
(127 paths, 157 schemas); all five existing Java integration tests pass on each
source tree. Fresh and no-op upgrade migration proofs preserve schemas, checksums,
seed data and synthetic user edits exactly. Web production builds and mobile H5
builds/post-generation type-checks pass on both trees. The same original Java,
Python and local-timezone web test failures remain explicitly documented; no
failure is called a pass or silently fixed. Native mobile packaging and live AI
behavior were not tested. See `docs/maintenance/english-coverage.md` and linked
validation reports for exact scopes and prerequisites. Temporary database/Redis
fixtures and their internal network were removed. No deployment, account, live AI
call, push or commit was performed. Ready for owner review; not auto-archived.
