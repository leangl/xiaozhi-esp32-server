## Why

The owner needs to read and maintain the code and documentation directly in English. Chinese comments, technical diagnostics, annotations, templates, and instructions currently span all major applications, even though some English documentation already exists.

## What Changes

- Execution order amended by the user's 2026-10-20 request: apply translation first. `remove-chinese-service-dependencies` remains pending; translate existing maintained surfaces without removing integrations or asserting service independence.
- Translate maintained comments/docstrings, developer documentation, OpenAPI descriptions, configuration explanations, technical logs/errors, test descriptions, and non-localized instructional strings into English without changing their intended semantics.
- Cover the Python engine, Java API, web/mobile source, digital-human tools, scripts/build files, and first-party docs. This does not port the mobile framework.
- Preserve Chinese locale dictionaries, language identifiers, representative Chinese input/output fixtures, tokenizer/model assets, and language-specific spoken resources. Extract genuinely localized inline content into locale resources instead of deleting Chinese support.
- Translate internal identifiers/paths only where needed and safe; preserve public protocol keys, persisted identifiers, error codes, and extension names unless an explicit compatible alias/migration is documented.
- Preserve checksummed historical migrations and mandatory license/attribution text; supply complete linked English companion references for maintainer-facing Chinese material rather than corrupting history or legal notices.
- Provide a tracked coverage inventory, English glossary, readable diagram/screenshot equivalents, and a reasoned residual-text exception manifest with a CI check.

## Capabilities

### New Capabilities

None. This change is documentation/readability and behavior-preserving translation/refactoring, not a new product capability. `.openspec.yaml` declares `skip_specs: true`; acceptance criteria live in the design and tasks rather than artificial functional delta specs.

### Modified Capabilities

None. API/firmware/data contracts, locale behavior, and supported feature semantics must remain compatible.

## Impact

The maintained first-party repository, including modules that are downloaded but not currently deployed. The separately checked-out parent MQTT gateway is explicitly inventoried and translated in a coordinated follow-up slice within the implementation scope once that repository is authorized for editing. Generated files are regenerated from translated sources; third-party vendored contents and binary models are not rewritten.

No running deployment changes, account creation, paid service usage, framework migration, provider replacement, or firmware changes are authorized by this planning workflow.
