"use client";

import { Card, Descriptions, List, Space, Tag, Typography } from "antd";
import { demoAgentResult, demoFitness } from "@/lib/demo";
import { useAgentStore } from "@/stores/agentStore";

export default function ExercisePage() {
  const latestResult = useAgentStore((state) => state.latestResult);
  const result = latestResult ?? demoAgentResult;
  const exercise = result.state.exercise_recommendation ?? {};
  const plans = (exercise.recommended_plan as Array<Record<string, string>> | undefined) ?? [];
  const safetyNotes = (exercise.safety_notes as string[] | undefined) ?? [
    "若出现疼痛、头晕或明显不适，应停止训练并咨询专业人士。"
  ];

  return (
    <main className="page-stack">
      <div>
        <Typography.Title level={2} className="page-heading">
          运动干预
        </Typography.Title>
        <Typography.Text type="secondary">
          根据饮食摄入、热量盈余、运动画像和安全边界生成饮食-运动协同建议。
        </Typography.Text>
      </div>

      <Card className="panel-card">
        <Space direction="vertical" size="small">
          <Tag color={latestResult ? "green" : "blue"}>{latestResult ? "最近一次 Agent 结果" : "演示结果"}</Tag>
          <Typography.Text>
            热量盈余：<Typography.Text strong>{String(exercise.calorie_surplus ?? "-")} kcal</Typography.Text>
          </Typography.Text>
          <Typography.Text>
            {String(exercise.weekly_baseline ?? "参考每周至少 150 分钟中等强度有氧运动，并结合每周 2 天以上肌力训练。")}
          </Typography.Text>
        </Space>
      </Card>

      <div className="two-column-grid">
        <Card title="推荐运动处方" className="panel-card">
          <List
            dataSource={plans}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <>
                      <Tag color={item.type === "力量" ? "green" : "blue"}>{item.type}</Tag>
                      {item.activity}
                    </>
                  }
                  description={`${item.duration} / ${item.intensity}强度 / ${item.reason}`}
                />
              </List.Item>
            )}
          />
        </Card>
        <Card title="运动画像与安全边界" className="panel-card">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="运动水平">{demoFitness.exercise_level}</Descriptions.Item>
            <Descriptions.Item label="每周频次">{demoFitness.weekly_frequency} 次</Descriptions.Item>
            <Descriptions.Item label="可用时间">
              {demoFitness.available_time_minutes} 分钟
            </Descriptions.Item>
            <Descriptions.Item label="偏好运动">
              {demoFitness.preferred_exercise.join("、")}
            </Descriptions.Item>
            <Descriptions.Item label="久坐">{demoFitness.is_sedentary ? "是" : "否"}</Descriptions.Item>
          </Descriptions>
        </Card>
      </div>

      <Card title="安全提醒" className="panel-card">
        <List
          dataSource={safetyNotes}
          renderItem={(item) => (
            <List.Item>
              <Tag color="orange">边界</Tag>
              {item}
            </List.Item>
          )}
        />
      </Card>
    </main>
  );
}
