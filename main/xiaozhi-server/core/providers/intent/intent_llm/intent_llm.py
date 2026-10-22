import asyncio
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from ..base import IntentProviderBase
from plugins_func.functions.play_music import initialize_music_handler
from config.logger import setup_logging
from core.utils.util import get_system_error_response
import re
import json
import hashlib
import time



TAG = __name__
logger = setup_logging()


class IntentProvider(IntentProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.llm = None
        self.promot = ""
        # Import the global cache manager
        from core.utils.cache.manager import cache_manager, CacheType

        self.cache_manager = cache_manager
        self.CacheType = CacheType
        self.history_count = 4  # Use the latest 4 conversation entries by default

    def get_intent_system_prompt(self, functions_list: str) -> str:
        """
        Generate a system prompt from configured intents and available functions.
        Args:
            functions: Available functions as a JSON-formatted string.
        Returns:
            Formatted system prompt.
        """

        # Build function descriptions
        functions_desc = "Available functions:\n"
        for func in functions_list:
            func_info = func.get("function", {})
            name = func_info.get("name", "")
            desc = func_info.get("description", "")
            params = func_info.get("parameters", {})

            functions_desc += f"\nFunction name: {name}\n"
            functions_desc += f"Description: {desc}\n"

            if params:
                functions_desc += "Parameters:\n"
                for param_name, param_info in params.get("properties", {}).items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "")
                    functions_desc += f"- {param_name} ({param_type}): {param_desc}\n"

            functions_desc += "---\n"

        prompt = (
            "[Strict format] Return JSON only. Never return natural-language text.\n\n"
            "You are an intent-recognition assistant. Analyze the user's latest message, identify the intent, and call the appropriate function.\n\n"
            "[Important] For the following queries, return result_for_context without calling a function:\n"
            "- Current time (Chinese examples: 现在几点, 当前时间, 查询时间)\n"
            "- Today's date (Chinese examples: 今天几号, 今天星期几, 今天是什么日期)\n"
            "- Today's lunar date or solar term (Chinese examples: 今天农历几号, 今天什么节气)\n"
            "- Current city (Chinese examples: 我现在在哪里, 你知道我在哪个城市吗)"
            "The system will construct the answer from contextual information.\n\n"
            "- Questions about exiting that use question words such as '怎么', '为什么', or '如何' (for example, '怎么退出了？') are not exit commands; return {'function_call': {'name': 'continue_chat'}\n"
            "- Trigger handle_exit_intent only for explicit commands such as '退出系统', '结束对话', or '我不想和你说话了'.\n\n"
            f"{functions_desc}\n"
            "Processing steps:\n"
            "1. Analyze the input and identify the user's intent.\n"
            "2. Check for the basic information queries above (time, date, etc.); return result_for_context for them.\n"
            "3. Choose the best-matching available function.\n"
            "4. If a function matches, produce the corresponding function_call structure.\n"
            '5. If no function matches, return {"function_call": {"name": "continue_chat"}}\n\n'
            "Response format requirements:\n"
            "1. Return pure JSON without any other text.\n"
            "2. Include the function_call field.\n"
            "3. Include name inside function_call.\n"
            "4. Include arguments when the function requires parameters.\n\n"
            "Examples (Chinese user inputs):\n"
            "```\n"
            "User: 现在几点了？\n"
            'Response: {"function_call": {"name": "result_for_context"}}\n'
            "```\n"
            "```\n"
            "User: 当前电池电量是多少？\n"
            'Response: {"function_call": {"name": "get_battery_level", "arguments": {"response_success": "当前电池电量为{value}%", "response_failure": "无法获取Battery的当前电量百分比"}}}\n'
            "```\n"
            "```\n"
            "User: 当前屏幕亮度是多少？\n"
            'Response: {"function_call": {"name": "self_screen_get_brightness"}}\n'
            "```\n"
            "```\n"
            "User: 设置屏幕亮度为50%\n"
            'Response: {"function_call": {"name": "self_screen_set_brightness", "arguments": {"brightness": 50}}}\n'
            "```\n"
            "```\n"
            "User: 我想结束对话\n"
            'Response: {"function_call": {"name": "handle_exit_intent", "arguments": {"say_goodbye": "goodbye"}}}\n'
            "```\n"
            "```\n"
            "User: 你好啊\n"
            'Response: {"function_call": {"name": "continue_chat"}}\n'
            "```\n\n"
            "Notes:\n"
            "1. Return JSON only, without any other text.\n"
            '2. Check basic information queries first (time, date, etc.); return {"function_call": {"name": "result_for_context"}} without arguments.\n'
            '3. If no function matches, return {"function_call": {"name": "continue_chat"}}.\n'
            "4. Ensure valid JSON with all required fields.\n"
            "5. result_for_context takes no parameters; the system obtains the information from context.\n"
            "Multiple-command handling:\n"
            "- If one user input contains several commands (Chinese example: '打开灯并且调高音量'),\n"
            "- return a JSON array containing multiple function_call entries.\n"
            "- Example: {'function_calls': [{name:'light_on'}, {name:'volume_up'}]}\n\n"
            "[Final warning] Do not output natural language, emoji, or explanations. Output valid JSON only; violating this rule causes a system error."
        )
        return prompt

    async def replyResult(self, text: str, original_text: str):
        """Use asyncio.to_thread to avoid blocking the event loop."""
        try:
            user_prompt = (
                "Based on the information above, reply in the conversation's established language (Chinese by default) with a brief, natural, human tone. Return only the answer. The user now says: "
                + original_text
            )
            # Run the synchronous blocking call in the thread pool without blocking the event loop
            llm_result = await asyncio.to_thread(
                self.llm.response_no_stream,
                system_prompt=text,
                user_prompt=user_prompt,
            )
            return llm_result
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in generating reply result: {e}")
            return get_system_error_response(self.config)

    async def detect_intent(
        self, conn: "ConnectionHandler", dialogue_history: List[Dict], text: str
    ) -> str:
        if not self.llm:
            raise ValueError("LLM provider not set")
        if conn.func_handler is None:
            return '{"function_call": {"name": "continue_chat"}}'

        # Record the overall start time
        total_start_time = time.time()

        # Log the model in use
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Using intent-recognition model: {model_info}")

        # Calculate the cache key
        cache_key = hashlib.md5((conn.device_id + text).encode()).hexdigest()

        # Check the cache
        cached_intent = self.cache_manager.get(self.CacheType.INTENT, cache_key)
        if cached_intent is not None:
            cache_time = time.time() - total_start_time
            logger.bind(tag=TAG).debug(
                f"Using cached intent: {cache_key} -> {cached_intent}, elapsed: {cache_time:.4f}s"
            )
            return cached_intent

        if self.promot == "":
            functions = conn.func_handler.get_functions()
            if hasattr(conn, "mcp_client"):
                mcp_tools = conn.mcp_client.get_available_tools()
                if mcp_tools is not None and len(mcp_tools) > 0:
                    if functions is None:
                        functions = []
                    functions.extend(mcp_tools)

            self.promot = self.get_intent_system_prompt(functions)

        music_config = initialize_music_handler(conn)
        music_file_names = music_config["music_file_names"]
        prompt_music = f"{self.promot}\n<musicNames>{music_file_names}\n</musicNames>"

        home_assistant_cfg = conn.config["plugins"].get("home_assistant")
        if home_assistant_cfg:
            devices = home_assistant_cfg.get("devices", [])
        else:
            devices = []
        if len(devices) > 0:
            hass_prompt = "\nThe following home-device list contains locations, device names, and entity_id values for control through homeassistant.\n"
            for device in devices:
                hass_prompt += device + "\n"
            prompt_music += hass_prompt

        logger.bind(tag=TAG).debug(f"User prompt: {prompt_music}")

        # Build the conversation-history prompt
        msgStr = ""

        # Get recent conversation history
        start_idx = max(0, len(dialogue_history) - self.history_count)
        for i in range(start_idx, len(dialogue_history)):
            msgStr += f"{dialogue_history[i].role}: {dialogue_history[i].content}\n"

        msgStr += f"User: {text}\n"
        user_prompt = f"current dialogue:\n{msgStr}"

        # Record preprocessing completion
        preprocess_time = time.time() - total_start_time
        logger.bind(tag=TAG).debug(f"Intent preprocessing took {preprocess_time:.4f}s")

        # Use the LLM for intent recognition
        llm_start_time = time.time()
        logger.bind(tag=TAG).debug(f"Starting LLM intent recognition, model: {model_info}")

        try:
            # Run the synchronous blocking call in the thread pool without blocking the event loop
            intent = await asyncio.to_thread(
                self.llm.response_no_stream,
                system_prompt=prompt_music,
                user_prompt=user_prompt,
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in intent detection LLM call: {e}")
            return '{"function_call": {"name": "continue_chat"}}'

        # Record LLM call completion
        llm_time = time.time() - llm_start_time
        logger.bind(tag=TAG).debug(
            f"External LLM intent recognition completed, model: {model_info}, call time: {llm_time:.4f}s"
        )

        # Record the postprocessing start time
        postprocess_start_time = time.time()

        # Clean up and parse the response
        intent = intent.strip()
        # Try to extract the JSON portion
        match = re.search(r"\{.*\}", intent, re.DOTALL)
        if match:
            intent = match.group(0)

        # Record the total processing time
        total_time = time.time() - total_start_time
        logger.bind(tag=TAG).debug(
            f"[Intent performance] Model: {model_info}, total: {total_time:.4f}s, LLM call: {llm_time:.4f}s, query: '{text[:20]}...'"
        )

        # Try parsing JSON
        try:
            intent_data = json.loads(intent)
            # Format function_call for the handler when present
            if "function_call" in intent_data:
                function_data = intent_data["function_call"]
                function_name = function_data.get("name")
                function_args = function_data.get("arguments", {})

                # Log the recognized function call
                logger.bind(tag=TAG).info(
                    f"LLM recognized intent: {function_name}, arguments: {function_args}"
                )

                # Handle each intent type
                if function_name == "result_for_context":
                    # Answer basic information queries directly from context
                    logger.bind(tag=TAG).info(
                        "Detected result_for_context intent; answering directly from context"
                    )

                elif function_name == "continue_chat":
                    # Handle regular conversation
                    # Keep messages unrelated to tools
                    clean_history = [
                        msg
                        for msg in conn.dialogue.dialogue
                        if msg.role not in ["tool", "function"]
                    ]
                    conn.dialogue.dialogue = clean_history

                else:
                    # Handle function calls
                    logger.bind(tag=TAG).info(f"Detected function-call intent: {function_name}")

            # Cache and return the result through the shared path
            self.cache_manager.set(self.CacheType.INTENT, cache_key, intent)
            postprocess_time = time.time() - postprocess_start_time
            logger.bind(tag=TAG).debug(f"Intent postprocessing took {postprocess_time:.4f}s")
            return intent
        except json.JSONDecodeError:
            # Postprocessing duration
            postprocess_time = time.time() - postprocess_start_time
            logger.bind(tag=TAG).error(
                f"Could not parse intent JSON: {intent}, postprocessing time: {postprocess_time:.4f}s"
            )
            # Fall back to continue_chat when parsing fails
            return '{"function_call": {"name": "continue_chat"}}'
