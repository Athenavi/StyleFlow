from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """用户扩展信息"""
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('designer', '设计师'),
        ('pattern_maker', '版师'),
        ('accountant', '财务'),
        ('erp_sync', 'ERP同步账号'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='designer')
    avatar = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    erp_user_id = models.CharField(max_length=50, blank=True, help_text='ERP系统用户ID')
    storage_uuid = models.CharField(max_length=16, blank=True, help_text='用户文件存储目录UUID')

    class Meta:
        db_table = 'accounts_profile'
        verbose_name = '用户扩展'
        verbose_name_plural = '用户扩展'

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
