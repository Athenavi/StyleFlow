'use client';

import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Upload, Button, Typography, App, Space,
  Image, Tag, Spin, Empty, Modal, Select, Input, Tooltip, Popconfirm, Tabs,
  Checkbox, message as Msg
} from 'antd';
import {
  CloudUploadOutlined, FolderOutlined, DeleteOutlined,
  SearchOutlined, LinkOutlined, RestOutlined,
  TagsOutlined, SelectOutlined, DeleteFilled, UndoOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

const CATEGORIES = [
  { value: 'model', label: '👤 模特图' },
  { value: 'garment', label: '👕 服装图' },
  { value: 'fabric', label: '🧵 面料图' },
  { value: 'sketch', label: '✏️ 设计稿' },
  { value: 'moodboard', label: '🎨 灵感图' },
  { value: 'other', label: '📁 其他' },
];

export default function MediaPage() {
  const { message } = App.useApp();
  const [activeMedia, setActiveMedia] = useState<any[]>([]);
  const [trashMedia, setTrashMedia] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState('active');
  const [selected, setSelected] = useState<number[]>([]);
  const [batchCatModal, setBatchCatModal] = useState(false);
  const [batchCat, setBatchCat] = useState('');

  const fetchMedia = async () => {
    setLoading(true);
    setSelected([]);
    try {
      // 同时获取正常和回收站数据
      const [activeRes, trashRes] = await Promise.all([
        api.get('/media', { ...(category ? { category } : {}), ...(search ? { search } : {}) }),
        api.get('/media', { ...(category ? { category } : {}), ...(search ? { search } : {}), trash: true }),
      ]);
      setActiveMedia(activeRes.data || activeRes.results || activeRes || []);
      setTrashMedia(trashRes.data || trashRes.results || trashRes || []);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchMedia(); }, [category, search]);

  const handleUpload = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) { message.error('不支持格式'); return false; }
    if (file.size > 10 * 1024 * 1024) { message.error('超过10MB'); return false; }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^.]+$/, ''));
    formData.append('category', category || 'other');
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(
        (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1') + '/media/upload',
        { method: 'POST', headers: { Authorization: token ? `Bearer ${token}` : '' }, body: formData,
        }
      );
      if (!res.ok) throw new Error();
      message.success('上传成功'); fetchMedia();
    } catch { message.error('上传失败'); }
    return false;
  };

  const handleDelete = async (id: number) => {
    try { await api.delete(`/media/${id}`); message.success('已移入回收站'); fetchMedia(); } catch { message.error('失败'); }
  };

  const handleRestore = async (id: number) => {
    try { await api.post(`/media/restore/${id}`); message.success('已恢复'); fetchMedia(); } catch { message.error('失败'); }
  };

  const handlePermanentDelete = async (id: number) => {
    try { await api.post(`/media/permanent-delete/${id}`); message.success('已永久删除'); fetchMedia(); } catch { message.error('失败'); }
  };

  const handleBatchDelete = async () => {
    if (selected.length === 0) return;
    try {
      if (tab === 'trash') {
        // 批量永久删除已选项
        for (const id of selected) {
          await api.post(`/media/permanent-delete/${id}`);
        }
        message.success(`${selected.length} 项已永久删除`);
      } else {
        await api.post('/media/batch-delete', { ids: selected });
        message.success(`${selected.length} 项已移入回收站`);
      }
      fetchMedia();
    } catch { message.error('操作失败'); }
  };

  const handleBatchCategory = async () => {
    if (!batchCat || selected.length === 0) return;
    try {
      await api.patch('/media/batch-category', { ids: selected, category: batchCat });
      message.success('分类已更新');
      setBatchCatModal(false); fetchMedia();
    } catch { message.error('更新失败'); }
  };

  const copyUrl = (url: string) => { navigator.clipboard.writeText(url); message.success('已复制'); };

  const toggleSelect = (id: number) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const renderGrid = (items: any[]) => {
    if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
    if (items.length === 0) return <Empty description={tab === 'trash' ? '回收站为空' : '暂无素材'} style={{ padding: 80 }} />;

    return <>
      {selected.length > 0 && (
        <Card size="small" style={{ marginBottom: 12, borderRadius: 6 }}>
          <Space>
            <Text strong>已选 {selected.length} 项</Text>
            {tab !== 'trash' && (
              <Button size="small" icon={<TagsOutlined />} onClick={() => setBatchCatModal(true)}>批量分类</Button>
            )}
            <Popconfirm title={tab === 'trash' ? '永久删除所有？' : `移入回收站 ${selected.length} 项？`}
              onConfirm={handleBatchDelete}>
              <Button size="small" danger icon={<DeleteFilled />}>
                {tab === 'trash' ? '永久删除' : '批量删除'}
              </Button>
            </Popconfirm>
            {tab === 'trash' && (
              <Popconfirm title="清空回收站全部文件？不可恢复！" onConfirm={async () => {
                try { await api.post('/media/empty-trash'); message.success('已清空'); fetchMedia(); } catch { message.error('失败'); }
              }}>
                <Button size="small" danger icon={<DeleteFilled />}>清空全部</Button>
              </Popconfirm>
            )}
            <Button size="small" onClick={() => setSelected([])}>取消选择</Button>
          </Space>
        </Card>
      )}

      <Row gutter={[12, 12]}>
        {items.map(item => (
          <Col key={item.id} xs={12} sm={8} md={6} lg={4}>
            <Card size="small" hoverable
              style={{ borderRadius: 6, outline: selected.includes(item.id) ? '2px solid #1677ff' : 'none' }}
              cover={<div style={{ height: 140, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa', cursor: 'pointer' }}
                  onClick={() => toggleSelect(item.id)}>
                <Image src={item.file_url} alt={item.title}
                  style={{ maxWidth: '100%', maxHeight: 140, objectFit: 'cover' }}
                  preview={{ mask: '预览' }}
                  fallback="data:image/png;base64,iVBORw0KGgo..." />
              </div>}
              actions={tab === 'trash' ? [
                <Tooltip title="恢复" key="restore"><UndoOutlined onClick={() => handleRestore(item.id)} /></Tooltip>,
                <Popconfirm title="永久删除？不可恢复" key="del">
                  <Tooltip title="永久删除"><DeleteFilled style={{ color: '#ff4d4f' }} onClick={() => handlePermanentDelete(item.id)} /></Tooltip>
                </Popconfirm>,
              ] : [
                <Tooltip title="复制链接" key="copy"><LinkOutlined onClick={() => copyUrl(item.file_url)} /></Tooltip>,
                <Popconfirm title="移入回收站？" key="del"><DeleteOutlined onClick={() => handleDelete(item.id)} /></Popconfirm>,
              ]}>
              <Card.Meta title={<Text ellipsis style={{ fontSize: 11 }}>{item.title}</Text>}
                description={
                  <Space size={4} wrap>
                    <Tag style={{ fontSize: 10 }}>{item.file_type?.toUpperCase()}</Tag>
                    <Tag style={{ fontSize: 10 }}>{CATEGORIES.find(c => c.value === item.category)?.label || item.category}</Tag>
                  </Space>
                } />
            </Card>
          </Col>
        ))}
      </Row>
    </>;
  };

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Title level={3} style={{ margin: 0 }}>
          <FolderOutlined style={{ marginRight: 8 }} />媒体库
        </Title>
        <Upload accept=".jpg,.jpeg,.png,.webp,.gif" showUploadList={false}
          beforeUpload={handleUpload as any}>
          <Button type="primary" icon={<CloudUploadOutlined />}>上传</Button>
        </Upload>
      </div>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space wrap>
          <Select value={category} onChange={setCategory} style={{ width: 140 }}
            options={[{ value: '', label: '全部分类' }, ...CATEGORIES]} />
          <Input placeholder="搜索..." prefix={<SearchOutlined />}
            value={search} onChange={e => setSearch(e.target.value)}
            onPressEnter={fetchMedia} style={{ width: 240 }} allowClear />
        </Space>
      </Card>

      <Tabs activeKey={tab} onChange={setTab} items={[
        { key: 'active', label: `📁 我的素材 (${activeMedia.length})`, children: renderGrid(activeMedia) },
        { key: 'trash', label: (
          <Space>
            <span>🗑️ 回收站 ({trashMedia.length})</span>
            {trashMedia.length > 0 && (
              <Popconfirm title="确定清空回收站？所有文件将被永久删除，不可恢复！" onConfirm={async () => {
                try { await api.post('/media/empty-trash'); message.success('回收站已清空'); fetchMedia(); } catch { message.error('失败'); }
              }}>
                <Button size="small" danger type="primary" style={{ fontSize: 11, height: 22, lineHeight: '22px', padding: '0 8px' }}>
                  清空全部
                </Button>
              </Popconfirm>
            )}
          </Space>
        ), children: renderGrid(trashMedia) },
      ]} />

      {/* 批量分类弹窗 */}
      <Modal title="批量修改分类" open={batchCatModal} onOk={handleBatchCategory}
        onCancel={() => setBatchCatModal(false)}>
        <div style={{ margin: '16px 0' }}>
          <Text>已选 {selected.length} 项，请选择目标分类：</Text>
        </div>
        <Select value={batchCat} onChange={setBatchCat} style={{ width: '100%' }}
          options={CATEGORIES} placeholder="选择分类" />
      </Modal>
    </DashboardLayout>
  );
}
