# V19 P84 命理特征主干

## 目标

P84 解决“知识库、规则库、画像、问题推荐、回答系统割裂”的问题。系统新增一层 `Bazi Feature Layer`，作为各模块之间的共同语言。

```text
八字事实
→ 规则图 / 知识库路径
→ 命理特征
→ 画像投影
→ 推荐问题
→ 回答证据包
→ 用户 / 命理师反馈
```

## 定位

命理特征不是画像，也不是断语。

- 知识库提供概念、边界和解释材料；
- 规则图识别结构条件和作用路径；
- 命理特征整理为可解释、可评分、可回答的中间对象；
- 画像是命理特征的用户可见投影；
- 推荐问题优先由高置信度、可回答的命理特征驱动；
- 回答围绕命理特征解释作用路径和证据门槛。

## Feature Schema

每个特征包含：

- `feature_id`
- `title`
- `domain`
- `source_layer`
- `evidence`
- `evidence_refs`
- `rule_paths`
- `knowledge_units`
- `confidence`
- `priority_score`
- `feature_state`
- `answer_readiness`
- `question_hooks`
- `answer_boundary`
- `portrait_projection`

## 当前第一批特征

- `feature.wealth.visible_but_constrained`
- `feature.wealth.output_to_wealth_path`
- `feature.wealth.visible_material`
- `feature.strength.borderline_capacity`
- `feature.strength.capacity_needs_support`
- `feature.useful_god.evidence_gate_not_ready`
- `feature.ten_god.mechanism_path_pending`
- `feature.branch.time_triggered_relation`
- `feature.pattern.index_candidate`

## 清理旧链路

P82 的问答式画像 hook 和 `structure_portrait.question_bias` 不再作为主链路驱动推荐和回答。画像层仍可保留旧字段用于兼容和审计，但运行时主链不得读取它来调整问题顺序、回答段落或 LLM prompt。

当前主链路改为：

```text
bazi_feature_layer.question_bias
→ guided_question_context.question_personalization_context
→ guided answer evidence pack
→ LLM prompt context
```

画像选项仍存在，但它的角色变为：

```text
画像选项 = 命理特征的可视化投影和校准入口
```

主链责任边界：

- `bazi_feature_layer.question_bias` 是推荐问题排序的唯一画像/特征侧 bias；
- `guided_question_context.question_personalization_context` 只返回 `feature_question_bias`，不再返回 `portrait_question_bias`；
- `guided_answer.retrieved_facts.structure_portrait` 只保留画像投影、选项、校准状态和标签证据；
- `guided_answer.evidence_pack.portrait_evidence` 不再回捞 `structure_portrait.question_bias`；
- LLM prompt 优先使用 `bazi_feature_layer` 与 `feature_evidence` 解释命理特征、证据门槛和回答边界。

## 边界

- 命理特征可以驱动推荐问题；
- 命理特征可以进入回答证据包；
- 命理特征可以被用户/命理师反馈调置信度；
- 命理特征不能直接改命盘事实；
- 命理特征不能直接改规则库；
- 命理特征不能输出硬断吉凶、应期、喜忌或财富结果。

## 验收

- `/api/agent/structure` 返回 `bazi_feature_layer`；
- `/api/agent/turn` 回答证据包包含 `feature_evidence`；
- 推荐问题 personalization 原因出现 `bazi_feature_spine`；
- 画像面板优先显示命理特征，再显示画像投影；
- 回答文本出现命理特征主线，并保持 forbidden text 为 0；
- 旧的画像问答 hook 不再进入主回答 compact context；
- 在运行时代码中，`structure_portrait.question_bias` 只允许保留在 `structure_portrait.py` 的兼容生成层；manifest 可保留替换声明，但主链读取路径不得再使用它。
