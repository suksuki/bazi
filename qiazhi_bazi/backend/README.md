# Qiazhi-Bazi Backend

后端采用 `FastAPI + SQLModel`，当前推荐结构是 `router -> service -> helper/model/skill`。

## 目录概览

```text
backend/
├── app/api/                 # 薄 controller、契约、endpoint helper
├── app/services/            # 业务编排 service
├── app/services/helpers/    # 纯拼装 / 纯归一化 helper
├── app/skills/              # 物理引擎与判词 skill
├── app/db/                  # session / models
└── tests/                   # unit + integration
```

## 依赖

使用仓库根目录 `requirements.txt`，至少包含：

- `fastapi`
- `uvicorn[standard]`
- `sqlmodel`
- `httpx`
- `pydantic`

## 环境变量

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 默认数据库连接串，当前架构禁止 SQLite 回退 |
| `QIAZHI_BAZI_DB_URL` | 兼容旧变量；未设置 `DATABASE_URL` 时才读取 |
| `QIAZHI_ALLOWED_DB_HOSTS` | 可选，逗号分隔数据库白名单，默认 `127.0.0.1,localhost` |
| `QIAZHI_CORS_ORIGINS` | 逗号分隔，默认 `http://localhost:3000` |
| `QIAZHI_BAZI_LLM_BASE_URL` | OpenAI 兼容 LLM 根地址 |
| `QIAZHI_BAZI_LLM_API_KEY` | 本地可填 `empty` |
| `QIAZHI_BAZI_LLM_MODEL` | 推理模型名 |
| `QIAZHI_ADMIN_TOKEN` | 可选，admin 路由访问令牌 |
| `QIAZHI_DNA_REGISTRY_PATH` | 可选，规则基因 JSON 路径（演化覆盖物理系数） |
| `QIAZHI_EVOLUTION_ADMISSION_PATH` / `QIAZHI_EVOLUTION_ADMIT` | 可选，演化结果是否准入覆盖 |

`runtime_config.json`（或由 Admin 写入的等价配置）中的 **`causal_routing`** 与 `app/core/routing/causal_router.py` 默认字典深度合并；单独 PATCH 某字段不会抹掉其余键。

## 管理端与演化相关 API（节选）

除 `runtime-config`、`db-status` 等外，典型还包括：

- `PUT /api/admin/runtime-config`：请求体可带 `causal_routing` 对象，与磁盘上 `llm` 等并存合并。
- 演化批跑、反馈等以 `app/api/admin.py` 与 `contracts` 为准；**`QIAZHI_ADMIN_TOKEN` 必须为非空字符串**，否则全部 `/api/admin/*` 返回 503（禁止未配置即放行）。

具体路径以 OpenAPI（`/docs`）或集成测试 `tests/integration/test_api_flow.py` 为准。

## 启动

```bash
cd qiazhi_bazi/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 测试

```bash
cd qiazhi_bazi/backend
pytest tests/unit tests/integration -q
```

## 架构文档

- [总体架构](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/OVERVIEW.md)
- [后端 service 设计](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/BACKEND_SERVICE_ARCH.md)
- [测试策略](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_STRATEGY.md)

健康检查：`GET http://127.0.0.1:8001/health`  
示例元数据：`GET http://127.0.0.1:8001/api/demo/metadata`
