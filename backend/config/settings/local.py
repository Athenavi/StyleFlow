"""本地一键运行配置（默认零外部依赖）

- 数据库:  SQLite（DATABASE_MODE=sqlite），可改为 postgres 沿用原数据库
- 任务队列: 进程内线程池（TASK_BACKEND=thread），无需 Redis / celery worker
- 文件存储: 本地磁盘（STORAGE_BACKEND=local），URL 使用同源相对路径 /media/...
- 访问方式: 本机 / 局域网直接可用（Host 不限制）；公网请配合反向代理

该模块只负责设定「零配置默认值」，随后继承 base.py 的完整配置。
显式设置的环境变量（或根目录 .env）始终优先。
"""
import os

# 必须在导入 base 之前完成默认值注入（setdefault：用户显式设置的值不会被覆盖）
os.environ.setdefault('DATABASE_MODE', 'sqlite')
os.environ.setdefault('TASK_BACKEND', 'thread')
os.environ.setdefault('STORAGE_BACKEND', 'local')
os.environ.setdefault('DJANGO_DEBUG', 'true')

from .base import *  # noqa: E402,F401,F403

# 本地模式自动准备数据目录（数据库/媒体/静态资源），避免"首次运行目录不存在"
for _path in (DATA_DIR, DATA_DIR / 'media', DATA_DIR / 'static'):  # noqa: F405
    try:
        _path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')

# 局域网 IP、域名、localhost 都可能访问，Host 默认不做限制；
# 公网部署时可在 .env 中显式限制，例如 ALLOWED_HOSTS=styleflow.example.com,127.0.0.1
_allowed_hosts = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
ALLOWED_HOSTS = _allowed_hosts or ['*']

# 前端已通过同源反向代理调用后端，这里放开 CORS 只是为了避免直连后端时被拦
CORS_ALLOW_ALL_ORIGINS = True

# 使用域名 / HTTPS 反向代理时，在 .env 中填写，例如：
#   CSRF_TRUSTED_ORIGINS=https://styleflow.example.com
_csrf_origins = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = _csrf_origins

# 反向代理终止 HTTPS 时，让 Django 识别真实协议与 Host
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', 'true').lower() in ('1', 'true', 'yes', 'on')


def _flag(name: str) -> bool:
    return os.getenv(name, 'false').lower() in ('1', 'true', 'yes', 'on')


# 本地/局域网默认关闭 HTTPS 强制跳转，公网部署时在 .env 中打开
SECURE_SSL_REDIRECT = _flag('SECURE_SSL_REDIRECT')
SESSION_COOKIE_SECURE = _flag('SESSION_COOKIE_SECURE')
CSRF_COOKIE_SECURE = _flag('CSRF_COOKIE_SECURE')

# 日志级别（本地排查问题时可设 DEBUG）
LOGGING['root']['level'] = os.getenv('LOG_LEVEL', 'INFO')  # noqa: F405
