# V20 下一阶段主线推进计划

更新时间：2026-05-20

## 当前判断

V20 第一阶段已经完成工程闭环：

```text
中枢大脑
-> 知识库
-> 八字规则
-> 八字特征
-> 八字上下文绑定
-> 八字画像
-> 智能问答
-> 角色视图
-> LLM 上下文
-> 合成验证
-> 518K 语料回放
-> 参数目标
-> runtime pointer
-> Admin 可观测
```

但这不等于命理能力已经满分。当前系统进入第二阶段：把训练产物从“能生成、能消费”推进到“更可信、更稳定、更容易自动生效”。

当前新增最高优先级约束：所有模块必须绑定当前被测算八字、大运、流年和流月。详见：

```text
docs/V20_BAZI_CONTEXT_BINDING_PLAN.md
```

2026-05-20 新增主线：问答交互系统重构。智能问题从“推荐八字知识问题”升级为“围绕当前命主八字的对话式测算系统”。新的执行总纲见：

```text
docs/V20_QA_INTERACTION_REFACTOR_MAINLINE.md
docs/V20_BAZI_ANCHORED_QUESTION_REFACTOR.md
```

优先级高于继续扩容智能问题样本。原因：如果提问本身脱离当前命盘，后续 LLM 回答、点击训练、DAG 追问和 518K 回放都会被泛问题污染。

当前状态：问答交互重构主线已完成第一版 100% 验收。后续回到质量扩容和 518K 回放，重点观察 `anchor_bound_rate`、`generic_question_rate`、真实点击反馈和角色表达稳定性。

## 机器状态快照

```text
mainline_status: 100%
central_brain_architecture: 100%
knowledge_status: complete
knowledge_rule_count: 494
knowledge_runtime_allowed_count: 494
external_topic_coverage: 21 / 21
synthetic_case_count: 55
synthetic_smoke_cases: 14
runtime_consumption: 7 / 7 consumed
candidate_promotion_score: 1.0
candidate_promotion_threshold: 0.82
```

2026-05-17 本轮推进后，线上 `linux_0_13` profile 已完成第一批 518K 小分片 smoke：

```text
run_id: codex_mainline_corpus_smoke
precompute_limit: 16
precompute_status: completed
artifact_status: completed
training_artifacts_status: ready
corpus_pointer_status: candidate_active
active_policy_version: v20.corpus_policy.candidate.6841c207b118
candidate_promotion_score: 0.6319
candidate_promotion_threshold: 0.82
similar_case_stability: 0.0312
```

结论：corpus 主链已经从“未构建”推进到“可消费并已生效”。下一步不是继续改框架，而是扩大样本规模，让相似盘稳定性从小分片低值提升到可推广水平。

同日继续扩容后：

| run_id | limit | precompute | artifacts | pointer | score | similar_case_stability |
|---|---:|---|---|---|---:|---:|
| codex_mainline_corpus_smoke | 16 | completed | completed | candidate_active | 0.6319 | 0.0312 |
| codex_mainline_corpus_64 | 64 | completed | completed | candidate_active | 0.6675 | 0.125 |
| codex_mainline_corpus_256 | 256 | completed | completed | candidate_active | 0.81 | 0.5 |
| codex_mainline_corpus_1024 | 1024 | completed | completed | candidate_active | 1.0 | 1.0 |

1024 分片已把 candidate quality 推过阈值：

```text
candidate_quality_status: ready_for_candidate_apply
promotion_decision: promote_candidate
active_policy_version: v20.corpus_policy.candidate.da1d717aff53
```

同日继续推进 rule/portrait 后：

```text
portrait_batch_case_count: 98
portrait_batch_failure_count: 0
portrait_pointer_status: candidate_active
portrait_active_policy_version: v20.portrait_policy.candidate.fc39343a086a
portrait_policy_count: 15

rule_replay_eval_status: ready
rule_replay_evaluated_packet_count: 380
rule_runtime_activation_count: 380
rule_pointer_status: candidate_active
rule_active_policy_version: v20.rule_policy.candidate.f9787e2957386254
```

