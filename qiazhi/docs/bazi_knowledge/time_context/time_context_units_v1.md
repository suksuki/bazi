# 时间背景知识单元 v1

状态：命理师审阅版目录

范围：大运、流年等时间背景作为结构层级。时间背景可以说明触发与层级，但不得改写本命结构。

## 治理边界

- 本命结构始终是基础层。
- 大运、流年是时间层，可以与本命天干地支形成关系。
- 时间关系必须标明发生层级。
- 时间触发不能在没有领域规则审核的情况下变成事件预测。

## 规范特征类型

- `luck_cycle_layer`
- `flow_year_layer`
- `time_relation_layer`
- `time_trigger`
- `natal_not_rewritten`
- `layer_priority`

## 中文目录

```text
p27.time.luck_cycle_background_layer
p27.time.flow_year_trigger_layer
p27.time.relation_layer_attribution
p27.time.no_natal_rewrite_boundary
p27.time.luck_flow_priority_boundary
p27.time.support_disturbance_tagging
p31b.time.small_luck_archive_boundary
p31b.time.flow_month_archive_boundary
```

## 审阅边界

时间背景可以回答：

- 关系发生在本命、大运、流年，还是跨层互动。
- 当前观察的是哪一组天干或地支关系。
- 它是背景、触发提示，还是单纯的层级标签。

时间背景不能回答：

- 某一年会发生什么。
- 某一年好坏。
- 本命结构是否被改变。

## P31B 补齐边界

小运、流月先作为后置时间层归档，不参与当前回答生成。它们后续如进入系统，必须遵守两条边界：

- 只能说明时间层级和触发候选，不输出具体事件或结果。
- 不能越过大运、流年和本命结构的层级优先级。
