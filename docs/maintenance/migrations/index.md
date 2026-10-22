# Historical migration English companions

Documentation only. NOT executable migrations. Do not add these Markdown files to Liquibase, execute their excerpts, or replace the original SQL/changelog files. The translation leaves original bytes, locale data and user records unchanged.

## Scope and reading guide

This directory covers all **108 files** in `main/manager-api/src/main/resources/db/changelog/`: **107 SQL files and 1 master YAML file**. **104 files contain Chinese text**, on **2,226 source lines**; each has an explicit companion. The other **4 files have no Chinese text** and also have short companions. There are **0 unmapped sources** and **0 locale-only file exclusions**.

Use a source's companion for English comments, schema annotations, provider-form labels and seeded descriptions. The voice tables translate **288 catalog rows in 14 source files**. The firmware and telephone-region tables translate **54** and **38** dictionary rows. The source row IDs, field keys, voice/firmware codes, enum values, placeholders, endpoints and guards remain authoritative. Each companion records the source SHA-256 captured for this translation slice.

Provider setup procedures, prices, quotas, model recommendations and legal notices describe the historical seed. The translator did not verify them as current advice, call paid providers, deploy services, change permissions or execute migrations. Preserving descriptions of historical provider removals does not implement the separately pending service-removal change.

## Source-to-companion mapping

Paths in the first column point to immutable originals. “No Han text” means no Chinese translation was necessary, not a blanket exclusion. Source-line counts include mixed code/data lines.

