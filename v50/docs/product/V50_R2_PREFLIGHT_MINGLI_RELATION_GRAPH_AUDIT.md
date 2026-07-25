# V50 R2 Preflight: Mingli Relation Graph Audit

```yaml
status: FROZEN_FOR_POST_R1_EXECUTION
current_phase: R1_PRODUCT_REVIEW
current_source_audit: COMPLETE
current_source_audit_ref: V50_RELATION_ATLAS_AND_PATH_PROVENANCE_CURRENT_STATE_AUDIT_V1.md
approved_design_baseline: V50_MINGLI_RELATION_ATLAS_CONSTITUTION_AND_ONECANVAS_LENS_V1.md
knowledge_promotion_baseline: V50_RELATION_KNOWLEDGE_PROMOTION_AND_CORE_SYNC_V1.md
r1_human_review_protocol: V50_ONECANVAS_R1_UNGUIDED_HUMAN_PRODUCT_REVIEW_V1.md
ui_change_in_this_preflight: false
r2_path_ui_authorized: false
production_deployment: false
```

## 0. Decision

做功路径不是一个孤立的画线功能。它要求系统先回答：盘中有哪些关系、
关系何时成立、哪些关系有方向、哪些关系能够参与路径、时间进入后关系是
新增、激活、增强、受阻还是重新打开。

因此 R1 产品门禁通过后的下一唯一获准切片冻结为：

> **RA1 · Relation Ontology, Provenance and Fixtures**

本文件保留 `R2 Preflight` 历史名称，用于记录进入辅助画路前必须完成的
关系审计。RA1 只定义命理关系本体、来源、流派与正反时间 Fixtures，不修改
OneCanvas 用户界面，不提前实现辅助画路。

## 1. Graph Model

六柱关系世界采用：

```text
Typed Temporal Multigraph + Hypergraph
```

- 同一对节点可以同时保留生克、五合等多种关系；
- 三合、三会、三刑等使用多节点 cluster，不拆成互相冒充的普通二元边；
- 每个关系实例明确属于原局、大运、流年、岁运或跨阶段补全；
- 关系存在不等于可以作为做功路径传递。

## 2. Epistemic Layers

```text
atomic_fact       五行、阴阳、藏干、十神映射、基础生克
structural        五合、六合、冲、刑、害、破、通根、透干
candidate         合化、成局、半合、拱合、合绊、路径闭合
committed         LifeCase 已提交的主路径、机制与阻断
hypothetical      Sandbox、假设时间、用户 PathDraft
```

候选、正式与实验关系可以同时呈现，但不得互相升级或覆盖。

## 3. Canonical Contracts

### `RelationDefinition`

```yaml
relation_type_id:
family:
name:
arity:
symmetry:
direction_model:
participant_constraints:
formation_conditions:
blocking_conditions:
temporal_behavior:
path_behavior:
school_profile:
source_refs:
visual_family:
explanation_template:
```

### `RelationInstance`

```yaml
relation_instance_id:
relation_type_id:
participant_refs:
stage: natal | luck | annual | luck_annual | cross_stage
epistemic_status:
condition_results:
activation_refs:
blocking_refs:
source_refs:
```

### `RelationClusterInstance`

```yaml
members:
required_members:
present_members:
completion_state:
completion_source:
break_or_block_reasons:
```

### `PathTransitionPolicy`

```yaml
eligible:
direction:
effect_kind: transmit | support | drain | control | bind | transform | activate | block | context
requires_context:
continuity_effect:
activation_effect:
blocking_effect:
reason_template:
```

## 4. Relation Coverage

第一版目录至少覆盖：

```text
五行：生、泄、克、耗、比和
天干：生克、五合、合化候选、合而不化、争合、合绊
地支：六合、六冲、三合、半合、拱合、三会、三刑、自刑、六害、六破
纵向：藏干、通根、透干、同柱生克、坐支，以及候选层的盖头、截脚
时间：原局与大运、原局与流年、岁运、跨阶段补全、激活、增强、阻断、重开
复合：伏吟、反吟、岁运并临、天合地合、天克地冲
```

流派争议规则必须声明 `school_profile`，不得作为全局原子事实。

## 5. What Is Not an Edge

以下内容不得被前端或 Compiler 偷偷降格为普通边：

- 十神：节点相对日主的角色标签；
- 月令、旺衰：上下文或节点状态修饰；
- 用神、忌神、格局：正式认知与解释层；
- 能量分数：尚待校准的评估结果；
- 视觉距离：展示属性，不改变命理语义。

## 6. Audit Method

### Atomic exhaustive tests

```text
10 × 10 天干有序对
12 × 12 地支有序对
12³ 地支三元组
12⁴ 地支四元组
60 × 60 六十甲子有序对
```

