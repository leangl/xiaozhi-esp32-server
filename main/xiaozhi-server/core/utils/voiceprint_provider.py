import asyncio
import time
import httpx
from config.service_policy import validate_endpoint, httpx_client, async_httpx_client
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict
from config.logger import setup_logging
from core.utils.cache.manager import cache_manager
from core.utils.cache.config import CacheType

TAG = __name__
logger = setup_logging()


class VoiceprintProvider:
    """Voiceprint recognition service provider."""
    
    def __init__(self, config: dict):
        self.original_url = config.get("url", "")
        self.speakers = config.get("speakers", [])
        self.speaker_map = self._parse_speakers()
        # Voiceprint similarity threshold; default: 0.4.
        self.similarity_threshold = float(config.get("similarity_threshold", 0.4))
        
        # Parse the API URL and key.
        self.api_url = None
        self.api_key = None
        self.speaker_ids = []
        
        if not self.original_url:
            logger.bind(tag=TAG).warning("Voiceprint URL not configured; recognition will be disabled")
            self.enabled = False
        else:
            validate_endpoint(self.original_url, "voiceprint")
            # Parse the URL and key.
            parsed_url = urlparse(self.original_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Extract key from query parameters.
            query_params = parse_qs(parsed_url.query)
            self.api_key = query_params.get('key', [''])[0]
            
            if not self.api_key:
                logger.bind(tag=TAG).error("No key parameter in URL; voiceprint recognition will be disabled")
                self.enabled = False
            else:
                # Build the identify endpoint URL.
                self.api_url = f"{base_url}/voiceprint/identify"
                validate_endpoint(self.api_url, "voiceprint")
                
                # Extract speaker_ids.
                for speaker_str in self.speakers:
                    try:
                        parts = speaker_str.split(",", 2)
                        if len(parts) >= 1:
                            speaker_id = parts[0].strip()
                            self.speaker_ids.append(speaker_id)
                    except Exception:
                        continue
                
                # Check for valid speaker configuration.
                if not self.speaker_ids:
                    logger.bind(tag=TAG).warning("No valid speakers configured; voiceprint recognition will be disabled")
                    self.enabled = False
                else:
                    # Run a health check to verify server availability.
                    if self._check_server_health():
                        self.enabled = True
                        logger.bind(tag=TAG).info(f"Voiceprint recognition enabled: API={self.api_url}, speakers={len(self.speaker_ids)}, similarity threshold={self.similarity_threshold}")
                    else:
                        self.enabled = False
                        logger.bind(tag=TAG).warning(f"Voiceprint server unavailable; recognition disabled: {self.api_url}")
    
    def _parse_speakers(self) -> Dict[str, Dict[str, str]]:
        """Parse speaker configuration."""
        speaker_map = {}
        for speaker_str in self.speakers:
            try:
                parts = speaker_str.split(",", 2)
                if len(parts) >= 3:
                    speaker_id, name, description = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    speaker_map[speaker_id] = {
                        "name": name,
                        "description": description
                    }
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Failed to parse speaker configuration: {speaker_str}, error: {e}")
        return speaker_map
    
    def _check_server_health(self) -> bool:
        """Check voiceprint server health."""
        if not self.api_url or not self.api_key:
            return False
    
        cache_key = f"{self.api_url}:{self.api_key}"
        
        # Check the cache.
        cached_result = cache_manager.get(CacheType.VOICEPRINT_HEALTH, cache_key)
        if cached_result is not None:
            logger.bind(tag=TAG).debug(f"Using cached health status: {cached_result}")
            return cached_result
        
        # Cache expired or absent.
        logger.bind(tag=TAG).info("Running voiceprint server health check")
        
        try:
            # Health-check URL.
            parsed_url = urlparse(self.api_url)
            health_url = f"{parsed_url.scheme}://{parsed_url.netloc}/voiceprint/health?key={self.api_key}"
            
            # Send the health-check request.
            validate_endpoint(health_url, "voiceprint")
            with httpx_client("voiceprint", timeout=3) as client:
                response = client.get(health_url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "healthy":
                    logger.bind(tag=TAG).info("Voiceprint server health check passed")
                    is_healthy = True
                else:
                    logger.bind(tag=TAG).warning("Unexpected voiceprint server status")
                    is_healthy = False
            else:
                logger.bind(tag=TAG).warning(f"Voiceprint server health check failed: HTTP {response.status_code}")
                is_healthy = False
                
        except httpx.TimeoutException:
            logger.bind(tag=TAG).warning("Voiceprint server connection timed out")
            is_healthy = False
        except httpx.ConnectError:
            logger.bind(tag=TAG).warning("Voiceprint server connection refused")
            is_healthy = False
        except Exception:
            logger.bind(tag=TAG).warning("Voiceprint health service unavailable; review its endpoint")
            is_healthy = False
        
        # Cache results using the global cache manager.
        cache_manager.set(CacheType.VOICEPRINT_HEALTH, cache_key, is_healthy)
        logger.bind(tag=TAG).info(f"Health-check result cached: {is_healthy}")
        
        return is_healthy
    
    async def identify_speaker(self, audio_data: bytes, session_id: str) -> Optional[str]:
        """Identify the speaker."""
        if not self.enabled or not self.api_url or not self.api_key:
            logger.bind(tag=TAG).debug("Voiceprint recognition disabled or unconfigured; skipping identification")
            return None
            
        try:
            api_start_time = time.monotonic()
            
            # Prepare request headers.
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            # Prepare multipart/form-data.
            data = {'speaker_ids': ','.join(self.speaker_ids)}
            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            validate_endpoint(self.api_url, "voiceprint")
            # Network request.
            async with async_httpx_client("voiceprint", timeout=10) as session:
                response = await session.post(self.api_url, headers=headers, data=data, files=files)
                    
                if response.status_code == 200:
                    result = response.json()
                    speaker_id = result.get("speaker_id")
                    score = result.get("score", 0)
                    total_elapsed_time = time.monotonic() - api_start_time

                    logger.bind(tag=TAG).info(f"Voiceprint recognition time: {total_elapsed_time:.3f}s")

                    if score < self.similarity_threshold:
                        logger.bind(tag=TAG).warning("Voiceprint similarity below configured threshold")
                        return "未知说话人"

                    if speaker_id and speaker_id in self.speaker_map:
                        logger.bind(tag=TAG).info("Voiceprint recognition succeeded")
                        return self.speaker_map[speaker_id]["name"]
                    logger.bind(tag=TAG).warning("Voiceprint speaker not recognized")
                    return "未知说话人"
                else:
                    logger.bind(tag=TAG).error(f"Voiceprint API error: HTTP {response.status_code}")
                    return None
                        
        except (asyncio.TimeoutError, httpx.TimeoutException):
            elapsed = time.monotonic() - api_start_time
            logger.bind(tag=TAG).error(f"Voiceprint recognition timed out: {elapsed:.3f}s")
            return None
        except Exception:
            elapsed = time.monotonic() - api_start_time
            logger.bind(tag=TAG).error("Voiceprint recognition unavailable; review its endpoint")
            return None

