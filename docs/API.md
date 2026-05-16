# API 文档

当前已完成阶段 10：认证、健康画像、运动画像、健康目标、饮食记录、每日营养分析、饮食风险识别、LangGraph Agent 工作流 API、Agent SSE 流式输出、RAG 知识库检索 API、周期报告与干预任务 API，以及 Prometheus 指标接口。

统一前缀：

```text
/api/v1
```

## 基础接口

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/health` | 服务健康检查 |
| GET | `/ready` | 服务就绪检查 |
| GET | `/metrics` | Prometheus 文本指标 |
| GET | `/api/v1/agent/capabilities` | Agent 能力与工具说明 |

`GET /metrics` 当前暴露：

- `nutrition_agent_app_info`
- `nutrition_agent_http_requests_total`
- `nutrition_agent_http_request_duration_seconds_sum`
- `nutrition_agent_http_request_duration_seconds_count`

## 认证接口

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 注册并返回 Access Token 与 Refresh Token |
| POST | `/api/v1/auth/login` | 登录并返回 Token |
| POST | `/api/v1/auth/refresh` | 刷新 Access Token |
| POST | `/api/v1/auth/logout` | 注销 Refresh Token |
| GET | `/api/v1/auth/me` | 获取当前用户 |

## 用户画像与目标

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/profile/me` | 获取当前用户健康画像 |
| PUT | `/api/v1/profile/me` | 创建或更新健康画像 |
| GET | `/api/v1/fitness-profile/me` | 获取当前用户运动画像 |
| PUT | `/api/v1/fitness-profile/me` | 创建或更新运动画像 |
| GET | `/api/v1/goals` | 获取健康目标列表 |
| POST | `/api/v1/goals` | 创建健康目标 |
| PUT | `/api/v1/goals/{goal_id}` | 更新健康目标 |
| PATCH | `/api/v1/goals/{goal_id}/status` | 更新目标状态 |

## 饮食记录

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/meals` | 按日期范围获取饮食记录 |
| POST | `/api/v1/meals` | 创建饮食记录与食物条目 |
| GET | `/api/v1/meals/{meal_id}` | 获取单条饮食记录 |
| PUT | `/api/v1/meals/{meal_id}` | 更新饮食记录，支持替换食物条目 |
| DELETE | `/api/v1/meals/{meal_id}` | 删除饮食记录 |

## 营养分析

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/analysis/daily` | 根据指定日期饮食记录生成每日营养分析 |
| GET | `/api/v1/analysis/daily` | 查询每日营养分析，可传 `start_date`、`end_date` |
| GET | `/api/v1/analysis/summary` | 查询区间分析汇总，包括数量、平均评分、平均热量 |

`POST /api/v1/analysis/daily` 请求示例：

```json
{
  "analysis_date": "2026-05-15"
}
```

返回包含：

- `score`：饮食评分。
- `totals`：热量、蛋白质、脂肪、碳水、膳食纤维、糖、钠摄入汇总。
- `macro_balance`：蛋白质、碳水、脂肪供能占比。
- `evidence`：目标热量、目标蛋白质、餐次数量、风险数量等证据。
- `summary`：面向用户的中文结论。

## 风险预警

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/risks` | 获取风险列表，可传 `risk_status`、`start_date`、`end_date` |
| POST | `/api/v1/risks/evaluate` | 重新评估指定日期风险 |
| PATCH | `/api/v1/risks/{risk_id}/status` | 更新风险状态，如 `resolved` |

当前规则层可识别：

- 热量超标或摄入过低。
- 蛋白质摄入不足。
- 膳食纤维偏低。
- 糖摄入偏高。
- 钠摄入偏高。
- 脂肪供能占比偏高。
- 早餐缺失。
- 夜宵记录。
- 晚餐过晚。

## Agent 工作流

阶段 5 已实现 LangGraph Agent 工作流，当前采用确定性规则工具作为本地可运行兜底。

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/agent/capabilities` | 查看 Agent 节点与工具能力 |
| POST | `/api/v1/agent/chat` | 创建会话并触发完整 Agent 分析 |
| POST | `/api/v1/agent/chat/stream` | 创建会话并通过 SSE 返回 Agent 进度、工具调用、答案片段和最终结果 |
| GET | `/api/v1/agent/sessions` | 获取当前用户 Agent 会话 |
| POST | `/api/v1/agent/sessions` | 创建 Agent 会话 |
| GET | `/api/v1/agent/sessions/{session_id}` | 获取会话详情 |
| GET | `/api/v1/agent/sessions/{session_id}/messages` | 获取会话消息 |
| POST | `/api/v1/agent/sessions/{session_id}/messages` | 发送消息并触发 Agent 运行 |
| GET | `/api/v1/agent/runs/{run_id}` | 获取 Agent 运行状态和最终 state |
| GET | `/api/v1/agent/runs/{run_id}/tool-calls` | 获取工具调用轨迹 |

