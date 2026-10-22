# PaddleSpeechTTS integration

## Important limitations

PaddleSpeech supports fast, local offline synthesis. As of the original guide's September 25, 2025 snapshot, the default model supports Chinese but not English; English text can produce no audio. Supporting both languages requires suitable training/model configuration.

## 1. Base environment

Use Windows, Linux, or WSL 2, Python 3.9 or later as supported by Paddle, and Conda or venv. Select the appropriate Paddle release for your CPU/GPU and Python version using the [official installation page](https://www.paddlepaddle.org.cn/install).

## 2. Start PaddleSpeech

### 1. Clone the source

```bash 
git clone https://github.com/PaddlePaddle/PaddleSpeech.git
```

### 2. Create an environment

```bash

conda create -n paddle_env python=3.10 -y
conda activate paddle_env
```

### 3. Install Paddle

Follow the supported platform/Python instructions at:

```
https://www.paddlepaddle.org.cn/install
```

### 4. Enter the source directory

```bash
cd PaddleSpeech
```

### 5. Install dependencies

```bash
pip install pytest-runner -i https://pypi.tuna.tsinghua.edu.cn/simple

# Use either of the following commands (as written in the original guide)
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
pip install paddlespeech -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. Download the speech model

Run this Chinese-language synthesis fixture. Its text means “Hello, this is a test” and must remain Chinese for the default Chinese-only model:

```bash
paddlespeech tts --input "你好，这是一次测试"
```

The command downloads the model cache under `.paddlespeech/models`.

### 7. Configure the transport

Open `PaddleSpeech\demos\streaming_tts_server\conf\tts_online_application.yaml` in an editor and set `protocol` to `websocket`.

### 8. Start the service

Use the command matching your actual configuration path:

```bash
paddlespeech_server start --config_file ./demos/streaming_tts_server/conf/tts_online_application.yaml
# Official default startup command:
paddlespeech_server start --config_file ./conf/tts_online_application.yaml
```

Successful startup looks like:

```
Prefix dict has been built successfully.
[2025-08-07 10:03:11,312] [   DEBUG] __init__.py:166 - Prefix dict has been built successfully.
INFO:     Started server process [2298]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8092 (Press CTRL+C to quit)
```

## 3. Configure Xiaozhi

The provider implementation is `main/xiaozhi-server/core/providers/tts/paddle_speech.py`.

For a server-only deployment, edit `main/xiaozhi-server/data/.config.yaml`:

```yaml
selected_module:
  TTS: PaddleSpeechTTS
TTS:
  PaddleSpeechTTS:
      type: paddle_speech
      protocol: websocket 
      url:  ws://127.0.0.1:8092/paddlespeech/tts/streaming  # Local TTS service URL [WebSocket default: ws://127.0.0.1:8092/paddlespeech/tts/streaming]
      spk_id: 0  # Speaker ID; 0 usually selects the default voice
      sample_rate: 24000  # Sample rate [WebSocket default 24000; HTTP default 0 selects automatically]
      speed: 1.0  # Speed: 1.0 normal, >1 faster, <1 slower
      volume: 1.0  # Volume: 1.0 normal, >1 louder, <1 quieter
      save_path:   # Output path
```

Start Xiaozhi:

```bash
python app.py
```

In `main/digital-human`, run `python start.py`, open `http://127.0.0.1:8006/index.html`, connect, and send a message. Check that PaddleSpeech logs the request.

The original log below retains the Chinese synthesis text (“Haha, why did you suddenly come chat with me?”) as speech fixture data. It also shows the accepted WebSocket connection, duration, first/final response latency, real-time factor, inference timings, and completed synthesis:

```
INFO:     127.0.0.1:44312 - "WebSocket /paddlespeech/tts/streaming" [accepted]
INFO:     connection open
[2025-08-07 11:16:33,355] [    INFO] - sentence: 哈哈，怎么突然找我聊天啦？
[2025-08-07 11:16:33,356] [    INFO] - The durations of audio is: 2.4625 s
[2025-08-07 11:16:33,356] [    INFO] - first response time: 0.1143045425415039 s
[2025-08-07 11:16:33,356] [    INFO] - final response time: 0.4777836799621582 s
[2025-08-07 11:16:33,356] [    INFO] - RTF: 0.19402382942625715
[2025-08-07 11:16:33,356] [    INFO] - Other info: front time: 0.06514096260070801 s, first am infer time: 0.008037090301513672 s, first voc infer time: 0.04112648963928223 s,
[2025-08-07 11:16:33,356] [    INFO] - Complete the synthesis of the audio streams
INFO:     connection closed

```
