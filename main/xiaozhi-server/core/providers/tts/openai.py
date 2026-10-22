from config.service_policy import post, validate_endpoint
from config.provider_profile import validate_provider_config
from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    TTS_PARAM_CONFIG = [
        ("ttsRate", "speed", 0.25, 4, 1, lambda v: round(float(v), 2)),
    ]

    def __init__(self, config, delete_audio_file):
        validate_provider_config("TTS", config, "openai", require_ready=True)
        validate_endpoint(config.get("api_url"), "tts")
        super().__init__(config, delete_audio_file)
        self.api_key = config.get("api_key") or "local-only"
        self.api_url = config["api_url"]
        self.model = config["model"]
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice", "alloy")
        self.audio_file_type = config.get("format", "wav")

        # Handle empty strings
        speed = config.get("speed", "1.0")
        self.speed = float(speed) if speed else 1.0

        # Apply percentage adjustments when present; otherwise use the shared configuration
        self._apply_percentage_params(config)

        self.output_file = config.get("output_dir", "tmp/")

    async def text_to_speak(self, text, output_file):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": self.audio_file_type,
            "speed": self.speed,
        }
        response = post(
            self.api_url, "tts", json=data, headers=headers, timeout=self.tts_timeout
        )
        if response.status_code == 200:
            if output_file:
                with open(output_file, "wb") as audio_file:
                    audio_file.write(response.content)
            else:
                return response.content
        else:
            raise Exception(
                f"TTS API request failed with status {response.status_code}"
            )
