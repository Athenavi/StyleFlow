from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin


class TryOnTask(TimestampMixin):
    """虚拟试衣任务"""
    CATEGORY_CHOICES = [
        ('upper', '上装'),
        ('lower', '下装'),
        ('dress', '连衣裙'),
        ('outer', '外套'),
    ]
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tryon_tasks')
    title = models.CharField(max_length=200, blank=True)
    person_image_url = models.URLField(max_length=500, help_text='人物照片URL')
    garment_image_url = models.URLField(max_length=500, help_text='服装图片URL')
    garment_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='upper')
    result_image_url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    task_id = models.CharField(max_length=100, blank=True, help_text='Celery task ID')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tryon_task'
        ordering = ['-created_at']
        verbose_name = '试衣任务'
        verbose_name_plural = '试衣任务'
