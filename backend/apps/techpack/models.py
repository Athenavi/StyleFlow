from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin


class TechPack(TimestampMixin):
    """工艺单"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('review', '审核中'),
        ('approved', '已批准'),
    ]

    title = models.CharField(max_length=200)
    style_code = models.CharField(max_length=50, blank=True, help_text='款号')
    category = models.CharField(max_length=50, blank=True, help_text='品类')
    design = models.ForeignKey('design.Design', on_delete=models.SET_NULL, null=True, blank=True)
    fabric_description = models.TextField(blank=True, help_text='面料说明')
    size_spec = models.JSONField(default=dict, blank=True, help_text='尺码规格表')
    process_steps = models.JSONField(default=list, blank=True, help_text='工序步骤列表')
    tech_drawing_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'techpack_techpack'
        ordering = ['-created_at']
        verbose_name = '工艺单'
        verbose_name_plural = '工艺单'
