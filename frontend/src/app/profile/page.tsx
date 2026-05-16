"use client";

import { Button, Card, Form, Input, InputNumber, Select, Space, Switch, Typography, message } from "antd";
import { useCallback, useEffect, useState } from "react";
import { api, type FitnessProfile, type HealthProfile } from "@/lib/api";
import { demoFitness, demoProfile } from "@/lib/demo";

export default function ProfilePage() {
  const [profileForm] = Form.useForm<HealthProfile>();
  const [fitnessForm] = Form.useForm<FitnessProfile>();
  const [loading, setLoading] = useState(false);

  const loadProfile = useCallback(async () => {
    try {
      const [profile, fitness] = await Promise.all([api.getProfile(), api.getFitnessProfile()]);
      profileForm.setFieldsValue(profile);
      fitnessForm.setFieldsValue(fitness);
    } catch {
      profileForm.setFieldsValue(demoProfile);
      fitnessForm.setFieldsValue(demoFitness);
    }
  }, [fitnessForm, profileForm]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadProfile();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadProfile]);

  async function saveProfile(values: HealthProfile) {
    setLoading(true);
    try {
      await api.saveProfile(values);
      message.success("健康画像已保存");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "保存失败");
    } finally {
      setLoading(false);
    }
  }

  async function saveFitness(values: FitnessProfile) {
    setLoading(true);
    try {
      await api.saveFitnessProfile(values);
      message.success("运动画像已保存");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "保存失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          健康画像
        </Typography.Title>
        <Typography.Text type="secondary">
          画像是 Agent 进行热量目标、风险识别和运动干预的基础上下文。
        </Typography.Text>
      </div>

      <div className="two-column-grid">
        <Card title="基础健康信息" className="panel-card">
          <Form form={profileForm} layout="vertical" onFinish={saveProfile}>
            <Form.Item name="age" label="年龄" rules={[{ required: true }]}>
              <InputNumber min={18} max={80} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="gender" label="性别" rules={[{ required: true }]}>
              <Select options={[{ value: "female", label: "女" }, { value: "male", label: "男" }]} />
            </Form.Item>
            <Space.Compact block>
              <Form.Item name="height_cm" label="身高 cm" rules={[{ required: true }]} style={{ width: "50%" }}>
                <InputNumber min={100} max={230} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="weight_kg" label="体重 kg" rules={[{ required: true }]} style={{ width: "50%" }}>
                <InputNumber min={30} max={200} style={{ width: "100%" }} />
              </Form.Item>
            </Space.Compact>
            <Form.Item name="sleep_hours" label="平均睡眠小时" rules={[{ required: true }]}>
              <InputNumber min={0} max={24} step={0.5} style={{ width: "100%" }} />
            </Form.Item>
            <Space.Compact block>
              <Form.Item name="bedtime" label="入睡时间" style={{ width: "50%" }}>
                <Input placeholder="00:30:00" />
              </Form.Item>
              <Form.Item name="wake_time" label="起床时间" style={{ width: "50%" }}>
                <Input placeholder="07:30:00" />
              </Form.Item>
            </Space.Compact>
            <Form.Item name="activity_level" label="日常活动水平" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "sedentary", label: "久坐" },
                  { value: "light", label: "轻度活动" },
                  { value: "moderate", label: "中等活动" },
                  { value: "active", label: "高活动" }
                ]}
              />
            </Form.Item>
            <Form.Item name="exercise_frequency" label="每周运动次数" rules={[{ required: true }]}>
              <InputNumber min={0} max={14} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="dietary_preferences" label="饮食偏好">
              <Select mode="tags" />
            </Form.Item>
            <Form.Item name="allergies" label="过敏或忌口">
              <Select mode="tags" />
            </Form.Item>
            <Form.Item name="budget_level" label="预算">
              <Input placeholder="student / medium / high" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存健康画像
            </Button>
          </Form>
        </Card>

        <Card title="运动画像" className="panel-card">
          <Form form={fitnessForm} layout="vertical" onFinish={saveFitness}>
            <Form.Item name="exercise_level" label="运动水平" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "beginner", label: "初级" },
                  { value: "intermediate", label: "中级" },
                  { value: "advanced", label: "进阶" }
                ]}
              />
            </Form.Item>
            <Form.Item name="weekly_frequency" label="每周运动频次" rules={[{ required: true }]}>
              <InputNumber min={0} max={14} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="preferred_exercise" label="偏好运动">
              <Select mode="tags" />
            </Form.Item>
            <Form.Item name="available_time_minutes" label="可支配运动时间">
              <InputNumber min={0} max={300} addonAfter="分钟" style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="fitness_goal" label="运动目标">
              <Select
                options={[
                  { value: "fat_loss", label: "减脂" },
                  { value: "muscle_gain", label: "增肌" },
                  { value: "maintenance", label: "维持健康" }
                ]}
              />
            </Form.Item>
            <Form.Item name="contraindications" label="运动禁忌/医生建议">
              <Select mode="tags" />
            </Form.Item>
            <Form.Item name="is_sedentary" label="长期久坐" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存运动画像
            </Button>
          </Form>
        </Card>
      </div>
    </main>
  );
}
