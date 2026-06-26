'use client';

import { useState, useEffect } from 'react';
import {
  Card, Button, Typography, Space, Spin, Empty, App,
  Tag, List, Tooltip, Popconfirm, Tabs, Alert, Table,
  Modal, Timeline, Descriptions, Row, Col
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ApartmentOutlined,
  PlayCircleOutlined, EyeOutlined, CheckCircleOutlined, CloseCircleOutlined,
  TeamOutlined, CopyOutlined, DownloadOutlined
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

export default function WorkflowPage() {
  const { message: msg } = App.useApp();
  const [defs, setDefs] = useState<any[]>([]);
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Process modal
  const [processModal, setProcessModal] = useState(false);
  const [currentInst, setCurrentInst] = useState<any>(null);
  const [processLoading, setProcessLoading] = useState(false);
  const [instDetail, setInstDetail] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dRes, iRes] = await Promise.all([
        api.get('/workflows/definitions'),
        api.get('/workflows/enriched'),
      ]);
      setDefs(dRes.data || dRes.results || dRes || []);
      setInstances(iRes.data || iRes.results || iRes || []);
    } catch { msg.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  // --- actions ---
  const handleDelete = async (id: number) => {
    try { await api.delete(`/workflows/definitions/${id}`); msg.success('已归档'); fetchData(); } catch { msg.error('操作失败'); }
  };
  const handleHardDelete = async (id: number) => {
    try { await api.delete(`/workflows/definitions/${id}/hard`); msg.success('已永久删除'); fetchData(); } catch { msg.error('操作失败'); }
  };
  const handleStart = async (defId: number, defName: string) => {
    try { await api.post('/workflows', { definition_id: defId, title: defName + ' ' + new Date().toLocaleString('zh-CN') }); msg.success('工作流已启动！'); fetchData(); } catch (err: any) { msg.error(err.response?.data?.error?.message || '启动失败'); }
  };
  const handleCopy = async (id: number) => {
    try { await api.post(`/workflows/definitions/${id}/copy`); msg.success('已复制'); fetchData(); } catch (err: any) { msg.error(err.response?.data?.error?.message || '复制失败'); }
  };
  const handleClaim = async (instanceId: number) => {
    try { await api.post(`/workflows/${instanceId}/claim`); msg.success('已认领'); fetchData(); } catch (err: any) { msg.error(err.response?.data?.error?.message || '认领失败'); }
  };
  const openProcess = async (inst: any) => {
    setCurrentInst(inst);
    try { const res: any = await api.get(`/workflows/${inst.id}`); setInstDetail(res.data || res); } catch { setInstDetail(inst); }
    setProcessModal(true);
  };
  const handleProceed = async (action: 'approve' | 'reject') => {
    if (!currentInst) return;
    setProcessLoading(true);
    try { await api.post(`/workflows/${currentInst.id}/proceed`, { action, comment: '' }); msg.success(action === 'approve' ? '✅ 已推进' : '❌ 已驳回'); setProcessModal(false); fetchData(); } catch (err: any) { msg.error(err.response?.data?.error?.message || '操作失败'); }
    finally { setProcessLoading(false); }
  };
  const handleInstallBuiltin = async (name: string) => {
    try { await api.post(`/workflows/builtin/${encodeURIComponent(name)}`); msg.success(`已安装「${name}」`); fetchData(); } catch (err: any) { msg.error(err.response?.data?.error?.message || '安装失败'); }
  };

  const instColumns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => { const st = STATUS_MAP[s] || {}; return <Tag color={st.color}>{st.label}</Tag>; } },
    { title: '节点', dataIndex: 'current_node', key: 'current_node', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '指派人', dataIndex: 'assigned_name', key: 'assigned_name', render: (v: string, r: any) => r.is_mine ? <Tag color="green">我</Tag> : v ? <Tag color="orange">{v}</Tag> : <Tag>待认领</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => v?.slice(0, 16) || '-' },
    {
      title: '操作', key: 'action',
      render: (_: any, r: any) => (
        <Space size={4}>
          {r.status === 'running' && !r.assigned_name && <Button size="small" type="primary" ghost icon={<TeamOutlined />} onClick={() => handleClaim(r.id)}>认领</Button>}
          {r.is_mine && <Button size="small" type="primary" icon={<EyeOutlined />} onClick={() => openProcess(r)}>处理</Button>}
        </Space>
      ),
    },
  ];

  const defActions = (item: any) => [
    <Popconfirm title="启动后将创建实例，确认？" key="start" onConfirm={() => handleStart(item.id, item.name)}>
      <Tooltip title="启动"><PlayCircleOutlined style={{ color: '#52c41a' }} /></Tooltip>
    </Popconfirm>,
    <Tooltip title="查看" key="view"><EyeOutlined onClick={() => router.push(`/workflow/${item.id}`)} /></Tooltip>,
    <Tooltip title="编辑" key="edit"><EditOutlined onClick={() => router.push(`/workflow/editor?id=${item.id}`)} /></Tooltip>,
    <Tooltip title="复制" key="copy"><CopyOutlined onClick={() => handleCopy(item.id)} /></Tooltip>,
    <Popconfirm title="归档（可恢复）？" key="soft" onConfirm={() => handleDelete(item.id)}>
      <Tooltip title="归档"><DeleteOutlined /></Tooltip>
    </Popconfirm>,
    <Popconfirm title="永久删除？不可恢复！" key="hard" onConfirm={() => handleHardDelete(item.id)}>
      <Tooltip title="永久删除"><CloseCircleOutlined style={{ color: '#ff4d4f' }} /></Tooltip>
    </Popconfirm>,
  ];

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;

  return (
    <DashboardLayout>
      <Title level={3} style={{ marginBottom: 16 }}><ApartmentOutlined style={{ marginRight: 8 }} />工作流</Title>

      <Alert message={<span><strong>使用说明：</strong>① 安装内置模板或新建 → ② 点击 ▶ 启动 → ③ 认领任务 → ④ 推进/驳回</span>}
        type="info" showIcon style={{ marginBottom: 16, borderRadius: 8 }} />

      <Tabs defaultActiveKey="defs" items={[
        {
          key: 'defs', label: <span>📋 我的模板 ({defs.length})</span>,
          children: (
            <>
              <div style={{ marginBottom: 12, textAlign: 'right' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => router.push('/workflow/editor')}>新建模板</Button>
              </div>
              {defs.length === 0 ? <Empty description="暂无模板，可安装内置模板或新建"><Button type="primary" onClick={() => router.push('/workflow/editor')}>立即创建</Button></Empty>
              : <List grid={{ gutter: 16, xs: 1, sm: 2, lg: 3 }} dataSource={defs}
                  renderItem={(item: any) => (
                    <List.Item>
                      <Card hoverable actions={defActions(item)} style={{ borderRadius: 8 }}>
                        <Card.Meta title={item.name}
                          description={<Space direction="vertical" size={4}>
                            <Text type="secondary">{item.description || '无描述'}</Text>
                            <Space><Tag>{item.nodes?.length || 0} 节点</Tag><Tag color="blue">初始:{item.initial}</Tag></Space>
                          </Space>} />
                      </Card>
                    </List.Item>
                  )} />}
            </>
          ),
        },
        {
          key: 'builtin', label: <span>📦 内置模板</span>,
          children: <BuiltinTemplates onInstalled={fetchData} msg={msg} />,
        },
        {
          key: 'instances', label: <span>▶ 运行中 ({instances.filter(i => i.status === 'running').length})</span>,
          children: <Table dataSource={instances} columns={instColumns} rowKey="id" pagination={{ pageSize: 10 }} size="small" />,
        },
      ]} />

      {/* Process modal */}
      <Modal title={currentInst?.title} open={processModal} onCancel={() => setProcessModal(false)}
        footer={currentInst?.status === 'running' ? (
          <Space><Button danger icon={<CloseCircleOutlined />} onClick={() => handleProceed('reject')} loading={processLoading}>驳回</Button>
            <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => handleProceed('approve')} loading={processLoading}>推进</Button></Space>
        ) : null} width={600}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="状态"><Tag color={STATUS_MAP[currentInst?.status]?.color}>{STATUS_MAP[currentInst?.status]?.label}</Tag></Descriptions.Item>
          <Descriptions.Item label="当前节点"><Tag color="blue">{currentInst?.current_node}</Tag></Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 16 }}>
          <Title level={5}>操作历史</Title>
          <Timeline items={instDetail?.nodes?.map((n: any) => ({
            color: n.action === 'approve' ? 'green' : n.action === 'reject' ? 'red' : 'blue',
            content: <span>{n.node_name} — {n.handler} <Tag>{n.action}</Tag></span>,
          })) || []} />
        </div>
      </Modal>
    </DashboardLayout>
  );
}

