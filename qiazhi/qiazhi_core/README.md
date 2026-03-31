# Qiazhi-Bazi (`qiazhi_core`)

MVP 基础设施（本阶段）：

- **`main.py`**：FastAPI 入口（含 CORS 与启动时建表）。
- **`schemas/protocol.py`**：`BaziMetadata` 协议（`basic_info`、`energy_profile`、`clash_combinations`）。
- **`llm/client.py`**：本地 Qwen OpenAI 兼容客户端，支持异步流式。
- **`database/models.py` + `database/session.py`**：`Consultation` / `DecisionChain` / `KnowledgeBase`。
- **`bridge/legacy_adapter.py`**：按需读取 legacy 配置并做 payload -> metadata 映射。

运行入口：`python qiazhi/main.py`（或 `uvicorn qiazhi_core.main:app --port 8001`）。
