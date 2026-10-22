from enum import Enum
import asyncio
from typing import Union, Optional


class InterfaceType(Enum):
    # Interface type.
    STREAM = "STREAM"  # Streaming interface.
    NON_STREAM = "NON_STREAM"  # Non-streaming interface.
    LOCAL = "LOCAL"  # Local service.


class AudioQueueBarrier:
    """Acknowledge prior PCM processing without running ASR on partial audio."""

    def __init__(self):
        self.future = asyncio.get_running_loop().create_future()

    def release(self):
        def complete():
            if not self.future.done():
                self.future.set_result(None)
        self.future.get_loop().call_soon_threadsafe(complete)
