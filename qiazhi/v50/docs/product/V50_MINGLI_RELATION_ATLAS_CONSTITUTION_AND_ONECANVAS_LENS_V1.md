# V50 Mingli Relation Atlas Constitution and OneCanvas Lens v1

```yaml
version: v1
frozen_at: 2026-07-19
status: DESIGN_BASELINE_FROZEN
analyst_direction: ACCEPTED
current_gate: R1_PRODUCT_REVIEW
relation_atlas_runtime_implementation: BLOCKED_PENDING_R1
relation_atlas_implementation_started: false
assisted_path_drawing: BLOCKED
production_deployment: BLOCKED
```

## 0. Constitution

> 六柱 OneCanvas 是命理关系世界最重要的直接操作投影，不是关系系统本身。

```text
Relation Atlas
定义系统认识到的命理关系世界

OneCanvas
让用户在六柱十二节点上直接操作和观察

Relation Lens
根据当前问题选择关系与信息深度

Path System
从具备路径资格的关系中形成可验证作用链

LLM Reasoner
比较、综合和解释已经存在的事实与候选

LifeCase
保存正式提交的认知、路径与完整来源
```

任何 Renderer、Abu、Theater 或 Xiangfa 都不得补算、创造或提升关系。

## 1. Authority Model

```text
Chart World / Temporal Snapshot
        ↓
Mingli Relation Engine
        ↓
RelationGraphSpec
        ↓
PathTransitionPolicy
        ↓
Candidate Path Generator
        ↓
WholePathValidator
        ↓
PathEvidenceVector
        ↓
LLM Reasoner / Analyst Review
        ↓
Commit Gate
        ↓
LifeCase Formal Path
        ↓
OneCanvas / Matrix / Theater / Xiangfa
```

### 1.1 Deterministic authority

系统算法拥有：

- 历法与四柱事实；
- 五行、阴阳、藏干、十神；
- 原子关系与复合关系识别；
- 时间阶段与关系实例；
- 路径资格；
- 候选路径生成；
- 路径方向、连续性、阶段一致性、阻断和闭合验证。

### 1.2 LLM authority

LLM 可以：

- 比较经过验证的候选路径；
- 结合全盘 Pattern、反证与现实问题形成综合理解；
- 提出带明确 provenance 的 `llm_proposal`；
- 解释某条关系、路径、条件或分歧；
- 在专业协议允许时提出提交建议。

LLM 不可以：

- 创建 RelationGraph 中不存在的关系；
- 绕过 PathTransitionPolicy 把任意关系连成路径；
- 绕过 WholePathValidator 声称路径闭合；
- 直接改变 `candidate / committed / blocked`；
- 把 Graph 排名候选称为算法最优结论。

正式 commitment 只能由 Commit Gate 或分析师动作产生。

## 2. One Core, Six Lenses, Three Depths

### 2.1 One Core

始终只有同一组十二个 semantic nodes：

```text
年干 年支
月干 月支
日干 日支
时干 时支
大运干 大运支
流年干 流年支
```

所有 Lens、Depth、理象转换和演时播放都保持：

- `semantic_ref` 不变；
- 节点身份不变；
- 节点语义位置不变；
- 当前选中对象不变；
- Sandbox 版本不变；
- PathDraft 不变。

### 2.2 Six Lenses

| Lens | Default content | Main question |
| --- | --- | --- |
| 总览 | 六柱、五行阴阳、十神、正式主路径、三项关键变化 | 这张盘当前最值得看什么？ |
| 五行 | 生、泄、克、耗、比和 | 力量如何作用？ |
| 合冲 | 五合、六合、冲、刑、害、破、三合、三会、三刑 | 哪些结构连接、牵制或扰动？ |
| 根透 | 藏干、通根、透干、同柱结构 | 节点从哪里得到根基，如何显现？ |
| 时运 | 大运、流年引发、增强、阻断、重开、共同补全 | 时间进入后改变了什么？ |
| 做功 | 正式主路径、Graph 候选、用户草稿、阻断、分叉 | 哪些关系形成连续作用链？ |

Lens 不是页面 Tab。它们只改变同一 Scene 中可见的关系集合和表达语法。

### 2.3 Three Depths

#### Overview

普通用户默认深度。只显示当前问题最重要的结构和变化。

#### Focus

