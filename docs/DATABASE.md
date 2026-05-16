# 数据库文档

当前数据库以 PostgreSQL 为生产目标，本地开发脚本可使用 SQLite 轻量运行。阶段 7 已落地认证、用户画像、运动画像、健康目标、饮食记录、营养分析、风险预警、Agent 工作流持久化表、RAG 知识库表，以及报告与干预任务表。

## 已实现表

### `users`

用户基础信息与登录身份。

关键字段：`id`、`name`、`email`、`password_hash`、`role`、`created_at`、`updated_at`。

### `refresh_tokens`

Refresh Token 哈希与撤销状态。

关键字段：`id`、`user_id`、`token_hash`、`expires_at`、`revoked_at`、`created_at`。

### `health_profiles`

用户健康画像。

关键字段：`user_id`、`age`、`gender`、`height_cm`、`weight_kg`、`sleep_hours`、`bedtime`、`wake_time`、`activity_level`、`exercise_frequency`、`dietary_preferences`、`allergies`、`budget_level`。

### `user_fitness_profiles`

用户运动画像，为运动干预 Agent 预留。

关键字段：`user_id`、`exercise_level`、`weekly_frequency`、`preferred_exercise`、`available_time_minutes`、`fitness_goal`、`contraindications`、`is_sedentary`。

### `health_goals`

用户健康目标。

关键字段：`user_id`、`goal_type`、`target_weight_kg`、`target_calories`、`target_protein_g`、`start_date`、`end_date`、`status`。

### `meals`

饮食餐次记录。

关键字段：`user_id`、`meal_date`、`meal_time`、`meal_type`、`location`、`source`、`note`。

### `food_items`

餐次下的食物条目与营养数据。

关键字段：`meal_id`、`name`、`amount`、`unit`、`calories`、`protein_g`、`fat_g`、`carbs_g`、`fiber_g`、`sugar_g`、`sodium_mg`、`confidence`。

### `nutrition_analyses`

每日营养分析结果。

关键字段：`user_id`、`goal_id`、`analysis_date`、`period_type`、`score`、`totals`、`macro_balance`、`evidence`、`summary`、`created_at`。

其中 `totals`、`macro_balance`、`evidence` 使用 JSON 存储，方便保留 AI/规则分析过程中的结构化证据。

### `risk_alerts`

饮食风险预警记录。

关键字段：`user_id`、`analysis_id`、`risk_type`、`severity`、`title`、`description`、`evidence`、`suggestion`、`status`、`created_at`、`resolved_at`。

### `agent_sessions`

Agent 会话记录。

关键字段：`user_id`、`title`、`goal_snapshot`、`status`、`created_at`、`updated_at`。

### `agent_messages`

Agent 会话消息。

关键字段：`session_id`、`role`、`content`、`metadata`、`created_at`。

### `agent_runs`

Agent 工作流运行记录。

关键字段：`session_id`、`graph_name`、`state`、`status`、`started_at`、`finished_at`。

### `agent_tool_calls`

Agent 工具调用轨迹。

关键字段：`run_id`、`tool_name`、`input`、`output`、`status`、`latency_ms`、`created_at`。

### `knowledge_documents`

RAG 知识文档原文。

关键字段：`title`、`source`、`category`、`content`、`metadata`、`created_at`、`updated_at`。

### `knowledge_chunks`

知识文档分块与 Embedding。

关键字段：`document_id`、`chunk_index`、`chunk_text`、`token_count`、`embedding`、`metadata`、`created_at`。

生产 PostgreSQL 迁移会执行 `CREATE EXTENSION IF NOT EXISTS vector`，并为 `knowledge_chunks.embedding` 创建 HNSW 向量索引。SQLite 本地测试使用同一 SQLAlchemy 模型降级运行。

### `reports`

周报/月报生成结果。

关键字段：`user_id`、`report_type`、`period_start`、`period_end`、`status`、`summary`、`metrics`、`recommendations`、`export_format`、`export_object_key`、`export_content`、`task_id`、`generated_at`。

其中 `metrics` 保存平均评分、平均热量、平均蛋白质、风险数量和高频风险类型；`recommendations` 保存报告级干预建议；`export_object_key` 采用 S3/MinIO 兼容对象路径。

### `intervention_tasks`

周期报告生成的干预任务。

关键字段：`user_id`、`report_id`、`risk_type`、`title`、`description`、`task_type`、`priority`、`status`、`scheduled_for`、`due_date`、`source`、`evidence`、`completed_at`。

## 已实现迁移

| 迁移文件 | 内容 |
| --- | --- |
| `202605150001_create_auth_tables.py` | `users`、`refresh_tokens` |
| `202605150002_create_core_business_tables.py` | 画像、目标、餐次、食物条目 |
| `202605150003_create_analysis_risk_tables.py` | 营养分析、风险预警 |
| `202605160001_create_agent_tables.py` | Agent 会话、消息、运行、工具调用 |
| `202605160002_create_knowledge_tables.py` | RAG 知识文档、知识分块、pgvector 向量字段 |
| `202605160003_create_reporting_tables.py` | 周报/月报、干预任务追踪 |

运行迁移：

```bash
cd backend
alembic upgrade head
```

## 后续规划表

- `meal_plans`
- `exercise_recommendations`
- `exercise_feedback`
- `uploaded_files`
