"""Device-owned turn boundaries. No inference runtime or model is imported."""
import time
from dataclasses import dataclass

from config.provider_profile import device_vad_max_audio_duration_ms, validate_provider_config
from core.providers.vad.base import VADProviderBase


class DeviceVadLimitError(ValueError):
    """A device failed to terminate its bounded PCM turn."""


@dataclass(frozen=True)
class DeviceAudioFrame:
    turn_id: int
    pcm: bytes


class VADProvider(VADProviderBase):
    device_controlled = True

    def __init__(self, config):
        validate_provider_config("VAD", config, "device", require_ready=True)
        self.max_audio_duration_ms = device_vad_max_audio_duration_ms(config)
        # Entry-point decoding normalizes audio to 16 kHz, mono, signed 16-bit PCM.
        self.max_pcm_bytes = self.max_audio_duration_ms * 32

    def is_listening(self, conn):
        return bool(getattr(conn, "_device_vad_active", False))

    def start_listening(self, conn):
        if self.is_listening(conn):
            return False
        conn._device_vad_active = True
        conn._device_vad_started_at = time.monotonic()
        conn._device_vad_pcm_bytes = 0
        conn._device_vad_received_bytes = 0
        conn._device_vad_turn_id = getattr(conn, "_device_vad_turn_id", 0) + 1
        return True

    def stop_listening(self, conn):
        was_active = self.is_listening(conn)
        conn._device_vad_active = False
        return was_active

    def _check_limits(self, conn, size):
        elapsed_ms = (time.monotonic() - conn._device_vad_started_at) * 1000
        if size > self.max_pcm_bytes or elapsed_ms >= self.max_audio_duration_ms:
            self.stop_listening(conn)
            raise DeviceVadLimitError("Device VAD turn exceeded max_audio_duration_ms; audio discarded")

    def queue_audio(self, conn, data):
        if not self.is_listening(conn):
            return None
        size = conn._device_vad_received_bytes + len(data)
        self._check_limits(conn, size)
        conn._device_vad_received_bytes = size
        return DeviceAudioFrame(conn._device_vad_turn_id, data)

    def is_vad(self, conn, data):
        if conn.client_listen_mode != "manual" or not self.is_listening(conn):
            return False
        size = conn._device_vad_pcm_bytes + len(data)
        self._check_limits(conn, size)
        conn._device_vad_pcm_bytes = size
        # Includes silence: only an explicit device stop can submit the question.
        return True

    def release_conn_resources(self, conn):
        for name in ("_device_vad_active", "_device_vad_started_at", "_device_vad_pcm_bytes",
                     "_device_vad_received_bytes", "_device_vad_turn_id"):
            if hasattr(conn, name):
                delattr(conn, name)
