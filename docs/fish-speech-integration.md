# Fish Speech integration on AutoDL

Sign in to AutoDL and rent an instance with this image:

```
PyTorch / 2.1.0 / 3.10(ubuntu22.04) / cuda 12.1
```

After startup, enable the instance's academic-network acceleration:

```
source /etc/network_turbo
```

Enter the working directory:

```
cd autodl-tmp/
```

Clone the project:

```
git clone https://gitclone.com/github.com/fishaudio/fish-speech.git ; cd fish-speech
```

Install dependencies:

```
pip install -e.
```

If PortAudio is missing, install it:

```
apt-get install portaudio19-dev -y
```

Then install these PyTorch versions:

```
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```

Download models:

```
cd tools
python download_models.py 
```

Start the API:

```
python -m tools.api_server --listen 0.0.0.0:6006 
```

Open the AutoDL instance list:

```
https://autodl.com/console/instance/list
```

Click **Custom Service** for the instance. In the dialog, select your local operating system (**Windows** or **Linux/Mac**). Copy that instance's SSH forwarding command and run it locally in PowerShell or a terminal. The shown form forwards local port 6006 to remote `127.0.0.1:6006`; use your instance's SSH host/port, not the screenshot's values. Accept the host-key prompt if you have verified it, then enter the supplied password. Password entry may show no characters. No further output after login is normal; **Permission denied** indicates a failed login, possibly a pasted password issue.

![AutoDL custom-service SSH tunnel instructions](images/fishspeech/autodl-01.png)

Keep the tunnel running and open `http://localhost:6006/` on your computer. The expected Fish Speech API page lists endpoints including `/v1/vqgan/encode`, `/v1/vqgan/decode`, `/v1/asr`, `/v1/tts`, and `/v1/chat`:

![Fish Speech API at localhost port 6006](images/fishspeech/autodl-02.png)

For a server-only deployment, use this configuration. The Chinese `reference_text` remains exact because it is the transcript paired with `config/assets/wakeup_words.wav`, not a maintainer instruction. It is a greeting from Xiaozhi in a Taiwanese-girl persona who enjoys conversation and gossip.

```
selected_module:
  TTS: FishSpeech
TTS:
  FishSpeech:
    reference_audio: ["config/assets/wakeup_words.wav",]
    reference_text: ["哈啰啊，我是小智啦，声音好听的台湾女孩一枚，超开心认识你耶，最近在忙啥，别忘了给我来点有趣的料哦，我超爱听八卦的啦",]
    api_key: "123"
    api_url: "http://127.0.0.1:6006/v1/tts"
```

Restart the service after configuration.
