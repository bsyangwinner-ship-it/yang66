"use client";

import { Card, Descriptions, List, Space, Tag, Typography } from "antd";
import { demoAgentResult } from "@/lib/demo";
import { useAgentStore } from "@/stores/agentStore";

export default function MealPlansPage() {
  const latestResult = useAgentStore((state) => state.latestResult);
  const result = latestResult ?? demoAgentResult;
  const mealPlan = result.state.meal_plan ?? {};
  const todayAdjustments = (mealPlan.today_adjustment as string[] | undefined) ?? [];
  const tomorrowPlan = (mealPlan.tomorrow_plan as string[] | undefined) ?? [];
  const substitutions = (mealPlan.substitutions as Array<Record<string, string>> | undefined) ?? [];
  const evidence = (mealPlan.evidence as Record<string, unknown> | undefined) ?? {};

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          智能餐单
        </Typography.Title>
        <Typography.Text type="secondary">
          汇总 Agent 生成的今日调整、明日三餐和外卖/食堂替换建议。
        </Typography.Text>
      </div>

      <Card className="panel-card">
        <Space direction="vertical" size="small">
          <Tag color={latestResult ? "green" : "blue"}>{latestResult ? "最近一次 Agent 结果" : "演示结果"}</Tag>
          <Typography.Text>{String(mealPlan.strategy ?? "优先保证蛋白质、蔬菜和饮食规律。")}</Typography.Text>
        </Space>
      </Card>

      <div className="two-column-grid">
        <Card title="今日调整" className="panel-card">
          <List
            dataSource={todayAdjustments}
            renderItem={(item) => (
              <List.Item>
                <Tag color="blue">今日</Tag>
                {item}
              </List.Item>
            )}
          />
        </Card>
        <Card title="明日三餐" className="panel-card">
          <List
            dataSource={tomorrowPlan}
            renderItem={(item) => (
              <List.Item>
                <Tag color="green">餐单</Tag>
                {item}
              </List.Item>
            )}
          />
        </Card>
      </div>

      <div className="two-column-grid">
        <Card title="替换方案" className="panel-card">
          <List
            dataSource={substitutions}
            locale={{ emptyText: "当前未触发明确替换项，保持均衡搭配即可。" }}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={`${item.from ?? "原选择"} -> ${item.to ?? "推荐替换"}`}
                  description="用于降低油脂、糖分或提升优质营养密度"
                />
              </List.Item>
            )}
          />
        </Card>
        <Card title="推荐依据" className="panel-card">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="热量">{String(evidence.calories ?? "-")} kcal</Descriptions.Item>
            <Descriptions.Item label="蛋白质">{String(evidence.protein_g ?? "-")} g</Descriptions.Item>
            <Descriptions.Item label="风险类型">
              {Array.isArray(evidence.risk_types) ? evidence.risk_types.join("、") : "-"}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    </main>
  );
}
