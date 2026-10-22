[![Banners](docs/images/banner1.png)](https://github.com/xinnan-tech/xiaozhi-esp32-server)

<h1 align="center">Xiaozhi Backend Service xiaozhi-esp32-server</h1>

This checkout uses a restricted, provider-independent backend profile. See
[service-removal status](docs/maintenance/service-removal-progress.md) and the
[supported deployment guide](docs/Deployment.md). Historical integrations and
examples elsewhere in the upstream documentation are not active offerings.
No existing deployment is upgraded automatically.

<p align="center">
This project is based on human-machine symbiotic intelligence theory and technology to develop intelligent terminal hardware and software systems<br/>providing backend services for the open-source intelligent hardware project
<a href="https://github.com/78/xiaozhi-esp32">xiaozhi-esp32</a><br/>
Implemented using Python, Java, and Vue according to the <a href="https://ccnphfhqs21z.feishu.cn/wiki/M0XiwldO9iJwHikpXD5cEx71nKh">Xiaozhi Communication Protocol</a><br/>
Support for MQTT+UDP protocol, Websocket protocol, MCP access point, voiceprint recognition, and knowledge base
</p>

<p align="center">
<a href="./docs/FAQ.md">FAQ</a>
· <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server/issues">Report Issues</a>
· <a href="./README.md#deployment-documentation">Deployment Docs</a>
· <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server/releases">Release Notes</a>
</p>

<p align="center">
  <a href="./README.md"><img alt="Project README" src="https://img.shields.io/badge/Project-DFE0E5"></a>
  <a href="./docs/readme/README_en.md"><img alt="README in English" src="https://img.shields.io/badge/English-DBEDFA"></a>
  <a href="./docs/readme/README_vi.md"><img alt="Tiếng Việt" src="https://img.shields.io/badge/Tiếng Việt-DFE0E5"></a>
  <a href="./docs/readme/README_de.md"><img alt="Deutsch" src="https://img.shields.io/badge/Deutsch-DFE0E5"></a>
  <a href="./docs/readme/README_pt_BR.md"><img alt="Português (Brasil)" src="https://img.shields.io/badge/Português (Brasil)-DFE0E5"></a>
  <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server/releases">
    <img alt="GitHub Contributors" src="https://img.shields.io/github/v/release/xinnan-tech/xiaozhi-esp32-server?logo=docker" />
  </a>
  <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/LICENSE">
    <img alt="GitHub pull requests" src="https://img.shields.io/badge/license-MIT-white?labelColor=black" />
  </a>
  <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server">
    <img alt="stars" src="https://img.shields.io/github/stars/xinnan-tech/xiaozhi-esp32-server?color=ffcb47&labelColor=black" />
  </a>
</p>

<p align="center">
Spearheaded by Professor Siyuan Liu's Team (South China University of Technology)
</br>
Led by Professor Siyuan Liu's team at South China University of Technology
</br>
<img src="docs/images/hnlg.jpg" alt="South China University of Technology" width="50%">
</p>

---

## Target Users 👥

This project requires ESP32 hardware devices to work. If you have purchased ESP32-related hardware, successfully connected to Brother Xia's deployed backend service, and want to build your own `xiaozhi-esp32` backend service independently, then this project is perfect for you.

Want to see the usage effects? Click the videos below 🎥

<table>
  <tr>
    <td>
      <a href="https://www.bilibili.com/video/BV1FMFyejExX" target="_blank">
        <picture>
          <img alt="Response latency demonstration" src="docs/images/demo9.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1vchQzaEse" target="_blank">
        <picture>
          <img alt="Response speed optimization" src="docs/images/demo6.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1WEcxzFEAT" target="_blank">
        <picture>
          <img alt="Digital human with voice wake-up" src="docs/images/demo8.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1CKVz6UEuB" target="_blank">
        <picture>
          <img alt="Device-to-device calling" src="docs/images/demo0.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1C1tCzUEZh" target="_blank">
        <picture>
          <img alt="Complex medical scenarios" src="docs/images/demo1.png" /></picture>
      </a>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://www.bilibili.com/video/BV1VC96Y5EMH" target="_blank">
        <picture>
          <img alt="Music, weather, and news" src="docs/images/demo7.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV12J7WzBEaH" target="_blank">
        <picture>
          <img alt="Real-time interruption" src="docs/images/demo10.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1Co76z7EvK" target="_blank">
        <picture>
          <img alt="Visual object recognition" src="docs/images/demo12.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1pNXWYGEx1" target="_blank">
        <picture>
          <img alt="Home appliance control" src="docs/images/demo5.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1TJ7WzzEo6" target="_blank">
        <picture>
          <img alt="Multiple-command tasks" src="docs/images/demo11.png" /></picture>
      </a>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://www.bilibili.com/video/BV1ZQKUzYExM" target="_blank">
        <picture>
          <img alt="MCP endpoint" src="docs/images/demo13.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1zUW5zJEkq" target="_blank">
        <picture>
          <img alt="MQTT command delivery" src="docs/images/demo4.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1Exu3zqEDe" target="_blank">
        <picture>
          <img alt="Voiceprint recognition" src="docs/images/demo14.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV1CDKWemEU6" target="_blank">
        <picture>
          <img alt="Custom voices" src="docs/images/demo2.png" /></picture>
      </a>
    </td>
    <td>
      <a href="https://www.bilibili.com/video/BV12yA2egEaC" target="_blank">
        <picture>
          <img alt="Cantonese conversation" src="docs/images/demo3.png" /></picture>
      </a>
    </td>
  </tr>
</table>

---

## Warnings ⚠️

1. This project is open-source software. This software has no commercial partnership with any third-party API service providers (including but not limited to speech recognition, large models, speech synthesis, and other platforms) that it interfaces with, and does not provide any form of guarantee for their service quality or financial security. It is recommended that users prioritize service providers with relevant business licenses and carefully read their service agreements and privacy policies. This software does not host any account keys, does not participate in fund flows, and does not bear the risk of recharge fund losses.

2. The functionality of this project is not complete and has not passed network security assessment. Please do not use it in production environments. If you deploy this project for learning purposes in a public network environment, please ensure necessary protection measures are in place.

---

<!-- Compatibility anchor for existing Chinese-language links and bookmarks. -->
<a id="部署文档"></a>

## Deployment Documentation

![Banners](docs/images/banner2.png)

This project provides two deployment methods. Please choose based on your specific needs:

#### 🚀 Deployment Method Selection
| Deployment Method | Features | Applicable Scenarios | Deployment Docs | Configuration Requirements | Video Tutorials |
|---------|------|---------|---------|---------|---------|
| **Server only** | Voice conversation with explicit compatible providers | Configuration-file deployment | [Source-built setup](docs/Deployment.md) | Measure the selected workload; no mandatory ASR model | - |
| **Full module** | Account, device and assistant management | Database-backed deployment | [Source-built setup](docs/Deployment_all.md) | Measure the selected workload | - |

For frequently asked questions and related tutorials, please refer to [this link](./docs/FAQ.md)

> 💡 Note: Below is a test platform deployed with the latest code. You can burn and test if needed. Concurrent users: 6, data will be cleared daily.

```
Intelligent Control Console Address: https://2662r3426b.vicp.fun
Intelligent Control Console Address (H5): https://2662r3426b.vicp.fun/h5/index.html

Service Test Tool: https://2662r3426b.vicp.fun/test/
OTA Interface Address: https://2662r3426b.vicp.fun/xiaozhi/ota/
Websocket Interface Address: wss://2662r3426b.vicp.fun/xiaozhi/v1/
```

#### 🚩 Configuration Description and Recommendations
> [!Note]
> Choose providers explicitly. Missing configuration is reported as unready;
> no paid service, model or credential is selected automatically. The old free
> vendor presets and streaming benchmark claims do not apply to this profile.

| Module Name | Supported configuration | Notes |
|:---:|:---:|:---:|
| ASR | Explicit OpenAI-compatible transcription endpoint | No legacy streaming adapter |
| LLM | OpenAI-compatible endpoint or loopback Ollama | Compatible streaming chat |
| VLLM | Optional approved compatible endpoint | Explicitly configured only |
| TTS | Explicit OpenAI-compatible speech endpoint | Deterministic audio framing tested separately |
| Intent(Intent Recognition) | function_call(Function calling) | function_call(Function calling) |
| Memory(Memory function) | mem_local_short(Local short-term memory) | mem_local_short(Local short-term memory) |

If you are concerned about the latency of each component, please refer to the [Xiaozhi Component Performance Test Report](https://github.com/xinnan-tech/xiaozhi-performance-research), and test in your own environment following the test methods in the report.

#### 🔧 Testing Tools
This project provides the following testing tools to help you verify the system and choose suitable models:

| Tool Name | Location | Usage Method | Function Description |
|:---:|:---|:---:|:---:|
| Audio Interaction Test Tool | main》digital-human》index.html | Run `python start.py` in `main/digital-human`, then open `http://127.0.0.1:8006/index.html` | Tests audio playback and reception functions, verifies if Python-side audio processing is normal |
| Provider benchmark | [Status and future benchmark requirements](docs/performance_tester.md) | Unavailable in the supported profile | The retired runner performs no provider calls. |

> 💡 Note: When testing model speed, only models with configured keys will be tested.

---
## Feature List ✨
### Implemented ✅
![Full-module deployment architecture](docs/images/deploy2.png)

English architecture equivalent: ESP32 devices send voice over WebSocket to the Python `xiaozhi-server`. The engine runs VAD, ASR, LLM/tool processing, memory, and TTS, then streams audio back. Administrators use `manager-web` to call the Java `manager-api`; MySQL stores management data and Redis caches it. The engine fetches configuration from `manager-api`. See the [full deployment guide](./docs/Deployment_all.md) for ports, OTA, and startup steps. Image labels and video previews remain in their original language; the feature table below explains their functions. The diagram also labels the optional MQTT gateway: MQTT text/events on TCP 1883, UDP audio on UDP 8884, and the command-delivery API on TCP 8007; the gateway bridges these to the engine over WebSocket. Vision uses HTTP 8003. MCP endpoint registration/message forwarding uses WebSocket 8004 and connects calculator, smart-home, computer-system, or other MCP clients. The 3D-Speaker voiceprint API uses HTTP 8005; voiceprint identification runs alongside ASR, supplying speaker identity while ASR supplies text/emotion to the LLM. The engine streams sentence/chunk output to TTS, calls MCP tools, uses memory, and applies private configuration. The management API serves static web resources and dynamic API requests, covering agents, devices, role presets, models, users, and OTA. MySQL 3306 provides persistent storage; Redis 6379 stores hot data.
| Feature Module | Description |
|:---:|:---|
| Core Architecture | Based on [MQTT+UDP gateway](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/mqtt-gateway-integration.md), WebSocket and HTTP servers, provides complete console management and authentication system |
| Voice Interaction | Compatible transcription and speech APIs, streamed chat, local Silero VAD and existing WebSocket audio framing |
| Voiceprint Recognition | Supports multi-user voiceprint registration, management, and recognition, processes in parallel with ASR, real-time speaker identity recognition and passes to LLM for personalized responses |
| Intelligent Dialogue | Supports multiple LLM(large language models), implements intelligent dialogue |
| Visual Perception | Supports multiple VLLM(vision large models), implements multimodal interaction |
| Intent Recognition | Supports LLM intent recognition, Function Call function calling, provides plugin-based intent processing mechanism |
| Memory System | Local short-term summaries using an approved LLM, report-only or no-memory mode; external memory SDKs are unavailable |
| Knowledge Base | Supports RAGFlow knowledge base, enabling LLM to judge whether to schedule the knowledge base after receiving the user's question, and then answer the question |
| Tool Calling | Supports client IOT protocol, client MCP protocol, server MCP protocol, MCP endpoint protocol, custom tool functions |
| Command Delivery | Supports MCP command delivery to ESP32 devices via MQTT protocol from Smart Console |
| Management Backend | Provides Web management interface, supports user management, system configuration and device management; Supports Simplified Chinese, Traditional Chinese and English display |
| Testing Tools | Offline policy, migration and protocol fixtures; the legacy provider benchmark is unavailable |
| Deployment Support | Supports Docker deployment and local deployment, provides complete configuration file management |
| Plugin System | Supports functional plugin extensions, custom plugin development, and plugin hot-loading |

### Under Development 🚧

To learn about specific development plan progress, [click here](https://github.com/users/xinnan-tech/projects/3). For frequently asked questions and related tutorials, please refer to [this link](./docs/FAQ.md)

If you are a software developer, here is an [Open Letter to Developers](./docs/contributor_open_letter.md). Welcome to join!

---

## Product Ecosystem 👬
Xiaozhi is an ecosystem. When using this product, you can also check out other [excellent projects](https://github.com/78/xiaozhi-esp32/blob/main/README_zh.md#%E7%9B%B8%E5%85%B3%E5%BC%80%E6%BA%90%E9%A1%B9%E7%9B%AE) in this ecosystem

---

## Supported backend profile

| Capability | Implementation | Endpoint or artifact |
| --- | --- | --- |
| ASR | `openai` | Explicit approved transcription API |
| LLM | `openai`, `ollama` | Approved compatible chat API or loopback Ollama |
| Vision | `openai` | Optional approved compatible API |
| TTS | `openai` | Approved speech API and configured voice |
| VAD | `silero` | Explicit local ONNX file; no model download |
| Memory | `nomem`, `mem_report_only`, `mem_local_short` | Local/report-only storage; summaries use the approved LLM |
| Intent | `nointent`, `intent_llm`, `function_call` | Only actually available tools are advertised |
| Optional tools | Time, exit, device control/calls, local music; reviewed self-hosted Home Assistant/RAGFlow/MCP/context/voiceprint | Loopback-only service policy; no subprocess installers |

Compatible wire formats do not approve an arbitrary host. Removed or unknown
endpoints, imports, presets and restores fail explicitly. SMS, weather, news, web
search, vendor voice cloning and hosted external-memory adapters are unavailable.
Historical data remains stored; no assistant or history is silently reassigned.
See [migration and verification evidence](docs/maintenance/service-removal-progress.md).

---

## Acknowledgments 🙏

| Logo | Project/Company | Description |
|:---:|:---:|:---|
| <img src="docs/images/logo_bailing.png" width="160"> | [Bailing Voice Dialogue Robot](https://github.com/wwbin2017/bailing) | This project is inspired by [Bailing Voice Dialogue Robot](https://github.com/wwbin2017/bailing) and implemented on its basis |
| <img src="docs/images/logo_tenclass.png" width="160"> | [Tenclass](https://www.tenclass.com/) | Thanks to [Tenclass](https://www.tenclass.com/) for formulating standard communication protocols, multi-device compatibility solutions, and high-concurrency scenario practice demonstrations for the Xiaozhi ecosystem; providing full-link technical documentation support for this project |
| <img src="docs/images/logo_xuanfeng.png" width="160"> | [Xuanfeng Technology](https://github.com/Eric0308) | Thanks to [Xuanfeng Technology](https://github.com/Eric0308) for contributing function calling framework, MCP communication protocol, and plugin-based calling mechanism implementation code. Through standardized instruction scheduling system and dynamic expansion capabilities, it significantly improves the interaction efficiency and functional extensibility of frontend devices (IoT) |
| <img src="docs/images/logo_junsen.png" width="160"> | [huangjunsen](https://github.com/huangjunsen0406) | Thanks to [huangjunsen](https://github.com/huangjunsen0406) for contributing the `Smart Control Console Mobile` module, which enables efficient control and real-time interaction across mobile devices, significantly enhancing the system's operational convenience and management efficiency in mobile scenarios. |
| <img src="docs/images/logo_huiyuan.png" width="160"> | [Huiyuan Design](http://ui.kwd988.net/) | Thanks to [Huiyuan Design](http://ui.kwd988.net/) for providing professional visual solutions for this project, using their design practical experience serving over a thousand enterprises to empower this project's product user experience |
| <img src="docs/images/logo_qinren.png" width="160"> | [Xi'an Qinren Information Technology](https://www.029app.com/) | Thanks to [Xi'an Qinren Information Technology](https://www.029app.com/) for deepening this project's visual system, ensuring consistency and extensibility of overall design style in multi-scenario applications |
| <img src="docs/images/logo_contributors.png" width="160"> | [Code Contributors](https://github.com/xinnan-tech/xiaozhi-esp32-server/graphs/contributors) | Thanks to [all code contributors](https://github.com/xinnan-tech/xiaozhi-esp32-server/graphs/contributors), your efforts have made the project more robust and powerful. |


<a href="https://www.star-history.com/?repos=xinnan-tech%2Fxiaozhi-esp32-server&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=xinnan-tech/xiaozhi-esp32-server&type=date&theme=dark&legend=top-left&sealed_token=cQovHKgZjqEnQ-svfYfN392irNvGuq-6pyv4cA8nd2jQEhQLz1ETV4YHTVk2UZyLMFbCQuZA7jduRh3YbeK5WPYaRLrfmIimGQa3lram652jJL9oQk-UuSZA5H6L4dPIhZc8KCc-Ur_UAUNbly7TePpnTR2otGknBLCOjOliD4fk1st6z7tPEDVjSRx5" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=xinnan-tech/xiaozhi-esp32-server&type=date&legend=top-left&sealed_token=cQovHKgZjqEnQ-svfYfN392irNvGuq-6pyv4cA8nd2jQEhQLz1ETV4YHTVk2UZyLMFbCQuZA7jduRh3YbeK5WPYaRLrfmIimGQa3lram652jJL9oQk-UuSZA5H6L4dPIhZc8KCc-Ur_UAUNbly7TePpnTR2otGknBLCOjOliD4fk1st6z7tPEDVjSRx5" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=xinnan-tech/xiaozhi-esp32-server&type=date&legend=top-left&sealed_token=cQovHKgZjqEnQ-svfYfN392irNvGuq-6pyv4cA8nd2jQEhQLz1ETV4YHTVk2UZyLMFbCQuZA7jduRh3YbeK5WPYaRLrfmIimGQa3lram652jJL9oQk-UuSZA5H6L4dPIhZc8KCc-Ur_UAUNbly7TePpnTR2otGknBLCOjOliD4fk1st6z7tPEDVjSRx5" />
 </picture>
</a>
