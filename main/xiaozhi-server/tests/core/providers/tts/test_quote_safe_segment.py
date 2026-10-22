"""TTSProviderBase._get_segment_text must not cut sentences inside quotes."""
import pytest

from core.providers.tts.base import TTSProviderBase


# Minimal stub for abstract-method instantiation; object.__new__ bypasses
# abstractmethod checks. New abstract methods intentionally do not fail here: tests do not call them.
class _TTS(TTSProviderBase):
    async def text_to_speak(self, text, output_file):
        return None


def _segments(text, step, first_sentence=False):
    tts = object.__new__(_TTS)
    tts.punctuations = ("。", "？", "?", "！", "!", "；", ";", "：")
    tts.first_sentence_punctuations = ("，", "~", "、", ",") + tts.punctuations
    tts.tts_text_buff, tts.processed_chars = [], 0
    tts.is_first_sentence, tts.tts_stop_request = first_sentence, False
    out = []
    for i in range(0, len(text), step):
        tts.tts_text_buff.append(text[i:i + step])
        segment = tts._get_segment_text()
        if segment:
            out.append(segment)
    tts.tts_stop_request = True
    rest = tts._get_segment_text()
    if rest:
        out.append(rest)
    return out


@pytest.mark.parametrize("step", [1, 3, 7])
def test_japanese_quote_followed_by_tte_stays_whole(step):
    assert _segments("思わず「わぁ！」って声が出たんだ。きみは？", step) == [
        "思わず「わぁ！」って声が出たんだ",
        "きみは？",
    ]


@pytest.mark.parametrize("step", [1, 4])
def test_chinese_quote_followed_by_speaker_stays_whole(step):
    segments = _segments("他大声说：“好！”然后笑了。", step)
    assert not any(seg.startswith("”") for seg in segments)
    # the leading “ is stripped by textUtils, the closing ” must stay with its sentence
    assert any("好！”然后笑了" in seg for seg in segments)


@pytest.mark.parametrize("step", [1, 5])
def test_closing_quote_then_period_is_not_left_alone(step):
    assert _segments("「すごい！」。次はね、雨！", step) == ["「すごい！」", "次はね、雨"]


@pytest.mark.parametrize("step", [1, 5])
def test_text_without_quotes_is_split_as_before(step):
    assert _segments("普通の文。次の文！最後", step) == ["普通の文", "次の文", "最後"]


@pytest.mark.parametrize("step", [1, 4])
def test_ascii_quote_at_stream_end_stays_whole(step):
    # The old logic split at the exclamation mark, leaving a stray quote in the next segment.
    # Now wait for the closing quote and emit the sentence together.
    assert _segments('She said, "Hi!"', step) == ['She said, "Hi!"']


_LQ, _RQ = "\u00ab", "\u00bb"        # French/Russian guillemets.
_GOPEN, _GCLOSE = "\u201e", "\u201c"  # German low-high quotation marks.


@pytest.mark.parametrize("step", [1, 4])
def test_guillemets_are_not_split(step):
    # The exclamation mark is inside guillemets; wait for the closer and sentence-ending punctuation.
    text = "Il a dit " + _LQ + "Bonjour ! " + _RQ + " puis est parti."
    assert _segments(text, step) == [text]


@pytest.mark.parametrize("step", [1, 4])
def test_german_low9_quotes_stay_whole(step):
    # The German closing quote U+201C also opens Chinese quotes and is counted as an opener.
    # Thus the German pair still appears unbalanced, with or without later sentence punctuation.
    # The whole German sentence flushes at stop: a conservative consequence of this conflict, not a defect.
    text = "Er sagte " + _GOPEN + "Hallo!" + _GCLOSE + " und ging."
    assert _segments(text, step) == [text]
    # A closing quote plus Chinese full stop also flushes together: U+201C's ambiguity blocks the normal path.
    text2 = "Er sagte " + _GOPEN + "Hallo!" + _GCLOSE + "。Dann geht er。"
    assert _segments(text2, step) == [text2]


@pytest.mark.parametrize("step", [1, 4])
def test_unterminated_quote_flushes_on_stop(step):
    # An unmatched quote must not hang: wait while streaming, then flush the whole segment at stop.
    assert _segments('"Hi', step) == ['"Hi']
    assert _segments("「わぁ", step) == ["「わぁ"]


_LB, _RB = "\u3010", "\u3011"  # 【】


@pytest.mark.parametrize("step", [1, 4])
def test_brackets_with_punct_inside_are_not_split(step):
    # Do not split at the exclamation mark inside full-width brackets.
    # Wait for the closing bracket, then split at sentence-ending punctuation.
    assert _segments("他说" + _LB + "重要！步骤" + _RB + "。然后走了。", step) == [
        "他说" + _LB + "重要！步骤",
        "然后走了",
    ]


def test_nested_mixed_quotes_stay_whole():
    # Count nested quote pairs independently without interference.
    assert _segments("“他说『好』了。”然后离开。", 1) == ["他说『好』了。”然后离开"]


def test_apostrophes_do_not_block_splitting():
    # Single quotes can be apostrophes (don't); do not balance them and delay the whole sentence.
    # Flushed text (remaining at stop) is emitted unchanged, without stripping.
    assert _segments("don't! It's fine.", 1) == ["don't", " It's fine."]


def test_first_sentence_still_splits_at_comma():
    assert _segments("そっか、実習で疲れたんだね。", 1, first_sentence=True)[0] == "そっか"
