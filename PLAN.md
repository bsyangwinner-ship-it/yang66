# AI 驱动的研究生营养分析与饮食决策系统开发计划

## 1. 需求分析

### 1.1 项目定位

本项目从传统“饮食健康数据看板”升级为 Agentic AI 饮食决策系统。系统核心链路为：

```text
用户提出目标 -> Agent 自动理解需求 -> 调用数据与工具 -> 分析饮食问题 -> 生成建议/餐单 -> 持续追踪与干预
```

系统不仅回答“今天吃得怎么样”，还要能像一个具备工具调用能力的营养管理 Agent：理解目标、读取健康画像、分析历史饮食、识别风险、生成餐单、跟踪效果，并在长期周期中进行健康干预。

### 1.2 目标用户

- 年龄集中在 22-30 岁的在校研究生。
- 学习、科研、实习压力高，久坐、熬夜、饮食不规律较常见。
- 饮食依赖食堂、外卖、便利店。
- 有健康意识，但缺少专业营养知识、持续记录习惯和个性化反馈。

### 1.3 核心痛点

- 不知道每天吃得是否健康。
- 不理解热量、蛋白质、脂肪、碳水、膳食纤维等营养结构。
- 减脂、增肌、控糖、改善作息等目标无法转化成具体餐单。
- 饮食问题难以及时发现，缺少连续反馈。
- 普通 AI 问答容易停留在泛泛建议，无法结合用户长期数据。
- 缺少周报、月报、趋势追踪和持续干预机制。

### 1.4 核心目标

- 构建研究生饮食健康数据看板。
- 基于画像、目标、饮食记录实现个性化营养评估。
- 使用 Agent 工作流完成多步骤饮食分析和推荐。
- 通过风险识别 Agent 自动发现潜在饮食问题。
- 通过运动干预推荐 Agent 将饮食摄入、热量盈余、营养结构和运动习惯联动起来，生成个性化运动建议。
- 使用 RAG 检索营养知识、饮食模板和历史案例，增强建议可靠性。
- 通过干预追踪 Agent 生成周报/月报，观察目标达成和风险变化。

## 2. 整体技术架构

### 2.1 架构分层

```text
前端交互层
  └─ 饮食看板 / AI 对话 / 目标设置 / 报告展示 / 风险预警 / 趋势追踪

后端服务层
  └─ 用户服务 / 权限服务 / 饮食记录服务 / 分析服务 / 推荐服务 / Agent 服务 / 报告服务

Agent 智能层
  └─ 规划 Agent / 用户画像 Agent / 营养分析 Agent / 风险识别 Agent / 餐单推荐 Agent / 运动干预推荐 Agent / 干预追踪 Agent

数据层
  └─ PostgreSQL / pgvector / Redis / S3 或 MinIO / PostgreSQL JSONB

部署与运维层
  └─ Docker / Nginx / CI/CD / OpenTelemetry / Prometheus / Grafana
```

### 2.2 推荐技术栈

#### 前端

| 模块 | 技术 |
| --- | --- |
| 前端框架 | Next.js + React + TypeScript |
| UI 组件库 | Ant Design |
| 图表展示 | Apache ECharts |
| 状态管理 | Zustand，必要时可扩展 Redux Toolkit |
| 实时输出 | SSE 优先，WebSocket 用于双向会话 |
| 表单与校验 | React Hook Form + Zod |
| 测试 | Vitest + React Testing Library |

#### 后端

| 模块 | 技术 |
| --- | --- |
| 后端框架 | Python FastAPI |
| Agent 编排 | LangGraph |
| 备选 Agent 能力 | OpenAI Agents SDK |
| LLM 调用 | OpenAI API |
| 异步任务 | Celery |
| 缓存与队列 | Redis |
| 接口协议 | REST API + SSE + WebSocket |
| 身份认证 | OAuth2 + JWT |
| 测试 | Pytest |

#### 数据库与存储

| 数据类型 | 技术 |
| --- | --- |
| 核心业务数据 | PostgreSQL |
| 向量检索 | pgvector |
| 缓存和任务状态 | Redis |
| 文件与图片 | S3 / MinIO |
| 半结构化 AI 结果 | PostgreSQL JSONB |

#### 部署与运维

| 模块 | 技术 |
| --- | --- |
| 容器化 | Docker / Docker Compose |
| 网关 | Nginx |
| HTTPS | Let's Encrypt |
| CI/CD | GitHub Actions |
| 指标监控 | Prometheus |
| 可视化监控 | Grafana |
| 链路追踪 | OpenTelemetry |
| 生产扩展 | Kubernetes 可选 |

### 2.3 Agent 框架选择

主方案：LangGraph + OpenAI API。

原因：

