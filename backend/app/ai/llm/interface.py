from abc import ABC, abstractmethod
from typing import AsyncIterator, List, TypedDict


class ChatMessage(TypedDict):
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMInterface(ABC):
    """All providers implement this so app code never depends on a
    specific vendor SDK. Swap providers purely via LLM_PROVIDER."""

    @abstractmethod
    async def generate(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        """Non-streaming completion."""

    @abstractmethod
    async def stream(self, messages: List[ChatMessage], temperature: float = 0.2) -> AsyncIterator[str]:
        """Streaming completion — yields text deltas."""
