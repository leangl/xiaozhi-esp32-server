# MCP endpoint deployment guide

This guide covers deploying the endpoint service, configuring a full-module installation, and configuring a server-only installation.

# 1. Deploy the MCP endpoint service

## Step 1: Download the source

Open [mcp-endpoint-server](https://github.com/xinnan-tech/mcp-endpoint-server), select **Code > Download ZIP**, extract the archive, and rename `mcp-endpoint-server-main` to `mcp-endpoint-server`.

## Step 2: Start the program

Docker is the recommended method below. For source deployment, see the [development README](https://github.com/xinnan-tech/mcp-endpoint-server/blob/main/README_dev.md).

```
# Enter the project root
cd mcp-endpoint-server

# Remove the previous containers and image
docker compose -f docker-compose.yml down
docker stop mcp-endpoint-server
docker rm mcp-endpoint-server
docker rmi ghcr.nju.edu.cn/xinnan-tech/mcp-endpoint-server:latest

# Start the Docker container
docker compose -f docker-compose.yml up -d
# Read logs
docker logs -f mcp-endpoint-server
```

The historical log below prints two secret-bearing URLs. Its Chinese labels distinguish the console's HTTP health/configuration endpoint from the server-only WebSocket endpoint and warn you not to disclose either URL.

```
250705 INFO-=====下面的地址分别是智控台/单模块MCP接入点地址====
250705 INFO-智控台MCP参数配置: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
250705 INFO-单模块部署MCP接入点: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
250705 INFO-=====请根据具体部署选择使用，请勿泄露给任何人======
```

Copy both URLs to a private note. Docker may print internal container IPs; replace the host with your computer's reachable LAN IP. For a host at `192.168.1.25`, change:

```
智控台MCP参数配置: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
单模块部署MCP接入点: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
```

to:

```
智控台MCP参数配置: http://192.168.1.25:8004/mcp_endpoint/health?key=abc
单模块部署MCP接入点: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

The first line in each block is for console configuration; the second is the server-only endpoint. Original labels remain as historical output examples. Open the first HTTP URL in a browser. A response like this indicates success:

```
{"result":{"status":"success","connections":{"tool_connections":0,"robot_connections":0,"total_connections":0}},"error":null,"id":null,"jsonrpc":"2.0"}
```

Keep both URLs for the next step.

# 2. Configure a full-module deployment

In the console, open **Parameters and Dictionaries > System Feature Configuration**, enable **MCP Endpoint**, and save. **Role Configuration > Edit Functions** should now display the endpoint feature.

As administrator, open **Parameters and Dictionaries > Parameter Management**. Find `server.mcp_endpoint`, whose initial value should be `null`. Click **Edit**, paste the console HTTP health/configuration URL into **Parameter Value**, and save.

If saving succeeds, inspect the agent's endpoint status. If it fails, the console cannot reach the endpoint; check firewalls and the configured LAN IP.

# 3. Configure a server-only deployment

Open `data/.config.yaml` and find `mcp_endpoint`, or add it if absent:

```
server:
  websocket: ws://你的ip或者域名:端口号/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# Additional configuration may appear here..

mcp_endpoint: 你的接入点websocket地址
```

The original placeholders remain unchanged: `你的ip或者域名:端口号` means “your IP or domain:port”; `你的接入点websocket地址` means “your endpoint WebSocket address”. Replace `mcp_endpoint` with the server-only WebSocket URL from section 1:

```
server:
  websocket: ws://你的ip或者域名:端口号/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# Additional configuration may appear here

mcp_endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

Start the server. The preserved historical log below shows successful VAD/ASR initialization followed by OTA, vision, MCP, and WebSocket addresses. It warns that the WebSocket address is not a browser page and recommends the digital-human interaction test.

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

An MCP endpoint line such as `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc` confirms that the endpoint setting loaded.

