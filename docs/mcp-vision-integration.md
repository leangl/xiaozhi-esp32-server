# Vision model guide

This guide covers server-only and full-module deployments.

Before enabling vision, prepare a camera-equipped device supported by the upstream firmware, such as the Lichuang Practical ESP32-S3 board. Use firmware version 1.6.6 or later and confirm that basic conversation works.

## Server-only deployment

### Step 1: Check networking

Vision uses port 8003 by default. For Docker, ensure `docker-compose.yml` publishes port `8003`; update the file if necessary. For source deployment, allow port `8003` through the firewall.

### Step 2: Select a vision model

In `data/.config.yaml`, set `selected_module.VLLM` to a supported vision model. The project supports OpenAI-compatible APIs, including `ChatGLMVLLM`:

```
selected_module:
  VAD: ..
  ASR: ..
  LLM: ..
  VLLM: ChatGLMVLLM
  TTS: ..
  Memory: ..
  Intent: ..
```

Obtain a key from [Zhipu AI](https://bigmodel.cn/usercenter/proj-mgmt/apikeys), or reuse an existing one. Add or update:

```
VLLM:
  ChatGLMVLLM:
    api_key: 你的api_key
```

The original placeholder `你的api_key` means “your API key”; replace it.

### Step 3: Start xiaozhi-server

For source deployment:

```
python app.py
```

For Docker:

```
docker restart xiaozhi-esp32-server
```

The preserved historical log lists OTA, vision analysis, and WebSocket URLs. Its warning says the WebSocket URL is not a browser page and recommends the digital-human module for browser interaction tests:

```
2025-06-01 **** - OTA接口是           http://192.168.4.7:8003/xiaozhi/ota/
2025-06-01 **** - 视觉分析接口是        http://192.168.4.7:8003/mcp/vision/explain
2025-06-01 **** - Websocket地址是       ws://192.168.4.7:8000/xiaozhi/v1/
2025-06-01 **** - =======上面的地址是websocket协议地址，请勿用浏览器访问=======
2025-06-01 **** - 如想测试websocket请启动digital-human模块，打开浏览器交互测试
2025-06-01 **** - =============================================================
```

Open the vision-analysis HTTP URL in a browser, or use this command on a host without a browser. Replace the original placeholder `你的视觉分析接口` with your vision-analysis endpoint:

```
curl -i 你的视觉分析接口
```

A healthy historical response says “MCP Vision is running; the vision explanation endpoint is …”:

```
MCP Vision 接口运行正常，视觉解释接口地址是：http://xxxx:8003/mcp/vision/explain
```

For public-network or Docker deployments, set the device-reachable vision URL in `data/.config.yaml`. The original placeholder `你的ip或者域名:端口号` means “your IP or domain:port”:

```
server:
  vision_explain: http://你的ip或者域名:端口号/mcp/vision/explain
```

Devices cannot use an unreachable LAN address or a container-internal address. For public IP `111.111.111.111`:

```
server:
  vision_explain: http://111.111.111.111:8003/mcp/vision/explain
```

Verify that the published vision explanation URL opens before continuing.

### Step 4: Test the camera

Wake the device and ask it to open the camera and describe what it sees. Inspect the server logs for errors.

## Full-module deployment

### Step 1: Check networking

Vision uses port 8003 by default. Ensure `docker-compose_all.yml` publishes port `8003`, or allow the port through the firewall for source deployment.

### Step 2: Check configuration structure

Compare `data/.config.yaml` with the `data/config_from_api.yaml` template described in the original guide. Add any missing settings.

### Step 3: Configure the vision API key

Obtain or reuse a [Zhipu AI key](https://bigmodel.cn/usercenter/proj-mgmt/apikeys). In the console, open **Model Configuration > Vision Language Models**, find `VLLM_ChatGLMVLLM`, click **Edit**, enter **API Key**, and save.

Open the agent's **Configure Role** page, choose that model under **Vision Language Model (VLLM)**, and save.

### Step 3: Start xiaozhi-server

For source deployment:

```
python app.py
```

For Docker:

```
docker restart xiaozhi-esp32-server
```

The historical output lists the vision and WebSocket URLs and warns to use the digital-human module for browser WebSocket tests:

```
2025-06-01 **** - 视觉分析接口是        http://192.168.4.7:8003/mcp/vision/explain
2025-06-01 **** - Websocket地址是       ws://192.168.4.7:8000/xiaozhi/v1/
2025-06-01 **** - =======上面的地址是websocket协议地址，请勿用浏览器访问=======
2025-06-01 **** - 如想测试websocket请启动digital-human模块，打开浏览器交互测试
2025-06-01 **** - =============================================================
```

Open the vision HTTP endpoint or use `curl` (replace `你的视觉分析接口` with your endpoint):

```
curl -i 你的视觉分析接口
```

A healthy response means the vision service is running and reports its explanation URL:

```
MCP Vision 接口运行正常，视觉解释接口地址是：http://xxxx:8003/mcp/vision/explain
```

For public-network or Docker deployments, configure the reachable URL; replace the original IP/domain/port placeholder:

```
server:
  vision_explain: http://你的ip或者域名:端口号/mcp/vision/explain
```

For example:

```
server:
  vision_explain: http://111.111.111.111:8003/mcp/vision/explain
```

Check the published URL from a browser before continuing.

### Step 4: Test the camera

Wake the device, ask it to open the camera and describe what it sees, and check server logs for errors.

Chinese text inside the preserved log/response blocks records historical output; the English explanations above provide its complete operational meaning. Configuration placeholders remain exact and have English definitions beside their examples.
