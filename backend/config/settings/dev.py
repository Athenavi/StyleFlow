from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ['django_extensions']  # noqa

CORS_ALLOW_ALL_ORIGINS = True

DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'  # noqa

# Print SQL queries in shell
LOGGING['root']['level'] = 'DEBUG'  # noqa
