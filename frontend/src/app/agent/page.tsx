"use client";

import { SendOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Collapse,
  DatePicker,
  Form,
  Input,
  List,
  Progress,
  Space,
  Tag,
  Timeline,
  Typography,
  message
} from "antd";
import dayjs from "dayjs";
import { useState } from "react";
import { api, type AgentRunResult, type AgentStreamEvent, type AgentToolCall } from "@/lib/api";
import { demoAgentResult, today } from "@/lib/demo";
import { useAgentStore } from "@/stores/agentStore";

type ChatForm = {
  message: string;
  analysis_date: dayjs.Dayjs;
};

type TraceItem = {
  key: string;
  label: string;
  node?: string;
  preview?: Record<string, unknown>;
};

function formatPreviewValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export default function AgentPage() {
  const [form] = Form.useForm<ChatForm>();
  const [result, setResult] = useState<AgentRunResult>(demoAgentResult);
  const [traceItems, setTraceItems] = useState<TraceItem[]>([]);
  const [toolCalls, setToolCalls] = useState<AgentToolCall[]>([]);
  const [streamedAnswer, setStreamedAnswer] = useState(demoAgentResult.assistant_message.content);
  const [loading, setLoading] = useState(false);
  const setLatestResult = useAgentStore((state) => state.setLatestResult);

  function handleStreamEvent(event: AgentStreamEvent) {
    if (event.type === "session") {
      setTraceItems([
        {
          key: `session-${event.run?.id ?? Date.now()}`,
          label: "创建会话与运行",
          preview: { run_id: event.run?.id, status: event.run?.status }
        }
      ]);
      return;
    }
    if (event.type === "node" && event.label) {
      setTraceItems((items) => [
        ...items,
        {
          key: `${event.node ?? "node"}-${items.length}`,
          label: event.label ?? event.node ?? "Agent 节点",
          node: event.node,
          preview: event.preview
        }
      ]);
      return;
    }
    if (event.type === "tool_call" && event.tool_call) {
      setToolCalls((items) => [...items, event.tool_call as AgentToolCall]);
      return;
    }
    if (event.type === "answer_delta" && event.content) {
      setStreamedAnswer((content) => `${content}${event.content}`);
      return;
    }
    if (event.type === "final" && event.result) {
      setResult(event.result);
      setLatestResult(event.result);
      setStreamedAnswer((content) => content || event.result?.assistant_message.content || "");
      return;
    }
    if (event.type === "error") {
      message.error(event.detail ?? "Agent 流式分析失败");
    }
  }

  async function send(values: ChatForm) {
    setLoading(true);
    setTraceItems([]);
    setToolCalls([]);
    setStreamedAnswer("");
    const analysisDate = values.analysis_date.format("YYYY-MM-DD");
    try {
      await api.streamAgentChat(values.message, analysisDate, handleStreamEvent);
      message.success("Agent 流式分析完成");
    } catch (error) {
      try {
        const data = await api.agentChat(values.message, analysisDate);
        setResult(data);
        setLatestResult(data);
        setStreamedAnswer(data.assistant_message.content);
        message.warning("流式接口暂不可用，已切换为同步分析结果");
      } catch {
        message.error(error instanceof Error ? error.message : "Agent 调用失败，已保留演示结果");
        setResult(demoAgentResult);
        setLatestResult(demoAgentResult);
        setStreamedAnswer(demoAgentResult.assistant_message.content);
      }
    } finally {
      setLoading(false);
    }
  }

  const progressPercent = traceItems.length ? Math.min(100, Math.round((traceItems.length / 9) * 100)) : 0;
  const mealTips = (result.state.meal_plan?.today_adjustment as string[] | undefined) ?? [];
  const exercisePlan =
    (result.state.exercise_recommendation?.recommended_plan as Array<Record<string, string>> | undefined) ?? [];
  const ragContext = result.state.rag_context ?? [];
  const risks = result.state.risks ?? [];
  const analysis = result.state.nutrition_analysis;
  const toolItems = toolCalls.map((call, index) => ({
    key: `${call.tool_name}-${index}`,
    label: (
      <Space wrap>
        <Tag color={call.status === "success" ? "green" : "red"}>{call.status}</Tag>
        <Typography.Text strong>{call.tool_name}</Typography.Text>
        <Typography.Text type="secondary">{call.latency_ms}ms</Typography.Text>
      </Space>
    ),
    children: (
      <div className="tool-call-grid">
        <pre>{JSON.stringify(call.input, null, 2)}</pre>
        <pre>{JSON.stringify(call.output, null, 2)}</pre>
      </div>
    )
  }));

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          Agent 对话
        </Typography.Title>
        <Typography.Text type="secondary">
          输入饮食问题或健康目标，系统会串联画像、分析、风险、RAG、餐单和运动干预工具。
        </Typography.Text>
      </div>

      <div className="two-column-grid">
        <Card title="向 Agent 提问" className="panel-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={send}
            initialValues={{
              analysis_date: dayjs(today),
              message: "今天中午吃了炸鸡汉堡，晚上又喝了奶茶，我今天应该怎么调整？"
            }}
          >
            <Form.Item name="analysis_date" label="分析日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="message" label="问题" rules={[{ required: true }]}>
              <Input.TextArea rows={5} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<SendOutlined />}>
              启动 Agent
            </Button>
          </Form>
        </Card>

        <Card title="流式建议" className="panel-card">
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Tag color={result.run.status === "completed" ? "green" : "blue"}>{result.run.status}</Tag>
            <Progress percent={progressPercent} size="small" status={loading ? "active" : "normal"} />
            <Typography.Paragraph className="agent-response">{streamedAnswer}</Typography.Paragraph>
          </Space>
        </Card>
      </div>

      <div className="two-column-grid">
        <Card title="Agent 执行过程" className="panel-card">
          {traceItems.length ? (
            <Timeline
              items={traceItems.map((item) => ({
                color: "blue",
                children: (
                  <Space direction="vertical" size={4}>
                    <Typography.Text strong>{item.label}</Typography.Text>
                    {item.preview ? (
                      <Typography.Text type="secondary">
                        {Object.entries(item.preview)
                          .map(([key, value]) => `${key}: ${formatPreviewValue(value)}`)
                          .join(" / ")}
                      </Typography.Text>
                    ) : null}
                  </Space>
                )
              }))}
            />
          ) : (
            <Alert message="提交问题后，这里会展示 Agent 节点流转过程。" type="info" showIcon />
          )}
        </Card>

        <Card title="工具调用轨迹" className="panel-card">
          {toolItems.length ? (
            <Collapse items={toolItems} size="small" />
          ) : (
            <Alert message="营养计算、风险识别、RAG、餐单和运动工具会在这里实时记录。" type="info" showIcon />
          )}
        </Card>
      </div>

      <div className="three-column-grid">
        <Card title="分析与风险" className="panel-card">
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            <Typography.Text>
              饮食评分：<Typography.Text strong>{analysis?.score ?? "-"}</Typography.Text>
            </Typography.Text>
            <Typography.Text>
              热量：<Typography.Text strong>{analysis?.totals.calories ?? "-"} kcal</Typography.Text>
            </Typography.Text>
            <List
              dataSource={risks.slice(0, 3)}
              renderItem={(item) => (
                <List.Item>
                  <Tag color={item.severity === "high" ? "red" : "orange"}>{item.severity}</Tag>
                  {item.title}
                </List.Item>
              )}
            />
          </Space>
        </Card>
        <Card title="餐单调整" className="panel-card">
          <List dataSource={mealTips} renderItem={(item) => <List.Item>{item}</List.Item>} />
        </Card>
        <Card title="运动干预" className="panel-card">
          <List
            dataSource={exercisePlan}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={`${item.activity ?? "运动"} ${item.duration ?? ""}`}
                  description={item.reason}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>

      <Card title="RAG 参考" className="panel-card">
        <List
          dataSource={ragContext}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta title={String(item.title ?? "知识片段")} description={String(item.source ?? "")} />
            </List.Item>
          )}
        />
      </Card>
    </main>
  );
}
