"use client";

import { Card, Progress, Space, Typography } from "antd";
import { useEffect, useState } from "react";
import { TrendChart } from "@/components/TrendChart";
import { api, type NutritionAnalysis } from "@/lib/api";
import { demoTrend, today, weekStart } from "@/lib/demo";

export default function TrendsPage() {
  const [trend, setTrend] = useState<NutritionAnalysis[]>(demoTrend);

  useEffect(() => {
    async function loadTrend() {
      try {
        const data = await api.listAnalysis(weekStart, today);
        if (data.length > 0) {
          setTrend(data);
        }
      } catch {
        setTrend(demoTrend);
      }
    }
    void loadTrend();
  }, []);

  const averageScore = Math.round(
    trend.reduce((sum, item) => sum + item.score, 0) / Math.max(trend.length, 1)
  );
  const latest = trend[trend.length - 1];
  const first = trend[0];
  const scoreDelta = latest.score - first.score;

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          趋势追踪
        </Typography.Title>
        <Typography.Text type="secondary">
          按周观察评分、热量、蛋白质和风险变化，判断干预是否真正有效。
        </Typography.Text>
      </div>

      <div className="dashboard-grid">
        <Card className="metric-card">
          <Typography.Text type="secondary">平均评分</Typography.Text>
          <Progress percent={averageScore} status={averageScore >= 75 ? "success" : "active"} />
        </Card>
        <Card className="metric-card">
          <Typography.Text type="secondary">评分变化</Typography.Text>
          <Typography.Title level={3}>{scoreDelta >= 0 ? `+${scoreDelta}` : scoreDelta}</Typography.Title>
        </Card>
        <Card className="metric-card">
          <Typography.Text type="secondary">最新热量</Typography.Text>
          <Typography.Title level={3}>{latest.totals.calories ?? 0} kcal</Typography.Title>
        </Card>
        <Card className="metric-card">
          <Typography.Text type="secondary">最新蛋白质</Typography.Text>
          <Typography.Title level={3}>{latest.totals.protein_g ?? 0} g</Typography.Title>
        </Card>
      </div>

      <TrendChart title="评分与热量变化" data={trend} />

      <Card title="本周复盘重点" className="panel-card">
        <Space direction="vertical">
          <Typography.Text>优先观察奶茶、甜饮和夜宵频次是否下降。</Typography.Text>
          <Typography.Text>蛋白质达标率应逐步接近 80% 以上。</Typography.Text>
          <Typography.Text>晚餐时间和饭后低强度活动会影响睡眠与恢复。</Typography.Text>
        </Space>
      </Card>
    </main>
  );
}
