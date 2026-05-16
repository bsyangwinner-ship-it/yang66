"use client";

import { Alert, List, Tag, Typography } from "antd";
import type { RiskAlert } from "@/lib/api";

const severityColor: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue"
};

export function RiskList({ risks }: { risks: RiskAlert[] }) {
  if (risks.length === 0) {
    return <Alert type="success" showIcon message="当前没有开放风险" />;
  }

  return (
    <List
      dataSource={risks}
      renderItem={(risk) => (
        <List.Item>
          <List.Item.Meta
            title={
              <>
                {risk.title} <Tag color={severityColor[risk.severity] ?? "default"}>{risk.severity}</Tag>
              </>
            }
            description={
              <>
                <Typography.Paragraph style={{ marginBottom: 4 }}>{risk.description}</Typography.Paragraph>
                <Typography.Text type="secondary">{risk.suggestion}</Typography.Text>
              </>
            }
          />
        </List.Item>
      )}
    />
  );
}
