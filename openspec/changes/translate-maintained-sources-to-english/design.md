## Context

User scope decisions on 2026-10-20: include the separate `../gateway` checkout
in a translation-only slice (no deployment); retain the bundled, source-unavailable
web generator unchanged as an exact hashed exception with English documentation.

See `proposal.md`. On 2026-10-20 the user selected this translation change first and authorized parallel subagents. The earlier service-removal prerequisite is waived by that explicit selection: the current source commit is the baseline, all currently maintained integrations remain in scope, and service removal remains separately pending. This is a behavior-preserving maintainability change and intentionally has `skip_specs: true`, not invented product delta requirements.

Observed surfaces:

- `main/xiaozhi-server`: Chinese docstrings/comments, tool schema descriptions, diagnostics and config explanations; `agent-base-prompt.txt` already mixes English instructions with Chinese examples and language-sensitive wording.
- `main/manager-api`: Chinese JavaDoc/OpenAPI annotations/error descriptions; immutable SQL changelog files also contain comments and seeded prose.
- `main/manager-web/src/i18n/{zh_CN,zh_TW}.js` and `main/manager-mobile/src/i18n/{zh_CN,zh_TW}.ts`: intentional locale resources; Java uses `resources/i18n/messages_zh_*.properties` and validation bundles.
- `main/manager-mobile`: developer prose mixed with `uni.*` API usage; translating the code does not remove that framework dependency.
- `main/digital-human`, root scripts/Dockerfiles/CI, `docs/Deployment*.md`, `docs/mqtt-gateway-integration.md`, and screenshot assets: substantial maintainer-facing prose. Existing `docs/readme/README_en.md` and `main/README_en.md` do not cover every guide.
- `../gateway` has independent Git history and Chinese diagnostics/comments; coordinate a separate authorized edit slice rather than treating it as tracked source in this repo.

## Goals / Non-Goals

**Goals:** an English-reading maintainer can understand every maintained module and follow supported setup/debugging instructions without translating Chinese manually; retain Chinese locale behavior and stable contracts.

**Non-Goals:** remove Chinese user language support; translate stored user conversations or personal prompts; rewrite dependencies/models; change product personas; port uni-app; redesign APIs; blindly replace all Han characters; rewrite Git history or applied migration checksums.

## Decisions

### 1. Inventory and translate by semantic category, not global replacement

Create `docs/maintenance/english-coverage.md`, a small terminology glossary, and a machine-readable exception manifest. Inventory Git-tracked first-party files by module, path and content category. Classify comments/docstrings, identifiers/paths, technical diagnostics, schemas, prompt instructions, fixtures, locale values, assets and immutable/legal records separately. Record translated/reviewed/exempt status and links to English companions.

Translate comments, documentation, test descriptions, OpenAPI summaries, YAML explanations, shell help and developer errors. Keep machine-readable codes/placeholders/regex/serialization schemas intact. If a Chinese human string is parsed by code or asserted by a client, first identify that contract; retain it as a documented compatibility literal/alias with an English explanation rather than silently breaking it. Internal naming can be translated with reference/import tests; no broad style cleanup.

Alternative rejected: replacing every Chinese string or using transliterated identifiers without translating meaning. Both miss semantic contracts and make review harder.

### 2. Preserve multilingual data with narrow exceptions

Keep Chinese translation values in the web/mobile dictionaries and Java `messages_zh_CN`, `messages_zh_TW`, `validation_zh_CN`, `validation_zh_TW` bundles. In mixed files such as i18n loaders, default bundles, tools, weekday maps and prompt templates, exempt only actual language data; translate surrounding instructions/comments. Treat Chinese input examples, speech recognition normalization, proper nouns, locale IDs, voice IDs and multilingual contract fixtures as language support, with English explanatory labels.

For hard-coded localized UI strings, move them to existing localization resources and add English values while retaining Chinese values, locale fallback and interpolation behavior. Do not switch all UI/device conversation languages to English merely to satisfy a text scan. Existing English prompt instructions with Chinese examples retain meaning and representative test coverage; no persona redesign or alteration of user-authored stored prompts.

### 3. Protect history and make English references complete

Applied Liquibase migration files remain byte-for-byte unchanged. Provide a mapped English companion reference under `docs/maintenance/migrations/` for each historical file containing maintainer-facing Chinese prose, including translated comments/seed descriptions and a warning that it is not executable migration input. A broad unexplained changelog exclusion does not satisfy readability. New migrations/comments use English; localizable seeded content remains in translation resources. Do not overwrite production/user-edited names or templates in a translation rollout.

