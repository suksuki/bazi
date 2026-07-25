# V50 Relation Atlas and Path Provenance Current-State Audit v1

```yaml
audit_date: 2026-07-19
status: COMPLETE
scope: current implementation and authority chain
onecanvas_ui_expansion: false
relation_atlas_implementation: not_started
r2_assisted_path_drawing: blocked
production_claim_system_best_path: forbidden
```

## 0. Decision

六柱 OneCanvas 是命理关系世界最重要的直接操作投影，但不是关系权威本身。

当前系统的真实主链是：

```text
确定性 Chart Facts
        ↓
现有 MingliGraph v1（不完整关系图）
        ↓
实验性 Candidate Path Explorer
        ↓
LLM Mingli Reasoner 形成 work_path
        ↓
Reliability / Formal Insight Gate
        ↓
LifeCase committed baseline
        ↓
Canvas 将 work_path 引用的 graph_relation 逐段映射回图边
        ↓
OneCanvas 展示“正式主路径”
```

因此当前不能声称：

```text
Graph 已经遍历全部命理关系；
系统已经从完整候选中算出最佳做功路径；
正式主路径由确定性路径算法直接裁决。
```

当前可以准确声称：

> 正式主路径来自已通过门禁并写入 LifeCase 的认知记录；Canvas 只在每一段
> 都能唯一映射回确定性关系事实时展示它。Graph 排名候选仍是实验观察。

## 1. Current Authority Chain

### 1.1 Atomic chart facts

历法、四柱、藏干、十神和五行映射来自确定性引擎。LLM 不创建这些事实。

### 1.2 Relation graph

`packages/core/graph/builder.py` 从命盘材料构造节点与边。当前确定性实现包括：

- 四柱天干、地支与藏干节点；
- 同柱位置连接；
- 地支藏干关系；
- 可见节点之间的五行生、克、同类支持；
- 仅针对 `巳酉丑` 的三合结构原型。

这些边的 `boundary` 明确是 computational relation，不是命理裁决。

### 1.3 Candidate path exploration

`packages/core/graph/path_explorer.py` 遍历现有 Graph，最多三段，并按照
`path_score_policy_v2` 排序。结果合同明确是 experimental evidence，不是 verdict。

### 1.4 LLM work path

`WorkPathReasoning.origin` 可以记录：

```text
system_enumerated
retrieval_suggested
llm_composed
mixed
```

默认值是 `llm_composed`。当前 Prompt 明确允许 LLM 比较系统候选、检索候选，
也允许在每一步可映射回事实时组合工具未表达的路径。

所以当前正式主路径的认知来源通常是：

```text
LLM composition or comparison
+ typed evidence refs
+ reliability review
+ LifeCase commit
```

它不是 Path Explorer 的第一名直接晋升。

### 1.5 Canvas projection

`apps/product/canvas_projection.py::_committed_path`：

1. 读取 `record.cognition.work_path.evidence_refs`；
2. 只接受 `category == graph_relation` 的事实；
3. 每个事实必须唯一匹配当前 Graph 中的一条边；
4. 任何一段不能唯一匹配时，整条路径不展示；
5. 匹配成功后，以 LifeCase baseline insight 作为 commitment ref。

因此 OneCanvas 目前展示的是：

> **LifeCase 已提交认知在当前确定性关系图上的可视化重验结果。**

## 2. Critical Findings

### P0-1. Relation catalog is structurally incomplete

Graph Enum 声明了多类边，但 Builder 实际只生产其中少数。六合、六冲、刑、害、
破、五合、通根、透干、三会、完整三合等尚未形成统一运行时目录。

风险：UI 图层名称可能比底层实际覆盖更完整，给人“系统已遍历全部关系”的错觉。

### P0-2. Triple combination is sample-specific

`TRIPLE_COMBINATIONS` 目前只有：

```text
巳酉丑 → 金
```

这属于历史样本特化，不能作为通用 Relation Atlas。

### P0-3. Hyperrelation is flattened into pairwise edges

巳酉丑当前被拆成“成员 → 酉桥节点”的普通二元边。三合、三会、三刑应当是
多节点 `RelationClusterInstance / Hyperrelation`，不能以某一成员冒充结构中心。

### P0-4. Path eligibility is over-broad

现有 `VALID_PATH_EDGE_TYPES` 几乎把所有边都允许进入路径，包括：

```text
stores
position_link
clashes
harmonizes
forms_triple_combination
```

这些关系的路径作用完全不同。`position_link` 和 `stores` 是结构关系，不应直接
等同于能量传递；冲、合与三合只能在显式 Policy 下作为激活、牵制、转化或阻断。

在正式 `PathTransitionPolicy` 建立前，Graph 排名不得升级为正式路径推荐。

### P0-5. Path score is uncalibrated and contains chart-specific priors

当前分数包含固定权重、固定 edge strength，以及对 fire / earth / metal 的固定
season bias。它适合历史研究原型，不足以表示所有命盘上的通用“最优路径”。

对外不得显示或暗示这些分数是已校准概率、能量值或专业置信度。

### P0-6. Formal path continuity is not fully typed

Canvas 当前按 evidence ref 收集关系和节点，但合同只验证引用存在，没有验证：

- 每一段首尾严格连续；
- 关系顺序与 `source → transformations → target` 一致；
- 多条 graph relation 引用是否属于同一条闭合路径；
- 路径中的 cluster 作用是否满足成立条件。

因此“每段都有边”还不等于“整条路径闭合”。

