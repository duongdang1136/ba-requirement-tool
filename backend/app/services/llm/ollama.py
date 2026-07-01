import json
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int,
        context_tokens: int,
        temperature: float,
        fallback_model: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.context_tokens = context_tokens
        self.temperature = temperature
        self.fallback_model = fallback_model

    def generate_json(self, system: str, prompt: str) -> dict:
        last_error: Exception | None = None
        models = [self.model]
        if self.fallback_model and self.fallback_model not in models:
            models.append(self.fallback_model)

        for model in models:
            try:
                return self._generate_json_with_model(model, system, prompt)
            except Exception as exc:
                last_error = exc

        raise OllamaError(f"Ollama generation failed: {last_error}") from last_error

    def _generate_json_with_model(self, model: str, system: str, prompt: str) -> dict:
        payload: dict[str, Any] = {
            "model": model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": self.context_tokens,
                "temperature": self.temperature,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(
                f"Cannot call Ollama at {self.base_url}. Check Ollama is running and model '{model}' is pulled."
            ) from exc

        data = response.json()
        raw = data.get("response", "")
        if not raw:
            raise OllamaError("Ollama returned an empty response.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama did not return valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise OllamaError("Ollama JSON response must be an object.")
        return parsed
