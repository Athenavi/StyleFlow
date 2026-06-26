from ninja import NinjaAPI
from ninja import Schema

from apps.accounts.api import router as accounts_router
from apps.design.api import router as design_router
from apps.tryon.api import router as tryon_router
from apps.planning.api import router as planning_router
from apps.techpack.api import router as techpack_router
from apps.workflow.api import router as workflow_router
from apps.costing.api import router as costing_router
from apps.wages.api import router as wages_router
from apps.erp.api import router as erp_router
from apps.admin.api import router as admin_router

api = NinjaAPI(
    title='StyleFlow API',
    version='1.0.0',
    description='StyleFlow 服装设计-生产协同平台 API',
    docs_url='/docs/',
    openapi_url='/openapi.json',
)

# Register routers
api.add_router('/auth', accounts_router, tags=['认证'])
api.add_router('/designs', design_router, tags=['设计工坊'])
api.add_router('/tryon', tryon_router, tags=['虚拟试衣'])
api.add_router('/planning', planning_router, tags=['商品企划'])
api.add_router('/techpacks', techpack_router, tags=['工艺单'])
api.add_router('/workflows', workflow_router, tags=['工作流'])
api.add_router('/costing', costing_router, tags=['核工价'])
api.add_router('/wages', wages_router, tags=['计件工资'])
api.add_router('/erp', erp_router, tags=['ERP对接'])
api.add_router('/admin', admin_router, tags=['系统配置'])


@api.exception_handler(Exception)
def global_exception(request, exc):
    return api.create_response(request, {
        'success': False,
        'error': {'code': 'INTERNAL_ERROR', 'message': str(exc)},
    }, status=500)
