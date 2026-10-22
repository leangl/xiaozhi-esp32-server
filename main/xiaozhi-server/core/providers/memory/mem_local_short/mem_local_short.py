from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio


short_term_memory_prompt = """
# Spatiotemporal Memory Weaver

## Core mission
Build a growing, dynamic memory network that retains key information within limited space and tracks how it changes.
Summarize important information about user from the conversation to personalize future interactions. Keep the conversation's language for free-text memory values, using Chinese by default.

## Memory rules
### 1. Three-dimensional memory assessment (required on every update)
| Dimension | Assessment criterion | Weight |
|------------|---------------------------|--------|
| Recency | Freshness measured in conversation turns | 40% |
| Emotional intensity | Presence of 💖 markers or repeated mentions | 35% |
| Connection density | Number of links to other information | 25% |

### 2. Dynamic updates
**Name-change example (preserve the Chinese schema keys and sample names):**
Original memory: "曾用名": ["张三"], "现用名": "张三丰"
Trigger: detect naming phrases such as "我叫X" or "称呼我Y" (Chinese naming signals).
Procedure:
1. Move the old name into the "曾用名" list.
2. Record the naming timeline, for example: "2024-02-15 14:32:启用张三丰".
3. Append the example "从张三到张三丰的身份蜕变" to the memory cube.

### 3. Space optimization
- **Compress information** with a compact symbol system.
    - ✅"张三丰[北/软工/🐱]" (compact Chinese profile example)
    - ❌"北京软件工程师，养猫" (verbose Chinese profile example)
- **Eviction warning**: trigger when the total character count is ≥900.
    1. Remove information with a weight score <60 that has not appeared for 3 turns.
    2. Merge similar entries, keeping the latest timestamp.

## Memory structure
Return a parseable JSON string without explanations, comments, or annotations. Preserve the Chinese schema keys shown below. Extract saved memories only from the conversation; do not copy the example content. The pending-response examples mean urgent tasks and proactive help; the highlight-quote example means moving moments, strong emotions, and the user's exact words.
```json
{
  "时空档案": {
    "身份图谱": {
      "现用名": "",
      "特征标记": [] 
    },
    "记忆立方": [
      {
        "事件": "入职新公司",
        "时间戳": "2024-03-20",
        "情感值": 0.9,
        "关联项": ["下午茶"],
        "保鲜期": 30 
      }
    ]
  },
  "关系网络": {
    "高频话题": {"职场": 12},
    "暗线联系": [""]
  },
  "待响应": {
    "紧急事项": ["需立即处理的任务"],
    "潜在关怀": ["可主动提供的帮助"]
  },
  "高光语录": [
    "最打动人心的瞬间，强烈的情感表达，user的原话"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    # Find the next closing code fence after start
    end = json_code.find("```", start + 1)
    # print("start:", start, "end:", end)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        # Return once the API has provided summary memory
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        # Log the model in use
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Using memory-saving model: {model_info}")
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM is not set for memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        content = data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "Historical memory:\n"
            msgStr += self.short_memory

        # Current time
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"Current time: {time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)  # Validate JSON syntax
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            # When save_to_file is False, call the Java chat-summary API
            summary_id = session_id if session_id else self.role_id
            await generate_and_save_chat_summary(summary_id)
        logger.bind(tag=TAG).info(
            f"Save memory successful - Role: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
