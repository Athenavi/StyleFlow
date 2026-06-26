'use client';

import { useState, useEffect } from 'react';
import {
  Card, Typography, Tag, Button, Space, Spin, message,
  Row, Col, Select, Divider, Descriptions
} from 'antd';
import {
  SettingOutlined, CheckCircleOutlined, SwapOutlined,
  RobotOutlined, PictureOutlined, SaveOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

export default function AdminSettingsPage() {
  const [providers, setProviders] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // User's personal AI settings
  const [llmProvider, setLlmProvider] = useState('openai');
  const [llmModel, setLlmModel] = useState('gpt-4o');
  const [imageProvider, setImageProvider] = useState('sd_webui');
  const [imageModel, setImageModel] = useState('sd-xl');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [provRes, settingsRes] = await Promise.all([
        api.get('/admin/providers'),
        api.get('/admin/my-settings'),
      ]);
      setProviders(provRes);

      const us = provRes.user_settings || {};
      setLlmProvider(us.llm_provider || 'openai');
      setLlmModel(us.llm_model || 'gpt-4o');
      setImageProvider(us.image_provider || 'sd_webui');
      setImageModel(us.image_model || 'sd-xl');
    } catch { message.error('加载配置失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch('/admin/my-settings', {
        llm_provider: llmProvider,
        llm_model: llmModel,
        image_provider: imageProvider,
        image_model: imageModel,
      });
      message.success('个人 AI 配置已保存');
      fetchData();
    } catch { message.error('保存失败'); }
    finally { setSaving(false); }
  };

  const getLlmModels = () => {
    const p = providers?.llm?.find((x: any) => x.name === llmProvider || x.provider === llmProvider);
    return p?.models || [llmModel];
  };

  const getImageModels = () => {
    const p = providers?.image?.find((x: any) => x.name === imageProvider || x.provider === imageProvider);
    return p?.models || [imageModel];
  };

  if (loading) {
    return <DashboardLayout><div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <Title level={3}>
        <SettingOutlined style={{ marginRight: 8 }} />
        我的 AI 模型配置
      </Title>

      <Row gutter={[24, 24]}>
        {/* LLM Settings */}
        <Col xs={24} lg={12}>
          <Card title={<><RobotOutlined /> 语言模型 (LLM)</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>提供商</Text>
                <Select
                  value={llmProvider}
                  onChange={(v) => { setLlmProvider(v); setLlmModel(''); }}
                  style={{ width: '100%', marginTop: 4 }}
                  options={providers?.llm?.filter((p: any) => p.configured).map((p: any) => ({
                    value: p.provider,
                    label: p.label,
                  }))}
                />
              </div>
              <div>
                <Text strong>模型</Text>
                <Select
                  value={llmModel}
                  onChange={setLlmModel}
                  style={{ width: '100%', marginTop: 4 }}
                  options={getLlmModels().map((m: string) => ({ value: m, label: m }))}
                />
              </div>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
                block
              >
                保存我的配置
              </Button>
            </Space>
          </Card>
        </Col>

        {/* Image Settings */}
        <Col xs={24} lg={12}>
          <Card title={<><PictureOutlined /> 图像生成模型</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>提供商</Text>
                <Select
                  value={imageProvider}
                  onChange={(v) => { setImageProvider(v); setImageModel(''); }}
                  style={{ width: '100%', marginTop: 4 }}
                  options={providers?.image?.filter((p: any) => p.configured).map((p: any) => ({
                    value: p.provider,
                    label: p.label,
                  }))}
                />
              </div>
              <div>
                <Text strong>模型</Text>
                <Select
                  value={imageModel}
                  onChange={setImageModel}
                  style={{ width: '100%', marginTop: 4 }}
                  options={getImageModels().map((m: string) => ({ value: m, label: m }))}
                />
              </div>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
                block
              >
                保存我的配置
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* System available providers */}
      <Title level={5}>系统可用提供商</Title>
      <Row gutter={[16, 16]}>
        {[...(providers?.llm || []), ...(providers?.image || [])].map((p: any) => (
          <Col key={p.name} xs={12} sm={8} lg={6}>
            <Card size="small" style={{ borderRadius: 8 }}>
              <Space direction="vertical" size={4}>
                <Text strong>{p.label}</Text>
                <Tag>{p.provider}</Tag>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {p.configured ? '✅ 已配置' : '⚠️ 未配置'}
                </Text>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </DashboardLayout>
  );
}