- LangGraph 适合多步骤任务流转。
- 支持 Agent 状态持久化、中断恢复和长周期任务管理。
- 适合“目标识别 -> 数据读取 -> 营养计算 -> 风险识别 -> 餐单推荐 -> 干预追踪”的业务流程。
- OpenAI API 提供 LLM 推理、工具调用和自然语言生成能力。

备选增强：OpenAI Agents SDK。

适用场景：

- 快速实现 Agent 工具调用。
- Agent 之间 handoff。
- Guardrails 和 Tracing 调试。
- 后续如果需要突出 Agent 原生工具链，可在 LangGraph 主流程外增加 SDK 实验模块。

## 3. Agent 功能模块设计

### 3.1 规划 Agent

职责：

- 理解用户输入目标，如“我想减脂”“最近熬夜多，晚餐怎么吃”。
- 判断需要调用哪些工具和子 Agent。
- 生成执行计划并驱动 LangGraph 工作流。
- 在必要时要求用户补充信息。

典型流程：

```text
识别目标 -> 检查健康画像完整度 -> 读取近 7 天饮食 -> 调用营养分析 -> 调用风险识别 -> 调用餐单推荐 -> 输出建议
```

### 3.2 用户画像 Agent

职责：

- 读取并理解身高、体重、年龄、性别。
- 理解作息时间、运动频率、健康目标。
- 解析饮食偏好、过敏、忌口、预算、食堂/外卖偏好。
- 输出推荐和分析所需的用户画像摘要。

### 3.3 营养分析 Agent

职责：

- 统计每日热量摄入。
- 分析蛋白质、脂肪、碳水比例。
- 计算膳食纤维、糖、钠等关键指标。
- 判断营养结构是否均衡。
- 生成饮食评分和解释。

### 3.4 风险识别 Agent

自动发现：

- 热量长期超标或过低。
- 蛋白质摄入不足。
- 膳食纤维偏低。
- 高糖饮食频繁。
- 晚餐过晚或夜宵频繁。
- 早餐缺失。
- 钠摄入偏高。
- 减脂期热量缺口过大。
- 增肌期蛋白质和总热量不足。

输出：

- 风险类型。
- 风险等级。
- 证据数据。
- 改善建议。

### 3.5 餐单推荐 Agent

结合用户目标生成：

- 今日饮食建议。
- 明日三餐推荐。
- 一周膳食计划。
- 食物替换方案。
- 外卖场景选择建议。
- 食堂场景选择建议。

推荐结果需要包含：

- 每餐建议。
- 大致热量和宏量营养素。
- 推荐原因。
- 替代选项。
- 执行难度。

### 3.6 运动干预推荐 Agent

正式名称：基于饮食摄入分析的智能运动推荐 Agent。

简化名称：饮食-运动协同决策 Agent。

核心目标：

- 根据当日或周期性饮食情况，结合健康目标、身体基础信息与运动习惯，推荐合适的运动类型、运动时长和运动强度。
- 实现热量摄入与消耗协同管理。
- 对高热量饮食给出可执行的运动补偿建议，但不机械要求“吃多少就必须运动多少”。
- 当蛋白质摄入充足时，优先推荐力量训练或自重抗阻训练。
- 当碳水摄入较高时，推荐中等强度有氧、间歇快走、骑行或跳操。
- 当晚餐高油高糖或用餐过晚时，推荐饭后低强度步行，当日避免过高强度训练。
- 为减脂、增肌、塑形、维持健康和改善作息生成动态运动策略。

输入信息：

- 饮食数据：当日总热量、三大营养素比例、高糖高脂高油摄入、晚餐是否过量、夜宵情况、一周饮食波动趋势。
- 用户画像：身高、体重、年龄、健康目标、基础代谢率、日常活动水平、当前运动频率、可支配运动时间。
- 健康与安全边界：是否初级运动者、是否长期久坐、运动禁忌、医生建议或特殊限制。

基础约束：

- 参考成人每周至少 150 分钟中等强度有氧运动。
- 结合每周 2 天以上肌力训练作为长期健康基础。
- 对久坐、初级运动者、晚间进食过晚或存在运动限制的用户，优先推荐低风险、低门槛方案。

输出内容：

- `exercise_goal`：运动目标，如减脂、增肌、维持健康、改善作息。
- `recommended_plan`：运动类型、活动、时长、强度和推荐原因。
- `safety_notes`：安全提醒和不适合进行的训练。
- `adjustment_reason`：与饮食分析、风险识别和用户目标相关的解释。

可调用工具：

- `calculate_calorie_surplus()`：计算热量盈余或缺口。
- `estimate_activity_energy_cost()`：估算不同运动的能量消耗。
- `get_user_fitness_profile()`：读取用户运动画像。
- `query_recent_diet_trend()`：查询近期饮食趋势。
- `generate_exercise_plan()`：生成结构化运动处方。

