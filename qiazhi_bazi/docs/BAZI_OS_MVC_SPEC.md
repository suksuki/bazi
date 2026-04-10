# Bazi OS MVC State Map

本文定义 0.13 实验室前端 MVC 状态协议，作为分析师与开发者共同基线。

## 1. Store 字段表 (`useLabStore`)


| 字段                           | 类型                               | 含义                                                |
| ---------------------------- | -------------------------------- | ------------------------------------------------- |
| `snapshot.ts`                | `number`                         | 快照更新时间戳                                           |
| `snapshot.active_session_id` | `string | null`                  | 当前活跃会话标识                                          |
| `snapshot.physics_tensor`    | `Record<string, unknown>`        | 物理层输出张量                                           |
| `snapshot.metadata`          | `Record<string, unknown>`        | 结构化命盘元信息                                          |
| `snapshot.timeline`          | `Record<string, unknown> | null` | 时间轴快照                                             |
| `snapshot.llm_prompt`        | `string`                         | 当前语义层提示词文本                                        |
| `snapshot.audit_summary`     | `unknown`                        | 审计摘要                                              |
| `snapshot.resolved_card_ids` | `string[]`                       | 已处理 decision 卡片 ID                                |
| `snapshot.interaction_hub`   | `object`                         | 三方交互摘要（health/audit/logs/cards）                   |
| `snapshot.final_verdict`     | `object`                         | 断言结果（正文/差分/证据/结构终审）                               |
| `snapshot.logic_diff`        | `object`                         | 基线对比差分（abs/entropy）                               |
| `snapshot.baseline_snapshot` | `object`                         | 基线锁定快照（physics_tensor + entropy + abs_loss_total） |
| `state.updates`              | `Array`                          | 最近 5 次 Store 更新记录（含 overload 标记）                  |


## 2. Controller 接口表（Action Contract）


| 接口                                       | 输入            | 输出              | 说明                                           |
| ---------------------------------------- | ------------- | --------------- | -------------------------------------------- |
| `onSeedSubmit(payload)`                  | `SeedPayload` | `Promise<void>` | 发起排盘与首轮审计，更新 Store 主快照                       |
| `onExecuteDecision(selected)`            | `InboxCard[]` | `Promise<void>` | 推进物理执行与审计历史（含 decision-steps）                |
| `refreshVerdict(selected)`               | `InboxCard[]` | `Promise<void>` | 基于最新上下文刷新语义断言                                |
| `executeDecisionAndRefresh(selected)`    | `InboxCard[]` | `Promise<void>` | 原子链路：先执行再刷新断言                                |
| `rerunFinalVerdictWithWeights(selected)` | `InboxCard[]` | `Promise<void>` | 参数重算与断言更新                                    |
| `setAsBaseline()`                        | `-`           | `void`          | 基线锁定，写入 `baseline_snapshot` 并重置 `logic_diff` |
| `revokeConfirmedDecision(id)`            | `string`      | `Promise<void>` | 撤销确认决策并同步状态                                  |


## 3. View 订阅表（Selector）


| View                           | 订阅切片                                                                                          | 目的                            |
| ------------------------------ | --------------------------------------------------------------------------------------------- | ----------------------------- |
| `MainView` (`StreamBoardView`) | `metadata`, `timeline`, `final_verdict`, `logic_diff`, `resolved_card_ids`, `interaction_hub` | 展示主面板、Decision、Result Summary |
| `DebugView` (`/debug`)         | `physics_tensor`, `interaction_hub`, `final_verdict`, `state.updates`                         | 展示 Trace、三方交互、State Sentinel  |
| `AdminView` (`/admin`)         | `pluginWeights`（经 controller 写入）、`physics_tensor`（只读）                                         | 插件权重调参与运维观察                   |


## 4. 持久化与同步原则

1. Store 是唯一实时状态中心，页面组件不直接读写核心状态存储。
2. `sessionStorage` 仅作为 Store 的卸载备份介质（`beforeunload`）。
3. Controller 是唯一写入口，View 只读 + 触发 Action。
4. 禁止通过 `storage` 事件建立跨页实时总线。

