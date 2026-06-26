'use client';

import { useState, useEffect } from 'react';
import {
  Card, Typography, Tag, Button, Space, Spin, message, Row, Col, Descriptions, Divider
} from 'antd';
import {
  SettingOutlined, CheckCircleOutlined, SwapOutlined,
  RobotOutlined, PictureOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

export default function AdminSettingsPage() {
  const [providers, setProviders] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const res: any = await api.get('/admin/providers');
      setProviders(res);
    } catch { message.error('加载配置失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchProviders(); }, []);

  const handleSwitch = async (name: string) => {
    setSwitching(true);
    try {
      await api.post('/admin/providers/switch', { provider_name: name });
      message.success(`已切换到 ${name}`);
      fetchProviders();
    } catch { message.error('切换失败'); }
    finally { setSwitching(false); }
  };

  if (loading) {
    return <DashboardLayout><div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <Title level={3}>
        <SettingOutlined style={{ marginRight: 8 }} />
        AI 模型配置
      </Title>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title={<><RobotOutlined /> LLM 语言模型</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {providers?.llm?.map((p: any) => (
                <Card
                  key={p.name}
                  size="small"
                  style={{
                    borderRadius: 8,
                    border: p.name === providers?.active_llm ? '2px solid #52c41a' : '1px solid #f0f0f0',
                  }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong>{p.label}</Text>
                      <Space>
                        {p.name === providers?.active_llm && <Tag color="green"><CheckCircleOutlined /> 当前使用</Tag>}
                        <Tag>{p.provider}</Tag>
                      </Space>
                    </div>
                    <Descriptions size="small" column={2}>
                      <Descriptions.Item label="模型">{p.model}</Descriptions.Item>
                      <Descriptions.Item label="状态">
                        {p.configured
                          ? <Tag color="success">已配置</Tag>
                          : <Tag color="warning">未配置</Tag>}
                      </Descriptions.Item>
                    </Descriptions>
                    {p.models?.length > 0 && (
                      <Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>可用模型: </Text>
                        {p.models.map((m: string) => <Tag key={m} style={{ fontSize: 11 }}>{m}</Tag>)}
                      </Space>
                    )}
                    {p.name !== providers?.active_llm && p.configured && (
                      <Button
                        type="primary"
                        ghost
                        size="small"
                        icon={<SwapOutlined />}
                        onClick={() => handleSwitch(p.name)}
                        loading={switching}
                      >
                        切换到此模型
                      </Button>
                    )}
                  </Space>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={<><PictureOutlined /> 图像生成模型</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {providers?.image?.map((p: any) => (
                <Card key={p.name} size="small" style={{ borderRadius: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text strong>{p.label}</Text>
                      <Tag>{p.provider}</Tag>
                    </div>
                    <Descriptions size="small" column={2}>
                      <Descriptions.Item label="模型">{p.model}</Descriptions.Item>
                      <Descriptions.Item label="状态">
                        {p.configured
                          ? <Tag color="success">已配置</Tag>
                          : <Tag color="warning">未配置</Tag>}
                      </Descriptions.Item>
                    </Descriptions>
                  </Space>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </DashboardLayout>
  );
}
