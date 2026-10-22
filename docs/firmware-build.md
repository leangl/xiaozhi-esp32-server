# Build ESP32 firmware

## Step 1: Prepare your OTA address

Since server version 0.3.12, both server-only and full-module deployments provide an OTA address. The setup differs between these modes.

### Server-only deployment

Open your OTA URL in a browser. Example:

```
http://192.168.1.25:8003/xiaozhi/ota/
```

A healthy response states that OTA is running and gives the device WebSocket address, such as `ws://xxx:8000/xiaozhi/v1/`. Start the digital-human module and use `index.html` to test that address.

If it cannot connect, correct `server.websocket` in `.config.yaml`, restart, and retest until the page can connect.

### Full-module deployment

Open your OTA URL. Example:

```
http://192.168.1.25:8002/xiaozhi/ota/
```

A healthy response states that OTA is running and reports the WebSocket cluster count. If it reports an unhealthy OTA endpoint, the console may lack a WebSocket address.

Log in as super administrator, open **Parameter Management**, find `server.websocket`, and enter your WebSocket URL:

```
ws://192.168.1.25:8000/xiaozhi/v1/
```

Refresh the OTA page. If it remains unhealthy, check that the WebSocket server started and that its address is configured.

## Step 2: Prepare the build environment

Follow [Set up ESP-IDF 5.3.2 and build Xiaozhi on Windows](https://icnynnzcwou8.feishu.cn/wiki/JEYDwTTALi5s2zkGlFGcDiRknXf).

## Step 3: Open the firmware configuration

Download the [xiaozhi-esp32 source](https://github.com/78/xiaozhi-esp32). Open `xiaozhi-esp32/main/Kconfig.projbuild`.

## Step 4: Change the OTA address

In `OTA_URL`, replace the `default` value `https://api.tenclass.net/xiaozhi/ota/` with your own OTA address, such as `http://192.168.1.25:8002/xiaozhi/ota/`.

Before:

```
config OTA_URL
    string "Default OTA URL"
    default "https://api.tenclass.net/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

After:

```
config OTA_URL
    string "Default OTA URL"
    default "http://192.168.1.25:8002/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

## Step 4: Set build parameters

```
# Enter the xiaozhi-esp32 repository root
cd xiaozhi-esp32
# This example targets esp32s3; replace it with the target for your board
idf.py set-target esp32s3
# Open menu configuration
idf.py menuconfig
```

In menu configuration, open **Xiaozhi Assistant** and set `BOARD_TYPE` to your board model. Save and return to the terminal.

## Step 5: Build firmware

```
idf.py build
```

## Step 6: Package the binary

```
cd scripts
python release.py
```

The packaging command generates `build/merged-binary.bin` in the project root. This is the image to flash to the hardware. If the second command reports a ZIP-related error but `merged-binary.bin` exists, the original guide permits continuing.

## Step 7: Flash the firmware

Connect the ESP32 to your computer and open this URL in Chrome:

```
https://espressif.github.io/esp-launchpad/
```

Follow [Flash tools / browser flashing without an IDF environment](https://ccnphfhqs21z.feishu.cn/wiki/Zpz4wXBtdimBrLk25WdcXzxcnNS), section **Method 2: ESP-Launchpad browser flashing**, starting at **3. Flash firmware / download to the development board**.

After flashing and connecting to the network, wake Xiaozhi and inspect the server console.

## Troubleshooting

The [FAQ](./FAQ.md) covers incorrect recognition languages, missing TTS files, TTS failures/timeouts, 4G connectivity, response latency, interruptions during pauses, and smart-home control.