### Fixtures for every relation

```text
最小成立
最小不成立
只差一个条件
时间补全
时间破坏
多重关系并存
```

### Properties

- 对称关系保持对称，方向关系保持方向；
- cluster 成员顺序不改变识别结果；
- 移除时间输入后恢复原局；
- 多重边不覆盖；
- candidate 不自动升级 committed；
- 被角色过滤的关系不经 fallback 回填；
- 同输入产生同实例、同来源和同排序。

### Graph health

检查无来源、重复、方向错误、参与节点缺失、cluster 非法拆边、时间残留、
路径引用不存在边、候选误提交等问题。

## 7. Relation Lenses

R2 路径提示不得从全量关系做无约束最短路。Compiler 必须按透镜输出
`path-eligible transitions`：

```text
五行流转
制化链
根透链
合局链
时间引动链
综合做功
```

OneCanvas 只显示当前透镜允许的连接目标；专业用户强制画出的无关系段必须
保持 `user_draft + missing`，不能伪装为系统关系。

## 8. Shared Visual Grammar

关系定义映射到复用组件，而不是每类规则手写 SVG：

```text
DirectedFlowEdge
BidirectionalBond
ConflictEdge
SupportEdge
RevealEdge
RelationCluster
TemporalActivationEdge
BlockedPathMarker
```

统一映射链：

```text
relation_type
→ visual_family
→ visual_token
→ explanation
→ theater_cue
→ xiangfa_binding
```

## 9. Required Deliverables

1. 四个正式 Contract 与版本号；
2. Relation Catalog；
3. Path Eligibility Matrix；
4. 原子穷举、正反 Fixture 与性质测试；
5. Graph Health 审计器；
6. Relation Coverage Matrix；
7. 内部 Mingli Relation Atlas / Inspector；
8. 三份真实 LifeCase 的分析师逐类审阅；
9. 失败项及最小修正记录；
10. R2 是否获准进入辅助画路径的门禁报告。

Coverage Matrix 至少包含：

```text
compiler support
fixture coverage
path eligibility
visual family
explanation
theater cue
xiangfa binding
analyst approval
```

## 10. Gate

```text
R1 human product gate PASS
        ↓
RA1 relation ontology and fixtures PASS
        ↓
RA2 relation core deterministic
        ↓
RA3 path policy and whole-path validation PASS
        ↓
RA4 full-corpus differential audit PASS
        ↓
RA5–RA7 contracts and projection fidelity PASS
        ↓
Only then authorize R2 assisted path drawing
```

发现命理算法缺陷时，必须先用失败 Fixture 证明，再修 Compiler。Renderer、
Abu、Theater 和 Xiangfa 都不得补算、猜测或提升关系。

## 11. Boundaries

```yaml
r1_product_review_continues: true
onecanvas_ui_modified: false
path_drawing_ui_added: false
reasoner_rewritten: false
life_case_modified: false
formal_state_written: false
production_deployed: false
```

## 12. Current Implementation Finding

当前代码来源审计已经完成，正式结论见：

`V50_RELATION_ATLAS_AND_PATH_PROVENANCE_CURRENT_STATE_AUDIT_V1.md`

其中冻结了三个事实：

1. Canvas 运行时关系来自确定性 Graph，不是 LLM 临时生成；
2. 当前正式 `work_path` 通常由 LLM Reasoner 综合形成，经门禁后提交到 LifeCase；
3. OneCanvas 展示的是该已提交认知在当前 Graph 上的逐段映射结果，不是完整
   Relation Atlas 自动选出的“系统最佳路径”。

现有 Graph 仍存在样本特化、关系目录不完整、Hyperrelation 被拆成普通边、路径
资格过宽和 provenance 分散等问题。因此 source audit 完成不等于 R2 implementation
获准；R1 真人产品门禁与本文件第 10 节 Gate 保持不变。

## 13. Approved Product and Implementation Baseline

分析师复核后，Relation Atlas 与 OneCanvas 的批准设计基线冻结于：

`V50_MINGLI_RELATION_ATLAS_CONSTITUTION_AND_ONECANVAS_LENS_V1.md`

它正式定义：

- 一核六镜三层；
- 天干、地支、柱内、中央做功与时间源的固定空间语法；
- BinaryRelation、HyperRelation、ContextModifier 与 TemporalActivation；
- RelationProvenance 与 PathProvenance；
- PathTransitionPolicy、WholePathValidator 与离散 PathEvidenceVector；
- 共享 Relation Presentation Grammar；
- RA1–RA7 实施包和首个真实 LifeCase 高保真原型范围。

该文档是 post-R1 实施基线，不改变当前 Gate。设计冻结不等于 Runtime 获准。
