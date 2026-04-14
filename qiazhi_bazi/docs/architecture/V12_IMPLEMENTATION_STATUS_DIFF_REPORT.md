# V12 实施现状差异报告（阶段里程碑）

## 里程碑 1：Hub 联调成功

- 当前行为：
  - 终判主链路由 `FinalVerdictSkill.generate` 接入 `BrainHub`。
  - `BrainHub` 在一次调用内完成 `MetadataProjectorV12 -> PSVEngine -> SemanticAuditor`。
  - 终判响应新增 `brain_hub`（含 `psv`、`audit`、`retry_count`、`dissent_block`）。
- 与目标差异：
  - 流式终判路径暂不做多轮重试，仅保留一次生成后审计。
- 剩余风险：
  - 弱模型在流式场景仍可能出现一次性幻觉，需要后续做流式重试策略。

## 里程碑 2：语义监军与自动重试落地

- 当前行为：
  - `SemanticAuditor` 实现轴向碰撞矩阵，支持 `PASS/FLAG/REJECT`。
  - `AUTO_RETRY_PROMPT` 强制注入 `Evidence Refs`，`max_auto_retry=2`。
  - 超限返回 `LIG_RETRY_EXHAUSTED` 与 `DissentBlock`。
- 与目标差异：
  - 词典仍是启发式关键词，尚未接入更细粒度短语权重表。
- 剩余风险：
  - 口语化改写可能绕过关键词命中，需迭代词典覆盖。

## 里程碑 3：ActiveProbing 挂起机制接入中枢

- 当前行为：
  - `evaluate_active_probing` 优先评估 **婚姻/情感偏置缺失 × 日支子午冲**（`M3_ZI_WU_MARRIAGE_PALACE_PROBE`），再评估 `decision_inbox` 高压插件对撞。
  - `run_internal_loop` / `run_full_cycle` 输出 `active_probing` 与 `interrupt_request`。
  - `TriLayer ArbiterBias` 增加 `interrupt_request` 与 `interrupt_state` 映射承载。
  - `MetadataProjectorV12` 已将 `metadata.bias_ack_tokens` 或 `persistence_layer.bias_ack_tokens` 汇入 `ArbiterBias.bias_ack_tokens`（此前恒为空列表，E2E 演示中已修正）。
- 与目标差异：
  - Resume API 仅完成契约对象，未接真实持久化状态流转。
- 剩余风险：
  - 多会话并发下中断状态需要事务级一致性保障。

## E2E 集成演示（脚本）

- 脚本：`backend/scripts/demo_v12_pulse.py`（样本 1990-06-14 正官格 mock）。
- 覆盖：`HUB_IDLE` → `PROBE_OFFERED` → `BIAS_ACK_INGESTED` → `LOCAL_RECOMPUTE_REQUESTED` → `AUDIT_GATE` → `ASSERTION_TREE_MATERIALIZED`，并打印 PSV 清单与 AssertionTree 节点顺序（FACT 居前，SYNTHESIS 根节点置末）。

## 里程碑 4：AssertionTree 接管输出（旧八股文路径停用）

- 当前行为：
  - 新增 `assertion_tree` 引擎，生成 FACT/LAW/WILL/SYNTHESIS 节点。
  - 默认 `narrative_strategy=assertion_tree`，终判提示不再注入 `verdict_skeleton`。
  - `verdict_anchor_layer.assertion_tree` 与 HTTP 响应 `assertion_tree` 已输出。
- 与目标差异：
  - 旧骨架代码仍保留（按策略停用，符合“保留代码”约束）。
- 剩余风险：
  - 前端若仍强依赖 `verdict_skeleton` 展示，需要同步渲染迁移。

## 里程碑 5：前后端交互合拢（Final Polish）

- 当前行为：
  - `analyze_clash_flow` / `analyze_seed_flow` 已返回 `active_probing`、`interrupt_request`、`psv_manifest`、`brain_hub_preview`，将 V12 大脑链路前置到 Analyze 阶段。
  - 前端 Stream Board 已映射：
    - `interrupt_request` → 阻塞式「逻辑追问对话框」；
    - `brain_hub.audit` 为 `FLAG` 或存在 `dissent_block` → 展示 `[逻辑异议]` 警示块；
    - 新增「系统基调 (PSV)」面板（红绿灯化 axis/polarity/strength）。
  - `final_verdict` 快照已落 `brain_hub`、`assertion_tree`、`narrative_strategy`，支持前端跨刷新稳定复现逻辑异议。
  - 数据库路径类报错统一纳入 `V12_ERROR_PROTOCOL`（`DB_ENV_PATH_NOT_READY` / `DB_WRITE_PATH_FAILED` / `DB_ENV_PATH_UNREACHABLE`）。
- 与目标差异：
  - 逻辑追问对话框当前为前端阻塞确认态，尚未把确认动作写入独立 Resume API 事务流（仍沿用现有会话持久化链）。
- 剩余风险：
  - 前端若长期停留在未确认追问态，需在后续版本补充「超时/重试/回退」策略与审计上报。
