'use client';

import DashboardLayout from '@/components/Layout/DashboardLayout';

export default function TryonPage() {
  return (
    <DashboardLayout>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>虚拟试衣</h2>
        <p style={{ color: '#666' }}>上传人物照片和服装图，AI 自动合成试穿效果。</p>
      </div>
    </DashboardLayout>
  );
}
