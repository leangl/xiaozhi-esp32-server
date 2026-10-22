# Integrate the Xiaozhi ESP32 server with Home Assistant

[TOC]

## Introduction

This guide connects an ESP32 voice assistant to Home Assistant.

## Prerequisites

Install and configure `HomeAssistant`. The example uses ChatGLM, whose free model supports function calling.

## Required preparation

### 1. Find the Home Assistant address

Open your Home Assistant address in a browser. For example, host `192.168.4.7` with default port `8123`:

```
http://192.168.4.7:8123
```

If the server and Home Assistant share a LAN or Wi-Fi network, you can find the IP in **Settings > System > Network**. Scroll to **Home Assistant URL**, find **Local Network**, and click the eye icon to reveal the address/interface. **Copy Link** copies the URL.

![Find the local Home Assistant URL](images/image-ha-integration-01.png)

If your environment resolves it, you can also use the configured local address:

```
http://homeassistant.local:8123
```

### 2. Create a long-lived access token

Sign in, click your avatar at the lower left, open your profile's **Security** tab, and scroll to **Long-Lived Access Tokens**. Generate an API key and keep it safe: the UI displays it only once. The original guide suggests keeping its QR image if you need to extract the key later; treat that image as a secret too.

## Method 1: Community Home Assistant tools

### Behavior and requirements

Restart `xiaozhi-esp32-server` after adding devices so it reloads the device list. Integrate `Xiaomi Home` in Home Assistant and import the Mi Home devices. The management console must be working. The original example uses version `0.3.10`, with Home Assistant and the console on one machine at different ports:

```
  http://192.168.4.7:8002
  ```

### 1. Prepare the device list

In Home Assistant, open **Settings > Devices & Services > Entities**. Search for each switch, open its control panel, and toggle it to confirm it works. Open its settings and copy its **Entity ID**.

Build entries in this format: location, ASCII comma, device name, ASCII comma, entity ID, ASCII semicolon. The first original entry means “office, toy lamp”:

```
公司,玩具灯,switch.cuco_cn_460494544_cp1_on_p_2_1;
```

For two lamps, the second entry adds an “office, desk lamp”:

```
公司,玩具灯,switch.cuco_cn_460494544_cp1_on_p_2_1;
公司,台灯,switch.iot_cn_831898993_socn1_on_p_2_1;
```

Chinese location/device labels remain as multilingual spoken-name data; entity IDs and delimiters remain exact. Save this device-list string for the next step.

### 2. Configure the console

As administrator, open **Agent Management**, choose your agent, and select **Configure Role**.

![Home Assistant tools in agent function configuration](images/image-ha-integration-06.png)

Set intent recognition to **External LLM Intent Recognition** or **LLM Autonomous Function Calling**. Click **Edit Functions**. In **Function Management**, enable **HomeAssistant Device State Query** and **HomeAssistant Device State Modification**.

Under **Selected Functions**, click the state-query tool and enter the Home Assistant address, token, and device-list string in **Parameter Configuration**. Click **Save Configuration**, then save the outer agent configuration too.

### 3. Test control

Wake the ESP32 and ask it to turn on a named light.

## Method 2: Use Home Assistant's conversation agent as the LLM

### Behavior

This hands intent recognition to Home Assistant, so Xiaozhi's `function_call` plugins are unavailable. You retain Home Assistant's native operations and conversation abilities. [Method 3](#method-3-home-assistant-mcp-server-recommended) allows Home Assistant operations alongside Xiaozhi plugins.

### Configuration

1. Configure a voice assistant or LLM integration in Home Assistant first.
2. Open **Developer Tools > Actions**. Find/select `conversation.process` (“Conversation: Process”):

![Choose conversation.process in Developer Tools](images/image-ha-integration-02.png)

3. Enable **Agent** and select your configured **Conversation Agent**, such as `ZhipuAi`:

![Select the configured conversation agent](images/image-ha-integration-03.png)

4. Click **Go to YAML Mode** at the lower left:

![Switch the action form to YAML mode](images/image-ha-integration-04.png)

5. Copy the `agent_id` value. The pictured `01JP2DYMBDF7F4ZA2DMCF2AGX2` is only an example:

![Copy agent_id from the YAML](images/image-ha-integration-05.png)

6. In `config.yaml`, find the Home Assistant LLM configuration and enter your Home Assistant URL, API key, and `agent_id`.
7. Set `selected_module.LLM` to `HomeAssistant` and `selected_module.Intent` to `nointent`.
8. Restart `xiaozhi-esp32-server`.

## Method 3: Home Assistant MCP server (recommended)

### Behavior

Install Home Assistant's [Model Context Protocol Server](https://www.home-assistant.io/integrations/mcp_server/). Like method 2, this uses an official Home Assistant integration. Unlike method 2, it lets you keep Xiaozhi's community plugins and use an LLM with function-call support.

### 1. Install the MCP integration

Follow the [integration documentation](https://www.home-assistant.io/integrations/mcp_server/) or open [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations), click [Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=mcp_server), select **Model Context Protocol Server**, and follow the setup prompts.

### 2. Configure the Xiaozhi MCP client

Find `data/.mcp_server_settings.json`. If it does not exist, copy the root `xiaozhi-server/mcp_server_settings.json` there and rename it, or [download the template](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/main/xiaozhi-server/mcp_server_settings.json).

Edit this entry inside `mcpServers`:

```json
"Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "http://YOUR_HA_HOST/mcp_server/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "YOUR_API_ACCESS_TOKEN"
      }
},
```

Replace `YOUR_HA_HOST` in `args` with your host and port. Because the example already includes `http://`, enter only `192.168.1.101:8123` if your full URL is `http://192.168.1.101:8123`. Replace `YOUR_API_ACCESS_TOKEN` with the long-lived access token.

Remove the final comma if this is the last entry in `mcpServers`; otherwise JSON parsing fails. Example fragment:

```json
 "mcpServers": {
    "Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "http://192.168.1.101:8123/mcp_server/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "abcd.efghi.jkl"
      }
    }
  }
```

### 3. Configure the selected modules

Choose an LLM that supports `function_call`; do not select Home Assistant as the LLM for this method. The original example uses free ChatGLM but notes occasional unreliable tool calls. Its alternative is `DoubaoLLM` with `model_name: doubao-1-5-pro-32k-250115`.

Set your LLM configuration in `config.yaml`, set `selected_module.Intent` to `function_call`, and restart `xiaozhi-esp32-server`.
