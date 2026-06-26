'use client';

import { useState, useEffect } from 'react';
import {
  Card, Button, Typography, Space, message, Spin, Input, App,
  Tag, Divider, Select, Switch, Modal, Tooltip, Row, Col
} from 'antd';
import { PlusOutlined, SaveOutlined, ArrowRightOutlined,
  DeleteOutlined, EditOutlined, ApartmentOutlined, RollbackOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';
import { useRouter, useSearchParams } from 'next/navigation';

const { Title, Text } = Typography;

const ROLE_OPTIONS = [
  { value: 'designer', label: '设计师' },
  { value: 'pattern_maker', label: '版师' },
  { value: 'accountant', label: '财务' },
  { value: 'admin', label: '管理员' },
];

interface NodeDef {
  name: string;
  label: string;
  handler_role: string[];
  auto_proceed: boolean;
  next: string[];
  reject_to?: string;
}

export default function WorkflowEditorPage() {
  const { message: msg } = App.useApp();
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams?.get('id');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [initial, setInitial] = useState('start');
  const [nodes, setNodes] = useState<NodeDef[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(!!editId);

  // Editing node modal
  const [nodeModal, setNodeModal] = useState(false);
  const [editIdx, setEditIdx] = useState<number | null>(null);
  const [nodeForm, setNodeForm] = useState<NodeDef>({
    name: '', label: '', handler_role: [], auto_proceed: false, next: [], reject_to: '',
  });

  useEffect(() => {
    if (editId) {
      api.get(`/workflows/definitions/${editId}`).then((res: any) => {
        const d = res.data || res;
        setName(d.name); setDescription(d.description || '');
        setInitial(d.initial); setNodes(d.nodes || []);
      }).catch(() => msg.error('加载失败')).finally(() => setLoading(false));
    }
  }, [editId]);

  const openNodeModal = (idx: number | null) => {
    if (idx !== null) {
      setNodeForm({ ...nodes[idx] });
      setEditIdx(idx);
    } else {
      setNodeForm({ name: '', label: '', handler_role: [], auto_proceed: false, next: [], reject_to: '' });
      setEditIdx(null);
    }
    setNodeModal(true);
  };

  const saveNode = () => {
    if (!nodeForm.name || !nodeForm.label) {
      msg.warning('请填写节点名称和标签'); return;
    }
    const updated = [...nodes];
    if (editIdx !== null) {
      updated[editIdx] = { ...nodeForm };
    } else {
      updated.push({ ...nodeForm });
    }
    setNodes(updated);
    setNodeModal(false);
  };

  const deleteNode = (idx: number) => {
    const name = nodes[idx].name;
    setNodes(nodes.filter((_, i) => i !== idx));
    // 清理其他节点对此节点的引用
    setNodes(prev => prev.map(n => ({
      ...n,
      next: n.next.filter(x => x !== name),
      reject_to: n.reject_to === name ? undefined : n.reject_to,
    })));
  };

  const moveNode = (idx: number, dir: -1 | 1) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= nodes.length) return;
    const arr = [...nodes];
    [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
    setNodes(arr);
  };

  const handleSave = async () => {
    if (!name) { msg.warning('请输入工作流名称'); return; }
    if (nodes.length < 2) { msg.warning('至少需要2个节点'); return; }
    setSaving(true);
    try {
      const body = { name, description, initial, nodes };
      if (editId) {
        await api.put(`/workflows/definitions/${editId}`, body);
        msg.success('已更新');
      } else {
        await api.post('/workflows/definitions', body);
        msg.success('已创建');
      }
      router.push('/workflow');
    } catch (err: any) {
      msg.error(err.response?.data?.error?.message || '保存失败');
    } finally { setSaving(false); }
  };

  const allNodeNames = nodes.map(n => n.name);

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />
          {editId ? '编辑工作流' : '新建工作流'}
        </Title>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>
          保存
        </Button>
      </div>

      <Row gutter={16}>
        <Col xs={24} lg={6}>
          <Card title="基本信息" size="small" style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div>
                <Text type="secondary">名称</Text>
                <Input value={name} onChange={e => setName(e.target.value)} placeholder="款式开发" />
              </div>
              <div>
                <Text type="secondary">描述</Text>
                <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="工作流描述" />
              </div>
              <div>
                <Text type="secondary">起始节点</Text>
                <Select value={initial} onChange={setInitial} style={{ width: '100%' }}
                  options={allNodeNames.map(n => ({ value: n, label: n }))} />
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={18}>
          <Card title={
            <Space>
              <span>节点列表</span>
              <Tag>{nodes.length} 个</Tag>
            </Space>
          } extra={<Button size="small" icon={<PlusOutlined />} onClick={() => openNodeModal(null)}>添加节点</Button>}
            style={{ borderRadius: 8 }}>
            {nodes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                暂无节点，点击「添加节点」开始构建工作流
              </div>
            ) : (
              <Space direction="vertical" style={{ width: '100%' }} size={8}>
                {nodes.map((node, idx) => (
                  <Card key={idx} size="small" style={{ borderRadius: 6, borderLeft: '3px solid #1677ff' }}
                    extra={
                      <Space size={4}>
                        <Tooltip title="上移"><Button size="small" disabled={idx === 0} onClick={() => moveNode(idx, -1)}>↑</Button></Tooltip>
                        <Tooltip title="下移"><Button size="small" disabled={idx === nodes.length - 1} onClick={() => moveNode(idx, 1)}>↓</Button></Tooltip>
                        <Tooltip title="编辑"><Button size="small" icon={<EditOutlined />} onClick={() => openNodeModal(idx)} /></Tooltip>
                        <Tooltip title="删除"><Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteNode(idx)} /></Tooltip>
                      </Space>
                    }>
                    <Space direction="vertical" size={4}>
                      <Space>
                        <Text strong>{node.label}</Text>
                        <Tag>{node.name}</Tag>
                        {node.auto_proceed && <Tag color="green">自动推进</Tag>}
                      </Space>
                      <Space>
                        {node.handler_role.map(r => <Tag key={r} color="blue">{r}</Tag>)}
                      </Space>
                      <Space>
                        <Text type="secondary">→ 下一步: </Text>
                        {node.next.map(n => <Tag key={n} color="success">{n}</Tag>)}
                        {node.reject_to && <><Text type="secondary">驳回→ </Text><Tag color="error">{node.reject_to}</Tag></>}
                        {idx < nodes.length - 1 && <ArrowRightOutlined style={{ color: '#ddd' }} />}
                      </Space>
                    </Space>
                  </Card>
                ))}
              </Space>
            )}
          </Card>
        </Col>
      </Row>

      {/* 节点编辑弹窗 */}
      <Modal title={editIdx !== null ? '编辑节点' : '添加节点'} open={nodeModal}
        onOk={saveNode} onCancel={() => setNodeModal(false)} width={500}>
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          <div>
            <Text type="secondary">节点标识 (name)</Text>
            <Input value={nodeForm.name} onChange={e => setNodeForm({ ...nodeForm, name: e.target.value })}
              placeholder="如: design, review" />
          </div>
          <div>
            <Text type="secondary">显示标签 (label)</Text>
            <Input value={nodeForm.label} onChange={e => setNodeForm({ ...nodeForm, label: e.target.value })}
              placeholder="如: 设计出款, 设计评审" />
          </div>
          <div>
            <Text type="secondary">处理角色</Text>
            <Select mode="multiple" value={nodeForm.handler_role} onChange={v => setNodeForm({ ...nodeForm, handler_role: v })}
              style={{ width: '100%' }} options={ROLE_OPTIONS} />
          </div>
          <div>
            <Text type="secondary">自动推进 <Switch size="small" checked={nodeForm.auto_proceed}
              onChange={v => setNodeForm({ ...nodeForm, auto_proceed: v })} /></Text>
          </div>
          <div>
            <Text type="secondary">下一步节点</Text>
            <Select mode="multiple" value={nodeForm.next} onChange={v => setNodeForm({ ...nodeForm, next: v })}
              style={{ width: '100%' }} options={allNodeNames.filter(n => n !== nodeForm.name).map(n => ({ value: n, label: n }))} />
          </div>
          <div>
            <Text type="secondary">驳回目标</Text>
            <Select value={nodeForm.reject_to || undefined} onChange={v => setNodeForm({ ...nodeForm, reject_to: v || '' })}
              style={{ width: '100%' }} allowClear
              options={allNodeNames.filter(n => n !== nodeForm.name).map(n => ({ value: n, label: n }))} />
          </div>
        </Space>
      </Modal>
    </DashboardLayout>
  );
}
