# IndexStreamTTS guide

## Prepare the environment

### 1. Clone the project

```bash
git clone https://github.com/Ksuriuri/index-tts-vllm.git
```

Enter the directory:

```bash
cd index-tts-vllm
```

Check out the historical version that uses vLLM 0.10.2:

```bash
git checkout 224e8d5e5c8f66801845c66b30fa765328fd0be3
```

### 2. Create and activate Conda

```bash
conda create -n index-tts-vllm python=3.12
conda activate index-tts-vllm
```

### 3. Install PyTorch 2.8.0

The original guide calls this the latest version at the time; this setup specifically needs PyTorch 2.8.0 for vLLM 0.10.2.

Check the GPU driver's supported CUDA version and installed compiler:

```bash
nvidia-smi
nvcc --version
```

Example driver maximum:

```bash
CUDA Version: 12.8
```

Example installed CUDA compiler:

```bash
Cuda compilation tools, release 12.8, V12.8.89
```

The original installation command for this CUDA 12.8 example is:

```bash
pip install torch torchvision
```

Use the [PyTorch installation instructions](https://pytorch.org/get-started/locally/) to obtain the required 2.8.0 version for your environment.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Download model weights

Download official weights to any local directory, then convert them. IndexTTS-1.5 weights are supported.

| Hugging Face | ModelScope |
| --- | --- |
| [IndexTTS](https://huggingface.co/IndexTeam/Index-TTS) | [IndexTTS](https://modelscope.cn/models/IndexTeam/Index-TTS) |
| [IndexTTS-1.5](https://huggingface.co/IndexTeam/IndexTTS-1.5) | [IndexTTS-1.5](https://modelscope.cn/models/IndexTeam/IndexTTS-1.5) |

For ModelScope, install and initialize Git LFS if needed:

```bash
sudo apt-get install git-lfs
git lfs install
```

Create a model directory and clone the weights:

```bash
mkdir model_dir
cd model_dir
git clone https://www.modelscope.cn/IndexTeam/IndexTTS-1.5.git
```

Convert the weights:

```bash
bash convert_hf_format.sh /path/to/your/model_dir
```

For weights under `model_dir/IndexTTS-1.5`:

```bash
bash convert_hf_format.sh model_dir/IndexTTS-1.5
```

The script creates Transformers-compatible weights under the model directory's `vllm` subdirectory so vLLM can load them.

### 6. Adapt the API response

This integration expects raw audio bytes. Edit `api_server.py`:

```bash
vi api_server.py
```

Use the original endpoint adaptation below:

```python
@app.post("/tts", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api(request: Request):
    try:
        data = await request.json()
        text = data["text"]
        character = data["character"]

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, text)

        return Response(content=wav.tobytes(), media_type="application/octet-stream")
        
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        print(tb_str)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )
```

### 7. Create a startup script

Run it in the corresponding Conda environment:

```bash
vi start_api.sh
```

Paste the following and save with `:wq`. Replace `/home/system/index-tts-vllm/model_dir/IndexTTS-1.5` with your actual model path. The script terminates processes using port 11996 and matching VLLM/EngineCore process names; review those broad process matches before running it.

```bash
# Activate the Conda environment
conda activate index-tts-vllm 
echo "Activated the project Conda environment"
sleep 2
# Find the process using port 11996
PID_VLLM=$(sudo netstat -tulnp | grep 11996 | awk '{print $7}' | cut -d'/' -f1)

# Check whether a process was found
if [ -z "$PID_VLLM" ]; then
  echo "No process found using port 11996"
else
  echo "Process found using port 11996, PID: $PID_VLLM"
  # Try a normal kill first, then wait 2 seconds
  kill $PID_VLLM
  sleep 2
  # Check whether the process is still running
  if ps -p $PID_VLLM > /dev/null; then
    echo "Process still running; forcing termination..."
    kill -9 $PID_VLLM
  fi
  echo "Terminated process $PID_VLLM"
fi

# Find VLLM::EngineCore processes
GPU_PIDS=$(ps aux | grep -E "VLLM|EngineCore" | grep -v grep | awk '{print $2}')

# Check whether a process was found
if [ -z "$GPU_PIDS" ]; then
  echo "No VLLM-related process found"
else
  echo "VLLM-related processes found, PIDs: $GPU_PIDS"
  # Try a normal kill first, then wait 2 seconds
  kill $GPU_PIDS
  sleep 2
  # Check whether the process is still running
  if ps -p $GPU_PIDS > /dev/null; then
    echo "Process still running; forcing termination..."
    kill -9 $GPU_PIDS
  fi
  echo "Terminated process $GPU_PIDS"
fi

# Create tmp if it does not exist
mkdir -p tmp

# Run api_server.py in the background; redirect logs to tmp/server.log
nohup python api_server.py --model_dir /home/system/index-tts-vllm/model_dir/IndexTTS-1.5 --port 11996 > tmp/server.log 2>&1 &
echo "api_server.py is running in the background; see tmp/server.log"
```

Make it executable and run it:

```bash
chmod +x start_api.sh
./start_api.sh
```

Read its logs:

```bash
tail -f tmp/server.log
```

The original guide mentions a `----gpu_memory_utilization` startup option, with default `0.25`, to adjust GPU memory use. That spelling contains four hyphens; verify the supported argument against the checked-out server before using it. This translation does not silently change the option.

## Voice configuration

Register single or blended custom voices in `assets/speaker.json` in the project root:

```json
{
    "说话人名称1": [
        "音频文件路径1.wav",
        "音频文件路径2.wav"
    ],
    "说话人名称2": [
        "音频文件路径3.wav"
    ]
}
```

The original Chinese placeholders mean “speaker name 1/2” and “audio file path 1/2/3.wav”. Replace them with your speaker names and file paths while preserving the JSON shape.

Restart the service after adding speakers so it registers the voices. Add the matching speaker in the management console; for a server-only installation, change the corresponding `voice`.
