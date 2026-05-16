# Agent 架构文档

本项目 Agent 主方案为 LangGraph + OpenAI API。

规划中的 Agent 节点：

- 规划 Agent
- 用户画像 Agent
- 营养分析 Agent
- 风险识别 Agent
- 餐单推荐 Agent
- 运动干预推荐 Agent
- 干预追踪 Agent

## 运动干预推荐 Agent

正式名称：基于饮食摄入分析的智能运动推荐 Agent。

简化名称：饮食-运动协同决策 Agent。

职责：

- 根据当日总热量、三大营养素比例、高糖高脂摄入、晚餐过量和夜宵情况生成运动建议。
- 结合身高、体重、年龄、健康目标、日常活动水平、运动频率和可支配运动时间。
- 读取运动禁忌或医生建议字段，避免不合适的运动推荐。
- 根据热量盈余推荐快走、慢跑、骑行、跳操等补偿方案。
- 根据蛋白质摄入和增肌/塑形目标推荐力量训练或自重抗阻训练。
- 根据晚餐高油高糖、作息混乱等情况推荐饭后低强度步行或恢复性运动。

基础约束：

- 参考成人每周至少 150 分钟中等强度有氧运动。
- 结合每周 2 天以上肌力训练。
- 对初级运动者、长期久坐者和存在限制的用户优先给出低风险方案。

工具：

- `calculate_calorie_surplus()`
- `estimate_activity_energy_cost()`
- `get_user_fitness_profile()`
- `query_recent_diet_trend()`
- `generate_exercise_plan()`

## 阶段 5 实现状态

阶段 5 已落地真实 LangGraph 工作流和工具调用持久化。当前工作流为：

```text
planner -> profile -> nutrition -> risk -> meal_plan -> exercise -> intervention
```

每次 Agent 运行会持久化：

- 会话记录
- 用户消息与助手消息
- Agent Run 状态
- 工具调用输入、输出、状态和耗时

无 OpenAI API Key 时，系统使用确定性规则和模板建议完成本地演示，保证“目标理解 -> 数据读取 -> 营养分析 -> 风险识别 -> 餐单推荐 -> 运动干预 -> 持续追踪”的闭环可运行。

## 阶段 6 实现状态

阶段 6 已新增 RAG 知识库和 `rag_search` 工具。当前工作流升级为：

```text
planner -> profile -> nutrition -> risk -> knowledge -> meal_plan -> exercise -> intervention
```

知识库能力：

- `knowledge_documents` 保存营养知识、饮食模板、运动建议和风险规则原文。
- `knowledge_chunks` 保存分块文本、Embedding、来源和元数据。
- PostgreSQL 生产环境使用 pgvector，迁移启用 `vector` 扩展并创建 HNSW 索引。
- 无 OpenAI API Key 时使用确定性哈希向量，保证本地离线演示和测试可运行。
- Agent 在生成餐单和最终回复前先检索知识库，可在输出中引用检索到的知识标题与来源。

## 阶段 9 实现状态

阶段 9 已新增 Agent SSE 流式输出。`POST /api/v1/agent/chat/stream` 会在同一次运行中推送：

- `session`：会话与运行 ID。
- `node`：LangGraph 节点完成事件和关键预览数据。
- `tool_call`：工具名称、输入、输出、状态和耗时。
- `answer_delta`：最终建议文本片段。
- `final`：完整 Agent 结果，可直接驱动餐单页和运动干预页。

前端 `/agent` 页面已展示节点时间线、工具调用轨迹、流式建议、风险、餐单、运动干预和 RAG 上下文。`/meal-plans` 与 `/exercise` 页面会读取最近一次 Agent 输出，使“对话分析 -> 推荐结果页”的产品路径保持一致。

## 阶段 10 实现状态

阶段 10 已补齐 Agent 项目的运维交付能力：

- 后端提供 `/metrics`，可观测 HTTP 请求量、耗时和应用版本信息。
- Prometheus 负责采集后端指标，Grafana 预置基础看板。
- OpenTelemetry Collector 已配置，后端可通过 `OTEL_ENABLED=true` 开启可选 Trace 导出。
- Nginx 统一代理前端、后端 API、文档、健康检查和 SSE 流式接口。
- GitHub Actions 覆盖前端、后端和 Docker Compose 配置检查。

这些配置让项目不只是功能 Demo，而是具备基础工程交付、监控和持续集成能力的 Agentic AI 应用。
