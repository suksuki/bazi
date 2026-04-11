# Test Case Matrix

更新时间：`2026-04-11`

## 最近一次自动化执行（2026-04-11）

### 执行命令

- 后端：`cd qiazhi_bazi/backend && python3 -m pytest tests/unit tests/integration -q`
- 前端（单元 + 集成风格 Vitest + 类型 + 静态检查 + 构建回归）：`cd qiazhi_bazi/frontend && npm run test:ci`

### 结果汇总

- 后端：`74` 项全部通过（`tests/unit` + `tests/integration`）
- 前端：`npm run test:ci` 全绿：`typecheck`、`lint`（见下述告警）、`vitest run`（`14` 个测试文件、`35` 条用例）、`next build`

### 本轮说明

- 前端新增 `npm run test:ci`（`typecheck` + `lint` + 全量 Vitest + `build`）与 `npm run test:stream-board`（Stream Board 子树）。
- 前端补齐 `.eslintrc.json` 与 `eslint` / `eslint-config-next`，`next lint` 可在非交互环境执行；当前仓库仍存在若干 `react-hooks/exhaustive-deps` 告警（不阻断 CI），后续可逐项收敛。
- 新增 `useStreamBoardPipeline` 契约单测，与 Stream Board 拆分文档对齐。

## 后端

| 层级 | 用例 | 文件 |
|---|---|---|
| unit | consultation create / structure confirm / rollback / history | `backend/tests/unit/test_consultation_service.py` |
| unit | db status / db init / llm test fallback | `backend/tests/unit/test_admin_service.py` |
| unit | translate / analyze-seed / final-verdict service | `backend/tests/unit/test_analysis_service.py` |
| unit | audit strict json / retry json / fallback | `backend/tests/unit/test_audit_service.py` |
| unit | llm chat / stream event formatting | `backend/tests/unit/test_llm_service.py` |
| unit | api helper / admin helper | `backend/tests/unit/test_api_helpers.py` |
| unit | physics rules | `backend/tests/unit/test_physics_rules.py` |
| unit | physics calculations | `backend/tests/unit/test_physics_calculations.py` |
| unit | runtime config | `backend/tests/unit/test_runtime_config.py` |
| integration | admin runtime-config roundtrip | `backend/tests/integration/test_api_flow.py` |
| integration | analyze-clash without live llm | `backend/tests/integration/test_api_flow.py` |
| integration | decision step write / rollback write | `backend/tests/integration/test_api_flow.py` |
| integration | analyze-seed end-to-end | `backend/tests/integration/test_api_flow.py` |

### 后端回归关注点

- `consultation -> decision_step -> rollback` 写链路不回归
- `analyze-seed` 返回 `metadata / timeline / physics_tensor / audit_summary`
- `audit` 保留 `strict_json / retry_json / fallback` 三条路径
- `final-verdict` 在有无 `consensus_history` 两种情况下都可工作

## 前端

| 层级 | 用例 | 文件 |
|---|---|---|
| unit | stream-board utils | `frontend/src/features/stream-board/__tests__/utils.test.ts` |
| unit | stream-board viewModel 映射 | `frontend/src/features/stream-board/__tests__/viewModel.test.ts` |
| unit | stream-board lab snapshot 纯函数灌回 | `frontend/src/features/stream-board/controller/__tests__/labSnapshotHydration.test.ts` |
| unit | stream-board pipeline 模块契约 | `frontend/src/features/stream-board/controller/__tests__/useStreamBoardPipeline.test.ts` |
| integration | stream-board lab snapshot 副作用 | `frontend/src/features/stream-board/hooks/__tests__/useStreamBoardLabSnapshotEffects.test.tsx` |
| integration | stream-board controller regression | `frontend/src/features/stream-board/__tests__/useStreamBoardController.test.tsx` |
| integration | stream-board view wiring | `frontend/src/features/stream-board/__tests__/StreamBoardView.test.tsx` |
| unit | AuditSidebar | `frontend/src/components/__tests__/AuditSidebar.test.tsx` |
| unit | admin-settings utils | `frontend/src/features/admin-settings/utils.test.ts` |
| integration | admin-settings controller hydrate + save | `frontend/src/features/admin-settings/__tests__/useAdminSettingsController.test.tsx` |
| unit | decision-inbox helpers | `frontend/src/features/decision-inbox/utils.test.ts` |
| unit | bazi-card helpers | `frontend/src/features/bazi-card/utils.test.ts` |
| unit | ten-god-list helpers | `frontend/src/features/ten-god-list/utils.test.ts` |
| unit | auditor-briefing helpers | `frontend/src/features/auditor-briefing/utils.test.ts` |

### 前端回归关注点

- `StreamBoard` 提交生辰后仍能生成卡片、审计和 verdict 链路；`activeView` 与 `ShellActiveView` 一致（不得用空字符串冒充 tab）
- `next build` 通过（类型与 App Router 导入错误在构建期暴露）
- `admin-settings` 仍能恢复本地配置、拉取模型、测试并保存 runtime config
- `DecisionInbox` 卡片选择和 verdict 文本高亮不回归
- `BaziCard` 根气、时间线和 branch energy 可视化逻辑不回归
- `TenGodNumericList` 锁定态和 anomaly badge 不回归
- `AuditorBriefing` 自动转决策项/已对齐/已加入状态不回归

## 建议后续补充

### 前端

- `AuditSidebar` helper / interaction tests
- `SeedInput` validation tests
- `TenGodNumericList` UI click-through tests
- `BaziCard` component-level interaction tests
- `DecisionInbox` component-level selection persistence tests

### 后端

- `analysis_helpers` 细粒度单测
- `audit_helpers` 细粒度单测
- 真实 DB regression harness
- `llm_service` route-level integration coverage
