# V19 框架适配性评估

## 结论

当前框架可以继续承载知识库、规则库、自我学习和合成数据测试，不建议现在整体替换。

更好的路线是：

```text
保留现有核心框架
补条件模型层
补批量合成数据生成器
补可恢复的评估编排层
补可审计的智能审批层
```

也就是说，不是换掉 V19，而是把 V19 从“规则和测试脚本集合”升级成“规则进化工作流”。

## 当前框架已经适配的部分

V19 已经具备这些关键能力：

- 知识库分层：source archive、knowledge drafts、content packs、manifest。
- 规则库：Rule DB 记录、risk_level、allowed_usage、forbidden_usage、engine_enabled。
- 智能门禁：P27 / P28I 已经能做低风险候选筛选、启用和回滚边界。
- 合成数据：P10-P11、P28G-P28J 已经能用合成盘矩阵验证规则覆盖和误触发。
- 回答审计：已有内部术语、预测词、模板化表达检查。
- 运行态隔离：知识/规则可以进入候选，但不必立刻改变答案结果。

这些正好符合命理系统需要的“受控进化”：知识先结构化，规则再门禁，合成数据最后验收。

## 当前不足

不足不是“没有高级框架”，而是缺少三层工程化能力：

1. 条件模型层还不够系统
   - 机制类规则需要 source_layer、capacity_strength、same_layer_action、rescue_path、time_layer。
   - P28J 已开始补这一层。

2. 合成数据生成还不够自动
   - 当前合成盘多是人工列矩阵。
   - 下一步应按条件模型自动生成正反样本。

3. 评估编排还不够可恢复
   - 现在 pytest 可以回归，但长流程缺少 durable run、checkpoint、run ledger。
   - 以后批量知识专题会越来越多，需要任务可恢复、可追踪。

## 外部框架判断

我查了三个成熟方向：

- OpenAI Agents SDK guardrails：适合把输入、输出和工具调用的门禁作为 agent 的一部分，支持触发 tripwire 后停止执行。参考：https://openai.github.io/openai-agents-python/guardrails/
- OpenAI Evals：适合把合成数据和回答质量变成可重复评估，官方强调 eval-driven development、自动评分和人类反馈校准。参考：https://developers.openai.com/api/docs/guides/evals 与 https://developers.openai.com/api/docs/guides/evaluation-best-practices
- LangGraph durable execution：适合长流程、人机协作和可恢复执行，它强调 checkpoint、thread id、可恢复 workflow。参考：https://docs.langchain.com/oss/python/langgraph/durable-execution

我的建议：

- 现在不要引入 LangGraph 重写主流程，成本偏高。
- 可以先引入“兼容它们的抽象”：run_id、step ledger、gate result、eval dataset、approval decision。
- 等 P28-P31 的知识专题流程稳定后，再考虑把长流程编排迁到 LangGraph 或类似引擎。
- OpenAI Evals / eval dataset 思路可以更早吸收，但先落成本地 JSONL/pytest 格式，避免引入平台依赖。
- Agents SDK guardrails 的思想可以直接复用：输入、规则启用、答案输出都要有 tripwire。

## 推荐升级路线

短期：

- 继续使用现有 Python 模块 + pytest + manifest。
- 新增 condition model registry。
- 新增 synthetic pair generator。
- 新增 rule activation gate report。

中期：

- 把每次知识专题 review 变成 run ledger。
- 将合成盘矩阵导出为 eval dataset。
- 增加自动评分器：命中、漏触发、误触发、禁词、回答聚焦度。
- 增加智能审批：低风险规则自动 dry-run，高风险规则自动阻断。

长期：

- 如果专题量和规则量继续扩大，再引入 durable workflow。
- 如果需要跨 agent 协作，再引入 Agents SDK 风格的 guardrail + tracing。
- 如果需要模型级调参，再把本地 synthetic eval 导出到 OpenAI Evals 或同类评估平台。

## 关键判断

当前 V19 的方向是对的：知识库和规则库是核心，自学习本质上应该是“失败归因 → draft/condition proposal → 合成验证 → 门禁启用”，而不是黑盒自动改模型。

所以这一阶段最该投入的不是换框架，而是把条件模型、合成数据和智能审批做扎实。
