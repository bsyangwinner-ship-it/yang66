"use client";

import { Card } from "antd";
import ReactECharts from "echarts-for-react";

type NutritionSnapshotProps = {
  macroBalance?: Record<string, number>;
};

export function NutritionSnapshot({ macroBalance }: NutritionSnapshotProps) {
  const option = {
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        name: "营养占比",
        type: "pie",
        radius: ["45%", "68%"],
        data: [
          { value: macroBalance?.carbs_pct ?? 54, name: "碳水" },
          { value: macroBalance?.protein_pct ?? 12, name: "蛋白质" },
          { value: macroBalance?.fat_pct ?? 34, name: "脂肪" }
        ]
      }
    ]
  };

  return (
    <Card title="今日营养结构" className="dashboard-card">
      <ReactECharts option={option} style={{ height: 260 }} />
    </Card>
  );
}
