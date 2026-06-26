from ninja import Router, Schema
from typing import List, Optional
from django.db import models as db_models
from .models import ErpStyle, ErpProcess

router = Router(tags=['ERP对接'])


class ErpStyleOut(Schema):
    style_code: str
    description: str
    category: str
    season: str
    status: str
    last_synced_at: str


class ErpProcessOut(Schema):
    process_code: str
    process_name: str
    category: str
    standard_time: Optional[float] = None
    unit_cost: Optional[float] = None


@router.get('/styles', response=List[ErpStyleOut])
def list_erp_styles(request, category: str = None, search: str = None):
    qs = ErpStyle.objects.all()
    if category:
        qs = qs.filter(category=category)
    if search:
        qs = qs.filter(db_models.Q(style_code__icontains=search) | db_models.Q(description__icontains=search))
    return qs.order_by('-last_synced_at')[:50]


@router.get('/styles/{code}', response=ErpStyleOut)
def get_erp_style(request, code: str):
    return ErpStyle.objects.get(style_code=code)


@router.get('/processes', response=List[ErpProcessOut])
def list_erp_processes(request, category: str = None):
    qs = ErpProcess.objects.all()
    if category:
        qs = qs.filter(category=category)
    return qs


@router.post('/sync')
def trigger_sync(request):
    """触发 ERP 数据同步"""
    from .sync_engine import ErpDirectSync
    syncer = ErpDirectSync()
    syncer.sync_styles()
    syncer.sync_processes()
    return {'success': True, 'message': '同步完成'}
