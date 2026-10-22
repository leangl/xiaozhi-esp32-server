# Start the digital-human module

## Overview

The test page integrates Sherpa-ONNX keyword detection with configurable wake words and real-time detection. The original guide describes the lightweight model as providing millisecond-scale responses.

## Wake-word models

### Download models (required)

The repository does not include the model files; download and configure them before starting.

- [Official model list](https://csukuangfj.github.io/sherpa/onnx/kws/pretrained_models/index.html)
- Recommended model: `sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01`.

### 1. Download the archive

```bash
# Method 1: Direct download (recommended)
cd main/digital-human/wakeword_runtime/
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01.tar.bz2

# Extract
tar xvf sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01.tar.bz2

# Method 2: ModelScope
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('pkufool/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01', cache_dir='./models')
"
```

### 2. Model package contents

```
sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/
├── encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx    # Speed-oriented
├── encoder-epoch-12-avg-2-chunk-16-left-64.onnx
├── encoder-epoch-99-avg-1-chunk-16-left-64.int8.onnx    # Speed-oriented
├── encoder-epoch-99-avg-1-chunk-16-left-64.onnx         # Accuracy-oriented
├── decoder-epoch-12-avg-2-chunk-16-left-64.onnx
├── decoder-epoch-99-avg-1-chunk-16-left-64.onnx         # Accuracy-oriented
├── joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx     # Speed-oriented
├── joiner-epoch-12-avg-2-chunk-16-left-64.onnx
├── joiner-epoch-99-avg-1-chunk-16-left-64.int8.onnx     # Speed-oriented
├── joiner-epoch-99-avg-1-chunk-16-left-64.onnx          # Accuracy-oriented
├── tokens.txt                    # Token mapping (required)
├── keywords_raw.txt              # May ship with the model (optional; runtime does not depend on it)
├── keywords.txt                  # Prebuilt keywords
├── test_wavs/                    # Test audio (optional)
├── configuration.json            # Model metadata (optional)
└── README.md                     # Documentation (optional)
```

### 3. Choose a configuration

Accuracy-oriented configuration (recommended):

```bash
cd sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01

# Create the model directory
mkdir -p ../models

# Copy the accuracy-oriented epoch-99 fp32 model set
cp encoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/encoder.onnx
cp decoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/decoder.onnx
cp joiner-epoch-99-avg-1-chunk-16-left-64.onnx ../models/joiner.onnx

# Copy supporting files
cp tokens.txt ../models/tokens.txt
# Keep keywords_raw.txt if supplied; the runtime does not depend on it
```

Speed-oriented configuration:

```bash
cd sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01

# Create the model directory
mkdir -p ../models

# Copy the speed-oriented epoch-99 int8 model set
cp encoder-epoch-99-avg-1-chunk-16-left-64.int8.onnx ../models/encoder.onnx
cp decoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/decoder.onnx
cp joiner-epoch-99-avg-1-chunk-16-left-64.int8.onnx ../models/joiner.onnx

# Copy supporting files
cp tokens.txt ../models/tokens.txt
```

The original guide warns against mixing fp32 and int8 model sets and recommends epoch-99 over epoch-12 for more training and better accuracy. Its speed example uses int8 encoder/joiner files with the supplied fp32 decoder. Preserve that provider-specific set rather than inventing an int8 decoder filename.

Required files are `encoder.onnx`, `decoder.onnx`, `joiner.onnx`, `tokens.txt`, and `keywords.txt`.

### Final directory layout

Put the files in `main/digital-human/wakeword_runtime/models/`:

```
wakeword_runtime/models/
├── encoder.onnx      # Encoder model (renamed)
├── decoder.onnx      # Decoder model (renamed)
├── joiner.onnx       # Joiner model (renamed)
├── tokens.txt        # Pinyin token mapping (228-line version)
├── keywords.txt      # Keyword configuration (generated on first startup)
└── keywords_raw.txt  # Optional; not required by the runtime
```

## Start and stop

From `main/digital-human`:

```bash
pip install -r wakeword_runtime/requirements.txt
python start.py
```

Default endpoints:

- Page: `http://127.0.0.1:8006/index.html`
- Event bridge: `ws://127.0.0.1:8006/wakeword-ws`
- Health: `http://127.0.0.1:8006/health`

Press `Ctrl+C` in the terminal to stop the static page service, event bridge, and wake-word detector together.

## Configuration

Edit [wakeword_runtime/config.json](../main/digital-human/wakeword_runtime/config.json). Main settings:

```json
{
  "wakeword": {
    "enabled": true
  },
  "model_dir": "models",
  "audio": {
    "input_device": null,
    "sample_rate": 16000,
    "channels": 1
  },
  "detector": {
    "num_threads": 4,
    "provider": "cpu",
    "max_active_paths": 2,
    "keywords_score": 1.8,
    "keywords_threshold": 0.1,
    "num_trailing_blanks": 1,
    "cooldown_seconds": 1.5
  },
  "logging": {
    "level": "INFO",
    "dir": "logs",
    "file": "wakeword-runtime.log"
  }
}
```

| Setting | Meaning |
| --- | --- |
| `wakeword.enabled` | Enable local wake-word detection |
| `model_dir` | Model and token directory |
| `audio.input_device` | Microphone input; null uses the system default |
| `audio.sample_rate` | Sample rate; default 16000 |
| `audio.channels` | Channel count; default 1 |
| `detector.num_threads` | Detector thread count |
| `detector.provider` | Inference provider, usually cpu |
| `detector.max_active_paths` | Search path count |
| `detector.keywords_score` | Keyword boost score |
| `detector.keywords_threshold` | Detection threshold |
| `detector.num_trailing_blanks` | Number of trailing blanks |
| `detector.cooldown_seconds` | Cooldown between triggers |
| `logging.level` | Log level |
| `logging.dir` | Log directory |
| `logging.file` | Log filename |

## Recommended workflow

### First run

Prepare the model files and `tokens.txt` under `models/`. Confirm `models/keywords.txt` exists. Run `python start.py` from `digital-human`, open `http://127.0.0.1:8006/index.html`, and check **Wake Words** in Settings.

### Change wake words

Open the page's **Settings > Wake Words** tab, change the enabled state or keyword list, and click **Apply Wake Words**. Follow the prompt to decide whether to restart immediately.

### Disable wake words

Disable **Enable Local Wake Words**, click **Apply Wake Words**, and restart when prompted (recommended). The page and event bridge remain available, but detection stops.
