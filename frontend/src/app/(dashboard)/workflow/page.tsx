'use client';

import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Tag, Button, Spin, Empty, Typography, Space,
  Modal, Descriptions, Timeline, message, Select
} from 'antd';
import {
  ApartmentOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ClockCircleOutlined, RightCircleOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  rejected: { color: 'error', label: '已驳回' },
  cancelled: { color: 'default', label: '已取消' },
};

const TYPE_MAP: Record<string, string> = {
  style_development: '款式开发',
  costing: '核工价审批',
  techpack_review: '工艺单审核',
};

export default function WorkflowPage() {
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [filter, setFilter] = useState('');

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filter) params.status = filter;
      const res: any = await api.get('/workflows', { params });
      setInstances(res.data || res.results || res || []);
    } catch { message.error('加载工作流失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchWorkflows(); }, [filter]);

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
      message.success(action === 'approve' ? '已推进' : '已驳回');
      setDetailVisible(false);
      fetchWorkflows();
    } catch { message.error('操作失败'); }
  };

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />工作流中心
        </Title>
        <Select
          value={filter}
          onChange={setFilter}
          style={{ width: 140 }}
          options={[
            { value: '', label: '全部' },
            { value: 'running', label: '进行中' },
            { value: 'completed', label: '已完成' },
            { value: 'rejected', label: '已驳回' },
          ]}
        />
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
       : instances.length === 0 ? <Empty description="暂无工作流" style={{ padding: 80 }} />
       : <Row gutter={[16, 16]}>
          {instances.map((inst) => {
            const st = STATUS_MAP[inst.status] || { color: 'default', label: inst.status };
            return (
              <Col key={inst.id} xs={24} sm={12} lg={8}>
                <Card hoverable onClick={() => showDetail(inst.id)} style={{ borderRadius: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Tag>{TYPE_MAP[inst.workflow_type] || inst.workflow_type}</Tag>
                      <Tag color={st.color}>{st.label}</Tag>
                    </div>
                    <Text strong ellipsis>{inst.title}</Text>
                    <Text type="secondary">
                      <ClockCircleOutlined /> {inst.created_at?.slice(0, 10)}
                    </Text>
                    <Text>
                      当前节点: <Tag color="blue">{inst.current_node}</Tag>
                    </Text>
                  </Space>
                </Card>
              </Col>
            );
          })}
         </Row>}

      <Modal
        title={selected?.title}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={700}
        footer={
          selected?.status === 'running' ? (
            <Space>
              <Button icon={<CloseCircleOutlined />} danger onClick={() => handleProceed(selected.id, 'reject')}>
                驳回
              </Button>
              <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => handleProceed(selected.id, 'approve')}>
                推进
              </Button>
            </Space>
          ) : null
        }
      >
        {selected && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="类型">{TYPE_MAP[selected.workflow_type]}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_MAP[selected.status]?.color}>{STATUS_MAP[selected.status]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="当前节点">{selected.current_node}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{selected.created_at?.slice(0, 16)}</Descriptions.Item>
            </Descriptions>

            <Title level={5}>操作历史</Title>
            <Timeline items={selected.nodes?.map((n: any) => ({
              color: n.action === 'approve' ? 'green' : n.action === 'reject' ? 'red' : 'blue',
              children: (
                <div>
                  <Text strong>{n.node_name}</Text>
                  <Text type="secondary"> — {n.handler}</Text>
                  <br />
                  <Text type="secondary">{n.action === 'approve' ? '✅ 通过' : n.action === 'reject' ? '❌ 驳回' : '▶ 开始'}
                    {n.comment ? `: ${n.comment}` : ''}
                  </Text>
                  <br />
                  <Text style={{ fontSize: 12 }} type="secondary">{n.created_at?.slice(0, 16)}</Text>
                </div>
              ),
            })) || []} />
          </Space>
        )}
      </Modal>
    </DashboardLayout>
  );
}
