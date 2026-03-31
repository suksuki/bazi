# Skills 路线图（增量补充）

> 以下为规划占位：**未实现的行**表示「将来可新增 Skill」；实现后把状态改为 ✅ 并在 `README.md` 索引表中添加条目。

## Phase A — 已有（legacy / FDS）

| 状态 | Skill 目录（拟） | 说明 |
|------|------------------|------|
| ✅ | `fds-sop-classical-engine` | 古典格局与 registry |
| ✅ | `fds-sop-llm-verdict` | 全息判词与 Ollama |

## Phase B — Qiazhi-Bazi（建议后续逐步增加）

| 状态 | Skill 目录（拟） | 说明 |
|------|------------------|------|
| ⬜ | `qiazhi-bazi-metadata` | `BaziMetadata` 协议演进、与 Bridge 字段对齐、LLM 语义字段约定 |
| ⬜ | `qiazhi-reasoning-engine` | 推演状态机、教练模式打钩流、裁决链记录 |
| ⬜ | `qiazhi-storehouse-plugin` | 墓库 L2 插件与仲裁流程（与现有 `qiazhi_core` 实现同步） |
| ⬜ | `qiazhi-i18n` | 中/英/韩 文案键与 API 契约 |

## Phase C — 工程与运维（按需）

| 状态 | Skill 目录（拟） | 说明 |
|------|------------------|------|
| ⬜ | `repo-pytest-legacy` | `legacy/tests` 与 `pytest.ini` 路径约定 |
| ⬜ | `repo-monorepo-layout` | `legacy/` vs `qiazhi/` 边界与启动命令 |

---

**维护**：每新增一个 Skill 目录，请更新 **Phase 表状态** + **`README.md` 当前索引表**。
