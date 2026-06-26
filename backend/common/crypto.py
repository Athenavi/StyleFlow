"""API Key 加密工具

双层加密：独立加密密钥 + 用户密码
- 独立密钥 (API_KEY_ENCRYPTION_KEY) → 防数据库全量泄露
- 用户密码 → 改密即失效，防账号被盗后持续窃取
"""
import hashlib
import base64
import os
from cryptography.fernet import Fernet
from django.conf import settings


def _get_master_key(user_password_hash: str = '') -> bytes:
    """派生加密密钥 = SHA256(独立密钥 + ":" + 用户密码哈希)"""
    env_key = os.environ.get('API_KEY_ENCRYPTION_KEY') or getattr(settings, 'API_KEY_ENCRYPTION_KEY', '')
    if not env_key:
        # fallback 仅向后兼容
        env_key = hashlib.sha256(
            ('API_KEY_ENCRYPTION:' + settings.SECRET_KEY).encode()
        ).hexdigest()

    raw = hashlib.sha256(
        (env_key + ':' + user_password_hash).encode('utf-8')
    ).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt_api_key(api_key: str, user_password_hash: str = '') -> str:
    """加密 API key"""
    if not api_key:
        return ''
    key = _get_master_key(user_password_hash)
    f = Fernet(key)
    return f.encrypt(api_key.encode('utf-8')).decode('utf-8')


def decrypt_api_key(encrypted_key: str, user_password_hash: str = '') -> str:
    """解密 API key"""
    if not encrypted_key:
        return ''
    try:
        key = _get_master_key(user_password_hash)
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode('utf-8')).decode('utf-8')
    except Exception:
        return ''


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 10:
        return api_key[:3] + '...'
    return api_key[:3] + '...' + api_key[-4:]
