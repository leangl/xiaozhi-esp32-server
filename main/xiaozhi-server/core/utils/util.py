import re
import os
import json
import copy
import wave
import socket
import ipaddress
import sys
import asyncio
import threading
import subprocess
import numpy as np
import opuslib_next
import psutil
from io import BytesIO
from contextlib import contextmanager
from core.utils import p3
from pydub import AudioSegment
from typing import Callable, Any

TAG = __name__


# Bypass stripped-down ffmpeg/ffprobe PATH shims injected by IDEs (such as Trae CN): during calls,
# prepend the Python interpreter's bin directory so pydub.utils.which() finds
# the conda environment's full binaries first. Restore PATH afterward without changing import-time globals.
# Disable with XIAOZHI_PYDUB_OVERRIDE_FFMPEG=0.
#
# Reference count plus lock: concurrent with blocks save and rewrite PATH only on first entry,
# restoring it only when ref_count reaches zero. This prevents mismatched save/restore operations
# from leaving the bin prefix behind or overlapping threads from violating try/finally guarantees.
_ffmpeg_path_lock = threading.Lock()
_ffmpeg_ref_count = 0
_ffmpeg_original_path: str | None = None


@contextmanager
def _ffmpeg_path_override():
    if os.environ.get("XIAOZHI_PYDUB_OVERRIDE_FFMPEG", "1") != "1":
        yield
        return
    bin_dir = os.path.dirname(sys.executable)
    ffprobe = os.path.join(bin_dir, "ffprobe")
    ffmpeg = os.path.join(bin_dir, "ffmpeg")
    if not (os.path.isfile(ffprobe) or os.path.isfile(ffmpeg)):
        yield
        return

    global _ffmpeg_ref_count, _ffmpeg_original_path
    with _ffmpeg_path_lock:
        if _ffmpeg_ref_count == 0:
            _ffmpeg_original_path = os.environ.get("PATH", "")
            os.environ["PATH"] = bin_dir + os.pathsep + _ffmpeg_original_path
        _ffmpeg_ref_count += 1
    try:
        yield
    finally:
        with _ffmpeg_path_lock:
            _ffmpeg_ref_count -= 1
            if _ffmpeg_ref_count == 0 and _ffmpeg_original_path is not None:
                os.environ["PATH"] = _ffmpeg_original_path
                _ffmpeg_original_path = None


# Delegate to util.ffmpeg_path_override for one-line use after importing util.
ffmpeg_path_override = _ffmpeg_path_override


def get_local_ip():
    """Return the first active local IPv4 address without sockets or DNS probes.

    Interface order comes from the OS, not remote reachability. On multihomed
    hosts this is an advertised-address hint, not a route to a specific peer.
    """
    try:
        stats = psutil.net_if_stats()
        for name, addresses in psutil.net_if_addrs().items():
            if name not in stats or not stats[name].isup:
                continue
            for entry in addresses:
                if entry.family != socket.AF_INET:
                    continue
                try:
                    address = ipaddress.IPv4Address(entry.address)
                except ipaddress.AddressValueError:
                    continue
                if not (address.is_loopback or address.is_unspecified or address.is_multicast):
                    return str(address)
    except Exception:
        # Address discovery must not block startup or fall back to a network probe.
        pass
    return "127.0.0.1"


