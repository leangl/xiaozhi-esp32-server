## Context

Execution update (2026-10-20): the user completed English translation first and
now requested this implementation, preferring Western or free/self-hosted
equivalents. The pre-removal translated snapshot and first implementation slice
are recorded in `docs/maintenance/service-removal-progress.md`. A missing paid
operator/account is not permission to introduce a data recipient; the live
provider and optional-replacement choices below remain explicit gates.

See `proposal.md` for motivation and the three delta specs for behavioral contracts. Source baseline: `eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b`; the local wrapper uses independently published 0.9.7 images, not images rebuilt from this checkout.

Observed seams (source inspection, not a network or supply-chain certification):

| Surface | Evidence | Proposed treatment |
| --- | --- | --- |
| Python AI providers | `core/providers/{asr,tts,llm,memory}`; `requirements.txt` includes dashscope, baidu-aip, cozepy, modelscope, funasr, powermem | Remove disallowed remote adapters and unused service SDKs; keep compatible provider interfaces. Review external memory and shared dependency imports explicitly. |
| Provider defaults/catalog | `config.yaml`, `config_from_api.yaml`; `ConfigServiceImpl`; `db/changelog` model/template seeds | Clean file defaults and forward-migrate active DB catalogs/templates; validate at both API writes and runtime load. |
| SMS | `modules/sms/service/imp/ALiYunSmsService.java`; `CaptchaServiceImpl.sendSMSValidateCode`; Maven Aliyun SDK | Remove network adapter/SDK; retain a non-network unavailable implementation so account/password and local CAPTCHA are not coupled to SMS bean startup. |
| Hidden connection context | `core/utils/util.py:get_ip_info` calls `whois.pconline.com.cn`; prompt/context helpers consume it | Remove automatic lookup and propagate explicit unknown/absent location without repeated retries. |
| Optional tools | QWeather default host; NewsNow/ChinaNews; search defaults to metaso; plugin discovery imports local modules | Remove disallowed routes and plugin/prompt metadata, and test eager imports. Preserve independent time/exit/device tools. |
| Builds/downloads | `Dockerfile-server-base` Aliyun pip mirror/trusted-host; Maven repository/pluginRepository Aliyun; upstream Compose image proxy; setup/docs model URLs | Use approved package registries, TLS verification and pinned owned artifacts; no SenseVoice/ModelScope download required in approved cloud-ASR profile. |
| CI | Python CI runs only `tests/test_smoke.py`; Java tests and web unit tests exist | Add focused adapter/config/migration/network tests, not only the current smoke target. |
| Outside root | `../compose.yaml`, `../bootstrap.mjs`, `../gateway/` plus deployment/model files | Document a coordinated, separately scoped handoff; do not alter the current deployment during this work. |

The observed list is the starting inventory, not a claim that suffix-based URL search finds all providers. Custom endpoint config, seeded model JSON, JS/SMS integrations, external memory, remote MCP/context tools, redirects, environment proxies, URLs embedded in plugin data, and download subprocesses are specific remaining audit targets.

## Goals / Non-Goals

**Goals:** auditable service independence across the supported backend; reusable existing APIs/transports; fresh-build and runtime proof; no unapproved data recipient introduced by migration.

**Non-Goals:** no new cloud infrastructure or full outbound-proxy product; no mobile framework port; no complete library rewrite based on origin; no hardware/firmware changes; no deployment, data export, or paid/live calls in the planning turn. Chinese language support remains valid and is unrelated to provider location.

## Decisions

### 1. Use an evidence-based service inventory and explicit approval list

Create a maintained inventory recording integration ID, operator/control evidence URL and review date, active destinations/redirects, credentials, source/preset/import locations, build/runtime role, and disposition. Start with named Alibaba/Aliyun/DashScope/Bailian, Baidu, Tencent, ByteDance/Volcengine/Doubao/Coze, iFlytek, Zhipu/BigModel, DeepSeek, SiliconFlow, QWeather, Metaso, the observed news/IP services and mirrors. Review uncertain operators and hosted aggregators (including 302.ai, Fish Audio, hosted Dify/FastGPT, and external memory) explicitly; do not approve them by assuming a non-`.cn` domain is acceptable.

Normalize and validate configured service endpoints against the small approved inventory at the provider/configuration seams. Cover Python direct YAML and managed configuration, Java preview/summary/LLM paths, tool/context/MCP URLs and redirect targets. Reject removed/unknown active destinations before use; credentials stay server-side. A factual link in documentation is not executable configuration. Avoid introducing a general multi-cloud policy service or an unaudited bypass flag.

Alternative rejected: deleting only vendor-named files or matching `.cn` hosts. That misses aliased OpenAI-compatible URLs, build mirrors and implicit fallbacks.

### 2. Keep existing abstractions, do not choose a paid provider in the cleanup

