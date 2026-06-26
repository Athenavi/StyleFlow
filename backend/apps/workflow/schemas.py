from ninja import Schema
from typing import Optional, List


class WorkflowInstanceOut(Schema):
    id: int
    workflow_type: str
    object_id: int
    title: str
    current_node: str
    status: str
    created_at: str
    updated_at: str
    definition_id: Optional[int] = None


class WorkflowNodeOut(Schema):
    id: int
    node_name: str
    handler: str
    action: str
    comment: str
    created_at: str


class WorkflowDetailOut(Schema):
    id: int
    workflow_type: str
    object_id: int
    title: str
    current_node: str
    status: str
    nodes: List[WorkflowNodeOut]
    created_at: str


class ProceedIn(Schema):
    action: str = 'approve'
    comment: str = ''
