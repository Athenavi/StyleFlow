from .models import WorkflowDefinition, WorkflowInstance, WorkflowNode, MAX_DEFINITIONS


class WorkflowEngine:
    """轻量级工作流引擎（支持 DB 和 JSON 双源）"""

    @staticmethod
    def load_definition(workflow_type_or_id) -> dict:
        """加载定义：优先 DB (int id)，后备 JSON 文件"""
        if isinstance(workflow_type_or_id, int):
            try:
                wd = WorkflowDefinition.objects.get(id=workflow_type_or_id, is_active=True)
                return {'name': wd.name, 'initial': wd.initial, 'nodes': wd.nodes}
            except WorkflowDefinition.DoesNotExist:
                raise ValueError(f'工作流定义 #{workflow_type_or_id} 不存在')

        # JSON 文件兜底
        import json
        from pathlib import Path
        path = Path(__file__).parent / 'definitions' / f'{workflow_type_or_id}.json'
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        raise ValueError(f'工作流定义 {workflow_type_or_id} 不存在')

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
            workflow_type='style_development',
            object_id=object_id, title=title, current_node=wf_def['initial'],
            created_by=created_by, data_snapshot=data_snapshot or {},
            definition=definition,
        )
        inst.nodes.create(node_name=wf_def['initial'], action='start')
        return inst

    @staticmethod
    def proceed(instance: WorkflowInstance, user, action='approve', comment='') -> WorkflowInstance:
        def_id = instance.definition_id or instance.workflow_type
        definition = WorkflowEngine.load_definition(def_id)
        current = WorkflowEngine._get_node(definition, instance.current_node)

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
        instance.save()
        return instance

    @staticmethod
    def get_user_todos(user) -> list:
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if not role:
            return []
        todos = []
        for inst in WorkflowInstance.objects.filter(status='running').select_related('definition'):
            try:
                def_id = inst.definition_id or inst.workflow_type
                definition = WorkflowEngine.load_definition(def_id)
                current = WorkflowEngine._get_node(definition, inst.current_node)
                if role in current.get('handler_role', []):
                    todos.append({
                        'instance_id': inst.id, 'title': inst.title,
                        'node_label': current['label'],
                        'workflow_type': inst.get_workflow_type_display(),
                        'created_at': inst.created_at.isoformat(),
                    })
            except (ValueError, FileNotFoundError):
                continue
        return todos
