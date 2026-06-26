"""文件存储服务

支持双后端：
- local: 存储到本地 MEDIA_ROOT/users/{uuid}/
- s3:    存储到 S3/MinIO/OSS bucket users/{uuid}/

通过 settings.STORAGE_BACKEND 切换，默认 local。
生产环境可挂载 OSS 到本地路径，或直接切换到 s3 后端。
"""
import os
import uuid
import io
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def get_user_storage_uuid(user) -> str:
    """获取用户的存储 UUID（首次自动生成）"""
    profile = getattr(user, 'profile', None)
    if not profile:
        from apps.accounts.models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)

    if not profile.storage_uuid:
        profile.storage_uuid = uuid.uuid4().hex[:16]
        profile.save(update_fields=['storage_uuid'])
    return profile.storage_uuid


def _user_dir(user) -> str:
    """用户存储目录: users/{uuid}/"""
    return f"users/{get_user_storage_uuid(user)}/"


def save_file(user, file_content: bytes, filename: str, subdir: str = '') -> str:
    """
    保存文件并返回可公开访问的 URL。
    
    - subdir: 子目录（如 'media/', 'designs/'）
    - 返回: URL 路径
    """
    # 生成唯一文件名
    ext = Path(filename).suffix or '.png'
    unique_name = f"{uuid.uuid4().hex}{ext}"
    
    # 完整存储路径: users/{uuid}/{subdir}{unique_name}
    rel_path = f"{_user_dir(user)}{subdir}{unique_name}"
    
    backend = getattr(settings, 'STORAGE_BACKEND', 'local')
    
    if backend == 's3':
        return _save_s3(file_content, rel_path)
    else:
        return _save_local(file_content, rel_path)


def _save_local(file_content: bytes, rel_path: str) -> str:
    """保存到本地 MEDIA_ROOT"""
    full_path = Path(settings.MEDIA_ROOT) / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(file_content)
    # 返回完整 URL（同时适配前后端分离）
    base = getattr(settings, 'BACKEND_BASE_URL', 'http://localhost:8000')
    return f"{base}{settings.MEDIA_URL}{rel_path}"


def _save_s3(file_content: bytes, rel_path: str) -> str:
    """保存到 S3/MinIO/OSS"""
    import boto3
    s3 = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.upload_fileobj(
        io.BytesIO(file_content),
        settings.AWS_STORAGE_BUCKET_NAME,
        rel_path,
        ExtraArgs={'ContentType': _guess_mime(rel_path)},
    )
    return f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{rel_path}"


def _guess_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.webp': 'image/webp',
        '.gif': 'image/gif',
    }.get(ext, 'application/octet-stream')
