# 08 - ERP 对接方案

> **版本**：v1.0 | **更新**：2026-06-26

---

## 8.1 对接目标

| 数据方向 | 内容 | 同步频率 | 优先级 |
|---------|------|---------|--------|
| **ERP → StyleFlow** | 款号、品类、波段 | 每日一次（凌晨） | P0 |
| **ERP → StyleFlow** | BOM 物料清单 | 每日一次 | P1 |
| **ERP → StyleFlow** | 工序标准、工价标准 | 每周一次 | P1 |
| **ERP → StyleFlow** | 生产报工数据 | 每小时 | P2 |
| **StyleFlow → ERP** | 新设计款式 | 流程完成时 | P0 |
| **StyleFlow → ERP** | 工艺单/核价结果 | 审批通过时 | P1 |

---

## 8.2 对接策略（按优先级）

### 方案 A：数据库直连（推荐）

**条件**：ERP 提供只读数据库账号，可直连 PostgreSQL / SQL Server / MySQL

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   ERP DB    │ ──SQL──▶│  同步程序    │ ──写入──▶│ StyleFlow DB │
│ (只读)       │         │ (Celery Beat)│         │ (本地镜像表)  │
└─────────────┘         └──────────────┘         └──────────────┘
```

**实现**：

```python
# apps/erp/sync_engine.py
from django.db import connections
from apps.erp.models import ErpStyle

class ErpDirectSync:
    """ERP 直连同步引擎"""

    def __init__(self):
        self.erp_db = 'erp'  # Django DATABASES 中配置的 ERP 连接别名

    def sync_styles(self):
        """同步款式主数据"""
        with connections[self.erp_db].cursor() as cursor:
            cursor.execute("""
                SELECT style_code, description, category, season,
                       bom_json, size_range, status
                FROM product_style
                WHERE updated_at >= %s
            """, [self._last_sync_time('erp_style')])

            for row in cursor.fetchall():
                ErpStyle.objects.update_or_create(
                    style_code=row[0],
                    defaults={
                        'description': row[1],
                        'category': row[2],
                        'season': row[3],
                        'bom': row[4] or {},
                        'size_range': row[5] or [],
                        'status': row[6],
                        'last_synced_at': timezone.now(),
                    }
                )

    def _last_sync_time(self, table):
        """获取上次同步时间"""
        from .models import SyncLog
        last = SyncLog.objects.filter(table_name=table).order_by('-synced_at').first()
        return last.synced_at if last else timezone.now() - timedelta(days=30)
