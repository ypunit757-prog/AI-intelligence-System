from app.ai.llm.openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    """Groq exposes an OpenAI-compatible chat completions API."""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key=api_key, model=model, base_url="https://api.groq.com/openai/v1")
