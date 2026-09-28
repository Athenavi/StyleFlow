import os
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent      # backend/config
BACKEND_DIR = CONFIG_DIR.parent                          # backend/
PROJECT_ROOT = BACKEND_DIR.parent                        # 仓库根目录
# 兼容历史引用（早期代码里 BASE_DIR 指向 backend/config，例如 backend/config/media）
BASE_DIR = CONFIG_DIR


def _load_env_file(path: Path) -> None:
    """极简 .env 加载器（已存在的环境变量优先，不依赖第三方包）"""
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


# 项目根目录 .env 优先，其次 backend/.env
for _env_file in (PROJECT_ROOT / '.env', BACKEND_DIR / '.env'):
    _load_env_file(_env_file)

# ---------------- 目录布局 ----------------
# 所有运行期可变数据（数据库/媒体/静态/日志）集中到 DATA_DIR，便于备份迁移
DATA_DIR = Path(os.getenv('STYLEFLOW_DATA_DIR') or (PROJECT_ROOT / 'data'))
if not DATA_DIR.is_absolute():
    DATA_DIR = PROJECT_ROOT / DATA_DIR

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

# API Key 独立加密密钥（与 SECRET_KEY 不同，永不落库）
# 生成命令: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY_ENCRYPTION_KEY = os.getenv('API_KEY_ENCRYPTION_KEY', '')

# 文件存储后端: local | s3
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')
# 后端服务地址（用于生成文件访问 URL）。留空 = 返回同源相对路径 /media/...
# 前后端同源部署（一键脚本默认）时请留空，局域网/域名访问才能正常显示图片。
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', '').rstrip('/')

# 任务执行后端: thread（进程内线程池，无需 Redis）| celery（需 Redis）
TASK_BACKEND = os.getenv('TASK_BACKEND', 'celery').lower()
LOCAL_TASK_WORKERS = int(os.getenv('LOCAL_TASK_WORKERS', '2'))
# 数据库: sqlite（零配置，默认一键模式）| postgres
DATABASE_MODE = os.getenv('DATABASE_MODE', 'postgres').lower()

DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'corsheaders',
    'django_filters',
    # Local apps
    'apps.accounts',
    'apps.design',
    'apps.tryon',
    'apps.planning',
    'apps.techpack',
    'apps.workflow',
    'apps.costing',
    'apps.wages',
    'apps.erp',
    'apps.media',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

if DATABASE_MODE == 'sqlite':
    # 零配置模式：数据文件位于 DATA_DIR/styleflow.sqlite3
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv('SQLITE_PATH') or str(DATA_DIR / 'styleflow.sqlite3'),
            'ATOMIC_REQUESTS': True,
            'OPTIONS': {
                'timeout': 30,       # 并发写入时等待锁，避免 database is locked
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'styleflow'),
            'USER': os.getenv('DB_USER', 'styleflow'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'styleflow'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 600,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv('STATIC_ROOT') or (DATA_DIR / 'static'))
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT') or (DATA_DIR / 'media'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # Dev only

# Ninja
from datetime import timedelta
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Celery
if TASK_BACKEND == 'thread':
    # 本地模式：任务在进程内线程池执行，不需要 Redis / worker 进程
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = False
else:
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_ROUTES = {
    'apps.design.tasks.*': {'queue': 'ai_generation'},
    'apps.tryon.tasks.*': {'queue': 'ai_generation'},
    'apps.techpack.tasks.*': {'queue': 'llm_tasks'},
    'apps.erp.tasks.*': {'queue': 'sync'},
}

# MinIO / S3
AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
AWS_STORAGE_BUCKET_NAME = os.getenv('MINIO_BUCKET', 'styleflow')
AWS_S3_ENDPOINT_URL = os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_REGION_NAME = 'us-east-1'

# AI Services (configured per environment)
AI_SERVICES = {
    'llm': {
        'default': {
            'provider': 'openai',
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': 'gpt-4o',
        },
        'openai': {
            'provider': 'openai',
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': 'gpt-4o',
        },
        'claude': {
            'provider': 'claude',
            'api_key': os.getenv('CLAUDE_API_KEY', ''),
            'model': 'claude-sonnet-4-20250514',
        },
        'tongyi': {
            'provider': 'tongyi',
            'api_key': os.getenv('TONGYI_API_KEY', ''),
            'model': 'qwen-max',
        },
    },
    'image': {
        'default': {
            'provider': 'sd_webui',
            'base_url': os.getenv('SD_WEBUI_URL', 'http://localhost:7860'),
        },
        'tongyi': {
            'provider': 'tongyi_image',
            'api_key': os.getenv('TONGYI_API_KEY', ''),
            'model': 'wanx-v1',
        },
    },
}

# ERP config
ERP_CONFIG = {
    'mode': os.getenv('ERP_MODE', 'direct'),  # direct / api / file
    'configured': bool(os.getenv('ERP_DB_NAME')),
}

# ERP 直连数据库（可选）：仅在配置了 ERP_DB_NAME 时注册，未配置则 ERP 同步接口返回友好提示
if os.getenv('ERP_DB_NAME'):
    DATABASES['erp'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('ERP_DB_NAME'),
        'USER': os.getenv('ERP_DB_USER', ''),
        'PASSWORD': os.getenv('ERP_DB_PASSWORD', ''),
        'HOST': os.getenv('ERP_DB_HOST', 'localhost'),
        'PORT': os.getenv('ERP_DB_PORT', '5432'),
        'ATOMIC_REQUESTS': False,
    }

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
