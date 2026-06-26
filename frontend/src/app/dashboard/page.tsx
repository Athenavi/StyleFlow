'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Spin } from 'antd';
import { useAuthStore } from '@/stores/auth';
import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function DashboardPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const { isAuthenticated, fetchMe: _fetchMe } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated()) {
      setChecking(false);
    } else {
      router.replace('/login');
    }
  }, []);

  if (checking) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>工作台</h2>
        <p style={{ color: '#666' }}>欢迎使用 StyleFlow，请从左侧菜单开始工作。</p>
      </div>
    </DashboardLayout>
  );
}
