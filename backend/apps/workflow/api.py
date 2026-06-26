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


@router.delete('/definitions/{def_id}/hard', response={204: None})
def hard_delete_def(request, def_id: int):
    """永久删除工作流定义"""
    wd = WorkflowDefinition.objects.get(id=def_id)
    wd.delete()
    return 204, None


@router.post('/definitions/{def_id}/copy', response=DefOut)
def copy_def(request, def_id: int):
    """复制工作流定义"""
    user = _get_user(request)
    count = WorkflowDefinition.objects.filter(user=user).count()
    if count >= MAX_DEFINITIONS:
        from ninja.errors import HttpError
        raise HttpError(400, f'最多 {MAX_DEFINITIONS} 条，请先删除后再复制')
    original = WorkflowDefinition.objects.get(id=def_id)
    wd = WorkflowDefinition.objects.create(
        user=user, name=f'{original.name} (副本)',
        description=original.description,
        initial=original.initial, nodes=original.nodes,
    )
    return wd


# --- 内置模板 ---

BUILTIN_TEMPLATES = {
    '款式开发': {
        'initial': 'planning', 'description': '标准款式开发流程：企划→设计→评审→工艺→核价→审批→发布',
    },
    '物料审批': {
        'initial': 'apply',
        'description': '物料采购审批流程：申请→部门审核→财务核价→总经理审批→采购执行',
        'nodes': [
            {'name': 'apply', 'label': '采购申请', 'handler_role': ['designer'], 'auto_proceed': False, 'next': ['dept_review'], 'reject_to': ''},
            {'name': 'dept_review', 'label': '部门审核', 'handler_role': ['admin'], 'auto_proceed': False, 'next': ['finance'], 'reject_to': 'apply'},
            {'name': 'finance', 'label': '财务核价', 'handler_role': ['accountant'], 'auto_proceed': False, 'next': ['gm_approval'], 'reject_to': 'dept_review'},
            {'name': 'gm_approval', 'label': '总经理审批', 'handler_role': ['admin'], 'auto_proceed': False, 'next': ['purchase'], 'reject_to': 'finance'},
            {'name': 'purchase', 'label': '采购执行', 'handler_role': ['admin'], 'auto_proceed': False, 'next': ['done'], 'reject_to': ''},
            {'name': 'done', 'label': '已完成', 'handler_role': [], 'auto_proceed': False, 'next': []},
        ],
    },
    'AI辅助设计': {
        'initial': 'requirement',
        'description': 'AI辅助设计流程：需求→AI生成→设计师修改→AI质检→评审→发布（AI参与节点自动执行）',
        'nodes': [
            {'name': 'requirement', 'label': '需求录入', 'handler_role': ['designer'], 'auto_proceed': False, 'next': ['ai_generate'], 'reject_to': ''},
            {'name': 'ai_generate', 'label': 'AI生成初稿', 'handler_role': ['designer'], 'auto_proceed': True, 'next': ['designer_review'], 'reject_to': ''},
            {'name': 'designer_review', 'label': '设计师修改', 'handler_role': ['designer'], 'auto_proceed': False, 'next': ['ai_quality'], 'reject_to': 'ai_generate'},
            {'name': 'ai_quality', 'label': 'AI质量检测', 'handler_role': ['designer'], 'auto_proceed': True, 'next': ['approval'], 'reject_to': ''},
            {'name': 'approval', 'label': '最终审批', 'handler_role': ['admin'], 'auto_proceed': False, 'next': ['released'], 'reject_to': 'designer_review'},
            {'name': 'released', 'label': '已发布', 'handler_role': [], 'auto_proceed': False, 'next': []},
        ],
    },
}


@router.post('/builtin/{template_name}')
def install_builtin(request, template_name: str):
    """安装内置工作流模板"""
    user = _get_user(request)
    if template_name not in BUILTIN_TEMPLATES:
        from ninja.errors import HttpError
        raise HttpError(404, f'模板 {template_name} 不存在')
    tpl = BUILTIN_TEMPLATES[template_name]
    count = WorkflowDefinition.objects.filter(user=user).count()
    if count >= MAX_DEFINITIONS:
        from ninja.errors import HttpError
        raise HttpError(400, f'最多 {MAX_DEFINITIONS} 条')
    exists = WorkflowDefinition.objects.filter(user=user, name=template_name).exists()
    if exists:
        from ninja.errors import HttpError
        raise HttpError(400, '已安装该模板')
    wd = WorkflowDefinition.objects.create(
        user=user, name=template_name, description=tpl['description'],
        initial=tpl['initial'], nodes=tpl.get('nodes', []),
    )
    return wd


@router.get('/builtin', response=List[DefOut])
def list_builtin(request):
    """列出所有内置模板"""
    return [
        {'id': 0, 'name': k, 'description': v['description'],
         'initial': v['initial'],
         'nodes': v.get('nodes', []),
         'created_at': ''}
        for k, v in BUILTIN_TEMPLATES.items()
    ]


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