选中一个节点后，只显示该节点一阶关系，并将其他节点标记为：

```text
正式可连
条件可连
存在关系但不可进入路径
没有关系
```

#### Audit

仅向授权专业角色披露：

```text
relation_type
rule_version
school_profile
formation_conditions
blocking_conditions
computed_at_stage
path_eligibility
origin_type
verified_by
llm_involved
epistemic_status
source_refs
```

## 3. Fixed Spatial Grammar

```text
                    天干关系轨道
      ─────────────────────────────────

 年干     月干     日干     时干     大运干     流年干
  │        │        │        │         │          │
 年支     月支     日支     时支     大运支     流年支

      ─────────────────────────────────
                    地支关系轨道
```

固定分工：

| Space | Relation family |
| --- | --- |
| 上方轨道 | 天干生克与五合 |
| 中央主轨 | 正式路径、Graph 候选、用户 PathDraft |
| 柱内纵向轨 | 同柱、藏干、通根、透干 |
| 下方轨道 | 六合、冲、刑、害、破 |
| 地支包围区 | 三合、三会、三刑等 Hyperrelation |
| 右侧时间源 | 大运、流年引动脉冲 |

响应式布局可以把六柱换行，但不得改变语义轨道与节点身份。

## 4. Relation Ontology

### 4.1 RelationDefinition

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
animation_cue:
theater_cue:
xiangfa_binding:
```

### 4.2 BinaryRelationInstance

用于确实可以表达为二元关系的结构：

```yaml
relation_instance_id:
relation_type_id:
from_node_ref:
to_node_ref:
stage: natal | luck | annual | luck_annual | sandbox
epistemic_status:
condition_results:
activation_refs:
blocking_refs:
provenance:
```

### 4.3 HyperRelationInstance

用于三合、三会、三刑等多节点结构：

```yaml
hyperrelation_instance_id:
relation_type_id:
member_refs: []
required_members: []
present_members: []
completion_state: complete | incomplete | temporal_complete | blocked
completion_source: natal | luck | annual | luck_annual | sandbox
formation_conditions: []
blocking_reasons: []
provenance:
```

Hyperrelation 不得为了方便绘制而拆成具有虚假方向的普通边。

### 4.4 ContextModifier

以下不是普通 edge：

```text
月令
旺衰
寒暖燥湿
节点状态
用神、忌神
格局
```

它们修饰节点、关系或假设，不直接进入普通路径遍历。

### 4.5 TemporalActivation

```yaml
activation_id:
source_temporal_node_ref:
target_relation_or_cluster_ref:
change_type: introduced | activated | reinforced | weakened | blocked | reopened | removed
reason_refs: []
stage:
provenance:
```

“时间柱出现”不自动等于“时间作用成立”。

## 5. Provenance

### 5.1 RelationProvenance

```yaml
origin_type: rule_engine | reasoner | analyst | migrated | llm_proposal
origin_ref:
rule_version:
school_profile:
computed_at_stage:
verified_by: compiler | reliability_gate | analyst | none
commitment_status: fact | candidate | committed | blocked | hypothetical
llm_involved: true | false
model_version:
derivation_fingerprint:
source_refs: []
```

### 5.2 PathProvenance

```yaml
origin_type: candidate_generator | reasoner | analyst | migrated | user_draft | llm_proposal
origin_ref:
candidate_path_ref:
relation_graph_version:
transition_policy_version:
validator_version:
evidence_vector_ref:
commitment_ref:
verified_by:
llm_involved:
model_version:
source_refs: []
```

所有未知来源必须显式标记 `unknown`，不得由字段位置猜测。

### 5.3 Disclosure

普通用户：

```text
来源：系统综合认知，已正式提交
结构验证：当前各段关系存在
```

专业审计：

```text
来源：LLM Reasoner 综合提出
状态：Reliability Gate 通过并提交 LifeCase
Graph 重验：3 / 3 段存在
整体连续闭合：待 WholePathValidator
算法最优：否
```

## 6. PathTransitionPolicy

每一种关系必须声明自己的路径能力：

```yaml
relation_type_id:
path_eligibility: never | direct | conditional
direction:
effect_kind: transmit | support | drain | control | bind | transform | activate | disrupt | block | context
required_context: []
forbidden_context: []
continuity_effect:
activation_effect:
blocking_effect:
reason_template:
```

初始硬边界：

| Relation | Default path eligibility |
| --- | --- |
| 生、泄、克、耗 | direct or conditional according to direction |
| 比和 | conditional support |
| 同柱位置 | never |
| 藏干 containment | never |
| 通根 | conditional support, not ordinary transmission |
| 透干 | conditional reveal, not ordinary transmission |
| 合 | conditional bind / transform |
| 冲 | conditional activate / disrupt / block |
| 刑、害、破 | conditional disrupt / block |
| 三合、三会 | conditional cluster transform |
| 月令、旺衰 | context only |

专业用户强制绘制的无合法关系段只能保存为：

```text
user_draft
missing_relation
not_formal
```

## 7. WholePathValidator

### 7.1 Input

```text
RelationGraphSpec
PathTransitionPolicy
Temporal Snapshot
Candidate Path or PathDraft
School Profile
```

### 7.2 Required checks

```text
每一段关系存在
方向兼容
节点首尾连续
所有段属于兼容时间快照
Hyperrelation 条件成立
不可重复节点约束
起点角色合理
终点角色合理
阻断已计入
闭合状态明确
provenance 完整
```

逐段存在只是必要条件，不是 WholePath PASS。

### 7.3 Output

```yaml
whole_path_status: valid | conditional | broken | invalid
validated_segments: []
invalid_segments: []
continuity_breaks: []
temporal_conflicts: []
hyperrelation_failures: []
blocking_refs: []
evidence_vector:
provenance:
```

## 8. PathEvidenceVector

未经校准的综合数值分统一降级为 `legacy_unvalidated`，不得公开显示。

```yaml
segment_validity: complete | partial | broken
direction_coherence: coherent | mixed | invalid
temporal_coherence: active | partial | inactive
root_support: strong | medium | weak | none
reveal_support: present | conditional | absent
blocking: none | minor | major
closure: closed | open | interrupted
provenance_quality: high | medium | low
```

界面只能把这些离散状态投影为视觉等级，不得暗示连续概率。

## 9. Relation Presentation Grammar

| Component | Relation family | Motion semantics |
| --- | --- | --- |
| FlowEdge | 生、泄、克、耗 | 有方向流动 |
| BondEdge | 五合、六合、比和 | 连接、结合或共同支持 |
| ConflictEdge | 冲、刑、害、破 | 冲击、持续制约、隐性干扰或裂痕 |
| RootEdge | 通根 | 向下扎根 |
| RevealEdge | 透干 | 向上显现 |
| HyperRelationBand | 三合、三会、三刑 | 多节点结构场 |
| TemporalPulse | 大运、流年引动 | 脉冲、激活、增强、阻断、重开 |
| PathOverlay | 正式、候选、用户路径 | 覆盖在基础关系上的连续作用 |
| BlockedMarker | 阻断 | 断裂、停止和原因定位 |
| ProvenancePopover | 来源与认识论 | 按角色披露 |

核心层次：

```text
基础关系：静态结构语法
时间引动：变化动画
做功路径：覆盖层连续流动
```

同一节点对的多重关系使用 Relation Bundle，不覆盖、不丢失：

```text
壬 ───── 丁
     克 · 合