2026-05-18 结构动态 518K path distribution 扩容到 1024 稳定分片：

```text
run_id: codex_structure_dynamics_1024
limit: 1024
status: completed
failure_count: 0
unsupported_label_count: 0
knowledge_coverage.status: covered_current_scope
knowledge_coverage.unsupported_count: 0
structure_dynamics_pointer_status: candidate_active
structure_dynamics_active_policy_version: v20.structure_dynamics_policy.candidate.ae30e2a428eb
corpus_distribution_case_count: 1024
```

本轮观察到的主结构分布：

| 标签 | count | ratio |
|---|---:|---:|
| 输出制官杀 | 414 | 40.43% |
| 食神制杀 | 228 | 22.27% |
| 伤官制杀 | 193 | 18.85% |
| 财生官/财滋杀 | 134 | 13.09% |
| 食伤生财 | 48 | 4.69% |
| 印星承身 | 5 | 0.49% |
| 官印/杀印相生 | 2 | 0.20% |

1024 分片一度发现 `resource->self` 路径被泛化成“核心做功链”。已补入 `印星承身` 机制单元，并修正 dominant label 选择：主路径只要能匹配知识机制，就必须使用机制名；runtime 语义阈值只影响候选置信，不允许回落为泛化标签。

2026-05-19 结构动态第二个 1024 分片继续扩容：

```text
run_id: codex_structure_dynamics_2048_window
start: 1024
limit: 1024
status: completed
failure_count: 0
unsupported_label_count: 0
knowledge_coverage.status: covered_current_scope
structure_dynamics_pointer_status: candidate_active
structure_dynamics_active_policy_version: v20.structure_dynamics_policy.candidate.7a59d11d275d
corpus_distribution_case_count: 1024
corpus_distribution_run_id: codex_structure_dynamics_2048_window
corpus_distribution_start: 1024
```

本轮观察到 `self -> day_master` 的同气承接路径，原本会退回“核心做功链”。已补入 `比劫承身` 机制单元，并把结构动态策略 payload 扩展为记录 `run_id/start/target_count`，保证训练直接生效后能追踪到具体分片来源。

本轮主结构分布：

| 标签 | count | ratio |
|---|---:|---:|
| 输出制官杀 | 409 | 39.94% |
| 食神制杀 | 244 | 23.83% |
| 伤官制杀 | 165 | 16.11% |
| 食伤生财 | 99 | 9.67% |
| 财生官/财滋杀 | 91 | 8.89% |
| 比劫承身 | 7 | 0.68% |
| 财破印 | 7 | 0.68% |
| 印星承身 | 2 | 0.20% |

本轮还修正了规则验证状态机：合成样例里的失败不再把整个 domain 的规则全部阻断。只要同一 domain/rule 有通过样例，失败样例会作为反例和继续训练信号进入 subcondition/replay，而不是恢复人工审核 gate。

`runtime_consumption = consumed` 表示 runtime 已经能读取对应 pointer，不表示所有 pointer 已 active。

当前 pointer 状态：

| Family | 状态 | 判断 |
|---|---|---|
| orchestrator | baseline_active_fast_track_ready | 中枢可消费候选，但当前仍在 baseline/fast-track 就绪态 |
| question | candidate_ready | 智能问题已有候选 |
| knowledge | candidate_ready | 知识映射已有候选 |
| role_view | not_enough_data | 角色交互样本不足 |
| rule | candidate_active | 380 条规则权重策略已直接生效 |
| portrait | candidate_active | 15 条画像权重策略已直接生效 |
| corpus | candidate_active | 518K 小分片 artifact 已生成，candidate 已直接生效 |
| structure_dynamics | candidate_active / consumed | SDE v2 合成做功链通过，active pointer 写入器已接入训练 bundle，runtime path scorer 已消费 active pointer，UI 主读为 `primary_dynamic_chain` |

## 核心原则

```text
不继续堆新模块
不恢复人工审核 gate
不让训练只停留在 artifact
不让 518K 直接成为单盘真值
```

