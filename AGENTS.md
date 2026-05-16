# 项目协作规则

## 1. 项目定位

本项目是“AI 驱动的研究生营养分析与饮食决策系统”，目标是构建一个 Agentic AI 饮食管理应用。核心链路为：

```text
用户提出目标 -> Agent 自动理解需求 -> 调用数据与工具 -> 分析饮食问题 -> 生成建议/餐单 -> 持续追踪与干预
```

系统应体现完整工程能力，而不是只做聊天页面。所有实现都应围绕饮食数据、营养分析、风险识别、个性化餐单和持续干预闭环展开。

## 2. 技术栈约定

### 2.1 前端

- 使用 Next.js + React + TypeScript。
- 使用 Ant Design 构建后台工作台风格界面。
- 使用 Apache ECharts 做热量趋势、营养占比、风险变化等图表。
- 使用 Zustand 管理全局轻量状态。
- 使用 React Hook Form + Zod 处理表单与校验。
- 使用 SSE 作为 Agent 流式输出的优先方案，WebSocket 用于双向实时会话扩展。

### 2.2 后端

- 使用 Python FastAPI。
- 使用 LangGraph 编排 Agent 工作流。
- 使用 OpenAI API 作为 LLM 调用入口。
- 使用 Celery + Redis 处理异步任务。
- 使用 OAuth2 + JWT 做身份认证。
- 使用 SQLAlchemy + Alembic 管理数据库模型和迁移。

### 2.3 数据与基础设施

- 使用 PostgreSQL 存储核心业务数据。
- 使用 pgvector 存储和检索知识库向量。
- 使用 Redis 做缓存、队列和临时任务状态。
- 使用 S3 / MinIO 存储上传图片、导出报告等文件。
- 使用 Docker Compose 做本地基础设施编排。

## 3. 代码组织规则

- 前端代码放在 `frontend/`。
- 后端代码放在 `backend/`。
- 文档放在 `docs/`。
- 部署与观测配置放在 `infra/`。
- 不在根目录堆放业务代码。
- 每个阶段只完成 `PLAN.md` 中定义的一个阶段，避免跨阶段实现。
- 新增功能时优先复用已有服务、模型和组件。
- 健康建议必须保留“辅助参考，不替代医生或注册营养师”的边界。

## 4. Agent 实现规则

- Agent 工作流以 LangGraph 为主。
- Agent 节点应保持职责单一：规划、画像理解、营养分析、风险识别、餐单推荐、干预追踪。
- 新增的运动干预推荐 Agent 负责饮食-运动协同决策，不能替代营养分析 Agent 或风险识别 Agent 的确定性计算。
- 关键营养计算和风险判断必须由确定性工具完成，LLM 只负责理解、编排、解释和生成自然语言建议。
- 运动推荐必须由规则层先计算热量盈余、用户运动基础、可支配时间和安全限制，再由 LLM 组织解释和个性化表达。
- 运动建议需参考成人每周至少 150 分钟中等强度有氧运动和每周 2 天以上肌力训练，但不能对初级、久坐或存在运动禁忌的用户给出高风险方案。
- 所有 Agent 工具调用应记录输入、输出、状态和耗时。
- Agent 输出应尽量包含证据数据，例如近 7 天平均热量、蛋白质达标率、风险触发原因。
- 无 OpenAI API Key 时，系统必须提供规则引擎和模板回复作为降级方案，保证本地演示可运行。

## 5. 启动方式

### 5.1 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:3000
```

### 5.2 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

默认访问：

```text
http://localhost:8000
```

接口文档：

```text
http://localhost:8000/docs
```

### 5.3 Docker Compose

后续阶段补齐 Docker 配置后，使用：

```bash
docker compose up --build
```

## 6. 测试与检查方式

### 6.1 前端

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

### 6.2 后端

```bash
cd backend
python -m ruff check .
python -m mypy app
python -m pytest
python -m compileall app
```

### 6.3 每阶段验收

每个阶段结束后必须执行：

- lint
- typecheck
- test
- build

如果某项因为本地缺少 Node、npm、Docker、PostgreSQL、Redis 或外部网络而无法执行，需要在阶段汇报中明确说明阻塞原因。

## 7. 环境变量规则

- 所有配置通过环境变量注入。
- `.env` 不提交仓库。
- `.env.example` 必须覆盖前端、后端、数据库、Redis、OpenAI、MinIO/JWT 等关键配置。
- 没有 OpenAI API Key 时，后端应启用本地规则降级模式。

## 8. 完成标准

阶段完成必须满足：

- 代码结构清晰，符合 `PLAN.md` 当前阶段范围。
- 本阶段新增功能有基础测试。
- lint、typecheck、test、build 尽可能全部通过。
- 如果存在无法通过项，必须说明原因、影响和下一步修复方式。
- README、API 文档、部署文档和项目总结在最终阶段补齐。

项目最终完成必须满足：

- 前端页面完整，覆盖看板、目标、画像、饮食记录、分析、风险、Agent 对话、餐单、趋势和报告。
- 后端 API 可运行，接口文档可访问。
- Agent 能完成“目标理解 -> 数据读取 -> 分析 -> 风险识别 -> 餐单推荐 -> 干预追踪”的闭环。
- PostgreSQL、pgvector、Redis、Celery、S3/MinIO 具备清晰配置和部署说明。
- 本地和部署环境都有明确启动方式。
