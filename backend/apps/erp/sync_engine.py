"""ERP 数据同步引擎"""
import logging
from datetime import datetime, timedelta
from django.db import connections, transaction
from django.utils import timezone

from .models import ErpStyle, ErpProcess

logger = logging.getLogger(__name__)


class SyncLog:
    """同步日志（简易实现）"""
    _logs = {}

    @classmethod
    def get_last_sync(cls, table: str) -> datetime:
        return cls._logs.get(table, timezone.now() - timedelta(days=30))

    @classmethod
    def record(cls, table: str):
        cls._logs[table] = timezone.now()


class ErpDirectSync:
    """ERP 数据库直连同步引擎"""

    erp_db = 'erp'

    def sync_styles(self):
        """同步款式主数据"""
        try:
            with connections[self.erp_db].cursor() as cursor:
                cursor.execute("""
                    SELECT style_code, description, category, season,
                           bom_json, size_range, status
                    FROM product_style
                    WHERE updated_at >= %s
                """, [SyncLog.get_last_sync('erp_style')])

                count = 0
                for row in cursor.fetchall():
                    ErpStyle.objects.update_or_create(
                        style_code=row[0],
                        defaults={
                            'description': row[1] or '',
                            'category': row[2] or '',
                            'season': row[3] or '',
                            'bom': row[4] or {},
                            'size_range': row[5] or [],
                            'status': row[6] or '',
                            'last_synced_at': timezone.now(),
                        }
                    )
                    count += 1

                SyncLog.record('erp_style')
                logger.info(f"Synced {count} ERP styles")
        except Exception as e:
            logger.error(f"ERP style sync failed: {e}")

    def sync_processes(self):
        """同步工序标准数据"""
        try:
            with connections[self.erp_db].cursor() as cursor:
                cursor.execute("""
                    SELECT process_code, process_name, category,
                           standard_time, unit_price
                    FROM process_standard
                    WHERE updated_at >= %s
                """, [SyncLog.get_last_sync('erp_process')])

                count = 0
                for row in cursor.fetchall():
                    ErpProcess.objects.update_or_create(
                        process_code=row[0],
                        defaults={
                            'process_name': row[1],
                            'category': row[2] or '',
                            'standard_time': row[3],
                            'unit_cost': row[4],
                            'last_synced_at': timezone.now(),
                        }
                    )
                    count += 1

                SyncLog.record('erp_process')
                logger.info(f"Synced {count} ERP processes")
        except Exception as e:
            logger.error(f"ERP process sync failed: {e}")
