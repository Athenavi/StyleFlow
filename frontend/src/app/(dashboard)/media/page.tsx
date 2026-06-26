'use client';

import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Upload, Button, Typography, message, Space,
  Image, Tag, Spin, Empty, Modal, Select, Input, Tooltip
} from 'antd';
import {
  CloudUploadOutlined, FolderOutlined, DeleteOutlined,
  SearchOutlined, LinkOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const CATEGORIES = [
  { value: '', label: '全部分类' },
  { value: 'model', label: '👤 模特图' },
  { value: 'garment', label: '👕 服装图' },
  { value: 'fabric', label: '🧵 面料图' },
  { value: 'sketch', label: '✏️ 设计稿' },
  { value: 'moodboard', label: '🎨 灵感图' },
  { value: 'other', label: '📁 其他' },
];

const FILE_TYPES = ['jpg', 'jpeg', 'png', 'webp', 'gif'];

export default function MediaPage() {
  const [media, setMedia] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const fetchMedia = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (category) params.category = category;
      if (search) params.search = search;
      const res: any = await api.get('/media', params);
      setMedia(res.data || res.results || res || []);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchMedia(); }, [category]);

  const handleUpload = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) {
      message.error('仅支持 JPG/PNG/WebP/GIF 格式');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      message.error('文件大小不能超过 10MB');
      return;
    }

    // multipart/form-data 上传到服务器
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^.]+$/, ''));
    formData.append('category', category || 'other');

    try {
      // 直接用 fetch 发 multipart（跳过 api.ts 的 JSON 拦截器）
      const token = localStorage.getItem('access_token');
      const res = await fetch(
        (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1') + '/media/upload',
        {
          method: 'POST',
          headers: { Authorization: token ? `Bearer ${token}` : '' },
          body: formData,
        }
      );
      if (!res.ok) throw new Error('上传失败');
      message.success('上传成功');
      fetchMedia();
    } catch { message.error('上传失败'); }
    return false;
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/media/${id}`);
      message.success('已删除');
      setMedia(prev => prev.filter(m => m.id !== id));
    } catch { message.error('删除失败'); }
  };

  const copyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    message.success('链接已复制');
  };

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <FolderOutlined style={{ marginRight: 8 }} />我的媒体库
        </Title>
        <Text type="secondary">支持 JPG / PNG / WebP / GIF，单文件 ≤ 10MB</Text>
      </div>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space wrap>
          <Upload accept=".jpg,.jpeg,.png,.webp,.gif" showUploadList={false}
            beforeUpload={handleUpload as any}>
            <Button type="primary" icon={<CloudUploadOutlined />}>上传素材</Button>
          </Upload>
          <Select value={category} onChange={setCategory} style={{ width: 140 }}
            options={CATEGORIES} />
          <Input placeholder="搜索标题或标签..." prefix={<SearchOutlined />}
            value={search} onChange={e => setSearch(e.target.value)}
            onPressEnter={fetchMedia} style={{ width: 240 }} allowClear />
        </Space>
      </Card>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
       : media.length === 0 ? <Empty description="暂无素材" style={{ padding: 80 }}>
           <Upload accept=".jpg,.jpeg,.png,.webp,.gif" showUploadList={false}
             beforeUpload={handleUpload as any}>
             <Button type="primary" icon={<CloudUploadOutlined />}>上传第一个素材</Button>
           </Upload>
         </Empty>
       : <Row gutter={[12, 12]}>
          {media.map(item => (
            <Col key={item.id} xs={12} sm={8} md={6} lg={4}>
              <Card
                hoverable
                size="small"
                style={{ borderRadius: 6 }}
                cover={
                  <div style={{ height: 160, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa' }}>
                    <Image src={item.file_url} alt={item.title}
                      style={{ maxWidth: '100%', maxHeight: 160, objectFit: 'cover' }}
                      preview={{ mask: '预览' }}
                      fallback="data:image/png;base64,iVBORw0KGgo..."
                    />
                  </div>
                }
                actions={[
                  <Tooltip title="复制链接" key="copy"><LinkOutlined onClick={() => copyUrl(item.file_url)} /></Tooltip>,
                  <Tooltip title="删除" key="del"><DeleteOutlined onClick={() => handleDelete(item.id)} /></Tooltip>,
                ]}
              >
                <Card.Meta
                  title={<Text ellipsis style={{ fontSize: 12 }}>{item.title}</Text>}
                  description={
                    <Space size={4}>
                      <Tag style={{ fontSize: 10 }}>{item.file_type?.toUpperCase()}</Tag>
                      <Text type="secondary" style={{ fontSize: 10 }}>
                        {item.width}×{item.height}
                      </Text>
                    </Space>
                  }
                />
              </Card>
            </Col>
          ))}
         </Row>}

      <Modal open={!!previewUrl} onCancel={() => setPreviewUrl(null)}
        footer={null} width={800}>
        {previewUrl && <Image src={previewUrl} style={{ width: '100%' }} />}
      </Modal>
    </DashboardLayout>
  );
}