下一阶段只做能提高机器 gate 可信度、candidate quality、runtime pointer active 率的任务。

## 第二阶段目标

```text
candidate_quality_signal: 0.62 -> 0.82+
corpus artifact: not_built -> partial_ready -> ready
rule pointer: blocked -> candidate_ready -> active
portrait pointer: blocked -> candidate_ready -> active
structure dynamics: runtime/ui ready -> SDE v2 graph redesign -> dynamic path policy candidate -> active pointer writer -> runtime scorer consumption -> larger 518K path distribution
bazi context binding: implicit -> explicit BaziContextFrame -> drift scoring
role_view pointer: not_enough_data -> answer_governance_active / candidate_ready
synthetic cases: 14 smoke -> 50+ topic cases
```

## P0: 八字上下文绑定

这是所有模块的最高级合同：

```text
BaziContextFrame = 当前原局四柱 + 大运 + 流年 + 流月
```

任何输出都不能脱离当前 context：

```text
结构动态必须来自当前八字和时间层
画像必须来自当前规则、特征和裁决
智能问题必须来自当前证据缺口和主线
LLM 只能消费锁定后的上下文包
训练只能调参，不能改写当前命盘事实
```

当前已落地：

```text
runtime_result.bazi_context_frame
runtime_result.context_alignment_report
training_plan.candidate_quality_signal.quality_scores.bazi_context_drift_score
training_plan.central_brain_tuning_package
training_plan.optimization_topics[].training_groups
training_task.result_summary.context_quality_signal
structure_dynamics.context_binding
decision_report.portrait_projection.context_binding
question_intent_model.context_binding
question_context_binding
llm_assist.context_pack.context_binding
role_view_model.context_binding
context_binding.evidence_anchors
Workbench UI 八字上下文面板
```

当前已补齐：

```text
Admin 训练页展示训练是否继承当前八字上下文
预留 geo_context 扩展位
```

下一步：

```text
把 context_quality_signal 的偏离原因细化到模块级别
在训练结果中展示结构动态语料 shard 是否覆盖当前主线类型
```

## P1: 518K 小分片回放与 corpus artifact

当前最大 blocker 是 corpus：

```text
corpus_artifact_status: completed
corpus_training_status: ready
similar_case_stability: 1.0
candidate_quality_signal: ready_for_candidate_apply
```

推进顺序：

```text
run_full_precompute.py --run-id codex_mainline_corpus_256 --limit 256 --status-every 32 --progress
build_corpus_artifacts.py --run-id codex_mainline_corpus_256 --progress --no-sqlite
build_corpus_artifacts.py --run-id codex_mainline_corpus_256 --status
build_corpus_artifacts.py --run-id codex_mainline_corpus_256 --training
```

验收：

```text
artifact_status: completed
training_artifacts.status: ready
similarity_manifest exists
portrait_axis_training exists
rule_proposal_training exists
candidate_quality_signal.similar_case_stability > 0
corpus pointer blocker 减少
```

注意：这仍是小分片，不是全量 518K。目标是先把 artifact 链跑通，再逐步扩大 limit。

## P2: Rule replay gate

当前状态：

```text
rule: candidate_active
rule_replay_eval_status: ready
runtime_activation_count: 380
```

推进顺序：

```text
run_rule_synthetic_training.py --progress
run_rule_replay_eval.py --progress
run_decision_registry_iteration.py --progress
run_training_iteration.py --write --progress --include-replay-eval --include-rule-iteration
```

验收：

```text
rule pointer 不再 blocked
rule replay result ready
false positive / counterexample signal 可读
rule_policy_effect 进入 runtime
```

## P3: Portrait batch gate

当前状态：

```text
portrait: candidate_active
rule_portrait_batch_status: pass
portrait_policy_count: 15
```

推进顺序：

```text
run_rule_portrait_batch.py --progress
run_practitioner_calibration_training.py --progress
run_training_iteration.py --write --progress --dynamic-limit 8
```

验收：