| Source migration/changelog | English companion | Han-text source lines | Coverage |
| --- | --- | --- | --- |
| [202503141335.sql](../../../main/manager-api/src/main/resources/db/changelog/202503141335.sql) | [202503141335.sql.md](202503141335.sql.md) | 48 | English companion |
| [202503141346.sql](../../../main/manager-api/src/main/resources/db/changelog/202503141346.sql) | [202503141346.sql.md](202503141346.sql.md) | 150 | English companion |
| [202504082211.sql](../../../main/manager-api/src/main/resources/db/changelog/202504082211.sql) | [202504082211.sql.md](202504082211.sql.md) | 42 | English companion |
| [202504092335.sql](../../../main/manager-api/src/main/resources/db/changelog/202504092335.sql) | [202504092335.sql.md](202504092335.sql.md) | 69 | English companion |
| [202504112044.sql](../../../main/manager-api/src/main/resources/db/changelog/202504112044.sql) | [202504112044.sql.md](202504112044.sql.md) | 43 | English companion |
| [202504112058.sql](../../../main/manager-api/src/main/resources/db/changelog/202504112058.sql) | [202504112058.sql.md](202504112058.sql.md) | 43 | English companion |
| [202504151206.sql](../../../main/manager-api/src/main/resources/db/changelog/202504151206.sql) | [202504151206.sql.md](202504151206.sql.md) | 19 | English companion |
| [202504181536.sql](../../../main/manager-api/src/main/resources/db/changelog/202504181536.sql) | [202504181536.sql.md](202504181536.sql.md) | 4 | English companion |
| [202504221135.sql](../../../main/manager-api/src/main/resources/db/changelog/202504221135.sql) | [202504221135.sql.md](202504221135.sql.md) | 47 | English companion |
| [202504221555.sql](../../../main/manager-api/src/main/resources/db/changelog/202504221555.sql) | [202504221555.sql.md](202504221555.sql.md) | 49 | English companion |
| [202504251422.sql](../../../main/manager-api/src/main/resources/db/changelog/202504251422.sql) | [202504251422.sql.md](202504251422.sql.md) | 16 | English companion |
| [202504291043.sql](../../../main/manager-api/src/main/resources/db/changelog/202504291043.sql) | [202504291043.sql.md](202504291043.sql.md) | 373 | English companion |
| [202504301341.sql](../../../main/manager-api/src/main/resources/db/changelog/202504301341.sql) | [202504301341.sql.md](202504301341.sql.md) | 48 | English companion |
| [202505022134.sql](../../../main/manager-api/src/main/resources/db/changelog/202505022134.sql) | [202505022134.sql.md](202505022134.sql.md) | 14 | English companion |
| [202505081146.sql](../../../main/manager-api/src/main/resources/db/changelog/202505081146.sql) | [202505081146.sql.md](202505081146.sql.md) | 26 | English companion |
| [202505091555.sql](../../../main/manager-api/src/main/resources/db/changelog/202505091555.sql) | [202505091555.sql.md](202505091555.sql.md) | 18 | English companion |
| [202505111914.sql](../../../main/manager-api/src/main/resources/db/changelog/202505111914.sql) | [202505111914.sql.md](202505111914.sql.md) | 3 | English companion |
| [202505122348.sql](../../../main/manager-api/src/main/resources/db/changelog/202505122348.sql) | [202505122348.sql.md](202505122348.sql.md) | 3 | English companion |
| [202505142037.sql](../../../main/manager-api/src/main/resources/db/changelog/202505142037.sql) | [202505142037.sql.md](202505142037.sql.md) | 4 | English companion |
| [202505151451.sql](../../../main/manager-api/src/main/resources/db/changelog/202505151451.sql) | [202505151451.sql.md](202505151451.sql.md) | 13 | English companion |
| [202505182234.sql](../../../main/manager-api/src/main/resources/db/changelog/202505182234.sql) | [202505182234.sql.md](202505182234.sql.md) | 53 | English companion |
| [202505201744.sql](../../../main/manager-api/src/main/resources/db/changelog/202505201744.sql) | [202505201744.sql.md](202505201744.sql.md) | 1 | English companion |
| [202505271414.sql](../../../main/manager-api/src/main/resources/db/changelog/202505271414.sql) | [202505271414.sql.md](202505271414.sql.md) | 39 | English companion |
| [202505292203.sql](../../../main/manager-api/src/main/resources/db/changelog/202505292203.sql) | [202505292203.sql.md](202505292203.sql.md) | 35 | English companion |
| [202506010920.sql](../../../main/manager-api/src/main/resources/db/changelog/202506010920.sql) | [202506010920.sql.md](202506010920.sql.md) | 16 | English companion |
| [202506031639.sql](../../../main/manager-api/src/main/resources/db/changelog/202506031639.sql) | [202506031639.sql.md](202506031639.sql.md) | 31 | English companion |
| [202506032232.sql](../../../main/manager-api/src/main/resources/db/changelog/202506032232.sql) | [202506032232.sql.md](202506032232.sql.md) | 8 | English companion |
| [202506051538.sql](../../../main/manager-api/src/main/resources/db/changelog/202506051538.sql) | [202506051538.sql.md](202506051538.sql.md) | 10 | English companion |
| [202506080955.sql](../../../main/manager-api/src/main/resources/db/changelog/202506080955.sql) | [202506080955.sql.md](202506080955.sql.md) | 2 | English companion |
| [202506091720.sql](../../../main/manager-api/src/main/resources/db/changelog/202506091720.sql) | [202506091720.sql.md](202506091720.sql.md) | 2 | English companion |
| [202506161101.sql](../../../main/manager-api/src/main/resources/db/changelog/202506161101.sql) | [202506161101.sql.md](202506161101.sql.md) | 0 | No Han text; documented |
| [202506191643.sql](../../../main/manager-api/src/main/resources/db/changelog/202506191643.sql) | [202506191643.sql.md](202506191643.sql.md) | 14 | English companion |
| [202506251620.sql](../../../main/manager-api/src/main/resources/db/changelog/202506251620.sql) | [202506251620.sql.md](202506251620.sql.md) | 4 | English companion |
| [202506261637.sql](../../../main/manager-api/src/main/resources/db/changelog/202506261637.sql) | [202506261637.sql.md](202506261637.sql.md) | 1 | English companion |
| [202507031602.sql](../../../main/manager-api/src/main/resources/db/changelog/202507031602.sql) | [202507031602.sql.md](202507031602.sql.md) | 2 | English companion |
| [202507041018.sql](../../../main/manager-api/src/main/resources/db/changelog/202507041018.sql) | [202507041018.sql.md](202507041018.sql.md) | 9 | English companion |
| [202507071130.sql](../../../main/manager-api/src/main/resources/db/changelog/202507071130.sql) | [202507071130.sql.md](202507071130.sql.md) | 18 | English companion |
| [202507071530.sql](../../../main/manager-api/src/main/resources/db/changelog/202507071530.sql) | [202507071530.sql.md](202507071530.sql.md) | 46 | English companion |
| [202507081646.sql](../../../main/manager-api/src/main/resources/db/changelog/202507081646.sql) | [202507081646.sql.md](202507081646.sql.md) | 2 | English companion |
| [202507101203.sql](../../../main/manager-api/src/main/resources/db/changelog/202507101203.sql) | [202507101203.sql.md](202507101203.sql.md) | 22 | English companion |
| [202508081701.sql](../../../main/manager-api/src/main/resources/db/changelog/202508081701.sql) | [202508081701.sql.md](202508081701.sql.md) | 22 | English companion |
| [202508111734.sql](../../../main/manager-api/src/main/resources/db/changelog/202508111734.sql) | [202508111734.sql.md](202508111734.sql.md) | 11 | English companion |
| [202508131557.sql](../../../main/manager-api/src/main/resources/db/changelog/202508131557.sql) | [202508131557.sql.md](202508131557.sql.md) | 11 | English companion |
| [202508271113.sql](../../../main/manager-api/src/main/resources/db/changelog/202508271113.sql) | [202508271113.sql.md](202508271113.sql.md) | 16 | English companion |
| [202509051745.sql](../../../main/manager-api/src/main/resources/db/changelog/202509051745.sql) | [202509051745.sql.md](202509051745.sql.md) | 34 | English companion |
| [202509080922.sql](../../../main/manager-api/src/main/resources/db/changelog/202509080922.sql) | [202509080922.sql.md](202509080922.sql.md) | 3 | English companion |
| [202509081140.sql](../../../main/manager-api/src/main/resources/db/changelog/202509081140.sql) | [202509081140.sql.md](202509081140.sql.md) | 2 | English companion |
| [202509091042.sql](../../../main/manager-api/src/main/resources/db/changelog/202509091042.sql) | [202509091042.sql.md](202509091042.sql.md) | 4 | English companion |
| [202509091633.sql](../../../main/manager-api/src/main/resources/db/changelog/202509091633.sql) | [202509091633.sql.md](202509091633.sql.md) | 8 | English companion |
| [202509161610.sql](../../../main/manager-api/src/main/resources/db/changelog/202509161610.sql) | [202509161610.sql.md](202509161610.sql.md) | 1 | English companion |
| [202509161701.sql](../../../main/manager-api/src/main/resources/db/changelog/202509161701.sql) | [202509161701.sql.md](202509161701.sql.md) | 37 | English companion |
| [202509191545.sql](../../../main/manager-api/src/main/resources/db/changelog/202509191545.sql) | [202509191545.sql.md](202509191545.sql.md) | 29 | English companion |
| [202509220926.sql](../../../main/manager-api/src/main/resources/db/changelog/202509220926.sql) | [202509220926.sql.md](202509220926.sql.md) | 18 | English companion |
| [202509220958.sql](../../../main/manager-api/src/main/resources/db/changelog/202509220958.sql) | [202509220958.sql.md](202509220958.sql.md) | 14 | English companion |
| [202509221530.sql](../../../main/manager-api/src/main/resources/db/changelog/202509221530.sql) | [202509221530.sql.md](202509221530.sql.md) | 5 | English companion |
| [202510071522.sql](../../../main/manager-api/src/main/resources/db/changelog/202510071522.sql) | [202510071522.sql.md](202510071522.sql.md) | 12 | English companion |
| [202510191042.sql](../../../main/manager-api/src/main/resources/db/changelog/202510191042.sql) | [202510191042.sql.md](202510191042.sql.md) | 0 | No Han text; documented |
| [202510250956.sql](../../../main/manager-api/src/main/resources/db/changelog/202510250956.sql) | [202510250956.sql.md](202510250956.sql.md) | 10 | English companion |
| [202510251150.sql](../../../main/manager-api/src/main/resources/db/changelog/202510251150.sql) | [202510251150.sql.md](202510251150.sql.md) | 12 | English companion |
| [202511131023.sql](../../../main/manager-api/src/main/resources/db/changelog/202511131023.sql) | [202511131023.sql.md](202511131023.sql.md) | 18 | English companion |
| [202511221450.sql](../../../main/manager-api/src/main/resources/db/changelog/202511221450.sql) | [202511221450.sql.md](202511221450.sql.md) | 12 | English companion |
| [202512031517.sql](../../../main/manager-api/src/main/resources/db/changelog/202512031517.sql) | [202512031517.sql.md](202512031517.sql.md) | 3 | English companion |
| [202512041515.sql](../../../main/manager-api/src/main/resources/db/changelog/202512041515.sql) | [202512041515.sql.md](202512041515.sql.md) | 8 | English companion |
| [202512131453.sql](../../../main/manager-api/src/main/resources/db/changelog/202512131453.sql) | [202512131453.sql.md](202512131453.sql.md) | 3 | English companion |
| [202512161529.sql](../../../main/manager-api/src/main/resources/db/changelog/202512161529.sql) | [202512161529.sql.md](202512161529.sql.md) | 1 | English companion |
| [202512192245.sql](../../../main/manager-api/src/main/resources/db/changelog/202512192245.sql) | [202512192245.sql.md](202512192245.sql.md) | 1 | English companion |
| [202512221117.sql](../../../main/manager-api/src/main/resources/db/changelog/202512221117.sql) | [202512221117.sql.md](202512221117.sql.md) | 3 | English companion |
| [202512301430.sql](../../../main/manager-api/src/main/resources/db/changelog/202512301430.sql) | [202512301430.sql.md](202512301430.sql.md) | 52 | English companion |
| [202601051433.sql](../../../main/manager-api/src/main/resources/db/changelog/202601051433.sql) | [202601051433.sql.md](202601051433.sql.md) | 9 | English companion |
| [202601141645.sql](../../../main/manager-api/src/main/resources/db/changelog/202601141645.sql) | [202601141645.sql.md](202601141645.sql.md) | 3 | English companion |
| [202601231530.sql](../../../main/manager-api/src/main/resources/db/changelog/202601231530.sql) | [202601231530.sql.md](202601231530.sql.md) | 39 | English companion |
| [202601261730.sql](../../../main/manager-api/src/main/resources/db/changelog/202601261730.sql) | [202601261730.sql.md](202601261730.sql.md) | 1 | English companion |
| [202602021555.sql](../../../main/manager-api/src/main/resources/db/changelog/202602021555.sql) | [202602021555.sql.md](202602021555.sql.md) | 1 | English companion |
| [202602051017.sql](../../../main/manager-api/src/main/resources/db/changelog/202602051017.sql) | [202602051017.sql.md](202602051017.sql.md) | 67 | English companion |
| [202602051125.sql](../../../main/manager-api/src/main/resources/db/changelog/202602051125.sql) | [202602051125.sql.md](202602051125.sql.md) | 1 | English companion |
| [202602061650.sql](../../../main/manager-api/src/main/resources/db/changelog/202602061650.sql) | [202602061650.sql.md](202602061650.sql.md) | 20 | English companion |
| [202602271137.sql](../../../main/manager-api/src/main/resources/db/changelog/202602271137.sql) | [202602271137.sql.md](202602271137.sql.md) | 29 | English companion |
| [202602281000.sql](../../../main/manager-api/src/main/resources/db/changelog/202602281000.sql) | [202602281000.sql.md](202602281000.sql.md) | 19 | English companion |
| [202603091051.sql](../../../main/manager-api/src/main/resources/db/changelog/202603091051.sql) | [202603091051.sql.md](202603091051.sql.md) | 3 | English companion |
| [202603101723.sql](../../../main/manager-api/src/main/resources/db/changelog/202603101723.sql) | [202603101723.sql.md](202603101723.sql.md) | 2 | English companion |
| [202603111131.sql](../../../main/manager-api/src/main/resources/db/changelog/202603111131.sql) | [202603111131.sql.md](202603111131.sql.md) | 36 | English companion |
| [202603231037.sql](../../../main/manager-api/src/main/resources/db/changelog/202603231037.sql) | [202603231037.sql.md](202603231037.sql.md) | 3 | English companion |
| [202603311200.sql](../../../main/manager-api/src/main/resources/db/changelog/202603311200.sql) | [202603311200.sql.md](202603311200.sql.md) | 2 | English companion |
| [202604010930.sql](../../../main/manager-api/src/main/resources/db/changelog/202604010930.sql) | [202604010930.sql.md](202604010930.sql.md) | 5 | English companion |
| [202604011035.sql](../../../main/manager-api/src/main/resources/db/changelog/202604011035.sql) | [202604011035.sql.md](202604011035.sql.md) | 1 | English companion |
| [202604011545.sql](../../../main/manager-api/src/main/resources/db/changelog/202604011545.sql) | [202604011545.sql.md](202604011545.sql.md) | 9 | English companion |
| [202604161357.sql](../../../main/manager-api/src/main/resources/db/changelog/202604161357.sql) | [202604161357.sql.md](202604161357.sql.md) | 3 | English companion |
| [202604201719.sql](../../../main/manager-api/src/main/resources/db/changelog/202604201719.sql) | [202604201719.sql.md](202604201719.sql.md) | 67 | English companion |
| [202604211515.sql](../../../main/manager-api/src/main/resources/db/changelog/202604211515.sql) | [202604211515.sql.md](202604211515.sql.md) | 12 | English companion |
| [202604211700.sql](../../../main/manager-api/src/main/resources/db/changelog/202604211700.sql) | [202604211700.sql.md](202604211700.sql.md) | 22 | English companion |
| [202604300930.sql](../../../main/manager-api/src/main/resources/db/changelog/202604300930.sql) | [202604300930.sql.md](202604300930.sql.md) | 49 | English companion |
| [202605071037.sql](../../../main/manager-api/src/main/resources/db/changelog/202605071037.sql) | [202605071037.sql.md](202605071037.sql.md) | 2 | English companion |
| [202605071120.sql](../../../main/manager-api/src/main/resources/db/changelog/202605071120.sql) | [202605071120.sql.md](202605071120.sql.md) | 2 | English companion |
| [202605081008.sql](../../../main/manager-api/src/main/resources/db/changelog/202605081008.sql) | [202605081008.sql.md](202605081008.sql.md) | 3 | English companion |
| [202605121509.sql](../../../main/manager-api/src/main/resources/db/changelog/202605121509.sql) | [202605121509.sql.md](202605121509.sql.md) | 2 | English companion |
| [202605251426.sql](../../../main/manager-api/src/main/resources/db/changelog/202605251426.sql) | [202605251426.sql.md](202605251426.sql.md) | 13 | English companion |
| [202606231030.sql](../../../main/manager-api/src/main/resources/db/changelog/202606231030.sql) | [202606231030.sql.md](202606231030.sql.md) | 11 | English companion |
| [202606261131.sql](../../../main/manager-api/src/main/resources/db/changelog/202606261131.sql) | [202606261131.sql.md](202606261131.sql.md) | 38 | English companion |
| [202607011405.sql](../../../main/manager-api/src/main/resources/db/changelog/202607011405.sql) | [202607011405.sql.md](202607011405.sql.md) | 7 | English companion |
| [202607071530.sql](../../../main/manager-api/src/main/resources/db/changelog/202607071530.sql) | [202607071530.sql.md](202607071530.sql.md) | 12 | English companion |
| [202607101200.sql](../../../main/manager-api/src/main/resources/db/changelog/202607101200.sql) | [202607101200.sql.md](202607101200.sql.md) | 1 | English companion |
| [202607290930.sql](../../../main/manager-api/src/main/resources/db/changelog/202607290930.sql) | [202607290930.sql.md](202607290930.sql.md) | 8 | English companion |
| [202608061030.sql](../../../main/manager-api/src/main/resources/db/changelog/202608061030.sql) | [202608061030.sql.md](202608061030.sql.md) | 0 | No Han text; documented |
| [202608061800.sql](../../../main/manager-api/src/main/resources/db/changelog/202608061800.sql) | [202608061800.sql.md](202608061800.sql.md) | 4 | English companion |
| [202608131030.sql](../../../main/manager-api/src/main/resources/db/changelog/202608131030.sql) | [202608131030.sql.md](202608131030.sql.md) | 0 | No Han text; documented |
| [202609021000.sql](../../../main/manager-api/src/main/resources/db/changelog/202609021000.sql) | [202609021000.sql.md](202609021000.sql.md) | 18 | English companion |
| [202609172100.sql](../../../main/manager-api/src/main/resources/db/changelog/202609172100.sql) | [202609172100.sql.md](202609172100.sql.md) | 2 | English companion |
| [db.changelog-master.yaml](../../../main/manager-api/src/main/resources/db/changelog/db.changelog-master.yaml) | [db.changelog-master.yaml.md](db.changelog-master.yaml.md) | 3 | English companion |

