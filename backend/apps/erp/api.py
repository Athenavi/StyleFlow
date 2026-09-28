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

    @staticmethod
    def resolve_last_synced_at(obj):
        return obj.last_synced_at.isoformat() if obj.last_synced_at else ''


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
    from ninja.errors import HttpError

    style = ErpStyle.objects.filter(style_code=code).first()
    if not style:
        raise HttpError(404, '款式不存在或尚未同步')
    return style


@router.get('/processes', response=List[ErpProcessOut])
def list_erp_processes(request, category: str = None):
    qs = ErpProcess.objects.all()
    if category:
        qs = qs.filter(category=category)
    return qs


@router.post('/sync')
def trigger_sync(request):
    """触发 ERP 数据同步"""
    from django.conf import settings as django_settings
    from ninja.errors import HttpError

    if not django_settings.ERP_CONFIG.get('configured'):
        raise HttpError(400, '未配置 ERP 数据库，请在 .env 中填写 ERP_DB_* 后重试')

    from .sync_engine import ErpDirectSync
    try:
        syncer = ErpDirectSync()
        syncer.sync_styles()
        syncer.sync_processes()
    except Exception as exc:
        raise HttpError(500, f'ERP 同步失败: {exc}')
    return {'success': True, 'message': '同步完成'}
