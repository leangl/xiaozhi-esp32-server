# Reviewed service replacement decisions

Initial review: 2026-10-20; implementation checkpoint: 2026-10-21. Scope is remote operators and mandatory downloads, not
the nationality of library authors or the Chinese language. A "remove" decision
below is a work item until its enforcement is recorded in
[progress](service-removal-progress.md). Do not treat this matrix as proof that
all listed runtime paths are already closed.

[The generated path inventory](service-inventory.json) records provider imports,
literal hosts, dynamic URL settings and network/download call-site lines for
159 current backend/build files. It never records credentials or conversation bodies.
Generate it with `python3 tools/service-inventory.py --write`. Literal references
include documentation and examples, so host discovery alone is not traffic proof.

## AI services and replacements

Paths in this table are relative to `main/xiaozhi-server/core/providers`; YAML
presets are in `main/xiaozhi-server/config.yaml`. Historical provider seeds are in
`main/manager-api/src/main/resources/db/changelog/` and must not be edited.

| Integration / evidence | Source and preset seams | Decision / replacement |
| --- | --- | --- |
| Alibaba/Aliyun/DashScope/Bailian ([operator product](https://www.alibabacloud.com/en/product/modelstudio)) | `asr/aliyun*.py`, `asr/qwen3_asr_flash.py`, `llm/AliBL/`, `tts/aliyun*.py`, `tts/alibl_stream.py`; Ali/Qwen presets and compatible URLs | Remove remote adapters/SDKs/presets; use reviewed OpenAI-compatible ASR/LLM/TTS endpoints or independently hosted equivalents. |
| Baidu ([speech platform](https://cloud.baidu.com/product/speech)) | `asr/baidu.py`; Baidu presets; separate `tts/paddle_speech.py` local server | Remove hosted SDK/ASR. A local Paddle server is a distinct self-hosted service and needs model/source review, not automatic nationality-based removal. |
| Tencent (source SDK/endpoint evidence; [official service link](https://www.tencentcloud.com/products/asr) timed out during review) | `asr/tencent.py`, `tts/tencent.py`; Tencent presets | Remove remote adapters and presets. Timeout does not approve the destination. |
| ByteDance/Volcengine/Doubao/Coze ([operator product](https://www.volcengine.com/product/doubao); JS-only page, SDK branding also in source) | `asr/doubao*.py`, `llm/coze/`, `tts/{doubao,huoshan_double_stream,cozecn}.py`; Volces gateway presets | Remove hosted branches/presets and `cozepy`; replace through compatible speech/chat interfaces, with no new recipient selected silently. |
| iFlytek ([official platform](https://www.xfyun.cn/)) | `asr/xunfei_stream.py`, `tts/xunfei_stream.py`; Spark compatible preset | Remove remote adapters/presets. |
| Zhipu/BigModel (source host and `ChatGLM*` presets) | generic `llm/openai/`, `vllm/openai.py`; `open.bigmodel.cn` | Remove presets and reject aliased base URLs; do not confuse a wire-compatible API with operator independence. Corporate review is not needed to retain an unrequested destination. |
| DeepSeek ([API docs](https://api-docs.deepseek.com/)) | generic `llm/openai/`; `DeepSeekLLM` preset | Remove active preset/vendor options and reject URL aliases. Local model weights, if ever selected, need independent provenance/license review. |
| SiliconFlow ([service docs](https://docs.siliconflow.com/en/userguide/introduction)) | `tts/siliconflow.py`, CosyVoice preset | Remove hosted adapter/presets. |
| MiniMax | `tts/minimax_httpstream.py`, MiniMax preset | Remote operator not approved in this change; remove active integration, with no assertion based only on its domain. |
| 302.ai and Fish Audio | `TTS302AI`, `tts/fishspeech.py` hosted branch | Review/unapproved: no approval inferred from `.ai`. Remove hosted defaults; self-hosted Fish Speech is separate and needs model/provenance review. |
| Hosted Dify/FastGPT and Xinference | `llm/{dify,fastgpt,xinference}/` | Review hosted destinations; retain service-neutral/self-hosted software only behind the same endpoint boundary. No automatic hosted fallback. |
| Mem0 / PowerMem | `memory/{mem0ai,powermem}/` and their SDK defaults | Review/quarantine hosted or implicit model/embedding destinations. Preserve existing data; retain `nomem`, `mem_report_only` and local short-memory paths using approved LLMs. |
| OpenAI ([speech API](https://developers.openai.com/api/docs/guides/speech-to-text)) | `asr/openai.py`, `llm/openai/`, `vllm/openai.py`, `tts/openai.py` | Retain explicit `api.openai.com` roles; no account/key or model chosen automatically. Local protocol fakes test the seam; no live provider claim. |
| Google ([compatible API](https://ai.google.dev/gemini-api/docs/openai)) | OpenAI-compatible LLM/VLLM endpoint; native `llm/gemini/` is a separate seam | Permit the documented compatible host only for LLM/VLLM. Native SDK/background routes remain review work, not blanket-approved. |
| Ollama / llama.cpp / compatible self-hosted speech | `llm/ollama/`, generic compatible adapters | Retain explicit loopback endpoints for tests/self-hosting. A cloud/LAN hostname requires an operator-reviewed policy addition; private IPs are not automatically trusted. No models are downloaded by policy. |
| Microsoft Edge TTS | `tts/edge.py` and `edge_tts` | Microsoft operator evidence differs from supported API/product suitability. Review the unofficial client separately; it is not the approved default replacement for commercial child-facing speech. |
| Vosk, Sherpa, FunASR/SenseVoice, local TTS, Silero VAD | local inference adapters / model assets | Local execution is not a remote operator. Remove mandatory SenseVoice/ModelScope fetching; retain optional local inference only with documented files, source/license/hash and no background download. |

## Other destinations and ownership seams

| Integration | Source | Decision |
| --- | --- | --- |
| Aliyun SMS | retired `modules/sms/service/imp/ALiYunSmsService.java`, POM, `aliyun.sms.*` settings | Client/SDK removed. Non-network unavailable implementation and pre-side-effect guards are in place. No SMS substitute was purchased or selected; ordinary password accounts/local CAPTCHA remain. |
| PConline IP lookup | `core/utils/util.py`, `core/utils/prompt_manager.py` | Removed. IP location and automatic weather are absent; no IP recipient substituted. |
| Local-IP routing probe | `core/utils/util.py:get_local_ip` | With explicit user approval, replaced the external 8.8.8.8:80 probe with local `psutil` interface reads. No outbound discovery or DNS fallback; regressions and the full candidate network gate pass. |
| QWeather ([API docs](https://dev.qweather.com/en/docs/)) | `plugins_func/functions/get_weather.py`, plugin defaults, prompt context | Remove hosted/default integration and advertisements; replacement needs explicit parent-supplied location and reviewed service/self-hosting. |
| Metaso ([official site](https://metaso.cn/)) | `plugins_func/functions/web_search.py`, default provider | Remove branch/default. Existing Tavily/Serply branches need their own operator/endpoint review; no implicit fallback. |
| ChinaNews / NewsNow | `plugins_func/functions/get_news_from_*.py` | Remove hosted implementations/default feeds and advertising. A future RSS provider must be explicitly reviewed, not scraped from arbitrary endpoints. |
| Home Assistant / RAGFlow | local tool and LLM adapters | Self-hosted interfaces are not automatically banned by library origin. Require explicit endpoint review; arbitrary public or hosted defaults are not approved. |
| Remote MCP/context/voiceprint | `core/providers/tools/{server_mcp,mcp_endpoint}`, `core/utils/context_provider.py`, Java configuration and voiceprint services | Validate destinations before credentials/device metadata; redirects/proxies and subprocesses remain separate call-site work. Device-local MCP messages do not imply remote HTTP approval. |
| Package mirrors / image proxies / model downloaders | Dockerfiles, POM, setup/Compose/CI, `fun_local`, requirements | Official PyPI/Maven Central/OCI sources replace mirrors. Pins, SBOMs, clean builds and externally enforced egress evidence remain required; a warm upstream image is not a compliant artifact. |

## Limits and activation gate

### Implemented supported profile (2026-10-21)

The distributable profile now retains OpenAI-compatible ASR/LLM/VLLM/TTS,
loopback Ollama, explicitly provisioned Silero VAD, `nomem`, `mem_report_only`,
`mem_local_short`, and the no-intent/LLM-intent/function-call interfaces. The
other remote/local inference adapters from the historical catalog are not
active alternatives in this profile. Native Google SDK, unofficial Edge TTS,
Mem0/PowerMem and arbitrary MCP subprocess installers are removed rather than
being implicitly approved by a table entry above. Historical SQL and referenced
data stay intact; the forward upgrader disables unsupported selections and
reports replacement-required records without copying keys to another operator.

SMS, hosted weather/news/search and voice cloning report unavailable. The last
has no reviewed remaining backend, so preserving its old records does not make
new cloning requests available. Time/lunar, exit, device control, role/music,
explicitly configured local Home Assistant/RAGFlow and remote MCP/context seams
remain behind the destination boundary; none receives a new remote default.

Trace-to-boundary index (paths relative to the backend module):

| Path / operation | Destination and before-send enforcement |
| --- | --- |
| Java `OpenAIStyleLLMServiceImpl`, title/summary and model previews | `ApprovedProviderCatalog` and `ApprovedServicePolicy`; exact reviewed AI hosts/roles or loopback; direct client, no redirect/proxy fallback. |
| Java `ConfigServiceImpl`, model/assistant/template writes and snapshots | Validate selected provider/config/voice before activation or restore; ordinary selectors exclude unavailable rows and server credentials. |
| Java SMS/CAPTCHA | No SMS network adapter; disabled paths reject before code/rate-limit mutations. Local image CAPTCHA/password flows retained. |
| Java `RestTemplateConfig`, RAGFlow, voiceprint and MCP access-point services | Validate reviewed loopback service destination before headers/request; static redacted failures. Voice cloning unavailable before new records/network. |
| Java `MqttGatewayAuthorization` / `WebSocketValidator` | Explicit loopback tool/WS URL before direct connection; no redirects or environment/system proxy fallback. |
| Python `config_loader`, provider factories, managed private configuration and runtime update | Exact supported implementation types; endpoint/readiness validation before imports/directories/cache/activation; failed update retains old config/instances; no private-config failure fallback. |
| Python `context_provider`, `voiceprint_provider`, device/HASS/RAGFlow tools | Endpoint policy before client construction; direct guarded HTTP clients, redacted errors, no automatic IP/weather context. |
| Python remote MCP HTTP/SSE/WebSocket | Endpoint validation at settings and worker boundaries; guarded SDK client factories; redirects rejected; command/args/env subprocess installation configurations rejected. Device-local MCP messages remain separate. |
| Python tool advertisement/execution | Explicit retained import list; retired names are neither advertised nor imported and stale calls return unavailable. |
| Python ASR/VAD initialization | No SenseVoice/ModelScope hub import/download; explicit existing Silero file and configured ASR readiness required. |
| Sibling gateway voice pools/reload | Required explicit public advertisement; only exact reviewed loopback/candidate voice WS targets; failed reload retains valid pool; direct/no redirects. No implicit `mqtt.xiaozhi.me` fallback. |
| Build/setup/CI | Official PyPI/npm/Central and digest-pinned reviewed OCI inputs; no mirror/TLS bypass or mandatory inference download. Production Linux ARM64 OS/transitive Maven archive locks and component preservation pass. |

Current build and runtime evidence, including limits and untested scenarios, is
in [candidate validation](service-candidate-validation.md). The initial table
is a decision history, not an offer to use deleted adapters. A local fake is not
a replacement cloud AI service or a claim about real recognition quality.

Brand/service pages above identify the named integrations, not an exhaustive
corporate ownership audit. Uncertain services remain unapproved, rather than
being labelled Western because of a domain suffix. Operator geography does not
prove child-data, retention, licensing or jurisdiction compliance.

No live egress to these providers was exercised. Catalog migration and focused
create/update/restore validation and both managed voice transports now pass.
Both baseline device-binding authorization defects were fixed with explicit
approval; the fresh API repeat passes 22/22 scenarios and both managed transports
pass again. Production Linux ARM64 build locking now passes. The full application
DNS/egress matrix passes after the approved local-only get_local_ip correction
and locked-image repeat. The initial failed report is preserved. Final review,
the separately approved CI fixture correction and implementation acceptance are
complete; all three specs are synchronized and the 30/30 change is archived. See
service-network-and-locks.md. The old runtime continues unchanged;
the approved rehearsal does not authorize cutover.
