from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = '用户扩展'
    verbose_name_plural = '用户扩展'


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'get_role', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role']

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = '角色'
    get_role.admin_order_field = 'profile__role'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