### 3.7 干预追踪 Agent

职责：

- 比较本周与上周饮食变化。
- 判断风险项是否下降。
- 跟踪健康目标完成度。
- 生成周报和月报。
- 提醒用户下一阶段重点改进事项。

这种“规划-执行-反馈”的 Agent 模式，是本项目区别于普通 Chatbot 的关键。加入运动干预后，整体链路变为：

```text
用户画像 Agent -> 营养分析 Agent -> 饮食风险识别 Agent -> 餐单推荐 Agent -> 运动干预推荐 Agent -> 长期健康追踪 Agent
```

### 3.8 RAG 与知识库

知识库内容：

- 营养学基础知识。
- 常见食物营养表。
- 食堂/外卖选择策略。
- 减脂、增肌、控糖、改善作息建议模板。
- 饮食风险干预规则。
- 成人运动建议、常见运动消耗估算、运动禁忌和恢复训练模板。
- 历史优质案例。

技术实现：

- 使用 OpenAI Embeddings 生成向量。
- 使用 PostgreSQL + pgvector 存储和检索。
- 使用 HNSW 或 IVFFlat 索引提升检索性能。
- Agent 回答复杂问题前先检索知识，再生成建议。

### 3.9 工具调用层

Agent 可调用工具：

- 用户画像读取工具。
- 饮食记录查询工具。
- 营养计算工具。
- 风险识别工具。
- 餐单生成工具。
- 热量盈余计算工具。
- 运动能耗估算工具。
- 运动处方生成工具。
- RAG 检索工具。
- 报告生成工具。
- 干预任务创建工具。
- 文件/图片解析工具。

可选增强：

- 引入 MCP 工具协议，让 Agent 标准化接入数据库查询、营养计算器、日历、用户文件和外部知识源。

## 4. 页面结构

前端使用 Next.js App Router，整体风格偏数据看板和工作台，使用 Ant Design 组件体系。

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| 登录注册 | `/login` | OAuth2/JWT 登录入口 |
| 总览看板 | `/` | 健康评分、热量趋势、营养结构、风险摘要、Agent 建议 |
| 目标设置 | `/goals` | 设置减脂、增肌、维持体重、控糖、改善作息等目标 |
| 健康画像 | `/profile` | 编辑身高、体重、年龄、作息、运动、偏好、忌口 |
| 饮食记录 | `/meals` | 记录三餐、零食、饮品、夜宵和营养信息 |
| Agent 对话 | `/agent` | 目标输入、流式分析、工具调用过程展示、最终建议 |
| 营养分析 | `/analysis` | 当日/区间营养摄入分析和饮食评分 |
| 风险预警 | `/risks` | 风险项、等级、证据、改善方案 |
| 智能餐单 | `/meal-plans` | 今日建议、明日三餐、一周计划、替换方案 |
| 运动干预 | `/exercise` | 根据饮食摄入、健康目标和运动画像生成运动推荐 |
| 趋势追踪 | `/trends` | 热量、宏量营养素、饮食规律、风险变化趋势 |
| 报告中心 | `/reports` | 周报、月报、导出文件 |
| 知识库管理 | `/knowledge` | 营养知识、食物数据、规则模板管理，后期可做管理员页 |

### 4.1 主要组件

- `AppShell`：整体布局和导航。
- `GoalSelector`：健康目标选择。
- `ProfileForm`：健康画像表单。
- `MealForm`：饮食记录表单。
- `FoodItemTable`：食物条目编辑表。
- `MetricCard`：关键指标卡片。
- `NutritionPieChart`：营养素占比图。
- `TrendLineChart`：趋势折线图。
- `RiskTimeline`：风险变化时间线。
- `AgentChatPanel`：Agent 对话和流式响应。
- `ToolCallTrace`：Agent 工具调用过程展示。
- `MealPlanCard`：餐单推荐卡片。
- `ExercisePlanCard`：运动干预推荐卡片。
- `ReportViewer`：周报/月报展示。

### 4.2 前端交互重点

- Agent 对话页使用 SSE 展示流式分析过程。
- 对于需要双向实时交互的任务，预留 WebSocket。
- 表单使用 React Hook Form + Zod 做前端校验。
- 状态管理使用 Zustand 保存当前用户、目标、日期筛选、会话状态。
- 图表使用 ECharts 展示热量趋势、营养占比、风险变化、目标完成度。

## 5. 数据库设计

数据库使用 PostgreSQL。向量检索使用 pgvector。灵活 AI 结果和 Agent 状态使用 JSONB。缓存、队列和临时状态使用 Redis。文件使用 S3 / MinIO。

### 5.1 核心业务表