## Exact retained-text categories

Original files retain their Chinese bytes because they belong to checksummed migration history. This is an immutability exception for each explicitly linked source above, not permission to omit its English meaning. The companions translate comments, DDL annotations, display labels, seed remarks and instructions. The following data/contract cases additionally need their original language or exact matching value:

| Source | Exact region/key | Reason and English explanation |
| --- | --- | --- |
| [202504092335.sql](202504092335.sql.md) | Lines 5–75, five `ai_agent_template` rows; names, `agent_code`, `system_prompt`, language label | Chinese persona/language data, with complete per-template explanations. Preserve slang, sound examples, quoted speech and `{{assistant_name}}`; do not change user-authored personas. |
| [202504112044.sql](202504112044.sql.md) | Line 35, `TTS_FishSpeech.config_json.reference_text` | Transcript aligned with reference speech audio; preserve the Chinese linguistic sample. The companion explains its meaning. |
| [202504112058.sql](202504112058.sql.md) | Line 39 `exit_commands`; line 51 `wakeup_words`; line 53 weather `default_location`; line 56 Home Assistant `devices` | Spoken commands/wake phrases, Guangzhou place name and Chinese device labels tied to fixed entity IDs; exact localized defaults remain unchanged. Surrounding technical remarks have English translations. |
| [202504151206.sql](202504151206.sql.md), [202504221135.sql](202504221135.sql.md), [202504221555.sql](202504221555.sql.md), [202505271414.sql](202505271414.sql.md), [202506051538.sql](202506051538.sql.md), [202507071530.sql](202507071530.sql.md), [202508081701.sql](202508081701.sql.md), [202508131557.sql](202508131557.sql.md), [202509051745.sql](202509051745.sql.md), [202509161701.sql](202509161701.sql.md), [202509191545.sql](202509191545.sql.md), [202604201719.sql](202604201719.sql.md), [202604300930.sql](202604300930.sql.md), [202606261131.sql](202606261131.sql.md) | Exact source lines and row IDs in each voice table; `name`, `languages`, `remark` | Localized catalog metadata/proper names. Every included voice row has an English descriptor/language/remark explanation; voice codes remain stable. This is not an exemption for prose descriptions. |
| [202504301341.sql](202504301341.sql.md) | Lines 32–85, firmware dictionary IDs 101001–101054; type ID 101 | Localized hardware/product names and repeated remarks paired with fixed firmware codes; the companion explains all 54 rows. |
| [202505142037.sql](202505142037.sql.md) | Line 1 persona REPLACE literals; line 5 `end_prompt.prompt` | Exact Chinese template-matching phrases and localized farewell prompt. The companion explains both instructions and persona wording changes. |
| [202505182234.sql](202505182234.sql.md) | Lines 28–65, telephone-region dictionary IDs 102001–102038 | Localized region labels/repeated remarks paired with dialing codes; all 38 English meanings appear in the companion. |
| [202506080955.sql](202506080955.sql.md) | Line 2 `wakeup_words` | Exact semicolon-delimited spoken wake phrases; preserve recognition behavior. |
| [202506251620.sql](202506251620.sql.md) | Line 14 `news_sources.default` | Chinese source names select The Paper, Baidu hot searches and Cailian Press; preserve provider-facing matching values. |
| [202509051745.sql](202509051745.sql.md) | Line 8 `pronunciation_dict.tone` | Chinese words paired with pinyin/English pronunciation examples; preserve pronunciation fixtures. |
| [202509220926.sql](202509220926.sql.md), [202509220958.sql](202509220958.sql.md) | Initial inserted `model_code` values | Persisted Chinese identifiers in historical seeds; later history normalizes them. Do not rename them in place. |
| [202511131023.sql](202511131023.sql.md) | Line 62 placeholder and `LIKE` literal | Exact Chinese “your api_key” sentinel limits an update to an untouched seed. Translation must not broaden that guard. |
| [202602021555.sql](202602021555.sql.md) | Line 1 `system_error_response.param_value` | Localized spoken error response; its maintainer-facing description has an English translation. |
| [202602061650.sql](202602061650.sql.md) | Lines 4–12, `ai_tts_voice.languages` CASE inputs/outputs | Exact stored language labels drive normalization. The companion explains each mapping without changing data. |
| [202608061800.sql](202608061800.sql.md) | Lines 12–16, remark REPLACE search/replacement literals | Exact historical remark text drives an update; preserve both old/new strings and the leading source BOM. The companion explains each phrase. |

