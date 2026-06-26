'use client';

import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function AdminUsersPage() {
  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>用户管理</h2>
        <p style={{ color: '#666' }}>系统用户管理（仅管理员）。</p>
      </div>
    </DashboardLayout>
  );
}
