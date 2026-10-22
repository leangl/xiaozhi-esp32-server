# Retained benchmark language data and compatibility literals

Historical translation record: the provider benchmark modules described below
were retired from the supported profile. This record does not advertise an
executable benchmark. See `docs/performance_tester.md` from the repository root.

The benchmark launcher, comments, docstrings, CLI help, diagnostics, report headings,
and unparsed status descriptions are English. The exact exceptions below preserve
benchmark inputs and compatibility rather than exempting any whole source file.
No benchmark or provider call is needed to review these strings.

## Language-specific inputs

- `performance_tester_llm.py`, `test_sentences`: the five original Chinese agent
  conversation inputs ask for comfort after a difficult day, tomorrow's weather,
  an interesting story, the current time/day of the week, and an 8 a.m. meeting
  alarm for the following day. Their wording and lengths remain unchanged.
- The same file's system-prompt substitutions identify Xiaozhi as a smart, friendly
  AI assistant and supply a fixed date/time, Saturday, a lunar date, Beijing, and
  sunny weather at 25–32 degrees Celsius. The fallback system prompt also requests
  a warm, friendly tone. Preserve the original Chinese input/reply language, the
  exact date/weather examples, and every double-brace template key.
- `performance_tester_tts.py`, `test_sentences`: the three original Classical
  Chinese excerpts are speech synthesis fixtures. Preserve their text, punctuation,
  selection slices, and lengths; translating them would change the measured workload.
  The shorter connectivity utterance means **connection test** and is also spoken
  input, not a log label.
- `performance_tester_stream_tts.py`, `test_texts`: the original Chinese sample
  means **Hello, this is a sentence.** Its `instruct_text` value asks for natural,
  fluent speech. Both are provider input affecting output language or style, not
  developer instructions to translate.
- `performance_tester_vllm.py`, `test_questions`: the original Chinese questions
  mean **What is in this image?** and **Describe this image in detail.** Preserve
  them, image paths, and the benchmark's reply language.

## Parsed compatibility literals

- In the ASR, LLM, TTS, and vision testers, the original Chinese credential sentinel
  means **your**. It detects unfilled sample credentials. Keep the literal in the
  membership/subsequence checks so old configuration examples are still rejected.
- In the LLM response collector, two Chinese substrings mean **exception** and
  **error**. They classify provider output and exception messages; changing them
  would alter error detection and partial-response handling.
- Streaming ASR/TTS success statuses retain their original localized **Success
  (valid trials / requested trials)** wording. Both report sorters test the original
  success substring to distinguish successful results from failed ones. Producers,
  matching tokens, interpolation expressions, and punctuation stay unchanged.

## Stable result names

Chinese `name` values passed to `_calculate_result`, returned for unavailable ASR
services, and stored in the streaming ASR fallback name map remain unchanged as
benchmark result labels. They correspond to:

| Tester | English reading of retained label |
| --- | --- |
| `DoubaoStreamASRTester` | Doubao streaming ASR |
| `QwenASRFlashTester` | Tongyi Qianwen ASR |
| `XunfeiStreamASRTester` | Xunfei streaming ASR |
| `test_aliyun_tts` | Aliyun TTS |
| `test_alibl_tts` | Aliyun Bailian TTS |
| `test_doubao_tts` | Volcengine TTS |
| `test_xunfei_tts` | Xunfei TTS |

Provider configuration keys, model/voice IDs, authentication fields, protocol keys,
endpoints, timeout values, success thresholds, outlier filters, timing boundaries,
sample counts, formulas, and number-format specifiers are not translation targets.
English time-unit labels still denote seconds; the measured values are unchanged.
