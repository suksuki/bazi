# Abu Mingli Topic 01: Structural Ablation v1

Status: implemented and machine-validated vertical slice  
Date: 2026-07-18

## Product Question

```text
阿布说命 01｜谁是命局里不可替代的节点？
```

这不是一段带按钮的视频，也不是让用户改八字。参与者先判断哪一个节点最关键，再在隔离沙盒中暂时拿开一个节点，观察已批准结构快照里的关系和路径如何变化。

本专题只证明一件事：

> 用户可以亲手操作一个真实、可追溯、不会污染正式案例的命理结构实验。

它不证明现实人生含义已经由确定性算法得出，也不代表 Live、TTS、Rive 表演或完整命理 Lab 已经完成。

## Experience Rhythm

```text
看四柱与已批准路径
→ 猜一个关键节点
→ 冻结预测
→ 在沙盒中拿开同一节点
→ 比较 Baseline / Modified / Diff
→ Abu 解释确定性的结构变化
→ 明确现实含义仍需专业 Reasoner
→ 恢复原局
→ 保存 TopicExploration
→ 结束专题
```

页面在所有阶段持续显示三条边界：

```text
实验分支
原命盘没有改变
当前探索不会自动写入正式认知
```

## Authority Split

| Authority | Allowed | Forbidden |
| --- | --- | --- |
| `visual_only` | 聚焦、变暗、显示路径和节点 | 重算结构、形成命理结论 |
| `deterministic_structure` | 在快照副本中拿开一个节点，重算边和路径完整性 | 推导现实职业、财富、健康或事件含义 |
| `reasoning_required` | 由专业 Reasoner 解释结构变化可能对应的现实条件 | 由 Renderer、Sandbox 或 Abu 文案自行补断 |

Abu 只能转述 `SandboxResult` 已确定的差异，例如关系消失数、受影响路径数和仍保留路径数。涉及“现实中会怎样”的内容必须保留 `reasoning_required`。

## Contracts

### MingliMechanismSnapshot

从正式、已批准的案例认知中签发的只读结构快照：

```yaml
MingliMechanismSnapshot:
  case_id:
  chart_version:
  life_case_version:
  cognitive_record_id:
  pillars: [year, month, day, hour]
  nodes:
  edges:
  approved_paths:
  competing_paths:
  approved_key_nodes:
  unresolved_conditions:
  claim_refs:
  snapshot_hash:
```

快照必须具备四柱、至少一条边和至少一条已批准路径。节点、边和路径引用不闭合时拒绝进入实验，产品层不得猜测路径。

### MingliVisualSpec

Renderer 只消费结构化视觉规格：

```yaml
MingliVisualSpec:
  snapshot_hash:
  pillars:
  nodes:
  edges:
  paths:
  interaction_capabilities:
    - focus_node: visual_only
    - toggle_path: visual_only
    - ablate_node: deterministic_structure
    - interpret_real_world_meaning: reasoning_required
```

### MingliSandboxState

```yaml
MingliSandboxState:
  base_snapshot_hash:
  predicted_key_node_id:
  selected_nodes:
  ablation_operations:
  comparison_mode: baseline | baseline_modified
  status: active | modified | restored | saved
  writes_life_case: false
```

每个沙盒最多执行一次单节点消融。预测一旦进入消融阶段即被冻结；恢复后不能再次消融；保存后不能恢复或修改。

### SandboxResult

```yaml
SandboxResult:
  authority: deterministic_structure
  base_snapshot_hash:
  modified_snapshot_hash:
  deterministic_changes:
    removed_node_id:
    invalidated_edges:
    remaining_edges:
    affected_paths:
    unaffected_paths:
    invalidated_claim_refs:
  reasoning_required: true
  writes_life_case: false
```

### TopicExploration

保存内容包括参与者预测、拿开的节点、观察、开放问题、快照哈希、结果引用和能力轨迹。它是专题探索记录，不是正式认知修订：

```yaml
case_local_only: true
writes_life_case: false
restored_original: true
capability_trace:
  - visual_only
  - deterministic_structure
  - reasoning_required
```

## Runtime And API

专题由 `required_experience_capabilities` 声明体验能力，客户端不按 Topic ID 分叉 Renderer 或状态机。

```text
GET  /api/v50/theater/sessions/{session_id}/participant/experiment
POST /api/v50/theater/sessions/{session_id}/participant/experiment/predict
POST /api/v50/theater/sessions/{session_id}/participant/experiment/ablate
POST /api/v50/theater/sessions/{session_id}/participant/experiment/restore
POST /api/v50/theater/sessions/{session_id}/participant/experiment/save
```

`ProductMingliExperimentPort` 只读取正式案例与已批准认知，重建确定性 Graph 后严格匹配批准路径。出现缺失案例、未批准路径、歧义节点或引用不闭合时，专题诚实阻断。

## UI Contract

- 四柱固定按年、月、日、时排列；天干在上、地支在下、藏干可见。
- 已批准路径与竞争路径保持不同视觉状态。
- 预测、消融、恢复和保存各自只有一个动作拥有者。
- `Baseline`、`Modified` 和 `Diff` 不得混成一张不可追踪的动画。
- 手机宽度下四柱、路径和动作不产生横向滚动。
- WebSocket 心跳若没有新序列，不重建当前交互 DOM，避免按钮在点击前被替换。

## Failure Behavior

以下状态必须阻断而不是生成看似完整的结构：

```text
case reference missing
formal LifeCase boundary missing
birth input missing
approved path missing or ambiguous
snapshot hash mismatch
node not in snapshot / not selectable
second ablation attempt
restore before ablation
save before deterministic result
```

旧案例如果没有可追溯的已批准路径，不自动升级。需要由正式认知链补齐后，才可进入本专题。

## Validation Evidence

```text
targeted structural + theater tests: 18 passed
related cognition/state/account tests: 17 passed
full V50 regression: 298 passed
JavaScript syntax check: passed
Python compile check: passed
desktop browser journey: completed end to end
mobile 390x844 lobby: no horizontal overflow
LifeCase hash before/after save: unchanged
TopicExploration: persisted with writes_life_case=false and restored_original=true
```

浏览器 QA 使用的临时案例、账户、场次、Envelope 和 TopicExploration 已在验证后删除。

## Known Limits And Next Authorized Slice

本版没有把以下能力包装成已完成：

```text
Qwen TTS for Topic 01
Live multi-participant voting
Rive actor and interruption blending
professional real-world interpretation after SandboxResult
free-form multi-operation Lab
automatic LifeCase revision
```

下一刀若获授权，应优先接入“由专业 Reasoner 消费 SandboxResult 并给出条件性现实解释”，同时仍经过 Reliability Gate；不是继续扩大确定性沙盒的判断权。
