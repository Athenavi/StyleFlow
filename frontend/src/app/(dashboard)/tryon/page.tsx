'use client';

import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Upload, Select, Image, Tag, Space,
  Typography, message, Spin, Divider, Empty, Modal
} from 'antd';
import {
  ThunderboltOutlined, UploadOutlined, PictureOutlined,
  HistoryOutlined, ReloadOutlined, DownloadOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

export default function TryonPage() {
  const [personUrl, setPersonUrl] = useState('');
  const [garmentUrl, setGarmentUrl] = useState('');
  const [category, setCategory] = useState('upper');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [historyVisible, setHistoryVisible] = useState(false);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try {
      const res: any = await api.get('/tryon/tasks');
      setHistory(res.data || res.results || res || []);
    } catch { /* ignore */ }
  };

  const handleUpload = (type: 'person' | 'garment') => (info: any) => {
    const url = info.file?.response?.data?.url || info.url || URL.createObjectURL(info.file);
    if (type === 'person') setPersonUrl(url);
    else setGarmentUrl(url);
    if (info.file?.status === 'done') message.success('上传成功');
  };

  const handleSynthesize = async () => {
    if (!personUrl || !garmentUrl) {
      message.warning('请上传人物照片和服装图片');
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
      // 轮询结果
      const poll = setInterval(async () => {
        try {
          const tasks: any = await api.get('/tryon/tasks');
          const list = tasks.data || tasks.results || tasks || [];
          const found = list.find((t: any) => t.task_id === tid || String(t.id) === tid);
          if (found && found.status === 'completed') {
            setResult(found.result_image_url);
            setLoading(false);
            clearInterval(poll);
            message.success('合成完成！');
            fetchHistory();
          } else if (found && found.status === 'failed') {
            setLoading(false);
            clearInterval(poll);
            message.error(found.error_message || '合成失败');
          }
        } catch { clearInterval(poll); setLoading(false); }
      }, 2000);
      setTimeout(() => { clearInterval(poll); setLoading(false); }, 60000);
    } catch { message.error('提交失败'); setLoading(false); }
  };

  return (
    <DashboardLayout>
      <Title level={3}>
        <PictureOutlined style={{ marginRight: 8 }} />虚拟试衣
      </Title>

      <Row gutter={24}>
        {/* 左侧：输入区 */}
        <Col xs={24} lg={10}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {/* 人物照片 */}
            <Card size="small" title="人物照片" style={{ borderRadius: 8 }}>
              {personUrl ? (
                <div style={{ textAlign: 'center' }}>
                  <Image src={personUrl} width={200} style={{ borderRadius: 8 }} />
                  <Button type="link" onClick={() => setPersonUrl('')} danger>更换</Button>
                </div>
              ) : (
                <Upload accept="image/*" customRequest={({ file, onSuccess }) => {
                  const url = URL.createObjectURL(file as Blob);
                  setPersonUrl(url);
                  onSuccess?.({ url }, file as any);
                }} showUploadList={false}>
                  <Button icon={<UploadOutlined />} block>上传人物照片</Button>
                </Upload>
              )}
            </Card>

            {/* 服装图片 */}
            <Card size="small" title="服装图片" style={{ borderRadius: 8 }}>
              {garmentUrl ? (
                <div style={{ textAlign: 'center' }}>
                  <Image src={garmentUrl} width={200} style={{ borderRadius: 8 }} />
                  <Button type="link" onClick={() => setGarmentUrl('')} danger>更换</Button>
                </div>
              ) : (
                <Upload accept="image/*" customRequest={({ file, onSuccess }) => {
                  const url = URL.createObjectURL(file as Blob);
                  setGarmentUrl(url);
                  onSuccess?.({ url }, file as any);
                }} showUploadList={false}>
                  <Button icon={<UploadOutlined />} block>上传服装图片</Button>
                </Upload>
              )}
            </Card>

            <Select value={category} onChange={setCategory} style={{ width: '100%' }}
              options={[
                { value: 'upper', label: '👔 上装' },
                { value: 'lower', label: '👖 下装' },
                { value: 'dress', label: '👗 连衣裙' },
                { value: 'outer', label: '🧥 外套' },
              ]} />

            <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleSynthesize}
              loading={loading} block size="large" style={{ height: 48, borderRadius: 8 }}>
              {loading ? '合成中...' : '开始合成'}
            </Button>

            <Button icon={<HistoryOutlined />} onClick={() => setHistoryVisible(true)} block>
              历史记录
            </Button>
          </Space>
        </Col>

        {/* 右侧：结果 */}
        <Col xs={24} lg={14}>
          <Card title="合成结果" style={{ borderRadius: 8, minHeight: 400 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" tip="AI 正在合成..." /></div>
            ) : result ? (
              <div style={{ textAlign: 'center' }}>
                <Image src={result} style={{ maxWidth: '100%', borderRadius: 8, maxHeight: 500 }} />
                <Divider />
                <Space>
                  <Button icon={<DownloadOutlined />} href={result} target="_blank">下载</Button>
                  <Button icon={<ReloadOutlined />} onClick={() => { setResult(null); }}>重新合成</Button>
                </Space>
              </div>
            ) : (
              <Empty description="上传图片后点击「开始合成」" style={{ padding: 60 }} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 历史记录弹窗 */}
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
