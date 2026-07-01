from app.core.config import settings
from app.services.llm.base import LLMClient
from app.services.llm.ollama import OllamaClient


def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider != "ollama":
        raise RuntimeError(f"Unsupported LLM_PROVIDER for local AI features: {settings.llm_provider}")

    return OllamaClient(
        base_url=settings.ollama_base_url or settings.local_llm_url,
        model=settings.ollama_model,
        fallback_model=settings.ollama_fallback_model,
        timeout_seconds=settings.ollama_timeout_seconds,
        context_tokens=settings.ollama_context_tokens,
        temperature=settings.llm_temperature,
    )
