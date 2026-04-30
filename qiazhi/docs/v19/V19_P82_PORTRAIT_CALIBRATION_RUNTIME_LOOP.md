# V19 P82 画像互动校准运行闭环

## 目标

P82 把 P81 的画像本体和校准 hook 接成运行闭环：

```text
画像标签
→ 用户 / 命理师确认
→ feedback ledger
→ profile scoped calibration summary
→ 画像置信度微调
→ 推荐提问 / 回答证据包
```

这一步不是 UI 装饰。UI 只是入口，真正的闭环在后端画像编译器和回答证据链中完成。

## 运行边界

- 用户反馈只调整画像标签的 `confidence`、`posterior_confidence`、`compiled_score`。
- 命理师确认权重略高，但仍只作为画像校准和 audit 信号。
- 反馈必须按 `profile_id` 归属，不能污染其他命盘。
- 标签 `value` 不被反馈改写。
- 规则库、知识库和答案结论不被用户反馈直接修改。

## 新增链路

### 1. 反馈入口

Oracle 画像面板展示两类校准入口：

- 普通用户：确认这条画像是否符合自身经历。
- 命理师：确认标签是否满足证据门槛、同层作用路径和时间层边界。

提交后写入 `subject_type = portrait_calibration`。

### 2. 反馈汇总

`portrait_calibration_feedback_summary` 只汇总同一 `profile_id` 的反馈：

- `by_label`
- `by_family`
- `average_rating`
- `user_count`
- `analyst_count`

无 profile scope 时返回空摘要，避免测试或匿名调用误吃历史反馈。

### 3. 画像回流

`build_structure_portrait` 消费 `portrait_calibration_feedback`：

- 正向反馈轻微提高相关标签置信度；
- 负向反馈轻微降低相关标签置信度；
- 命理师确认会放大一点权重；
- 只影响排序、推荐问题和回答证据包。

### 4. 推荐与回答

校准后的画像继续进入：

- `guided_question_context.question_personalization_context.portrait_question_bias`
- `guided_question_answer.retrieved_facts.structure_portrait`
- `guided_answer.evidence_pack.portrait_evidence`

因此用户持续确认后，首屏推荐问题和回答依据会越来越贴近这张命盘的画像。

## 验收

- Oracle UI 有画像校准卡片。
- feedback ledger 能记录 `portrait_calibration`。
- 后端能按 profile 汇总画像反馈。
- 画像编译器能应用反馈并保持 `NO_RULE_MUTATION_FROM_CALIBRATION`。
- 回答证据包能看到校准后的画像。
- 合成测试仍保持 forbidden text 为 0。

## P83 修正

P82 的第一版校准入口仍偏“问答式”，并且画像值太多停留在候选态。P83 将校准入口改为画像选项：

- UI 直接列出画像选项；
- 用户和命理师选择画像项；
- feedback 记录 `option_id`；
- 后端按 `by_option` 汇总；
- 已确认选项生成 `confirmed_portrait_assertions`。

P82 保留为反馈回流边界，P83 成为画像确认的产品形态。
