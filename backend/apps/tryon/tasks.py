import logging
from celery import shared_task

from .models import TryOnTask

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30,
             queue='ai_generation', soft_time_limit=180)
def run_tryon_task(self, user_id: int, person_image_url: str,
                    garment_image_url: str, category: str = 'upper',
                    title: str = ''):
    """执行虚拟试衣（调用 VTON 模型或模拟）"""
    import time
    start = time.time()

    try:
        # TODO: 对接真实 VTON 模型 (IDM-VTON / OOTDiffusion)
        # 目前用模拟数据
        time.sleep(3)  # 模拟处理耗时

        # 模拟结果图片（实际应该调用 VTON API）
        result_url = person_image_url  # 模拟：实际应返回合成图

        # 更新数据库
        task_record = TryOnTask.objects.filter(task_id=self.request.id).first()
        if task_record:
            task_record.status = 'completed'
            task_record.result_image_url = result_url
            task_record.metadata = {
                'latency_ms': int((time.time() - start) * 1000),
                'model': 'idm-vton',
            }
            task_record.save()

            # 自动保存到媒体库
            from apps.media.models import UserMedia
            UserMedia.objects.create(
                user_id=user_id,
                title=f'试衣 {title or task_record.id}',
                file_url=result_url,
                file_type='png',
                category='garment',
            )

        logger.info(f"TryOn completed in {int((time.time()-start)*1000)}ms")
        return {'result_image_url': result_url, 'status': 'completed'}

    except Exception as exc:
        logger.error(f"TryOn failed: {exc}")
        TryOnTask.objects.filter(task_id=self.request.id).update(
            status='failed', error_message=str(exc)
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'status': 'failed', 'error': str(exc)}
