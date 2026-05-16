"use client";

import {
  Alert,
  Button,
  Card,
  List,
  Progress,
  Space,
  Tag,
  Typography,
  message
} from "antd";
import { useEffect, useMemo, useState } from "react";
import { MetricCard } from "@/components/MetricCard";
import { NutritionSnapshot } from "@/components/NutritionSnapshot";
import { RiskList } from "@/components/RiskList";
import { TrendChart } from "@/components/TrendChart";
import { api, type NutritionAnalysis, type RiskAlert, type Report } from "@/lib/api";
import {
  demoAnalysis,
  demoReports,
  demoRisks,
  demoTrend,
  today,
  weekStart
} from "@/lib/demo";
import { formatCalories, formatPercent } from "@/lib/format";

export default function DashboardPage() {
  const [analysis, setAnalysis] = useState<NutritionAnalysis>(demoAnalysis);
  const [trend, setTrend] = useState<NutritionAnalysis[]>(demoTrend);
  const [risks, setRisks] = useState<RiskAlert[]>(demoRisks);
  const [reports, setReports] = useState<Report[]>(demoReports);
  const [loading, setLoading] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [analysisList, riskList, reportList] = await Promise.all([
        api.listAnalysis(weekStart, today),
        api.listRisks(),
        api.listReports()
      ]);
      if (analysisList.length > 0) {
        setTrend(analysisList);
        setAnalysis(analysisList[analysisList.length - 1]);
      }
      if (riskList.length > 0) {
        setRisks(riskList);
      }
      if (reportList.length > 0) {
        setReports(reportList);
      }
    } catch (error) {
      message.info("当前使用演示数据。登录并启动后端后可查看真实数据。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDashboard();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const proteinTarget = Number(analysis.evidence.target_protein_g ?? 85);
  const proteinProgress = Math.min(
    100,
    Math.round(((analysis.totals.protein_g ?? 0) / proteinTarget) * 100)
  );
  const openRiskCount = risks.filter((risk) => risk.status === "open").length;
  const latestReport = reports[0];
  const highSignalActions = useMemo(
    () => [
      "下一餐优先选择少油蛋白、两份蔬菜和半份主食。",
      "饮品改为无糖茶或白水，暂停奶茶和甜饮。",
      "晚餐后安排 10-20 分钟轻松步行，避免睡前高强度训练。"
    ],
    []
  );

  return (
    <main className="page-stack">
      <div className="page-title-row">
        <div>
          <Typography.Title level={2} className="page-heading">
            总览看板
          </Typography.Title>
          <Typography.Text type="secondary">
            把饮食记录、营养分析、风险预警、运动干预和报告追踪放在同一个工作台里。
          </Typography.Text>
        </div>
        <Button loading={loading} onClick={loadDashboard}>
          刷新数据
        </Button>
      </div>

      <div className="dashboard-grid">
        <MetricCard title="今日饮食评分" value={analysis.score} suffix="分" />
        <MetricCard title="今日热量" value={formatCalories(analysis.totals.calories ?? 0)} />
        <MetricCard title="蛋白质达标" value={formatPercent(proteinProgress)} />
        <MetricCard title="开放风险" value={openRiskCount} suffix="项" />
      </div>

      <div className="two-column-grid">
        <Card title="Agent 今日结论" className="dashboard-card">
          <Alert
            type={analysis.score >= 75 ? "success" : "warning"}
            showIcon
            message={analysis.summary}
            description="系统建议用于健康管理辅助，不替代医生或注册营养师建议。"
          />
          <List
            style={{ marginTop: 16 }}
            dataSource={highSignalActions}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        </Card>
        <NutritionSnapshot macroBalance={analysis.macro_balance} />
      </div>

      <div className="two-column-grid">
        <TrendChart title="近 7 天评分与热量趋势" data={trend} />
        <Card title="风险预警" className="dashboard-card">
          <RiskList risks={risks.slice(0, 4)} />
        </Card>
      </div>

      <Card title="最新报告与干预" className="dashboard-card">
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Typography.Text>{latestReport.summary}</Typography.Text>
          <Space wrap>
            <Tag color="blue">平均评分 {String(latestReport.metrics.average_score ?? "-")}</Tag>
            <Tag color="orange">开放风险 {String(latestReport.metrics.open_risk_count ?? "-")}</Tag>
            <Tag color="green">{latestReport.status}</Tag>
          </Space>
          <Progress percent={proteinProgress} status={proteinProgress >= 80 ? "success" : "active"} />
        </Space>
      </Card>
    </main>
  );
}
