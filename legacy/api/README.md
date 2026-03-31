# FDS 老系统 API（仅 v2）

在项目根目录执行：

```bash
cd legacy && uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

或：

```bash
PYTHONPATH=legacy uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

## 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v2/manifold/trace/{user_id}` | 流形追踪 |

掐指八字（Qiazhi-Bazi）请使用 **独立进程**：`uvicorn qiazhi.api.app:app --port 8001`（见仓库根 `REPO_LAYOUT.md`）。