当前工作流节点：

```text
planner -> profile -> nutrition -> risk -> knowledge -> meal_plan -> exercise -> intervention
```

Agent 会通过 `rag_search` 工具读取知识库上下文；如果知识库为空，则继续使用规则引擎完成本地演示。

`POST /api/v1/agent/chat/stream` 请求体与 `/agent/chat` 一致：

```json
{
  "message": "今天中午吃了炸鸡汉堡，晚上又喝了奶茶，我想减脂应该怎么调整？",
  "analysis_date": "2026-05-15"
}
```

SSE 事件类型：

| event | 说明 |
| --- | --- |
| `session` | 返回创建的会话与运行 ID |
| `node` | 返回当前完成的 LangGraph 节点、中文标签与关键预览数据 |
| `tool_call` | 返回工具名称、输入、输出、状态和耗时 |
| `answer_delta` | 返回最终建议文本片段，用于前端逐段展示 |
| `final` | 返回与 `/agent/chat` 相同结构的最终 `AgentRunResult` |
| `error` | 返回流式执行异常说明 |

## RAG 知识库

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/knowledge/documents` | 获取知识文档列表，可传 `category` |
| POST | `/api/v1/knowledge/documents` | 导入知识文档 |
| GET | `/api/v1/knowledge/documents/{document_id}` | 获取文档与分块 |
| POST | `/api/v1/knowledge/documents/{document_id}/embed` | 将文档分块并生成 Embedding |
| GET | `/api/v1/knowledge/search` | 相似度检索，可传 `q`、`top_k`、`category` |

导入文档请求示例：

```json
{
  "title": "奶茶与添加糖干预",
  "source": "local nutrition guide",
  "category": "risk_rule",
  "content": "含糖饮品会快速提高添加糖摄入，减脂阶段建议优先选择无糖茶或白水。",
  "metadata": {
    "version": "2026-05"
  }
}
```

无 OpenAI API Key 时，系统使用确定性哈希向量作为本地降级 Embedding；有 Key 时预留 OpenAI Embeddings 调用入口。

## 报告与干预追踪

| 方法 | 路由 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/reports` | 获取当前用户报告列表，可传 `report_type`、`report_status` |
| POST | `/api/v1/reports/generate` | 生成周报/月报，默认同步生成，可传 `run_async=true` 进入 Celery 队列 |
| GET | `/api/v1/reports/{report_id}` | 获取报告详情、指标、建议与导出内容 |
| GET | `/api/v1/interventions` | 获取干预任务列表，可传 `task_status`、`start_date`、`end_date` |
| POST | `/api/v1/interventions/schedule` | 从指定报告或最近已完成报告生成干预任务 |
| PATCH | `/api/v1/interventions/{task_id}/status` | 更新干预任务状态 |

报告生成请求示例：

```json
{
  "report_type": "weekly",
  "period_start": "2026-05-10",
  "period_end": "2026-05-16",
  "run_async": false,
  "export_format": "markdown"
}
```

报告会汇总周期内评分、热量、蛋白质、风险类型与开放风险，并生成 Markdown 导出内容。当前本地模式将导出内容保存在数据库字段中，同时生成 S3/MinIO 兼容的 `export_object_key`，后续可接入真实对象存储上传。

## 后续规划接口

| 模块 | 计划接口 |
| --- | --- |
| 智能餐单 | 餐单生成、餐单历史、食物替换 |
| 运动干预 | 饮食驱动运动推荐、执行反馈 |
| 文件导出 | 报告文件上传到 S3/MinIO、下载签名 URL |
