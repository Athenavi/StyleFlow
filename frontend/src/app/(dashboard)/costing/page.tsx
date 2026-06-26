'use client';

import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Tag, Typography, Space, Spin, Empty, App,
  Row, Col, Statistic, InputNumber, message as Msg, Modal, Descriptions, Divider
} from 'antd';
import { CalculatorOutlined, ThunderboltOutlined, FileTextOutlined } from '@ant-design/icons';
import DashboardLayout from '@/components/Layout/DashboardLayout';
import api from '@/lib/api';

const { Title, Text } = Typography;

export default function CostingPage() {
  const { message } = App.useApp();
  const [costings, setCostings] = useState<any[]>([]);
  const [techpacks, setTechpacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tpId, setTpId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [resultVisible, setResultVisible] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/costing/list'),
      api.get('/techpacks'),
    ]).then(([cRes, tRes]: any) => {
      setCostings(cRes.data || cRes.results || cRes || []);
      setTechpacks(tRes.data || tRes.results || tRes || []);
    }).catch(() => message.error('加载失败'))
    .finally(() => setLoading(false));
  }, []);

  const handleCalculate = async () => {
    if (!tpId) { message.warning('请选择工艺单'); return; }
    setCalcLoading(true);
    try {
      const res: any = await api.post(`/costing/calculate?techpack_id=${tpId}`);
      setResult(res);
      setResultVisible(true);
    } catch { message.error('核算失败'); }
    finally { setCalcLoading(false); }
  };

  if (loading) return <DashboardLayout><Spin style={{ display: 'block', padding: 80 }} /></DashboardLayout>;

  return (
    <DashboardLayout>
      <Title level={3}><CalculatorOutlined style={{ marginRight: 8 }} />核工价</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="新核算" style={{ borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>选择工艺单</Text>
                <select value={tpId || ''} onChange={e => setTpId(Number(e.target.value) || null)}
                  style={{ width: '100%', padding: 8, marginTop: 4, borderRadius: 4, border: '1px solid #d9d9d9' }}>
                  <option value="">-- 请选择 --</option>
                  {techpacks.map((tp: any) => (
                    <option key={tp.id} value={tp.id}>{tp.title} ({tp.style_code || '无款号'})</option>
                  ))}
                </select>
              </div>
              <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleCalculate}
                loading={calcLoading} block size="large">
                自动核算
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          <Card title="历史核算" style={{ borderRadius: 8 }}>
            {costings.length === 0 ? <Empty description="暂无核算记录" /> : (
              <Table dataSource={costings} rowKey="id" size="small" pagination={{ pageSize: 5 }}
                columns={[
                  { title: '工艺单', dataIndex: 'techpack_id', key: 'techpack_id' },
                  { title: '工费', dataIndex: 'total_labor_cost', key: 'total_labor_cost',
                    render: (v: number) => `¥${v?.toFixed(2)}` },
                  { title: '状态', dataIndex: 'approved', key: 'approved',
                    render: (v: boolean) => v ? <Tag color="green">已批准</Tag> : <Tag>待审批</Tag> },
                  { title: '时间', dataIndex: 'created_at', key: 'created_at',
                    render: (v: string) => v?.slice(0, 10) },
                ]} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 核算结果弹窗 */}
      <Modal title="核算结果" open={resultVisible} onCancel={() => setResultVisible(false)}
        footer={
          <Button type="primary" onClick={() => setResultVisible(false)}>关闭</Button>
        } width={500}>
        {result && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Title level={4} style={{ color: '#1677ff' }}>总工费: ¥{result.total_labor_cost?.toFixed(2)}</Title>
            <Divider />
            <Title level={5}>工序明细</Title>
            {(result.process_breakdown || []).map((p: any, i: number) => (
              <Descriptions key={i} size="small" column={3} bordered>
                <Descriptions.Item label="工序" span={2}>{p.process_name}</Descriptions.Item>
                <Descriptions.Item label="工费">¥{p.unit_cost?.toFixed(2)}</Descriptions.Item>
              </Descriptions>
            ))}
          </Space>
        )}
      </Modal>
    </DashboardLayout>
  );
}
