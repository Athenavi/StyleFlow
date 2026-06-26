'use client';

import { useState, useEffect } from 'react';
import {
  Card, Button, Typography, Space, message, Spin, Empty, App,
  Tag, List, Tooltip, Popconfirm, Tabs, Alert, Table, Badge, Descriptions
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ApartmentOutlined,
  PlayCircleOutlined, EyeOutlined, CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

const { Title, Text } = Typography;

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  rejected: { color: 'error', label: '已驳回' },
  cancelled: { color: 'default', label: '已取消' },
};

export default function WorkflowDefsPage() {
  const { message: msg } = App.useApp();
  const [defs, setDefs] = useState<any[]>([]);
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dRes, iRes] = await Promise.all([
        api.get('/workflows/definitions'),
        api.get('/workflows'),
      ]);
      setDefs(dRes.data || dRes.results || dRes || []);
      setInstances(iRes.data || iRes.results || iRes || []);
    } catch { msg.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleDelete = async (id: number) => {
    try { await api.delete(`/workflows/definitions/${id}`); msg.success('已删除'); fetchData(); } catch { msg.error('删除失败'); }
  };

  const handleStart = async (defId: number, defName: string) => {
    try {
      const res: any = await api.post('/workflows', {
        definition_id: defId,
        title: defName + ' ' + new Date().toLocaleString('zh-CN'),
      });
      msg.success('工作流已启动！可在「运行中实例」查看');
      fetchData();
    } catch (err: any) { msg.error(err.response?.data?.error?.message || '启动失败'); }
  };

  const instColumns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const st = STATUS_MAP[s] || { color: 'default', label: s };
        return <Tag color={st.color}>{st.label}</Tag>;
      },
    },
    { title: '当前节点', dataIndex: 'current_node', key: 'current_node',
      render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '指派人', dataIndex: 'assigned_name', key: 'assigned_name',
      render: (v: string) => v ? <Tag color="orange">{v}</Tag> : <Tag>待认领</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v?.slice(0, 16) || '-' },
    {
      title: '操作', key: 'action',
      render: (_: any, r: any) => (
        <Button size="small" icon={<EyeOutlined />}
          onClick={() => { /* 跳转到实例详情后续实现 */ }}>查看</Button>
      ),
    },
  ];

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;

  return (
    <DashboardLayout>
      <Title level={3} style={{ marginBottom: 16 }}>
        <ApartmentOutlined style={{ marginRight: 8 }} />工作流
      </Title>

      <Alert message={
        <span>
          <strong>使用说明：</strong>
          ① 在下方「工作流模板」中点击 <PlayCircleOutlined /> 启动工作流 →
          ② 实例在「运行中实例」列表出现，状态为「进行中」 →
          ③ 相应角色的用户进入工作流看板 → 点击「认领」任务（先到先得）→
          ④ 认领后点击详情弹窗中的「推进」/「驳回」处理节点
        </span>
      } type="info" showIcon style={{ marginBottom: 16, borderRadius: 8 }} />

      <Tabs defaultActiveKey="defs" items={[
        {
          key: 'defs',
          label: <span>📋 工作流模板 ({defs.length})</span>,
          children: (
            <>
              <div style={{ marginBottom: 12, textAlign: 'right' }}>
                <Button type="primary" icon={<PlusOutlined />}
                  onClick={() => router.push('/workflow/editor')}>
                  新建模板
                </Button>
              </div>
              {defs.length === 0 ? (
                <Empty description="暂无工作流模板，点击上方创建">
                  <Button type="primary" onClick={() => router.push('/workflow/editor')}>立即创建</Button>
                </Empty>
              ) : (
                <List grid={{ gutter: 16, xs: 1, sm: 2, lg: 3 }}
                  dataSource={defs}
                  renderItem={(item: any) => (
                    <List.Item>
                      <Card
                        hoverable
                        actions={[
                          <Tooltip title="启动" key="start">
                            <PlayCircleOutlined style={{ color: '#52c41a' }}
                              onClick={() => handleStart(item.id, item.name)} />
                          </Tooltip>,
                          <Tooltip title="查看" key="view">
                            <EyeOutlined onClick={() => router.push(`/workflow/${item.id}`)} />
                          </Tooltip>,
                          <Tooltip title="编辑" key="edit">
                            <EditOutlined onClick={() => router.push(`/workflow/editor?id=${item.id}`)} />
                          </Tooltip>,
                          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(item.id)} key="del">
                            <Tooltip title="删除"><DeleteOutlined /></Tooltip>
                          </Popconfirm>,
                        ]}
                        style={{ borderRadius: 8 }}
                      >
                        <Card.Meta
                          title={item.name}
                          description={
                            <Space direction="vertical" size={4}>
                              <Text type="secondary">{item.description || '无描述'}</Text>
                              <Space>
                                <Tag>{item.nodes?.length || 0} 个节点</Tag>
                                <Tag color="blue">初始: {item.initial}</Tag>
                              </Space>
                            </Space>
                          }
                        />
                      </Card>
                    </List.Item>
                  )}
                />
              )}
            </>
          ),
        },
        {
          key: 'instances',
          label: <span>▶ 运行中实例 ({instances.filter(i => i.status === 'running').length})</span>,
          children: (
            <Table dataSource={instances} columns={instColumns} rowKey="id"
              pagination={{ pageSize: 10 }} size="small" />
          ),
        },
      ]} />
    </DashboardLayout>
  );
}
