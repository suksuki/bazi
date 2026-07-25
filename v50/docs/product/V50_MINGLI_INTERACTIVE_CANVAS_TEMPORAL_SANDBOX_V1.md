# V50 Mingli Interactive Canvas · Temporal Sandbox v1

Status: frozen design baseline; C0 CLOSED / PASS; C1 not started  
Date: 2026-07-18  
Slice: second vertical experience slice after `看见命局`

## 0. One-Line Definition

> Canvas 不是第二个 Reasoner，而是正式认知与实验状态的可视化执行层。

本切片正式命名为：

```text
操作命局 · Temporal Sandbox
```

它让用户观察原局在加入大运、流年后的结构变化，并通过 Abu 理解：

```text
新增了什么？
改变了什么？
哪条主路径因此受到影响？
```

本切片不新增命理结论，不修改 LifeCase，不以动画效果替代专业认知。

## 1. Product Position

DeepBazi 的前两个纵向体验切片共同构成核心闭环：

```text
看见命局
系统把已经提交的命局认知呈现给人

操作命局
人通过安全操作理解结构如何随时间变化

Abu
在人与当前命理认知之间完成解释
```

Canvas 可在未来被课堂、研究、Live、剧场和视频消费，但本轮不实现这些消费端。

## 2. Cognitive Authority

```text
Chart World Instance
+ Temporal Snapshot
+ committed LifeCase
        ↓
Mingli Canvas Compiler
        ↓
MingliCanvasSpec
        ↓
Renderer
```

用户操作后的唯一合法链路为：

```text
CanvasAction
    ↓
Sandbox Mutation
    ↓
重新编译
    ↓
新的 MingliCanvasSpec
    ↓
CanvasDiffSpec
    ↓
动画、差异摘要与 Abu 解释
```

前端不得从原始命盘自行判断合冲刑害、十神、路径、做功或时序影响。Renderer 只渲染 Spec；它不补关系、不拼路径、不提升结论确定性。

## 3. Five Provenance States

Canvas 中每个可见对象、关系、路径和变化都必须具有显式来源：

| Source mode | Meaning | Formal authority |
| --- | --- | --- |
| `canonical` | 命盘、历法、柱位和确定性结构事实 | immutable chart authority |
| `committed` | LifeCase 已正式提交的认知、主路径或条件 | formal case cognition |
| `derived` | Compiler 从正式状态确定性推导出的展示结果 | reproducible projection |
| `hypothetical` | 用户在沙盒中选择的时间或实验变量 | sandbox only |
| `presentation` | 排列、缩放、聚焦和图层等纯视觉变化 | no Mingli meaning |

假设状态必须保留完整来源：

```yaml
source_mode: hypothetical
base_snapshot_id: snapshot-xxx
mutation:
  temporal.year: 癸卯
```

Abu、字幕和差异摘要必须继承该来源。任何 `hypothetical` 内容都不得被表达成命主真实经历或正式案例结论。

## 4. Semantic Change Vocabulary

v1 禁止使用未经真实校准的连续强度分数，例如 `82 → 46`。结构变化使用离散语义：

```text
introduced
removed
activated
reinforced
weakened
blocked
reopened
unchanged
```

每个变化必须携带可追溯原因：

```yaml
change_type: blocked
target_ref: path_food_controls_kill
because:
  - relation_ref: relation-gui-controls-ding
    statement: 癸水克丁火
  - dependency_ref: path-dependency-ding
    statement: 丁火是该路径的必要节点
```

上述状态表达的是关系或路径语义变化，不代表吉凶、事件概率或人生结果强度。

## 5. Core Contract: MingliCanvasSpec

```yaml
MingliCanvasSpec:
  schema_version: deepbazi.mingli_canvas_spec.v1

  identity:
    canvas_spec_id:
    chart_version_id:
    temporal_snapshot_id:
    life_case_id:
    sandbox_session_id:
    compiled_at:
    compiler_version:
    content_hash:

  semantic_slots:
    - slot_id:
      slot_type: natal_year | natal_month | natal_day | natal_hour | luck | year
      semantic_position:
      visual_position:
      immutable:
      source_mode:

  nodes:
  relations:
  clusters:
  paths:

  epistemology:
    epistemic_status:
    source_refs:
    commitment_refs:
    uncertainty:
    rejection_or_block_reasons:

  interaction:
    allowed_interactions:
    immutable_slots:
    sandbox_mutations:

  presentation:
    visual_anchors:
    layers:
    emphasis:
    narration_targets:
```

### Contract rules

1. `semantic_position` 永远表示真实柱位；拖拽只可改变 `visual_position`。
2. 原局四柱为 immutable；大运、流年是本切片允许切换的时间变量。
3. `visual_anchors`、颜色、坐标和动画提示不进入命理语义对象。
4. candidate、committed、blocked 和 hypothetical 必须保留不同的认识论状态。
5. 无来源对象、无依据关系、无法追溯路径不能进入合法 Spec。

