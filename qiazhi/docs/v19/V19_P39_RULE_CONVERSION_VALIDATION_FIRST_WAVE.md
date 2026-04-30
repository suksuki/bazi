# V19 P39 Rule Conversion Validation First Wave

## 目标

P39 把当前知识库中可低风险自动转化的知识，批量转成“候选规则合同”，并立刻生成合成验证样本。

这一步解决两个问题：

- 不再只围绕少数高优先主题做小批量转化。
- 先让所有 R0/R1/R2 知识进入可验证候选层，后续再做智能门禁、深度机制样本和运行启用。

## 范围

- 总知识草案：436 条。
- 自动候选范围：R0/R1/R2，共 348 条。
- 阻断范围：R3/R4，共 88 条。
- 运行规则启用：0 条。
- 回答/领域预测输出：禁止。

## 转化模型

每条候选规则都补齐以下合同：

- `candidate_rule_id`
- `knowledge_id`
- `conversion_mode`
- `framework_model`
- `condition_axes_required`
- `expected_signal`
- `expected_question_keys`
- `forbidden_outputs`
- `answer_boundary`
- `engine_enabled = false`
- `activation_allowed = false`

## 转化模式

- `condition_model_candidate`：机制、格局、强弱、引动、冲合刑害破、财官印食伤等结构知识。
- `answer_expression_contract`：回答文本、安全降级和禁用表达。
- `governance_gate_contract`：Review UI、Rule DB、门禁和回滚边界。
- `metadata_boundary_rule`：地理、排盘、背景元数据边界。
- `archive_metadata_candidate`：辅助符号和归档型中性标签。
- `metadata_seed_rule_candidate`：普通元数据候选。

## 合成验证样本

每条候选规则生成 4 类样本：

- `positive_contract`：正例，必要条件轴满足时允许识别中性结构信号。
- `negative_missing_condition_axis`：反例，缺少必要条件轴时必须阻断。
- `distractor_time_layer`：时间层干扰，大运流年存在时不能改写本命结构或误触发。
- `distractor_hidden_layer`：藏干层干扰，只有背景藏干时不能误触发显性机制。

当前样本数：348 * 4 = 1392。

## 回归标准

- 候选规则必须全部 `engine_enabled = false`。
- `activation_updated_count = 0`。
- R3/R4 不得进入候选规则。
- 每条候选必须有条件轴、问题路由、禁用输出合同。
- 非正例样本不得产生正向信号。
- 禁词/预测词合同不得失败。

## 当前结果

- 候选规则：348。
- 阻断记录：88。
- 合成样本：1392。
- 样本失败：0。
- 误触发：0。
- 禁词失败：0。
- 状态：pass。

## 下一步

P40 可在 P39 的候选层上做两件事：

- 对 `condition_model_candidate` 里的重点机制生成 8-12 条深度正反样本。
- 建立智能审批/门禁，将通过深度样本的低风险规则送入 dry-run 激活队列。
