"use client";

import {
  AlertOutlined,
  BarChartOutlined,
  CalendarOutlined,
  DashboardOutlined,
  FileTextOutlined,
  FormOutlined,
  LineChartOutlined,
  LoginOutlined,
  MessageOutlined,
  ProfileOutlined,
  RobotOutlined,
  SettingOutlined,
  ThunderboltOutlined
} from "@ant-design/icons";
import { Layout, Menu, Space, Typography } from "antd";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const { Header, Sider, Content } = Layout;

const navItems = [
  { key: "/", icon: <DashboardOutlined />, label: <Link href="/">总览看板</Link> },
  { key: "/login", icon: <LoginOutlined />, label: <Link href="/login">登录</Link> },
  { key: "/goals", icon: <SettingOutlined />, label: <Link href="/goals">目标</Link> },
  { key: "/profile", icon: <ProfileOutlined />, label: <Link href="/profile">画像</Link> },
  { key: "/meals", icon: <FormOutlined />, label: <Link href="/meals">饮食记录</Link> },
  { key: "/analysis", icon: <BarChartOutlined />, label: <Link href="/analysis">营养分析</Link> },
  { key: "/risks", icon: <AlertOutlined />, label: <Link href="/risks">风险预警</Link> },
  { key: "/agent", icon: <RobotOutlined />, label: <Link href="/agent">Agent 对话</Link> },
  { key: "/meal-plans", icon: <CalendarOutlined />, label: <Link href="/meal-plans">餐单建议</Link> },
  { key: "/exercise", icon: <ThunderboltOutlined />, label: <Link href="/exercise">运动干预</Link> },
  { key: "/trends", icon: <LineChartOutlined />, label: <Link href="/trends">趋势追踪</Link> },
  { key: "/reports", icon: <FileTextOutlined />, label: <Link href="/reports">报告中心</Link> }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const selectedKey =
    navItems
      .map((item) => item.key)
      .filter((key) => pathname === key || (key !== "/" && pathname.startsWith(key)))
      .sort((a, b) => b.length - a.length)[0] ?? "/";

  return (
    <Layout className="app-shell">
      <Sider breakpoint="lg" collapsedWidth="0" width={236} className="app-sider">
        <div className="brand">
          <RobotOutlined />
          <span>Nutrition Agent</span>
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[selectedKey]} items={navItems} />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Space direction="vertical" size={0}>
            <Typography.Text strong>研究生营养分析与饮食决策系统</Typography.Text>
            <Typography.Text type="secondary">
              饮食分析、风险识别、运动干预和周期追踪工作台
            </Typography.Text>
          </Space>
          <Typography.Text type="secondary">
            <MessageOutlined /> Agentic AI
          </Typography.Text>
        </Header>
        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  );
}
