from functools import wraps
from django.http import HttpRequest
from ninja.errors import HttpError

from .auth import get_user_from_token


def require_role(roles: list[str]):
    """角色权限装饰器：限制 API 访问角色"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                raise HttpError(401, '未提供认证令牌')

            token = auth[7:]
            user = get_user_from_token(token)
            if user is None:
                raise HttpError(401, '令牌无效或已过期')

            profile = getattr(user, 'profile', None)
            if profile is None or profile.role not in roles:
                raise HttpError(403, f'需要 {"/".join(roles)} 权限')

            request.user = user
            request.profile = profile
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_current_user(request: HttpRequest):
    """从请求中获取当前认证用户（供 Ninja Router 内使用）"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise HttpError(401, '未提供认证令牌')

    token = auth[7:]
    user = get_user_from_token(token)
    if user is None:
        raise HttpError(401, '令牌无效或已过期')
    return user