```

## 10. Shared Projections

所有投影消费同一份 `RelationGraphSpec`：

| Projection | Purpose |
| --- | --- |
| OneCanvas | 直接操作六柱并理解关系位置 |
| Relation Matrix | 审计节点对的遗漏、重复和多重关系 |
| Hyperrelation Map | 审计三合、三会、三刑和时间补全 |
| Temporal Diff | 查看原局、大运、流年的离散变化 |
| Relation Ledger | 查看规则、来源、状态和条件 |
| Theater | 将同一关系编排成时间 Cue |
| Xiangfa | 将同一语义对象转换为象法表现 |
| Abu Context Pack | 约束解释范围 |

各投影只改变 presentation，不创建新 relation instance。

## 11. First Real-LifeCase Prototype Contract

R1 PASS 后，首个高保真原型只使用一份真实、已提交 LifeCase。

### 11.1 Desktop

```text
顶部：正式盘 / 实验 A / 实验 B，Undo / Redo / Reset，理象滑杆，演时

次级控制：总览｜五行｜合冲｜根透｜时运｜做功

主画布：六柱十二节点 + 固定关系轨道

底部摘要：当前 Lens 最重要的三项变化

选择后抽屉：聚焦关系；专业角色可继续进入审计层
```

### 11.2 Mobile

- 六柱可两行排布，但年/月/日/时/运/年身份固定；
- Lens 使用可横向滚动的紧凑标签；
- 默认只显示总览层；
- 聚焦与审计信息进入 Bottom Sheet；
- 不常驻 Relation Matrix；
- 路径控制、播放和恢复保持单手可达；
- 任何折叠不改变当前 Scene State。

### 11.3 Required tasks

```text
切换六种 Lens 而不丢失选中对象
聚焦一个节点并识别一阶关系
区分“存在关系但不可入路径”
查看正式主路径来源
查看一个多重关系 Bundle
查看一个 Hyperrelation
从原局播放到大运、流年
解释一次增强或阻断
返回总览并保持实验与 PathDraft
```

### 11.4 Prototype boundaries

```yaml
real_life_case_required: true
formal_state_writes: false
relation_inference_in_frontend: false
llm_relation_creation: false
assisted_path_drawing: false
production_deployment: false
```

## 12. Delivery Packages

The detailed promotion and synchronization contract is frozen in
`V50_RELATION_KNOWLEDGE_PROMOTION_AND_CORE_SYNC_V1.md`. The sequence below
supersedes the earlier five-package draft so `RA` identifiers have one meaning.

### RA1 Ontology, Provenance and Fixtures

- 完整 RelationDefinition；
- Binary / Hyper / Context / Temporal；
- 全部三合、三会、三刑；
- 多重关系共存；
- 流派配置。

RA1 不新增普通用户 UI，不修改 Reasoner 或 LifeCase。

### RA2 Relation Core

- Typed Temporal Multigraph；
- Hyperrelation 实例；
- 多重关系并存；
- 时间阶段编译；
- Graph Health。

### RA3 Path Core

- PathTransitionPolicy；
- Candidate Generator；
- WholePathValidator；
- PathEvidenceVector；
- legacy numeric score isolation。

### RA4 Historical Differential Audit

- 全量 LifeCase 关系与路径差异；
- 失效 commitment 清单；
- 分析师复核队列；
- 旧版本回放。

### RA5 Reasoner Contract

- 只消费已验证 RelationGraphSpec、CandidatePaths 与 PathEvidenceVector；
- 输出引用 relation/evidence ID；
- 不得绕过 Graph 创造关系。

### RA6 LifeCase Versioned Write

- 正式路径节点与关系引用；
- provenance 与验证版本；
- Reasoner 来源与 analyst gate；
- 不静默改写历史案例。

### RA7 Shared Projections

- 共享关系组件；
- OneCanvas 六镜三层；
- Matrix / Hyperrelation / Temporal Diff；
- Theater / Xiangfa / Abu binding；
- 投影忠实性与角色披露审计。

## 13. Gate

```text
R1 human product gate PASS
        ↓
