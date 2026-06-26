from ninja import Schema
from typing import Optional, List
from datetime import datetime


class WorkflowInstanceOut(Schema):
    id: int
    workflow_type: str
    object_id: int
    title: str
    current_node: str
    status: str
    created_at: str = ''
    updated_at: str = ''
    definition_id: Optional[int] = None

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''

    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat() if obj.updated_at else ''


class WorkflowNodeOut(Schema):
    id: int
    node_name: str
    handler: str
    action: str
    comment: str
    created_at: str = ''

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


class WorkflowDetailOut(Schema):
    id: int
    workflow_type: str
    object_id: int
    title: str
    current_node: str
    status: str
    nodes: List[WorkflowNodeOut]
    created_at: str = ''

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


class ProceedIn(Schema):
    action: str = 'approve'
    comment: str = ''
