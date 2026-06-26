'use client';

import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Tag, Button, Spin, Empty, Typography, Space,
  Modal, Descriptions, Timeline, message, Select, Badge, Tooltip
} from 'antd';
import {
  ApartmentOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ClockCircleOutlined, PlusOutlined, UnorderedListOutlined,
  AppstoreOutlined, HistoryOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  rejected: { color: 'error', label: '已驳回' },
  cancelled: { color: 'default', label: '已取消' },
};

const TYPE_LABEL: Record<string, string> = {
  style_development: '款式开发',
  costing: '核工价审批',
  techpack_review: '工艺单审核',
};

// Kanban 阶段配置
const KANBAN_COLUMNS = [
  { key: 'running', label: '进行中', color: '#1677ff' },
  { key: 'completed', label: '已完成', color: '#52c41a' },
  { key: 'rejected', label: '已驳回', color: '#ff4d4f' },
];

export default function WorkflowPage() {
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [viewMode, setViewMode] = useState<'kanban' | 'list'>('kanban');
  const [todos, setTodos] = useState<any[]>([]);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filterType) params.workflow_type = filterType;
      const [wfRes, todoRes] = await Promise.all([
        api.get('/workflows', { params }),
        api.get('/workflows/todos'),
      ]);
      setInstances(wfRes.data || wfRes.results || wfRes || []);
      setTodos(todoRes?.todos || []);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchWorkflows(); }, [filterType]);

  const showDetail = async (id: number) => {
    try {
      const res: any = await api.get(`/workflows/${id}`);
      setSelected(res.data || res);
      setDetailVisible(true);
    } catch { message.error('加载详情失败'); }
  };

  const handleProceed = async (id: number, action: string) => {
    try {
      await api.post(`/workflows/${id}/proceed`, { action, comment: '' });
      message.success(action === 'approve' ? '✅ 已推进' : '❌ 已驳回');
      setDetailVisible(false);
      fetchWorkflows();
    } catch { message.error('操作失败'); }
  };

  // 按状态分组（看板）
  const grouped = KANBAN_COLUMNS.map(col => ({
    ...col,
    items: instances.filter(i => i.status === col.key),
  }));

  // 待办 ID 集合
  const todoIds = new Set(todos.map((t: any) => t.instance_id));

  const renderCard = (inst: any) => (
    <Card
      key={inst.id}
      hoverable
      size="small"
      style={{ marginBottom: 8, borderRadius: 6, borderLeft: `3px solid ${todoIds.has(inst.id) ? '#faad14' : '#d9d9d9'}` }}
      onClick={() => showDetail(inst.id)}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={4}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Tag style={{ fontSize: 11, margin: 0 }}>{TYPE_LABEL[inst.workflow_type] || inst.workflow_type}</Tag>
          {todoIds.has(inst.id) && <Badge count="待办" size="small" color="#faad14" />}
        </div>
        <Text strong ellipsis style={{ fontSize: 13 }}>{inst.title}</Text>
        <div>
          <Text type="secondary" style={{ fontSize: 11 }}>节点: </Text>
          <Tag color="blue" style={{ fontSize: 11 }}>{inst.current_node}</Tag>
        </div>
        <Text type="secondary" style={{ fontSize: 11 }}>{inst.created_at?.slice(0, 10)}</Text>
      </Space>
    </Card>
  );

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />工作流
        </Title>
        <Space>
          {todos.length > 0 && <Tag color="gold">{todos.length} 个待办</Tag>}
          <Select value={filterType} onChange={setFilterType} style={{ width: 130 }}
            options={[
              { value: '', label: '全部类型' },
              { value: 'style_development', label: '款式开发' },
              { value: 'costing', label: '核工价审批' },
              { value: 'techpack_review', label: '工艺单审核' },
            ]} />
          <Tooltip title="看板视图"><Button icon={<AppstoreOutlined />} type={viewMode === 'kanban' ? 'primary' : 'default'} onClick={() => setViewMode('kanban')} /></Tooltip>
          <Tooltip title="列表视图"><Button icon={<UnorderedListOutlined />} type={viewMode === 'list' ? 'primary' : 'default'} onClick={() => setViewMode('list')} /></Tooltip>
        </Space>
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
       : instances.length === 0 ? <Empty description="暂无工作流" style={{ padding: 80 }} />

       : viewMode === 'kanban' ? (
         <Row gutter={16} style={{ minHeight: 400 }}>
           {grouped.map(col => (
             <Col key={col.key} xs={24} sm={8}>
               <Card title={<Space><Badge color={col.color} />{col.label}<Tag>{col.items.length}</Tag></Space>}
                 style={{ borderRadius: 8, background: '#fafafa' }} size="small">
                 {col.items.length === 0
                   ? <Empty description="无" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                   : col.items.map(renderCard)}
               </Card>
             </Col>
           ))}
         </Row>
       ) : (
         // 列表视图
         <Row gutter={[16, 16]}>
           {instances.map(inst => (
             <Col key={inst.id} xs={24} sm={12} lg={8}>
               {renderCard(inst)}
             </Col>
           ))}
         </Row>
       )}

      {/* 详情弹窗 */}
      <Modal title={selected?.title} open={detailVisible} onCancel={() => setDetailVisible(false)}
        width={650} footer={selected?.status === 'running' ? (
          <Space>
            <Button icon={<CloseCircleOutlined />} danger onClick={() => handleProceed(selected.id, 'reject')}>驳回</Button>
            <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => handleProceed(selected.id, 'approve')}>推进</Button>
          </Space>
        ) : null}>
        {selected && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="类型">{TYPE_LABEL[selected.workflow_type]}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_CONFIG[selected.status]?.color}>{STATUS_CONFIG[selected.status]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="当前节点"><Tag color="blue">{selected.current_node}</Tag></Descriptions.Item>
              <Descriptions.Item label="创建时间">{selected.created_at?.slice(0, 16)}</Descriptions.Item>
            </Descriptions>
            <Title level={5}><HistoryOutlined /> 操作历史</Title>
            <Timeline items={selected.nodes?.map((n: any) => ({
              color: n.action === 'approve' ? 'green' : n.action === 'reject' ? 'red' : 'blue',
              children: <div>
                  <Text strong>{n.node_name}</Text>
                  <Text type="secondary"> — {n.handler}</Text>
                  <br />
                  <Text type="secondary">
                    {n.action === 'approve' ? '✅ 通过' : n.action === 'reject' ? '❌ 驳回' : '▶ 开始'}
                    {n.comment ? `: ${n.comment}` : ''}
                  </Text>
                  <br />
                  <Text style={{ fontSize: 12 }} type="secondary">{n.created_at?.slice(0, 16)}</Text>
                </div>,
            })) || []} />
          </Space>
        )}
      </Modal>
    </DashboardLayout>
  );
}