RA1 ontology fixtures PASS
        ↓
RA2 relation core and provenance PASS
        ↓
RA3 whole-path validation PASS
        ↓
RA4 corpus differential audit PASS
        ↓
RA5 Reasoner citation contract PASS
        ↓
RA6 LifeCase versioned write PASS
        ↓
RA7 shared projection fidelity PASS
        ↓
authorize assisted path drawing
```

当前只冻结设计基线。未经 R1 PASS，不开始 RA Runtime，不部署生产。

## 14. Non-negotiable Invariants

1. 关系存在不等于可以进入做功路径。
2. Hyperrelation 不得降格为虚假二元边。
3. 同一节点对的多种关系不得互相覆盖。
4. 前端不得推导关系、路径资格或时间作用。
5. LLM 不得创建 Relation Graph 中不存在的关系。
6. LLM 提案不得自动变成 committed。
7. 逐段关系存在不等于整条路径闭合。
8. 未校准数值不得包装成概率、能量或专业置信度。
9. 被角色过滤的关系不得被 fallback 重新注入。
10. 所有视图共享 semantic identity 与 provenance。

## 15. Final Definition

> Relation Atlas 建立完整、可追溯的命理关系世界；OneCanvas 让人直接操作这个
> 世界；六种 Lens 帮助不同用户理解它；正式路径则是在这个世界中经过资格过滤、
> 整体验证、认知比较和提交门禁后形成的一条可解释作用链。
