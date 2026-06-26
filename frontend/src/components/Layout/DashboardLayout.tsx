'use client';

import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, theme, Spin, Space, Tooltip } from 'antd';
import {
  DashboardOutlined,
  PictureOutlined,
  ThunderboltOutlined,
  FileTextOutlined,
  ApartmentOutlined,
  DollarOutlined,
  CalculatorOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  FolderOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';

const { Header, Sider, Content } = Layout;


interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, isAuthenticated, fetchMe } = useAuthStore();
  const { token: themeToken } = theme.useToken();
  const themeMode = useThemeStore((s) => s.mode);
  const resolved = useThemeStore((s) => s.resolved);
  const setMode = useThemeStore((s) => s.setMode);

  const role = user?.role || '';

  const nextTheme = themeMode === 'light' ? 'dark' : themeMode === 'dark' ? 'system' : 'light';
  const ThemeIcon = resolved === 'dark' ? <MoonOutlined /> : themeMode === 'system' ? <DesktopOutlined /> : <SunOutlined />;

  // 基于角色的菜单栏
  const menuItems: any[] = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  ];

  // 设计师/版师 可见
  if (['designer', 'pattern_maker', 'admin'].includes(role)) {
    menuItems.push({
      key: 'design', icon: <PictureOutlined />, label: 'AI 设计工坊',
      children: [
        { key: '/design/generate', icon: <ThunderboltOutlined />, label: 'AI 生成' },
        { key: '/design/gallery', icon: <PictureOutlined />, label: '设计稿库' },
      ],
    });
  }

  // 所有人可见
  menuItems.push(
    { key: '/tryon', icon: <ThunderboltOutlined />, label: '虚拟试衣' },
  );

  if (['pattern_maker', 'designer', 'admin'].includes(role)) {
    menuItems.push({ key: '/techpack', icon: <FileTextOutlined />, label: '工艺单' });
  }

  menuItems.push(
    { key: '/workflow', icon: <ApartmentOutlined />, label: '工作流' },
  );

  if (['accountant', 'admin'].includes(role)) {
    menuItems.push(
      { key: '/costing', icon: <CalculatorOutlined />, label: '核工价' },
      { key: '/wages', icon: <DollarOutlined />, label: '计件工资' },
    );
  }

  menuItems.push(
    { key: '/erp', icon: <DatabaseOutlined />, label: 'ERP 数据' },
    { key: '/media', icon: <FolderOutlined />, label: '媒体库' },
    { key: '/admin/settings', icon: <SettingOutlined />, label: 'AI 配置' },
  );

  // On mount: verify token and fetch user
  useEffect(() => {
    if (isAuthenticated()) {
      fetchMe().finally(() => setInitializing(false));
    } else {
      router.push('/login');
    }
  }, []);

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: '个人设置' },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') logout();
      if (key === 'profile') router.push('/admin/users');
    },
  };

  const selectedKey = '/' + pathname.split('/').filter(Boolean).slice(0, 2).join('/');
  const openKeys = pathname.split('/').filter(Boolean).length > 2
    ? [pathname.split('/').slice(0, -1).join('/')]
    : [];

  if (initializing) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large"><span style={{ color: '#1677ff' }}>加载中...</span></Spin>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="light"
        style={{ borderRight: '1px solid #f0f0f0' }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: collapsed ? 16 : 20,
          fontWeight: 700,
          color: themeToken.colorPrimary,
          borderBottom: '1px solid #f0f0f0',
        }}>
          {collapsed ? 'SF' : 'StyleFlow'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={openKeys}
          items={menuItems}
          onClick={({ key }) => router.push(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          height: 64,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Space>
            <Tooltip title={`主题: ${themeMode}，点击切换`}>
              <Button type="text" icon={ThemeIcon} onClick={() => setMode(nextTheme)} />
            </Tooltip>
            <Dropdown menu={userMenu} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar icon={<UserOutlined />} src={user?.avatar || undefined} />
                <span>{user?.username || '用户'}</span>
                <span style={{ fontSize: 12, color: '#999' }}>({user?.role || '-'})</span>
              </div>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: 24, minHeight: 280 }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
