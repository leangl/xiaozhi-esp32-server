# Automatic firmware OTA upgrades for server-only deployments

Skip this guide for full-module deployments.

## Overview

The server-only `xiaozhi-server` includes OTA firmware management. It checks the reported device model and version, matches an available newer version, and offers the firmware update.

## Prerequisites

The server-only installation must be running, and the device must connect to it.

## Step 1: Prepare firmware files

### 1. Create the firmware directory

Put files in `data/bin/`; create it if necessary:

```bash
mkdir -p data/bin
```

### 2. File naming

Use this original naming pattern:

```
{设备型号}_{版本号}.bin
```

The placeholders mean “device model” and “version”. The model may be `lichuang-dev` or `bread-compact-wifi`. The version must start with a digit and may contain digits, letters, dots, underscores, and hyphens. The extension must be `.bin`.

Examples:

```
bread-compact-wifi_1.6.6.bin
lichuang-dev_2.0.0.bin
```

### 3. Copy the firmware

Use the application image `xiaozhi.bin`, **not** the full-flash image `merged-binary.bin`. Replace the original device-model/version placeholders:

```bash
cp xiaozhi.bin data/bin/设备型号_版本号.bin
```

For example:

```bash
cp xiaozhi.bin data/bin/bread-compact-wifi_1.6.6.bin
```

## Step 2: Configure the public address (public deployments only)

For a server-only deployment using a public IP or domain, set `server.vision_explain`. The server uses its host and port as the base for firmware download URLs. An incorrect or missing public address can make downloads unreachable.

LAN deployments can skip this step. In `data/.config.yaml`:

```yaml
server:
  vision_explain: http://你的域名或IP:端口号/mcp/vision/explain
```

The original placeholder `你的域名或IP:端口号` means “your domain or IP:port”. Replace it with the address the device can reach.

Default LAN example:

```yaml
server:
  vision_explain: http://192.168.1.100:8003/mcp/vision/explain
```

Public-domain example:

```yaml
server:
  vision_explain: http://yourdomain.com:8003/mcp/vision/explain
```

Use a device-reachable address, not a container-internal URL, `127.0.0.1`, or `localhost`. With Nginx reverse proxying, use the externally exposed host and port rather than the application's internal listening port.

## Troubleshooting

### 1. The device receives no update

Check the `{model}_{version}.bin` naming, the `data/bin/` directory, matching device model, a version newer than the device's current version, and server logs for OTA requests.

### 2. The download URL is unreachable

Check the host/IP in `server.vision_explain`, the port (default 8003), device access to the public address, Docker address selection, and firewall rules. For Nginx, use the externally exposed host/port.

### 3. Check the device's current version

OTA request logs include the version reported by the device. This original Chinese historical log means “device AA:BB:CC:DD:EE:FF already has the latest firmware: 1.6.6”:

```
[ota_handler] - 设备 AA:BB:CC:DD:EE:FF 固件已是最新: 1.6.6
```

### 4. A newly added file has no effect

The default firmware cache lasts 30 seconds. Wait 30 seconds before another OTA request, restart `xiaozhi-server`, or reduce `firmware_cache_ttl`.
