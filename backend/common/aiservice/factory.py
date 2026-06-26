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


def _build_service(config: dict) -> Optional[object]:
    """根据 provider 配置构建服务实例"""
    provider = config['provider']
    if provider == 'openai':
        from .providers import OpenAIService
        return OpenAIService(
            api_key=config['api_key'],
            base_url=config.get('base_url'),
            model=config.get('model', 'gpt-4o'),
        )
    elif provider == 'claude':
        from .llm.claude import ClaudeService
        return ClaudeService(
            api_key=config['api_key'],
            model=config.get('model', 'claude-sonnet-4-20250514'),
        )
    elif provider == 'tongyi':
        from .llm.tongyi import TongyiService
        return TongyiService(
            api_key=config['api_key'],
            model=config.get('model', 'qwen-max'),
        )
    elif provider == 'sd_webui':
        from .providers import SDWebUIService
        return SDWebUIService(base_url=config['base_url'])
    elif provider == 'tongyi_image':
        from .image.tongyi import TongyiImageService
        return TongyiImageService(
            api_key=config['api_key'],
            model=config.get('model', 'wanx-v1'),
        )
    return None


def _get_provider_config(provider_type: str, provider_name: str, model: str = None) -> Optional[dict]:
    """获取 provider 的系统配置，合并用户选择的模型"""
    services = settings.AI_SERVICES.get(provider_type, {})
    config = services.get(provider_name)
    if not config:
        # 回退到 default
        config = services.get('default')
    if not config:
        return None
    config = {**config}
    if model:
        config['model'] = model
    return config


def get_user_llm_config(user) -> dict:
    """获取用户的 LLM 配置（含解密后的 API Key）"""
    try:
        setting = user.ai_setting
        provider_name = setting.llm_provider
        model = setting.llm_model
        user_api_key = setting.get_llm_api_key()
    except Exception:
        provider_name = None
        model = None
        user_api_key = None

    config = _get_provider_config('llm', provider_name, model) if provider_name else None
    if not config:
        config = _get_provider_config('llm', 'default', model)
    config = config or {}

    # 如果用户设置了自定义 API Key，覆盖系统配置
    if user_api_key:
        config['api_key'] = user_api_key

    return config


def get_user_image_config(user) -> dict:
    """获取用户的图像模型配置（含解密后的 API Key）"""
    try:
        setting = user.ai_setting
        provider_name = setting.image_provider
        model = setting.image_model
        user_api_key = setting.get_image_api_key()
    except Exception:
        provider_name = None
        model = None
        user_api_key = None

    config = _get_provider_config('image', provider_name, model) if provider_name else None
    if not config:
        config = _get_provider_config('image', 'default', model)
    config = config or {}

    if user_api_key:
        config['api_key'] = user_api_key

    return config


def get_llm_service_for_user(user) -> Optional[BaseLLMService]:
    """获取用户配置的 LLM 服务"""
    config = get_user_llm_config(user)
    if not config:
        return None
    key = f"user_llm_{user.id}_{config.get('provider')}_{config.get('model')}"
    if key not in _llm_instances:
        _llm_instances[key] = _build_service(config)
    return _llm_instances.get(key)


def get_image_service_for_user(user) -> Optional[BaseImageService]:
    """获取用户配置的图像生成服务"""
    config = get_user_image_config(user)
    if not config:
        return None
    key = f"user_img_{user.id}_{config.get('provider')}_{config.get('model')}"
    if key not in _image_instances:
        _image_instances[key] = _build_service(config)
    return _image_instances.get(key)


# ---- 全局（管理员）级别的兼容函数 ----
def get_active_llm_config() -> dict:
    active_name = cache.get('styleflow:active_llm_provider')
    services = settings.AI_SERVICES.get('llm', {})
    if active_name and active_name in services:
        return {**services[active_name], 'name': active_name}
    # fallback
    for name, cfg in services.items():
        return {**cfg, 'name': name}
    return {}


def set_active_llm_provider(name: str) -> bool:
    if name not in settings.AI_SERVICES.get('llm', {}):
        return False
    cache.set('styleflow:active_llm_provider', name, timeout=None)
    return True


def get_llm_service(name: str = None) -> Optional[BaseLLMService]:
    if name is None:
        config = get_active_llm_config()
        name = config.get('name', 'default')
    else:
        config = settings.AI_SERVICES.get('llm', {}).get(name)
    if not config:
        return None
    instance_key = f"global_{name}"
    if instance_key not in _llm_instances:
        _llm_instances[instance_key] = _build_service(config)
    return _llm_instances.get(instance_key)


def get_image_service(name: str = "default") -> Optional[BaseImageService]:
    if name not in _image_instances:
        config = settings.AI_SERVICES.get('image', {}).get(name)
        if config:
            _image_instances[name] = _build_service(config)
    return _image_instances.get(name)


def get_prompt_template(name: str = 'style') -> dict:
    return PROMPT_TEMPLATES.get(name, PROMPT_TEMPLATES['style'])
