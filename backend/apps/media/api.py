from ninja import Router, Schema
from typing import List, Optional

from .models import UserMedia
from apps.accounts.auth import get_user_from_token

router = Router(tags=['媒体库'])


class MediaOut(Schema):
    id: int
    title: str
    file_url: str
    thumbnail_url: str
    file_type: str
    file_size: int
    width: int
    height: int
    category: str
    tags: List[str]
    created_at: str


class MediaUploadOut(Schema):
    id: int
    file_url: str
    title: str


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


class MediaUploadIn(Schema):
    file_url: str
    title: str = ''
    category: str = 'other'
    file_type: str = 'png'
    file_size: int = 0
    width: int = 0
    height: int = 0


@router.post('/upload', response=MediaUploadOut)
def upload_media(request, payload: MediaUploadIn):
    """上传媒体文件（仅支持图片：jpg/png/webp/gif，最大10MB）"""
    user = _get_user(request)

    file_url = payload.file_url
    title = payload.title
    category = payload.category
    file_type = payload.file_type
    file_size = payload.file_size
    width = payload.width
    height = payload.height

    # 类型校验
    if file_type not in dict(UserMedia._meta.get_field('file_type').choices):
        from ninja.errors import HttpError
        raise HttpError(400, f'不支持的文件类型: {file_type}（仅支持 jpg/png/webp/gif）')

    media = UserMedia.objects.create(
        user=user,
        title=title or f'素材 {UserMedia.objects.filter(user=user).count() + 1}',
        file_url=file_url,
        file_type=file_type,
        file_size=min(file_size, UserMedia.MAX_FILE_SIZE) if file_size else 0,
        width=width,
        height=height,
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
