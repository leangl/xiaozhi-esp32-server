# MQTT gateway deployment

The `xiaozhi-esp32-server` project can support hardware MQTT+UDP connections using a modified version of the upstream [xiaozhi-mqtt-gateway](https://github.com/78/xiaozhi-mqtt-gateway). This guide covers gateway deployment, then full-module and server-only configuration.

## Preparation

Append `?from=mqtt_gateway` to the server's WebSocket address to obtain its MQTT-gateway WebSocket URL.

For source deployment:

```
ws://127.0.0.1:8000/xiaozhi/v1/?from=mqtt_gateway
```

For Docker:

```
ws://你宿主机局域网IP:8000/xiaozhi/v1/?from=mqtt_gateway
```

The original placeholder `你宿主机局域网IP` means “your host's LAN IP”; replace it.

## Required ports

Open TCP ports `1883` and `8007`, and **UDP** port `8884` on the server. The protocol choice matters.

## Part 1: Deploy the gateway

1. Clone the [modified gateway](https://github.com/xinnan-tech/xiaozhi-mqtt-gateway.git):

```bash
git clone https://ghfast.top/https://github.com/xinnan-tech/xiaozhi-mqtt-gateway.git
cd xiaozhi-mqtt-gateway
```

2. Install dependencies:

```bash
npm install
npm install -g pm2
```

3. Copy the example configuration:

```bash
cp config/mqtt.json.example config/mqtt.json
```

4. Edit `config/mqtt.json`. Set `chat_servers` to the URL from Preparation. Source-mode example:

``` 
{
    "production": {
        "chat_servers": [
            "ws://127.0.0.1:8000/xiaozhi/v1/?from=mqtt_gateway"
        ]
    },
    "debug": false,
    "max_mqtt_payload_size": 8192,
    "mcp_client": {
        "capabilities": {
        },
        "client_info": {
            "name": "xiaozhi-mqtt-client",
            "version": "1.0.0"
        },
        "max_tools_count": 128
    }
}
```

5. Create `.env` in the gateway project root:

```
PUBLIC_IP=your-ip         # Server public IP
MQTT_PORT=1883            # MQTT server port
UDP_PORT=8884             # UDP server port
API_PORT=8007             # Management API port
MQTT_SIGNATURE_KEY=test   # MQTT signing key
SERVER_SECRET=Te1st12134  # Server secret: match console server.secret or xiaozhi-server server.auth_key
```

Set `PUBLIC_IP` to the actual public IP or domain. Use a strong `MQTT_SIGNATURE_KEY`, preferably more than eight characters with upper- and lowercase letters. Avoid simple passwords such as `123456` or `test`. Keep the key for server configuration below.

`SERVER_SECRET` generates WebSocket authentication information. If `server.auth.enabled` is `true`, match the console's `server.secret` for full-module deployments or the configuration file's `server.auth_key` for server-only deployments.

6. Start the gateway:

```
# Start the service
pm2 start ecosystem.config.js

# Read logs
pm2 logs xz-mqtt
```

The original historical log means “MQTT server listening on port 1883” and “UDP server listening on x.x.x.x:8884”:

```
0|xz-mqtt  | 2025-09-11T12:14:48: MQTT 服务器正在监听端口 1883
0|xz-mqtt  | 2025-09-11T12:14:48: UDP 服务器正在监听 x.x.x.x:8884
```

To restart it later:

```
pm2 restart xz-mqtt
```

## Part 2: Full-module MQTT+UDP configuration

Check the version at the bottom of the console home page. Upgrade if it is below `0.7.7`.

In **Parameter Management**:

1. Set `server.mqtt_gateway` to `PUBLIC_IP:MQTT_PORT` from `.env`:

```
192.168.0.7:1883
```

2. Set `server.mqtt_signature_key` to the same `MQTT_SIGNATURE_KEY`.
3. Set `server.udp_gateway` to `PUBLIC_IP:UDP_PORT`:

```
192.168.0.7:8884
```

4. Set `server.mqtt_manager_api` to `PUBLIC_IP:API_PORT`:

```
192.168.0.7:8007
```

Check whether OTA returns MQTT settings. Replace `http://localhost:8002/xiaozhi/ota/` with your OTA URL:

```
curl 'http://localhost:8002/xiaozhi/ota/' \
  -H 'Content-Type: application/json' \
  -H 'Client-Id: 7b94d69a-9808-4c59-9c9b-704333b38aff' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw $'{\n  "application": {\n    "version": "1.0.1",\n    "elf_sha256": "1"\n  },\n  "board": {\n    "mac": "11:22:33:44:55:66"\n  }\n}'
```

A response containing `mqtt` configuration indicates success. Original wire-format example:

```
{"server_time":{"timestamp":1757567894012,"timeZone":"Asia/Shanghai","timezone_offset":480},"activation":{"code":"460609","message":"http://xiaozhi.server.com\n460609","challenge":"11:22:33:44:55:66"},"firmware":{"version":"1.0.1","url":"http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL"},"websocket":{"url":"ws://192.168.4.23:8000/xiaozhi/v1/"},"mqtt":{"endpoint":"192.168.0.7:1883","client_id":"GID_default@@@11_22_33_44_55_66@@@7b94d69a-9808-4c59-9c9b-704333b38aff","username":"eyJpcCI6IjA6MDowOjA6MDowOjA6MSJ9","password":"Y8XP9xcUhVIN9OmbCHT9ETBiYNE3l3Z07Wk46wV9PE8=","publish_topic":"device-server","subscribe_topic":"devices/p2p/11_22_33_44_55_66"}}
```

Devices receive MQTT settings through OTA. Confirm the OTA endpoint is reachable, restart/wake the device, and check the gateway logs for a successful connection:

```
pm2 logs xz-mqtt
```

## Part 3: Server-only MQTT+UDP configuration

Open `data/.config.yaml`. Under `server`, set `mqtt_gateway` to `PUBLIC_IP:MQTT_PORT`:

```
192.168.0.7:1883
```

Set `mqtt_signature_key` to `MQTT_SIGNATURE_KEY`, and `udp_gateway` to `PUBLIC_IP:UDP_PORT`:

```
192.168.0.7:8884
```

Test OTA delivery of MQTT configuration, replacing the OTA URL:

```
curl 'http://localhost:8002/xiaozhi/ota/' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw $'{\n  "application": {\n    "version": "1.0.1",\n    "elf_sha256": "1"\n  },\n  "board": {\n    "mac": "11:22:33:44:55:66"\n  }\n}'
```

A response containing `mqtt` settings indicates success. Original wire-format example:

```
{"server_time":{"timestamp":1758781561083,"timeZone":"GMT+08:00","timezone_offset":480},"activation":{"code":"527111","message":"http://xiaozhi.server.com\n527111","challenge":"11:22:33:44:55:66"},"firmware":{"version":"1.0.1","url":"http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL"},"websocket":{"url":"ws://192.168.1.15:8000/xiaozhi/v1/"},"mqtt":{"endpoint":"192.168.1.15:1883","client_id":"GID_default@@@11_22_33_44_55_66@@@11_22_33_44_55_66","username":"eyJpcCI6IjE5Mi4xNjguMS4xNSJ9","password":"fjAYs49zTJecWqJ3jBt+kqxVn/x7vkXRAc85ak/va7Y=","publish_topic":"device-server","subscribe_topic":"devices/p2p/11_22_33_44_55_66"}}
```

Confirm that the device reaches OTA, restart/wake it, and inspect the gateway connection logs:

```
pm2 logs xz-mqtt
```
