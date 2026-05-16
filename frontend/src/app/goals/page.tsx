"use client";

import { Button, Card, DatePicker, Form, InputNumber, Select, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { api, type HealthGoal } from "@/lib/api";
import { demoGoals, today } from "@/lib/demo";

type GoalForm = {
  goal_type: string;
  target_weight_kg?: number;
  target_calories?: number;
  target_protein_g?: number;
  start_date: dayjs.Dayjs;
  end_date?: dayjs.Dayjs;
};

const goalLabels: Record<string, string> = {
  fat_loss: "减脂",
  muscle_gain: "增肌",
  maintenance: "维持健康",
  glucose_control: "控糖",
  sleep_improvement: "改善作息"
};

export default function GoalsPage() {
  const [form] = Form.useForm<GoalForm>();
  const [goals, setGoals] = useState<HealthGoal[]>(demoGoals);
  const [loading, setLoading] = useState(false);

  async function loadGoals() {
    try {
      const data = await api.listGoals();
      if (data.length > 0) {
        setGoals(data);
      }
    } catch {
      setGoals(demoGoals);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadGoals();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function createGoal(values: GoalForm) {
    setLoading(true);
    try {
      await api.createGoal({
        goal_type: values.goal_type,
        target_weight_kg: values.target_weight_kg ?? null,
        target_calories: values.target_calories ?? null,
        target_protein_g: values.target_protein_g ?? null,
        start_date: values.start_date.format("YYYY-MM-DD"),
        end_date: values.end_date?.format("YYYY-MM-DD") ?? null,
        status: "active"
      });
      message.success("目标已创建");
      form.resetFields();
      await loadGoals();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "创建失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          目标设置
        </Typography.Title>
        <Typography.Text type="secondary">
          将减脂、增肌、控糖或作息改善目标转成可计算的热量和蛋白质约束。
        </Typography.Text>
      </div>

      <div className="two-column-grid">
        <Card title="创建目标" className="panel-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={createGoal}
            initialValues={{ goal_type: "fat_loss", start_date: dayjs(today) }}
          >
            <Form.Item name="goal_type" label="目标类型" rules={[{ required: true }]}>
              <Select
                options={Object.entries(goalLabels).map(([value, label]) => ({ value, label }))}
              />
            </Form.Item>
            <Form.Item name="target_weight_kg" label="目标体重 kg">
              <InputNumber min={30} max={200} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="target_calories" label="目标热量 kcal">
              <InputNumber min={1000} max={5000} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="target_protein_g" label="目标蛋白质 g">
              <InputNumber min={0} max={300} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="start_date" label="开始日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="end_date" label="结束日期">
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              创建目标
            </Button>
          </Form>
        </Card>

        <Card title="目标列表" className="panel-card">
          <Table
            rowKey="id"
            dataSource={goals}
            pagination={false}
            className="compact-table"
            columns={[
              {
                title: "目标",
                dataIndex: "goal_type",
                render: (value: string) => goalLabels[value] ?? value
              },
              { title: "热量", dataIndex: "target_calories", render: (value) => value ?? "-" },
              { title: "蛋白质", dataIndex: "target_protein_g", render: (value) => value ?? "-" },
              {
                title: "状态",
                dataIndex: "status",
                render: (value: string) => <Tag color={value === "active" ? "green" : "default"}>{value}</Tag>
              }
            ]}
          />
        </Card>
      </div>
    </main>
  );
}
