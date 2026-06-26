from django.db import models
from common.models import TimestampMixin


class ErpStyle(models.Model):
    """ERP 款式数据镜像"""
    style_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    season = models.CharField(max_length=50, blank=True)
    bom = models.JSONField(default=dict, blank=True)
    size_range = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, blank=True)
    last_synced_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'erp_style'
        verbose_name = 'ERP款式数据'
        verbose_name_plural = 'ERP款式数据'


class ErpProcess(models.Model):
    """ERP 工序标准数据"""
    process_code = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    standard_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    last_synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'erp_process'
        verbose_name = 'ERP工序数据'
        verbose_name_plural = 'ERP工序数据'
