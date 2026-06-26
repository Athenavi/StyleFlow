from .models import WorkflowDefinition, WorkflowInstance, WorkflowNode, MAX_DEFINITIONS


class WorkflowEngine:

    @staticmethod
    def load_definition(workflow_type_or_id) -> dict:
        if isinstance(workflow_type_or_id, int):
            wd = WorkflowDefinition.objects.get(id=workflow_type_or_id, is_active=True)
            return {'name': wd.name, 'initial': wd.initial, 'nodes': wd.nodes}
        import json; from pathlib import Path
        path = Path(__file__).parent / 'definitions' / f'{workflow_type_or_id}.json'
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        raise ValueError(f'定义 {workflow_type_or_id} 不存在')

    @staticmethod
    def _get_node(definition: dict, name: str) -> dict:
        for n in definition['nodes']:
            if n['name'] == name:
                return n
        raise ValueError(f'节点 {name} 不存在')

    @staticmethod
    def create_instance(definition_id: int, object_id: int, title: str, created_by,
                        data_snapshot: dict = None) -> WorkflowInstance:
        definition = WorkflowDefinition.objects.get(id=definition_id, is_active=True)
        wf_def = WorkflowEngine.load_definition(definition_id)
        inst = WorkflowInstance.objects.create(
            workflow_type='style_development', object_id=object_id, title=title,
            current_node=wf_def['initial'], created_by=created_by,
            data_snapshot=data_snapshot or {}, definition=definition,
        )
        inst.nodes.create(node_name=wf_def['initial'], action='start')
        return inst

    @staticmethod
    def claim(instance: WorkflowInstance, user) -> WorkflowInstance:
        """认领当前节点任务（同一角色多人时，先到先得）"""
        if instance.assigned_to and instance.assigned_to != user:
            raise ValueError(f'该任务已被 {instance.assigned_to.username} 认领')
        if instance.status != 'running':
            raise ValueError('该工作流已结束')
        instance.assigned_to = user
        instance.save(update_fields=['assigned_to'])
        return instance

    @staticmethod
    def proceed(instance: WorkflowInstance, user, action='approve', comment='') -> WorkflowInstance:
        def_id = instance.definition_id or instance.workflow_type
        definition = WorkflowEngine.load_definition(def_id)
        current = WorkflowEngine._get_node(definition, instance.current_node)

        # 检查认领
        if instance.assigned_to and instance.assigned_to != user:
            raise ValueError(f'该任务已被 {instance.assigned_to.username} 认领，需由TA处理')

        if action == 'reject':
            nxt = current.get('reject_to')
            if not nxt:
                raise ValueError('当前节点不支持驳回')
        elif action == 'approve':
            nxt_list = current.get('next', [])
            if not nxt_list:
                raise ValueError('已是终态')
            nxt = nxt_list[0]
        else:
            raise ValueError(f'不支持: {action}')

        instance.nodes.create(node_name=instance.current_node,
                              handler=user.get_full_name() or user.username,
                              action=action, comment=comment)

        next_def = WorkflowEngine._get_node(definition, nxt)
        instance.current_node = nxt
        instance.status = 'completed' if not next_def.get('next') else 'running'
        instance.assigned_to = None  # 进入下一节点，清除认领
        instance.save()
        return instance

    @staticmethod
    def get_user_todos(user) -> list:
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if not role:
            return []
        todos = []
        for inst in WorkflowInstance.objects.filter(status='running').select_related('definition', 'assigned_to'):
            try:
                def_id = inst.definition_id or inst.workflow_type
                definition = WorkflowEngine.load_definition(def_id)
                current = WorkflowEngine._get_node(definition, inst.current_node)
                if role in current.get('handler_role', []):
                    # 同一角色多人时，标注是否已被其他人认领
                    is_claimed_by_other = inst.assigned_to and inst.assigned_to != user
                    is_claimed_by_me = inst.assigned_to == user
                    todos.append({
                        'instance_id': inst.id, 'title': inst.title,
                        'node_label': current['label'],
                        'workflow_type': inst.get_workflow_type_display(),
                        'created_at': inst.created_at.isoformat(),
                        'assigned_to': inst.assigned_to.username if inst.assigned_to else None,
                        'assigned_name': inst.assigned_to.username if inst.assigned_to else None,
                        'claimable': not inst.assigned_to,
                        'is_mine': is_claimed_by_me,
                    })
            except (ValueError, FileNotFoundError):
                continue
        return todos
