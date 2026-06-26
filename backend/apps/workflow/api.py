from ninja import Router
from typing import List
from django.db import models as db_models

from .models import WorkflowInstance
from .schemas import WorkflowInstanceOut, WorkflowDetailOut, ProceedIn
from .engine import WorkflowEngine

router = Router(tags=['工作流'])


@router.get('', response=List[WorkflowInstanceOut])
def list_workflows(request, status: str = None, workflow_type: str = None):
    """工作流实例列表"""
    qs = WorkflowInstance.objects.all()
    if status:
        qs = qs.filter(status=status)
    if workflow_type:
        qs = qs.filter(workflow_type=workflow_type)
    return qs.order_by('-created_at')


@router.get('/todos')
def get_todos(request):
    """获取当前用户的待办事项"""
    from apps.accounts.auth import get_user_from_token
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')
    return {'todos': WorkflowEngine.get_user_todos(user)}


@router.get('/{instance_id}', response=WorkflowDetailOut)
def get_workflow(request, instance_id: int):
    """工作流详情（含节点历史）"""
    return WorkflowInstance.objects.prefetch_related('nodes').get(id=instance_id)


@router.post('/{instance_id}/proceed')
def proceed_workflow(request, instance_id: int, payload: ProceedIn):
    """推进或驳回流程"""
    from apps.accounts.auth import get_user_from_token
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')

    instance = WorkflowInstance.objects.get(id=instance_id)
    WorkflowEngine.proceed(instance, user, action=payload.action, comment=payload.comment)
    return {'success': True, 'status': instance.status, 'current_node': instance.current_node}
