from django.db import models
from common.models import TimestampMixin


class ProcessTemplate(models.Model):
    """工序模板（预置行业标准工序）"""
    category = models.CharField(max_length=50, db_index=True)
    process_name = models.CharField(max_length=100)
    standard_time = models.DecimalField(max_digits=6, decimal_places=2, help_text='标准工时(分钟)')
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, help_text='单件工费')
    sequence = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'costing_process_template'
        ordering = ['category', 'sequence']
        verbose_name = '工序模板'
        verbose_name_plural = '工序模板'


class CostingResult(TimestampMixin):
    """核价结果"""
    techpack = models.ForeignKey('techpack.TechPack', on_delete=models.CASCADE, related_name='costings')
    total_labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    process_breakdown = models.JSONField(default=list)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'costing_result'
        verbose_name = '核价结果'
        verbose_name_plural = '核价结果'
