# Context provider guide

## Overview

A context provider adds an external data source to Xiaozhi's system-prompt context. At wake-up, it fetches external data and injects it into the LLM's system prompt, giving the assistant the current state of something in the world.

Context providers supply data on each wake-up. Memory supplies earlier conversation content; MCP/function calling fetches a capability or knowledge when needed.

Examples include health sensors (temperature, blood pressure, oxygen saturation), live business-system data (server load, tasks, stock information), and text available through HTTP APIs.

For fresh updates after wake-up, combine a context provider with MCP tools.

## How it works

Configure one or more HTTP API URLs. During prompt construction, the system checks for `{{ dynamic_context }}`, requests all configured APIs, formats their responses as Markdown lists, and replaces that placeholder.

## API contract

Use `GET`. The system adds a `device-id` request header. Return JSON containing `code` and `data`.

### Dictionary response

This original multilingual fixture means: living-room temperature 26°C, living-room humidity 45%, and front door closed. Chinese keys and values remain unchanged as API/locale example data:

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "客厅温度": "26℃",
    "客厅湿度": "45%",
    "大门状态": "已关闭"
  }
}
```

Injected form:

```markdown
<context>
- **客厅温度：** 26℃
- **客厅湿度：** 45%
- **大门状态：** 已关闭
</context>
```

### List response

This fixture says “you have 10 pending tasks” and “the car is traveling at 100 km/h”:

```json
{
  "code": 0,
  "data": [
    "您有10个待办事项",
    "当前汽车的行驶速度是100km每小时"
  ]
}
```

Injected form:

```markdown
<context>
- 您有10个待办事项
- 当前汽车的行驶速度是100km每小时
</context>
```

## Configuration

### Method 1: Full-module console

Open **Role Configuration > Context Providers** using **Edit Sources**. Click **Add**, enter the API URL, add `Authorization` or other headers if required, and save.

### Method 2: Server-only configuration

Add `context_providers` to `xiaozhi-server/data/.config.yaml`:

```yaml
# Context provider configuration
context_providers:
  - url: "http://api.example.com/data"
    headers:
      Authorization: "Bearer your-token"
  - url: "http://another-api.com/data"
```

## Enable the feature

The default prompt template `data/.agent-base-prompt.txt` already includes `{{ dynamic_context }}`; you do not need to add it:

```markdown
<context>
[Important: this information is provided in real time. Use it directly without querying tools.]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
...
{{ dynamic_context }}
</context>
```

To disable this feature, leave the provider list empty or remove `{{ dynamic_context }}` from the prompt template.

## Appendix: Mock API server

Use this local `mock_api_server.py` example for testing. Its Chinese response data remains as multilingual fixtures, while comments and diagnostics are in English.

- `/health`: test device ID, heart rate 80 bpm, blood pressure 120/80 mmHg, and a “good” state.
- `/news/list`: headlines about Python 3.14, AI assistants, and tomorrow's heavy rain.
- `/weather/simple`: clear becoming cloudy, 20–25°C, good air quality, suitable for travel.
- `/device/info`: header-based lookup, device ID, 85% battery, firmware v2.0.1.
- Unknown paths: HTTP 404 with the original `error` fixture value `接口不存在` (“endpoint does not exist”).

```python
import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

# Listening port
PORT = 8081

class MockRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the path and query parameters
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        response_data = {}
        status_code = 200

        print(f"Received request: {path}, parameters: {query}")

        # Case 1: Mock health data (dictionary response)
        # Path endpoint: /health
        # Read device_id from the request header
        if path == "/health":
            device_id = self.headers.get("device-id", "unknown_device")
            print(f"device_id: {device_id}")
            response_data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "测试设备ID": device_id,
                    "心率": "80 bpm",
                    "血压": "120/80 mmHg",
                    "状态": "良好"
                }
            }

        # Case 2: Mock news (list response)
        # No parameters: /news/list
        elif path == "/news/list":
            response_data = {
                "code": 0,
                "msg": "success",
                "data": [
                    "今日头条：Python 3.14 发布",
                    "科技新闻：AI 助手改变生活",
                    "本地新闻：明日有大雨，记得带伞"
                ]
            }

        # Case 3: Mock weather summary (string response)
        # No parameters: /weather/simple
        elif path == "/weather/simple":
            response_data = {
                "code": 0,
                "msg": "success",
                "data": "今日晴转多云，气温 20-25 度，空气质量优，适合出行。"
            }

        # Case 4: Mock device details (query-parameter style)
        # Endpoint: /device/info
        # Read device_id from the request header
        elif path == "/device/info":
            device_id = self.headers.get("device-id", "unknown_device")
            response_data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "查询方式": "Header参数",
                    "设备ID": device_id,
                    "电量": "85%",
                    "固件": "v2.0.1"
                }
            }
        
        # Case 5: 404 Not Found
        else:
            status_code = 404
            response_data = {"error": "接口不存在"}

        # Send the response
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

# Start the service
# Allow address reuse to avoid errors after quick restarts
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MockRequestHandler) as httpd:
    print(f"==================================================")
    print(f"Mock API Server started: http://localhost:{PORT}")
    print(f"Available endpoints:")
    print(f"1. [dictionary] http://localhost:{PORT}/health")
    print(f"2. [list] http://localhost:{PORT}/news/list")
    print(f"3. [text] http://localhost:{PORT}/weather/simple")
    print(f"4. [parameters] http://localhost:{PORT}/device/info")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nService stopped")
```
