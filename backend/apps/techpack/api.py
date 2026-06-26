from ninja import Router, Schema
from typing import Optional, List
from django.db import models

from .models import TechPack

router = Router(tags=['工艺单'])


class TechPackOut(Schema):
    id: int
    title: str
    style_code: str
    category: str
    design_id: Optional[int] = None
    fabric_description: str
    size_spec: dict
    process_steps: list
    status: str
    created_at: str
    updated_at: str


class TechPackCreateIn(Schema):
    title: str
    style_code: str = ''
    category: str = ''
    design_id: Optional[int] = None
    fabric_description: str = ''
    size_spec: dict = {}
    process_steps: list = []


@router.get('', response=List[TechPackOut])
def list_techpacks(request, status: str = None):
    qs = TechPack.objects.all()
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@router.get('/{tp_id}', response=TechPackOut)
def get_techpack(request, tp_id: int):
    return TechPack.objects.get(id=tp_id)


@router.post('', response=TechPackOut)
def create_techpack(request, payload: TechPackCreateIn):
    from apps.accounts.auth import get_user_from_token
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    tp = TechPack.objects.create(created_by=user, **payload.dict())
    return tp


@router.post('/generate')
def generate_techpack(request, design_id: int):
    """AI 自动生成工艺单"""
    from apps.design.models import Design
    from common.aiservice.factory import get_llm_service
    from apps.costing.models import ProcessTemplate

    design = Design.objects.get(id=design_id)

    llm = get_llm_service('default')
    schema = {
        "type": "object",
        "properties": {
            "collar_type": {"type": "string"},
            "sleeve_type": {"type": "string"},
            "length": {"type": "string"},
            "fabric_recommendation": {"type": "string"},
            "process_notes": {"type": "string"},
        },
    }
    result = llm.extract_json(
        f"根据以下设计描述提取服装工艺参数：\nPrompt: {design.prompt}\n分类: {design.get_category_display()}",
        schema=schema,
    )

    processes = ProcessTemplate.objects.filter(
        category=design.category, is_active=True
    ).values('process_name', 'standard_time', 'unit_cost')

    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    from apps.accounts.auth import get_user_from_token
    user = get_user_from_token(token)

    tp = TechPack.objects.create(
        design=design,
        title=f"{design.title or '设计稿'} 工艺单",
        category=design.category,
        fabric_description=result.get('fabric_recommendation', ''),
        process_steps=list(processes),
        created_by=user,
    )
    return {'id': tp.id, 'title': tp.title, 'status': tp.status}
