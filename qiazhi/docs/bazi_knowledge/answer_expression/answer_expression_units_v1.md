# 回答表达知识单元 v1

状态：命理师审阅版目录

范围：只管理面向用户的回答表达方式，不新增命理事实，不改变规则判断。

## 治理边界

- 回答应使用普通中文解释结构事实。
- 回答应避免内部字段，例如 `rule_id`、`signal_id`、`source_signal_id`。
- 回答不应输出“必然”“一定”“发财”“破财”等断语。
- 对当前系统不支持的问题，应明确降级到可支持的结构问题。
- 时间背景、墓库、冲合刑害、财星等内容都必须表达为结构信息，而不是预测结果。

## 中文目录

```text
answer.structure_plain_language.v1
answer.unsupported_question_boundary.v1
p10.answer_expression.no_prediction_banner_cleanup
p10.answer_expression.remove_internal_jargon
p10.answer_expression.user_question_intent_first
p21.question.structural_recommendation_diversity
```

## 审阅重点

命理师 review 时重点看三件事：

- 是否说清楚结构事实。
- 是否误把结构事实说成吉凶、预测或结果。
- 是否有模板废话、内部术语或不自然表达。