def is_private_ip(ip_addr):
    """
    Check if an IP address is a private IP address (compatible with IPv4 and IPv6).

    @param {string} ip_addr - The IP address to check.
    @return {bool} True if the IP address is private, False otherwise.
    """
    try:
        # Validate IPv4 or IPv6 address format
        if not re.match(
            r"^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", ip_addr
        ):
            return False  # Invalid IP address format

        # IPv4 private address ranges
        if "." in ip_addr:  # IPv4 address
            ip_parts = list(map(int, ip_addr.split(".")))
            if ip_parts[0] == 10:
                return True  # 10.0.0.0/8 range
            elif ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                return True  # 172.16.0.0/12 range
            elif ip_parts[0] == 192 and ip_parts[1] == 168:
                return True  # 192.168.0.0/16 range
            elif ip_addr == "127.0.0.1":
                return True  # Loopback address
            elif ip_parts[0] == 169 and ip_parts[1] == 254:
                return True  # Link-local address 169.254.0.0/16
            else:
                return False  # Not a private IPv4 address
        else:  # IPv6 address
            ip_addr = ip_addr.lower()
            if ip_addr.startswith("fc00:") or ip_addr.startswith("fd00:"):
                return True  # Unique Local Addresses (FC00::/7)
            elif ip_addr == "::1":
                return True  # Loopback address
            elif ip_addr.startswith("fe80:"):
                return True  # Link-local unicast addresses (FE80::/10)
            else:
                return False  # Not a private IPv6 address

    except (ValueError, IndexError):
        return False  # IP address format error or insufficient segments


def get_ip_info(ip_addr, logger):
    """Compatibility shim: IP-derived location is unavailable, without a lookup.

    Do not forward a child's device IP or reuse results from the retired service.
    A future parent-configured location must be explicit, not inferred from IP.
    """
    return {}


