from django.db import models
from django.conf import settings


class UserAISetting(models.Model):
    """用户自定义 AI 模型配置"""
    LLM_PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('claude', 'Anthropic Claude'),
        ('tongyi', '阿里云通义千问'),
    ]
    IMAGE_PROVIDER_CHOICES = [
        ('sd_webui', 'Stable Diffusion WebUI'),
        ('tongyi_image', '通义万相'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_setting',
    )
    llm_provider = models.CharField(
        max_length=30, choices=LLM_PROVIDER_CHOICES, default='openai',
        help_text='语言模型提供商',
    )
    llm_model = models.CharField(
        max_length=100, default='gpt-4o',
        help_text='语言模型名称',
    )
    image_provider = models.CharField(
        max_length=30, choices=IMAGE_PROVIDER_CHOICES, default='sd_webui',
        help_text='图像生成模型提供商',
    )
    image_model = models.CharField(
        max_length=100, default='sd-xl',
        help_text='图像模型名称',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_ai_setting'
        verbose_name = '用户AI配置'
        verbose_name_plural = '用户AI配置'

    def __str__(self):
        return f'{self.user.username} - LLM:{self.llm_provider}/{self.llm_model}'
