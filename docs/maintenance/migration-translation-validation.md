# Migration translation verification

Verified on 2026-10-20 against baseline
`eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b` and the translated worktree.

## Results

- All **118 protected hashes** match the original source.
- All **108 immutable migration resources** remain byte-identical: master YAML
  and 107 SQL files. No migration was added or omitted.
- Fresh baseline and translated databases have identical schemas and seed data:
  **30 tables, 497 product seed rows and 107 migration checksums**.
- Both fresh runs execute 107 changesets and leave zero pending changes.
- Baseline-to-translated update leaves zero pending changes and preserves every
  row, schema and Liquibase ledger value exactly. Synthetic edits to one setting
  and one agent-template name/prompt (including localized text and placeholders)
  survive unchanged.
- Repeating the update is exactly idempotent.

Fresh comparisons fix the SQL session clock identically and exclude only
Liquibase's per-deployment `DATEEXECUTED` and `DEPLOYMENT_ID` metadata. Upgrade
comparisons exclude **no columns**, including those ledger fields. No SQL edits,
checksum resets, `changelogSync` or migration bypasses were used.

## Isolation and reproduction

Runtime: Java 21, Maven 3.9.11, Liquibase 4.20.0, MySQL Connector/J 9.1.0,
Spring Core 6.2.3 and MySQL 8.4.11. Maven resolution during execution is offline
against a private copy of the previously populated official-Central cache.

[The Python runner](../../tools/migration-translation-validation.py) extracts
baseline/current resources and compares snapshots from
[the Java harness](../../tools/migration-translation-validation.java). It requires
a caller-owned **internal** Docker network labelled
`xiaozhi.validation=migration-translation-20261020`, a disposable MySQL instance
aliased `migration-db`, and three empty fixture databases named
`migration_baseline`, `migration_current` and `migration_upgrade`. Its fixed
password `disposable-validation-only` is fixture-only, not a real credential.
No host ports or real database mounts are needed; the executed fixture used a
1 GiB tmpfs for MySQL storage.

```sh
python3 tools/migration-translation-validation.py \
  --network xiaozhi-migration-validation-20261020 \
  --cache /private/tmp/xiaozhi-translation-m2 \
  --settings /private/tmp/xiaozhi-maven-test-settings.xml
```

The harness uses `SpringResourceAccessor` and a matching Liquibase resource scope
for the unchanged `classpath:/db/changelog/db.changelog-master.yaml` entry point.
Initial harness-only XML/resource-resolution errors were corrected before the
successful proof; they were not migration defects.

This verifies the translation-only **no-op upgrade**, not an older application
version upgrade, the separate provider-removal change, or live application data.
No existing service, account, firmware or user-authored record was accessed.
