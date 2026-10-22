# Java and OpenAPI translation verification

Executed on 2026-10-20 against source baseline
`eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b` and the translated worktree.
This checks compatibility; it does not certify a clean upstream test suite.

## Isolation

Both source trees were copied into disposable containers using
`maven:3.9.11-eclipse-temurin-21`, with `--network none`, a read-only root
filesystem/source mount and a temporary writable `/tmp`. Dependencies were
previously downloaded from official Maven Central into a temporary cache;
the source POM and its repository configuration were not changed. No existing
database, Redis instance, provider credentials or running service was used.
The separately described integration run used only disposable internal fixtures.

The source checkout includes the sibling `manager-web` tree because an existing
snapshot test reads its role configuration component. No frontend is executed
by these Java tests.

## Expanded offline suite

On **each** source tree: **146 tests, 144 passed, 1 failed, 1 errored**.
This includes one validation-only Springdoc test. The same two existing defects
occur before and after translation:

- `SensitiveDataUtilsTest.maskMiddle_keeps_four_at_each_end_for_long_strings`:
  expected `true`, received `false` (line 47).
- `CorrectWordFileServiceImplTest.getAllItemsByAgentId_returns_mapped_items_when_mappings_exist`:
  MyBatis-Plus cannot find the lambda cache for `CorrectWordItemEntity` (line 61).

They were neither suppressed nor fixed as part of translation. Maven correctly
returns failure. The two existing full-application test classes `DeviceTest`
and `loginControllerTest` are excluded from this offline run because they
require database/Redis application initialization; this result does not claim
those classes passed in the offline run; their separate integration result follows.

To reproduce with an already populated Maven cache inside the isolated copy,
copy [the validation harness](../../tools/OpenApiTranslationValidationTest.java)
to `src/test/java/translation/validation/OpenApiTranslationValidationTest.java`
and run:

```sh
mvn -o -B -ntp -s /settings.xml -Dmaven.repo.local=/cache \
  -DskipTests=false -Dtranslation.openapi.output=/artifacts/openapi.json \
  '-Dtest=*,!DeviceTest,!loginControllerTest' test
```

`/settings.xml` mirrors dependencies to official Maven Central. The test command
is offline; a missing cached dependency must be obtained separately, not by
enabling networking for the tests.

## Existing application integration tests

`DeviceTest` and `loginControllerTest` were also executed separately against fresh
MySQL schemas and a temporary Redis fixture: **5 tests passed on each source tree**.
The real application context initialized, including its unmodified Liquibase
history and startup services. Each source tree had its own empty database and
Redis database index. The containers used a dedicated internal Docker network
with no published ports or Internet access; MySQL data lived in tmpfs. No live
device or SMS/AI provider was invoked.

```sh
mvn -o -B -ntp -s /settings.xml -Dmaven.repo.local=/cache \
  -DskipTests=false -Dtest=DeviceTest,loginControllerTest test
```

Environment overrides redirected `SPRING_DATASOURCE_DRUID_URL`, username and
password to the disposable fixture and `SPRING_DATA_REDIS_HOST`/`DATABASE` to the
temporary Redis. Druid initial/minimum pool size was one. These overrides were
not saved in application configuration. The fixtures were removed after use.

## Generated OpenAPI

The harness starts Spring MVC/Springdoc with the project's actual controllers,
DTOs and `SwaggerConfig`, but registers controller instances without service
initialization. It calls only `/v3/api-docs` through MockMvc; it does not invoke
business endpoints, disable production authorization, or start a listening server.

Both descriptions contain **127 paths and 157 schemas**. The translated output
contains **1,202 English description/summary/title values** and **13 retained
Chinese multilingual examples**. Comparison permits documentation metadata,
tag labels and examples to change, while retaining route/property names,
operation IDs, required flags, defaults, enums and security declarations.

```sh
node tools/openapi-translation-check.mjs baseline-openapi.json translated-openapi.json
```

Result: **pass**, normalized contract SHA256:
`8dc93ac940af5c974e90d2ebe33e3695872c3e52011e473d4c8f046e13db8432`.
This is a generated-document contract check, not a claim of production endpoint
authorization or external-provider integration coverage.
