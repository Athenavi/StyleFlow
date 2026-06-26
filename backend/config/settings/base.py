import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

# API Key 独立加密密钥（与 SECRET_KEY 不同，永不落库）
# 生成命令: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY_ENCRYPTION_KEY = os.getenv('API_KEY_ENCRYPTION_KEY', '')

# 文件存储后端: local | s3
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')
# 后端服务地址（用于生成文件访问 URL）
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')

DEBUG = True

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

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
