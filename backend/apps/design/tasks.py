import logging
from celery import shared_task
from django.conf import settings

from .models import Design
from common.aiservice.factory import get_image_service, get_image_service_for_user, get_prompt_template
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30,
             queue='ai_generation', soft_time_limit=300)
def generate_design_task(self, user_id: int, prompt: str,
                          negative_prompt: str = '', category: str = 'style',
                          width: int = 512, height: int = 768,
                          template: str = 'style', title: str = ''):
    """AI 设计稿生成任务"""
    import time
    start = time.time()

    try:
        # 获取参数模板
        tmpl = get_prompt_template(template)

        # 构造完整 prompt
        full_prompt = tmpl['prompt_prefix'].format(prompt=prompt)
        neg_prompt = negative_prompt or tmpl['negative_prompt']

        # 使用用户配置的图像生成服务
        user = User.objects.get(id=user_id)
        service = get_image_service_for_user(user) or get_image_service('default')

        result = service.text2img(
            prompt=full_prompt,
            negative_prompt=neg_prompt,
            width=width,
            height=height,
            steps=tmpl.get('steps', 25),
            cfg_scale=tmpl.get('cfg_scale', 7),
        )

        # 保存到数据库
        design = Design.objects.create(
            creator_id=user_id,
            title=title or prompt[:50],
            prompt=prompt,
            negative_prompt=neg_prompt,
            category=category,
            image_url=result.image_url,
            width=width,
            height=height,
            tags=[],
            metadata={
                'seed': result.seed,
                'model': result.model,
                'latency_ms': result.latency_ms,
                'template': template,
            },
            status='completed',
        )

        logger.info(f"Design #{design.id} generated in {result.latency_ms}ms, seed={result.seed}")

        from .schemas import DesignOut
        design_out = DesignOut.from_orm(design)

        return {
            'design_id': design.id,
            'image_url': result.image_url,
            'design': {
                'id': design.id,
                'title': design.title,
                'image_url': result.image_url,
                'category': category,
                'status': 'completed',
            },
        }

    except Exception as exc:
        logger.error(f"Design generation failed: {exc}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'error': str(exc), 'status': 'failed'}
