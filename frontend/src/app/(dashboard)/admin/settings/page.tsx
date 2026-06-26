'use client';

import { useState, useEffect } from 'react';
import {
  Card, Typography, Input, Button, Space, Spin, message,
  Row, Col, Table, Tag
} from 'antd';
import { SaveOutlined, RobotOutlined, PictureOutlined, LinkOutlined, KeyOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

// 常见 API 参考表
const REFERENCE_DATA = [
  { provider: 'OpenAI', api_base: 'https://api.openai.com/v1', models: 'gpt-4o, gpt-4o-mini', docs: 'https://platform.openai.com/docs' },
  { provider: 'Anthropic Claude', api_base: 'https://api.anthropic.com', models: 'claude-sonnet-4, claude-3-haiku', docs: 'https://docs.anthropic.com' },
  { provider: '阿里通义千问', api_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', models: 'qwen-max, qwen-plus, qwen-turbo', docs: 'https://help.aliyun.com/zh/model-studio' },
  { provider: 'DeepSeek', api_base: 'https://api.deepseek.com', models: 'deepseek-chat, deepseek-reasoner', docs: 'https://platform.deepseek.com/docs' },
  { provider: 'Groq', api_base: 'https://api.groq.com/openai/v1', models: 'llama-3.3-70b, mixtral-8x7b', docs: 'https://console.groq.com/docs' },
  { provider: 'Stable Diffusion', api_base: 'http://localhost:7860', models: 'sd-xl, sd-3.5', docs: 'https://github.com/AUTOMATIC1111/stable-diffusion-webui' },
];

const refColumns = [
  { title: '提供商', dataIndex: 'provider', key: 'provider', width: 130 },
  { title: 'API 地址', dataIndex: 'api_base', key: 'api_base', render: (v: string) => <code style={{ fontSize: 12 }}>{v}</code> },
  { title: '常用模型', dataIndex: 'models', key: 'models' },
  { title: '文档', dataIndex: 'docs', key: 'docs', render: (v: string) => <a href={v} target="_blank" rel="noreferrer">查看 <LinkOutlined /></a> },
];

export default function AdminSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // LLM
  const [llmModel, setLlmModel] = useState('');
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmKey, setLlmKey] = useState('');
  const [llmKeyMask, setLlmKeyMask] = useState('');

  // Image
  const [imgModel, setImgModel] = useState('');
  const [imgBaseUrl, setImgBaseUrl] = useState('');
  const [imgKey, setImgKey] = useState('');
  const [imgKeyMask, setImgKeyMask] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const s: any = await api.get('/admin/my-settings');
      setLlmModel(s.llm_model || '');
      setLlmBaseUrl(s.llm_api_base_url || '');
      setLlmKeyMask(s.llm_api_key_masked || '');
      setImgModel(s.image_model || '');
      setImgBaseUrl(s.image_api_base_url || '');
      setImgKeyMask(s.image_api_key_masked || '');
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const body: any = { llm_model: llmModel, llm_api_base_url: llmBaseUrl, image_model: imgModel, image_api_base_url: imgBaseUrl };
      if (llmKey) body.llm_api_key = llmKey;
      if (imgKey) body.image_api_key = imgKey;
      await api.patch('/admin/my-settings', body);
      message.success('已保存');
      setLlmKey(''); setImgKey('');
      fetchData();
    } catch { message.error('保存失败'); }
    finally { setSaving(false); }
  };

  if (loading) return <DashboardLayout><div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div></DashboardLayout>;

  return (
    <DashboardLayout>
      <Title level={3}><RobotOutlined style={{ marginRight: 8 }} />AI 模型设置</Title>

      <Row gutter={24}>
        {/* 对话模型 */}
        <Col xs={24} lg={12}>
          <Card title={<><RobotOutlined /> 对话模型</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text type="secondary"><LinkOutlined /> API 地址</Text>
                <Input value={llmBaseUrl} onChange={e => setLlmBaseUrl(e.target.value)}
                  placeholder="留空用默认地址（如 https://api.openai.com/v1）" />
              </div>
              <div>
                <Text type="secondary"><Tag>模型名称</Tag></Text>
                <Input value={llmModel} onChange={e => setLlmModel(e.target.value)}
                  placeholder="如 gpt-4o, claude-sonnet-4, qwen-max" />
              </div>
              <div>
                <Text type="secondary"><KeyOutlined /> API Key {llmKeyMask && <Tag style={{ fontSize: 11 }}>{llmKeyMask}</Tag>}</Text>
                <Input.Password value={llmKey} onChange={e => setLlmKey(e.target.value)}
                  placeholder={llmKeyMask ? '留空则沿用已有 Key' : '输入 API Key'} />
              </div>
            </Space>
          </Card>
        </Col>

        {/* 图像模型 */}
        <Col xs={24} lg={12}>
          <Card title={<><PictureOutlined /> 图像模型</>} style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text type="secondary"><LinkOutlined /> API 地址</Text>
                <Input value={imgBaseUrl} onChange={e => setImgBaseUrl(e.target.value)}
                  placeholder="留空用默认（如 http://localhost:7860）" />
              </div>
              <div>
                <Text type="secondary"><Tag>模型名称</Tag></Text>
                <Input value={imgModel} onChange={e => setImgModel(e.target.value)}
                  placeholder="如 sd-xl, wanx-v1" />
              </div>
              <div>
                <Text type="secondary"><KeyOutlined /> API Key {imgKeyMask && <Tag style={{ fontSize: 11 }}>{imgKeyMask}</Tag>}</Text>
                <Input.Password value={imgKey} onChange={e => setImgKey(e.target.value)}
                  placeholder={imgKeyMask ? '留空则沿用已有 Key' : '输入 API Key'} />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}
        size="large" style={{ marginTop: 24, width: '100%', height: 48, borderRadius: 8 }}>
        保存配置
      </Button>

      {/* 参考表 */}
      <Card title="常见 API 参考" style={{ marginTop: 24, borderRadius: 8 }}>
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          以下为常见 AI 服务的 API 地址和模型名称，可直接复制填入上方设置。
        </Text>
        <Table dataSource={REFERENCE_DATA} columns={refColumns} rowKey="provider"
          pagination={false} size="small" />
      </Card>
    </DashboardLayout>
  );
}
