import json
import logging
from typing import Optional

import openai
import requests

from common.aiservice.llm import BaseLLMService, LLMResponse
from common.aiservice.image import BaseImageService, ImageResult

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """OpenAI / 兼容API 的 LLM 服务"""

    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4o"):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._pricing = {
            "gpt-4o": (2.5, 10),
            "gpt-4o-mini": (0.15, 0.6),
            "gpt-4o-2024-08-06": (2.5, 10),
            "claude-sonnet-4-20250514": (3.0, 15),
        }

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        import time
        start = time.time()
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
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
        content = resp.choices[0].message.content
        return json.loads(content)

    def _calculate_cost(self, usage):
        pricing = self._pricing.get(self.model, (2.5, 10))
        input_cost = usage.prompt_tokens / 1_000_000 * pricing[0]
        output_cost = usage.completion_tokens / 1_000_000 * pricing[1]
        return round(input_cost + output_cost, 6)


class SDWebUIService(BaseImageService):
    """Stable Diffusion WebUI API 服务"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def text2img(self, prompt: str, negative_prompt: str = "",
                  width: int = 512, height: int = 768, **kwargs) -> ImageResult:
        import time
        start = time.time()

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or self._default_neg(),
            "width": width,
            "height": height,
            "steps": kwargs.get("steps", 25),
            "cfg_scale": kwargs.get("cfg_scale", 7),
            "seed": kwargs.get("seed", -1),
            "sampler_name": kwargs.get("sampler", "Euler a"),
        }

        resp = requests.post(
            f"{self.base_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        image_url = self._save_to_storage(data['images'][0])
        return ImageResult(
            image_url=image_url,
            seed=data.get('seed', -1),
            model='sd-xl',
            latency_ms=int((time.time() - start) * 1000),
        )

    def img2img(self, init_image_url: str, prompt: str, **kwargs) -> ImageResult:
        import time
        start = time.time()

        payload = {
            "init_images": [self._fetch_image_b64(init_image_url)],
            "prompt": prompt,
            "negative_prompt": kwargs.get("negative_prompt", self._default_neg()),
            "steps": kwargs.get("steps", 25),
            "cfg_scale": kwargs.get("cfg_scale", 7),
            "denoising_strength": kwargs.get("denoising_strength", 0.75),
        }

        resp = requests.post(
            f"{self.base_url}/sdapi/v1/img2img",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        image_url = self._save_to_storage(data['images'][0])
        return ImageResult(
            image_url=image_url,
            seed=data.get('seed', -1),
            model='sd-xl',
            latency_ms=int((time.time() - start) * 1000),
        )

    def _default_neg(self):
        return ("lowres, bad anatomy, bad hands, text, error, extra digit, "
                "worst quality, low quality, jpeg artifacts, signature, watermark, blurry")

    def _save_to_storage(self, base64_image: str) -> str:
        """保存 base64 图片到 MinIO，返回 URL"""
        import uuid, base64, io
        from django.conf import settings
        import boto3

        image_data = base64.b64decode(base64_image.split(',', 1)[-1])
        filename = f"designs/{uuid.uuid4().hex}.png"

        s3 = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        s3.upload_fileobj(
            io.BytesIO(image_data),
            settings.AWS_STORAGE_BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': 'image/png'},
        )
        return f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"

    def _fetch_image_b64(self, url: str) -> str:
        """从 URL 获取图片并转为 base64"""
        import base64
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode('utf-8')
