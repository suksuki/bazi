# V20 Structure Dynamics Engine v2 重构设计

## 背景

当前 `dynamics/engine.py` 已接入 runtime、UI、中枢和回答上下文，但它的主链算法已经偏离原始设计。

原始设计要求 SDE 是确定性的动态结构事实层：

```text
当前八字 + 大运 + 流年 + 流月
-> 加权动态图
-> 核心通路 / 做功链提取
-> 知识库机制定性
-> 中枢大脑统一仲裁
```

现有实现实际更接近：

```text
十神压缩成 output / wealth / authority / resource / self
-> 固定链路模板排序
-> 规则命中加权
-> 输出 dominant_chain
```

这会造成两个问题：

- 系统只能在少数固定套路里选择，无法真正发现当前八字的核心做功通路。
- 新增一个误判时容易继续补模板，例如补一个“食神制杀”，但这不是建模层的正确方向。

因此 SDE v2 的目标不是继续扩充固定 chain list，而是恢复“先计算核心通路，再由知识库定性”的架构。

## 核心原则

1. **被测八字和时间层是唯一核心上下文**

   所有结构动态都必须来自当前原局四柱、大运、流年、流月。画像、问题、角色、LLM 不能反向影响 SDE。

2. **SDE 是事实层，不是断语层**

   SDE 输出动态结构、主链、阻断、承接、稳定性、显化度和候选定性，不输出财富、事业、婚恋等结果断语。

3. **先算链，再命名**

   图算法先找出最强通路，例如：

   ```text
   丁食神 -> 辛七杀 -> 癸偏印 -> 乙日主
   ```

   知识库再定性为“食神制杀”“杀印承接”“输出制官杀”等候选机制。

4. **确定性运行，训练只调参**

   Runtime 不调用 LLM，不依赖人工审核。训练结果只更新权重、阈值、排序参数和语义匹配策略。

5. **中枢统一消费**

   SDE v2 输出进入中枢证据编译，由中枢和规则、画像、问题意图一起仲裁。

## SDE v2 数据流

```text
ChartFacts
-> TimeContext
-> FeatureLayer
-> DynamicGraphBuilder
-> PathExtractor
-> PathStateEvaluator
-> KnowledgeSemanticMatcher
-> StructureDynamicsV2Payload
-> OrchestratorEvidence
-> MainlineArbitration / BrainState / UI / LLM Context
```

## 图模型

### 节点

| 节点类型 | 示例 | 作用 |
| --- | --- | --- |
| `day_master` | 乙日主 | 所有十神关系的中心锚点 |
| `stem` | 年干辛、时干丁 | 透干、显化、直接作用 |
| `hidden_stem` | 丑中辛、癸、己 | 暗藏、持续、根气和潜在作用 |
| `branch` | 酉、巳、卯、丑 | 地支关系、根气、宫位 |
| `ten_god` | 食神、七杀、偏印 | 关系语义节点 |
| `element` | wood/fire/earth/metal/water | 生克网络 |
| `time_layer` | 大运、流年、流月 | 引动和阶段背景 |
| `structure_candidate` | 输出制官杀、财生官 | 知识库语义候选，不参与事实生成 |

### 边

| 边类型 | 含义 | 方向 |
| --- | --- | --- |
| `reveal` | 透干显化 | pillar/stem -> ten_god |
| `hide` | 藏干潜伏 | branch -> hidden_stem -> ten_god |
| `generate` | 五行相生 | source -> target |
| `control` | 五行相克 / 制约 | source -> target |
| `root` | 通根和承接 | branch/hidden -> day_master 或 ten_god |
| `activate` | 岁运引动 | time_layer -> natal node |
| `combine` | 合、合住、合动 | branch/stem -> branch/stem |
| `clash` | 冲动、释放、失稳 | branch -> branch |
| `block` | 阻断、制约、失稳 | blocker -> path node |
| `support` | 承接、缓冲 | resource/self -> pressure/output |

## 主链提取

SDE v2 不再依赖固定 `CHAIN_SEGMENT_PRIORITY` 作为主算法。主链来自 top-k path 搜索。

### 候选起点

优先从当前盘里能量较高的节点开始：

- 透干十神
- 月令相关十神
- 被大运/流年引动的节点
- 高权重藏干
- 规则和 feature 层标记的 dominant structures

### 候选终点

终点不是固定套路，而是结构收束点：

- 日主承接：路径回到 day_master / self / resource。
- 财星收束：输出进入财星并被日主或系统承接。
- 官杀收束：压力被制、化、承接或阻断。
- 印星收束：压力转入支持。
- 阻断终点：路径被冲、合、印制、比劫分夺等阻断。

### 路径评分

```text
path_score =
  node_strength
  + edge_strength
  + visibility
  + continuity
  + time_activation
  + terminal_convergence
  - blockage_penalty
  - drift_penalty
```

