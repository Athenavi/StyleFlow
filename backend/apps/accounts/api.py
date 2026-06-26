from ninja import Router
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest

from .schemas import LoginIn, RegisterIn, RefreshIn, TokenOut, UserOut, ErrorOut
from .auth import create_access_token, create_refresh_token, decode_token, get_user_from_token
from .models import Profile

router = Router(tags=['认证'])


@router.post('/login', response={200: TokenOut, 401: ErrorOut})
def login(request, payload: LoginIn):
    """用户登录，返回 JWT Token"""
    user = authenticate(username=payload.username, password=payload.password)
    if user is None:
        return 401, {'code': 'INVALID_CREDENTIALS', 'message': '用户名或密码错误'}
    if not user.is_active:
        return 401, {'code': 'ACCOUNT_DISABLED', 'message': '账号已被禁用'}

    return TokenOut(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post('/register', response={201: UserOut, 400: ErrorOut})
@transaction.atomic
def register(request, payload: RegisterIn):
    """用户注册"""
    if User.objects.filter(username=payload.username).exists():
        return 400, {'code': 'USERNAME_EXISTS', 'message': '用户名已存在'}

    user = User.objects.create_user(
        username=payload.username,
        password=payload.password,
        email=payload.email,
    )
    # 更新 Profile 角色（post_save 信号已自动创建 Profile）
    profile = user.profile
    role = payload.role if payload.role in dict(Profile.ROLE_CHOICES) else 'designer'
    if profile.role != role:
        profile.role = role
        profile.save()

    return 201, UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.profile.role,
    )


@router.post('/refresh', response={200: TokenOut, 401: ErrorOut})
def refresh(request, payload: RefreshIn):
    """刷新 access token"""
    payload_data = decode_token(payload.refresh_token)
    if payload_data is None or payload_data.get('type') != 'refresh':
        return 401, {'code': 'INVALID_TOKEN', 'message': '无效的 refresh token'}

    try:
        user = User.objects.get(id=payload_data['user_id'])
    except User.DoesNotExist:
        return 401, {'code': 'USER_NOT_FOUND', 'message': '用户不存在'}

    return TokenOut(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.get('/me', response={200: UserOut, 401: ErrorOut})
def get_me(request):
    """获取当前用户信息"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return 401, {'code': 'NO_TOKEN', 'message': '未提供认证令牌'}

    token = auth[7:]
    user = get_user_from_token(token)
    if user is None:
        return 401, {'code': 'INVALID_TOKEN', 'message': '令牌无效或已过期'}

    profile = user.profile
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=profile.role,
        avatar=profile.avatar or '',
        is_admin=profile.role == 'admin',
    )


@router.patch('/me', response={200: UserOut, 401: ErrorOut})
def update_me(request):
    """更新当前用户信息"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return 401, {'code': 'NO_TOKEN', 'message': '未提供认证令牌'}

    token = auth[7:]
    user = get_user_from_token(token)
    if user is None:
        return 401, {'code': 'INVALID_TOKEN', 'message': '令牌无效或已过期'}

    import json
    body = json.loads(request.body)
    if 'email' in body:
        user.email = body['email']
        user.save()
    if 'phone' in body:
        user.profile.phone = body['phone']
        user.profile.save()

    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.profile.role,
        avatar=user.profile.avatar or '',
        is_admin=user.profile.role == 'admin',
    )
