"""文件存储服务

支持双后端：
- local: 存储到本地 MEDIA_ROOT/users/{uuid}/...
- s3:    存储到 S3 / MinIO / OSS bucket users/{uuid}/...

通过 settings.STORAGE_BACKEND 切换，默认 local。

URL 约定（重要）：
- 默认生成「同源相对路径」，如 /media/users/xxx/media/yyy.png。
  这样无论用户用 localhost、局域网 IP 还是域名访问，图片都能正常加载。
- 若显式设置了 BACKEND_BASE_URL（例如 http://192.168.1.5:8000），则生成绝对地址。
- 服务端需要真正抓取文件时（AI 图生图、虚拟试衣），用 to_absolute_url() 还原为可请求地址。
"""
import io
import os
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings


# --------------------------------------------------------------------------- #
# 路径与 URL 工具
# --------------------------------------------------------------------------- #
def _public_url(rel_path: str) -> str:
    """相对路径 → 对外可访问 URL（同源相对路径，或配置了 BACKEND_BASE_URL 时的绝对地址）"""
    rel_path = str(rel_path).lstrip('/')
    base = (getattr(settings, 'BACKEND_BASE_URL', '') or '').rstrip('/')
    return f"{base}{settings.MEDIA_URL}{rel_path}"


def _url_to_rel_path(file_url: str) -> str:
    """把任意形式的文件地址还原为相对 MEDIA_ROOT 的路径

    兼容以下写法：
      http://host:8000/media/users/uuid/a.png  （历史绝对地址）
      /media/users/uuid/a.png                  （当前相对地址）
      media/users/uuid/a.png                   （旧相对地址）
      users/uuid/a.png                         （纯相对路径）
    """
    if not file_url:
        return ''
    url = str(file_url).strip()
    path = urlparse(url).path if '://' in url else url
    media = str(settings.MEDIA_URL)
    idx = path.find(media)
    if idx != -1:
        return unquote(path[idx + len(media):]).lstrip('/')
    for prefix in ('/media/', 'media/'):
        if path.startswith(prefix):
            return unquote(path[len(prefix):]).lstrip('/')
    return unquote(path.lstrip('/'))


def to_local_path(file_url: str) -> Path:
    """文件地址 → 本地磁盘路径（local 后端专用）"""
    return Path(settings.MEDIA_ROOT) / _url_to_rel_path(file_url)


def to_absolute_url(file_url: str) -> str:
    """文件地址 → 服务端可直接请求的绝对 URL（供 AI 服务读取图片使用）"""
    url = str(file_url or '').strip()
    if url.startswith(('http://', 'https://')):
        return url
    base = (getattr(settings, 'BACKEND_BASE_URL', '') or '').rstrip('/')
    if not base:
        port = os.getenv('BACKEND_PORT', '8000')
        base = f"http://127.0.0.1:{port}"
    return f"{base}{settings.MEDIA_URL}{_url_to_rel_path(url)}"


def _guess_mime(path: str) -> str:
    ext = Path(str(path)).suffix.lower()
    return {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.webp': 'image/webp',
        '.gif': 'image/gif',
    }.get(ext, 'application/octet-stream')


def read_file_bytes(file_url: str, timeout: int = 30) -> bytes:
    """读取文件内容：local 后端直接读磁盘，其它情况按绝对 URL 下载。

    供 AI 服务（图生图 / 虚拟试衣）取用素材，避免服务端再去依赖 HTTP 端口。
    """
    local = to_local_path(file_url)
    if local.exists() and local.is_file():
        return local.read_bytes()
    import requests
    resp = requests.get(to_absolute_url(file_url), timeout=timeout)
    resp.raise_for_status()
    return resp.content


# --------------------------------------------------------------------------- #
# 用户存储目录
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# 写入
# --------------------------------------------------------------------------- #
def save_bytes(file_content: bytes, subdir: str = '', ext: str = '.png') -> str:
    """保存不绑定用户的文件（AI 出图结果等），返回可访问 URL"""
    ext = ext if ext.startswith('.') else f'.{ext}'
    return _write(file_content, f"{subdir.lstrip('/')}{uuid.uuid4().hex}{ext}")


def save_file(user, file_content: bytes, filename: str, subdir: str = '') -> str:
    """
    保存文件并返回可公开访问的 URL。

    - subdir: 子目录（如 'media/', 'designs/'）
    - 返回: URL 路径
    """
    ext = Path(filename).suffix or '.png'
    rel_path = f"{_user_dir(user)}{subdir}{uuid.uuid4().hex}{ext}"
    return _write(file_content, rel_path)


def _write(file_content: bytes, rel_path: str) -> str:
    if getattr(settings, 'STORAGE_BACKEND', 'local') == 's3':
        return _save_s3(file_content, rel_path)
    return _save_local(file_content, rel_path)


def _save_local(file_content: bytes, rel_path: str) -> str:
    """保存到本地 MEDIA_ROOT"""
    full_path = Path(settings.MEDIA_ROOT) / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(file_content)
    return _public_url(rel_path)


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


# --------------------------------------------------------------------------- #
# 回收站 / 删除（local 后端为真实文件移动，s3 后端下仅标记数据库状态）
# --------------------------------------------------------------------------- #
def _trash_rel_path(rel_path: str) -> str:
    return f".trash/{rel_path.lstrip('/')}"


def move_to_trash(user, file_url: str) -> bool:
    """将文件移入回收站 MEDIA_ROOT/.trash/（保留原相对路径结构）"""
    try:
        rel = _url_to_rel_path(file_url)
        if not rel:
            return False
        old_path = Path(settings.MEDIA_ROOT) / rel
        if not old_path.exists():
            return False
        trash_path = Path(settings.MEDIA_ROOT) / _trash_rel_path(rel)
        trash_path.parent.mkdir(parents=True, exist_ok=True)
        if trash_path.exists():
            trash_path.unlink()
        old_path.replace(trash_path)
        return True
    except Exception:
        return False


def restore_from_trash(user, file_url: str) -> bool:
    """从回收站恢复文件到原位置"""
    try:
        rel = _url_to_rel_path(file_url)
        if not rel:
            return False
        trash_path = Path(settings.MEDIA_ROOT) / _trash_rel_path(rel)
        if not trash_path.exists():
            return False
        orig_path = Path(settings.MEDIA_ROOT) / rel
        orig_path.parent.mkdir(parents=True, exist_ok=True)
        trash_path.replace(orig_path)
        return True
    except Exception:
        return False


def delete_file(file_url: str) -> bool:
    """永久删除文件（同时清理回收站中的副本）"""
    try:
        rel = _url_to_rel_path(file_url)
        if not rel:
            return False
        for path in (Path(settings.MEDIA_ROOT) / rel,
                     Path(settings.MEDIA_ROOT) / _trash_rel_path(rel)):
            if path.exists():
                path.unlink()
        return True
    except Exception:
        return False
