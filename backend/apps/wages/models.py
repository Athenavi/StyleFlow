from django.db import models


class WageRecord(models.Model):
    """计件工资记录"""
    worker_id = models.CharField(max_length=50, db_index=True)
    worker_name = models.CharField(max_length=100)
    date = models.DateField(db_index=True)
    style_code = models.CharField(max_length=50, blank=True)
    process_name = models.CharField(max_length=100)
    quantity = models.IntegerField(help_text='完成数量')
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, help_text='单价')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='合计')
    source = models.CharField(max_length=20, default='manual')

    class Meta:
        db_table = 'wages_record'
        ordering = ['-date', 'worker_id']
        indexes = [models.Index(fields=['worker_id', 'date'])]
        verbose_name = '工资记录'
        verbose_name_plural = '工资记录'
