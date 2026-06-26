from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Profile
from .ai_settings import UserAISetting


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建 Profile 和 AI Settings"""
    if created:
        Profile.objects.get_or_create(user=instance)
        UserAISetting.objects.get_or_create(user=instance)
