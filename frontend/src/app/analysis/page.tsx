"use client";

import { Button, Card, DatePicker, Descriptions, Space, Typography, message } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { MetricCard } from "@/components/MetricCard";
import { NutritionSnapshot } from "@/components/NutritionSnapshot";
import { TrendChart } from "@/components/TrendChart";
import { api, type NutritionAnalysis } from "@/lib/api";
import { demoAnalysis, demoTrend, today, weekStart } from "@/lib/demo";
import { formatCalories, formatPercent } from "@/lib/format";

export default function AnalysisPage() {
  const [date, setDate] = useState(dayjs(today));
  const [analysis, setAnalysis] = useState<NutritionAnalysis>(demoAnalysis);
  const [trend, setTrend] = useState<NutritionAnalysis[]>(demoTrend);
  const [loading, setLoading] = useState(false);

  async function loadAnalysis() {
    try {
      const data = await api.listAnalysis(weekStart, today);
      if (data.length > 0) {
        setTrend(data);
        setAnalysis(data[data.length - 1]);
      }
    } catch {
      setTrend(demoTrend);
      setAnalysis(demoAnalysis);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAnalysis();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function generate() {
    setLoading(true);
    try {
      const result = await api.generateAnalysis(date.format("YYYY-MM-DD"));
      setAnalysis(result);
      await loadAnalysis();
      message.success("营养分析已生成");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "生成失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-stack">
      <div className="page-title-row">
        <div>
          <Typography.Title level={2} className="page-heading">
            营养分析
          </Typography.Title>
          <Typography.Text type="secondary">
            根据每日饮食记录生成评分、营养结构和证据数据。
          </Typography.Text>
        </div>
        <Space>
          <DatePicker value={date} onChange={(value) => value && setDate(value)} />
          <Button type="primary" loading={loading} onClick={generate}>
            生成分析
          </Button>
        </Space>
      </div>

      <div className="dashboard-grid">
        <MetricCard title="评分" value={analysis.score} suffix="分" />
        <MetricCard title="热量" value={formatCalories(analysis.totals.calories ?? 0)} />
        <MetricCard title="蛋白质" value={`${analysis.totals.protein_g ?? 0} g`} />
        <MetricCard title="糖摄入" value={`${analysis.totals.sugar_g ?? 0} g`} />
      </div>

      <div className="two-column-grid">
        <Card title="分析结论" className="panel-card">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="日期">{analysis.analysis_date}</Descriptions.Item>
            <Descriptions.Item label="总结">{analysis.summary}</Descriptions.Item>
            <Descriptions.Item label="蛋白质占比">
              {formatPercent(analysis.macro_balance.protein_pct ?? 0)}
            </Descriptions.Item>
            <Descriptions.Item label="碳水占比">
              {formatPercent(analysis.macro_balance.carbs_pct ?? 0)}
            </Descriptions.Item>
            <Descriptions.Item label="脂肪占比">
              {formatPercent(analysis.macro_balance.fat_pct ?? 0)}
            </Descriptions.Item>
          </Descriptions>
        </Card>
        <NutritionSnapshot macroBalance={analysis.macro_balance} />
      </div>

      <TrendChart title="周期变化" data={trend} />
    </main>
  );
}
