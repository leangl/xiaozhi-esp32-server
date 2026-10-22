import httpx
from config.service_policy import httpx_client, validate_endpoint
from typing import Dict, Any, List
from config.logger import setup_logging

TAG = __name__

class ContextDataProvider:
    """Populate data context by fetching from configured APIs."""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger or setup_logging()
        self.context_data = ""

    def fetch_all(self, device_id: str) -> str:
        """Get all configured context data."""
        context_providers = self.config.get("context_providers", [])
        if not context_providers:
            return ""

        formatted_lines = []
        for provider in context_providers:
            url = provider.get("url")
            headers = provider.get("headers", {})

            if not url:
                continue

            try:
                headers = headers.copy() if isinstance(headers, dict) else {}
                # Add device_id to request headers.
                headers["device-id"] = device_id
                
                # Send the request.
                validate_endpoint(url, "context")
                with httpx_client("context", timeout=3) as client:
                    response = client.get(url, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict):
                        if result.get("code") == 0:
                            data = result.get("data")
                            # Format the data.
                            if isinstance(data, dict):
                                for k, v in data.items():
                                    formatted_lines.append(f"- **{k}：** {v}")
                            elif isinstance(data, list):
                                for item in data:
                                    formatted_lines.append(f"- {item}")
                            else:
                                formatted_lines.append(f"- {data}")
                        else:
                            self.logger.bind(tag=TAG).warning("Context service returned an error")
                    else:
                        self.logger.bind(tag=TAG).warning("Context service returned an invalid response")
                else:
                    self.logger.bind(tag=TAG).warning("Context request failed (status {})", response.status_code)
            except Exception:
                self.logger.bind(tag=TAG).warning("Context service unavailable; configure a reviewed endpoint")
        
        # Join all formatted lines into one string.
        self.context_data = "\n".join(formatted_lines)
        return self.context_data
