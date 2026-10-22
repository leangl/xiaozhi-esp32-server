import time
import os
from config.logger import setup_logging
from typing import Optional, Tuple, List
from core.providers.asr.dto.dto import InterfaceType
from core.providers.asr.base import ASRProviderBase

from config.service_policy import post, validate_endpoint
from config.provider_profile import validate_provider_config

TAG = __name__
logger = setup_logging()

class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        validate_provider_config("ASR", config, "openai", require_ready=True)
        self.interface_type = InterfaceType.NON_STREAM
        self.api_key = config.get("api_key") or "local-only"
        self.api_url = config.get("base_url")
        validate_endpoint(self.api_url, "asr")
        self.model = config.get("model_name")        
        self.output_dir = config.get("output_dir") or "tmp/"
        self.delete_audio_file = delete_audio_file

        os.makedirs(self.output_dir, exist_ok=True)

    def requires_file(self) -> bool:
        return True

    async def speech_to_text(self, opus_data: List[bytes], session_id: str, artifacts=None) -> Tuple[Optional[str], Optional[str]]:
        file_path = None
        try:
            if artifacts is None:
                return "", None
            file_path = artifacts.file_path
                
            logger.bind(tag=TAG).info(f"file path: {file_path}")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            
            # Pass the model name using data
            data = {
                "model": self.model
            }


            with open(file_path, "rb") as audio_file:  # Use a with statement to ensure the file closes
                files = {
                    "file": audio_file
                }

                start_time = time.time()
                response = post(
                    self.api_url,
                    "asr",
                    files=files,
                    data=data,
                    headers=headers
                )
                logger.bind(tag=TAG).debug(
                    f"Speech recognition duration: {time.time() - start_time:.3f}s | status: {response.status_code}"
                )

            if response.status_code == 200:
                text = response.json().get("text", "")
                return text, file_path
            else:
                raise Exception(f"ASR API request failed with status {response.status_code}")
                
        except Exception:
            logger.bind(tag=TAG).error("Speech recognition failed; verify approved ASR configuration and availability")
            return "", None
        
