from functools import lru_cache

from app.ai.llm.gemini_provider import GeminiProvider
from app.ai.llm.groq_provider import GroqProvider
from app.ai.llm.interface import LLMInterface
from app.ai.llm.ollama_provider import OllamaProvider
from app.ai.llm.openai_provider import OpenAIProvider
from app.config.settings import get_settings


@lru_cache
def get_llm() -> LLMInterface:
    """Provider is selected purely from LLM_PROVIDER — never hardcoded."""
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.llm_model)
    if provider == "groq":
        return GroqProvider(api_key=settings.groq_api_key, model=settings.llm_model)
    if provider == "gemini":
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.llm_model)
    return OllamaProvider(base_url=settings.ollama_base_url, model=settings.llm_model)
