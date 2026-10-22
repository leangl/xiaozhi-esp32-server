# MCP endpoint integration guide

This guide uses the open-source MCP calculator to connect a custom MCP service to your endpoint. First [enable MCP endpoints](./mcp-endpoint-enable.md) on `xiaozhi-server`.

# Add a calculator tool to an agent

### Full-module deployment

Open **Agent Management > Configure Role** in the console. Click **Edit Functions** beside **Intent Recognition**. At the bottom of the dialog, find **MCP Endpoint** and copy the agent's **MCP Endpoint Address**. You will need it below.

### Server-only deployment

If you have configured an endpoint, startup prints a log like this. The preserved Chinese lines are historical output: VAD and ASR initialize, then the server lists OTA, vision, MCP, and WebSocket URLs. The warning says to use the digital-human module for browser interaction tests, not open the WebSocket URL as a web page.

```
250705[__main__]-INFO-初始化组件: vad成功 SileroVAD
250705[__main__]-INFO-初始化组件: asr成功 FunASRServer
250705[__main__]-INFO-OTA接口是          http://192.168.1.25:8002/xiaozhi/ota/
250705[__main__]-INFO-视觉分析接口是     http://192.168.1.25:8002/mcp/vision/explain
250705[__main__]-INFO-mcp接入点是        ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
250705[__main__]-INFO-Websocket地址是    ws://192.168.1.25:8000/xiaozhi/v1/
250705[__main__]-INFO-=======上面的地址是websocket协议地址，请勿用浏览器访问=======
250705[__main__]-INFO-如想测试websocket请启动digital-human模块，打开浏览器交互测试
250705[__main__]-INFO-=============================================================
```

In this example, the MCP endpoint address is `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc`. Copy your actual address for the next step.

## Step 1: Download the MCP calculator

Open the [calculator project](https://github.com/78/mcp-calculator), select **Code > Download ZIP**, and extract it. Rename `mcp-calculator-main` to `mcp-calculator`. Enter the directory and install dependencies. The environment-removal command deletes any existing environment with this name.

```bash
# Enter the project directory
cd mcp-calculator

conda remove -n mcp-calculator --all -y
conda create -n mcp-calculator python=3.10 -y
conda activate mcp-calculator

pip install -r requirements.txt
```

## Step 2: Start the calculator

Copy your agent's MCP endpoint from the console or server logs. Example:

```
ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Set it in the environment:

```bash
export MCP_ENDPOINT=ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Start the process:

```bash
python mcp_pipe.py calculator.py
```

### Console deployment

Refresh the agent's MCP connection status in the console. You should see the added tools.

### Server-only deployment

After a device connects, a successful historical log looks like this. The Chinese lines mean: initialize the endpoint, send initialization, connect, complete initialization, initialize the unified tool handler, list server identity and tool count, finish fetching tools, refresh the cache, and list supported functions.

```
250705 -INFO-正在初始化MCP接入点: wss://2662r3426b.vicp.fun/mcp_e 
250705 -INFO-发送MCP接入点初始化消息
250705 -INFO-MCP接入点连接成功
250705 -INFO-MCP接入点初始化成功
250705 -INFO-统一工具处理器初始化完成
250705 -INFO-MCP接入点服务器信息: name=Calculator, version=1.9.4
250705 -INFO-MCP接入点支持的工具数量: 1
250705 -INFO-所有MCP接入点工具已获取，客户端准备就绪
250705 -INFO-工具缓存已刷新
250705 -INFO-当前支持的函数列表: [ 'get_time', 'get_lunar', 'play_music', 'get_weather', 'handle_exit_intent', 'calculator']
```

If `'calculator'` appears in the function list, the device can call that tool through intent recognition.
