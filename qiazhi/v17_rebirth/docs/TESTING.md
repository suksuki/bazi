# V17 Rebirth 自动化测试

## 概览

| 层级 | 技术 | 路径 / 命令 |
|------|------|----------------|
| 后端单元 / 契约 | pytest | `qiazhi/v17_rebirth/tests/` |
| 后端集成 | pytest + `TestClient` | `-m integration` |
| 回归契约 | pytest | `-m regression` |
| 前端单元 | Vitest | `qiazhi/v17_rebirth/frontend/tests/` |

仓库根 `pytest.ini` 已将 `qiazhi` 加入 `pythonpath`，包导入形式为 `from v17_rebirth...`。

## 一键脚本

```bash
bash qiazhi/v17_rebirth/scripts/run_automated_tests.sh
```

脚本顺序：V17 pytest（默认排除 `integration`）→ 集成标记用例 → 前端 `pnpm test:ci`（ESLint + `next build` + Vitest）。Next.js 16 起 CLI 不再提供 `next lint`，与本仓库 `package.json` 中 `eslint .` 一致。

脚本会在 Relation Origin Gate 之前执行插件参数审计门禁：`scripts/audit_plugin_params.py` 的 `declared_but_unused` 不能包含任何项；一旦发现未接线参数，会直接中止自动化流程并输出失败原因。

## 常用命令

```bash
# 仅 V17 后端（快速，不含 integration）
pytest qiazhi/v17_rebirth/tests -m "not integration" -q

# 含 FastAPI /health 集成
pytest qiazhi/v17_rebirth/tests -m integration -q

# 全量 V17 测试目录
pytest qiazhi/v17_rebirth/tests -q

# 前端
cd qiazhi/v17_rebirth/frontend && pnpm install && pnpm test
```

## 与遗留测试

根目录 `testpaths` 仍包含 `legacy/tests` 等；只跑 V17 时请显式传入路径 `qiazhi/v17_rebirth/tests`，避免拉全仓历史用例。

## 排障

- **ImportError: v17_rebirth**：在仓库根执行 pytest，或设置 `PYTHONPATH=qiazhi`。
- **集成测试失败**：确认未改 `app` 的 `/health` 契约；流式端点需要真实 LLM，默认不在 CI 中覆盖。