#### users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 用户 ID |
| name | VARCHAR | 昵称 |
| email | VARCHAR UNIQUE | 邮箱 |
| password_hash | VARCHAR | 密码哈希 |
| role | VARCHAR | user/admin |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### refresh_tokens

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | Token ID |
| user_id | UUID FK | 用户 ID |
| token_hash | VARCHAR | Refresh Token 哈希 |
| expires_at | TIMESTAMP | 过期时间 |
| revoked_at | TIMESTAMP NULL | 撤销时间 |
| created_at | TIMESTAMP | 创建时间 |

#### health_profiles

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 画像 ID |
| user_id | UUID FK | 用户 ID |
| age | INTEGER | 年龄 |
| gender | VARCHAR | 性别或自定义 |
| height_cm | NUMERIC | 身高 |
| weight_kg | NUMERIC | 体重 |
| sleep_hours | NUMERIC | 平均睡眠时长 |
| bedtime | TIME NULL | 通常入睡时间 |
| wake_time | TIME NULL | 通常起床时间 |
| activity_level | VARCHAR | 久坐、轻度、中度、高强度 |
| exercise_frequency | INTEGER | 每周运动次数 |
| dietary_preferences | JSONB | 饮食偏好 |
| allergies | JSONB | 过敏或忌口 |
| budget_level | VARCHAR NULL | 饮食预算 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### health_goals

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 目标 ID |
| user_id | UUID FK | 用户 ID |
| goal_type | VARCHAR | 减脂、增肌、维持体重、控糖、改善作息 |
| target_weight_kg | NUMERIC NULL | 目标体重 |
| target_calories | NUMERIC NULL | 目标热量 |
| target_protein_g | NUMERIC NULL | 目标蛋白质 |
| start_date | DATE | 开始日期 |
| end_date | DATE NULL | 结束日期 |
| status | VARCHAR | active、paused、completed |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### meals

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 餐次 ID |
| user_id | UUID FK | 用户 ID |
| meal_date | DATE | 日期 |
| meal_time | TIME NULL | 用餐时间 |
| meal_type | VARCHAR | 早餐、午餐、晚餐、加餐、饮品、夜宵 |
| location | VARCHAR NULL | 食堂、外卖、便利店、自炊 |
| source | VARCHAR | manual、image、agent |
| note | TEXT NULL | 备注 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### food_items

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 食物条目 ID |
| meal_id | UUID FK | 餐次 ID |
| name | VARCHAR | 食物名称 |
| amount | NUMERIC | 数量 |
| unit | VARCHAR | 份、克、杯等 |
| calories | NUMERIC | 热量 kcal |
| protein_g | NUMERIC | 蛋白质 |
| fat_g | NUMERIC | 脂肪 |
| carbs_g | NUMERIC | 碳水 |
| fiber_g | NUMERIC | 膳食纤维 |
| sugar_g | NUMERIC | 糖 |
| sodium_mg | NUMERIC | 钠 |
| confidence | NUMERIC NULL | AI 估算置信度 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 5.2 分析、风险、推荐与报告表

#### nutrition_analyses

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 分析 ID |
| user_id | UUID FK | 用户 ID |
| goal_id | UUID FK NULL | 关联目标 |
| analysis_date | DATE | 分析日期 |
| period_type | VARCHAR | daily、weekly、monthly |
| score | INTEGER | 饮食评分 |
| totals | JSONB | 热量和营养总量 |
| macro_balance | JSONB | 宏量营养素占比 |
| evidence | JSONB | 计算证据 |
| summary | TEXT | 分析摘要 |
| created_at | TIMESTAMP | 创建时间 |

#### risk_alerts

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 风险 ID |
| user_id | UUID FK | 用户 ID |
| analysis_id | UUID FK NULL | 对应分析 |
| risk_type | VARCHAR | 高糖、蛋白质不足、晚餐过晚等 |
| severity | VARCHAR | low、medium、high |
| title | VARCHAR | 风险标题 |
| description | TEXT | 风险解释 |
| evidence | JSONB | 风险证据 |
| suggestion | TEXT | 改善建议 |
| status | VARCHAR | open、resolved、ignored |
| created_at | TIMESTAMP | 创建时间 |
| resolved_at | TIMESTAMP NULL | 解决时间 |

#### meal_plans

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 餐单 ID |
| user_id | UUID FK | 用户 ID |
| goal_id | UUID FK NULL | 关联目标 |
| plan_type | VARCHAR | today、tomorrow、weekly |
| title | VARCHAR | 餐单标题 |
| meals | JSONB | 餐单结构 |
| nutrition_targets | JSONB | 目标营养值 |
| rationale | TEXT | 推荐依据 |
| created_by | VARCHAR | agent、rule、admin |
| created_at | TIMESTAMP | 创建时间 |

