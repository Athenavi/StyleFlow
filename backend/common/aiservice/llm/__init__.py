from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    cost: float
    latency_ms: int


class BaseLLMService(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        ...

    @abstractmethod
    def extract_json(self, prompt: str, schema: dict) -> dict:
        ...

    def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        return self.chat([{"role": "user", "content": prompt}],
                        max_tokens=max_tokens).content
