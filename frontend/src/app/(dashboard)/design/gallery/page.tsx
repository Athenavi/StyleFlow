'use client';

import { useState, useEffect } from 'react';
import {
  Row, Col, Card, Input, Select, Tag, Image, Space, Typography,
  Spin, Empty, App, Tabs, Button, Modal, message as Msg, Upload
} from 'antd';
import {
  PictureOutlined, SearchOutlined, ClockCircleOutlined,
  EditOutlined, UploadOutlined, FolderOpenOutlined, DeleteOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const CATEGORIES = [
  { value: 'style', label: '款式图' },
  { value: 'sketch', label: '线稿' },
  { value: 'fabric', label: '面料图' },
  { value: 'moodboard', label: '灵感板' },
  { value: 'flatten', label: '平铺图' },
];

export default function DesignGalleryPage() {
  const { message } = App.useApp();
  const [designs, setDesigns] = useState<any[]>([]);
  const [publicDesigns, setPublicDesigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState('personal');

  // Edit modal
  const [editModal, setEditModal] = useState(false);
  const [editItem, setEditItem] = useState<any>(null);
  const [editCategory, setEditCategory] = useState('');

  // Media picker
  const [mediaPicker, setMediaPicker] = useState(false);
  const [mediaList, setMediaList] = useState<any[]>([]);

  const fetchDesigns = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (category) params.category = category;
      if (search) params.search = search;

      if (tab === 'personal') {
        const res: any = await api.get('/designs', params);
        const list = res.items || res.data || res.results || [];
        setDesigns(list);
        setPublicDesigns([]);
      } else {
        const res: any = await api.get('/designs', params);
        const list = res.items || res.data || res.results || [];
        setDesigns([]);
      }
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchDesigns(); }, [category, tab]);

  const handleSearch = () => { fetchDesigns(); };

  const openEdit = (item: any) => {
    setEditItem(item);
    setEditCategory(item.category);
    setEditModal(true);
  };

  const saveCategory = async () => {
    if (!editItem) return;
    try {
      await api.patch(`/designs/${editItem.id}`, { category: editCategory });
      message.success('已更新分类');
      setEditModal(false);
      fetchDesigns();
    } catch { message.error('更新失败'); }
  };

  const openMediaPicker = () => {
    api.get('/media').then((res: any) => {
      setMediaList(res.data || res.results || res || []);
    }).catch(() => {});
    setMediaPicker(true);
  };

  const selectFromMedia = (url: string, title: string) => {
    // 从媒体库导入设计稿
    api.post('/designs', {
      title, image_url: url, category: category || 'style',
      prompt: '从媒体库导入',
    }).then(() => {
      message.success('已导入设计稿库');
      setMediaPicker(false);
      fetchDesigns();
    }).catch(() => message.error('导入失败'));
  };

  const renderGrid = (items: any[]) => (
    loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
    : items.length === 0 ? <Empty description="暂无设计稿" style={{ padding: 80 }} />
    : <Row gutter={[16, 16]}>
        {items.map((item) => (
          <Col key={item.id} xs={24} sm={12} md={8} lg={6}>
            <Card
              hoverable
              cover={
                <Image alt={item.title} src={item.image_url || '/placeholder.png'}
                  style={{ height: 240, objectFit: 'cover' }} preview={{ mask: '点击预览' }}
                  fallback="data:image/png;base64,iVBORw0KGgo..." />
              }
              style={{ borderRadius: 8 }}
              actions={[
                <Button key="cat" type="link" size="small" icon={<EditOutlined />}
                  onClick={() => openEdit(item)}>分类</Button>,
              ]}
            >
              <Card.Meta
                title={<Text ellipsis style={{ maxWidth: 180 }}>{item.title || `设计稿 #${item.id}`}</Text>}
                description={
                  <Space direction="vertical" size={4}>
                    <Space>
                      <Tag>{CATEGORIES.find(c => c.value === item.category)?.label || item.category}</Tag>
                      <Tag color={item.status === 'completed' ? 'green' : 'orange'}>
                        {item.status === 'completed' ? '已完成' : '草稿'}
                      </Tag>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>{item.created_at?.slice(0, 10)}</Text>
                  </Space>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
  );

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <PictureOutlined style={{ marginRight: 8 }} />设计稿库
        </Title>
        <Space>
          <Button icon={<FolderOpenOutlined />} onClick={openMediaPicker}>从媒体库导入</Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space wrap size="middle">
          <Select value={category} onChange={setCategory} style={{ width: 140 }}
            options={[{ value: '', label: '全部分类' }, ...CATEGORIES]} placeholder="按分类筛选" />
          <Input placeholder="搜索设计稿..." prefix={<SearchOutlined />}
            value={search} onChange={e => setSearch(e.target.value)}
            onPressEnter={handleSearch} style={{ width: 300 }} allowClear />
          <Text type="secondary"><ClockCircleOutlined /> {(tab === 'personal' ? designs : publicDesigns).length} 件</Text>
        </Space>
      </Card>

      <Tabs activeKey={tab} onChange={setTab} items={[
        { key: 'personal', label: `🙋 我的设计 (${designs.length})`, children: renderGrid(designs) },
        { key: 'public', label: `🌐 公共设计库 (${publicDesigns.length})`, children: renderGrid(publicDesigns) },
      ]} />

      {/* 分类编辑弹窗 */}
      <Modal title="修改分类" open={editModal} onOk={saveCategory} onCancel={() => setEditModal(false)}>
        <div style={{ margin: '16px 0' }}>
          <Text strong>设计稿：{editItem?.title || `#${editItem?.id}`}</Text>
        </div>
        <Select value={editCategory} onChange={setEditCategory} style={{ width: '100%' }}
          options={CATEGORIES} />
      </Modal>

      {/* 媒体库选择器 */}
      <Modal title="从媒体库导入" open={mediaPicker} onCancel={() => setMediaPicker(false)} footer={null} width={640}>
        {mediaList.length === 0 ? <Empty description="媒体库为空，请先上传素材" /> : (
          <Row gutter={[12, 12]}>
            {mediaList.map((m: any) => (
              <Col key={m.id} xs={8} sm={6}>
                <Card size="small" hoverable
                  cover={<Image src={m.file_url} style={{ height: 120, objectFit: 'cover' }} preview={false} />}
                  onClick={() => selectFromMedia(m.file_url, m.title)}
                  style={{ borderRadius: 6 }}>
                  <Card.Meta title={<Text ellipsis style={{ fontSize: 11 }}>{m.title}</Text>} />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Modal>
    </DashboardLayout>
  );
}
