# M5 初始化报告：偏好镜像与「子午冲」裁决风格（V13.0）

> 基于 `ArbiterPreferenceLedger`（黄金样本索引）与 `BrainHtnSnapshot` 同化链路的**静态**说明；非在线训练权重报告。

## 1. 账本里有什么

- **`ArbiterPreferenceLedger`**（`app/db/learning_ledger.py`）：将 `BrainHtnSnapshot.assimilated=true` 的快照登记为 **`preference_tier=GOLD`**，字段含 `snapshot_id`、`session_id`、`version_id`、`training_weight`；**V13.02** 起增加 **`interaction_pattern_id`**（如 `conflict_pattern_signature`），为子午冲等偏好自适应预留主键列。
- **同步入口**：`sync_gold_training_set(session)` —— 把已同化脑快照批量标记为 GOLD，用于后续仲裁路由与审计对齐（与 `load_gold_arbiter_matching` 等决策枢纽配合）。

当前表结构**不存储**「用户对子午冲点了哪张卡」级别的细粒度偏好向量；黄金层标识的是**哪些 HTN 快照已被标记为可信赖训练样本**，而不是已拟合的神经网络权重。

## 2. 「裁决者风格报告」（摘要）

| 维度 | 状态 |
|------|------|
| 偏好向量 / 嵌入 | **未**：Ledger 仅做 GOLD 标记与索引，无 per-user style embedding |
| 子午冲专用策略 | **未**：无单独「子午冲」分类权重列；子午冲相关行为由 **Active Probing / 冲突矩阵 / Inbox match_score / 静默仲裁** 等业务规则驱动 |
| 可观测偏好信号 | **部分**：`resume_feedback_history`、`ResumePulseHistory`、`arbitration_audit_feed_v1` 可回放人类选择 |

**结论（风格）**：系统记录的是 **「哪些快照算黄金教材」**，而不是「已经学会你在子午冲上总选 A」。要回答「是否学会子午冲偏好」，在工程上应表述为：**尚未从 Ledger 单独推出子午冲偏好模型；若需，应在 M5 后续迭代写入显式特征（如 conflict_signature → chosen_plugin_id）并做离线聚合。**

## 3. 与「子午冲」相关的现有机制（非 Ledger）

- **情感轴追问**：`active_probing` 中 `M3_ZI_WU_MARRIAGE_PALACE_PROBE`（日支子午且缺婚姻偏置时）。
- **高压插件仲裁**：`M3_HIGH_TENSION_PENDING` + `v1294` 批量 LLM 静默路径。
- **Resume 流水**：`persistence_layer.resume_feedback_history` 用于二次收敛与审计（V13.01 起与 analyze-clash 二段跳衔接）。

## 4. 建议的下一步（演习用）

1. 在 `ResumePulseHistory.user_feedback_payload` 或 `resume_feedback_history[].feedback` 中**稳定写入** `conflict_signature` + `chosen_plugin_id`。  
2. 离线脚本聚合 GOLD 快照上的选择分布，再生成真正的「风格向量」或规则表。  
3. 将聚合结果挂到 `runtime_config.brain` 或专用表，供 `should_auto_resolve` / 仲裁 prompt 读取。

---

*文档版本：V13.0 发布配套 · 与代码路径 `app/db/learning_ledger.py`、`app/logic/brain/decision_hub.py` 对齐。*
