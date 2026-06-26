from django.db import models
from django.conf import settings

from common.crypto import encrypt_api_key, decrypt_api_key, mask_api_key


class UserAISetting(models.Model):
    """用户自定义 AI 模型配置（API Key 加密存储）"""
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
    )
    llm_model = models.CharField(
        max_length=100, default='gpt-4o',
    )
    image_provider = models.CharField(
        max_length=30, choices=IMAGE_PROVIDER_CHOICES, default='sd_webui',
    )
    image_model = models.CharField(
        max_length=100, default='sd-xl',
    )

    # 加密存储的 API Key（密文）
    llm_api_key_enc = models.TextField(blank=True, help_text='语言模型 API Key（加密）')
    image_api_key_enc = models.TextField(blank=True, help_text='图像模型 API Key（加密）')

    # 自定义 API 地址
    llm_api_base_url = models.CharField(max_length=500, blank=True, help_text='LLM API 地址，留空用默认')
    image_api_base_url = models.CharField(max_length=500, blank=True, help_text='图像API地址，留空用默认')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_ai_setting'
        verbose_name = '用户AI配置'
        verbose_name_plural = '用户AI配置'

    def __str__(self):
        return f'{self.user.username} - LLM:{self.llm_provider}'

    # ---- 明文读写 API Key（自动加解密） ----

    def set_llm_api_key(self, raw_key: str):
        """设置明文 LLM API Key（自动加密存储）"""
        pwd = self.user.password
        self.llm_api_key_enc = encrypt_api_key(raw_key, pwd)

    def get_llm_api_key(self) -> str:
        """获取明文 LLM API Key（自动解密）"""
        return decrypt_api_key(self.llm_api_key_enc, self.user.password)

    def set_image_api_key(self, raw_key: str):
        pwd = self.user.password
        self.image_api_key_enc = encrypt_api_key(raw_key, pwd)

    def get_image_api_key(self) -> str:
        return decrypt_api_key(self.image_api_key_enc, self.user.password)

    @property
    def llm_api_key_masked(self) -> str:
        return mask_api_key(self.get_llm_api_key()) if self.llm_api_key_enc else ''

    @property
    def image_api_key_masked(self) -> str:
        return mask_api_key(self.get_image_api_key()) if self.image_api_key_enc else ''
