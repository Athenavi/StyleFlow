import json
from pathlib import Path
from typing import Optional
from django.db import transaction

from .models import WorkflowInstance, WorkflowNode


class WorkflowEngine:
    """轻量级工作流引擎"""

    _definitions: dict = {}

    @classmethod
    def load_definition(cls, workflow_type: str) -> dict:
        """加载流程定义"""
        if workflow_type not in cls._definitions:
            path = Path(__file__).parent / 'definitions' / f'{workflow_type}.json'
            if not path.exists():
                raise ValueError(f"流程定义 {workflow_type} 不存在")
            with open(path, encoding='utf-8') as f:
                cls._definitions[workflow_type] = json.load(f)
        return cls._definitions[workflow_type]

    @classmethod
    def get_node_def(cls, definition: dict, node_name: str) -> dict:
        for node in definition['nodes']:
            if node['name'] == node_name:
                return node
        raise ValueError(f"节点 {node_name} 不存在")

    @classmethod
    @transaction.atomic
    def create_instance(cls, workflow_type: str, object_id: int,
                         title: str, created_by, data_snapshot: dict = None) -> WorkflowInstance:
        definition = cls.load_definition(workflow_type)
        instance = WorkflowInstance.objects.create(
            workflow_type=workflow_type,
            object_id=object_id,
            title=title,
            current_node=definition['initial'],
            created_by=created_by,
            data_snapshot=data_snapshot or {},
        )
        instance.nodes.create(node_name=definition['initial'], action='start')
        return instance

    @classmethod
    @transaction.atomic
    def proceed(cls, instance: WorkflowInstance, user, action: str = 'approve',
                 comment: str = '') -> WorkflowInstance:
        definition = cls.load_definition(instance.workflow_type)
        current_def = cls.get_node_def(definition, instance.current_node)

        if action == 'reject':
            reject_to = current_def.get('reject_to')
            if not reject_to:
                raise ValueError("当前节点不支持驳回")
            next_node = reject_to
        elif action == 'approve':
            next_nodes = current_def.get('next', [])
            if not next_nodes:
                raise ValueError("当前已是终态")
            next_node = next_nodes[0]
        else:
            raise ValueError(f"不支持的操作: {action}")

        instance.nodes.create(
            node_name=instance.current_node,
            handler=f"{user.get_full_name() or user.username}",
            action=action,
            comment=comment,
        )

        next_def = cls.get_node_def(definition, next_node)
        is_terminal = not next_def.get('next')
        instance.current_node = next_node
        instance.status = 'completed' if is_terminal else 'running'
        instance.save()

        if is_terminal:
            cls._on_completed(instance)

        return instance

    @classmethod
    def _on_completed(cls, instance: WorkflowInstance):
        """流程完成回调"""
        pass  # 后续可扩展：回写ERP、发送通知等

    @classmethod
    def get_user_todos(cls, user) -> list:
        """获取用户的待办事项"""
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if not role:
            return []

        todos = []
        for inst in WorkflowInstance.objects.filter(status='running'):
            try:
                definition = cls.load_definition(inst.workflow_type)
                current_def = cls.get_node_def(definition, inst.current_node)
                if role in current_def.get('handler_role', []):
                    todos.append({
                        'instance_id': inst.id,
                        'title': inst.title,
                        'node_label': current_def['label'],
                        'workflow_type': inst.get_workflow_type_display(),
                        'created_at': inst.created_at.isoformat(),
                    })
            except (ValueError, FileNotFoundError):
                continue
        return todos
