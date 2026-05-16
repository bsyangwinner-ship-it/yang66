# 部署文档

本项目支持两种交付路径：

- 本地完整 Docker Compose：适合演示、联调和面试作品展示。
- 云端拆分部署：前端 Vercel，后端 Render，数据库/Redis/S3 使用托管服务。

## 本地 Docker Compose

复制环境变量：

```bash
copy .env.example .env
```

启动完整环境：

```bash
docker compose up --build
```

服务端口：

| 服务 | 地址 |
| --- | --- |
| Nginx Gateway | `http://localhost:8080` |
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| Backend Docs | `http://localhost:8000/docs` |
| Metrics | `http://localhost:8000/metrics` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3001` |
| OTel Collector gRPC | `localhost:4317` |
| OTel Collector HTTP | `localhost:4318` |

默认 Grafana 账号来自 `.env`：

```text
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

后端容器启动时会自动执行：

```bash
alembic upgrade head
```

因此首次启动会自动创建认证、业务、Agent、知识库、报告和干预追踪表。

## 本地脚本开发

如果只做本地开发，不想启动完整 Docker：

```bash
scripts\dev-backend.cmd
scripts\dev-frontend.cmd
```

后端脚本默认使用 SQLite 并自动建表，适合快速调试 API 和前端页面。

## Nginx

配置文件：

```text
infra/nginx/nginx.conf
```

路由策略：

- `/` 转发到前端 `frontend:3000`。
- `/api/` 转发到后端 `backend:8000`。
- `/health`、`/ready`、`/metrics`、`/docs`、`/openapi.json` 转发到后端。
- `/api/` 下关闭代理缓冲，保证 Agent SSE 流式输出可用。

## 监控

后端提供无额外依赖的 Prometheus 文本指标：

```text
GET /metrics
```

当前指标：

- `nutrition_agent_app_info`
- `nutrition_agent_http_requests_total`
- `nutrition_agent_http_request_duration_seconds_sum`
- `nutrition_agent_http_request_duration_seconds_count`

Prometheus 配置：

```text
infra/prometheus/prometheus.yml
```

Grafana 预置：

```text
infra/grafana/provisioning
infra/grafana/dashboards/nutrition-agent.json
```

默认看板包含请求速率、平均延迟和应用状态。

## OpenTelemetry

OTel Collector 配置：

```text
infra/otel/collector-config.yml
```

后端支持可选 OpenTelemetry 自动接入：

```text
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=graduate-nutrition-agent-api
```

为了保证本地无网络、无额外包时仍可运行，OpenTelemetry Python 依赖采用可选加载：没有安装相关包时会自动跳过，不影响 API、测试和演示。

## CI/CD

GitHub Actions 配置：

```text
.github/workflows/ci.yml
```

CI 包含三个 Job：

- Backend：`ruff`、`mypy`、`pytest`、`compileall`。
- Frontend：`eslint`、`tsc`、`vitest`、`next build`。
- Docker Compose：`docker compose config --quiet`。

## Vercel + Render 部署建议

### 前端 Vercel

Root Directory：

```text
frontend
```

Build Command：

```bash
npm run build
```

环境变量：

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-backend-domain>
```

### 后端 Render

Root Directory：

```text
backend
```

Build Command：

```bash
pip install -e ".[dev]"
```

Start Command：

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

关键环境变量：

```text
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
JWT_SECRET_KEY=<strong-secret>
CORS_ORIGINS=["https://<vercel-domain>"]
OPENAI_API_KEY=<optional>
ENABLE_RULE_FALLBACK=true
```

### 数据服务

- PostgreSQL 需要启用 pgvector 扩展。
- Redis 用于 Celery、缓存和任务状态。
- S3 或 MinIO 用于报告导出和后续图片上传。

## 生产注意事项

- 不要使用默认 `JWT_SECRET_KEY`、MinIO 密码或 Grafana 密码。
- 健康建议必须保持“辅助参考，不替代医生或注册营养师”的边界。
- OpenAI API Key 不存在时，规则引擎和模板回复会保证演示可运行。
- 面向真实用户时，需要补充隐私政策、数据删除、用户授权和敏感健康数据合规说明。
