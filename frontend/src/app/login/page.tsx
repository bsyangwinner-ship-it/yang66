"use client";

import { Alert, Button, Card, Form, Input, Segmented, Space, Typography, message } from "antd";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, clearToken, saveToken } from "@/lib/api";

type LoginForm = {
  name?: string;
  email: string;
  password: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [notice, setNotice] = useState<{
    type: "info" | "success" | "warning" | "error";
    message: string;
  } | null>(null);

  async function handleSubmit(values: LoginForm) {
    setNotice({
      type: "info",
      message: mode === "login" ? "正在登录，请稍候..." : "正在注册账号并自动登录，请稍候..."
    });
    setLoading(true);
    try {
      const result =
        mode === "login"
          ? await api.login(values.email, values.password)
          : await api.register(values.name || "研究生用户", values.email, values.password);
      saveToken(result.access_token);
      setNotice({
        type: "success",
        message: mode === "login" ? `登录成功：${result.user.email}` : `注册成功：${result.user.email}`
      });
      message.success(mode === "login" ? `已登录：${result.user.email}` : "注册成功，已自动登录");
      router.push("/profile");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "登录失败";
      setNotice({
        type: "error",
        message:
          errorMessage === "Email already registered"
            ? "该邮箱已经注册，请切换到登录模式，或换一个邮箱注册。"
            : errorMessage
      });
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmitFailed() {
    setNotice({
      type: "warning",
      message: "请先检查表单：邮箱必须有效，密码至少 8 位。"
    });
  }

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          {mode === "login" ? "登录" : "注册账号"}
        </Typography.Title>
        <Typography.Text type="secondary">
          {mode === "login"
            ? "登录后即可把页面表单连接到本地 FastAPI 数据。也可以直接浏览演示数据。"
            : "创建账号后会自动登录，并跳转到健康画像页面继续完善资料。"}
        </Typography.Text>
      </div>

      <Card className="panel-card" style={{ maxWidth: 560 }}>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Segmented
              block
              value={mode}
              options={[
                { label: "登录", value: "login" },
                { label: "注册", value: "register" }
              ]}
              onChange={(value) => {
                setMode(value as "login" | "register");
                setNotice(null);
              }}
            />
            <Alert
              showIcon
              type={mode === "login" ? "info" : "success"}
              message={
                mode === "login"
                  ? "当前是登录模式。输入已注册邮箱和密码后点击登录。"
                  : "当前是注册模式。填写邮箱和密码后点击“注册并登录”。"
              }
            />
            <Button
              onClick={() => {
                clearToken();
                message.success("本地 Token 已清除");
              }}
            >
              清除 Token
            </Button>
          </Space>

          {notice && <Alert showIcon type={notice.type} message={notice.message} />}

          <Form
            layout="vertical"
            onFinish={handleSubmit}
            onFinishFailed={handleSubmitFailed}
            initialValues={{ password: "Password123!" }}
          >
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
