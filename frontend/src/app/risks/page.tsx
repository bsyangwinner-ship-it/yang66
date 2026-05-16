"use client";

import { Button, Card, DatePicker, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { RiskList } from "@/components/RiskList";
import { api, type RiskAlert } from "@/lib/api";
import { demoRisks, today } from "@/lib/demo";

const severityColor: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue"
};

export default function RisksPage() {
  const [date, setDate] = useState(dayjs(today));
  const [risks, setRisks] = useState<RiskAlert[]>(demoRisks);
  const [loading, setLoading] = useState(false);

  async function loadRisks() {
    try {
      const data = await api.listRisks();
      if (data.length > 0) {
        setRisks(data);
      }
    } catch {
      setRisks(demoRisks);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRisks();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function evaluate() {
    setLoading(true);
    try {
      const data = await api.evaluateRisks(date.format("YYYY-MM-DD"));
      setRisks(data);
      message.success("风险已重新评估");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "评估失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-stack">
      <div className="page-title-row">
        <div>
          <Typography.Title level={2} className="page-heading">
            风险预警
          </Typography.Title>
          <Typography.Text type="secondary">
            自动识别高糖、蛋白质不足、膳食纤维偏低、夜宵和晚餐过晚等问题。
          </Typography.Text>
        </div>
        <div>
          <DatePicker value={date} onChange={(value) => value && setDate(value)} />
          <Button type="primary" loading={loading} onClick={evaluate} style={{ marginLeft: 8 }}>
            重新评估
          </Button>
        </div>
      </div>

      <div className="two-column-grid">
        <Card title="当前重点风险" className="panel-card">
          <RiskList risks={risks.filter((risk) => risk.status === "open").slice(0, 5)} />
        </Card>
        <Card title="风险明细" className="panel-card">
          <Table
            rowKey="id"
            dataSource={risks}
            pagination={{ pageSize: 6 }}
            className="compact-table"
            columns={[
              { title: "风险", dataIndex: "title" },
              {
                title: "等级",
                dataIndex: "severity",
                render: (value: string) => <Tag color={severityColor[value] ?? "default"}>{value}</Tag>
              },
              { title: "状态", dataIndex: "status" },
              { title: "建议", dataIndex: "suggestion" }
            ]}
          />
        </Card>
      </div>
    </main>
  );
}