参数由训练优化：

- `dynamic_node_weight`
- `dynamic_edge_weight`
- `visibility_weight`
- `time_trigger_weight`
- `root_continuity_weight`
- `blockage_penalty`
- `terminal_convergence_weight`
- `semantic_match_threshold`
- `volatility_threshold`
- `structure_stability_floor`

## 链路状态

每条路径都输出状态：

| 状态 | 含义 |
| --- | --- |
| `closed` | 路径有连续承接和收束 |
| `partial` | 路径成立但缺少一段承接 |
| `blocked` | 关键节点被制、冲、合住或反证阻断 |
| `leaking` | 能量外泄，未形成明确收束 |
| `volatile` | 岁运冲动或触发导致波动放大 |
| `overdriven` | 某节点过载，主线强但稳定性下降 |
| `collapsed` | 核心路径被破坏，主链切换到备选链 |

## 知识库定性

知识库不决定主链，只给已提取路径命名和解释边界。

例如图算法提取：

```text
食神 -> 七杀 -> 印星 -> 日主
```

知识库候选：

- 食神制杀
- 杀印相生
- 输出制官杀后由印承接

如果图算法提取：

```text
食伤 -> 财 -> 官杀
```

知识库候选：

- 食伤生财
- 财生官
- 财滋杀
- 食神生财制杀

定性必须附带：

- required_context
- matched_context
- missing_context
- counter_evidence
- boundary
- confidence

## 输出合同

SDE v2 保持对现有字段兼容，同时新增图路径字段。

```json
{
  "version": "v20.structure_dynamics.v2",
  "dominant_chain": {
    "chain_key": "output->authority->resource",
    "nodes": ["output", "authority", "resource"],
    "state": "partial",
    "terminal_node": "resource",
    "pattern_key": "knowledge.semantic.output_authority_resource",
    "pattern_label": "输出制官杀后由印承接",
    "path_id": "dynamic_path.1"
  },
  "dominant_path": {
    "path_id": "dynamic_path.1",
    "node_labels": ["丁食神", "辛七杀", "癸偏印", "乙日主"],
    "edge_labels": ["制约", "转化", "承接"],
    "score": 0.82,
    "state": "partial",
    "terminal": "乙日主"
  },
  "candidate_paths": [],
  "semantic_candidates": [],
  "path_diagnostics": {
    "blocked_edges": [],
    "activated_by_time": [],
    "stability_drivers": [],
    "volatility_drivers": []
  }
}
```

## 与中枢大脑对齐

中枢消费顺序：

```text
SDE dominant_path
-> OrchestratorEvidence 结构动态证据
-> MainlineArbitration 与规则/画像/问题意图合并
-> BrainState 输出统一主线
-> UI 和 LLM Context 使用同一份中枢结果
```

中枢不需要知道 SDE 内部算法细节，只消费：

- `dominant_path`
- `semantic_candidates`
- `chain_state`
- `volatility_score`
- `time_layer_status`
- `context_binding`

## 训练专题

### 合成验证

结构动态合成样本必须覆盖：

- 食伤生财 vs 食神制杀
- 食伤生财 vs 财滋杀
- 杀印相生 vs 官印相生
- 财生官 vs 财破印
- 比劫夺财 vs 官杀制比劫护财
- 印制食伤 vs 财制印护食
- 岁运引动但不改原局事实
- 冲导致稳定性下降但不等于能量消失

### 518K 回放

518K 不作为单盘真值，只用于：

- 路径分布稳定性
- 参数异常检测
- 冷门路径覆盖
- UI 展示压力测试
- 中枢消费一致性回归

### 自动调参

训练输出直接写 runtime pointer：

```text
dynamic_path_weight_policy
semantic_match_policy
volatility_threshold_policy
time_activation_policy
```

不做人工审核；只做机器回放和合成验证，失败则不写 pointer。当前已落地：

```text
structure_dynamics_synthetic
-> build_structure_dynamics_runtime_pointer
-> write_structure_dynamics_runtime_pointer_activate_candidate
-> training/structure_dynamics_policy_versions/active_pointer.json
-> dynamics.graph_engine runtime_policy consumption
```

结构动态 pointer 只调做功链权重、语义匹配阈值和承接/阻断相关参数，不改写四柱、日主、藏干、十神等命盘事实。

## UI 对齐

Admin 训练页：

- 新增“结构动态 v2”训练专题。
- 展示当前参数、最近训练结果、合成覆盖、518K 分片计划、pointer 状态。

测算页：

- 结构动态面板展示“核心做功链”，不是只显示一个套路名称。
- 命理师/管理员可展开图路径证据。
- 普通用户只看人话主线：当前结构如何动、在哪里承接、哪里受阻。