Use existing cloud-ASR, OpenAI-compatible LLM and configurable TTS interfaces as approved-endpoint seams. Automated tests supply local protocol-compatible fixtures and deterministic audio. A deployable configuration must explicitly supply reviewed real provider settings; a missing provider leaves the corresponding capability unready with a clear English diagnostic. No fake is presented as real AI.

Remove disallowed adapters, preset rows, examples offered as active defaults, and unused SDK dependencies from the distributable backend. Remove eager local-model imports and mandatory mounts from the supported cloud-ASR path. Local model inference is not itself an external Chinese service; nevertheless the current FunASR/SenseVoice dependency must not be mandatory or auto-download via ModelScope. Any optional retained model gets a separate reviewed provenance/license/hash/source entry and no background downloader.

Alternative rejected: deleting the entire Python engine or introducing LangChain as part of this change. Both expand scope without being needed for service independence.

### 3. Disable optional integrations explicitly rather than invent replacements

Remove Aliyun SMS and its settings/UI enrollment paths; guard SMS-dependent registration and recovery while preserving password accounts/local CAPTCHA. No unrequested email/SMS provider or weakened recovery flow is introduced. Geolocation becomes unknown; removed weather/news/search tools are not advertised and return an unavailable result for stale requests. Preserve independent function names/error codes where compatible; no network fallbacks.

### 4. Treat upgrades and image provenance as first-class work

Never edit old Liquibase SQL to remove seeded provider records. Add forward-only migrations that disable legacy catalog entries, preserve referenced assistant IDs/history, and annotate/report affected configuration. API selectors omit removed choices; runtime validation catches saved stale choices. Preserve snapshots as inert historical data and prevent their restoration from reactivating disallowed services. Preserve credentials encrypted/redacted as applicable, never export them in reports. Invalidate `sys:params` and `server:config` through controlled application upgrade paths.

Build Python/Java images from this source and record full digests, dependency manifests/SBOMs, approved registries and dependency locks. Remove mirror/proxy assumptions in all supported deployment paths, not only the default Dockerfile. Keep current images/data available solely for authorized rollback; do not declare upstream images clean based on build-host geography.

### 5. Prove both software behavior and actual egress

Run existing and focused tests with live-provider flags off. Use fresh-cache builds and a disposable integration stack, isolated users/devices, local fake AI endpoints, test DNS plus an externally enforced outbound allowlist/capture. Count denied attempts as failures. In-process HTTP mocks alone do not prove no egress; include DNS, TCP/UDP, redirects, child processes and SDK background access. Record test scenario, process/container, destinations and attempted/allowed/denied status, but no conversation/audio bodies or secrets.

Exercise startup without local model files, account/CAPTCHA/recovery failure paths, provider changes and snapshot restore, device binding, direct WebSocket and gateway audio framing, history/summary access, and removed context/tool calls. The current `../smoke.mjs` is only an infrastructure baseline; it does not cover gateway voice or real turns. Hosted integration/live acoustic accuracy remains a separately authorized check, not a prerequisite for planning completion.

## Risks / Trade-offs

- [Optional features become unavailable] → Document exact removals in English and expose consistent unavailable outcomes; replacements are separate product choices.
- [Registry mirror removal exposes missing dependencies] → Fresh-cache builds, pinned inputs and explicit approved-source failures; never reintroduce a hidden mirror as fallback.
- [Saved providers/snapshots can bypass cleaned defaults] → Forward migration plus validation of create/update/import/restore/runtime paths and cache invalidation tests.
- [Unknown operator classification] → Unreviewed services stay disabled; evidence review precedes activation. No claim of a complete corporate ownership audit from code strings.
- [Raw arbitrary tools/context URLs can leak data] → Apply the same approval check to their destinations; keep broader SSRF hardening out of this plan's completion claim.
- [Resource/latency changes after ASR choice] → No performance claims; select and benchmark real approved providers separately.

## Migration Plan

1. Capture code baseline, contract fixtures and current database migration checksums; inventory user-selected integrations with secrets redacted.
2. Implement policy, removals and forward migration in isolated slices, retaining baseline tests for each slice.
3. Build from clean approved sources. Rehearse on disposable copies with separate volumes/ports and deterministic AI endpoints; record all egress attempts.
4. Obtain explicit approved production/evaluation provider choices and secret provisioning before a live rehearsal. Back up DB, uploaded audio, Redis-dependent state, model/config files and image digests under the user's control.
5. Coordinate parent wrapper/gateway edits only within authorized roots. Run both old-client contracts against candidate images; get explicit approval for any live cutover. This proposal does not restart the existing stack.
6. Roll back code and DB/volumes/config as a matched set if necessary, preserving post-cutover writes separately before restoration. Restoring historical code is not permission to contact removed providers; keep egress restricted and affected features unavailable until approved configuration is restored.

## Open Questions

- Which approved ASR/LLM/TTS endpoints and credentials will the operator select for a later live trial? Offline fixture acceptance does not depend on this choice, and deployment is explicitly gated on it.
- Which optional removed capabilities warrant a future replacement? This plan deliberately does not select a new weather/news/SMS vendor.
