'use client';

import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function WagesPage() {
  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>计件工资</h2>
        <p style={{ color: '#666' }}>查看生产报工和工资报表。</p>
      </div>
    </DashboardLayout>
  );
}
