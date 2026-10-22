# Device-to-device calling plugin

## Overview

Two configured devices can communicate over bidirectional voice/data channels:

```text
Device A → authorization check → MQTT gateway → remote wake-up of device B → connection → call
```

## Prerequisites

1. At least two `ESP32-S3` devices. This model supports remote wake-up.
2. Two microphones per device. You can try one microphone, but expect severe stuttering.
3. A [full-module deployment](Deployment_all.md), because the console manages permissions and communication.
4. A configured [MQTT gateway](mqtt-gateway-integration.md) with code from after May 27, 2026. Check the gateway version if you already deployed it.

## Configuration

### Step 1: Enable contacts

Use console version `0.9.4` or later. Sign in, open **System Feature Configuration**, enable **Contacts** in the feature list, and click **Save Configuration**.

### Step 2: Grant calling permissions

Open **Contacts** in the top menu. Under the agent on the left, select device A; you can search by MAC address or note name. In the right-hand details, set a spoken name for device B, enable its **Calling Permission**, and save.

For communication in both directions, configure each side:

- Allow B in A's configuration so A can contact B.
- Allow A in B's configuration so B can contact A.

### Step 3: Add the calling tool to the agent

Open **Agent Management**, find the agent associated with those contacts, select **Edit Role**, then **Edit Functions**. Enable **Device Calls Device**, save the function configuration, save the outer agent configuration, and restart the device.

### Step 4: Add the firmware remote-wake-up tool

The original instructions target [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) versions 2.1.0 through 2.2.6 (the May 29, 2026 version).

In `application.h`, add:

```cpp
    void RemoteWakeup(const std::string& reason);
    ```

In `application.cc`, add:

```cpp
    void Application::RemoteWakeup(const std::string& reason){
        if (!protocol_) {
            return;
        }

        auto state = GetDeviceState();
        
        if (state == kDeviceStateIdle) {
            audio_service_.EncodeWakeWord();

            if (!protocol_->IsAudioChannelOpened()) {
                SetDeviceState(kDeviceStateConnecting);
                if (!protocol_->OpenAudioChannel()) {
                    audio_service_.EnableWakeWordDetection(true);
                    return;
                }
            }
            std::string wake_word = reason;
    #if CONFIG_USE_AFE_WAKE_WORD || CONFIG_USE_CUSTOM_WAKE_WORD
            // Encode and send the wake word data to the server
            while (auto packet = audio_service_.PopWakeWordPacket()) {
                protocol_->SendAudio(std::move(packet));
            }
            // Set the chat state to wake word detected
            protocol_->SendWakeWordDetected(wake_word);
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #else
            // Set flag to play popup sound after state changes to listening
            // (PlaySound here would be cleared by ResetDecoder in EnableVoiceProcessing)
            play_popup_on_listening_ = true;
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #endif
        } else if (state == kDeviceStateSpeaking) {
            AbortSpeaking(kAbortReasonWakeWordDetected);
            SetDeviceState(kDeviceStateIdle);
        } else if (state == kDeviceStateActivating) {
            SetDeviceState(kDeviceStateIdle);
        }
    }
    ```

In `mcp_server.cc`, add the remote-wake-up tool:

```cpp
    AddUserOnlyTool("self.remote_wakeup", "Remote wakeup function with configurable parameters",
        PropertyList({
            Property("reason", kPropertyTypeString, "Wakeup reason"),
        }),
        [this](const PropertyList& properties) -> ReturnValue {
            std::string reason = properties["reason"].value<std::string>();
            ESP_LOGI(TAG, "Wakeup reason=%s", reason.c_str());
            auto& app = Application::GetInstance();
            app.RemoteWakeup(reason);
            return true;
    ```

This last excerpt is an original partial C++ snippet; complete its surrounding registration syntax against your firmware version. This documentation translation preserves it rather than making an untested firmware change.

Follow the [firmware build and flashing guide](firmware-build.md). Enable **AEC** during compilation whether the device has one microphone or two.

### Step 5: Configure the MQTT gateway

Follow the [MQTT gateway guide](mqtt-gateway-integration.md). Check that an existing gateway includes the May 27, 2026 changes or later.

## Call flow

Prepare both devices, grant permissions in the console, and add the calling tool to the agent. Tell one device to call the other's configured name, then check whether device B responds.

## Troubleshooting

### Device B does not respond

Check that B is online in the console, that its firmware includes the remote-wake-up tool, that the MQTT gateway connection works, and that both sides' permissions are configured.

### No calling permission

Check that A's configuration allows B and that you saved the change.

### Confirm that contacts are enabled

The console's top menu should show **Contacts**.

### ASR confuses similar contact names

The Chinese examples `张山` and `张三` are distinct names with similar pronunciation; they remain as ASR language fixtures. Check your ASR provider's hotword support.

For `FunASRServer`, add the intended name to the container's hotword file and restart that container. For Volcengine, add a hotword file in its console, then set that file's name in the model configuration. The original guide refers to the Volcengine TTS setting here; verify the provider-specific ASR/hotword setting before applying it.