```

### 方案 B：API 对接

**条件**：ERP 提供 REST/SOAP API

```python
class ErpApiSync:
    """ERP API 同步引擎"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def sync_styles(self, page=1):
        resp = self.session.get(
            f"{self.base_url}/api/styles",
            params={'page': page, 'page_size': 100, 'updated_after': self._last_sync},
            timeout=30,
        )
        data = resp.json()
        for item in data['results']:
            ErpStyle.objects.update_or_create(
                style_code=item['code'],
                defaults={'description': item['desc'], ...}
            )
        if data['next']:
            self.sync_styles(page=page + 1)
```

### 方案 C：CSV/Excel 导入（兜底）

```python
class ErpFileSync:
    """CSV 文件导入（无 API 无直连时的兜底方案）"""

    def import_styles(self, file_path: str):
        import pandas as pd
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            ErpStyle.objects.update_or_create(
                style_code=row['款号'],
                defaults={
                    'description': row.get('描述', ''),
                    'category': row.get('品类', ''),
                    'season': row.get('波段', ''),
                }
            )
```

---

## 8.3 数据映射

### 款式主数据

| ERP 字段 | ErpStyle 字段 | 类型 | 转换逻辑 |
|----------|--------------|------|---------|
| `style_code` | `style_code` | String | 直接映射 |
| `style_desc` | `description` | Text | 直接映射 |
| `category_id` → `category_name` | `category` | String | 通过字典表转换 ID→名称 |
| `season_code` | `season` | String | 直接映射 |
| `bom_json` / 多张 BOM 子表 | `bom` | JSONB | 聚合为 [{material, quantity, unit}] |
| `size_group` | `size_range` | JSON | 转为 ["S","M","L","XL"] |

### 工序数据

| ERP 字段 | ErpProcess 字段 | 类型 | 转换逻辑 |
|----------|----------------|------|---------|
| `process_code` | `process_code` | String | 直接映射 |
| `process_name` | `process_name` | String | 直接映射 |
| `category_id` | `category` | String | 字典转换 |
| `std_time_min` | `standard_time` | Decimal | 直接映射 |
| `unit_price` | `unit_cost` | Decimal | 直接映射 |

---

## 8.4 回写机制

### 回写接口（StyleFlow → ERP）

```python
# apps/erp/writeback.py
class ErpWriteBack:
    """向 ERP 回写数据"""

    RETRY_MAX = 3
    RETRY_DELAY = 60  # 秒

    def write_style(self, design: Design, techpack: TechPack) -> bool:
        """将新款式回写到 ERP 开发模块"""
        payload = {
            "style_code": self._generate_style_code(),
            "description": design.title,
            "category": techpack.category,
            "tech_drawing": design.image_url,
            "size_spec": techpack.size_spec,
            "process_steps": techpack.process_steps,
        }
        for attempt in range(self.RETRY_MAX):
            try:
                resp = requests.post(
                    f"{self.settings['base_url']}/api/styles",
                    json=payload,
                    headers=self._headers(),
                    timeout=30,
                )
                resp.raise_for_status()
                self._log_success('write_style', payload)
                return True
            except requests.RequestException as e:
                self._log_failure('write_style', payload, str(e))
                if attempt < self.RETRY_MAX - 1:
                    time.sleep(self.RETRY_DELAY)
        return False

    def _generate_style_code(self):
        """生成款号：SF + 年份 + 4位序号（如 SF20260001）"""
        today = timezone.now()
        prefix = f"SF{today.year}"
        last = ErpStyle.objects.filter(
            style_code__startswith=prefix
        ).order_by('style_code').last()
        seq = (int(last.style_code[-4:]) + 1) if last else 1
        return f"{prefix}{seq:04d}"
```

### 回写状态跟踪

```python
class WriteBackLog(models.Model):
    """回写日志"""
    ACTION_CHOICES = [
        ('write_style', '写入款式'),
        ('write_techpack', '写入工艺单'),
        ('write_costing', '写入核价结果'),
    ]
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    object_id = models.IntegerField()
    payload = models.JSONField()
    response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'erp_writeback_log'
```

---

## 8.5 同步配置与管理

### Django 配置

```python
# config/settings/base.py
ERP_CONFIG = {
    'mode': os.getenv('ERP_MODE', 'direct'),  # direct / api / file
    # 直连模式
    'direct': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('ERP_DB_NAME'),
        'USER': os.getenv('ERP_DB_USER'),
        'PASSWORD': os.getenv('ERP_DB_PASSWORD'),
        'HOST': os.getenv('ERP_DB_HOST'),
        'PORT': os.getenv('ERP_DB_PORT'),
        'OPTIONS': {
            'options': '-c statement_timeout=30000',  # 30s 查询超时
        },
    },
    # API 模式
    'api': {
        'base_url': os.getenv('ERP_API_URL'),
        'api_key': os.getenv('ERP_API_KEY'),
        'timeout': 30,
    },
}
```

### Celery Beat 定时任务

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-erp-styles-daily': {
        'task': 'apps.erp.tasks.sync_erp_styles',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点
    },
    'sync-erp-processes-weekly': {
        'task': 'apps.erp.tasks.sync_erp_processes',
        'schedule': crontab(hour=3, minute=30, day_of_week=1),  # 每周一
    },
    'retry-failed-writebacks': {
        'task': 'apps.erp.tasks.retry_failed_writebacks',
        'schedule': crontab(hour='*/4', minute=0),  # 每4小时
    },
}
```

---

## 8.6 安全与隔离

| 措施 | 说明 |
|------|------|
| **最小权限** | ERP 只读账号仅授予查询必要表的 SELECT 权限 |
| **连接隔离** | ERP 数据库连接与 StyleFlow 主库分离（独立的 DATABASES 配置） |
| **查询超时** | 所有 ERP 查询设置 `statement_timeout`，防止慢查询拖垮 ERP |
| **敏感字段** | API Key、密码等通过环境变量注入，不硬编码 |
| **数据校验** | 同步数据写入前做完整性校验，无效数据记录日志并跳过 |
| **断连恢复** | 同步失败后自动重试，最多 3 次，间隔 60s |
