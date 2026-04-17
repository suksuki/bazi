# Arbiter Handbook（V12）

## 1. 如何看脉冲图

- 青色点：`AssertionNode` 节点脉冲，表示断言树在该节点完成了结构化物化。
- 绿色点：LLM 轮次事件（润色/终判相关）。
- 橙色点：`Resume` 重启点，表示会话从某个中断节点重新起跳。
- 点击任意点会打开回放浮层：查看该点对应的能量快照、骨架快照及（若存在）反馈 payload。

## 2. 如何用橙色重启点修正推演

1. 在主界面触发中断（出现 InterruptOverlay）。
2. 选择动作（确认冲突/修正能量/忽略警告），并提交 Resume。
3. 打开 Debug 页，进入「模型交互记录（多轮）」中的脉冲图。
4. 找到橙色点，点击查看：
   - `interrupted_node_id`：本次从哪个节点恢复；
   - `resume_timestamp`：恢复时间；
   - `user_feedback_payload`：当时的裁决反馈。
5. 对照后续青色节点链（AssertionNode）是否按预期收敛。

## 3. REJECT 与错题本（Dissent Ledger）

- 当 SemanticAuditor 判定 `REJECT` 时，系统会将该条记录写入 `brain_dissent_ledger`。
- 该记录包含：
  - 原始 AI 文本；
  - PSV 基调快照；
  - reason_code（拒稿维度）。
- 这些数据用于后续 RLHF-C 参数校准。

## 4. 常见异常排查

- `V12_SCHEMA_VIOLATION_ERROR`：
  - 含义：终判返回缺失 `assertion_tree`，系统按协议阻断回退。
  - 处理：检查终判输出结构，确认 `assertion_tree.nodes` 非空。
  - API 返回包含 `pulse_id`，可在 Debug 里按脉冲追踪定位。

## 5. 推荐操作习惯

- 每次 Resume 后先看橙色点，再看后续青色节点是否形成闭环。
- 遇到连续 REJECT 时，优先看 `learning-insights` 给出的高频维度建议，而不是直接放宽审计阈值。
- 任何“看起来可用但没有 AssertionTree”的结果都应视为协议错误，不可用于签发。
