from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin


class Design(TimestampMixin):
    """AI 设计稿"""
    CATEGORY_CHOICES = [
        ('sketch', '线稿'),
        ('style', '款式图'),
        ('fabric', '面料图'),
        ('moodboard', '灵感板'),
        ('flatten', '平铺图'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('completed', '已完成'),
        ('archived', '已归档'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')
    title = models.CharField(max_length=200, blank=True)
    prompt = models.TextField(blank=True, help_text='AI 生成提示词')
    negative_prompt = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='style')
    image_url = models.URLField(max_length=500, blank=True, help_text='最终图片URL')
    thumbnail_url = models.URLField(max_length=500, blank=True)
    width = models.IntegerField(default=512)
    height = models.IntegerField(default=768)
    tags = models.JSONField(default=list, blank=True, help_text='标签数组')
    metadata = models.JSONField(default=dict, blank=True, help_text='AI生成参数等扩展信息')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'design_design'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['category']),
        ]
        verbose_name = '设计稿'
        verbose_name_plural = '设计稿'

    def __str__(self):
        return self.title or f'设计稿 #{self.id}'


class DesignVersion(TimestampMixin):
    """设计稿版本"""
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    image_url = models.URLField(max_length=500)
    prompt = models.TextField(blank=True)
    change_note = models.TextField(blank=True)

    class Meta:
        db_table = 'design_version'
        unique_together = ['design', 'version_number']
        ordering = ['-version_number']
        verbose_name = '设计稿版本'
        verbose_name_plural = '设计稿版本'