#### user_fitness_profiles

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 运动画像 ID |
| user_id | UUID FK | 用户 ID |
| exercise_level | VARCHAR | beginner、intermediate、advanced |
| weekly_frequency | INTEGER | 每周运动次数 |
| preferred_exercise | JSONB | 偏好运动，如快走、跑步、骑行、力量训练 |
| available_time_minutes | INTEGER | 单次可支配运动时间 |
| fitness_goal | VARCHAR | 减脂、增肌、塑形、维持健康、改善作息 |
| contraindications | JSONB | 运动禁忌、医生建议或特殊限制 |
| is_sedentary | BOOLEAN | 是否长期久坐 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### exercise_recommendations

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 运动推荐 ID |
| user_id | UUID FK | 用户 ID |
| diet_analysis_id | UUID FK NULL | 关联营养分析 |
| exercise_goal | VARCHAR | 运动目标 |
| recommendation_content | JSONB | 结构化运动处方 |
| exercise_type | VARCHAR | 有氧、力量、恢复、混合 |
| duration_minutes | INTEGER | 推荐总时长 |
| intensity | VARCHAR | 低、中、高 |
| rationale | TEXT | 推荐理由 |
| safety_notes | TEXT | 安全提醒 |
| created_at | TIMESTAMP | 创建时间 |

#### exercise_feedback

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 反馈 ID |
| user_id | UUID FK | 用户 ID |
| recommendation_id | UUID FK | 推荐 ID |
| completed | BOOLEAN | 是否完成 |
| actual_duration_minutes | INTEGER NULL | 实际运动时长 |
| satisfaction_score | INTEGER NULL | 满意度评分 |
| note | TEXT NULL | 反馈备注 |
| created_at | TIMESTAMP | 创建时间 |

#### recommendations

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 推荐 ID |
| user_id | UUID FK | 用户 ID |
| target_goal | VARCHAR | 推荐目标 |
| title | VARCHAR | 推荐标题 |
| content | TEXT | 推荐内容 |
| actions | JSONB | 可执行动作 |
| source_analysis_id | UUID FK NULL | 来源分析 |
| created_at | TIMESTAMP | 创建时间 |

#### intervention_tasks

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 干预任务 ID |
| user_id | UUID FK | 用户 ID |
| goal_id | UUID FK NULL | 关联目标 |
| task_type | VARCHAR | reminder、checkin、report |
| title | VARCHAR | 任务标题 |
| payload | JSONB | 任务内容 |
| scheduled_at | TIMESTAMP | 计划执行时间 |
| status | VARCHAR | pending、running、done、failed |
| created_at | TIMESTAMP | 创建时间 |

#### reports

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 报告 ID |
| user_id | UUID FK | 用户 ID |
| report_type | VARCHAR | weekly、monthly |
| period_start | DATE | 开始日期 |
| period_end | DATE | 结束日期 |
| content | JSONB | 报告结构化内容 |
| summary | TEXT | 报告摘要 |
| file_url | VARCHAR NULL | 导出文件地址 |
| created_at | TIMESTAMP | 创建时间 |

### 5.3 Agent 与知识库表

#### agent_sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 会话 ID |
| user_id | UUID FK | 用户 ID |
| title | VARCHAR | 会话标题 |
| goal_snapshot | JSONB | 会话目标快照 |
| status | VARCHAR | active、completed、failed |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### agent_messages

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 消息 ID |
| session_id | UUID FK | 会话 ID |
| role | VARCHAR | user、assistant、tool、system |
| content | TEXT | 消息内容 |
| metadata | JSONB | 附加信息 |
| created_at | TIMESTAMP | 创建时间 |

#### agent_runs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 运行 ID |
| session_id | UUID FK | 会话 ID |
| graph_name | VARCHAR | LangGraph 名称 |
| state | JSONB | Agent 状态 |
| status | VARCHAR | running、completed、failed、interrupted |
| started_at | TIMESTAMP | 开始时间 |
| finished_at | TIMESTAMP NULL | 结束时间 |

#### agent_tool_calls

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 工具调用 ID |
| run_id | UUID FK | Agent 运行 ID |
| tool_name | VARCHAR | 工具名称 |
| input | JSONB | 工具输入 |
| output | JSONB | 工具输出 |
| status | VARCHAR | success、failed |
| latency_ms | INTEGER | 耗时 |
| created_at | TIMESTAMP | 创建时间 |

#### knowledge_documents

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 文档 ID |
| title | VARCHAR | 标题 |
| source | VARCHAR | 来源 |
| category | VARCHAR | 分类 |
| content | TEXT | 原始内容 |
| metadata | JSONB | 元数据 |
| created_at | TIMESTAMP | 创建时间 |

#### knowledge_chunks

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 分块 ID |
| document_id | UUID FK | 文档 ID |
| chunk_text | TEXT | 分块文本 |
| embedding | VECTOR | pgvector 向量 |
| metadata | JSONB | 元数据 |
| created_at | TIMESTAMP | 创建时间 |

