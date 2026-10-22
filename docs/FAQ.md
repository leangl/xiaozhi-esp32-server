# Frequently asked questions

### 1. ASR recognizes Korean, Japanese, or English when I speak Chinese

The supported profile uses the approved `openai` ASR implementation and requires
explicit endpoint/model settings. Check those settings and the provider's
language options. It does not use or download SenseVoice/FunASR model files. See
[supported configuration](Deployment.md#project-configuration).

### 2. TTS reports a task error or missing file

Check that you installed `libopus` and `ffmpeg` in the correct Conda environment. If needed:

```
conda install conda-forge::libopus
conda install conda-forge::ffmpeg
```

### 3. TTS often fails or times out

Only the `openai` TTS implementation remains supported. Check its approved
endpoint, model, voice and readiness errors. Environment proxies and redirects
must not bypass endpoint validation. EdgeTTS and vendor-specific streaming TTS
are unavailable; do not switch to an old preset or buy a replacement tier as an
implicit troubleshooting step.

### 4. Wi-Fi connects to my server, but 4G does not

The upstream firmware requires a secure connection in 4G mode. Choose one approach:

1. Modify firmware as shown in the [video](https://www.bilibili.com/video/BV18MfTYoE85).
2. Configure an SSL certificate in Nginx following the [tutorial](https://icnt94i5ctj4.feishu.cn/docx/GnYOdMNJOoRCljx1ctecsj9cnRe).

### 5. Improve dialogue response latency

Select the approved ASR/LLM/TTS configuration first and verify a complete turn
with synthetic local fixtures. No latency or cost comparison has been established
for this retained profile. The legacy benchmark is retired; see
[benchmark status](performance_tester.md) before planning measurements. A paid
latency/accuracy trial requires separate approval.

### 6. Xiaozhi interrupts during pauses in slow speech

Increase `min_silence_duration_ms`, for example to `1000`:

```yaml
VAD:
  SileroVAD:
    threshold: 0.5
    type: silero
    model_path: models/silero_vad.onnx  # Explicitly provision a reviewed local artifact
    min_silence_duration_ms: 700  # Increase this value if you pause for longer while speaking
```

### 7. Deployment guides

- [Server-only deployment](./Deployment.md)
- [Full-module deployment](./Deployment_all.md)
- [MQTT+UDP gateway](./mqtt-gateway-integration.md)
- [Automatic source updates and builds](./dev-ops-integration.md)
- [Nginx integration](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)
- [Build custom Docker images](./docker-build.md)

### 8. Firmware guides

- [Build firmware](./firmware-build.md)
- [Set the OTA address in prebuilt firmware](./firmware-setting.md)
- [Automatic OTA upgrades for server-only deployments](./ota-upgrade-guide.md)

### 9. Extensions

- SMS registration/recovery: unavailable until an approved replacement is implemented.
- [Home Assistant](./homeassistant-integration.md)
- [Vision and camera recognition](./mcp-vision-integration.md)
- [Deploy MCP endpoints](./mcp-endpoint-enable.md)
- [Connect MCP endpoints](./mcp-endpoint-integration.md)
- [Read device information in MCP methods](./mcp-get-device-info.md)
- [Voiceprint recognition](./voiceprint-integration.md)
- [RAGFlow knowledge base](./ragflow-integration.md)
- [Context providers](./context-provider-integration.md)
- [Device-to-device calls](./device-call-guide.md)
- Weather/news/web search and external memory SDKs: unavailable; no fallback provider.

### 10. Digital human

- [Start digital-human](./digital-human-wakeword.md)
- [Deploy digital-human on an N100 mini PC](./all-in-one-digital-human-setup.md)

### 11. Voice cloning and local speech synthesis

- [Clone voices in the console](./huoshan-streamTTS-voice-cloning.md)
- [Index-TTS](./index-stream-integration.md)
- [Fish Speech](./fish-speech-integration.md)
- [PaddleSpeech](./paddlespeech-deploy.md)

### 12. Performance tests

- [Component testing guide](./performance_tester.md)
- [Published test results](https://github.com/xinnan-tech/xiaozhi-performance-research)

### 13. Report other problems

Open an [issue](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues).
