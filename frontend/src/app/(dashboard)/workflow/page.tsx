'use client';

import { useState, useEffect } from 'react';
import {
  Card, Button, Typography, Space, message, Spin, Empty, App,
  Modal, Input, Tag, List, Tooltip, Popconfirm
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ApartmentOutlined,
  CopyOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

const { Title, Text } = Typography;

export default function WorkflowDefsPage() {
  const { message: msg } = App.useApp();
  const [defs, setDefs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchDefs = async () => {
    setLoading(true);
    try {
      const res: any = await api.get('/workflows/definitions');
      setDefs(res.data || res.results || res || []);
    } catch { msg.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchDefs(); }, []);

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/workflows/definitions/${id}`);
      msg.success('已删除');
      fetchDefs();
    } catch { msg.error('删除失败'); }
  };

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />工作流管理
        </Title>
        <Button type="primary" icon={<PlusOutlined />}
          onClick={() => router.push('/workflow/editor')}>
          新建工作流
        </Button>
      </div>

      {loading ? <Spin style={{ display: 'block', padding: 80 }} /> : defs.length === 0 ? (
        <Empty description="暂无工作流定义">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => router.push('/workflow/editor')}>
            创建第一个工作流
          </Button>
        </Empty>
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, lg: 3 }}
          dataSource={defs}
          renderItem={(item: any) => (
            <List.Item>
              <Card
                hoverable
                actions={[
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
    </DashboardLayout>
  );
}
