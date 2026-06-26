'use client';

import { useState, useEffect } from 'react';
import {
  Card, Table, Tag, Typography, Space, Spin, Empty, App,
  Row, Col, Statistic, DatePicker, Input
} from 'antd';
import { DollarOutlined, SearchOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

export default function WagesPage() {
  const { message } = App.useApp();
  const [records, setRecords] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [workerId, setWorkerId] = useState('');
  const [dates, setDates] = useState<[string, string] | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (workerId) params.worker_id = workerId;
      if (dates) { params.date_from = dates[0]; params.date_to = dates[1]; }
      const [rRes, sRes] = await Promise.all([
        api.get('/wages/records', params),
        api.get('/wages/summary', params),
      ]);
      setRecords(rRes.data || rRes.results || rRes || []);
      setSummary(sRes);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, [workerId, dates]);

  const columns = [
    { title: '工号', dataIndex: 'worker_id', key: 'worker_id' },
    { title: '姓名', dataIndex: 'worker_name', key: 'worker_name' },
    { title: '日期', dataIndex: 'date', key: 'date', render: (v: string) => v?.slice(0, 10) },
    { title: '款号', dataIndex: 'style_code', key: 'style_code' },
    { title: '工序', dataIndex: 'process_name', key: 'process_name', ellipsis: true },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '单价', dataIndex: 'unit_price', key: 'unit_price', render: (v: number) => `¥${v?.toFixed(2)}` },
    { title: '合计', dataIndex: 'total_amount', key: 'total_amount', render: (v: number) => <Text strong>¥{v?.toFixed(2)}</Text> },
  ];

  return (
    <DashboardLayout>
      <Title level={3}><DollarOutlined style={{ marginRight: 8 }} />计件工资</Title>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="总人数" value={summary?.total_workers || 0} suffix="人" /></Card></Col>
        <Col span={6}><Card><Statistic title="总金额" value={summary?.total_amount || 0} prefix="¥" precision={2} /></Card></Col>
        <Col span={6}><Card><Statistic title="总件数" value={summary?.total_quantity || 0} suffix="件" /></Card></Col>
        <Col span={6}><Card><Statistic title="记录数" value={summary?.records || 0} suffix="条" /></Card></Col>
      </Row>

      <Card style={{ borderRadius: 8 }}>
        <Space style={{ marginBottom: 16 }}>
          <Input placeholder="搜索工号..." prefix={<SearchOutlined />} value={workerId}
            onChange={e => setWorkerId(e.target.value)} style={{ width: 200 }} allowClear />
          <RangePicker onChange={(_, dateStrings) => setDates(dateStrings as [string, string])} />
        </Space>

        {loading ? <Spin style={{ display: 'block', padding: 40 }} /> :
          records.length === 0 ? <Empty description="暂无工资记录" /> :
          <Table dataSource={records} columns={columns} rowKey="id"
            pagination={{ pageSize: 15 }} size="small" scroll={{ x: 900 }} />
        }
      </Card>
    </DashboardLayout>
  );
}
