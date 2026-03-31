# Qiazhi-Bazi（掐指八字）新系统

**心智模型**：以本目录为产品中心；**默认不围绕老系统（legacy）叙事**，仅在必要时引用其算力与数据（见根目录 `QIAZHI_BAZI_MASTER_PLAN.md` §1.1）。

- **`main.py`**：Python 入口，仅启动 FastAPI（不加载 legacy Streamlit）。
- **`qiazhi_core/`**：协议与墓库等插件；可按需桥接 `legacy` 内 `core/config`。
- **`api/`**：路由（由 `main.py` 调用 uvicorn 加载 `qiazhi.api.app:app`）。
- **`web/`**：Next.js + Tailwind（`/qiazhi`）。

启动：`python qiazhi/main.py` 或 `uvicorn qiazhi.api.app:app --port 8001`。详见 `web/README.md`。