#### uploaded_files

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUID PK | 文件 ID |
| user_id | UUID FK | 用户 ID |
| file_name | VARCHAR | 文件名 |
| file_type | VARCHAR | 文件类型 |
| object_key | VARCHAR | S3/MinIO 对象 Key |
| url | VARCHAR | 文件访问地址 |
| metadata | JSONB | 元数据 |
| created_at | TIMESTAMP | 创建时间 |

### 5.4 主要索引

- `users.email`
- `refresh_tokens.user_id`
- `health_profiles.user_id`
- `health_goals.user_id, health_goals.status`
- `meals.user_id, meals.meal_date`
- `food_items.meal_id`
- `nutrition_analyses.user_id, nutrition_analyses.analysis_date, nutrition_analyses.period_type`
- `risk_alerts.user_id, risk_alerts.status, risk_alerts.created_at`
- `meal_plans.user_id, meal_plans.created_at`
- `user_fitness_profiles.user_id`
- `exercise_recommendations.user_id, exercise_recommendations.created_at`
- `exercise_feedback.user_id, exercise_feedback.recommendation_id`
- `recommendations.user_id, recommendations.created_at`
- `agent_sessions.user_id, agent_sessions.updated_at`
- `agent_runs.session_id, agent_runs.status`
- `agent_tool_calls.run_id, agent_tool_calls.tool_name`
- `knowledge_chunks.embedding` 使用 HNSW 或 IVFFlat 向量索引

## 6. API 设计

后端使用 FastAPI，统一前缀为 `/api/v1`。接口包括 REST、SSE 和 WebSocket。

### 6.1 健康检查

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/health` | 服务健康检查 |
| GET | `/ready` | 依赖就绪检查 |

### 6.2 认证与权限

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录，返回 Access Token 和 Refresh Token |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| POST | `/api/v1/auth/logout` | 注销 Refresh Token |
| GET | `/api/v1/auth/me` | 获取当前用户 |

### 6.3 用户画像与目标

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/profile/me` | 获取当前用户健康画像 |
| PUT | `/api/v1/profile/me` | 创建或更新健康画像 |
| GET | `/api/v1/goals` | 获取健康目标列表 |
| POST | `/api/v1/goals` | 创建健康目标 |
| PUT | `/api/v1/goals/{goal_id}` | 更新健康目标 |
| PATCH | `/api/v1/goals/{goal_id}/status` | 暂停、完成或恢复目标 |

### 6.4 饮食记录

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/meals` | 按日期范围获取餐食 |
| POST | `/api/v1/meals` | 新增餐食 |
| GET | `/api/v1/meals/{meal_id}` | 获取单个餐食 |
| PUT | `/api/v1/meals/{meal_id}` | 更新餐食 |
| DELETE | `/api/v1/meals/{meal_id}` | 删除餐食 |
| POST | `/api/v1/meals/from-image` | 上传饮食图片并生成待确认记录 |

### 6.5 营养分析与风险

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/analysis/daily` | 生成每日营养分析 |
| GET | `/api/v1/analysis/daily` | 查询每日分析 |
| GET | `/api/v1/analysis/summary` | 查询区间分析汇总 |
| GET | `/api/v1/risks` | 获取风险列表 |
| POST | `/api/v1/risks/evaluate` | 重新评估指定日期风险 |
| PATCH | `/api/v1/risks/{risk_id}/status` | 更新风险状态 |

### 6.6 Agent 会话

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/agent/sessions` | 获取 Agent 会话列表 |
| POST | `/api/v1/agent/sessions` | 创建 Agent 会话 |
| GET | `/api/v1/agent/sessions/{session_id}` | 获取会话详情 |
| GET | `/api/v1/agent/sessions/{session_id}/messages` | 获取消息历史 |
| POST | `/api/v1/agent/sessions/{session_id}/messages` | 发送消息并触发 Agent |
| GET | `/api/v1/agent/runs/{run_id}` | 获取 Agent 运行状态 |
| GET | `/api/v1/agent/runs/{run_id}/tool-calls` | 获取工具调用记录 |
| GET | `/api/v1/agent/stream/{run_id}` | SSE 流式返回 Agent 输出 |
| WS | `/api/v1/agent/ws/{session_id}` | WebSocket 双向 Agent 会话 |

### 6.7 餐单、推荐与报告

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/meal-plans/generate` | 生成餐单 |
| GET | `/api/v1/meal-plans` | 获取餐单历史 |
| GET | `/api/v1/fitness-profile/me` | 获取当前用户运动画像 |
| PUT | `/api/v1/fitness-profile/me` | 创建或更新运动画像 |
| POST | `/api/v1/exercise-recommendations/generate` | 根据饮食分析生成运动推荐 |
| GET | `/api/v1/exercise-recommendations` | 获取运动推荐历史 |
| POST | `/api/v1/exercise-recommendations/{recommendation_id}/feedback` | 提交运动执行反馈 |
| GET | `/api/v1/recommendations` | 获取建议列表 |
| POST | `/api/v1/recommendations/generate` | 生成个性化建议 |
| GET | `/api/v1/reports` | 获取报告列表 |
| POST | `/api/v1/reports/generate` | 生成周报/月报 |
| GET | `/api/v1/trends` | 获取趋势数据 |

