from enum import Enum
from typing import Union, Optional


class SentenceType(Enum):
    # Speech stage.
    FIRST = "FIRST"  # First sentence.
    MIDDLE = "MIDDLE"  # Speech in progress.
    LAST = "LAST"  # Last sentence.


class ContentType(Enum):
    # Content type.
    TEXT = "TEXT"  # Text content.
    FILE = "FILE"  # File content.
    ACTION = "ACTION"  # Action content.


class InterfaceType(Enum):
    # Interface type.
    DUAL_STREAM = "DUAL_STREAM"  # Bidirectional streaming.
    SINGLE_STREAM = "SINGLE_STREAM"  # Unidirectional streaming.
    NON_STREAM = "NON_STREAM"  # Non-streaming.


class TTSMessageDTO:
    def __init__(
        self,
        sentence_id: str,
        # Speech stage.
        sentence_type: SentenceType,
        # Content type.
        content_type: ContentType,
        # Content details, usually text to synthesize or lyrics for the audio.
        content_detail: Optional[str] = None,
        # Supply a file path when the content type is FILE.
        content_file: Optional[str] = None,
    ):
        self.sentence_id = sentence_id
        self.sentence_type = sentence_type
        self.content_type = content_type
        self.content_detail = content_detail
        self.content_file = content_file
