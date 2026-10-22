# Server-only deployment architecture

![Server-only deployment architecture](images/deploy1.png)

ESP32 devices exchange audio and control frames with the Python engine over
WebSocket on port 8000. The engine runs VAD, ASR, LLM, intent/memory and TTS. This
profile reads local YAML; it does not require the management database. HTTP OTA
and vision use port 8003. The diagram includes historical provider choices; use
only the supported implementations below.

<!-- Compatibility anchors for existing links and bookmarks. -->
<a id="方式一docker只运行server"></a>

## Method 1: Docker candidate

Complete [source builds and remaining release gates](docker-build.md) first.
Install Docker from its official distribution for your OS in a dedicated test
environment. The retired `docker-setup.sh` prints guidance and performs no install,
download, daemon reconfiguration, upgrade or restart.

Keep `main/xiaozhi-server/docker-compose.yml` in the checkout. It requires explicit
`SERVER_IMAGE` and `SERVER_BASE_IMAGE` values for artifacts built from this source,
and `CANDIDATE_DATA_DIR` for a new isolated configuration directory. It binds
loopback ports 18000 and 18003 by default. There are no fixed container names or
required ASR-model mounts. Use a new Compose project name for each rehearsal.

Do not start a candidate against live configuration or data. After separate
rehearsal authorization, an operator can use this template with synthetic local
AI fixtures and network enforcement. Plain Compose is not an egress sandbox.
No start/restart command is part of this preparation guide.

<a id="方式二本地源码只运行server"></a>

## Method 2: Local source candidate

Use a new Python 3.10 virtual environment in a disposable checkout. Install
`libopus` and `ffmpeg` from reviewed official OS packages. Do not modify global
Conda/pip channels or delete an existing environment. Install Python packages only
after the dependency and egress review described in the build guide:

```sh
python3.10 -m venv /path/to/new-candidate-venv
/path/to/new-candidate-venv/bin/python -m pip --isolated install \
  --index-url https://pypi.org/simple \
  --only-binary=:all: --require-hashes -r main/xiaozhi-server/requirements.lock
```

This command downloads hash-locked binary artifacts from PyPI; it is not an
offline test. Verify that the lock's CPython 3.10 Linux aarch64 target covers your
candidate platform. Run it only in the reviewed build environment.

<a id="配置项目"></a>
<a id="project-configuration"></a>

## Project configuration

Create a new candidate configuration from the current
`main/xiaozhi-server/config.yaml` template. Keep existing private files unchanged.
Select and configure each required provider before any conversation. Missing or
removed choices must remain unavailable; no replacement or credential migration
occurs automatically.

| Capability | Supported implementation types |
| --- | --- |
| ASR | `openai` |
| LLM | `openai`, `ollama` |
| Vision LLM | `openai` |
| TTS | `openai` |
| VAD | `silero` |
| Memory | `nomem`, `mem_local_short`, `mem_report_only` |
| Intent | `nointent`, `intent_llm`, `function_call` |

Approved cloud origins are `https://api.openai.com` for ASR/LLM/vision/TTS and
`https://generativelanguage.googleapis.com` for LLM/vision. The policy also accepts
literal loopback IPs and `localhost` for self-hosted fixtures. It rejects unknown
destinations, environment-proxy routing and redirect bypasses. Select model IDs,
voices and credentials explicitly; a compatible API shape does not approve a
different operator. Real calls require separate approval and may incur charges.

Inside a container, `localhost` refers to that container. An AI fixture in another
Compose service is not approved through its service-name alias. Coordinate a
loopback-accessible fixture topology; do not widen the policy to get a rehearsal
working. The management API connection is separate from AI-provider policy.

Removed SMS, geolocation, weather/news/search and external-memory choices are
unavailable. Do not follow older integration tutorials to reactivate them.

<a id="模型文件"></a>
<a id="model-files"></a>

## Model files

The supported cloud-ASR profile requires no SenseVoice/FunASR model and performs
no ModelScope or substitute model download. Preserve old model files as operator
data; the Docker build excludes them. The checkout contains a Silero ONNX asset,
but its byte hash is not a provenance pin. Provision an approved VAD model path
explicitly; the default placeholder is not ready. Complete the provenance/license
review as described in the build guide. Do not introduce a background fetch on
missing files.

<a id="运行状态确认"></a>
<a id="startup-verification"></a>

## Startup verification and device endpoints

In an authorized isolated rehearsal, verify configuration readiness with an empty
ASR model cache, then exercise deterministic ASR/LLM/TTS fixtures. Record outbound
DNS and connections, including denied attempts. Verify direct WebSocket framing,
audio output, missing-provider errors and stale removed-feature calls. A startup
log alone does not establish acceptance or a paid-provider result.

The candidate template exposes `ws://127.0.0.1:18000/xiaozhi/v1/` and
`http://127.0.0.1:18003/xiaozhi/ota/` to the host. Physical ESP32 devices cannot use
the host's loopback address. A later approved deployment must choose device-
reachable endpoints and configure access/TLS; this guide does not open LAN ports.
The WebSocket URL is not a browser page. See [firmware setup](firmware-setting.md)
for the device protocol, after the endpoint choice has been approved.

## Upgrade and rollback

Follow the backup, disposable-copy migration, egress, approval and paired rollback
requirements in [the build guide](docker-build.md#rehearsal-and-rollback). Keep the
running deployment unchanged during preparation. An old provider selection needs
an explicit approved replacement before its capability resumes.
