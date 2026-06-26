from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin


class WorkflowInstance(TimestampMixin):
    """工作流实例"""
    WORKFLOW_TYPES = [
        ('style_development', '款式开发'),
        ('costing', '核工价审批'),
        ('techpack_review', '工艺单审核'),
    ]
    STATUS_CHOICES = [
        ('running', '进行中'),
        ('completed', '已完成'),
        ('rejected', '已驳回'),
        ('cancelled', '已取消'),
    ]

    workflow_type = models.CharField(max_length=30, choices=WORKFLOW_TYPES)
    object_id = models.IntegerField(help_text='关联业务对象ID')
    title = models.CharField(max_length=200)
    current_node = models.CharField(max_length=50, default='start')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    data_snapshot = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'workflow_instance'
        indexes = [models.Index(fields=['workflow_type', 'status'])]
        verbose_name = '工作流实例'
        verbose_name_plural = '工作流实例'


class WorkflowNode(models.Model):
    """工作流节点记录"""
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='nodes')
    node_name = models.CharField(max_length=50)
    handler = models.CharField(max_length=100, blank=True, help_text='处理人')
    action = models.CharField(max_length=50, help_text='操作: approve/reject/submit/start')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_node'
        ordering = ['created_at']
        verbose_name = '工作流节点'
        verbose_name_plural = '工作流节点'
