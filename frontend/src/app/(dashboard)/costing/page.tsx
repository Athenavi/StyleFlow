'use client';

import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function CostingPage() {
  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>核工价</h2>
        <p style={{ color: '#666' }}>自动核算款式工价。</p>
      </div>
    </DashboardLayout>
  );
}
