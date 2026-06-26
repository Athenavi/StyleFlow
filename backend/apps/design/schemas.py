from ninja import Schema, ModelSchema
from typing import Optional, List
from datetime import datetime

from .models import Design


class DesignOut(ModelSchema):
    created_at: str
    updated_at: str

    class Meta:
        model = Design
        fields = ['id', 'title', 'prompt', 'category', 'image_url',
                  'thumbnail_url', 'width', 'height', 'tags', 'status', 'is_active']

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat() if obj.created_at else ''

    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat() if obj.updated_at else ''


class DesignCreateIn(Schema):
    title: str = ''
    prompt: str
    negative_prompt: str = ''
    category: str = 'style'
    width: int = 512
    height: int = 768
    tags: List[str] = []


class DesignUpdateIn(Schema):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class GenerateIn(Schema):
    prompt: str
    negative_prompt: str = ''
    category: str = 'style'
    width: int = 512
    height: int = 768
    template: str = 'style'
    title: str = ''


class GenerateOut(Schema):
    task_id: str
    status: str = 'pending'


class TaskStatusOut(Schema):
    task_id: str
    status: str
    result: Optional[DesignOut] = None
    error: Optional[str] = None


class DesignVersionOut(Schema):
    id: int
    version_number: int
    image_url: str
    prompt: str
    change_note: str
    created_at: str
