# Weather plugin guide

## Overview

The `get_weather` plugin lets the Xiaozhi ESP32 voice assistant query weather across China. It uses QWeather for current conditions and seven-day forecasts.

## Obtain an API key

### 1. Register with QWeather

Open the [QWeather console](https://console.qweather.com/), register, verify your email, and sign in.

### 2. Create a project and credentials

1. Open [Project Management](https://console.qweather.com/project?lang=zh) and select **Create Project**.
2. Enter a project name, such as “Xiaozhi Voice Assistant”, and save.
3. In that project, select **Create Credential**.
4. Give the credential a name, choose **API Key** authentication, and save.
5. Copy the generated `API Key`.

### 3. Obtain the API Host

Open [Settings](https://console.qweather.com/setting?lang=zh) and select **API Host**. Copy the dedicated host assigned to your account. You need both the key and host.

## Configure the plugin

### Method 1: Management console (recommended)

1. Sign in, open **Role Configuration**, and select an agent.
2. Select **Edit Functions**, find **Weather Query** in the right-hand parameter area, and enable it.
3. Paste the key into **Weather Plugin API Key** and the host into **Developer API Host**.
4. Save the function configuration, then save the agent.

### Method 2: Server-only deployment

In `data/.config.yaml`, set `api_key`, `api_host`, and `default_location` (for example, Guangzhou).

The original placeholder values below remain unchanged: `你的和风天气API密钥` means your QWeather API key; `你的和风天气API主机地址` means your QWeather API host; `你的默认查询城市` means your default query city. Replace them with your values.

```yaml
plugins:
  get_weather:
    api_key: "你的和风天气API密钥"
    api_host: "你的和风天气API主机地址"
    default_location: "你的默认查询城市"
```