## 6. Core Contract: CanvasDiffSpec

差异由 Compiler 正式输出，前端不得临时比较两份 JSON 后自行解释。

```yaml
CanvasDiffSpec:
  schema_version: deepbazi.canvas_diff_spec.v1
  diff_id:
  from_spec_id:
  to_spec_id:
  source_action_ref:

  added_nodes:
  removed_nodes:
  added_relations:
  removed_relations:
  changed_relations:

  introduced_paths:
  activated_paths:
  blocked_paths:
  reopened_paths:
  reinforced_paths:
  weakened_paths:
  unchanged_paths:

  changed_epistemic_status:
  explanation_refs:
  uncertainty:
  content_hash:
```

同一份 Diff 同时服务：

```text
状态过渡动画
页面差异摘要
Abu Context Pack
教学步骤（未来）
视频脚本（未来）
确定性回归测试
```

## 7. Sandbox Contract

现有 `MingliSandboxState` 是可复用基础，但 Temporal Sandbox v1 需要补齐来源和时间变更合同：

```yaml
TemporalSandboxState:
  sandbox_session_id:
  base_canvas_spec_id:
  base_snapshot_id:
  base_life_case_id:
  revision:
  selected_luck:
  selected_year:
  mutations:
  current_canvas_spec_id:
  current_diff_spec_id:
  status: active | modified | restored | discarded | saved_as_exploration
  writes_chart: false
  writes_life_case: false
```

允许保存的只是探索记录，不是正式认知：

```text
Sandbox
→ TopicExploration / private exploration history
→ optional future Reasoner review
→ Reliability Gate
→ explicit LifeCase revision only
```

不存在从 Canvas 直接写回 LifeCase 的按钮或隐式路径。

## 8. First Product Experience

### Default rhythm

```text
原局
→ 加入大运
→ 加入流年
```

每一步只显示：

```text
新增了什么
改变了什么
主路径受到什么影响
```

### Default layout

```text
顶部 / 中央：六柱结构
主区域：当前选中关系层
侧栏 / 移动端抽屉：差异摘要
底部 / 抽屉：LifeCase 主路径
左下 Abu：解释当前对象、当前阶段和当前假设边界
第二视图：专业 Graph
```

首屏不默认展示完整 Graph，避免普通用户面对关系蜘蛛网。

### Relation layers in v1

至少支持四类可独立开关的关系层：

```text
生克泄制
合与结构组合
冲刑害破
做功路径
```

具体关系是否存在、处于何种状态由 Compiler 提供；图层开关只改变呈现。

## 9. Abu Grounding Contract

点击柱、干支、关系或路径时，Abu 只获得当前 `CanvasContextPack`：

```yaml
CanvasContextPack:
  canvas_spec_id:
  diff_spec_id:
  selected_object_refs:
  current_stage: natal | luck | year
  source_modes:
  committed_claim_refs:
  hypothetical_mutations:
  explanation_refs:
  uncertainty:
  must_not_say:
```

Abu 可以：

- 解释当前对象是什么；
- 解释从上一状态到当前状态发生了什么；
- 指出主路径为何被激活、削弱或阻断；
- 说明哪些内容只是沙盒假设；
- 引导用户切换关系层或下一阶段。

Abu 不可以：

- 根据画面自由补出新关系；
- 把时间假设说成真实经历；
- 把结构变化直接翻译成确定事件；
- 修改命盘、LifeCase 或专业判断；
- 以通用话术填补当前 Spec 没有的信息。

## 10. Role Disclosure

同一 Spec 使用不同披露深度，不运行四套 Canvas：

| Role | Default disclosure |
| --- | --- |
| Guest | 不开放 Temporal Sandbox；只可见受控演示或摘要 |
| Member | 六柱、关键关系、主路径和自然语言差异 |
| Practitioner | 完整关系、候选路径、证据、反证和假设比较 |
| Research | 来源、版本、Diff、异常、开放问题和可复现实验 |
| Teacher/Admin | 可使用批准命例编排教学场景；不得改写正式案例 |

Admin 的角色切换用于测试披露边界，不改变底层认知。

## 11. Technical Direction

### v1 choice

```text
framework-agnostic TypeScript contracts
+ existing read-only Experience API
+ SVG renderer
+ CSS / Web Animations state transitions
```

原因：六柱、关系线、路径、锚点、无障碍标注和高清缩放都适合 SVG；第一刀需要先证明语义正确与交互清楚。

### Deferred candidates

```text
React Flow
用于未来复杂专业 Graph 和可定制节点

Cytoscape.js
只在真实复杂网络与自动布局需求被验证后考虑

GSAP
只在课堂时间线编排进入已授权切片后考虑

Rive / Gemini actor assets
属于 Abu 表演层，不属于 Canvas 语义计算
```

本轮不得同时引入 React Flow、Cytoscape、Framer Motion 和 GSAP。

