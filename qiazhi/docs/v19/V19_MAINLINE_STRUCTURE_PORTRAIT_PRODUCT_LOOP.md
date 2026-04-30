# V19 结构画像产品闭环

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

## 边界

结构画像是“路径选择和候选判断层”，不是命断层。它可以帮助系统更快选择用户该问什么、回答该引用什么证据，但不能替代规则图、知识库和合成回归。
