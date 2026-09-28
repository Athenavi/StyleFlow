"""任务执行桥接层

API 层统一调用 submit() / get_status()，底层支持两种执行后端：

- thread（默认，本地一键模式）：进程内线程池执行，不需要 Redis、不需要独立 worker
  进程。提交后立即返回 task_id，任务在后台线程运行，前端轮询状态即可，页面不会卡住。
- celery（可选，多机 / 高并发）：交给 Celery 处理，需要 Redis 与 worker 进程。

线程模式内部使用 celery 的 ``task.apply(task_id=...)`` 执行，因此任务函数里的
``self.request.id`` 依然等于 submit() 返回的 task_id（例如 TryOnTask.task_id 的匹配
逻辑无需改动）。
"""
import logging
import threading
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings

logger = logging.getLogger(__name__)

# 线程模式的运行状态（仅保存在内存中，容量有限避免长跑进程内存增长）
_MAX_LOCAL_TASKS = 500
_states: "OrderedDict[str, dict]" = OrderedDict()
_lock = threading.Lock()
_executor = None


def backend() -> str:
    """当前任务执行后端: thread | celery"""
    return str(getattr(settings, 'TASK_BACKEND', 'celery')).lower()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        workers = int(getattr(settings, 'LOCAL_TASK_WORKERS', 2) or 2)
        _executor = ThreadPoolExecutor(
            max_workers=max(1, workers), thread_name_prefix='styleflow-task'
        )
        logger.info('本地任务线程池已创建，并发: %s', max(1, workers))
    return _executor


def _set(task_id: str, **state) -> None:
    with _lock:
        current = _states.get(task_id) or {}
        current.update(state)
        _states[task_id] = current
        while len(_states) > _MAX_LOCAL_TASKS:
            _states.popitem(last=False)


def _run(task, task_id: str, kwargs: dict) -> None:
    from django.db import connections

    _set(task_id, status='STARTED')
    try:
        result = task.apply(kwargs=kwargs, task_id=task_id)
        if result.successful():
            _set(task_id, status='SUCCESS', result=result.result, error=None)
        else:
            _set(task_id, status='FAILURE', result=None, error=str(result.result))
    except Exception as exc:  # 任务内部异常不应影响其他任务/请求
        logger.exception('后台任务 %s 执行失败', task_id)
        _set(task_id, status='FAILURE', result=None, error=str(exc))
    finally:
        try:  # 线程内新建的数据库连接需要显式关闭，否则会泄漏
            connections.close_all()
        except Exception:
            pass


def submit(task, task_id: str = None, **kwargs) -> str:
    """提交任务并返回 task_id

    task_id 可由调用方预先指定（例如需要先把记录写库再执行任务，避免竞态）。
    """
    task_id = task_id or uuid.uuid4().hex

    if backend() == 'celery':
        task.apply_async(kwargs=kwargs, task_id=task_id)
        return task_id

    _set(task_id, status='PENDING', result=None, error=None)
    _get_executor().submit(_run, task, task_id, kwargs)
    return task_id


def get_status(task_id: str) -> dict:
    """查询任务状态: {'status': ..., 'result': ..., 'error': ...}"""
    if backend() != 'celery':
        with _lock:
            state = _states.get(task_id)
        if state:
            return {
                'status': state.get('status', 'PENDING'),
                'result': state.get('result'),
                'error': state.get('error'),
            }
        # 线程模式状态下不落库，服务重启后历史任务无法查询
        return {'status': 'UNKNOWN', 'result': None, 'error': None}

    from celery.result import AsyncResult
    from config.celery_app import app as celery_app

    result = AsyncResult(task_id, app=celery_app)
    error = None
    payload = None
    if result.successful():
        payload = result.result or {}
    elif result.failed():
        error = str(result.info) if result.info else '任务失败'
    return {'status': result.status, 'result': payload, 'error': error}
