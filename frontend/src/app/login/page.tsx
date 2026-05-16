"use client";

import { Button, Card, Form, Input, Space, Typography, message } from "antd";
import { useState } from "react";
import { api, clearToken, saveToken } from "@/lib/api";

type LoginForm = {
  name?: string;
  email: string;
  password: string;
};

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");

  async function handleSubmit(values: LoginForm) {
    setLoading(true);
    try {
      const result =
        mode === "login"
          ? await api.login(values.email, values.password)
          : await api.register(values.name || "研究生用户", values.email, values.password);
      saveToken(result.access_token);
      message.success(`已登录：${result.user.email}`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          登录
        </Typography.Title>
        <Typography.Text type="secondary">
          登录后即可把页面表单连接到本地 FastAPI 数据。也可以直接浏览演示数据。
        </Typography.Text>
      </div>

      <Card className="panel-card" style={{ maxWidth: 560 }}>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Space>
            <Button type={mode === "login" ? "primary" : "default"} onClick={() => setMode("login")}>
              登录
            </Button>
            <Button
              type={mode === "register" ? "primary" : "default"}
              onClick={() => setMode("register")}
            >
              注册
            </Button>
            <Button
              onClick={() => {
                clearToken();
                message.success("本地 Token 已清除");
              }}
            >
              清除 Token
            </Button>
          </Space>

          <Form layout="vertical" onFinish={handleSubmit} initialValues={{ password: "Password123!" }}>
            {mode === "register" && (
              <Form.Item name="name" label="昵称">
                <Input placeholder="例如：科研高压型用户" />
              </Form.Item>
            )}
            <Form.Item
              name="email"
              label="邮箱"
              rules={[{ required: true, type: "email", message: "请输入有效邮箱" }]}
            >
              <Input placeholder="student@example.com" />
            </Form.Item>
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, min: 8, message: "至少 8 位" }]}
            >
              <Input.Password />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              {mode === "login" ? "登录" : "注册并登录"}
            </Button>
          </Form>
        </Space>
      </Card>
    </main>
  );
}