## 分阶段计划

### P4.1 设计与兼容骨架

- 新增 `dynamics/graph_engine.py`。
- 输出 `dominant_path`、`candidate_paths`、`semantic_candidates`。
- 旧 `dominant_chain` 仅作为迁移期字段；主读完成后移除对外输出。

### P4.2 图路径评分

- 实现节点强度、边权重、显化度、连续性、时间引动、阻断惩罚。
- 删除主算法对固定 `CHAIN_SEGMENT_PRIORITY` 的依赖。

### P4.3 知识库定性

- 从知识库 interaction / wealth / career / blind_lifa 中读取机制模板。
- 按 extracted path 匹配语义候选。

### P4.4 中枢接入

- `orchestrator.evidence` 消费 `dominant_path`。
- `brain_state` 显示核心做功链和状态。
- LLM context 只接收 compact path card。

### P4.5 训练与合成验证

- 新增结构动态合成样本。
- 新增 `structure_dynamics_training` 原子训练。
- 训练结果直接更新 runtime pointer。

### P4.6 UI 对齐

- Admin 训练页显示结构动态 v2 专题。
- 测算页结构动态面板显示做功链、承接、阻断、岁运引动。

## 当前推进状态

| 项目 | 状态 | 说明 |
| --- | --- | --- |
| 文档设计 | 已落地 | 本文档为 v2 重构合同 |
| runtime 兼容 | 已落地主读版 | 旧 `dominant_chain` 已移除对外输出；保留内部 `legacy_dynamic_chain` 排查字段，并输出 `dominant_chain_v2`、`primary_dynamic_chain`、`dominant_path`、`candidate_paths`、`semantic_candidates`、`sde_v2` |
| 图建模 | 已落地主读 | `dynamics.graph_engine` 使用 Weighted Dynamic Graph 抽取做功路径，`primary_dynamic_chain` 默认读取 v2 |
| 知识库定性 | 已落地完整知识单元版 | `knowledge.structure_mechanisms` 已接管结构动态命名和反例边界，并已晋升为 reviewed KnowledgeUnit，供知识库、画像、问题和回答治理消费 |
| 训练专题 | 已接自动生效链路 | 新增结构动态 v2 合成评估器、`structure_dynamics_synthetic` 原子训练任务和 `structure_dynamics_runtime_policy_pointer`；合成通过后可直接写 active pointer |
| runtime pointer 消费 | 已落地 | `dynamics.graph_engine` 已读取 active pointer，消费 `dynamic_path_weight_policy` 和 `semantic_match_policy`，报告输出 `sde_v2.runtime_policy` |
| 分布与切换报告 | 已落地 | 已输出 path distribution、知识覆盖、语料回放和主链切换报告，Admin 训练计划可见覆盖、反例、岁运阻断和切换状态 |
| UI 对齐 | 已落地 | 测算页结构动态面板已读取 `primary_dynamic_chain`；Admin 训练页已显示结构动态覆盖、知识覆盖、语料回放和切换报告 |

## 下一步主线

1. 继续扩大 518K 分片回放规模，发现冷门链路和异常过拟合。
2. 继续扩充 synthetic topic cases，特别是冷门结构和岁运阻断反例。
3. 保持 `primary_dynamic_chain` 主读，旧 `dominant_chain` 不再对外输出；内部仅保留 `legacy_dynamic_chain` 作为排查字段。

## P4.2 当前迁移判断

`dominant_chain_v2` 已通过 `primary_dynamic_chain` 成为 runtime 主读字段，旧 `dominant_chain` 已从 runtime 对外结构中移除；需要排查时使用内部 `legacy_dynamic_chain`。

原因：

- v2 已能识别“做功链”，语义命名已迁移到 `knowledge.structure_mechanisms` 桥接层。
- legacy/v2 synthetic switch report 无不可解释冲突。
- 中枢主线、证据编译、brain state 和测算页结构动态面板已经优先读取 `primary_dynamic_chain`。

切换条件：

```text
structure_dynamics_v2_synthetic_cases >= 20
dynamic_path_consistency >= 0.86
semantic_candidate_precision >= 0.84
legacy_v2_conflict_report 可解释
orchestrator consumes primary_dynamic_chain backed by dominant_chain_v2
UI shows primary_dynamic_chain without breaking existing chain card
```

已完成：

```text
orchestrator_evidence 增加 structure_dynamics_v2 证据
mainline_arbitration 优先读取 primary_dynamic_chain
brain_state.public_summary 增加 dynamic_work_path
brain_state.public_summary.dynamic_chain 优先读取 primary_dynamic_chain
workbench 结构动态面板显示核心做功链
validation.structure_dynamics_synthetic 增加 v2 合成验证
Admin 训练计划增加 structure_dynamics_synthetic 原子任务
knowledge.structure_mechanisms 接管 SDE v2 结构命名第一版
```

