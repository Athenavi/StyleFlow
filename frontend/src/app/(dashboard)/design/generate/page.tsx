'use client';

import { useState } from 'react';
import {
  Input, Button, Card, Select, Slider, Row, Col, Tag, message,
  Space, Typography, Spin, Divider, Image, Tooltip, Empty
} from 'antd';
import {
  ThunderboltOutlined, DownloadOutlined, StarOutlined,
  ReloadOutlined, SettingOutlined, PictureOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { TextArea } = Input;
const { Title, Text } = Typography;

const TEMPLATES: Record<string, { label: string; desc: string }> = {
  style: { label: '款式图', desc: '白底正面款式图，适合设计稿归档' },
  flat: { label: '平铺图', desc: '技术线稿风格，无阴影' },
  model: { label: '模特穿搭', desc: '模特身着效果，摄影棚布光' },
  fabric: { label: '面料特写', desc: '面料纹理细节特写' },
  sketch: { label: '手绘草图', desc: '设计手稿风格，概念草图' },
};

const CATEGORIES = [
  { value: 'style', label: '款式图' },
  { value: 'sketch', label: '线稿' },
  { value: 'fabric', label: '面料图' },
  { value: 'moodboard', label: '灵感板' },
  { value: 'flatten', label: '平铺图' },
];

export default function DesignGeneratePage() {
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [template, setTemplate] = useState('style');
  const [category, setCategory] = useState('style');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(768);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      message.warning('请输入提示词');
      return;
    }

    setLoading(true);
    setResults([]);
    try {
      const res: any = await api.post('/designs/generate', {
        prompt: prompt.trim(),
        negative_prompt: negativePrompt,
        category,
        width,
        height,
        template,
        title: prompt.trim().slice(0, 50),
      });

      const tid = res.task_id;
      setTaskId(tid);

      // Poll for result
      const poll = setInterval(async () => {
        try {
          const statusRes: any = await api.get(`/designs/tasks/${tid}`);
          if (statusRes.status === 'SUCCESS' && statusRes.result) {
            setResults((prev) => [statusRes.result, ...prev]);
            setLoading(false);
            clearInterval(poll);
            message.success('生成完成！');
          } else if (statusRes.status === 'FAILURE') {
            setLoading(false);
            clearInterval(poll);
            message.error(statusRes.error || '生成失败');
          }
        } catch {
          clearInterval(poll);
          setLoading(false);
        }
      }, 1500);

      // Timeout after 120s
      setTimeout(() => {
        clearInterval(poll);
        setLoading(false);
      }, 120000);
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '提交生成任务失败');
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <Title level={3}>
        <ThunderboltOutlined style={{ marginRight: 8 }} />
        AI 设计生成
      </Title>

      <Row gutter={24}>
        {/* Left: Input Panel */}
        <Col xs={24} lg={10}>
          <Card style={{ borderRadius: 12 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>提示词 *</Text>
                <TextArea
                  rows={4}
                  placeholder="描述您想要的服装设计，如：一件优雅的夏季连衣裙，V领，及膝，花卉图案"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  style={{ marginTop: 4 }}
                />
              </div>

              <div>
                <Text strong>生成模板</Text>
                <Select
                  value={template}
                  onChange={setTemplate}
                  style={{ width: '100%', marginTop: 4 }}
                  options={Object.entries(TEMPLATES).map(([k, v]) => ({
                    value: k,
                    label: `${v.label} - ${v.desc}`,
                  }))}
                />
              </div>

              <div>
                <Text strong>款式分类</Text>
                <Select
                  value={category}
                  onChange={setCategory}
                  style={{ width: '100%', marginTop: 4 }}
                  options={CATEGORIES}
                />
              </div>

              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleGenerate}
                loading={loading}
                block
                size="large"
                style={{ height: 48, borderRadius: 8 }}
              >
                {loading ? '生成中...' : '生成设计'}
              </Button>

              <Divider style={{ margin: '8px 0' }} />

              <Tooltip title="展开高级参数">
                <Button
                  type="text"
                  icon={<SettingOutlined />}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  block
                >
                  {showAdvanced ? '收起' : '展开'}高级参数
                </Button>
              </Tooltip>

              {showAdvanced && (
                <Space direction="vertical" style={{ width: '100%' }} size="small">
                  <div>
                    <Text type="secondary">负面提示词</Text>
                    <TextArea
                      rows={2}
                      placeholder="不想出现的内容..."
                      value={negativePrompt}
                      onChange={(e) => setNegativePrompt(e.target.value)}
                      style={{ marginTop: 4 }}
                    />
                  </div>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Text type="secondary">宽度: {width}</Text>
                      <Slider min={256} max={1024} step={64} value={width} onChange={setWidth} />
                    </Col>
                    <Col span={12}>
                      <Text type="secondary">高度: {height}</Text>
                      <Slider min={256} max={1024} step={64} value={height} onChange={setHeight} />
                    </Col>
                  </Row>
                </Space>
              )}
            </Space>
          </Card>
        </Col>

        {/* Right: Results */}
        <Col xs={24} lg={14}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '80px 0' }}>
              <Spin size="large" tip="AI 正在创作中..." />
            </div>
          )}

          {!loading && results.length === 0 && (
            <div style={{ textAlign: 'center', padding: '80px 0' }}>
              <PictureOutlined style={{ fontSize: 64, color: '#ddd' }} />
              <Title level={4} type="secondary" style={{ marginTop: 16 }}>
                输入提示词，点击「生成设计」
              </Title>
              <Text type="secondary">AI 将根据您的描述生成服装设计稿</Text>
            </div>
          )}

          {results.length > 0 && (
            <div>
              <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 12 }}>
                生成结果
              </Text>
              <Row gutter={[16, 16]}>
                {results.map((item, idx) => (
                  <Col key={idx} xs={24} sm={12}>
                    <Card
                      hoverable
                      cover={
                        <Image
                          alt={item.title}
                          src={item.image_url}
                          style={{ objectFit: 'cover', height: 300 }}
                          fallback="data:image/png;base64,iVBORw0KGgo..."
                        />
                      }
                      actions={[
                        <Tooltip title="收藏" key="star">
                          <StarOutlined />
                        </Tooltip>,
                        <Tooltip title="下载" key="download">
                          <DownloadOutlined />
                        </Tooltip>,
                        <Tooltip title="再次生成" key="retry">
                          <ReloadOutlined />
                        </Tooltip>,
                      ]}
                    >
                      <Card.Meta
                        title={item.title || `设计稿 #${item.id}`}
                        description={
                          <Space>
                            <Tag>{CATEGORIES.find(c => c.value === item.category)?.label || item.category}</Tag>
                            <Tag color="green">已完成</Tag>
                          </Space>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}
        </Col>
      </Row>
    </DashboardLayout>
  );
}
