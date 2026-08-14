from typing import AsyncIterator, List

import httpx

from app.ai.llm.interface import ChatMessage, LLMInterface


class GeminiProvider(LLMInterface):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @staticmethod
    def _to_gemini_contents(messages: List[ChatMessage]) -> list:
        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        return contents

    async def generate(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": self._to_gemini_contents(messages),
                    "generationConfig": {"temperature": temperature},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream(self, messages: List[ChatMessage], temperature: float = 0.2) -> AsyncIterator[str]:
        # Simplified: Gemini's streaming endpoint returns a JSON array over
        # time; for a first version we fall back to non-streaming and yield
        # once. Replace with true SSE parsing (streamGenerateContent) as a
        # follow-up iteration.
        text = await self.generate(messages, temperature)
        yield text
