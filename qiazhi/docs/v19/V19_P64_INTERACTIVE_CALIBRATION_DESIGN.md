# V19 P64 Interactive Calibration Design

P64 定义“交互式命盘校准层”。它让系统不仅回答用户，也能在合适时反向询问用户，用用户提供的人生事件作为观测证据，回溯每个人的隐藏校准参数。

这不是自动改规则，也不是黑盒学习。P64 的边界是：

```text
八字结构 = 结构先验
用户事件 = 观测证据
隐藏因子 = 当前用户的个体校准参数
校准结果 = 只影响问题排序、路径排序和后续询问优先级
```

## 为什么现在入场

同一张八字不等于同一条人生轨迹。现实中的家庭资源、行动效率、机会可达性、环境变化、风险承受和关键事件，会让同样结构出现不同兑现程度。

现有系统已经具备：

- Rule Graph Orchestrator：结构路径选择。
- P59/P62：静默学习信号和训练账本。
- P63：静默评估队列。
- Guardrails：用户反馈不直接改规则。

所以 P64 不替换现有框架，而是在 Rule Graph 后面增加一层：

```text
Rule Graph structural prior
→ Calibration Inquiry Orchestrator
→ User Event Evidence Ledger
→ Latent Factor Estimator
→ Personalized Route Re-ranker
→ Answer / Question Recommendation
```

## 隐藏因子目录

P64 第一版定义 12 个可解释因子：

- `baseline_amplifier`：基础兑现放大因子。
- `action_efficiency`：行动效率。
- `resource_support`：资源支持。
- `opportunity_access`：机会可达性。
- `risk_tolerance`：风险承受。
- `timing_sensitivity`：时间引动敏感度。
- `wealth_amplifier`：财富兑现放大因子。
- `career_amplifier`：事业兑现放大因子。
- `relationship_sensitivity`：关系事件敏感度。
- `relocation_mobility`：迁移流动性。
- `stress_recovery_capacity`：压力恢复能力。
- `health_safety_modifier`：健康安全边界修正。

这些因子只允许用于：

- 当前用户的路径重排。
- 反向问题优先级。
- 内部 posterior calibration。
- 合成用户校准评估。

禁止用于：

- 修改核心命理规则真值。
- 自动启用生产规则。
- 给用户展示“幸运分”“概率分”。
- 健康、寿命、疾病推断。

## 用户事件证据账本

事件账本第一版采用结构化记录：

```json
{
  "event_domain": "wealth",
  "event_type": "income_change",
  "time_range": "2019-2020",
  "date_precision": "year_range",
  "valence": "positive",
  "intensity": 4,
  "confidence": 0.8,
  "allowed_use": "personal_calibration_only"
}
```

允许领域：

- 财富
- 事业
- 关系
- 健康
- 迁移
- 家庭
- 学习
- 压力

所有事件默认只进入 `personal_calibration_only`，不进入知识库规则真值。

## 反向问题原则

系统可以问用户，但问题必须中性。

允许：

- “某些年份里，你的收入或资源状态有没有明显变化？”
- “你的职业角色、岗位责任或工作平台，是否有过明显转换的阶段？”
- “遇到压力较大的阶段时，你通常恢复得较快、较慢，还是波动较大？”

禁止：

- 暗示某年一定发财、结婚、离婚、出事。
- 暗示疾病、寿命、治疗、诊断。
- 用确定性应期语言诱导用户。

## 模型选型

当前启用：

- Rule Graph structural prior。
- Deterministic factor scoring。
- Bayesian update for internal posterior。
- Active learning question selection。

暂不启用：

- GNN core inference。
- RL core rule update。
- User feedback to rule truth。
- Black-box domain prediction。

后续可以预留：

- Factor Graph：事件账本足够后接入。
- Contextual Bandit：只用于下一个问题排序。
- GNN：只用于路径 embedding / rerank。
- RL：只用于对话策略，不改规则真值。

## 当前入口

- `v19.synthetic_validation.calibration_design.build_p64_interactive_calibration_design`
- `v19.synthetic_validation.calibration_design.run_p64_interactive_calibration_design_regression`
- `GET /api/lab/interactive-calibration-design`
- `POST /api/lab/interactive-calibration-design/run`

## 验收

新增回归：

`test_p64_interactive_calibration_design_defines_safe_latent_factor_framework`

要求：

- 必须包含核心隐藏因子。
- 事件 schema 必须包含时间、领域、强度、置信度和 allowed use。
- 反向问题覆盖财富、事业、关系、健康、迁移、压力。
- 反向问题不能包含诱导性或预测性词汇。
- GNN/RL 不得进入核心推理。
- runtime / answer / rule mutation 全部为 0。

## 给分析师的反馈

目前信息已经足够进入设计实现。建议后续 review 聚焦三点：

- 隐藏因子目录是否还缺少关键变量，尤其是资源、行动效率、时间敏感度。
- 反向问题是否足够中性，是否存在诱导用户确认某种结果的风险。
- 健康和关系事件的边界是否足够保守，尤其是疾病、寿命、诊断、离婚等高风险表达。
