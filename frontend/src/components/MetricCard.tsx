import { Card, Statistic } from "antd";
import type { ReactNode } from "react";

type MetricCardProps = {
  title: string;
  value: string | number;
  suffix?: string;
  icon?: ReactNode;
};

export function MetricCard({ title, value, suffix, icon }: MetricCardProps) {
  return (
    <Card className="metric-card">
      <Statistic title={title} value={value} suffix={suffix} prefix={icon} />
    </Card>
  );
}
