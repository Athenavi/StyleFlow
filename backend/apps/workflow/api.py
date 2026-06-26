from typing import List, Optional
from ninja import Router, Schema
from django.db import models as db_models

from .models import WorkflowDefinition, WorkflowInstance, MAX_DEFINITIONS
from .schemas import WorkflowInstanceOut, ProceedIn
from .engine import WorkflowEngine
from apps.accounts.auth import get_user_from_token

router = Router(tags=['工作流'])


# --- 工作流定义 CRUD ---

class NodeDefIn(Schema):
    name: str
    label: str
    handler_role: List[str] = []
    auto_proceed: bool = False
    next: List[str] = []
    reject_to: Optional[str] = None


class DefOut(Schema):
    id: int
    name: str
    description: str
    initial: str
    nodes: list
    created_at: str = ''

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


class DefCreateIn(Schema):
    name: str
    description: str = ''
    initial: str = 'start'
    nodes: List[NodeDefIn] = []


def _get_user(request):
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')
    return user


@router.get('/definitions', response=List[DefOut])
def list_defs(request):
    """我的工作流定义列表"""
    user = _get_user(request)
    return WorkflowDefinition.objects.filter(user=user, is_active=True)


@router.post('/definitions', response=DefOut)
def create_def(request, payload: DefCreateIn):
    """创建工作流定义（最多10条）"""
    user = _get_user(request)
    count = WorkflowDefinition.objects.filter(user=user).count()
    if count >= MAX_DEFINITIONS:
        from ninja.errors import HttpError
        raise HttpError(400, f'最多创建 {MAX_DEFINITIONS} 条工作流')
    wd = WorkflowDefinition.objects.create(
        user=user, name=payload.name, description=payload.description,
        initial=payload.initial,
        nodes=[n.dict() for n in payload.nodes],
    )
    return wd


@router.get('/definitions/{def_id}', response=DefOut)
def get_def(request, def_id: int):
    return WorkflowDefinition.objects.get(id=def_id, is_active=True)


@router.put('/definitions/{def_id}', response=DefOut)
def update_def(request, def_id: int, payload: DefCreateIn):
    """更新工作流定义"""
    wd = WorkflowDefinition.objects.get(id=def_id)
    wd.name = payload.name
    wd.description = payload.description
    wd.initial = payload.initial
    wd.nodes = [n.dict() for n in payload.nodes]
    wd.save()
    return wd


@router.delete('/definitions/{def_id}', response={204: None})
def delete_def(request, def_id: int):
    wd = WorkflowDefinition.objects.get(id=def_id)
    wd.is_active = False
    wd.save()
    return 204, None


# --- 工作流实例 ---

class InstanceCreateIn(Schema):
    definition_id: int
    title: str
    object_id: int = 0
    data_snapshot: dict = {}


@router.get('', response=List[WorkflowInstanceOut])
def list_workflows(request, status: str = None):
    qs = WorkflowInstance.objects.all().select_related('assigned_to')
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@router.get('/enriched')
def list_enriched(request, status: str = None):
    """返回包含认领信息的实例列表"""
    user = _get_user(request)
    qs = WorkflowInstance.objects.all().select_related('assigned_to')
    if status:
        qs = qs.filter(status=status)
    result = []
    for inst in qs.order_by('-created_at'):
        result.append({
            'id': inst.id, 'title': inst.title,
            'workflow_type': inst.workflow_type, 'object_id': inst.object_id,
            'current_node': inst.current_node, 'status': inst.status,
            'created_at': inst.created_at.isoformat() if inst.created_at else '',
            'updated_at': inst.updated_at.isoformat() if inst.updated_at else '',
            'definition_id': inst.definition_id,
            'assigned_name': inst.assigned_to.username if inst.assigned_to else None,
            'is_mine': inst.assigned_to == user,
        })
    return result


@router.post('', response=WorkflowInstanceOut)
def create_workflow_instance(request, payload: InstanceCreateIn):
    """从定义创建工作流实例"""
    user = _get_user(request)
    inst = WorkflowEngine.create_instance(
        definition_id=payload.definition_id,
        object_id=payload.object_id,
        title=payload.title,
        created_by=user,
        data_snapshot=payload.data_snapshot,
    )
    return inst


@router.get('/todos')
def get_todos(request):
    user = _get_user(request)
    return {'todos': WorkflowEngine.get_user_todos(user)}


@router.post('/{instance_id}/claim')
def claim_task(request, instance_id: int):
    """认领当前节点任务（先到先得）"""
    user = _get_user(request)
    instance = WorkflowInstance.objects.get(id=instance_id)
    try:
        WorkflowEngine.claim(instance, user)
        return {'success': True, 'assigned_to': user.username}
    except ValueError as e:
        from ninja.errors import HttpError
        raise HttpError(400, str(e))


@router.get('/{instance_id}')
def get_workflow(request, instance_id: int):
    return WorkflowInstance.objects.prefetch_related('nodes').get(id=instance_id)


@router.post('/{instance_id}/proceed')
def proceed_workflow(request, instance_id: int, payload: ProceedIn):
    user = _get_user(request)
    instance = WorkflowInstance.objects.get(id=instance_id)
    try:
        WorkflowEngine.proceed(instance, user, action=payload.action, comment=payload.comment)
        return {'success': True, 'status': instance.status, 'current_node': instance.current_node}
    except ValueError as e:
        from ninja.errors import HttpError
        raise HttpError(400, str(e))
