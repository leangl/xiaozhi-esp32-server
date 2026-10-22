from config.logger import setup_logging
from openai import OpenAI
from config.service_policy import httpx_client, validate_endpoint
from config.provider_profile import validate_provider_config
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        validate_provider_config("LLM", config, "ollama", require_ready=True)
        self.model_name = config.get("model_name")
        self.base_url = config["base_url"].rstrip("/")
        # Initialize OpenAI client with Ollama base URL
        # Add v1 when it is absent
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"
        validate_endpoint(self.base_url, "llm")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't need an API key but OpenAI client requires one
            http_client=httpx_client("llm"),
        )

    def response(self, session_id, dialogue, **kwargs):
        responses = self.client.chat.completions.create(
            model=self.model_name, messages=dialogue, stream=True
        )
        is_active = True
        # Handle tags split across chunks
        buffer = ""

        try:
            for chunk in responses:
                try:
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else ""

                    if content:
                        # Append content to the buffer
                        buffer += content

                        # Process tags in the buffer
                        while "<think>" in buffer and "</think>" in buffer:
                            # Find and remove complete <think></think> tags
                            pre = buffer.split("<think>", 1)[0]
                            post = buffer.split("</think>", 1)[1]
                            buffer = pre + post

                        # Handle an opening tag without a closing tag
                        if "<think>" in buffer:
                            is_active = False
                            buffer = buffer.split("<think>", 1)[0]

                        # Handle a closing tag without an opening tag
                        if "</think>" in buffer:
                            is_active = True
                            buffer = buffer.split("</think>", 1)[1]

                        # Emit buffered content when the current state is active
                        if is_active and buffer:
                            yield buffer
                            buffer = ""  # Clear the buffer

                except Exception as e:
                    logger.bind(tag=TAG).error(f"Error processing chunk: {e}")
        finally:
            responses.close()

    def response_with_functions(self, session_id, dialogue, functions=None):
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=dialogue,
            stream=True,
            tools=functions,
        )

        is_active = True
        buffer = ""

        try:
            for chunk in stream:
                try:
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else None
                    tool_calls = (
                        delta.tool_calls if hasattr(delta, "tool_calls") else None
                    )

                    # Pass tool calls through directly
                    if tool_calls:
                        yield None, tool_calls
                        continue

                    # Process text content
                    if content:
                        # Append content to the buffer
                        buffer += content

                        # Process tags in the buffer
                        while "<think>" in buffer and "</think>" in buffer:
                            # Find and remove complete <think></think> tags
                            pre = buffer.split("<think>", 1)[0]
                            post = buffer.split("</think>", 1)[1]
                            buffer = pre + post

                        # Handle an opening tag without a closing tag
                        if "<think>" in buffer:
                            is_active = False
                            buffer = buffer.split("<think>", 1)[0]

                        # Handle a closing tag without an opening tag
                        if "</think>" in buffer:
                            is_active = True
                            buffer = buffer.split("</think>", 1)[1]

                        # Emit buffered content when the current state is active
                        if is_active and buffer:
                            yield buffer, None
                            buffer = ""  # Clear the buffer
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Error processing function chunk: {e}")
                    continue
        finally:
            stream.close()
