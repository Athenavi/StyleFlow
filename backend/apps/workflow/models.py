from django.db import models
from django.contrib.auth.models import User
from common.models import TimestampMixin

MAX_DEFINITIONS = 10


class WorkflowDefinition(TimestampMixin):
    """工作流定义（用户可编辑的可视化工作流模板，最多10条）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_defs')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    initial = models.CharField(max_length=50, default='start')
    nodes = models.JSONField(default=list, blank=True, help_text='节点列表')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'workflow_definition'
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['user', 'name'], name='uq_user_wf_name')]
        verbose_name = '工作流定义'

    def __str__(self):
        return f'{self.name} ({len(self.nodes)} 节点)'


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
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.SET_NULL, null=True, blank=True)
    current_node = models.CharField(max_length=50, default='start')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    data_snapshot = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_workflows')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_workflows')

    class Meta:
        db_table = 'workflow_instance'
        indexes = [models.Index(fields=['workflow_type', 'status'])]
        verbose_name = '工作流实例'


class WorkflowNode(models.Model):
    """工作流节点记录"""
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='nodes')
    node_name = models.CharField(max_length=50)
    handler = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=50, help_text='approve/reject/submit/start')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_node'
        ordering = ['created_at']
        verbose_name = '工作流节点'
