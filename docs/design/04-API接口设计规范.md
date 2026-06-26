# 04 - API 接口设计规范

> **版本**：v1.0 | **更新**：2026-06-26

---

## 4.1 设计原则

- **RESTful 风格**：资源导向，动词通过 HTTP Method 表达
- **版本前缀**：`/api/v1/...`，便于后续版本迭代
- **统一响应格式**：所有接口返回标准化 JSON
- **自动文档**：Django Ninja 生成 OpenAPI 3.0，访问 `/api/docs`
- **类型安全**：请求/响应使用 Pydantic Schema 声明，避免手写序列化

---

## 4.2 统一响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 列表响应（分页）

```json
{
  "success": true,
  "data": [
    { "id": 1, "title": "..." },
    { "id": 2, "title": "..." }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "DESIGN_NOT_FOUND",
    "message": "设计稿不存在",
    "details": {}
  }
}
```

---

## 4.3 认证鉴权

### JWT 认证流程

```
客户端                    Django Ninja
  │                           │
  │  POST /api/v1/auth/login  │
  │  { username, password }   │
  │ ───────────────────────►  │
  │                           │ 验证用户
  │ ◄───────────────────────  │
  │  { access_token,          │
  │    refresh_token }        │
  │                           │
  │  GET /api/v1/designs      │
  │  Authorization: Bearer xxx│
  │ ───────────────────────►  │
  │                           │ 验证 token
  │ ◄───────────────────────  │
  │  { designs... }           │
```

**Token 策略**：
- Access Token：有效期 30 分钟
- Refresh Token：有效期 7 天
- 刷新端点：`POST /api/v1/auth/refresh`

### 权限装饰器

```python
# Ninja Router 中
from ninja import Router
from common.permissions import require_role

router = Router()

@router.get('/designs')
@require_role(['designer', 'admin'])
def list_designs(request):
    ...
```

---

## 4.4 API 端点清单

### 4.4.1 认证模块 `/api/v1/auth`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | 公开 |
| POST | `/api/v1/auth/login` | 登录，返回 JWT | 公开 |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 公开 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | 登录 |
| PATCH | `/api/v1/auth/me` | 更新个人资料 | 登录 |

### 4.4.2 设计工坊 `/api/v1/designs`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/designs` | 设计稿列表（分页、筛选） | 登录 |
| POST | `/api/v1/designs` | 创建设计稿 | 登录 |
| GET | `/api/v1/designs/{id}` | 设计稿详情 | 登录 |
| PATCH | `/api/v1/designs/{id}` | 更新设计稿信息 | 登录/创建者 |
| DELETE | `/api/v1/designs/{id}` | 删除设计稿（软删除） | 登录/创建者 |
| POST | `/api/v1/designs/generate` | 提交 AI 生成任务 | 登录 |
| GET | `/api/v1/designs/tasks/{task_id}` | 查询任务状态/结果 | 登录 |
| GET | `/api/v1/designs/{id}/versions` | 版本列表 | 登录 |

**Query 参数（列表接口）**：
- `page` (int, default=1)
- `page_size` (int, default=20, max=100)
- `category` (str, optional)
- `status` (str, optional)
- `search` (str, optional, 搜索标题/标签)
- `ordering` (str, default='-created_at')

### 4.4.3 虚拟试衣 `/api/v1/tryon`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/tryon/tasks` | 提交试衣合成任务 | 登录 |
| GET | `/api/v1/tryon/tasks/{id}` | 查询任务状态/结果 | 登录 |
| GET | `/api/v1/tryon/tasks` | 我的试衣任务列表 | 登录 |

### 4.4.4 工艺单 `/api/v1/techpacks`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/techpacks` | 工艺单列表 | 登录 |
| POST | `/api/v1/techpacks` | 创建工艺单（手动） | 设计师/版师 |
| POST | `/api/v1/techpacks/generate` | AI 自动生成工艺单 | 设计师/版师 |
| GET | `/api/v1/techpacks/{id}` | 工艺单详情 | 登录 |
| PATCH | `/api/v1/techpacks/{id}` | 更新工艺单 | 创建者 |
| POST | `/api/v1/techpacks/{id}/submit` | 提交审核 | 创建者 |
| POST | `/api/v1/techpacks/{id}/approve` | 审核通过 | 管理员 |