### P1-1. Provenance is present but fragmented

当前系统分别保存了：

- Graph edge 的 material/evidence refs；
- WorkPath 的 `origin`；
- LifeCase 的 reasoner/model/context provenance；
- Canvas 的 source/commitment refs。

但 OneCanvas 的单条关系或路径还不能统一回答：

```text
谁最初提出？
哪一版规则计算？
是否经过 LLM？
由谁验证？
在哪个阶段成立？
属于哪个流派配置？
```

### P1-2. LLM context is truncated

Chart World 当前最多向 LLM 提供 28 条优先关系和 8 条候选路径。即使 Relation
Graph 未来完整，Reasoner 也不能被假定已经比较了全图。Context Compiler 必须按
问题和关系透镜选择最小充分子图，并保留“未进入本轮上下文”的审计记录。

### P1-3. Temporal relation semantics are incomplete

正式大运和流年节点可加入 Canvas，但“加入时间节点”与“该节点真实激活、增强、
阻断或重开某条关系”仍需 typed temporal effect。没有 typed effect 时只能显示时间
进入，不能补画作用路径。

## 3. Current Coverage Matrix

| Relation family | Runtime state | Current path eligibility | Required correction |
| --- | --- | --- | --- |
| 五行生 | deterministic, coarse | direct | 保留方向；补 provenance 与条件 |
| 五行克 | deterministic, coarse | direct | 保留方向；区分克、制、耗语义 |
| 同类支持 | deterministic | bidirectional | 明确 symmetry，不用单向假边 |
| 同柱位置 | deterministic | currently direct | 禁止作为普通做功传递边 |
| 藏干 | deterministic | currently direct | 改为 containment / reveal context |
| 通根 | enum only / incomplete | currently allowed | 先实现定义和 Fixture，再决定 Policy |
| 透干 | missing typed relation | unavailable | 建立 hidden-stem → stem reveal relation |
| 天干五合 | missing | unavailable | 建立多重关系与成立条件 |
| 六合 | missing | unavailable | 建立 bond / bind 语义 |
| 六冲 | enum only / builder missing | currently allowed in policy | 实现后仅 conditional activate/disrupt |
| 刑、害、破 | missing | unavailable | 分类型，不合并成一个冲突边 |
| 三合 | only 巳酉丑 prototype | currently direct | 改为 hyperrelation + condition state |
| 三会 / 三刑 | missing | unavailable | 建立 cluster contract |
| 大运 / 流年进入 | slot/node supported | not a complete path effect | typed temporal activation required |
| LifeCase 正式主路径 | committed projection | display only | 增加连续性和统一 provenance 审计 |
| 用户 PathDraft | presentation/hypothetical | never formal automatically | 由 path-eligible transitions 验证 |

## 4. Target Authority Model

```text
Mingli Relation Engine
  owns deterministic relation facts and relation instances

PathTransitionPolicy
  owns whether and how a relation may participate in a path

Candidate Path Generator
  owns exhaustive structural candidates inside an approved lens

Path Evaluator
  owns continuity, activation, support, blocking and closure vectors

LLM Mingli Reasoner
  may compare, interpret and propose a path using typed facts
  may not invent a relation
  may not silently promote its proposal to committed

Reliability Gate / Analyst
  owns formal commitment according to release mode

LifeCase
  owns the committed cognition and its complete provenance

OneCanvas / Matrix / Theater / Xiangfa
  render the same relation and path objects without recomputation
```

这保留 LLM 的整盘综合能力，同时取消它对原子关系和正式提交状态的越权。

## 5. Required Provenance Contract

每条关系和路径最终至少需要：

```yaml
origin_type: rule_engine | reasoner | analyst | migrated | user_draft | llm_proposal
origin_ref:
rule_version:
school_profile:
computed_at_stage: natal | luck | annual | luck_annual | sandbox
verified_by: compiler | reliability_gate | analyst | none
commitment_status: fact | candidate | committed | blocked | hypothetical
llm_involved: true | false
model_version:
source_refs: []
```

未知来源必须显式写 `unknown`，不得根据字段所在位置推断成算法结论。

## 6. Product Terminology

当前 OneCanvas 统一使用：

```text
正式主路径
用户路径草稿
Graph 候选路径
当前路径验证结果
```

R2 Gate 通过前禁止：

```text
系统最佳路径
系统推荐路径
当前最优路径
能量百分比
路径成功率
```

## 7. Next Gate

本次只完成来源审计与方向冻结。下一步仍遵循：

```text
R1 真人产品审阅 PASS
        ↓
R2 Preflight Relation Atlas contracts
        ↓
原子与复合关系 Fixture
        ↓
PathTransitionPolicy
        ↓
Relation Coverage / Health Audit
        ↓
真实 LifeCase 分析师审阅
        ↓
才允许辅助画路径
```

当前不得借此审计直接重写 Graph、扩展用户 UI 或部署生产。

## 8. Final Assessment

```yaml
canvas_runtime_relations_created_by_llm: false
formal_work_path_cognition_llm_involved: true
formal_path_committed_via_life_case: true
canvas_revalidates_typed_relation_refs: true
complete_relation_atlas_exists: false
general_candidate_path_policy_exists: false
system_best_path_claim_supported: false
r2_preflight_direction: frozen
r2_implementation_authorized: false
```

一句话：

> 六柱负责所见即所得地操作命盘；Relation Atlas 负责定义系统认识到的命理关系；
> 正式主路径必须明确说明它由谁提出、依据什么、如何验证以及由谁提交。