### 6.8 知识库与文件

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/files` | 上传文件到 S3/MinIO |
| GET | `/api/v1/files` | 获取文件列表 |
| POST | `/api/v1/knowledge/documents` | 创建知识文档 |
| POST | `/api/v1/knowledge/documents/{document_id}/embed` | 文档分块并入向量库 |
| GET | `/api/v1/knowledge/search` | pgvector 相似度检索 |

## 7. 文件目录

采用前后端分离的单仓库结构，支持 Docker Compose 本地编排。

```text
.
├── PLAN.md
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── AGENT_ARCHITECTURE.md
│   ├── DATABASE.md
│   └── SUMMARY.md
├── infra/
│   ├── nginx/
│   ├── prometheus/
│   ├── grafana/
│   └── otel/
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── stores/
│   │   └── test/
│   └── __tests__/
└── backend/
    ├── pyproject.toml
    ├── Dockerfile
    ├── alembic.ini
    ├── app/
    │   ├── main.py
    │   ├── core/
    │   ├── db/
    │   ├── models/
    │   ├── schemas/
    │   ├── api/
    │   ├── services/
    │   ├── agents/
    │   │   ├── graph.py
    │   │   ├── state.py
    │   │   ├── nodes/
    │   │   └── tools/
    │   ├── tasks/
    │   └── tests/
    └── alembic/
        ├── env.py
        └── versions/
