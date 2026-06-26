'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Card, Row, Col, Button, Upload, Select, Image, Tag, Space,
  Typography, App, Spin, Divider, Empty, Modal, Tooltip, Alert
} from 'antd';
import {
  ThunderboltOutlined, UploadOutlined, PictureOutlined,
  HistoryOutlined, ReloadOutlined, DownloadOutlined,
  FolderOpenOutlined, BulbOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

// 示例图片（来自 picsum 免费占位图）
const SAMPLES = {
  person: 'https://picsum.photos/seed/person1/400/600',
  garment: {
    upper: 'https://picsum.photos/seed/upper1/400/400',
    lower: 'https://picsum.photos/seed/lower1/400/400',
    dress: 'https://picsum.photos/seed/dress1/400/500',
    outer: 'https://picsum.photos/seed/outer1/400/400',
  },
};

const TIPS = {
  person: '建议上传正面全身照，背景简洁，光线均匀',
  garment: '建议上传单品平铺图，背景干净，款式清晰',
};

export default function TryonPage() {
  const { message } = App.useApp();
  const [personUrl, setPersonUrl] = useState('');
  const [garmentUrl, setGarmentUrl] = useState('');
  const [category, setCategory] = useState('upper');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [mediaPicker, setMediaPicker] = useState<{ type: 'person' | 'garment'; visible: boolean }>({ type: 'person', visible: false });
  const [mediaList, setMediaList] = useState<any[]>([]);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try { const res: any = await api.get('/tryon/tasks'); setHistory(res.data || res.results || res || []); } catch { /* ignore */ }
  };

  const fetchMedia = async () => {
    try { const res: any = await api.get('/media'); setMediaList(res.data || res.results || res || []); } catch { /* ignore */ }
  };

  const openMediaPicker = (type: 'person' | 'garment') => {
    fetchMedia();
    setMediaPicker({ type, visible: true });
  };

  const selectFromMedia = (url: string) => {
    if (mediaPicker.type === 'person') setPersonUrl(url);
    else setGarmentUrl(url);
    setMediaPicker({ ...mediaPicker, visible: false });
    message.success('已选择');
  };

  const useSample = (type: 'person' | 'garment') => {
    if (type === 'person') {
      setPersonUrl(SAMPLES.person);
    } else {
      setGarmentUrl(SAMPLES.garment[category as keyof typeof SAMPLES.garment]);
    }
  };

  const handleUpload = (type: 'person' | 'garment') => (info: any) => {
    const url = info.file?.response?.data?.url || info.url || URL.createObjectURL(info.file);
    if (type === 'person') setPersonUrl(url);
    else setGarmentUrl(url);
  };

  const handleSynthesize = async () => {
    if (!personUrl || !garmentUrl) {
      message.warning('请上传或选择人物照片和服装图片');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res: any = await api.post('/tryon/tasks', {
        person_image_url: personUrl,
        garment_image_url: garmentUrl,
        garment_category: category,
        title: `试衣 ${new Date().toLocaleString('zh-CN')}`,
      });
      const tid = res.task_id;
      const poll = setInterval(async () => {
        try {
          const tasks: any = await api.get('/tryon/tasks');
          const list = tasks.data || tasks.results || tasks || [];
          const found = list.find((t: any) => t.task_id === tid || String(t.id) === tid);
          if (found?.status === 'completed') {
            setResult(found.result_image_url); setLoading(false); clearInterval(poll);
            message.success('合成完成！'); fetchHistory();
          } else if (found?.status === 'failed') {
            setLoading(false); clearInterval(poll);
            message.error(found.error_message || '合成失败');
          }
        } catch { clearInterval(poll); setLoading(false); }
      }, 2000);
      setTimeout(() => { clearInterval(poll); setLoading(false); }, 60000);
    } catch { message.error('提交失败'); setLoading(false); }
  };

  const ImageCard = ({ label, type, url, setUrl }: { label: string; type: 'person' | 'garment'; url: string; setUrl: (v: string) => void }) => (
    <Card size="small" title={label} style={{ borderRadius: 8 }}
      extra={
        <Space size={4}>
          <Tooltip title="使用示例图片"><Button size="small" icon={<BulbOutlined />} onClick={() => useSample(type)} /></Tooltip>
          <Tooltip title="从媒体库选择"><Button size="small" icon={<FolderOpenOutlined />} onClick={() => openMediaPicker(type)} /></Tooltip>
        </Space>
      }>
      {url ? (
        <div style={{ textAlign: 'center' }}>
          <Image src={url} width={180} style={{ borderRadius: 6, maxHeight: 220, objectFit: 'cover' }} />
          <br /><Button type="link" onClick={() => setUrl('')} danger size="small">清除</Button>
        </div>
      ) : (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Upload accept="image/*" customRequest={({ file, onSuccess }) => {
            const u = URL.createObjectURL(file as Blob);
            setUrl(u); onSuccess?.({ url: u }, file as any);
          }} showUploadList={false}>
            <Button icon={<UploadOutlined />} block>本地上传</Button>
          </Upload>
          <Button icon={<BulbOutlined />} block onClick={() => useSample(type)}>使用示例</Button>
          <Button icon={<FolderOpenOutlined />} block onClick={() => openMediaPicker(type)}>从媒体库</Button>
        </Space>
      )}
    </Card>
  );

  return (
    <DashboardLayout>
      <Title level={3}><PictureOutlined style={{ marginRight: 8 }} />虚拟试衣</Title>

      <Alert message="上传人物照片和服装图片，AI 自动合成试穿效果。可使用示例图片快速体验。" type="info" showIcon
        style={{ marginBottom: 16, borderRadius: 8 }} />

      <Row gutter={24}>
        <Col xs={24} lg={10}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <ImageCard label="👤 人物照片" type="person" url={personUrl} setUrl={setPersonUrl} />
            <ImageCard label="👕 服装图片" type="garment" url={garmentUrl} setUrl={setGarmentUrl} />

            <Select value={category} onChange={setCategory} style={{ width: '100%' }}
              options={[
                { value: 'upper', label: '👔 上装' },
                { value: 'lower', label: '👖 下装' },
                { value: 'dress', label: '👗 连衣裙' },
                { value: 'outer', label: '🧥 外套' },
              ]} />

            <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleSynthesize}
              loading={loading} block size="large" style={{ height: 48, borderRadius: 8 }}>
              {loading ? 'AI 合成中...' : '开始合成'}
            </Button>

            <Button icon={<HistoryOutlined />} onClick={() => setHistoryVisible(true)} block>
              历史记录 ({history.length})
            </Button>
          </Space>
        </Col>

        <Col xs={24} lg={14}>
          <Card title="合成结果" style={{ borderRadius: 8, minHeight: 400 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: 80 }}>
                <Spin size="large" /><p style={{ marginTop: 16, color: '#666' }}>AI 正在合成，请稍候...</p>
              </div>
            ) : result ? (
              <div style={{ textAlign: 'center' }}>
                <Image src={result} style={{ maxWidth: '100%', borderRadius: 8, maxHeight: 500 }} />
                <Divider />
                <Space>
                  <Button icon={<DownloadOutlined />} href={result} target="_blank">下载</Button>
                  <Button icon={<ReloadOutlined />} onClick={() => setResult(null)}>重新合成</Button>
                </Space>
              </div>
            ) : (
              <Empty description={
                <span>上传图片后点击「开始合成」<br /><Text type="secondary" style={{ fontSize: 12 }}>也可点击 💡 使用示例快速体验</Text></span>
              } style={{ padding: 60 }} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 媒体库选择器 */}
      <Modal title="从媒体库选择" open={mediaPicker.visible} onCancel={() => setMediaPicker({ ...mediaPicker, visible: false })}
        footer={null} width={640}>
        {mediaList.length === 0 ? <Empty description="媒体库暂无素材，请先上传" /> : (
          <Row gutter={[12, 12]}>
            {mediaList.filter(m => m.file_url).map(m => (
              <Col key={m.id} xs={8} sm={6}>
                <Card size="small" hoverable
                  cover={<Image src={m.file_url} style={{ height: 120, objectFit: 'cover' }} preview={false} />}
                  onClick={() => selectFromMedia(m.file_url)}
                  style={{ borderRadius: 6 }}
                >
                  <Card.Meta title={<Text ellipsis style={{ fontSize: 11 }}>{m.title}</Text>} />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Modal>

      {/* 历史记录 */}
      <Modal title="试衣历史" open={historyVisible} onCancel={() => setHistoryVisible(false)}
        footer={null} width={700}>
        {history.length === 0 ? <Empty description="暂无记录" /> : (
          <Row gutter={[12, 12]}>
            {history.map((h: any) => (
              <Col key={h.id} xs={12} sm={8}>
                <Card size="small" hoverable
                  cover={h.result_image_url
                    ? <Image src={h.result_image_url} style={{ height: 150, objectFit: 'cover' }} />
                    : <div style={{ height: 150, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Tag>{h.status === 'processing' ? '处理中' : h.status === 'failed' ? '失败' : '等待中'}</Tag>
                      </div>
                  }
                  onClick={() => h.result_image_url && setResult(h.result_image_url)}
                >
                  <Card.Meta title={h.title || `试衣 #${h.id}`}
                    description={<Text type="secondary" style={{ fontSize: 12 }}>{h.created_at?.slice(0, 16)}</Text>} />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Modal>
    </DashboardLayout>
  );
}
