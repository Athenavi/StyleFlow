from ninja import Router, Schema, Form, File
from typing import List, Optional
from ninja.files import UploadedFile

from .models import UserMedia
from apps.accounts.auth import get_user_from_token
from common.storage import save_file

router = Router(tags=['媒体库'])


class MediaOut(Schema):
    id: int
    title: str
    file_url: str
    thumbnail_url: str = ''
    file_type: str
    file_size: int
    width: int = 0
    height: int = 0
    category: str
    tags: List[str] = []
    created_at: str


class MediaUploadOut(Schema):
    id: int
    file_url: str
    title: str


ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_SIZE = 10 * 1024 * 1024


def _get_user(request):
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')
    return user


@router.get('', response=List[MediaOut])
def list_media(request, category: str = None, search: str = None):
    """我的媒体库列表"""
    user = _get_user(request)
    qs = UserMedia.objects.filter(user=user, is_active=True)
    if category:
        qs = qs.filter(category=category)
    if search:
        from django.db import models
        qs = qs.filter(models.Q(title__icontains=search) | models.Q(tags__contains=search))
    return qs[:100]


@router.post('/upload', response=MediaUploadOut)
def upload_media(request, title: str = Form(''), category: str = Form('other'),
                  file: UploadedFile = File(...)):
    """上传媒体文件（multipart/form-data，仅支持 jpg/png/webp/gif，≤10MB）"""
    user = _get_user(request)

    # 校验扩展名
    ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
    if ext not in ALLOWED_EXTS:
        from ninja.errors import HttpError
        raise HttpError(400, f'不支持 {ext}（仅支持 jpg/png/webp/gif）')

    # 校验大小
    content = file.read()
    if len(content) > MAX_SIZE:
        from ninja.errors import HttpError
        raise HttpError(400, '文件超过 10MB 限制')

    # 保存文件到用户目录
    file_url = save_file(user, content, file.name, subdir='media/')

    # 写入数据库
    file_type = ext.replace('.', '')
    file_type = 'jpg' if file_type == 'jpeg' else file_type
    media = UserMedia.objects.create(
        user=user,
        title=title or file.name.rsplit('.', 1)[0],
        file_url=file_url,
        file_type=file_type,
        file_size=len(content),
        category=category if category in dict(UserMedia.CATEGORY_CHOICES) else 'other',
    )
    return {'id': media.id, 'file_url': media.file_url, 'title': media.title}


@router.delete('/{media_id}', response={204: None})
def delete_media(request, media_id: int):
    """删除媒体素材"""
    user = _get_user(request)
    media = UserMedia.objects.get(id=media_id, user=user)
    media.is_active = False
    media.save()
    return 204, None
