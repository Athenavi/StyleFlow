from ninja import Router, Schema
from typing import List, Optional

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
    created_at: str


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

@router.get('', response=List[WorkflowInstanceOut])
def list_workflows(request, status: str = None):
    qs = WorkflowInstance.objects.all()
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@router.get('/todos')
def get_todos(request):
    user = _get_user(request)
    return {'todos': WorkflowEngine.get_user_todos(user)}


@router.get('/{instance_id}')
def get_workflow(request, instance_id: int):
    return WorkflowInstance.objects.prefetch_related('nodes').get(id=instance_id)


@router.post('/{instance_id}/proceed')
def proceed_workflow(request, instance_id: int, payload: ProceedIn):
    user = _get_user(request)
    instance = WorkflowInstance.objects.get(id=instance_id)
    WorkflowEngine.proceed(instance, user, action=payload.action, comment=payload.comment)
    return {'success': True, 'status': instance.status, 'current_node': instance.current_node}