```

## 8. 开发阶段拆分

每次只完成一个阶段。每个阶段结束后都运行 lint、typecheck、test、build，并修复失败项。若阶段需要新增依赖，必须先说明并安装依赖，然后再验收。

### 阶段 0：规划文档

目标：

- 创建并维护 `PLAN.md`。
- 明确需求分析、页面结构、数据库设计、API 设计、文件目录、开发阶段和风险点。

验收标准：

- `PLAN.md` 覆盖 Agentic AI 新架构。
- 不写应用代码。

### 阶段 1：项目规则与工程骨架

目标：

- 创建 `AGENTS.md`。
- 初始化 Next.js + TypeScript + Ant Design + ECharts 前端骨架。
- 初始化 FastAPI 后端骨架。
- 建立基础 lint、typecheck、test、build 命令。
- 添加 `.env.example` 和基础 README 占位。

验收标准：

- 前后端目录存在且职责清晰。
- 前端基础页面可构建。
- 后端 `/health` 可访问。
- 前后端基础测试通过。

### 阶段 2：认证、配置与基础设施

目标：

- 实现配置管理。
- 实现 OAuth2 + JWT 认证。
- 接入 PostgreSQL、Redis、S3/MinIO 配置。
- 添加 Docker Compose：frontend、backend、postgres、redis、minio。
- 添加 Alembic 基础迁移。

验收标准：

- 用户可注册、登录、刷新 Token。
- Docker Compose 可启动基础依赖。
- 数据库迁移可运行。
- 认证接口测试通过。

### 阶段 3：核心业务数据模型与 API

目标：

- 实现用户画像、健康目标、饮食记录、食物条目模型。
- 实现画像、目标、餐食 CRUD API。
- 实现基础权限隔离。

验收标准：

- 登录用户只能访问自己的数据。
- 可创建画像、目标和餐食记录。
- 数据模型测试和 API 测试通过。

### 阶段 4：营养分析与风险识别

目标：

- 实现营养计算服务。
- 实现每日/周/月分析服务。
- 实现风险识别规则。
- 实现分析和风险 API。

验收标准：

- 可根据饮食记录生成评分和营养分析。
- 可识别高糖、蛋白质不足、纤维不足、夜宵频繁、早餐缺失等风险。
- 核心算法有单元测试覆盖。

### 阶段 5：LangGraph Agent 工作流

目标：

- 实现 Agent State。
- 实现规划 Agent、画像 Agent、营养分析 Agent、风险识别 Agent、餐单推荐 Agent、运动干预推荐 Agent、干预追踪 Agent 的节点。
- 实现工具调用层。
- 持久化 Agent 会话、运行状态和工具调用记录。

验收标准：

- 输入“我想减脂”可触发完整 Agent 流程。
- Agent 能读取画像和近 7 天饮食数据。
- Agent 能生成分析、风险、餐单建议和运动干预建议。
- Agent 运行状态和工具调用记录可查询。

### 阶段 6：RAG 知识库与 pgvector

目标：

- 启用 pgvector。
- 实现知识文档、分块、Embedding 入库。
- 实现相似度检索工具。
- 将 RAG 工具接入 Agent。

验收标准：

- 可导入营养知识文档。
- Agent 回答可引用检索到的知识上下文。
- 向量检索 API 有测试覆盖。

### 阶段 7：异步任务、报告与干预追踪

目标：

- 接入 Celery + Redis。
- 实现周报/月报生成任务。
- 实现干预任务调度。
- 支持报告文件导出到 S3/MinIO。

验收标准：

- 可异步生成周报/月报。
- 可记录干预任务并跟踪状态。
- 报告 API 和任务测试通过。

### 阶段 8：前端应用页面与数据看板

目标：

- 实现登录、看板、目标、画像、运动画像、饮食记录、分析、风险、运动干预、趋势页面。
- 使用 Ant Design 组织后台工作台。
- 使用 ECharts 展示趋势、占比和风险变化。

验收标准：

- 用户可完成从登录到记录饮食再查看分析的主流程。
- 图表在无数据、少量数据、演示数据下均可正常显示。
- 页面在桌面和移动端可用。

### 阶段 9：Agent 对话、流式输出与餐单推荐页面

目标：

- 实现 Agent 对话页。
- 使用 SSE 展示流式输出。
- 展示工具调用过程。
- 实现智能餐单和推荐结果页面。
- 实现饮食驱动的运动推荐结果展示。

验收标准：

- 用户输入目标后可以看到 Agent 分析过程。
- 页面能展示工具调用、分析结果、风险、餐单和运动干预建议。
- 推荐结果具体、可执行。

### 阶段 10：运维、监控、CI/CD 与最终文档

目标：

- 添加 Nginx 配置。
- 添加 GitHub Actions。
- 添加 OpenTelemetry、Prometheus、Grafana 基础配置。
- 补齐 README、`.env.example`、部署文档、API 文档、Agent 架构文档、数据库文档、项目总结。

验收标准：

- CI 能运行 lint、typecheck、test、build。
- Docker Compose 可完成本地一键启动。
- 文档覆盖本地开发、部署、环境变量、API、Agent 工作流和项目总结。

## 9. 每阶段通用验收命令

### 前端

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

### 后端

```bash
python -m ruff check .
python -m mypy app
python -m pytest
python -m compileall app
```

### Docker 与基础设施

```bash
docker compose config
docker compose up -d
docker compose ps
```

实际命令以 `AGENTS.md` 和 `README.md` 中最终脚本为准。

## 10. 风险点

### 10.1 依赖和本地环境

风险：Next.js、FastAPI、LangGraph、Celery、pgvector 等依赖较多，本地如果缺少 Node、npm、Docker、PostgreSQL 或 Redis，会影响构建和运行。

应对：提供 Docker Compose，统一依赖；阶段验收中明确记录无法运行的原因和修复方式。

### 10.2 Agent 输出可靠性

风险：LLM 可能生成不准确或过度自信的营养建议。

应对：将关键营养计算、风险识别和阈值判断放在确定性工具中；LLM 负责解释和组织建议；输出中保留证据数据。

### 10.3 医疗健康边界

风险：用户可能将系统建议当作医学诊断。

应对：在页面和文档中明确系统是健康管理辅助工具，不替代医生或注册营养师。涉及疾病、严重不适、特殊医学饮食时建议咨询专业人士。

### 10.4 RAG 知识质量

风险：知识库来源不可靠会影响推荐质量。

应对：知识文档记录来源、版本和分类；管理员可管理知识；检索结果进入 Agent 上下文前做过滤。

### 10.5 长周期任务复杂度

风险：周报、月报、干预任务和 Agent 状态持久化会增加系统复杂度。

应对：先实现可运行闭环，再逐步增强任务调度、重试和观测能力。

### 10.6 成本与限流

风险：OpenAI API、Embedding、Agent 工具调用会带来费用和速率限制。

应对：增加缓存、请求限流、任务队列、模型配置和无 Key 降级方案。没有 API Key 时使用规则引擎和模板输出保证演示可运行。

### 10.7 数据隐私

风险：健康数据、饮食记录和对话内容属于敏感个人数据。

应对：使用 JWT 鉴权、用户数据隔离、最小化日志、敏感字段脱敏、上传文件权限控制。

### 10.8 部署复杂度

风险：Docker、Nginx、CI/CD、监控组件过多，容易超出项目初期范围。

应对：分阶段交付。先保证应用功能闭环，再补充生产级部署和监控。
