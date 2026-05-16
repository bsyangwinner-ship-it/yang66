"use client";

import { Button, Card, DatePicker, Form, List, Select, Space, Table, Tag, Typography, message } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { api, type InterventionTask, type Report } from "@/lib/api";
import { demoInterventions, demoReports, today, weekStart } from "@/lib/demo";

type ReportForm = {
  report_type: "weekly" | "monthly";
  period: [dayjs.Dayjs, dayjs.Dayjs];
};

export default function ReportsPage() {
  const [form] = Form.useForm<ReportForm>();
  const [reports, setReports] = useState<Report[]>(demoReports);
  const [tasks, setTasks] = useState<InterventionTask[]>(demoInterventions);
  const [loading, setLoading] = useState(false);

  async function loadReports() {
    try {
      const [reportList, taskList] = await Promise.all([api.listReports(), api.listInterventions()]);
      if (reportList.length > 0) setReports(reportList);
      if (taskList.length > 0) setTasks(taskList);
    } catch {
      setReports(demoReports);
      setTasks(demoInterventions);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadReports();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function generate(values: ReportForm) {
    setLoading(true);
    try {
      await api.generateReport({
        report_type: values.report_type,
        period_start: values.period[0].format("YYYY-MM-DD"),
        period_end: values.period[1].format("YYYY-MM-DD")
      });
      message.success("报告已生成");
      await loadReports();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "生成失败");
    } finally {
      setLoading(false);
    }
  }

  async function completeTask(task: InterventionTask) {
    try {
      await api.updateIntervention(task.id, "completed");
      message.success("干预任务已完成");
      await loadReports();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "更新失败");
    }
  }

  const latestReport = reports[0];

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          报告中心
        </Typography.Title>
        <Typography.Text type="secondary">
          生成周报/月报，把趋势、风险和下一步干预任务沉淀下来。
        </Typography.Text>
      </div>

      <div className="two-column-grid">
        <Card title="生成报告" className="panel-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={generate}
            initialValues={{
              report_type: "weekly",
              period: [dayjs(weekStart), dayjs(today)]
            }}
          >
            <Form.Item name="report_type" label="报告类型">
              <Select options={[{ value: "weekly", label: "周报" }, { value: "monthly", label: "月报" }]} />
            </Form.Item>
            <Form.Item name="period" label="报告周期" rules={[{ required: true }]}>
              <DatePicker.RangePicker style={{ width: "100%" }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              生成报告
            </Button>
          </Form>
        </Card>

        <Card title="最新报告" className="panel-card">
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Typography.Title level={4}>{latestReport.title}</Typography.Title>
            <Typography.Text>{latestReport.summary}</Typography.Text>
            <Space wrap>
              <Tag color="blue">{latestReport.report_type}</Tag>
              <Tag color="green">{latestReport.status}</Tag>
              <Tag color="orange">开放风险 {String(latestReport.metrics.open_risk_count ?? "-")}</Tag>
            </Space>
            <Typography.Text type="secondary">{latestReport.export_object_key}</Typography.Text>
          </Space>
        </Card>
      </div>

      <div className="two-column-grid">
        <Card title="报告列表" className="panel-card">
          <Table
            rowKey="id"
            dataSource={reports}
            pagination={{ pageSize: 5 }}
            className="compact-table"
            columns={[
              { title: "标题", dataIndex: "title" },
              { title: "周期", render: (_, record) => `${record.period_start} ~ ${record.period_end}` },
              { title: "状态", dataIndex: "status" }
            ]}
          />
        </Card>
        <Card title="干预任务" className="panel-card">
          <List
            dataSource={tasks}
            renderItem={(task) => (
              <List.Item
                actions={[
                  <Button key="complete" size="small" onClick={() => completeTask(task)}>
                    完成
                  </Button>
                ]}
              >
                <List.Item.Meta
                  title={
                    <>
                      <Tag color={task.priority === "high" ? "red" : "blue"}>{task.priority}</Tag>
                      {task.title}
                    </>
                  }
                  description={`${task.description} · ${task.status}`}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    </main>
  );
}
