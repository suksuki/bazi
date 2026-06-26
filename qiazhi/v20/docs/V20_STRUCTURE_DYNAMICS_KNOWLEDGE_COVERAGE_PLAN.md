# V20 结构动态知识覆盖计划

## 目标

结构动态 v2 的核心输出不是固定套路名，而是当前八字、大运、流年上的做功主线路。每一条主线路定性都必须能回到三层依据：

```text
动态图路径 -> 知识机制单元 -> 八字知识目录 / 规则目录
```

如果 SDE v2 计算出一个结构标签，但知识机制、目录种子和规则目录都不能解释它，这个标签不能进入主线展示，也不能作为训练调参依据。

## 当前结论

当前合成分布范围内，已观察到的结构动态标签都有知识支撑：

```text
食神制杀
伤官制杀
输出制官杀
食伤生财
财生官/财滋杀
官印/杀印相生
印制食伤
比劫夺财
财破印
```

支撑来源：

```text
knowledge.structure_mechanisms
knowledge.directory_seeds
rules.catalog
validation.structure_dynamics_path_distribution
validation.structure_dynamics_knowledge_coverage
```

这只能证明“当前合成样本和当前观察分布已覆盖”，不能证明 518K 全量八字里的所有冷门路径都已经覆盖。

## 新增审计链路

```text
run_structure_dynamics_synthetic_suite
-> build_structure_dynamics_path_distribution
-> build_structure_dynamics_knowledge_coverage_report
-> ops.training_tasks.training_plan
-> Admin 训练页：结构知识覆盖
```

## 新增 518K 分片回放链路

```text
scripts/run_structure_dynamics_corpus_distribution.py
-> validation.structure_dynamics_corpus_distribution
-> training/structure_dynamics_corpus_distribution/latest.json
-> learning.structure_dynamics_runtime_pointer
-> ops.training_tasks.training_plan
-> Admin 训练页：结构语料回放
```

这条链路按分片回放 518K 八字空间，不在打开 Admin 页面时重算。训练页只读最新 artifact；点击“结构动态语料回放”才会后台运行脚本。

审计字段：

```text
observed_label_count
mechanism_unit_count
covered_count
unsupported_count
coverage_rows[]
unsupported_labels[]
partial_rule_catalog_labels[]
next_gaps[]
```

## 主线并入

P4 结构动态主线增加一个固定 gate：

```text
structure_dynamics_knowledge_coverage.status == covered_current_scope
unsupported_count == 0
structure_dynamics_corpus_distribution.unsupported_label_count == 0
```

结构动态 runtime pointer 已消费语料分布结果：如果语料回放发现 `unsupported_labels`，结构动态候选策略会被 `structure_dynamics_corpus_distribution_has_unsupported_labels` 阻断；如果没有缺口，候选策略会记录 corpus 分片状态和样本数。

如果未来 518K 回放发现新标签：

```text
1. 先进入 unsupported_labels
2. 补 knowledge.structure_mechanisms 机制单元
3. 补 directory seed / KnowledgeUnit / rule catalog
4. 补合成反例和时间层样本
5. 再允许进入 Admin 和测算页主线展示
```

## 后续任务

```text
P4.5: 518K structure path distribution 回放
P4.6: 将 knowledge.structure_mechanisms 晋升为完整 KnowledgeUnit
P4.7: 冷门路径补充合成样本和反例
P4.8: dominant_chain_v2 已通过 primary_dynamic_chain 切为线上主读
```

## UI 对齐

Admin 训练页新增“结构知识覆盖”卡片，展示：

```text
观察标签
机制单元
已覆盖
缺口
每个标签的支撑来源数量
```

这个卡片不是审计人工审核，而是为了让训练和中枢知道：结构动态不是套模板，而是每个做功链都能回到知识理论。
