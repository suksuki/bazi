# 仓库目录结构（双系统）

| 目录 | 说明 |
|------|------|
| **`legacy/`** | **老系统（Antigravity / FDS）**：`core/`、`config/`、`ui/`、`controllers/`、`registry/`、`docs/`、`scripts/`、`tests/`、`data_local/`、`api/`（v2）、Streamlit **`legacy/main.py`** 等。 |
| **`qiazhi/`** | **Qiazhi-Bazi（产品中心）**：`main.py`、`qiazhi_core/`、`api/`、`web/`。规划见 **`QIAZHI_BAZI_MASTER_PLAN.md`**（默认以新系统为叙事中心，legacy 仅按需引用）。 |
| **仓库根** | monorepo 元数据：`README.md`、`requirements.txt`、`.cursorrules`、`pytest.ini`、`data`（外部数据 symlink）等。配置目录仅为 **`legacy/config/`**（根目录不设 `config`）。 |
| **`.cursor/skills/`** | **Cursor Agent Skills**（随仓库共享）：规范与路线图见 **`.cursor/skills/README.md`**、**`ROADMAP.md`**。 |

若 Qiazhi 需调用 legacy 内 `core`（如 Bridge），运行环境需将 **`legacy/` 加入 `PYTHONPATH`**（`qiazhi.api.app` 已自动插入）；**非**日常开发默认前提。

## 启动

- **老系统 Streamlit**：`streamlit run legacy/main.py`
- **老 API**：`cd legacy && uvicorn api.app:app --reload --port 8000`
- **新系统 Qiazhi（Python 入口）**：`python qiazhi/main.py`（等价于 uvicorn 8001）
- **新系统前端**：`cd qiazhi/web && npm run dev`
