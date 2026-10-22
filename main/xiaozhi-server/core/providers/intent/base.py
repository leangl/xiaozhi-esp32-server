from abc import ABC, abstractmethod
from typing import List, Dict
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class IntentProviderBase(ABC):
    def __init__(self, config):
        self.config = config

    def set_llm(self, llm):
        self.llm = llm
        # Read the model name and type information.
        model_name = getattr(llm, "model_name", str(llm.__class__.__name__))
        # Log detailed configuration information.
        logger.bind(tag=TAG).info(f"Intent recognition LLM set to: {model_name}")

    @abstractmethod
    async def detect_intent(self, conn, dialogue_history: List[Dict], text: str) -> str:
        """
        Detect the intent of the user's latest utterance.
        Args:
            dialogue_history: Conversation history; each record contains role and content.
        Returns:
            Recognized intent in the following legacy Chinese command format
            (examples are compatibility/language data, not translated identifiers):
            - "继续聊天" (continue chatting)
            - "结束聊天" (end the conversation)
            - "播放音乐 歌名" or "随机播放音乐" (play a named song or random music)
            - "查询天气 地点名" or "查询天气 [当前位置]" (weather for a place/current location)
        """
        pass
