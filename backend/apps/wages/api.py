from ninja import Router, Schema
from typing import List, Optional
from datetime import date
from django.db.models import Sum, Count
from decimal import Decimal

from .models import WageRecord

router = Router(tags=['计件工资'])


class WageOut(Schema):
    id: int
    worker_id: str
    worker_name: str
    date: str
    style_code: str
    process_name: str
    quantity: int
    unit_price: float
    total_amount: float


class WageSummaryOut(Schema):
    total_workers: int
    total_amount: float
    total_quantity: int
    records: int


@router.get('/records', response=List[WageOut])
def list_wages(request, worker_id: str = None, date_from: str = None, date_to: str = None):
    qs = WageRecord.objects.all()
    if worker_id:
        qs = qs.filter(worker_id=worker_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    return qs[:100]


@router.get('/summary')
def wage_summary(request, date_from: str = None, date_to: str = None):
    qs = WageRecord.objects.all()
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    agg = qs.aggregate(
        total=Sum('total_amount'),
        qty=Sum('quantity'),
        cnt=Count('id'),
        workers=Count('worker_id', distinct=True),
    )
    return {
        'total_workers': agg['workers'] or 0,
        'total_amount': float(agg['total'] or 0),
        'total_quantity': agg['qty'] or 0,
        'records': agg['cnt'] or 0,
    }
