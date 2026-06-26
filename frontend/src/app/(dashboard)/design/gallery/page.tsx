'use client';

import { useState, useEffect } from 'react';
import {
  Row, Col, Card, Input, Select, Tag, Image, Space, Typography,
  Spin, Empty, message
} from 'antd';
import {
  PictureOutlined, SearchOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { Search } = Input;

const CATEGORIES = [
  { value: '', label: '全部' },
  { value: 'style', label: '款式图' },
  { value: 'sketch', label: '线稿' },
  { value: 'fabric', label: '面料图' },
  { value: 'moodboard', label: '灵感板' },
  { value: 'flatten', label: '平铺图' },
];

interface DesignItem {
  id: number;
  title: string;
  image_url: string;
  thumbnail_url: string;
  prompt: string;
  category: string;
  tags: string[];
  status: string;
  created_at: string;
}

export default function DesignGalleryPage() {
  const [designs, setDesigns] = useState<DesignItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');

  const fetchDesigns = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (category) params.category = category;
      if (search) params.search = search;
      const res: any = await api.get('/designs', { params });
      setDesigns(res.data || res.results || res || []);
    } catch (err: any) {
      message.error('加载设计稿失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDesigns(); }, [category]);

  const handleSearch = (value: string) => {
    setSearch(value);
    fetchDesigns();
  };

  const getCategoryLabel = (val: string) =>
    CATEGORIES.find(c => c.value === val)?.label || val;

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <PictureOutlined style={{ marginRight: 8 }} />
          设计稿库
        </Title>
      </div>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space wrap size="middle">
          <Select
            value={category}
            onChange={setCategory}
            options={CATEGORIES}
            style={{ width: 140 }}
            placeholder="按分类筛选"
          />
          <Search
            placeholder="搜索设计稿..."
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
            style={{ width: 300 }}
            allowClear
          />
          <Text type="secondary">
            <ClockCircleOutlined /> 共 {designs.length} 件
          </Text>
        </Space>
      </Card>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : designs.length === 0 ? (
        <Empty description="暂无设计稿" style={{ padding: 80 }} />
      ) : (
        <Row gutter={[16, 16]}>
          {designs.map((item) => (
            <Col key={item.id} xs={24} sm={12} md={8} lg={6}>
              <Card
                hoverable
                cover={
                  <Image
                    alt={item.title}
                    src={item.image_url || '/placeholder.png'}
                    style={{ height: 240, objectFit: 'cover' }}
                    preview={{ mask: '点击预览' }}
                    fallback="data:image/png;base64,iVBORw0KGgo..."
                  />
                }
                style={{ borderRadius: 8 }}
              >
                <Card.Meta
                  title={
                    <Text ellipsis style={{ maxWidth: 180 }}>
                      {item.title || `设计稿 #${item.id}`}
                    </Text>
                  }
                  description={
                    <Space direction="vertical" size={4}>
                      <Space>
                        <Tag>{getCategoryLabel(item.category)}</Tag>
                        <Tag color={item.status === 'completed' ? 'green' : 'orange'}>
                          {item.status === 'completed' ? '已完成' : '草稿'}
                        </Tag>
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.created_at?.slice(0, 10)}
                      </Text>
                    </Space>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </DashboardLayout>
  );
}