Preserve required original license notices and attribution; add clearly labeled non-authoritative English explanations when needed without replacing legal originals. Preserve external identifiers/trademarks and explain them. Binary/vendor/model contents are not editable translation targets; any first-party guide depending on Chinese-only diagrams/screenshots gets an equivalent English diagram, annotated copy or complete adjacent explanation. Audit image/asset filenames and links for discoverability. Do not promise automatic OCR validation for arbitrary assets.

### 4. An English-first documentation entry point, not a pile of duplicate stale pages

Make the root README and supported developer/deployment/API/testing guides readable in English, consolidate overlapping English material, and provide a link map for renamed pages. Keep localized README variants only as optional locale content, not as a substitute for translating otherwise Chinese-only guides. All maintained docs (including optional modules) receive an English path; removed-vendor guides are explicitly retired and receive a concise English retirement/migration note rather than obsolete executable instructions.

### 5. Coverage is evidence, not a zero-Unicode quota

Add a repeatable scan of tracked textual content and tracked path names, including build/CI files. Scan output records each Han-text occurrence or bounded content region. Exceptions use exact paths/keys/literals or hashes, categories and English reasons; no `main/**`/`docs/**` catch-all. Legitimate locale files can use explicit per-file exceptions with surrounding code/comments separately reviewed. A new unexplained occurrence fails CI; obsolete exceptions also fail. Supplement scanning with review for English clarity and meaning; a scanner cannot prove translation quality.

Do not delete/update tests merely to erase Chinese. Preserve fixture semantics, JSON keys, formatter placeholders, message/command IDs, Unicode decoding, and supported language behavior. Historical migration bytes and locale fixture/dictionary snapshots are explicit acceptance checks. Generated OpenAPI/manifests are regenerated from source, not hand-edited.

## Risks / Trade-offs

- [Protocol literal mistaken for prose] → Inventory consumers, keep aliases/compatibility notes, and compare wire/data fixtures.
- [Translation changes prompts or tool semantics] → Preserve intent/constraints/placeholders; English and Chinese scenario review; no live AI calls needed for structural checks. Semantic model quality remains separately tested.
- [Historical SQL cannot be edited] → Complete linked English companion references, immutable checksum gate and fresh/upgrade schema tests.
- [Large diff hides unrelated changes] → Module-sized commits, glossary consistency and before/after verification; no mechanical reformatting.
- [Chinese-only screenshots remain inaccessible] → Asset inventory with reviewed English equivalent, not only a text-file scan.
- [Exceptions hide unfinished work] → Every residual category justified, scoped and reviewed; any untranslated non-exempt maintainer prose blocks completion.

## Migration Plan

1. Record the user-selected translation-first order, pin the current source baseline and inventory all existing first-party surfaces; do not claim the pending service-removal change is complete.
2. Capture migration/locale hashes and functional contract fixtures. Run existing checks before translation; record pre-existing failures rather than claiming a clean baseline.
3. Translate Python, Java, frontend/mobile/digital-human, scripts/config/CI and docs in independently verified slices. Add exact English companions for immutable files and update asset/link references.
4. Run Python tests, Java tests, web unit tests, mobile snapshot tests/type-check, JSON/YAML parsing, doc links, residual-text checks and wire/prompt/locale comparisons. A native mobile build remains subject to existing DCloud tooling; this change does not secretly provision it.
5. Coordinate the separate gateway translation slice with its own baseline and transport tests if authorized. Generate a final coverage report explicitly listing any excluded repository/surface.
6. Stop for review after source/docs validation. If a translated build is later deployed, retain prior artifacts and roll back only translated slices; there is no new DB migration to undo. Do not alter a separate service-removal slice, whether it is applied before or after this translation.

## Acceptance Checklist

- Every maintained first-party module/guide has English maintainer-facing prose or a complete linked English companion for a justified immutable original.
- No unexplained Chinese technical comments, diagnostics, internal identifiers, path names, or required documentation remain.
- Chinese locale dictionaries, Chinese-capable behavior and multilingual fixtures remain intact; any changes are reviewed extraction/normalization with equivalent values.
- API codes/keys, tool names, MQTT/WebSocket framing, persisted IDs, migration checksums and existing authorization remain unchanged.
- Coverage scanner and relevant module tests pass, or pre-existing failures are explicitly separated and accepted; untested surfaces are not called complete.
- No service configuration, user data, running container, paid provider or device is changed by the translation workflow without a later explicit deployment request.

## Open Questions

No architecture-blocking decisions remain. Individual ambiguous phrases and asset translations are reviewed against their call site/glossary while executing the relevant slice; uncertainty about a public contract requires retaining the compatible literal and documenting it, not guessing.
