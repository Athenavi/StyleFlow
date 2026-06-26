from ninja import Router, Schema, Form, File
from typing import List, Optional
from ninja.files import UploadedFile

from .models import UserMedia
from apps.accounts.auth import get_user_from_token
from common.storage import save_file, move_to_trash, restore_from_trash, delete_file

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
    created_at: str = ''

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


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
def list_media(request, category: str = None, search: str = None, trash: bool = False,
                page: int = 1, page_size: int = 50):
    """我的媒体库列表（分页+分类筛选）"""
    user = _get_user(request)
    qs = UserMedia.objects.filter(user=user, is_active=not trash)
    if category:
        qs = qs.filter(category=category)
    if search:
        from django.db import models
        qs = qs.filter(models.Q(title__icontains=search) | models.Q(tags__contains=search))
    total = qs.count()
    qs = qs.order_by('-created_at')[(page - 1) * page_size:page * page_size]
    return qs


@router.post('/upload', response=MediaUploadOut)
def upload_media(request, title: str = Form(''), category: str = Form('other'),
                  file: UploadedFile = File(...)):
    user = _get_user(request)
    ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
    if ext not in ALLOWED_EXTS:
        from ninja.errors import HttpError
        raise HttpError(400, f'不支持 {ext}（仅支持 jpg/png/webp/gif）')
    content = file.read()
    if len(content) > MAX_SIZE:
        raise HttpError(400, '文件超过 10MB 限制')
    file_url = save_file(user, content, file.name, subdir='media/')
    file_type = ext.replace('.', '')
    file_type = 'jpg' if file_type == 'jpeg' else file_type
    media = UserMedia.objects.create(
        user=user, title=title or file.name.rsplit('.', 1)[0],
        file_url=file_url, file_type=file_type, file_size=len(content),
        category=category if category in dict(UserMedia.CATEGORY_CHOICES) else 'other',
    )
    return {'id': media.id, 'file_url': media.file_url, 'title': media.title}


class IdsIn(Schema):
    ids: List[int]


class BatchCatIn(Schema):
    ids: List[int]
    category: str


@router.patch('/batch-category')
def batch_category(request, payload: BatchCatIn):
    """批量修改分类"""
    user = _get_user(request)
    if payload.category not in dict(UserMedia.CATEGORY_CHOICES):
        from ninja.errors import HttpError
        raise HttpError(400, '无效分类')
    updated = UserMedia.objects.filter(id__in=payload.ids, user=user).update(category=payload.category)
    return {'updated': updated}


@router.post('/batch-delete')
def batch_delete(request, payload: IdsIn):
    """批量删除（移入回收站——文件移到 .trash 目录）"""
    user = _get_user(request)
    items = UserMedia.objects.filter(id__in=payload.ids, user=user)
    for item in items:
        move_to_trash(user, item.file_url)
    updated = items.update(is_active=False)
    return {'moved_to_trash': updated}


@router.post('/restore/{media_id}')
def restore_media(request, media_id: int):
    """从回收站恢复（文件从 .trash 移回原位置）"""
    user = _get_user(request)
    media = UserMedia.objects.get(id=media_id, user=user, is_active=False)
    restore_from_trash(user, media.file_url)
    media.is_active = True
    media.save()
    return {'restored': True}


@router.post('/empty-trash')
def empty_trash(request):
    """清空回收站（永久删除文件和数据库记录）"""
    user = _get_user(request)
    items = UserMedia.objects.filter(user=user, is_active=False)
    for item in items:
        delete_file(item.file_url)
    deleted, _ = items.delete()
    return {'permanently_deleted': deleted}


@router.delete('/{media_id}', response={204: None})
def delete_media(request, media_id: int):
    """删除（移入回收站）"""
    user = _get_user(request)
    media = UserMedia.objects.get(id=media_id, user=user)
    move_to_trash(user, media.file_url)
    media.is_active = False
    media.save()
    return 204, None