示例：

```text
辛酉 癸巳 乙卯 丁丑
dominant_chain_v2: 食神制杀
dynamic_work_path: 丁食神 -> 辛七杀 -> 癸偏印 -> 乙日主
action: 制约、相生、承接日主
```

## P4.4 合成验证第一版

新增：

```text
validation/structure_dynamics_synthetic.py
tests/test_v20_structure_dynamics_synthetic.py
```

当前样本覆盖已从 3 个扩到 27 个，覆盖食神制杀、伤官制杀、财生官/财滋杀、官印/杀印相生、印星承身、比劫承身、食伤生财、泛化输出制官杀、正官型输出制官杀、不同日主同构稳定性和岁运冲合阻断；反例机制已接入第一版，当前合成验证会要求食伤生财样本同时暴露 `财破印`、`比劫夺财`、`印制食伤` 候选，并要求官印和承身类样本暴露对应语义候选，岁运样本暴露 `clash/break/punishment` 等阻断诊断。下一步继续接 518K path distribution 的真实大样本回放。

| case | 目标 | 期望做功链 |
| --- | --- | --- |
| `food_controls_killing` | 食神制杀 | 丁食神 -> 辛七杀 -> 癸偏印 -> 乙日主 |
| `shangguan_controls_killing` | 伤官制杀 | 丙伤官 -> 辛七杀 -> 癸偏印 -> 乙日主 |
| `wealth_authority_resource` | 财生官/财滋杀 | 庚正财 -> 癸七杀 -> 乙偏印 -> 丁日主 |
| `*.xin_day/gui_day/ding_day/ji_day` | 食神制杀跨日主稳定性 | 食神 -> 七杀 -> 印星 -> 日主 |
| `*.ren_day/jia_day/bing_day/wu_day/geng_day` | 伤官制杀跨日主稳定性 | 伤官 -> 七杀 -> 印星 -> 日主 |
| `wealth_authority_resource.*` | 财官印/财滋杀跨日主稳定性 | 财星 -> 官杀 -> 印星 -> 日主 |
| `output_generate_wealth.*` | 食伤生财 + 反例候选 | 印比/食伤 -> 财星；同时要求语义候选暴露财破印、比劫夺财、印制食伤边界 |
| `output_controls_authority.*` | 泛化输出制官杀 | 伤官/食神 -> 官杀 -> 印星 -> 日主 |
| `time_clash_blocker.*` | 岁运冲合阻断 | 原主链保持，同时要求 `time_relation_blockers` 暴露冲、破、刑等阻断证据 |

结构动态分布报告：

```text
validation.structure_dynamics_path_distribution
-> label_distribution
-> counterexample_coverage
-> time_blocker_coverage
-> Admin training plan 结构动态覆盖卡
```

兼容主链切换报告：

```text
validation.structure_dynamics_legacy_v2_switch
-> compare dominant_chain vs dominant_chain_v2
-> explainable_count / unexplained_conflict_count
-> switch_policy.recommended_runtime_field = dominant_chain_v2
-> Admin training plan 结构动态切换报告
```

结构知识覆盖报告：

```text
validation.structure_dynamics_knowledge_coverage
-> observed labels from path distribution
-> knowledge.structure_mechanisms support
-> knowledge.directory_seeds support
-> rules.catalog support
-> Admin training plan 结构知识覆盖卡
```

结构语料回放报告：

```text
scripts/run_structure_dynamics_corpus_distribution.py
-> validation.structure_dynamics_corpus_distribution
-> 518K canonical_case_at 分片回放
-> label_distribution / semantic_distribution / chain_distribution
-> knowledge_coverage.unsupported_labels
-> learning.structure_dynamics_runtime_pointer 阻断 unsupported label
-> Admin training plan 结构语料回放卡
```

当前准入指标：

```text
dynamic_path_consistency: 1.0
semantic_candidate_precision: 1.0
structure_dynamics_knowledge_coverage.status: covered_current_scope
structure_dynamics_knowledge_coverage.unsupported_count: 0
structure_dynamics_corpus_distribution.unsupported_label_count: 0
```

Admin 训练入口：

```text
task_key: structure_dynamics_synthetic
script: scripts/run_structure_dynamics_synthetic.py --summary --progress
topic: structure_dynamics
brain_node: synthetic_validation
parameter_targets: dynamic_path_weight, semantic_match_weight
```

```text
task_key: structure_dynamics_corpus_distribution
script: scripts/run_structure_dynamics_corpus_distribution.py --run-id admin_structure_dynamics_corpus --limit 32 --write --summary --progress
topic: structure_dynamics
brain_node: corpus_replay_518k
parameter_targets: structure_stability_floor, semantic_match_weight
```
