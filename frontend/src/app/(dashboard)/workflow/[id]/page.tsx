'use client';

import { useState, useEffect } from 'react';
import {
  Card, Typography, Spin, Tag, Space, Timeline, Button, App,
  Descriptions, Divider, message as Msg
} from 'antd';
import { ArrowRightOutlined, ApartmentOutlined,
  PlayCircleOutlined, EditOutlined, RollbackOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';

const { Title, Text } = Typography;

export default function WorkflowDetailPage() {
  const { message } = App.useApp();
  const params = useParams();
  const router = useRouter();
  const [def, setDef] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    api.get(`/workflows/definitions/${params?.id}`)
      .then((res: any) => setDef(res.data || res))
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false));
  }, [params?.id]);

  const handleStart = async () => {
    setStarting(true);
    try {
      const res: any = await api.post('/workflows', {
        definition_id: def.id,
        title: def.name + ' ' + new Date().toLocaleString('zh-CN'),
      });
      message.success('工作流已启动');
      router.push('/workflow');
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '启动失败');
    } finally { setStarting(false); }
  };

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;
  if (!def) return <DashboardLayout>未找到</DashboardLayout>;

  return (
    <DashboardLayout>
      <Space style={{ marginBottom: 16 }}>
        <Button onClick={() => router.push('/workflow')}>← 返回</Button>
        <Button icon={<EditOutlined />} onClick={() => router.push(`/workflow/editor?id=${def.id}`)}>编辑</Button>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart} loading={starting}>
          启动工作流
        </Button>
      </Space>

      <Card style={{ borderRadius: 8 }}>
        <Title level={4}><ApartmentOutlined /> {def.name}</Title>
        <Descriptions column={3} size="small">
          <Descriptions.Item label="描述">{def.description || '无'}</Descriptions.Item>
          <Descriptions.Item label="起始节点"><Tag color="blue">{def.initial}</Tag></Descriptions.Item>
          <Descriptions.Item label="节点数"><Tag>{def.nodes?.length}</Tag></Descriptions.Item>
        </Descriptions>

        <Divider />

        <Title level={5}>流程步骤</Title>
        <Timeline items={def.nodes?.map((n: any) => ({
          color: n.name === def.initial ? 'blue' : 'gray',
          children: <Card size="small" style={{ borderRadius: 6, borderLeft: '3px solid #1677ff' }}>
              <Space direction="vertical" size={4}>
                <Space wrap>
                  <Text strong>{n.label}</Text>
                  <Tag>{n.name}</Tag>
                  {n.auto_proceed && <Tag color="green">自动推进</Tag>}
                </Space>
                <Space wrap>
                  {n.handler_role?.map((r: string) => <Tag key={r} color="blue">{r}</Tag>)}
                </Space>
                <Space wrap>
                  {n.next?.length > 0 && <><Text type="secondary">✅ 通过 →</Text> {n.next.map((x: string) => <Tag key={x} color="success">{x}</Tag>)}</>}
                  {n.reject_to && <><RollbackOutlined style={{ color: '#ff4d4f' }} /><Text type="secondary">驳回 →</Text><Tag color="error">{n.reject_to}</Tag></>}
                </Space>
              </Space>
            </Card>,
        })) || []} />
      </Card>
    </DashboardLayout>
  );
}
