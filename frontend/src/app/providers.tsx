'use client';

import { useEffect } from 'react';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { ConfigProvider, App as AntApp, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useThemeStore } from '@/stores/theme';

export default function Providers({ children }: { children: React.ReactNode }) {
  const themeMode = useThemeStore((s) => s.mode);
  const resolved = useThemeStore((s) => s.resolved);
  const init = useThemeStore((s) => s.init);

  useEffect(() => { init(); }, [init]);

  const algorithm = resolved === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm;

  return (
    <AntdRegistry>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm,
          token: {
            colorPrimary: '#667eea',
            borderRadius: 8,
          },
        }}
      >
        <AntApp>
          {children}
        </AntApp>
      </ConfigProvider>
    </AntdRegistry>
  );
}
