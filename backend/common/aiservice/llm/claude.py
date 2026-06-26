"""Claude (Anthropic) LLM 服务实现"""
import json
import time
import logging
from typing import Optional

import anthropic

from common.aiservice.llm import BaseLLMService, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeService(BaseLLMService):
    """Anthropic Claude LLM 服务"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._pricing = {
            "claude-sonnet-4-20250514": (3.0, 15),
            "claude-sonnet-4": (3.0, 15),
            "claude-3-5-haiku-20241022": (0.80, 4.0),
            "claude-3-opus-20240229": (15, 75),
        }

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        start = time.time()

        # 分离 system prompt
        system = None
        chat_messages = messages
        if messages and messages[0].get('role') == 'system':
            system = messages[0]['content']
            chat_messages = messages[1:]

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get('max_tokens', 4096),
            system=system,
            messages=chat_messages,
            temperature=kwargs.get('temperature', 0.7),
        )

        content = ''.join(block.text for block in resp.content if block.type == 'text')
        usage = resp.usage
        cost = self._calculate_cost(usage.input_tokens, usage.output_tokens)

        return LLMResponse(
            content=content,
            model=self.model,
            tokens_used=usage.input_tokens + usage.output_tokens,
            cost=cost,
            latency_ms=int((time.time() - start) * 1000),
        )

    def extract_json(self, prompt: str, schema: dict) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system="You are a helpful assistant that outputs JSON only.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = ''.join(block.text for block in resp.content if block.type == 'text')
        return json.loads(content)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._pricing.get(self.model, (3.0, 15))
        input_cost = input_tokens / 1_000_000 * pricing[0]
        output_cost = output_tokens / 1_000_000 * pricing[1]
        return round(input_cost + output_cost, 6)
