'use client';

import { useState, useEffect } from 'react';
import { Card, Typography, Spin, Tag, Space, Timeline, Button, App } from 'antd';
import { ArrowRightOutlined, ApartmentOutlined, RollbackOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';

const { Title, Text } = Typography;

export default function WorkflowDetailPage() {
  const { message: msg } = App.useApp();
  const params = useParams();
  const router = useRouter();
  const [def, setDef] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/workflows/definitions/${params?.id}`)
      .then((res: any) => setDef(res.data || res))
      .catch(() => msg.error('加载失败'))
      .finally(() => setLoading(false));
  }, [params?.id]);

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;
  if (!def) return <DashboardLayout>未找到</DashboardLayout>;

  return (
    <DashboardLayout>
      <Space style={{ marginBottom: 16 }}>
        <Button onClick={() => router.push('/workflow')}>← 返回</Button>
        <Button onClick={() => router.push(`/workflow/editor?id=${def.id}`)}>编辑</Button>
      </Space>

      <Card title={<><ApartmentOutlined /> {def.name}</>} style={{ borderRadius: 8 }}>
        <Text type="secondary">{def.description || '无描述'}</Text>
        <div style={{ marginTop: 16 }}>
          <Text>起始节点: <Tag color="blue">{def.initial}</Tag></Text>
          <Text style={{ marginLeft: 16 }}>节点数: <Tag>{def.nodes?.length}</Tag></Text>
        </div>

        <Timeline style={{ marginTop: 24 }} items={def.nodes?.map((n: any) => ({
          color: n.name === def.initial ? 'blue' : 'gray',
          children: <Card size="small" style={{ borderRadius: 6 }}>
              <Space direction="vertical" size={4}>
                <Space><Text strong>{n.label}</Text><Tag>{n.name}</Tag>{n.auto_proceed && <Tag color="green">自动</Tag>}</Space>
                <Space>
                  {n.handler_role?.map((r: string) => <Tag key={r} color="blue">{r}</Tag>)}
                </Space>
                <Space>
                  {n.next?.length > 0 && <><Text type="secondary">→</Text> {n.next.map((x: string) => <Tag key={x} color="success">{x}</Tag>)}</>}
                  {n.reject_to && <><RollbackOutlined style={{ color: '#ff4d4f' }} /><Tag color="error">{n.reject_to}</Tag></>}
                </Space>
              </Space>
            </Card>,
        })) || []} />
      </Card>
    </DashboardLayout>
  );
}
