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