```text
portrait pointer candidate_ready / active
portrait_axis_weight 可读
portrait drift score 保持稳定
不同角色画像深度不串线
```

## P4: 结构动态 v2 重构与训练专题

状态：2026-05-18 已完成主链落地，进入规模扩容。

结构动态不是旁路展示模块，它现在已经在测算链路里作为动态事实层存在：

```text
api.runtime -> build_structure_dynamics
orchestrator.evidence -> structure_dynamics evidence
orchestrator.brain_state -> dynamic chain / stability / time layer
workbench UI -> 结构动态面板
```

当前实现已暴露一个主线偏差：旧 SDE 用少数固定十神段落选择 `dominant_chain`，容易把“核心通路提取”退化为“固定套路套用”。这与 `V20_V21_STRUCTURE_DYNAMICS_ENGINE.md` 的 Weighted Dynamic Graph 设计不一致。

P4 升级为 SDE v2 重构主线：

```text
当前八字 + 大运 + 流年 + 流月
-> DynamicGraphBuilder
-> PathExtractor
-> KnowledgeSemanticMatcher
-> StructureDynamicsV2Payload
-> OrchestratorEvidence / BrainState / UI / Training
```

设计合同：

```text
docs/V20_STRUCTURE_DYNAMICS_V2_REDESIGN.md
```

P4.1 兼容骨架：

```text
新增 dynamics/graph_engine.py
输出 dominant_path / candidate_paths / semantic_candidates
旧 dominant_chain 已移除对外输出；内部 legacy_dynamic_chain 仅供排查
状态：已完成
```

P4.2 主算法从固定 `CHAIN_SEGMENT_PRIORITY` 迁移到图路径评分：

```text
node_strength
edge_strength
visibility
continuity
time_activation
terminal_convergence
blockage_penalty
状态：已完成
```

P4.3 把结构动态显式纳入训练计划：

```text
topic_key: structure_dynamics
atomic_trainings:
  - structure_dynamics_synthetic
  - synthetic_case_suite
  - rule_replay_eval
  - rule_portrait_batch
  - training_iteration_fast
parameter_targets:
  - dynamic_path_weight
  - semantic_match_weight
  - volatility_threshold
  - time_trigger_weight
  - structure_stability_floor
runtime_pointer_targets:
  - structure_dynamics_runtime_policy_pointer
  - orchestrator_runtime_policy_pointer
  - rule_runtime_policy_pointer
synthetic_gates:
  - dynamic_path_consistency
  - semantic_candidate_precision
  - time_layer_boundary
  - no_event_prediction
状态：已完成
```

P4.4 当前剩余工作是扩容，不是重构：

```text
structure_dynamics_corpus_distribution 32 -> 256 -> 1024 -> 2048 window -> scheduled shard
观察 unsupported_label_count、top_labels、counterexample_coverage、time_blocker_coverage
只有路径标签能回到 knowledge.structure_mechanisms 和八字知识目录时才允许 candidate_active
```

验收：

```text
结构动态继续保持 deterministic，不调用 LLM
结构动态只提供动态上下文，不输出最终断语
中枢仲裁同时消费规则、画像、问题意图和结构动态
Admin 训练计划能看到 structure_dynamics 训练专题
测算页能看到核心做功链、承接、阻断和岁运引动
合成样本能区分相似路径，例如食伤生财、制杀、杀印、财滋杀
```

## P5: Synthetic case 扩容

当前 smoke coverage 是 pass，但数量偏小：

```text
synthetic_smoke_cases: 14
coverage_gap_count: 0
```

下一阶段扩到 50+ cases。每个专题必须有：

```text
正例
反例
边界例
metamorphic pair
```

优先专题：

```text
强弱承载
用神路径冲突
十神位置与混杂
干支冲合刑害并见
真假从格 / 破格 / 清浊
岁运并临 / 伏吟反吟 / 墓库开闭
事业财富关系健康边界
角色泄露
问题 DAG 发散与重复
```

验收：

```text
synthetic_case_count >= 50
每个 P1/P2/P3 专题至少 4 case
rule/portrait/question/role evaluator 都能输出 failure reason
training_iteration_fast 默认仍保持可运行
```

