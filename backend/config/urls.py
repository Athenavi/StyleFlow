from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve

from .api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
    # 媒体文件与静态资源：本地/局域网/单机部署由 Django 直接提供，
    # 前端通过同源代理 /media、/static 访问，因此无论用 localhost、局域网 IP
    # 还是域名打开页面，图片都能正常显示。
    # 若使用 Nginx/Caddy 等反向代理，可让代理直接接管这两个前缀以提升性能。
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
