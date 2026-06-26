"""AI 服务工厂 - 根据配置返回对应的服务实例"""
from django.conf import settings
from django.core.cache import cache
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

# Provider metadata
PROVIDER_INFO = {
    'openai': {'label': 'OpenAI', 'models': ['gpt-4o', 'gpt-4o-mini'], 'type': 'llm'},
    'claude': {'label': 'Anthropic Claude', 'models': ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'], 'type': 'llm'},
    'tongyi': {'label': '阿里云通义千问', 'models': ['qwen-max', 'qwen-plus', 'qwen-turbo'], 'type': 'llm'},
    'sd_webui': {'label': 'Stable Diffusion WebUI', 'models': ['sd-xl'], 'type': 'image'},
    'tongyi_image': {'label': '通义万相', 'models': ['wanx-v1'], 'type': 'image'},
}

# Active provider (cached in Redis, falls back to settings)
ACTIVE_PROVIDER_CACHE_KEY = 'styleflow:active_llm_provider'


def get_active_llm_config() -> dict:
    """获取当前活跃的 LLM 配置"""
    active_name = cache.get(ACTIVE_PROVIDER_CACHE_KEY)
    if not active_name:
        # 默认使用 settings 中的 default
        for name, config in settings.AI_SERVICES.get('llm', {}).items():
            return {**config, 'name': name}
    config = settings.AI_SERVICES.get('llm', {}).get(active_name)
    if not config:
        # fallback to first available
        for name, cfg in settings.AI_SERVICES.get('llm', {}).items():
            return {**cfg, 'name': name}
    return {**config, 'name': active_name}


def set_active_llm_provider(name: str) -> bool:
    """切换活跃的 LLM provider"""
    config = settings.AI_SERVICES.get('llm', {}).get(name)
    if not config:
        return False
    cache.set(ACTIVE_PROVIDER_CACHE_KEY, name, timeout=None)
    # 清除缓存的实例，下次调用时重新创建
    _llm_instances.pop(name, None)
    _llm_instances.pop('_active', None)
    return True


def get_llm_service(name: str = None) -> Optional[BaseLLMService]:
    """获取 LLM 服务实例"""
    if name is None:
        config = get_active_llm_config()
        name = config.get('name', 'default')
    else:
        config = settings.AI_SERVICES.get('llm', {}).get(name)

    if not config:
        return None

    instance_key = name
    if instance_key not in _llm_instances:
        provider = config['provider']

        if provider == 'openai':
            from .providers import OpenAIService
            _llm_instances[instance_key] = OpenAIService(
                api_key=config['api_key'],
                base_url=config.get('base_url'),
                model=config.get('model', 'gpt-4o'),
            )
        elif provider == 'claude':
            from .llm.claude import ClaudeService
            _llm_instances[instance_key] = ClaudeService(
                api_key=config['api_key'],
                model=config.get('model', 'claude-sonnet-4-20250514'),
            )
        elif provider == 'tongyi':
            from .llm.tongyi import TongyiService
            _llm_instances[instance_key] = TongyiService(
                api_key=config['api_key'],
                model=config.get('model', 'qwen-max'),
            )

    return _llm_instances.get(instance_key)


def get_image_service(name: str = "default") -> Optional[BaseImageService]:
    """获取图像服务实例"""
    if name not in _image_instances:
        config = settings.AI_SERVICES.get('image', {}).get(name)
        if not config:
            return None

        if config['provider'] == 'sd_webui':
            from .providers import SDWebUIService
            _image_instances[name] = SDWebUIService(base_url=config['base_url'])
        elif config['provider'] == 'tongyi_image':
            from .image.tongyi import TongyiImageService
            _image_instances[name] = TongyiImageService(
                api_key=config['api_key'],
                model=config.get('model', 'wanx-v1'),
            )
    return _image_instances.get(name)


def get_prompt_template(name: str = 'style') -> dict:
    return PROMPT_TEMPLATES.get(name, PROMPT_TEMPLATES['style'])
