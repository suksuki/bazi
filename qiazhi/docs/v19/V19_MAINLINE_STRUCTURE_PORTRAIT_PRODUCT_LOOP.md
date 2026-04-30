# V19 结构画像产品闭环

P77-P81 将画像层继续推进到 UI QA、回答正文、影子调优、常用命理入口和标签本体编译器。

## 目标

把结构画像层从“内部特征”推进到可验证的产品闭环：

- UI 能看到结构标签和候选判断；
- 回答证据包能携带画像来源；
- 合成盘能验证画像不会把问题推荐收敛成同一套；
- 静默学习系统能收集画像路由信号，但不自动改规则。
- 标签由本体编译器生成，并绑定规则图知识路径、问题钩子、回答边界和互动校准 hooks。

## P73: Portrait UI

Oracle 首屏新增 `portraitPanel`，展示：

- 结构画像标题；
- 重点标签数量和全部标签数量；
- 强弱、用神、财富、地支、时间、格局等重点标签，同一家族只展示最有解释价值的一条；
- 1-3 条候选判断。

UI 只展示“重点标签”和“结构提示”；背景、弱证据、重复家族标签保留给路由和审计，不直接铺到首屏。界面不展示喜忌硬结论，也不输出概率断言。

## P81: Portrait Ontology And Calibration

画像标签主链改为：

```text
facts / vectors
→ label ontology
→ Rule Graph knowledge support
→ compiled score
→ posterior confidence
→ question hooks / answer boundary / calibration hooks
```

旧粗标签生成链路不再作为主逻辑保留；底层 facts 和 vectors 只作为本体编译器输入。

每个标签都必须带：

- `required_evidence`
- `source_layers`
- `question_hooks`
- `answer_boundary`
- `knowledge_evidence_ids`
- `user_calibration_hooks`
- `analyst_confirmation_hooks`

用户反馈只校准画像置信度和问题路径；命理师确认进入 audit，不自动改规则库。

## P82: Portrait Calibration Runtime Loop

P82 将互动校准落到完整运行链路：

- Oracle 画像面板渲染用户校准卡片和命理师确认入口；
- feedback ledger 记录 `subject_type = portrait_calibration`；
- 后端按 `profile_id` 汇总画像反馈，避免不同命盘互相污染；
- `build_structure_portrait` 消费反馈，只微调标签置信度、后验置信度和编译分；
- 推荐问题和回答证据包拿到的是校准后的画像；
- 规则库、知识库、标签含义和答案结论都不被反馈直接改写。

## P83: Portrait Option Model

P83 修正 P82 的产品形态：校准不再是“系统继续问用户一个问题”，而是由系统列出画像选项，让用户或命理师直接选择。

新增：

- `structure_portrait.portrait_options`
- `structure_portrait.labels[].selection_options`
- `structure_portrait.labels[].selected_option`
- `structure_portrait.confirmed_portrait_assertions`
- feedback summary 的 `by_option`

用户选择后，画像项可以从 `system_suggested` 进入 `user_confirmed`；命理师选择后进入 `analyst_confirmed`。确认画像只影响个性化画像、推荐问题和回答证据路径，不改命盘事实，不改规则库。

## P84: Bazi Feature Spine

P84 将画像、规则、知识、推荐问题和回答证据包接到同一条命理特征主干：

```text
规则图 / 知识路径
→ bazi_feature_layer.features
→ portrait_projection
→ feature_question_bias
→ guided answer feature_evidence
```

从 P84 起，画像不再作为主推理源头，而是命理特征的可视化投影和校准入口。旧的画像问答 hook 和 `structure_portrait.question_bias` 不再进入主链路；推荐问题只读取 `bazi_feature_layer.question_bias`，回答优先围绕命理特征说明作用路径和证据门槛。

## P74: Portrait Evidence Pack

`guided_evidence_pack` 增加 `portrait_evidence`：

- `label_ids`
- `judgement_ids`
- `dominant_label_ids`
- `recommended_question_keys`
- compact `vectors`

同时将画像标签纳入 `evidence_bindings`，类型为 `structure_portrait_label`。这些绑定只用于解释回答依据，不能激活规则，也不能改写答案。

## P75: Portrait Synthetic Matrix

新增 `structure_portrait_matrix`，固定使用 12 个 P11 合成盘验证：

- 画像向量至少形成 5 种签名；
- 首屏问题至少形成 6 种签名；
- 标签覆盖 strength / useful_god / ten_god / wealth / branch / time / pattern；
- 禁止输出硬断词；
- `runtime_mutation = false`。

## P76: Silent Learning Hook

P62 silent training ledger 新增 `portrait_routing_signal`，P63 silent eval queue 新增 `portrait_route_weight_shadow_review`。

允许进入静默队列的内容：

- 画像权重复核；
- 合成样本优先级复核；
- 问题推荐排序影子评估。

禁止：

- 用户反馈直接改规则；
- 画像直接生成断言；
- 静默训练自动启用规则；
- 输出硬用神忌神结论。

## P77: Portrait UI QA

目标：

- Oracle 首屏能稳定显示画像标签；
- 多语言切换后画像标签仍能读；
- 回答依据摘要显示 portrait 证据数量；
- 常用命理入口和画像标签不遮挡、不挤压主问题区。

## P78: Portrait Evidence In Answer

回答正文增加“结构画像参考”：

- 显示画像标签；
- 显示候选判断；
- 显示证据门槛；
- 明确画像只帮助证据排序和问题路径选择。

强弱、用神、忌神、格局等问题继续保持候选表达，不输出“喜木火/忌金水”类硬结论。

## P79: Portrait Shadow Tuning

新增 20 个 P11 合成盘影子调优报告：

- 统计画像向量签名；
- 统计首屏问题签名；
- 统计问题 bucket 覆盖；
- 生成 `shadow_review_only` 权重建议。

这些建议只进入静默队列，不直接改生产排序权重。

## P80: Common Bazi Entry Completion

常用命理入口继续保留在推荐系统：

- 日主强弱；
- 用神候选；
- 忌神边界；
- 喜用五行边界；
- 格局结构；
- 十神重点；
- 大运流年引动。

这些入口由 Rule Graph、结构画像和证据包共同排序，不能退回固定模板推荐。

## 边界

结构画像是“路径选择和候选判断层”，不是命断层。它可以帮助系统更快选择用户该问什么、回答该引用什么证据，但不能替代规则图、知识库和合成回归。
