# Frontend MVC Guide

更新时间：`2026-04-12`（掐指 `calculationCount` 三段式补充）

## 1. 目标

前端 MVC 在本仓库中的含义不是传统 class-based MVC，而是更适合 React/Next 的职责拆分：

- `page` 充当路由装配层
- `controller hook` 充当控制器
- `view/component` 充当展示层
- `utils/constants/types` 充当轻量 model/support 层

## 2. 推荐模式

```text
src/features/<feature>/
├── use<Feature>Controller.ts
├── <Feature>View.tsx
├── utils.ts
├── constants.ts
├── types.ts
└── __tests__/
```

## 3. 现有示例

### Stream Board

- 入口：[frontend/src/components/StreamBoard.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/components/StreamBoard.tsx:1)
- Controller（Facade）：[frontend/src/features/stream-board/useStreamBoardController.ts](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/stream-board/useStreamBoardController.ts:1)
- 编排子模块：`controller/useStreamBoardPipeline.ts`（副作用管线：`activeView`、插件重算定时器、语言切换等；入参为强类型 `StreamBoardPipelineParams`，由 Facade 注入 setter/ref）
- View：[frontend/src/features/stream-board/StreamBoardView.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/stream-board/StreamBoardView.tsx:1)
- 展示用纯映射：`viewModel.ts`（便于单测与 View 瘦身）
- **指令舱「掐指一算」与 Decision Inbox（2026-04）**
  - View：`StreamBoardView.tsx` 中 `handleFullCalculate`：`isCalculating` 与主栏 `actionMode` 对齐；请求返回后 **至少 800ms** 的强制 Loading 窗口；`Promise.race` 超时与 `SeedSubmitResult`（`useSeedAnalysis`）错误态在 **`UnifiedActionBar` 的 `errorFootnote`** 展示；成功路径用 **`successFootnote`** 区分「计算完成，已更新逻辑视图」与「物理逻辑收敛稳态」文案（依据 `utils/physicsTensorFingerprint.ts` 对 `physics_tensor` 的前后指纹）。
  - **掐指三段式 `calculationCount`（0/1/2）**：0 主文案「掐指一算」→ 首次成功后 1「掐指再算」→ 第二次测算且 tensor 指纹不变则 2「下次再算」并 **主栏整组 `disabled`**（`UnifiedActionBar` 的 `mainActionConverged` 灰底）；终局脚注「✨ 逻辑已收敛，推演已至终局…」。生辰 / 插件权重 / 实验室 `labConfig` / 参考年 / Inbox 勾选任一相对上次成功快照变化则 **`lastSuccessfulInputBundle` 失配**，`calculationCount` 复位为 0。
  - 每次全量测算结束在 `finally` 中 **`calculationNonce` 自增**，驱动 `BoardCommandPanel` 内 `DecisionInbox` / `UnifiedActionBar` 的 `key` 重振，避免 UI 与快照脱节。
  - **`decision_journal`**：`mergeSnapshot` 对 `decision_journal` 为整段替换；`BoardCommandPanel` 勾选时仅 **追加** `suppress_inbox` 条目，**不因换勾选而按 removedIds 回删**，避免「选 B 后 A 复活」；显式撤销仍走 `revokeConfirmedDecision` 等路径。
  - 静默重算：`hooks/useStreamBoardSilentRecalculateLayout.ts` 失败时经 `appendSilentAnalyzeLogRef` 写入 `result_logs`（`[SILENT_ANALYZE]` 前缀）。

### Admin Settings

- 入口：[frontend/src/app/admin/settings/page.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/app/admin/settings/page.tsx:1)
- Controller：[frontend/src/features/admin-settings/useAdminSettingsController.ts](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/admin-settings/useAdminSettingsController.ts:1)
- View：[frontend/src/features/admin-settings/AdminSettingsView.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/admin-settings/AdminSettingsView.tsx:1)

## 4. 何时拆分

满足以下任一条件就应该考虑拆：

- 文件超过约 `180` 行
- 同时包含网络请求、状态管理、布局渲染
- 有 3 个以上 `useEffect`
- 有明显的“纯计算”代码段可以单测
- UI 与业务判断互相交织难以阅读

## 5. 测试建议

- `controller`：集成测试，mock `fetch/localStorage/timers`
- `view`：交互测试，检查 callback wiring
- `utils`：纯单元测试

## 6. 当前前端测试分层

- `StreamBoardView`：view 级交互测试
- `useStreamBoardController`：controller 回归测试（analyze-seed 主链路）
- `useStreamBoardLabSnapshotEffects`：实验室 snapshot 灌回副作用
- `labSnapshotHydration` / `viewModel`：纯函数与映射单测
- `utils/physicsTensorFingerprint`：`physics_tensor` 稳定指纹（全量测算收敛判定）
- `useStreamBoardPipeline`：模块契约与 `activeView` 类型字面量单测
- `AuditSidebar`：组件级单测
- `admin-settings`：controller 集成测试
- `decision-inbox / bazi-card / ten-god-list / auditor-briefing`：helper 单测

## 7. Stream Board 控制器重构约定（2026-04）

- **`useStreamBoardController.ts` 仅作编排（Facade）**：禁止再向该文件堆叠新业务分支；新逻辑放入 `features/stream-board/hooks/useStreamBoard*.ts` 或 `controller/*` 纯函数。
- **子域 Hook（已实现）**：
  - `hooks/useStreamBoardVerdictState.ts`：终审正文、结构候选、版本与历史
  - `hooks/useStreamBoardPhysicsState.ts`：`physics_tensor` 在 UI 上的切片（十神分、审计、熵）
  - `hooks/useStreamBoardAuditUiState.ts`：流式判词、审计侧栏、诊断
  - `hooks/useStreamBoardLogicDrawerState.ts`：Arbiter 逻辑抽屉
  - `hooks/useStreamBoardLabSnapshotEffects.ts`：实验室 `snapshot` 灌回、导航恢复诊断、Inbox 重置（`useLayoutEffect` / `useEffect`）
- **数据流（简图）**：`LabStore.snapshot` → 子域 state 初始化 → `mergeSnapshot` / API 回写 → View；Hydration 与持久化仍由主编排 hook 内 `useEffect` 协调，子 hook 不直接访问 `localStorage`。
- **新增 UI 状态**：先判断属于哪一子域，再决定放进哪个 `useStreamBoard*State`，避免上帝对象回潮。
