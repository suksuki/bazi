# Test Case Matrix

更新时间：`2026-04-08`

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
| integration | stream-board controller regression | `frontend/src/features/stream-board/__tests__/useStreamBoardController.test.tsx` |
| integration | stream-board view wiring | `frontend/src/features/stream-board/__tests__/StreamBoardView.test.tsx` |
| unit | admin-settings utils | `frontend/src/features/admin-settings/utils.test.ts` |
| integration | admin-settings controller hydrate + save | `frontend/src/features/admin-settings/__tests__/useAdminSettingsController.test.tsx` |
| unit | decision-inbox helpers | `frontend/src/features/decision-inbox/utils.test.ts` |
| unit | bazi-card helpers | `frontend/src/features/bazi-card/utils.test.ts` |
| unit | ten-god-list helpers | `frontend/src/features/ten-god-list/utils.test.ts` |
| unit | auditor-briefing helpers | `frontend/src/features/auditor-briefing/utils.test.ts` |

### 前端回归关注点

- `StreamBoard` 提交生辰后仍能生成卡片、审计和 verdict 链路
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
