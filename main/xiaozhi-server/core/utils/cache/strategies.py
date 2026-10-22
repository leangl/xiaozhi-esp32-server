"""
Cache strategies and data structures.
"""

import time
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class CacheStrategy(Enum):
    """Supported cache strategies."""

    TTL = "ttl"  # Time-based expiration.
    LRU = "lru"  # Least recently used.
    FIXED_SIZE = "fixed_size"  # Fixed capacity.
    TTL_LRU = "ttl_lru"  # Combined TTL and LRU strategy.


@dataclass
class CacheEntry:
    """Cache entry data structure."""

    value: Any
    timestamp: float
    ttl: Optional[float] = None  # Time to live, in seconds.
    access_count: int = 0
    last_access: float = None

    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.timestamp

    def is_expired(self) -> bool:
        """Check whether this entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def touch(self):
        """Update the access time and count."""
        self.last_access = time.time()
        self.access_count += 1