def write_json_file(file_path, data):
    """Write data to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def remove_punctuation_and_length(text):
    # Unicode ranges for full-width and half-width symbols.
    full_width_punctuations = (
        "！＂＃＄％＆＇（）＊＋，－。／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
    )
    half_width_punctuations = r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
    space = " "  # Half-width space.
    full_width_space = "　"  # Full-width space.

    # Remove full-width/half-width symbols and spaces.
    result = "".join(
        [
            char
            for char in text
            if char not in full_width_punctuations
            and char not in half_width_punctuations
            and char not in space
            and char not in full_width_space
        ]
    )

    if result == "Yeah":
        return 0, ""
    return len(result), result


def check_model_key(modelType, modelKey):
    if "你" in modelKey:
        return f"Configuration error: {modelType} API key is not set; current value: {modelKey}"
    return None


def parse_string_to_list(value, separator=";"):
    """
    Convert an input value to a list.
    Args:
        value: Input value: None, a string or a list.
        separator: Delimiter; defaults to a semicolon.
    Returns:
        list: Processed values.
    """
    if value is None or value == "":
        return []
    elif isinstance(value, str):
        return [item.strip() for item in value.split(separator) if item.strip()]
    elif isinstance(value, list):
        return value
    return []


def check_ffmpeg_installed() -> bool:
    """
    Check whether ffmpeg is installed and executable in the current environment.

    Returns:
        bool: True if ffmpeg works; otherwise raise ValueError.

    Raises:
        ValueError: Detailed guidance when ffmpeg is missing or its dependencies are unavailable.
    """
    try:
        # Try executing ffmpeg.
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,  # A nonzero exit code raises CalledProcessError.
        )

        output = (result.stdout + result.stderr).lower()
        if "ffmpeg version" in output:
            return True

        # Treat missing version output as an error too.
        raise ValueError("No valid ffmpeg version output detected.")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # Extract error output.
        stderr_output = ""
        if isinstance(e, subprocess.CalledProcessError):
            stderr_output = (e.stderr or "").strip()
        else:
            stderr_output = str(e).strip()

        # Build the basic error guidance.
        error_msg = [
            "❌ ffmpeg is not working correctly.\n",
            "Recommended steps:",
            "1. Ensure the correct conda environment is activated;",
            "2. See the project setup guide for installing ffmpeg in conda.\n",
        ]

        # 🎯 Add guidance for specific errors.
        if "libiconv.so.2" in stderr_output:
            error_msg.append("⚠️ Missing dependency: libiconv.so.2")
            error_msg.append("Fix: run this in the current conda environment:")
            error_msg.append("   conda install -c conda-forge libiconv\n")
        elif (
            "no such file or directory" in stderr_output
            and "ffmpeg" in stderr_output.lower()
        ):
            error_msg.append("⚠️ The ffmpeg executable was not found.")
            error_msg.append("Fix: run this in the current conda environment:")
            error_msg.append("   conda install -c conda-forge ffmpeg\n")
        else:
            error_msg.append("Error details:")
            error_msg.append(stderr_output or "Unknown error.")

        # Raise the detailed exception.
        raise ValueError("\n".join(error_msg)) from e


def extract_json_from_string(input_string):
    """Extract the JSON portion of a string."""
    pattern = r"(\{.*\})"
    match = re.search(pattern, input_string, re.DOTALL)  # Enable re.DOTALL.
    if match:
        return match.group(1)  # Return the extracted JSON string.
    return None


def audio_to_data_stream(
    audio_file_path, is_opus=True, callback: Callable[[Any], Any] = None, sample_rate=16000, opus_encoder=None
) -> None:
    with _ffmpeg_path_override():
        _audio_to_data_stream_inner(
            audio_file_path, is_opus, callback, sample_rate, opus_encoder
        )


def _audio_to_data_stream_inner(
    audio_file_path, is_opus, callback, sample_rate, opus_encoder
):
    file_type = os.path.splitext(audio_file_path)[1]
    if file_type:
        file_type = file_type.lstrip(".")
    # -nostdin prevents ffmpeg from blocking while waiting for standard input.
    audio = AudioSegment.from_file(
        audio_file_path, format=file_type, parameters=["-nostdin"]
    )
    audio = audio.set_channels(1).set_frame_rate(sample_rate).set_sample_width(2)
    pcm_to_data_stream(audio.raw_data, is_opus, callback, sample_rate, opus_encoder)


async def audio_to_data(
    audio_file_path: str, is_opus: bool = True, use_cache: bool = True
) -> list[bytes]:
    """
    Convert an audio file to a list of Opus/PCM frames.
    Args:
        audio_file_path: Audio file path.
        is_opus: Whether to encode as Opus.
        use_cache: Whether to use the cache.
    """
    from core.utils.cache.manager import cache_manager
    from core.utils.cache.config import CacheType

    # Build a cache key containing the file path and encoding type.
    cache_key = f"{audio_file_path}:{is_opus}"

    # Try retrieving results from the cache.
    if use_cache:
        cached_result = cache_manager.get(CacheType.AUDIO_DATA, cache_key)
        if cached_result is not None:
            return cached_result

    def _sync_audio_to_data():
        # Get the filename extension.
        file_type = os.path.splitext(audio_file_path)[1]
        if file_type:
            file_type = file_type.lstrip(".")
        # Read the audio file with -nostdin: reading standard input would block FFmpeg.
        with _ffmpeg_path_override():
            audio = AudioSegment.from_file(
                audio_file_path, format=file_type, parameters=["-nostdin"]
            )

        # Convert to mono, 16 kHz, 16-bit little-endian audio to match the encoder.
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

        # Get raw PCM data (16-bit little-endian).
        raw_data = audio.raw_data

        # Initialize the Opus encoder.
        encoder = opuslib_next.Encoder(16000, 1, opuslib_next.APPLICATION_AUDIO)

        # Encoding parameters.
        frame_duration = 60  # 60ms per frame
        frame_size = int(16000 * frame_duration / 1000)  # 960 samples/frame

        datas = []
        # Process all audio by frame, zero-padding the final frame if necessary.
        for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
            # Get the current frame's binary data.
            chunk = raw_data[i : i + frame_size * 2]

            # Zero-pad an incomplete final frame.
            if len(chunk) < frame_size * 2:
                chunk += b"\x00" * (frame_size * 2 - len(chunk))

            if is_opus:
                # Convert to a NumPy array for processing.
                np_frame = np.frombuffer(chunk, dtype=np.int16)
                # Encode Opus data.
                frame_data = encoder.encode(np_frame.tobytes(), frame_size)
            else:
                frame_data = chunk if isinstance(chunk, bytes) else bytes(chunk)

            datas.append(frame_data)

        return datas

    loop = asyncio.get_running_loop()
    # Run synchronous audio processing in a separate thread.
    result = await loop.run_in_executor(None, _sync_audio_to_data)

    # Cache the result using the configured TTL (ten minutes).
    if use_cache:
        cache_manager.set(CacheType.AUDIO_DATA, cache_key, result)

    return result


def audio_bytes_to_data_stream(
    audio_bytes, file_type, is_opus, callback: Callable[[Any], Any], sample_rate=16000, opus_encoder=None
) -> None:
    """
    Convert audio bytes directly to Opus/PCM; supports wav, mp3 and p3.
    """
    if file_type == "p3":
        # Decode p3 directly.
        return p3.decode_opus_from_bytes_stream(audio_bytes, callback)
    else:
        # Use pydub for other formats.
        with _ffmpeg_path_override():
            audio = AudioSegment.from_file(
                BytesIO(audio_bytes), format=file_type, parameters=["-nostdin"]
            )
        audio = audio.set_channels(1).set_frame_rate(sample_rate).set_sample_width(2)
        raw_data = audio.raw_data
        pcm_to_data_stream(raw_data, is_opus, callback, sample_rate, opus_encoder)


def pcm_to_data_stream(raw_data, is_opus=True, callback: Callable[[Any], Any] = None, sample_rate=16000, opus_encoder=None):
    """
    Stream-encode PCM as Opus or output PCM directly.

    Args:
        raw_data: Raw PCM data.
        is_opus: Whether to encode as Opus.
        callback: Callback.
        sample_rate: Sample rate.
        opus_encoder: OpusEncoderUtils instance (recommended to preserve encoder state across chunks).
    """
    using_temp_encoder = False
    if is_opus and opus_encoder is None:
        encoder = opuslib_next.Encoder(sample_rate, 1, opuslib_next.APPLICATION_AUDIO)
        using_temp_encoder = True

    # Encoding parameters.
    frame_duration = 60  # 60ms per frame
    frame_size = int(sample_rate * frame_duration / 1000)  # samples/frame

    # Process all audio by frame, zero-padding the final frame if necessary.
    for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
        # Get the current frame's binary data.
        chunk = raw_data[i : i + frame_size * 2]

        # Zero-pad an incomplete final frame.
        if len(chunk) < frame_size * 2:
            chunk += b"\x00" * (frame_size * 2 - len(chunk))

        if is_opus:
            if using_temp_encoder:
                # Use a temporary encoder for standalone audio only.
                np_frame = np.frombuffer(chunk, dtype=np.int16)
                frame_data = encoder.encode(np_frame.tobytes(), frame_size)
                callback(frame_data)
            else:
                # Use the supplied encoder for streaming TTS to preserve state.
                is_last = (i + frame_size * 2 >= len(raw_data))
                opus_encoder.encode_pcm_to_opus_stream(chunk, end_of_stream=is_last, callback=callback)
        else:
            # PCM mode: output directly.
            frame_data = chunk if isinstance(chunk, bytes) else bytes(chunk)
            callback(frame_data)


def opus_datas_to_wav_bytes(opus_datas, sample_rate=16000, channels=1):
    """
    Decode a list of Opus frames to WAV bytes.
    """
    decoder = opuslib_next.Decoder(sample_rate, channels)
    try:
        pcm_datas = []

        frame_duration = 60  # ms
        frame_size = int(sample_rate * frame_duration / 1000)  # 960

        for opus_frame in opus_datas:
            # Decode to PCM (bytes, two bytes per sample).
            pcm = decoder.decode(opus_frame, frame_size)
            pcm_datas.append(pcm)

        pcm_bytes = b"".join(pcm_datas)

        # Write WAV bytes.
        wav_buffer = BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return wav_buffer.getvalue()
    finally:
        if decoder is not None:
            try:
                del decoder
            except Exception:
                pass


def check_vad_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("VAD") is None
    ):
        return False
    current_vad_module = before_config["selected_module"]["VAD"]
    new_vad_module = new_config["selected_module"]["VAD"]
    return (current_vad_module != new_vad_module
            or before_config["VAD"][current_vad_module] != new_config["VAD"][new_vad_module])


def check_asr_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("ASR") is None
    ):
        return False
    update_asr = False
    current_asr_module = before_config["selected_module"]["ASR"]
    new_asr_module = new_config["selected_module"]["ASR"]

    # Update if the module names differ.
    if current_asr_module != new_asr_module:
        return True

    # If module names match, compare their types.
    current_asr_type = (
        current_asr_module
        if "type" not in before_config["ASR"][current_asr_module]
        else before_config["ASR"][current_asr_module]["type"]
    )
    new_asr_type = (
        new_asr_module
        if "type" not in new_config["ASR"][new_asr_module]
        else new_config["ASR"][new_asr_module]["type"]
    )
    update_asr = current_asr_type != new_asr_type
    return update_asr


def filter_sensitive_info(config: dict) -> dict:
    """
    Filter sensitive information from configuration.
    Args:
        config: Original configuration dictionary.
    Returns:
        Filtered configuration dictionary.
    """
    sensitive_keys = [
        "api_key",
        "personal_access_token",
        "access_token",
        "token",
        "secret",
        "access_key_secret",
        "secret_key",
    ]

    def _filter_dict(d: dict) -> dict:
        filtered = {}
        for k, v in d.items():
            if any(sensitive in k.lower() for sensitive in sensitive_keys):
                filtered[k] = "***"
            elif isinstance(v, dict):
                filtered[k] = _filter_dict(v)
            elif isinstance(v, list):
                filtered[k] = [_filter_dict(i) if isinstance(i, dict) else i for i in v]
            elif isinstance(v, str):
                try:
                    json_data = json.loads(v)
                    if isinstance(json_data, dict):
                        filtered[k] = json.dumps(
                            _filter_dict(json_data), ensure_ascii=False
                        )
                    else:
                        filtered[k] = v
                except (json.JSONDecodeError, TypeError):
                    filtered[k] = v
            else:
                filtered[k] = v
        return filtered

    return _filter_dict(copy.deepcopy(config))


def get_vision_url(config: dict) -> str:
    """Get the vision URL.

    Args:
        config: Configuration dictionary.

    Returns:
        str: vision URL
    """
    server_config = config["server"]
    vision_explain = server_config.get("vision_explain", "")
    if "你的" in vision_explain:
        local_ip = get_local_ip()
        port = int(server_config.get("http_port", 8003))
        vision_explain = f"http://{local_ip}:{port}/mcp/vision/explain"
    return vision_explain


def is_valid_image_file(file_data: bytes) -> bool:
    """
    Check whether file data is a valid image format.

    Args:
        file_data: Binary file data.

    Returns:
        bool: True for a valid image format, otherwise False.
    """
    # Magic bytes (headers) for common image formats.
    image_signatures = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"BM": "BMP",
        b"II*\x00": "TIFF",
        b"MM\x00*": "TIFF",
        b"RIFF": "WEBP",
    }

    # Check the header against known image formats.
    for signature in image_signatures:
        if file_data.startswith(signature):
            return True

    return False


def sanitize_tool_name(name: str) -> str:
    """Sanitize tool names for OpenAI compatibility."""
    # Support Chinese characters, English letters, digits, underscores and hyphens.
    return re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", name)


def validate_mcp_endpoint(mcp_endpoint: str) -> bool:
    """
    Validate the MCP endpoint format.

    Args:
        mcp_endpoint: MCP endpoint string.

    Returns:
        bool: Whether the endpoint is valid.
    """
    # 1. Check for the ws prefix.
    if not mcp_endpoint.startswith("ws"):
        return False

    # 2. Check for key or call.
    if "key" in mcp_endpoint.lower() or "call" in mcp_endpoint.lower():
        return False

    # 3. Check for /mcp/.
    if "/mcp/" not in mcp_endpoint:
        return False

    return True

def get_system_error_response(config: dict) -> str:
    """Get the spoken response for system errors.

    Args:
        config: Configuration dictionary.

    Returns:
        str: Spoken system-error response in the existing user-facing language.
    """
    return config.get("system_error_response", "主人，小智现在有点忙，我们稍后再试吧。")
