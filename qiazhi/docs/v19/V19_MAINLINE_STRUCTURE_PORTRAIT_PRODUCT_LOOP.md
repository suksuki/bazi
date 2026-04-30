# V19 结构画像产品闭环

P77-P80 将画像层继续推进到 UI QA、回答正文、影子调优和常用命理入口。

## 目标

把结构画像层从“内部特征”推进到可验证的产品闭环：

- UI 能看到结构标签和候选判断；
- 回答证据包能携带画像来源；
- 合成盘能验证画像不会把问题推荐收敛成同一套；
- 静默学习系统能收集画像路由信号，但不自动改规则。

## P73: Portrait UI

Oracle 首屏新增 `portraitPanel`，展示：

- 结构画像标题；
- 候选标签数量；
- 强弱、用神、十神、财富、地支、时间、格局等标签；
- 1-3 条候选判断。

UI 只展示“候选标签”和“结构提示”，不展示喜忌硬结论，也不输出概率断言。

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
