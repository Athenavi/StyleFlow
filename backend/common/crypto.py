"""API Key 加密工具

使用用户的密码哈希派生加密密钥，确保：
1. 同一用户的 API key 只能用该用户的密码解密
2. 用户修改密码后，旧密钥自动失效（需重新设置 API key）
3. 数据库泄露时 API key 仍受保护
"""
import hashlib
import base64
from cryptography.fernet import Fernet
from django.conf import settings


def _derive_key(user_password_hash: str) -> bytes:
    """从用户密码哈希派生 Fernet 密钥（32 bytes base64）"""
    raw = hashlib.sha256(
        (settings.SECRET_KEY + ':' + user_password_hash).encode('utf-8')
    ).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt_api_key(api_key: str, user_password_hash: str) -> str:
    """加密 API key，返回 base64 密文"""
    if not api_key:
        return ''
    key = _derive_key(user_password_hash)
    f = Fernet(key)
    return f.encrypt(api_key.encode('utf-8')).decode('utf-8')


def decrypt_api_key(encrypted_key: str, user_password_hash: str) -> str:
    """解密 API key，返回明文"""
    if not encrypted_key:
        return ''
    try:
        key = _derive_key(user_password_hash)
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode('utf-8')).decode('utf-8')
    except Exception:
        return ''  # 密码已变更或数据损坏


def mask_api_key(api_key: str) -> str:
    """脱敏显示：sk-...abc"""
    if len(api_key) <= 8:
        return api_key[:3] + '...'
    return api_key[:3] + '...' + api_key[-3:]
