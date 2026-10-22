"""
Cache configuration management.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .strategies import CacheStrategy


class CacheType(Enum):
    """Supported cache types."""

    LOCATION = "location"
    WEATHER = "weather"
    LUNAR = "lunar"
    INTENT = "intent"
    IP_INFO = "ip_info"
    CONFIG = "config"
    DEVICE_PROMPT = "device_prompt"
    VOICEPRINT_HEALTH = "voiceprint_health"  # Voiceprint recognition health checks.
    AUDIO_DATA = "audio_data"  # Audio data cache.


@dataclass
class CacheConfig:
    """Cache configuration."""

    strategy: CacheStrategy = CacheStrategy.TTL
    ttl: Optional[float] = 300  # Default: five minutes.
    max_size: Optional[int] = 1000  # Default: at most 1,000 entries.
    cleanup_interval: float = 60  # Cleanup interval, in seconds.

    @classmethod
    def for_type(cls, cache_type: CacheType) -> "CacheConfig":
        """Return preset configuration for a cache type."""
        configs = {
            CacheType.LOCATION: cls(
                strategy=CacheStrategy.TTL, ttl=None, max_size=1000  # Manual invalidation.
            ),
            CacheType.IP_INFO: cls(
                strategy=CacheStrategy.TTL, ttl=86400, max_size=1000  # 24 hours.
            ),
            CacheType.WEATHER: cls(
                strategy=CacheStrategy.TTL, ttl=28800, max_size=1000  # Eight hours.
            ),
            CacheType.LUNAR: cls(
                strategy=CacheStrategy.TTL, ttl=2592000, max_size=365  # Expires after 30 days.
            ),
            CacheType.INTENT: cls(
                strategy=CacheStrategy.TTL_LRU, ttl=600, max_size=1000  # Ten minutes.
            ),
            CacheType.CONFIG: cls(
                strategy=CacheStrategy.FIXED_SIZE, ttl=None, max_size=20  # Manual invalidation.
            ),
            CacheType.DEVICE_PROMPT: cls(
                strategy=CacheStrategy.TTL, ttl=None, max_size=1000  # Manual invalidation.
            ),
            CacheType.VOICEPRINT_HEALTH: cls(
                strategy=CacheStrategy.TTL, ttl=600, max_size=100  # Expires after ten minutes.
            ),
            CacheType.AUDIO_DATA: cls(
                strategy=CacheStrategy.TTL, ttl=600, max_size=100  # Expires after ten minutes.
            ),
        }
        return configs.get(cache_type, cls())
