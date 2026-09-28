from ninja import Router, Schema
from typing import List, Optional
from decimal import Decimal

from .models import CostingResult, ProcessTemplate
from apps.techpack.models import TechPack

router = Router(tags=['核工价'])


class CostingListOut(Schema):
    id: int
    techpack_id: int
    total_labor_cost: float
    total_material_cost: float
    approved: bool
    created_at: str = ''

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


@router.get('/list', response=List[CostingListOut])
def list_costings(request):
    return CostingResult.objects.all().order_by('-created_at')[:50]


class CostingOut(Schema):
    id: int
    techpack_id: int
    total_labor_cost: float
    total_material_cost: float
    process_breakdown: list
    approved: bool
    created_at: str

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''


@router.post('/calculate')
def calculate_costing(request, techpack_id: int):
    """自动核算工价"""
    from ninja.errors import HttpError

    tp = TechPack.objects.filter(id=techpack_id).first()
    if not tp:
        raise HttpError(404, '工艺单不存在')

    breakdown = []
    total_labor = Decimal('0.00')

    for step in tp.process_steps:
        process_name = step.get('process_name', '') if isinstance(step, dict) else step
        template = ProcessTemplate.objects.filter(
            process_name__icontains=process_name,
            is_active=True,
        ).first()
        if template:
            breakdown.append({
                'process_name': template.process_name,
                'standard_time': float(template.standard_time),
                'unit_cost': float(template.unit_cost),
            })
            total_labor += template.unit_cost

    result, _ = CostingResult.objects.update_or_create(
        techpack=tp,
        defaults={
            'total_labor_cost': total_labor,
            'process_breakdown': breakdown,
        }
    )
    return {
        'id': result.id,
        'total_labor_cost': float(total_labor),
        'process_breakdown': breakdown,
    }


# 注意：该「通配路径」必须放在 /list、/calculate 之后，否则会抢先匹配
@router.get('/{techpack_id}', response=CostingOut)
def get_costing(request, techpack_id: int):
    from ninja.errors import HttpError

    result = CostingResult.objects.filter(techpack_id=techpack_id).first()
    if not result:
        raise HttpError(404, '核算记录不存在')
    return result
