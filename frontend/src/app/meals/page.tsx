"use client";

import { Button, Card, DatePicker, Form, Input, InputNumber, Select, Table, Typography, message } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { api, type Meal } from "@/lib/api";
import { demoMeals, today } from "@/lib/demo";
import { formatCalories } from "@/lib/format";

type MealForm = {
  meal_date: dayjs.Dayjs;
  meal_time?: string;
  meal_type: string;
  location?: string;
  note?: string;
  name: string;
  amount: number;
  unit: string;
  calories: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
};

function mealCalories(meal: Meal): number {
  return meal.food_items.reduce((sum, item) => sum + item.calories, 0);
}

export default function MealsPage() {
  const [form] = Form.useForm<MealForm>();
  const [meals, setMeals] = useState<Meal[]>(demoMeals);
  const [loading, setLoading] = useState(false);

  async function loadMeals() {
    try {
      const data = await api.listMeals();
      if (data.length > 0) {
        setMeals(data);
      }
    } catch {
      setMeals(demoMeals);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadMeals();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function createMeal(values: MealForm) {
    setLoading(true);
    try {
      await api.createMeal({
        meal_date: values.meal_date.format("YYYY-MM-DD"),
        meal_time: values.meal_time || null,
        meal_type: values.meal_type,
        location: values.location || null,
        note: values.note || null,
        food_items: [
          {
            name: values.name,
            amount: values.amount,
            unit: values.unit,
            calories: values.calories,
            protein_g: values.protein_g,
            fat_g: values.fat_g,
            carbs_g: values.carbs_g,
            fiber_g: values.fiber_g,
            sugar_g: values.sugar_g,
            sodium_mg: values.sodium_mg
          }
        ]
      });
      message.success("饮食记录已保存");
      form.resetFields();
      await loadMeals();
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
          饮食记录
        </Typography.Title>
        <Typography.Text type="secondary">
          快速记录三餐、饮品、夜宵和核心营养指标，为后续分析提供数据。
        </Typography.Text>
      </div>

      <div className="two-column-grid">
        <Card title="新增记录" className="panel-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={createMeal}
            initialValues={{
              meal_date: dayjs(today),
              meal_type: "lunch",
              amount: 1,
              unit: "份",
              protein_g: 0,
              fat_g: 0,
              carbs_g: 0,
              fiber_g: 0,
              sugar_g: 0,
              sodium_mg: 0
            }}
          >
            <Form.Item name="meal_date" label="日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="meal_time" label="时间">
              <Input placeholder="12:30:00" />
            </Form.Item>
            <Form.Item name="meal_type" label="餐次" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "breakfast", label: "早餐" },
                  { value: "lunch", label: "午餐" },
                  { value: "dinner", label: "晚餐" },
                  { value: "snack", label: "零食" },
                  { value: "night_snack", label: "夜宵" }
                ]}
              />
            </Form.Item>
            <Form.Item name="location" label="来源">
              <Input placeholder="食堂 / 外卖 / 便利店" />
            </Form.Item>
            <Form.Item name="name" label="食物名称" rules={[{ required: true }]}>
              <Input placeholder="例如：鸡胸肉饭" />
            </Form.Item>
            <Form.Item name="calories" label="热量 kcal" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="amount" label="数量">
              <InputNumber min={0.1} step={0.1} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input />
            </Form.Item>
            <div className="three-column-grid">
              <Form.Item name="protein_g" label="蛋白质 g">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="fat_g" label="脂肪 g">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="carbs_g" label="碳水 g">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
            </div>
            <div className="three-column-grid">
              <Form.Item name="fiber_g" label="纤维 g">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="sugar_g" label="糖 g">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="sodium_mg" label="钠 mg">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
            </div>
            <Form.Item name="note" label="备注">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存记录
            </Button>
          </Form>
        </Card>

        <Card title="近期饮食" className="panel-card">
          <Table
            rowKey="id"
            dataSource={meals}
            pagination={{ pageSize: 6 }}
            className="compact-table"
            columns={[
              { title: "日期", dataIndex: "meal_date" },
              { title: "餐次", dataIndex: "meal_type" },
              {
                title: "食物",
                render: (_, record) => record.food_items.map((item) => item.name).join("、") || "-"
              },
              { title: "热量", render: (_, record) => formatCalories(mealCalories(record)) }
            ]}
          />
        </Card>
      </div>
    </main>
  );
}
