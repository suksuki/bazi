# V20 中枢大脑智能架构

更新时间：2026-05-16

## 主理念

V20 的系统原则是：

```text
中枢大脑统一调配
高迭代训练
免人工审核
机器训练产物直接生效
UI 可见、可启动、可追踪、可回滚
```

中枢大脑不是状态面板，而是系统控制层。所有知识、规则、画像、问题、角色、合成数据、518K 训练和 runtime pointer 都必须进入中枢统一编排。

## 总架构

```text
Central Brain Orchestrator
  -> Knowledge Brain
  -> Rule Brain
  -> Portrait Brain
  -> Question Brain
  -> Role Brain
  -> Synthetic Lab
  -> Corpus Trainer 518K
  -> Parameter Optimizer
  -> Runtime Pointer Publisher
  -> Admin Training Console
```

中枢负责回答三个问题：

```text
当前缺什么？
应该训练什么？
训练成功后应该改哪个参数并让哪个 runtime pointer 生效？
```

## BrainGraph

V20 采用轻量 BrainGraph，不先引入重型工作流框架。

```text
knowledge_gap_pick
-> knowledge_atom_contract
-> rule_candidate_generation
-> portrait_mapping_generation
-> question_policy_generation
-> role_policy_generation
-> synthetic_case_binding
-> synthetic_validation
-> corpus_replay_518k
-> parameter_optimizer
-> runtime_pointer_publish
-> ui_observability
```

每个节点统一输出：

```text
status
inputs
outputs
metrics
parameter_targets
runtime_pointer_targets
blocking_machine_reason
runtime_mutation
```

## 模块控制协议

| 模块 | 中枢控制内容 | 训练结果 |
|---|---|---|
| 知识库 | 知识缺口、知识点合同、来源边界、反例 | knowledge runtime pointer |
| 八字规则 | 规则候选、权重、子条件、反例惩罚 | rule runtime pointer |
| 八字画像 | 画像轴、画像深度、主题投射 | portrait runtime pointer |
| 智能问题 | 问题来源、排序、DAG 追问链 | question runtime pointer |
| 角色视图 | 游客、用户、命理师、管理员可见深度 | role-view runtime pointer |
| 合成数据 | 边界验证、规则碰撞、反例覆盖 | synthetic training artifact |
| 518K 全量 | 分布校准、覆盖率、稳定性 replay | corpus runtime pointer |
| 回答治理 | 证据边界、角色表达、下一步问题 | answer governance parameter targets |

## 新增知识点合同

新增知识点不能只写文本，必须一次性绑定：

```text
knowledge_id
directory_node
source_refs
condition_atoms
rule_path
portrait_outputs
question_outputs
answer_guidance
counterexamples
synthetic_cases
runtime_boundary
parameter_targets
runtime_pointer_targets
```

## 训练闭环

统一训练链路：

```text
发现缺口
-> 中枢生成训练计划
-> 后台执行原子训练
-> synthetic 验证
-> 518K/分片 replay
-> 生成 parameter_targets
-> 写 active runtime pointer
-> UI 展示生效结果
```

不再存在“训练完成但没有调参目标”的训练任务。只读运维检查必须明确标记为 `ops_validation`，不能混入训练专题。

## 免审核直接生效

保留：

```text
机器 gate
训练日志
artifact
runtime pointer 版本
阻断原因
回滚入口
```

移除：

```text
人工审核 gate
手动批准生效
训练后等待确认
```

生效条件：

```text
task.status == succeeded
parameter_targets 有效
optimizer writer 存在
machine gate 通过
= 自动写 active pointer
```

## 训练分层

| 层级 | 名称 | 用途 | 数据 |
|---|---|---|---|
| L1 | 快速训练 | 改动后快速刷新候选参数 | 小 synthetic |
| L2 | 专题训练 | 知识、规则、画像、问题、角色专项优化 | synthetic + 小样本 replay |
| L3 | 夜间训练 | 全量稳定性和覆盖校准 | 518K 分片 |
| L4 | 周期训练 | 联合规则/画像/问题/角色评估 | 518K + sampled LLM eval |

## 成熟框架借鉴

不直接重构为外部框架，先借鉴成熟模式：

| 框架/范式 | 借鉴点 | V20 落地 |
|---|---|---|
| LangGraph | 状态图、节点、条件边 | `BrainGraph` |
| Ray | 分布式 replay 和训练 | 518K shard executor |
| MLflow | run、artifact、registry | runtime artifact + pointer registry |
| Feast | offline/online feature store | 八字特征、画像特征、角色特征分层 |
| Great Expectations | 数据质量验证 | synthetic / corpus validation |
| OpenTelemetry | trace、metric、log | 训练链路和 pointer 生效观测 |
| DSPy | 参数化 prompt/program 优化 | 回答治理和问题策略优化 |

## UI 叙事层

中枢大脑的结果必须在测算页以用户能理解的语言呈现，而不是只暴露工程状态。

已接入 `readingProgressPanel`：

```text
feature_state_model -> 八字特征完成度
portrait_projection -> 八字画像完成度
role_view_model -> 角色阅读完成度
questions + question_profile -> 智能问答完成度
role_question_narrative_prompt_framework -> 问题叙事与 LLM 回复提示词
```

不同角色使用不同叙事：

```text
guest: 先给你抓住重点
user: 本次阅读主线
practitioner: 复核链路已收束
admin/lab: 观测链路已对齐
```

角色化问题叙事与 LLM 提示词主文档：

```text
docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md
```

## Admin UI 对齐

Admin 训练页升级成“中枢训练控制台”：

```text
主线状态
训练专题
原子训练
当前后台任务
训练产物
runtime pointer 生效结果
回滚入口
中枢编排图
```

每个训练卡片必须展示：

```text
会优化什么参数
会影响哪个模块
会写哪个 runtime pointer
是否后台运行
预计耗时
最近一次是否生效
阻断原因
```

## 当前完成度

```text
中枢控制协议：已定义
知识规则联合编排：已接入
训练任务后台运行：已接入
自动调参直接生效：已接入多 pointer writer
Admin UI 控制台：已按 BrainGraph 展示中枢任务编排
518K 分片训练：已有 skeleton，已接入 BrainGraph

综合：99%+
```

## 下一步实施顺序

```text
Step 1: 增加 central_brain_architecture 机器状态。已完成。
Step 2: Admin UI 读取中枢架构状态并展示训练专题。已完成。
Step 3: 训练任务 registry 按 BrainGraph 分组。已完成。
Step 4: knowledge_rule_orchestrator 输出接入 mainline_status。已完成。
Step 5: nightly 518K executor 接入 BrainGraph。已完成 skeleton 级接入。
Step 6: 所有训练任务强制 parameter_targets + pointer targets。已完成第一版。
Step 7: Admin 训练计划输出 candidate_quality_signal，把合成覆盖和 518K 回放 artifact 合成候选质量信号。已完成。
Step 8: candidate_quality_signal 输出 quality_scores 和 candidate_promotion_score，形成合成验证 + 518K 回放的候选推进评分。已完成第一版。
Step 9: 扩容 518K 分片回放，把更多候选参数推到可直接生效状态。
```
