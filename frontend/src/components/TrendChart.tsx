"use client";

import { Card } from "antd";
import ReactECharts from "echarts-for-react";
import type { NutritionAnalysis } from "@/lib/api";

type TrendChartProps = {
  title?: string;
  data: NutritionAnalysis[];
};

export function TrendChart({ title = "趋势追踪", data }: TrendChartProps) {
  const option = {
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 40, right: 24, top: 48, bottom: 32 },
    xAxis: {
      type: "category",
      data: data.map((item) => item.analysis_date.slice(5))
    },
    yAxis: [
      { type: "value", name: "评分", min: 0, max: 100 },
      { type: "value", name: "kcal" }
    ],
    series: [
      {
        name: "饮食评分",
        type: "line",
        smooth: true,
        data: data.map((item) => item.score)
      },
      {
        name: "热量",
        type: "bar",
        yAxisIndex: 1,
        data: data.map((item) => item.totals.calories ?? 0)
      }
    ]
  };

  return (
    <Card title={title} className="dashboard-card">
      <ReactECharts option={option} style={{ height: 320 }} />
    </Card>
  );
}
