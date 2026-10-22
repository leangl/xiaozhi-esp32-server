# Volcengine bidirectional streaming TTS and voice cloning

This guide covers preparation, configuration, cloning, and using a voice through the management console.

## Phase 1: Preparation

A super administrator must enable the Volcengine service and obtain an App Id and Access Token. The provider may include one voice resource; copy that resource into this project. To clone more voices, purchase additional resources, copy each voice ID (`S_xxxxx`), and assign it to a system account.

### 1. Enable the service

Open https://console.volcengine.com/speech/app and create an application in **Application Management**. Enable the large-model speech synthesis and voice-cloning services.

### 2. Obtain the voice resource ID

Open https://console.volcengine.com/speech/service/9999 and copy **App Id**, **Access Token**, and **Voice ID** (`S_xxxxx`). These are the three values illustrated in the provider screenshot:

![Volcengine application credentials and voice resource](images/image-clone-integration-01.png)

## Phase 2: Configure Volcengine

### 1. Enter provider credentials

As super administrator, open **Model Configuration > Text-to-Speech**. Find **Volcengine Bidirectional Streaming TTS**, click **Edit**, put App Id in **Application ID** and Access Token in **Access Token**, then save.

### 2. Assign a voice resource to an account

Open **Parameters and Dictionaries > System Feature Configuration**, enable **Voice Cloning**, and save. The top menu now includes **Voice Cloning**.

Open **Voice Cloning > Voice Resources** and click **Add**. Select **Volcengine Bidirectional Streaming TTS** as **Platform Name**. Enter the provider's `S_xxxxx` ID in **Voice Resource ID** and press Enter. In **Owner Account**, choose the system account to receive the resource, including your own if appropriate, and save.

## Phase 3: Clone the voice

Open **Voice Cloning > Voice Cloning**. If the page says your account has no voice resources and asks you to contact an administrator, return to phase 2 and assign a resource to that account.

If resources appear, select one and click **Upload Audio**. Choose an audio sample, listen to it or trim a segment, then confirm with **Upload Audio**. The screenshot shows the upload/preview/selection step:

![Upload and preview a voice sample](images/image-clone-integration-02.png)

After upload, the resource should show **Pending Cloning**. Click **Clone Now** and wait 1–2 seconds for the result. On failure, hover over the **Error Information** icon to read the cause. On success, the state becomes **Training Successful**. Use the edit button under **Voice Name** to give the resource a recognizable name.

## Phase 4: Use the cloned voice

Open **Agent Management**, choose an agent, and click **Configure Role**. Select **Volcengine Bidirectional Streaming TTS** as TTS. Choose a voice resource whose name includes **Cloned Voice**, then save. The screenshot illustrates this voice selection:

![Select a cloned voice for an agent](images/image-clone-integration-03.png)

Wake Xiaozhi and start a conversation.