## P6: 角色与智能问答真实交互信号

当前状态：

```text
role_view: not_enough_data
question: candidate_ready
```

推进方向：

```text
role_question_click ledger
question DAG path replay
followup / skip / helpful / unhelpful reward
role-specific question order
answer governance style policy
```

验收：

```text
role_view pointer 至少进入 answer_governance_active
guest/user/practitioner/admin 问题路径分离稳定
智能问题 candidate 不只是生成，而能被 replay 比较
```

## 执行顺序

当前优先级：

```text
1. 结构动态 518K path distribution 从 1024 扩到 scheduled shard，并保持 unsupported label = 0
2. synthetic case 从 55 扩到 topic-level 正例/反例/边界/metamorphic 组合
3. Role/Question 真实交互样本积累，提升 role_view candidate 数据量
4. 知识库 mechanism units 从桥接层升级为完整知识库机制单元
5. 持续检查 UI 是否只展示最新主线：中枢、知识、规则、画像、智能问答、结构动态、训练直生效
6. 中枢主读字段保持 `primary_dynamic_chain`，旧字段只做兼容
```

## 当前本轮推进动作

本轮已执行 P1 的最小安全步：

```text
run_id: codex_mainline_corpus_smoke
precompute_limit: 16 -> 64 -> 256 -> 1024
sqlite_cache: disabled
runtime_pointer_write: direct candidate activation
runtime_profile: linux_0_13
status: completed
```

P1 smoke、256 分片和 1024 分片已通过，`candidate_quality_signal` 已越过 `0.82` 阈值。rule/portrait 两条 pointer 已从 blocked 推进到 candidate_active。结构动态已补齐 SDE v2 图路径、BrainState/UI 展示、合成验证任务、`structure_dynamics_runtime_policy_pointer` 写入器、runtime scorer 消费和 `knowledge.structure_mechanisms` 语义命名桥接层。结构动态合成样本已从 3 扩到 27，当前 pass_rate、dynamic_path_consistency、semantic_candidate_precision 均为 1.0；财破印、比劫夺财、印制食伤、印星承身、比劫承身、官印/杀印相生、正官型输出制官杀和岁运冲合阻断已进入 synthetic gate。Admin 训练计划已展示结构动态覆盖、结构知识覆盖、结构语料回放、反例覆盖、岁运阻断覆盖和主链切换报告。当前新增 `validation.structure_dynamics_knowledge_coverage` 和 `validation.structure_dynamics_corpus_distribution`，要求观察到的结构标签必须能回到机制单元、完整 KnowledgeUnit、八字知识目录和规则目录；语料回放发现 unsupported label 时会阻断结构动态 runtime pointer，空主链兜底状态不作为知识标签。2026-05-20 已完成 `codex_structure_dynamics_9216_window`，从 `start=8192` 再回放 1024 盘，failure 0、unsupported label 0，active pointer 已推进到 `v20.structure_dynamics_policy.candidate.189b9461a5e6`。中枢和 UI 主读已统一为 `primary_dynamic_chain`，旧 `dominant_chain` 已从 raw runtime 输出和角色投影中移除，只保留 `legacy_dynamic_chain` 作为内部排查字段；同节点主线合并时由闭合结构动态主链负责命名，规则候选只补证据。下一步只剩继续扩大 518K 分片、补更冷门 synthetic topic cases、积累真实角色/问题反馈。

智能问题进入新主线：见 `docs/V20_SMART_QUESTION_RECOMMENDER_PLAN.md`。下一阶段把现有 `QuestionCandidate`、`question_seed_registry`、`question_dag`、`question_agent`、`role_question_click_ledger` 和 `question_runtime_pointer` 收束成对话式问题推荐系统。核心原则是所有问题必须绑定当前八字、大运流年、结构动态主链、规则和画像；下一问必须和上一问有合法 DAG 连续性；已问问题进入 suppression/cooldown；不同角色使用不同叙事风格，Admin 显示推荐原因和训练状态。
