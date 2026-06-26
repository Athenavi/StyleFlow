"""AI 服务工厂 - 根据配置返回对应的服务实例"""
from django.conf import settings
from typing import Optional

from .llm import BaseLLMService
from .image import BaseImageService

_llm_instances: dict = {}
_image_instances: dict = {}

# 参数模板
PROMPT_TEMPLATES = {
    'style': {
        'prompt_prefix': 'fashion design, {prompt}, clean lines, professional garment, white background, front view',
        'negative_prompt': 'lowres, bad anatomy, bad hands, text, error, extra digit, cropped, worst quality',
        'steps': 25,
        'cfg_scale': 7,
    },
    'flat': {
        'prompt_prefix': 'flat drawing, technical sketch, {prompt}, front view, white background, fashion design, clean lines',
        'negative_prompt': 'shading, shadow, 3d, model, person, background, texture',
        'steps': 20,
        'cfg_scale': 6,
    },
    'model': {
        'prompt_prefix': 'model wearing {prompt}, fashion photography, studio lighting, full body, elegant pose',
        'negative_prompt': 'lowres, bad anatomy, bad hands, text, error, watermark, blurry',
        'steps': 30,
        'cfg_scale': 7.5,
    },
    'fabric': {
        'prompt_prefix': 'fabric texture closeup, {prompt}, material detail, high resolution, textile',
        'negative_prompt': 'lowres, person, model, garment, shadow, text',
        'steps': 20,
        'cfg_scale': 6,
    },
    'sketch': {
        'prompt_prefix': 'fashion illustration, {prompt}, sketch style, clean lines, design concept',
        'negative_prompt': 'photo, realistic, shading, color, background',
        'steps': 25,
        'cfg_scale': 7,
    },
}


def get_llm_service(name: str = "default") -> Optional[BaseLLMService]:
    """获取 LLM 服务实例"""
    if name not in _llm_instances:
        config = settings.AI_SERVICES.get('llm', {}).get(name)
        if not config:
            return None

        if config['provider'] == 'openai':
            from .providers import OpenAIService
            _llm_instances[name] = OpenAIService(
                api_key=config['api_key'],
                base_url=config.get('base_url'),
                model=config.get('model', 'gpt-4o'),
            )
        # Add Claude etc. here later
    return _llm_instances.get(name)


def get_image_service(name: str = "default") -> Optional[BaseImageService]:
    """获取图像服务实例"""
    if name not in _image_instances:
        config = settings.AI_SERVICES.get('image', {}).get(name)
        if not config:
            return None

        if config['provider'] == 'sd_webui':
            from .providers import SDWebUIService
            _image_instances[name] = SDWebUIService(
                base_url=config['base_url'],
            )
    return _image_instances.get(name)


def get_prompt_template(name: str = 'style') -> dict:
    """获取预设参数模板"""
    return PROMPT_TEMPLATES.get(name, PROMPT_TEMPLATES['style'])
