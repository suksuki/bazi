# Test Case Matrix

更新时间：`2026-04-14`

## 最近一次自动化执行（2026-04-12）

### 执行命令

- 后端单元：`cd qiazhi_bazi/backend && python3 -m pytest tests/unit -q`
- 后端集成（快速子集）：`cd qiazhi_bazi/backend && python3 -m pytest tests/integration/test_api_flow.py -q`
- 前端：`cd qiazhi_bazi/frontend && npm run typecheck && npx vitest run`
- 全量 CI 参考：`cd qiazhi_bazi/frontend && npm run test:ci`（含 `lint`、`next build`）；后端全量 `pytest tests/unit tests/integration`（集成中含长耗时与物理断言用例，见下）。

### 结果汇总

- 后端单元：`188` 项通过（`tests/unit`，约 `3.5s`）。
- 后端集成：`tests/integration/test_api_flow.py` **`7` 项通过**（约 `2s`）。`test_causal_logic_cases` 等用例依赖完整物理/枢纽输出，当前环境中 **`test_case_01_tan_cai_huai_yin_pivot_and_work` 可能因 `target_pivot` 与期望不一致失败**（与前端 Stream Board UI 改动无关）；`test_full_stack_plugins` / `test_plugin_full_sovereignty` 耗时可至数分钟以上，适合夜间或 CI 全量跑。
- 前端：`tsc --noEmit` 通过；`vitest run`：**`16` 个测试文件、`70` 条用例**全部通过（含新增 `physicsTensorFingerprint` 单测）。

### 本轮说明

- Stream Board：**`utils/physicsTensorFingerprint`** 稳定指纹单测；`StreamBoardView.test.tsx` 注明与 controller/指纹单测的分工；架构说明见 `docs/architecture/FRONTEND_MVC.md`（掐指一算 Loading、`decision_journal` 追加语义、`SeedSubmitResult` 与脚注 UX）。
- 历史条目：2026-04-11 批次仍见下文「后端 / 前端」矩阵；矩阵中文件路径仍有效，用例行数以本节「结果汇总」为准。

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
| unit | causal router negotiate | `backend/tests/unit/test_causal_router.py` |
| unit | DNA registry / admission / routing audit append | `backend/tests/unit/test_dna_registry.py` |
| unit | blind skill_prompt sovereignty sort | `backend/tests/unit/test_skill_prompt_routing.py` |
| integration | admin runtime-config roundtrip | `backend/tests/integration/test_api_flow.py` |
| integration | analyze-clash without live llm | `backend/tests/integration/test_api_flow.py` |
| integration | decision step write / rollback write | `backend/tests/integration/test_api_flow.py` |
| integration | analyze-seed end-to-end | `backend/tests/integration/test_api_flow.py` |
| unit | v12.92 热补丁：m5-gold-stats 降级 + final-verdict 409 分流 | `backend/tests/unit/test_router_v129_hotfix.py` |

### 后端回归关注点

- `consultation -> decision_step -> rollback` 写链路不回归
- `analyze-seed` 返回 `metadata / timeline / physics_tensor / audit_summary`
- `audit` 保留 `strict_json / retry_json / fallback` 三条路径
- `final-verdict` 在有无 `consensus_history` 两种情况下都可工作
- `final-verdict` 命中 `PROBE_WAITING` 时返回 `409 FINAL_VERDICT_FLOW_STATE_CONFLICT`（非 422）
- `m5-gold-stats` 在 DB/Schema 不可用时返回降级 JSON（`degraded=true`），避免前端监控站 500 风暴

## 前端

| 层级 | 用例 | 文件 |
|---|---|---|
| unit | stream-board utils | `frontend/src/features/stream-board/__tests__/utils.test.ts` |
| unit | stream-board physics_tensor 指纹（收敛判定） | `frontend/src/features/stream-board/utils/__tests__/physicsTensorFingerprint.test.ts` |
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
- `DecisionInbox` 卡片选择和 verdict 文本高亮不回归；`decision_journal` 追加抑制与全量测算脚注行为见 `FRONTEND_MVC.md`
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
