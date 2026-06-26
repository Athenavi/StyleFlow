"""通义千问 (Tongyi Qwen) LLM 服务实现"""
import json
import time
import logging
from typing import Optional

import openai  # 通义千问兼容 OpenAI SDK

from common.aiservice.llm import BaseLLMService, LLMResponse

logger = logging.getLogger(__name__)


class TongyiService(BaseLLMService):
    """阿里云通义千问 LLM 服务（兼容 OpenAI SDK）"""

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model
        self._pricing = {
            "qwen-max": (2.0, 6.0),
            "qwen-plus": (0.8, 2.0),
            "qwen-turbo": (0.3, 0.6),
            "qwen2.5-72b-instruct": (4.0, 12.0),
        }

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        start = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 4096),
        )
        usage = resp.usage
        cost = self._calculate_cost(usage)
        return LLMResponse(
            content=resp.choices[0].message.content,
            model=self.model,
            tokens_used=usage.total_tokens,
            cost=cost,
            latency_ms=int((time.time() - start) * 1000),
        )

    def extract_json(self, prompt: str, schema: dict) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)

    def _calculate_cost(self, usage):
        pricing = self._pricing.get(self.model, (2.0, 6.0))
        input_cost = usage.prompt_tokens / 1_000_000 * pricing[0]
        output_cost = usage.completion_tokens / 1_000_000 * pricing[1]
        return round(input_cost + output_cost, 6)
