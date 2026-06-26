# V20 第二阶段质量扩容执行计划

更新时间：2026-05-20

## 阶段定位

第一阶段主线已经收口：中枢大脑、结构动态、知识桥、画像、智能问题、训练直生效和 UI 角色分层都已进入可运行闭环。

第二阶段不再补主链缺口，而是持续提高覆盖面、稳定性和表达质量：

```text
当前八字 + 大运流年上下文
-> 中枢大脑统一调度
-> 知识库 / 规则 / 结构动态 / 画像 / 智能问题
-> synthetic 验证
-> 518K 分片回放
-> 真实交互反馈
-> runtime pointer 直接生效
```

## 执行原则

- 所有训练结果优先通过 runtime pointer 直接生效，不走人工审核 gate。
- 518K 只做离线覆盖、分布和稳定性校准，不作为单盘画像真值。
- synthetic cases 优先补边界盘、反例盘、相邻结构误判盘。
- UI 必须同步展示最新框架：用户侧自然语言，Admin/命理师侧可见证据、策略和 pointer。
- 每轮扩容必须可回放、可度量、可回滚。

## 主线任务组

| 优先级 | 任务组 | 目标 | 主要产物 | 验收标准 |
| --- | --- | --- | --- | --- |
| P1 | 结构动态 518K 分片扩容 | 从 7168 继续扩大真实分片覆盖，发现冷门结构标签和知识缺口 | `structure_dynamics_corpus_distribution` artifact + active structure pointer | failure=0，unsupported_label=0，active pointer 已更新 |
| P1 | 知识库机制覆盖 | 将 518K 新观察标签回填到机制知识单元、KnowledgeUnit、规则目录 | 知识覆盖报告 + 知识机制单元 | observed labels 均可回到知识库 |
| P2 | synthetic case 扩容 | 扩展结构动态、用神、关系、健康、智能问题边界样本 | synthetic validation reports | pass_rate=1.0，反例不误升主结构 |
| P2 | 智能问题真实反馈 | 持续积累点击、跳过、追问、评价样本 | `role_question_click_training` + `question_review_training` | atom boost/penalty 样本数增长并直接进入 pointer |
| P3 | 角色叙事质量 | 优化游客、用户、命理师、Admin 的问题和回答语气 | role narrative / answer governance reports | 用户侧少工程语言，命理师侧证据充分 |
| P3 | Admin 训练台可观测 | 展示扩容进度、分片位置、pointer 版本和质量趋势 | admin training UI | 能看到下一步推荐训练任务和当前生效策略 |

## 当前执行序列

### E1: 结构动态 518K 分片扩容

上一段稳定分片：

```text
run_id: codex_structure_dynamics_7168_window
start: 6144
limit: 1024
failure_count: 0
unsupported_label_count: 0
active pointer: v20.structure_dynamics_policy.candidate.90dddd0fbe77
```

本轮执行：

```text
run_id: codex_structure_dynamics_8192_window
start: 7168
limit: 1024
```

执行后动作：

1. 写入 corpus distribution artifact。
2. 检查 failure 和 unsupported label。
3. 若机器 gate 通过，激活 structure dynamics runtime pointer。
4. 更新中枢进度文档。

执行结果：

```text
status: completed
run_id: codex_structure_dynamics_8192_window
start: 7168
limit: 1024
failure_count: 0
unsupported_label_count: 0
observed labels: 8 主标签 / 11 语义候选标签
knowledge_coverage.status: covered_current_scope
previous active pointer: v20.structure_dynamics_policy.candidate.90dddd0fbe77
new active pointer: v20.structure_dynamics_policy.candidate.5f6beabbf3b2
```

主要分布：

```text
输出制官杀: 409
食神制杀: 231
伤官制杀: 203
财生官/财滋杀: 120
食伤生财: 41
比劫承身: 10
印星承身: 8
官印/杀印相生: 2
```

结论：E1 已完成。本段没有发现知识库不支持的新结构标签，结构动态策略已直接生效。

### E2: 知识缺口回填

如果 E1 出现 unsupported label：

1. 补 `knowledge.structure_mechanisms`。
2. 补完整 KnowledgeUnit。
3. 补 synthetic 正例/反例。
4. 重跑知识覆盖和结构动态 synthetic。

如果 E1 无 unsupported label：

1. 记录覆盖扩大。
2. 继续下一段 1024 shard。

下一段建议：

```text
run_id: codex_structure_dynamics_9216_window
start: 8192
limit: 1024
```

执行结果：

```text
status: completed
run_id: codex_structure_dynamics_9216_window
start: 8192
limit: 1024
failure_count: 0
unsupported_label_count: 0
observed labels: 5 主标签 / 10 语义候选标签
knowledge_coverage.status: covered_current_scope
previous active pointer: v20.structure_dynamics_policy.candidate.5f6beabbf3b2
new active pointer: v20.structure_dynamics_policy.candidate.189b9461a5e6
```

主要分布：

```text
输出制官杀: 413
食神制杀: 256
伤官制杀: 226
财生官/财滋杀: 88
食伤生财: 41
```

结论：9216 window 已完成。本段没有发现知识库不支持的新结构标签，结构动态策略已直接生效。

下一段建议：

```text
run_id: codex_structure_dynamics_10240_window
start: 9216
limit: 1024
```

### E3: 智能问题反馈样本观察

每轮训练后读取：

```text
role_question_click_training.next_question_feedback_policy
question_review_training.recommendations
question_runtime_pointer.policy_payload.next_question_plan_policy
```

目标是让真实交互逐步替代纯 synthetic boost。

## 完成口径

第二阶段不是一次性“完成”，而是按分片和专题滚动推进。

本轮完成标准：

```text
E1 shard completed
failure_count = 0
unsupported_label_count = 0
structure pointer candidate_active
docs updated
relevant tests pass
```