// --- Built-in Templates Component ---
function BuiltinTemplates({ onInstalled, msg }: { onInstalled: () => void; msg: any }) {
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => {
    api.get('/workflows/builtin').then((res: any) => {
      setList(res.data || res.results || res || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const install = async (name: string) => {
    setInstalling(name);
    try {
      await api.post(`/workflows/builtin/${encodeURIComponent(name)}`);
      msg.success(`已安装「${name}」`);
      onInstalled();
    } catch (err: any) {
      msg.error(err.response?.data?.error?.message || '安装失败');
    } finally { setInstalling(null); }
  };

  if (loading) return <Spin style={{ display: 'block', padding: 40 }} />;
  return (
    <Row gutter={[16, 16]}>
      {list.map((tpl: any) => (
        <Col key={tpl.name} xs={24} sm={12} lg={8}>
          <Card title={tpl.name} style={{ borderRadius: 8 }}
            extra={<Popconfirm title={`安装「${tpl.name}」？`} onConfirm={() => install(tpl.name)}>
              <Button size="small" icon={<DownloadOutlined />} loading={installing === tpl.name}>安装</Button>
            </Popconfirm>}>
            <Text type="secondary">{tpl.description}</Text>
            <div style={{ marginTop: 8 }}><Tag>{tpl.nodes?.length || 0} 个节点</Tag></div>
          </Card>
        </Col>
      ))}
    </Row>
  );
}
