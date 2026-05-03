# V20 Portrait And Tag Model

V20 画像层不再等同于规则命中列表，也不再把 `weak_candidate`、`requires_review`、`mixed` 这类内部裁决状态当成用户画像。

## 核心定义

```text
Rule Layer      = 证明命理命题是否成立
Decision Layer  = 对规则证据、反证、强弱、时序做裁决
Topic Projection = 把裁决投射到财富、事业、关系、健康、时间等主题
Portrait Layer  = 给当前八字贴画像 TAG 和主题定性
Question Layer  = 根据画像 TAG、主题投射和用户意图生成问题
```

因此：

```text
Rule != Portrait
Rule -> Decision -> TopicProjection -> PortraitTag -> Question
```

## UI 展示原则

用户画像区只展示：

- `label`: 画像轴名称，例如 `财富承接画像`
- `profile_tag`: 画像主 TAG，例如 `财的材料与承接：主线成形`
- `profile_tags`: 多个画像标签，例如 `财星`、`食伤输出`、`比劫竞争`
- `profile_summary`: 白话画像摘要
- `attention_level`: `high / medium / normal`

用户画像区不展示：

- `decision_states:confirmed,weak_candidate`
- `requires_review`
- `weak_candidate`
- 规则 id
- 调试 score
- 原始裁决链 debug 文本

这些信息可以留给命理师视图、规则命中区或调试证据区，但不能成为画像本身。

## 当前画像轴

```text
strength     -> 日主承载画像
wealth       -> 财富承接画像
career       -> 事业角色画像
relationship -> 关系互动画像
health       -> 身心平衡画像
time         -> 时运触发画像
useful_god   -> 调候取向画像
pattern      -> 格局结构画像
element      -> 五行气势画像
branch       -> 地支互动画像
ten_god      -> 十神角色画像
```

## 系统决策与命理师修订

系统必须先给出画像定性。命理师不是和系统二选一，而是在系统定性之后做修订：

```text
System PortraitTag
-> PractitionerRevision
-> Fused Portrait View
```

命理师可以调整：

- 画像权重
- TAG 排序
- 主题关注度
- 证据解释方式
- 追问方向

命理师不能直接修改：

- 四柱事实
- 十神事实
- 藏干事实
- 合冲刑害事实
- calendar/chart facts

## 当前实现位置

- `v20/interaction/portrait_projection.py`
- `v20/interaction/portrait_graph.py`
- `v20/interaction/portrait_schema.py`
- `v20/interaction/question_intent.py`
- `v20/frontend/app.js`
- `v20/access/projection.py`

## 下一步计划表

| 顺序 | 主线任务 | 目标 | 输出 | 状态 |
| --- | --- | --- | --- | --- |
| P0-1 | 画像 TAG 映射层 | 建立稳定的 `Rule -> Decision -> TopicProjection -> PortraitTag` 映射，不再靠临时文本匹配 | `v20.interaction.portrait_tags` / rule-domain tag catalog / 可追溯画像证据 | completed |
| P0-2 | TAG 驱动推荐问题 | 推荐问题根据画像 TAG 和用户意图生成，而不是模板或规则标题拼接 | `PortraitTag -> QuestionCandidate` hooks / domain-specific question ranking | completed |
| P0-3 | 八字图谱画像摘要 | 给一个八字生成简短断命式画像：主轴、优势、压力、时间触发、建议问题 | `PortraitGraphSummary` / UI summary block | completed |
| P1-1 | 自学习闭环补缺 | 补齐 `portrait_active_item`、`corpus_signal_count`、`subcondition_active_ready_count`、`rule_replay_eval` | fast test learning/corpus 断言恢复 | pending |
| P1-2 | 518K 与合成八字回放 | 用全量 corpus 和 synthetic cases 校验 TAG 分布、问题多样性、规则过宽/过窄 | replay report / tag coverage / question diversity report | pending |
| P2-1 | 命理师修订学习 | 系统先决策，命理师修订权重和表达，进入离线学习 | `PractitionerRevision -> TrainingSignal` | pending |
| P2-2 | LLM 表达层强化 | LLM 消费画像 TAG、EvidencePack、AnswerPlan，输出多语言命理师白话表达 | practitioner answer adapter / verifier | pending |

当前立即推进 P0-1，然后接 P0-2。P1 的学习/语料链路在画像和问题主链稳定后补齐。

## 验证

画像相关回归测试：

```bash
./v20/scripts/test_targeted.sh "portrait or runtime or question_ranking or access"
```

期望结果：

```text
54 passed
```
