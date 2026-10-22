# Configure a custom server with prebuilt firmware

## Step 1: Check the version

Flash [upstream firmware version 1.6.1 or later](https://github.com/78/xiaozhi-esp32/releases).

## Step 2: Prepare your OTA address

A full-module deployment provides an OTA address. Open yours in a browser, for example:

```
https://2662r3426b.vicp.fun/xiaozhi/ota/
```

A healthy response says OTA is running and gives the WebSocket cluster count. If it reports an unhealthy endpoint, configure the WebSocket URL in the console: log in as super administrator, open **Parameter Management**, find `server.websocket`, and enter the device-reachable address. Example:

```
wss://2662r3426b.vicp.fun/xiaozhi/v1/
```

Refresh the OTA URL. If it still fails, check that the WebSocket server has started and that the address is correct.

## Step 3: Enter network setup mode

Enter the device's network setup mode. At the top of the setup page, open **Advanced Options**. Enter your server's OTA URL in the custom OTA/server-address field, save, and restart the device. This is the action illustrated below; keep the trailing `/xiaozhi/ota/` path.

![Custom OTA address in device network setup](../docs/images/firmware-setting-ota.png)

## Step 4: Wake Xiaozhi and inspect logs

Wake the device and check the server's output for a normal connection.

## Troubleshooting

See the [FAQ](./FAQ.md) for incorrect recognition languages, missing TTS files, TTS failures/timeouts, 4G connections, latency, interruptions during pauses, and smart-home control.
