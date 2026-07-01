from typing import Protocol


class LLMClient(Protocol):
    model: str

    def generate_json(self, system: str, prompt: str) -> dict:
        ...
