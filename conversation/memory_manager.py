# memory_manager.py

from typing import Optional

from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

import config


class ConversationManager:

    MAX_BUFFER_TURNS = 10

    def __init__(self, memory_type: str = "buffer", llm=None):
        self.memory_type = memory_type
        self.llm = llm
        self._turn_count = 0

        if memory_type == "summary":
            if self.llm is None:
                self.llm = ChatGroq(
                    api_key=config.GROQ_API_KEY,
                    model=config.GROQ_MODEL,
                    temperature=0,
                )
            self.memory = ConversationSummaryMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True,
            )
        else:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
            )

    def add_user_message(self, message: str) -> None:
        self.memory.chat_memory.add_user_message(message)
        self._turn_count += 1
        self._trim_if_needed()

    def add_ai_message(self, message: str) -> None:
        self.memory.chat_memory.add_ai_message(message)

    def get_conversation_history(self) -> list:
        return self.memory.chat_memory.messages

    def get_formatted_history(self) -> str:
        lines = []
        for msg in self.memory.chat_memory.messages:
            role = "Customer" if isinstance(msg, HumanMessage) else "Agent"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def get_langchain_messages(self) -> list:
        return [
            HumanMessage(content=m.content) if isinstance(m, HumanMessage)
            else AIMessage(content=m.content)
            for m in self.memory.chat_memory.messages
        ]

    def turn_count(self) -> int:
        return self._turn_count

    def clear(self) -> None:
        self.memory.clear()
        self._turn_count = 0

    def _trim_if_needed(self) -> None:
        msgs = self.memory.chat_memory.messages
        max_msgs = self.MAX_BUFFER_TURNS * 2
        if len(msgs) > max_msgs:
            self.memory.chat_memory.messages = msgs[-max_msgs:]
