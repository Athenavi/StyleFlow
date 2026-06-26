'use client';

import { useState, useEffect } from 'react';
import {
  Table, Card, Button, Tag, Typography, Space, message, Spin,
  Modal, Descriptions, Input, Select
} from 'antd';
import { FileTextOutlined, PlusOutlined, ThunderboltOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  draft: { color: 'default', label: '草稿' },
  review: { color: 'processing', label: '审核中' },
  approved: { color: 'success', label: '已批准' },
};

export default function TechpackPage() {
  const [techpacks, setTechpacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [genDesignId, setGenDesignId] = useState('');
  const [generating, setGenerating] = useState(false);

  const fetchTechpacks = async () => {
    setLoading(true);
    try {
      const res: any = await api.get('/techpacks');
      setTechpacks(res.data || res.results || res || []);
    } catch { message.error('加载工艺单失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTechpacks(); }, []);

  const showDetail = (tp: any) => {
    setSelected(tp);
    setDetailVisible(true);
  };

  const handleGenerate = async () => {
    if (!genDesignId) { message.warning('请输入设计稿ID'); return; }
    setGenerating(true);
    try {
      const res: any = await api.post(`/techpacks/generate?design_id=${genDesignId}`);
      message.success(`工艺单 #${res.id} 已生成`);
      setGenDesignId('');
      fetchTechpacks();
    } catch { message.error('生成失败'); }
    finally { setGenerating(false); }
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '款号', dataIndex: 'style_code', key: 'style_code' },
    { title: '品类', dataIndex: 'category', key: 'category' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const st = STATUS_MAP[s] || { color: 'default', label: s };
        return <Tag color={st.color}>{st.label}</Tag>;
      },
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Button type="link" onClick={() => showDetail(record)}>查看</Button>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <FileTextOutlined style={{ marginRight: 8 }} />工艺单管理
        </Title>
        <Space>
          <Input
            placeholder="设计稿ID"
            value={genDesignId}
            onChange={(e) => setGenDesignId(e.target.value)}
            style={{ width: 160 }}
          />
          <Button icon={<ThunderboltOutlined />} onClick={handleGenerate} loading={generating}>
            AI 生成工艺单
          </Button>
        </Space>
      </div>

      <Card style={{ borderRadius: 8 }}>
        {loading ? <Spin style={{ display: 'block', padding: 40 }} /> :
          <Table
            dataSource={techpacks}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 15 }}
          />
        }
      </Card>

      <Modal
        title={selected?.title}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={600}
      >
        {selected && (
          <Descriptions column={2} size="small" layout="vertical">
            <Descriptions.Item label="标题">{selected.title}</Descriptions.Item>
            <Descriptions.Item label="款号">{selected.style_code || '-'}</Descriptions.Item>
            <Descriptions.Item label="品类">{selected.category || '-'}</Descriptions.Item>
            <Descriptions.Item label="面料说明">{selected.fabric_description || '-'}</Descriptions.Item>
            <Descriptions.Item label="工序" span={2}>
              {selected.process_steps?.length > 0
                ? selected.process_steps.map((s: any, i: number) => (
                    <Tag key={i}>{s.process_name || s}</Tag>
                  ))
                : '无'}
            </Descriptions.Item>
            <Descriptions.Item label="尺码表" span={2}>
              {selected.size_spec ? JSON.stringify(selected.size_spec) : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </DashboardLayout>
  );
}
