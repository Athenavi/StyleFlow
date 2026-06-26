from ninja import Router, Schema
from django.conf import settings
from typing import Optional
from ninja.errors import HttpError

from common.aiservice.factory import (
    PROVIDER_INFO, get_active_llm_config, set_active_llm_provider,
    get_user_llm_config, get_user_image_config,
)
from apps.accounts.auth import get_user_from_token
from apps.accounts.ai_settings import UserAISetting

router = Router(tags=['系统配置'])


class UserAISettingsOut(Schema):
    llm_provider: str
    llm_model: str
    llm_api_base_url: str = ''
    image_provider: str
    image_model: str
    image_api_base_url: str = ''
    llm_api_key_masked: str = ''
    image_api_key_masked: str = ''


class UserAISettingsIn(Schema):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_base_url: Optional[str] = None
    image_provider: Optional[str] = None
    image_model: Optional[str] = None
    image_api_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None     # 明文传入，加密存储
    image_api_key: Optional[str] = None   # 明文传入，加密存储


def _get_current_user(request):
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        raise HttpError(401, '未认证')
    return user


@router.get('/providers')
def list_providers(request):
    """查询所有可用 provider + 当前用户的自定义配置"""
    user = _get_current_user(request)

    llm_providers = []
    for name, config in settings.AI_SERVICES.get('llm', {}).items():
        info = PROVIDER_INFO.get(config['provider'], {})
        llm_providers.append({
            'name': name,
            'label': info.get('label', config['provider']),
            'provider': config['provider'],
            'model': config.get('model', ''),
            'configured': bool(config.get('api_key')),
            'models': info.get('models', []),
        })

    image_providers = []
    for name, config in settings.AI_SERVICES.get('image', {}).items():
        info = PROVIDER_INFO.get(config['provider'], {})
        image_providers.append({
            'name': name,
            'label': info.get('label', config['provider']),
            'provider': config['provider'],
            'model': config.get('model', ''),
            'configured': bool(config.get('api_key') or config.get('base_url')),
        })

    # 用户自定义设置
    user_llm = get_user_llm_config(user)
    user_img = get_user_image_config(user)

    return {
        'llm': llm_providers,
        'image': image_providers,
        'active_llm': user_llm.get('name') or get_active_llm_config().get('name', 'default'),
        'user_settings': {
            'llm_provider': user_llm.get('provider', 'openai'),
            'llm_model': user_llm.get('model', 'gpt-4o'),
            'image_provider': user_img.get('provider', 'sd_webui'),
            'image_model': user_img.get('model', 'sd-xl'),
        },
    }


@router.get('/my-settings', response=UserAISettingsOut)
def get_my_ai_settings(request):
    """获取当前用户的 AI 配置（API Key 脱敏显示）"""
    user = _get_current_user(request)
    setting, _ = UserAISetting.objects.get_or_create(user=user)
    return {
        'llm_provider': setting.llm_provider,
        'llm_model': setting.llm_model,
        'llm_api_base_url': setting.llm_api_base_url or '',
        'image_provider': setting.image_provider,
        'image_model': setting.image_model,
        'image_api_base_url': setting.image_api_base_url or '',
        'llm_api_key_masked': setting.llm_api_key_masked,
        'image_api_key_masked': setting.image_api_key_masked,
    }


@router.patch('/my-settings', response=UserAISettingsOut)
def update_my_ai_settings(request, payload: UserAISettingsIn):
    """更新当前用户的 AI 配置（API Key 自动加密存储）"""
    user = _get_current_user(request)
    setting, _ = UserAISetting.objects.get_or_create(user=user)

    update_data = payload.dict(exclude_unset=True)

    if 'llm_api_key' in update_data:
        setting.set_llm_api_key(update_data.pop('llm_api_key'))
    if 'image_api_key' in update_data:
        setting.set_image_api_key(update_data.pop('image_api_key'))

    for key, value in update_data.items():
        setattr(setting, key, value)
    setting.save()

    return {
        'llm_provider': setting.llm_provider,
        'llm_model': setting.llm_model,
        'llm_api_base_url': setting.llm_api_base_url or '',
        'image_provider': setting.image_provider,
        'image_model': setting.image_model,
        'image_api_base_url': setting.image_api_base_url or '',
        'llm_api_key_masked': setting.llm_api_key_masked,
        'image_api_key_masked': setting.image_api_key_masked,
    }


@router.post('/providers/switch')
def switch_provider(request, provider_name: str):
    """切换全局默认 LLM（管理员用）"""
    success = set_active_llm_provider(provider_name)
    if not success:
        raise HttpError(400, f'提供商 "{provider_name}" 不存在')
    return {'success': True, 'active_llm': provider_name}
