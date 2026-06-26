from datetime import datetime, timedelta
from typing import Optional
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from ninja import Schema


class LoginIn(Schema):
    username: str
    password: str


class RegisterIn(Schema):
    username: str
    password: str
    email: str = ''
    role: str = 'designer'


class TokenOut(Schema):
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'


class UserOut(Schema):
    id: int
    username: str
    email: str
    role: str
    avatar: str = ''


class ErrorOut(Schema):
    code: str
    message: str


def create_access_token(user: User) -> str:
    """生成 access token（30分钟有效期）"""
    now = datetime.utcnow()
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': now + timedelta(minutes=30),
        'iat': now,
        'type': 'access',
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def create_refresh_token(user: User) -> str:
    """生成 refresh token（7天有效期）"""
    now = datetime.utcnow()
    payload = {
        'user_id': user.id,
        'exp': now + timedelta(days=7),
        'iat': now,
        'type': 'refresh',
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> Optional[dict]:
    """解码并验证 token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token: str) -> Optional[User]:
    """从 token 获取用户"""
    payload = decode_token(token)
    if payload is None:
        return None
    try:
        return User.objects.get(id=payload.get('user_id'))
    except User.DoesNotExist:
        return None
