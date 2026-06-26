from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin

# 严格限制的上传类型
ALLOWED_MIME_TYPES = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
    'image/gif': 'gif',
}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class UserMedia(TimestampMixin):
    """用户媒体库素材"""
    CATEGORY_CHOICES = [
        ('model', '模特图'),
        ('garment', '服装图'),
        ('fabric', '面料图'),
        ('sketch', '设计稿'),
        ('moodboard', '灵感图'),
        ('other', '其他'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    title = models.CharField(max_length=200, blank=True)
    file_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True)
    file_type = models.CharField(max_length=20, choices=[
        ('jpg', 'JPEG'), ('png', 'PNG'), ('webp', 'WebP'), ('gif', 'GIF'),
    ])
    file_size = models.IntegerField(default=0, help_text='字节')
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'media_user_media'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'category']),
        ]
        verbose_name = '媒体素材'
        verbose_name_plural = '媒体素材'

    def __str__(self):
        return self.title or f'{self.file_type} #{self.id}'
