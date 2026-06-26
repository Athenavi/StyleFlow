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

router = Router(tags=['设计工坊'])


@router.get('', response=List[DesignOut])
@paginate(PageNumberPagination, page_size=20)
def list_designs(request,
                 category: Optional[str] = None,
                 status: Optional[str] = None,
                 search: Optional[str] = None):
    """设计稿列表（分页+筛选）"""
    qs = Design.objects.filter(creator=request.user, is_active=True)
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
    design = Design.objects.create(
        creator=request.user,
        title=payload.title,
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        category=payload.category,
        width=payload.width,
        height=payload.height,
        tags=payload.tags,
    )
    return design


@router.get('/{design_id}', response=DesignOut)
def get_design(request, design_id: int):
    """设计稿详情"""
    return Design.objects.get(id=design_id, creator=request.user, is_active=True)


@router.patch('/{design_id}', response=DesignOut)
def update_design(request, design_id: int, payload: DesignUpdateIn):
    """更新设计稿"""
    design = Design.objects.get(id=design_id, creator=request.user, is_active=True)
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(design, key, value)
    design.save()
    return design


@router.delete('/{design_id}', response={204: None})
def delete_design(request, design_id: int):
    """删除设计稿（软删除）"""
    design = Design.objects.get(id=design_id, creator=request.user)
    design.is_active = False
    design.save()
    return 204, None


@router.post('/generate', response=GenerateOut)
def generate(request, payload: GenerateIn):
    """提交 AI 生成任务"""
    from apps.accounts.auth import get_user_from_token

    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')

    task = generate_design_task.delay(
        user_id=user.id,
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        category=payload.category,
        width=payload.width,
        height=payload.height,
        template=payload.template,
        title=payload.title,
    )
    return {'task_id': task.id, 'status': 'pending'}


@router.get('/tasks/{task_id}', response=TaskStatusOut)
def get_task_status(request, task_id: str):
    """查询生成任务状态"""
    from celery.result import AsyncResult
    from config.celery_app import app

    result = AsyncResult(task_id, app=app)
    task_result = {}
    error = None

    if result.successful():
        task_result = result.result or {}
    elif result.failed():
        error = str(result.info) if result.info else '任务失败'

    return {
        'task_id': task_id,
        'status': result.status,
        'result': task_result.get('design'),
        'error': error,
    }


@router.get('/{design_id}/versions', response=List[DesignVersionOut])
def list_versions(request, design_id: int):
    """设计稿版本列表"""
    design = Design.objects.get(id=design_id, creator=request.user)
    return design.versions.all()
