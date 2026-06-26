from ninja import Router, Schema
from typing import Optional, List

from .models import TryOnTask
from apps.accounts.auth import get_user_from_token

router = Router(tags=['虚拟试衣'])


class TryOnTaskOut(Schema):
    id: int
    title: str
    person_image_url: str
    garment_image_url: str
    garment_category: str
    result_image_url: Optional[str] = None
    status: str
    error_message: str = ''
    created_at: str


class TryOnCreateIn(Schema):
    title: str = ''
    person_image_url: str
    garment_image_url: str
    garment_category: str = 'upper'


class TryOnTaskIdOut(Schema):
    task_id: str
    status: str = 'pending'


def _get_user(request):
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    user = get_user_from_token(token)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, '未认证')
    return user


@router.get('/tasks', response=List[TryOnTaskOut])
def list_tasks(request, status: str = None):
    """我的试衣任务列表"""
    user = _get_user(request)
    qs = TryOnTask.objects.filter(user=user)
    if status:
        qs = qs.filter(status=status)
    return qs


@router.post('/tasks', response=TryOnTaskIdOut)
def create_task(request, payload: TryOnCreateIn):
    """提交试衣任务"""
    user = _get_user(request)

    from .tasks import run_tryon_task
    task = run_tryon_task.delay(
        user_id=user.id,
        person_image_url=payload.person_image_url,
        garment_image_url=payload.garment_image_url,
        category=payload.garment_category,
        title=payload.title,
    )

    TryOnTask.objects.create(
        user=user,
        title=payload.title or f'试衣 #{task.id[:8]}',
        person_image_url=payload.person_image_url,
        garment_image_url=payload.garment_image_url,
        garment_category=payload.garment_category,
        task_id=task.id,
        status='processing',
    )

    return {'task_id': task.id, 'status': 'processing'}


@router.get('/tasks/{task_id}', response=TryOnTaskOut)
def get_task(request, task_id: int):
    """查询任务详情"""
    user = _get_user(request)
    return TryOnTask.objects.get(id=task_id, user=user)
