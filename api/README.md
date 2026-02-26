# FDS 2.0 API — 全量流形追踪

## 启动生产服务（端口暴露给前端）

在项目根目录执行：

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0`：对外暴露端口，前端/其他主机可访问。
- 默认端口 `8000`，可按需改为 `--port 8080` 等。

## 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v2/manifold/trace/{user_id}` | 流形追踪：60 格局 D_M 概率云，返回前 top_k 叠加态。可选查询参数 `dynamic_5d`（JSON）、`top_k`（默认 3）。 |

## 健康检查

- `GET /docs` — Swagger 文档
- `GET /openapi.json` — OpenAPI 规范
