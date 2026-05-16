# AI 驱动的研究生营养分析与饮食决策系统

面向在校研究生的 Agentic AI 饮食健康管理系统。系统目标是完成：

```text
用户提出目标 -> Agent 自动理解需求 -> 调用数据与工具 -> 分析饮食问题 -> 生成建议/餐单 -> 持续追踪与干预
```

当前进度：阶段 10，项目已完成。已实现认证、用户画像、运动画像、健康目标、饮食记录、每日营养分析、饮食风险识别、LangGraph Agent 工作流、RAG 知识库、周期报告与干预任务追踪、前端工作台页面与数据看板、Agent SSE 流式对话、工具调用轨迹展示、餐单与运动推荐结果页联动，并补齐 Docker Compose、Nginx、Prometheus、Grafana、OpenTelemetry Collector 和 GitHub Actions。

## 技术栈

- 前端：Next.js、React、TypeScript、Ant Design、ECharts、Zustand
- 后端：FastAPI、SQLAlchemy、Alembic、JWT、Celery
- Agent：LangGraph + OpenAI API，支持规则降级
- 数据库：PostgreSQL、pgvector，本地开发可用 SQLite
- 基础设施：Docker Compose、Redis、MinIO、Nginx、Prometheus、Grafana

## 本地启动

前端：

```bash
scripts\dev-frontend.cmd
```

访问：

```text
http://127.0.0.1:3000
```

后端：

```bash
scripts\dev-backend.cmd
```

访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

后端本地脚本默认使用 SQLite 并自动建表，方便没有 Docker/PostgreSQL 的环境直接试用 API。

完整 Docker Compose：

```bash
docker compose up --build
```

访问：

```text
http://localhost:8080
```

可观测性：

```text
Prometheus: http://localhost:9090
Grafana: http://localhost:3001
Metrics: http://localhost:8000/metrics
```

## 常用检查命令

前端：

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

后端：

```bash
cd backend
python -m ruff check .
python -m mypy app
python -m pytest
python -m compileall app
```

数据库迁移：

```bash
cd backend
alembic upgrade head
```

Docker Compose：

```bash
docker compose up --build
```

## 已实现 API

- `/api/v1/auth/*`：注册、登录、刷新、登出、当前用户。
- `/api/v1/profile/me`：健康画像。
- `/api/v1/fitness-profile/me`：运动画像。
- `/api/v1/goals`：健康目标。
- `/api/v1/meals`：饮食记录与食物条目。
- `/api/v1/analysis/daily`：每日营养分析。
- `/api/v1/analysis/summary`：分析汇总。
- `/api/v1/risks`：风险预警与状态更新。
- `/api/v1/agent/capabilities`：Agent 能力说明。
- `/api/v1/agent/chat`：创建会话并触发完整 Agent 分析。
- `/api/v1/agent/chat/stream`：创建会话并以 SSE 返回节点进度、工具调用、答案片段和最终结果。
- `/api/v1/agent/sessions`：Agent 会话。
- `/api/v1/agent/sessions/{session_id}/messages`：会话消息与 Agent 触发。
- `/api/v1/agent/runs/{run_id}`：Agent 运行状态。
- `/api/v1/agent/runs/{run_id}/tool-calls`：Agent 工具调用轨迹。
- `/api/v1/knowledge/documents`：知识文档导入与查询。
- `/api/v1/knowledge/documents/{document_id}/embed`：文档分块并写入向量。
- `/api/v1/knowledge/search`：知识库相似度检索，Agent 会通过 `rag_search` 工具引用上下文。
- `/api/v1/reports/generate`：生成周报/月报，支持同步生成和 Celery 异步入口。
- `/api/v1/reports`：报告列表与报告详情。
- `/api/v1/interventions`：干预任务列表与状态追踪。
- `/api/v1/interventions/schedule`：从已完成报告生成干预任务。
- `/metrics`：Prometheus 文本指标。

## 已实现页面

- `/`：总览看板，展示评分、热量、蛋白质达标、开放风险、趋势图和最新报告。
- `/login`：登录、注册和本地 Token 管理。
- `/profile`：健康画像与运动画像表单。
- `/goals`：健康目标创建与列表。
- `/meals`：饮食记录创建与近期记录。
- `/analysis`：每日营养分析生成、营养结构和趋势图。
- `/risks`：风险评估、风险列表和改善建议。
- `/agent`：Agent 对话入口，展示 SSE 流式答案、节点时间线、工具调用轨迹、风险、餐单、运动和 RAG 上下文。
- `/meal-plans`：读取最近一次 Agent 结果，展示餐单策略、今日调整、明日三餐、替换方案和推荐依据。
- `/exercise`：读取最近一次 Agent 结果，展示饮食驱动运动处方、热量盈余、长期约束和安全提醒。
- `/trends`：评分、热量和蛋白质趋势追踪。
- `/reports`：周报/月报生成、报告列表和干预任务管理。

更多说明见 [API 文档](docs/API.md)、[数据库文档](docs/DATABASE.md)、[Agent 架构](docs/AGENT_ARCHITECTURE.md)、[部署文档](docs/DEPLOYMENT.md) 和 [最终验收记录](docs/ACCEPTANCE.md)。
