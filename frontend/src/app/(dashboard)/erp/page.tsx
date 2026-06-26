'use client';

import { useState, useEffect } from 'react';
import {
  Table, Card, Button, Tag, Typography, Space, message, Spin,
  Modal, Descriptions, Input, Select, Row, Col, Statistic
} from 'antd';
import { DatabaseOutlined, SyncOutlined, SearchOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

export default function ErpPage() {
  const [styles, setStyles] = useState<any[]>([]);
  const [processes, setProcesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('styles');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sRes, pRes] = await Promise.all([
        api.get('/erp/styles', { params: { search } }),
        api.get('/erp/processes'),
      ]);
      setStyles(Array.isArray(sRes) ? sRes : []);
      setProcesses(Array.isArray(pRes) ? pRes : []);
    } catch { message.error('加载ERP数据失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, [search]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.post('/erp/sync');
      message.success('同步完成');
      fetchData();
    } catch { message.error('同步失败'); }
    finally { setSyncing(false); }
  };

  const showDetail = (item: any) => {
    setSelected(item);
    setDetailVisible(true);
  };

  const styleColumns = [
    { title: '款号', dataIndex: 'style_code', key: 'style_code' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '品类', dataIndex: 'category', key: 'category' },
    { title: '波段', dataIndex: 'season', key: 'season' },
    { title: '状态', dataIndex: 'status', key: 'status' },
    {
      title: '同步时间', dataIndex: 'last_synced_at', key: 'last_synced_at',
      render: (v: string) => v?.slice(0, 16) || '-',
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Button type="link" onClick={() => showDetail(record)}>查看BOM</Button>
      ),
    },
  ];

  const processColumns = [
    { title: '工序编码', dataIndex: 'process_code', key: 'process_code' },
    { title: '工序名称', dataIndex: 'process_name', key: 'process_name' },
    { title: '品类', dataIndex: 'category', key: 'category' },
    { title: '标准工时(分钟)', dataIndex: 'standard_time', key: 'standard_time' },
    { title: '单件工费', dataIndex: 'unit_cost', key: 'unit_cost' },
  ];

  return (
    <DashboardLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ marginRight: 8 }} />ERP 数据
        </Title>
        <Button icon={<SyncOutlined />} onClick={handleSync} loading={syncing}>
          触发同步
        </Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="款式总数" value={styles.length} suffix="件" /></Card></Col>
        <Col span={6}><Card><Statistic title="工序标准" value={processes.length} suffix="条" /></Card></Col>
        <Col span={6}><Card><Statistic title="品类数" value={new Set(styles.map((s: any) => s.category)).size} suffix="个" /></Card></Col>
        <Col span={6}><Card><Statistic title="最近同步" value="今日" /></Card></Col>
      </Row>

      <Card
        style={{ borderRadius: 8 }}
        tabList={[
          { key: 'styles', tab: `款式数据 (${styles.length})` },
          { key: 'processes', tab: `工序标准 (${processes.length})` },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === 'styles' ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <Input
                placeholder="搜索款号或描述..."
                prefix={<SearchOutlined />}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: 320 }}
                allowClear
              />
            </div>
            <Table
              dataSource={styles}
              columns={styleColumns}
              rowKey="style_code"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </>
        ) : (
          <Table
            dataSource={processes}
            columns={processColumns}
            rowKey="process_code"
            pagination={{ pageSize: 15 }}
            loading={loading}
            size="small"
          />
        )}
      </Card>

      <Modal
        title={`款式: ${selected?.style_code}`}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={600}
      >
        {selected && (
          <Descriptions column={1} size="small" layout="vertical">
            <Descriptions.Item label="描述">{selected.description || '-'}</Descriptions.Item>
            <Descriptions.Item label="品类">{selected.category || '-'}</Descriptions.Item>
            <Descriptions.Item label="波段">{selected.season || '-'}</Descriptions.Item>
            <Descriptions.Item label="BOM 物料清单">
              {selected.bom && Object.keys(selected.bom).length > 0
                ? <pre>{JSON.stringify(selected.bom, null, 2)}</pre>
                : '无'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </DashboardLayout>
  );
}
