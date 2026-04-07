# Qiazhi-Bazi Backend

## 依赖

使用仓库根目录 `requirements.txt`（需含 `fastapi`、`uvicorn[standard]`、`sqlmodel`、`httpx`、`pydantic`）。

## 环境变量

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 默认读取该变量；建议本地 `postgresql://postgres:***@127.0.0.1:5432/qiazhi_bazi` |
| `QIAZHI_BAZI_DB_URL` | 兼容旧变量；未设置 `DATABASE_URL` 时才会读取 |
| `QIAZHI_ALLOWED_DB_HOSTS` | 可选，逗号分隔数据库白名单（默认仅 `127.0.0.1,localhost`） |
| `QIAZHI_CORS_ORIGINS` | 逗号分隔，默认 `http://localhost:3000` |
| `QIAZHI_BAZI_LLM_BASE_URL` | OpenAI 兼容根，如 `http://192.168.0.10:8000/v1` |
| `QIAZHI_BAZI_LLM_API_KEY` | 本地可填 `empty` |
| `QIAZHI_BAZI_LLM_MODEL` | 模型名，与推理服务一致 |

## 启动

```bash
cd qiazhi_bazi/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

健康检查：`GET http://127.0.0.1:8001/health`  
示例元数据：`GET http://127.0.0.1:8001/api/demo/metadata`