## 12. Acceptance Criteria

### Data safety

- 原局四柱不能被 Sandbox 修改；
- `ChartVersion`、`TemporalSnapshot`、`LifeCase` 没有写操作；
- 每个实验状态有独立 `sandbox_session_id`；
- 刷新或退出时明确保留为探索记录或丢弃；
- 不存在自动 promotion。

### Cognitive correctness

- 每个节点、关系、路径和 Diff 均有来源与认识论状态；
- candidate、committed、blocked、hypothetical 的视觉语言不同；
- Abu 的每个解释可追溯到当前 Spec / Diff / Context Pack；
- 实验结果始终显示“假设状态”；
- 不使用虚假连续强度分数。

### Interaction value

- 可选择一个大运和一个流年；
- 可逐阶段播放，也可手动切换；
- 至少四类关系图层；
- 可查看 introduced、removed、activated、blocked 等变化；
- LifeCase 主路径可定位到画布对象；
- 点击柱、干支、关系和路径均有针对性解释；
- 桌面和移动端语义一致。

### Architecture boundary

- 前端不存在命理判定逻辑；
- Compiler 是 Spec 和 Diff 的唯一生产者；
- Spec 可脱离 Renderer 使用 fixtures 验证；
- 同一输入的 Spec 与 Diff 可复现且哈希稳定；
- 不为本切片重构现有 Experience Shell；
- Canvas 不成为新 Engine、新 Brain 或新 Formal Store。

## 13. Authorized Implementation Slices

### Slice C0 — Contract fixtures

只建立：

```text
MingliCanvasSpec v1
CanvasDiffSpec v1
CanvasAction v1
TemporalSandboxState v1
CanvasContextPack v1
一个批准命例的原局 / 大运 / 流年 fixtures
Compiler determinism tests
```

不做页面。

Implementation result (2026-07-18):

```text
MingliCanvasSpec v1                    implemented
CanvasDiffSpec v1                     implemented
CanvasAction v1                       implemented
TemporalSandboxState v1               implemented
CanvasContextPack v1                  implemented
approved temporal fixture             implemented
all-eight-diff-semantics fixture      implemented
determinism / provenance / isolation  passed
role disclosure audit                 passed
full regression                       320 passed
```

Audit:

```text
reports/mingli-canvas-c0/MASTER_AUDIT_REPORT.md
reports/mingli-canvas-c0/mingli_canvas_c0_audit_v1.json
```

C0 只证明无 Renderer 条件下的合同闭环。它不证明六柱画布、专业时序语义或真人交互体验已经成立。

### C0 closure lock

```yaml
phase: C0 Contract Fixtures
status: CLOSED
gate: PASS
implementation_complete: true
production_ui_change: false
deployment_required: false

verification:
  c0_tests: 7 passed
  targeted_regression: 14 passed
  full_regression: 320 passed

protected_boundaries:
  runtime_modified: false
  reasoner_modified: false
  life_case_modified: false
  ui_modified: false
  mingli_algorithm_modified: false
  llm_used: false
  sandbox_writes_formal_state: false
```

Permanent disclosure invariant:

> 一旦对象因角色披露策略被过滤，任何 fallback、补全、默认选择或上下文组装，都不得使其重新进入 Spec、Diff 或 CanvasContextPack。

后续问题只允许按以下归属处理：

```text
合同缺陷
→ 先新增或修订 C0 fixture，证明缺陷后才能修改合同

展示问题
→ 只在 C1 Renderer 内解决，不反向增加命理语义捷径
```

C0 不再接受顺手优化或范围扩展。

### Slice C1 — Read-only six-pillar canvas

只建立：

```text
固定原局四柱
选择一个大运和流年
四类关系图层
原局 / 大运 / 流年切换
主路径定位
桌面与移动 SVG renderer
```

C1 是关闭 C0 后唯一获准的下一阶段。它只验证经过角色过滤的 Spec 能否被忠实、安全、清晰地呈现；不得提前实现完整 Temporal Sandbox。

### Slice C2 — Formal diff and Abu explanation

只建立：

```text
CanvasDiffSpec rendering
逐阶段播放
差异摘要
对象点击
CanvasContextPack
Abu grounded explanation
```

只有 C0、C1、C2 通过后，才讨论课堂编辑器、多人 Live、录制与视频导出。

## 14. Explicitly Out Of Scope

```text
新增命理算法
LLM 自由看图
Canvas 内部推断合冲或路径
数值化能量仪表盘
修改原局四柱
自动写回 LifeCase
课堂脚本编辑器
多人 Live
录制与视频导出
短视频模板
复杂 Graph 自动布局
完整 Xiangfa 场景
```

## 15. Final Product Rule

> 第一刀不以漂亮动画验收，而以安全、可追溯、可复现的命盘状态变化验收。

任何视觉效果只要让假设看起来像事实、让候选看起来像结论、或让结构动画脱离正式认知，即视为失败。
