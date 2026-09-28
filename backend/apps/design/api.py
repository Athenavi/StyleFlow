from ninja import Router
from ninja.pagination import paginate, PageNumberPagination
from django.db import models
from typing import List, Optional

from .models import Design
from .schemas import (
    DesignOut, DesignCreateIn, DesignUpdateIn,
    GenerateIn, GenerateOut, TaskStatusOut, DesignVersionOut,
)
from .tasks import generate_design_task
from apps.accounts.auth import get_user_from_token

router = Router(tags=['设计工坊'])


def _get_user(request):
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')
    return user


@router.get('', response=List[DesignOut])
@paginate(PageNumberPagination, page_size=20)
def list_designs(request,
                 category: Optional[str] = None,
                 status: Optional[str] = None,
                 search: Optional[str] = None):
    """设计稿列表（分页+筛选）"""
    user = _get_user(request)
    qs = Design.objects.filter(creator=user, is_active=True)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(models.Q(title__icontains=search) | models.Q(tags__contains=search))
    return qs


@router.post('', response=DesignOut)
def create_design(request, payload: DesignCreateIn):
    """手动创建设计稿"""
    user = _get_user(request)
    design = Design.objects.create(
        creator=user,
        title=payload.title,
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        category=payload.category,
        width=payload.width,
        height=payload.height,
        tags=payload.tags,
        image_url=payload.image_url,
    )
    return design


@router.get('/{design_id}', response=DesignOut)
def get_design(request, design_id: int):
    """设计稿详情"""
    user = _get_user(request)
    design = Design.objects.filter(id=design_id, creator=user, is_active=True).first()
    if not design:
        from ninja.errors import HttpError
        raise HttpError(404, '设计稿不存在')
    return design


@router.patch('/{design_id}', response=DesignOut)
def update_design(request, design_id: int, payload: DesignUpdateIn):
    """更新设计稿"""
    user = _get_user(request)
    design = Design.objects.filter(id=design_id, creator=user, is_active=True).first()
    if not design:
        from ninja.errors import HttpError
        raise HttpError(404, '设计稿不存在')
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(design, key, value)
    design.save()
    return design


@router.delete('/{design_id}', response={204: None})
def delete_design(request, design_id: int):
    """删除设计稿（软删除）"""
    user = _get_user(request)
    design = Design.objects.filter(id=design_id, creator=user).first()
    if not design:
        from ninja.errors import HttpError
        raise HttpError(404, '设计稿不存在')
    design.is_active = False
    design.save()
    return 204, None


@router.post('/generate', response=GenerateOut)
def generate(request, payload: GenerateIn):
    """提交 AI 生成任务（后台执行，返回 task_id，前端轮询状态）"""
    from common import taskqueue

    user = _get_user(request)
    task_id = taskqueue.submit(
        generate_design_task,
        user_id=user.id,
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        category=payload.category,
        width=payload.width,
        height=payload.height,
        template=payload.template,
        title=payload.title,
    )
    return {'task_id': task_id, 'status': 'pending'}


@router.get('/tasks/{task_id}', response=TaskStatusOut)
def get_task_status(request, task_id: str):
    """查询生成任务状态"""
    from common import taskqueue

    user = _get_user(request)
    payload = taskqueue.get_status(task_id)
    status = payload.get('status') or 'PENDING'
    error = payload.get('error')

    design = None
    if status == 'SUCCESS':
        data = payload.get('result') or {}
        design_id = data.get('design_id') or (data.get('design') or {}).get('id')
        if design_id:
            design = Design.objects.filter(id=design_id, creator=user).first()
        if design is None:
            error = error or '任务已完成，但未找到生成结果'

    return {
        'task_id': task_id,
        'status': status,
        'result': design,
        'error': error,
    }


@router.get('/{design_id}/versions', response=List[DesignVersionOut])
def list_versions(request, design_id: int):
    """设计稿版本列表"""
    user = _get_user(request)
    design = Design.objects.filter(id=design_id, creator=user).first()
    if not design:
        from ninja.errors import HttpError
        raise HttpError(404, '设计稿不存在')
    return design.versions.all()
