from ninja import Router
from django.conf import settings

from common.aiservice.factory import PROVIDER_INFO, get_active_llm_config, set_active_llm_provider

router = Router(tags=['系统配置'])


@router.get('/providers')
def list_providers(request):
    """查询所有可用的 AI 服务提供商及其配置状态"""
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

    active = get_active_llm_config()

    return {
        'llm': llm_providers,
        'image': image_providers,
        'active_llm': active.get('name', 'default'),
    }


@router.post('/providers/switch')
def switch_provider(request, provider_name: str):
    """切换当前活跃的 LLM 提供商"""
    success = set_active_llm_provider(provider_name)
    if not success:
        from ninja.errors import HttpError
        raise HttpError(400, f'提供商 "{provider_name}" 不存在')
    return {'success': True, 'active_llm': provider_name}
