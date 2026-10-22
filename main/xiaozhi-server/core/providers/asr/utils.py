import re
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

EMOTION_EMOJI_MAP = {
    "HAPPY": "🙂",
    "SAD": "😔",
    "ANGRY": "😡",
    "NEUTRAL": "😶",
    "FEARFUL": "😰",
    "DISGUSTED": "🤢",
    "SURPRISED": "😲",
    "EMO_UNKNOWN": "😶",  # Default unknown emotions to a neutral expression
}
# EVENT_EMOJI_MAP = {
#     "<|BGM|>": "🎼",
#     "<|Speech|>": "",
#     "<|Applause|>": "👏",
#     "<|Laughter|>": "😀",
#     "<|Cry|>": "😭",
#     "<|Sneeze|>": "🤧",
#     "<|Breath|>": "",
#     "<|Cough|>": "🤧",
# }

def lang_tag_filter(text: str) -> dict:
    """
    Parse FunASR recognition results, extracting tags and plain text in order

    Args:
        text: Raw ASR text, possibly containing multiple tags

    Returns:
        dict: {"language": "zh", "emotion": "SAD", "emoji": "😔", "content": "你好"} when tags are present;
              {"content": "纯文本"} when no tags are present (Chinese sample content is retained)

    Examples:
        FunASR format: <|language|><|emotion|><|event|><|other options|>original text
        >>> lang_tag_filter("<|zh|><|SAD|><|Speech|><|withitn|>你好啊，测试测试。")
        {"language": "zh", "emotion": "SAD", "emoji": "😔", "content": "你好啊，测试测试。"}
        >>> lang_tag_filter("<|en|><|HAPPY|><|Speech|><|withitn|>Hello hello.")
        {"language": "en", "emotion": "HAPPY", "emoji": "🙂", "content": "Hello hello."}
        >>> lang_tag_filter("plain text")
        {"content": "plain text"}
    """
    # Extract all tags in order
    tag_pattern = r"<\|([^|]+)\|>"
    all_tags = re.findall(tag_pattern, text)

    # Remove all <|...|> tags to obtain plain text
    clean_text = re.sub(tag_pattern, "", text).strip()
    # SenseVoice sometimes inserts spaces between Japanese words; remove spaces between Chinese/Japanese characters
    # Preserve spaces between Korean and English words
    clean_text = re.sub(
        r"(?<=[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60])\s+"
        r"(?=[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60])",
        "",
        clean_text,
    )

    # Keep the return structure consistent so callers do not treat plain text as a dictionary.
    if not all_tags:
        return {"content": clean_text}

    # Extract tags in the fixed FunASR order and return a dict
    language = all_tags[0] if len(all_tags) > 0 else "zh"
    emotion = all_tags[1] if len(all_tags) > 1 else "NEUTRAL"
    # event = all_tags[2] if len(all_tags) > 2 else "Speech"  # Event tag is currently unused

    result = {
        "content": clean_text,
        "language": language,
        "emotion": emotion,
        # "event": event,
    }

    # Add emoji mappings
    if emotion in EMOTION_EMOJI_MAP:
        result["emotion"] = EMOTION_EMOJI_MAP[emotion]
    # Event tag is currently unused
    # if event in EVENT_EMOJI_MAP:
    #     result["event"] = EVENT_EMOJI_MAP[event]

    return result
