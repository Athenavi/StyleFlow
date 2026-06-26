# Common models and mixins
from django.db import models


class TimestampMixin(models.Model):
    """自增时间戳 Mixin"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
