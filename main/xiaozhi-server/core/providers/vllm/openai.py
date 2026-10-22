import openai
import json
from config.service_policy import httpx_client, validate_endpoint
from config.provider_profile import validate_provider_config
from config.logger import setup_logging
from core.providers.vllm.base import VLLMProviderBase

TAG = __name__
logger = setup_logging()


class VLLMProvider(VLLMProviderBase):
    def __init__(self, config):
        validate_provider_config("VLLM", config, "openai", require_ready=True)
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key") or "local-only"
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        validate_endpoint(self.base_url, "vllm")

        param_defaults = {
            "max_tokens": (500, int),
            "temperature": (0.7, lambda x: round(float(x), 1)),
            "top_p": (1.0, lambda x: round(float(x), 1)),
        }

        for param, (default, converter) in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else default,
                )
            except (ValueError, TypeError):
                setattr(self, param, default)

        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url,
                                    http_client=httpx_client("vllm"))

    def response(self, question, base64_image):
        question = question + "(Please reply in Chinese)"
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages, stream=False
            )

            return response.choices[0].message.content

        except Exception:
            logger.bind(tag=TAG).error("Vision response failed; verify approved VLLM configuration and availability")
            raise RuntimeError("Approved vision service request failed") from None
