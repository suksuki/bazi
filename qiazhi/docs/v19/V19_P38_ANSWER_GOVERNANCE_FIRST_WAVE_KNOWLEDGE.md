# V19 P38 回答表达与治理第一批新知识

## 定位

P38 补 L11 回答表达与治理知识。它不新增命理事实，只规定知识进入回答、Review UI 和 Rule DB 门禁时的安全边界。

## 新增专题

```text
docs/bazi_knowledge/answer_expression/answer_governance_first_wave_topic_v1.md
```

## 新增知识包

```text
docs/bazi_knowledge/packs/p38_answer_governance_first_wave_knowledge_draft_seeds_v1.json
```

## 覆盖对象

| 组 | 对象 |
|---|---|
| 回答表达 | 结构说人话、不支持问题降级、内部术语过滤、预测断语过滤、证据边界、时间层表达、领域安全降级、反馈表达优化 |
| Review UI | 失败归因展示、draft 提案展示、合成评估报告 |
| Rule DB 门禁 | 智能门禁报告、回滚谱系、自动审批边界 |

每个对象 2 条知识草案，合计 28 条。

## 安全边界

- 回答不输出内部字段、预测断语或模板废话。
- Review UI 只展示归因、证据、提案和报告，不自动批准。
- Rule DB 变更必须有门禁报告、合成回归、禁词检查和回滚路径。