Chinese credential placeholders elsewhere mean “your” corresponding credential. They remain in original immutable seeds only; they are not locale-data exemptions for maintainer instructions. Each relevant companion explains them. No real user prompt, conversation, credential, name or record needs translation updates.

## Verification and historical risks

Verification passed for 108 source SHA-256 values against the pre-edit capture, the 108-source/108-companion mapping, all 107 master SQL references, 464 local Markdown links and 2 explicit anchor references. Annotation checks found the English meaning for all 372 Chinese schema annotations and all 407 inline-JSON provider labels; the companions also explain SQL JSON_OBJECT labels in prose. No Han text, trailing whitespace or unbalanced fenced blocks remain in the 109 new Markdown files. No migration, database, container or paid-service tests run for this documentation-only slice.

Source inconsistencies remain visible: detached FunASR commands paired with “enter the container” prose; sentence-versus-character quota wording; copied VLLM/firmware comments on ASR/telephone data; `timber_weights` versus `timbre_weights`; a tag-order repair guard broader than its comment; flat PowerMem seeds versus nested examples; and the TTS JSON migration's removal of emotion keys without copying them. These are historical risks, not fixes included in translation.

The parent change still needs its repository-wide coverage/checksum integration and any authorized fresh/upgrade database proof. This directory neither edits OpenSpec tasks nor claims the whole translation or service-removal project is complete.