### 4.4.5 工作流 `/api/v1/workflows`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/workflows` | 工作流实例列表 | 登录 |
| GET | `/api/v1/workflows/{id}` | 实例详情（含节点历史） | 登录 |
| POST | `/api/v1/workflows/{id}/proceed` | 推进到下一节点 | 有权限 |
| POST | `/api/v1/workflows/{id}/reject` | 驳回 | 有权限 |

### 4.4.6 核工价 `/api/v1/costing`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/costing/{techpack_id}` | 查看核价结果 | 登录 |
| POST | `/api/v1/costing/calculate` | 发起核价计算 | 版师/管理员 |
| POST | `/api/v1/costing/{id}/approve` | 审批核价 | 管理员 |

### 4.4.7 计件工资 `/api/v1/wages`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/wages/report` | 工资报表 | 财务/管理员 |
| GET | `/api/v1/wages/records` | 明细记录 | 财务/管理员 |
| POST | `/api/v1/wages/sync` | 手动触发同步（从ERP） | 管理员 |

### 4.4.8 ERP 数据 `/api/v1/erp`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/erp/styles` | ERP 款式列表 | 登录 |
| GET | `/api/v1/erp/styles/{code}` | 款式详情（含BOM） | 登录 |
| GET | `/api/v1/erp/processes` | 工序标准数据 | 登录 |
| POST | `/api/v1/erp/sync` | 触发数据同步 | 管理员 |

### 4.4.9 管理后台 `/api/v1/admin`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/users` | 用户管理列表 | 管理员 |
| PATCH | `/api/v1/admin/users/{id}` | 修改用户角色/状态 | 管理员 |
| GET | `/api/v1/admin/stats` | 系统统计数据 | 管理员 |

---

## 4.5 错误码体系

| HTTP 状态码 | 业务错误码 | 说明 |
|-------------|-----------|------|
| 400 | `INVALID_PARAMETERS` | 请求参数错误 |
| 401 | `UNAUTHORIZED` | 未认证（无 token 或 token 过期） |
| 403 | `FORBIDDEN` | 无权限 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | 资源冲突（如重复创建） |
| 422 | `VALIDATION_ERROR` | 数据校验失败 |
| 429 | `RATE_LIMITED` | 请求过于频繁 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |
| 503 | `SERVICE_UNAVAILABLE` | 服务暂不可用（如 AI 模型离线） |

---

## 4.6 SSE 任务进度推送

### 连接端点

```
GET /api/v1/events/tasks?token={jwt_token}
```

### 事件格式

```
event: task_progress
data: {"task_id": "abc123", "status": "processing", "progress": 60}

event: task_completed
data: {"task_id": "abc123", "result_url": "..."}

event: task_failed
data: {"task_id": "abc123", "error": "模型服务超时"}
```

### 连接生命周期

1. 客户端打开 SSE 连接（附带 token 验证）
2. 连接保持，服务端推送该用户相关任务的事件
3. 客户端断开后自动清理订阅

---

## 4.7 Ninja 代码示例

```python
# apps/design/api.py
from ninja import Router, Schema
from ninja.pagination import paginate, PageNumberPagination
from typing import List, Optional

router = Router(tags=['设计工坊'])

class DesignOut(Schema):
    id: int
    title: str
    image_url: str
    category: str
    status: str
    created_at: str

class DesignCreate(Schema):
    title: str = ''
    prompt: str
    category: str = 'style'
    width: int = 512
    height: int = 768

class GenerateOut(Schema):
    task_id: str
    status: str = 'pending'

@router.get('', response=List[DesignOut])
@paginate(PageNumberPagination, page_size=20)
def list_designs(request, category: Optional[str] = None, search: Optional[str] = None):
    qs = Design.objects.filter(creator=request.user, is_active=True)
    if category:
        qs = qs.filter(category=category)
    if search:
        qs = qs.filter(models.Q(title__icontains=search) | models.Q(tags__contains=search))
    return qs

@router.post('/generate', response=GenerateOut)
def generate_design(request, payload: DesignCreate):
    """提交AI生成任务"""
    task = generate_design_task.delay(
        user_id=request.user.id,
        prompt=payload.prompt,
        category=payload.category,
        width=payload.width,
        height=payload.height,
    )
    return {'task_id': task.id}
```
