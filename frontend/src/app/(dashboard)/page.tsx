'use client';

import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>工作台</h2>
        <p style={{ color: '#666' }}>欢迎使用 StyleFlow，请从左侧菜单开始工作。</p>
      </div>
    </DashboardLayout>
  );
}
