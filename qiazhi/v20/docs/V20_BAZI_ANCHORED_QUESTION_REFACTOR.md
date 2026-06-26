# V20 八字锚定提问系统重构计划

更新时间：2026-05-20

## 问题判断

当前智能问题系统已经有种子问题、问题原子、问题链 DAG、点击反馈、训练 pointer 和角色化叙事，但提问质量仍不稳定。核心原因不是问题数量不足，而是最终展示的问题没有被强制绑定到当前命主八字。

现在的问题链路更像：

```text
Feature / Decision / Seed / Atom
-> QuestionCandidate
-> 排序
-> UI 展示
```

这会导致部分问题停留在八字知识问答层面，例如“用神方向先扶身还是泄秀”。这类问题本身是合法命理问题，但如果没有绑定当前日主、原局、大运、流年、结构主链和证据缺口，就会把系统带离当前命主测算。

## 新原则

所有问题必须围绕当前被测算八字，但不要求机械重复四柱文本。

必须满足：

```text
原局四柱
+ 日主
+ 大运
+ 流年
+ 结构动态主链
+ 规则/画像/特征证据
+ 当前角色
+ 已问问题状态
```

问题可以自然表达，但至少要带一个真实上下文锚点：

- 当前日主或承接状态
- 当前结构主线
- 当前大运/流年触发
- 当前画像矛盾
- 当前规则证据
- 当前中枢裁决理由

禁止：

- 纯八字知识问答直接出现在测算页
- 没有大运/流年时提大运/流年触发问题
- 没有结构主线时提结构闭合/做功问题
- 没有证据缺口时提复核类问题
- LLM 根据泛问题自行补命盘事实

## 新链路

```text
QuestionSeed / QuestionAtom
-> QuestionIntent
-> BaziQuestionAnchor
-> RoleQuestionNarrative
-> DisplayQuestion
-> LLM SelectedQuestionContext
```

`QuestionSeed` 和 `QuestionAtom` 不再直接作为 UI 标题来源。它们只表达“要问哪类问题”。最终问题必须由当前盘锚点渲染。

## BaziQuestionAnchor

每个问题必须生成一个问题锚点：

```text
context_id
question_key
atom_id
role_key
anchor_status
natal_pillars
day_master
luck_pillar
flow_year_pillar
primary_dynamic_chain
mainline_domain
mainline_label
evidence_refs
portrait_axes
feature_ids
time_binding
why_this_question
missing_requirements
```

### anchor_status

| status | 含义 | UI 行为 |
|---|---|---|
| `bound` | 已绑定当前盘、主线和证据 | 可展示 |
| `weak` | 有当前盘，但证据不足 | 降权，Admin 可见 |
| `missing_time` | 需要大运/流年但当前缺失 | 隐藏 |
| `missing_structure` | 需要结构主线但当前缺失 | 隐藏 |
| `unsupported` | 不能回到当前盘证据 | 隐藏 |

## 问题渲染规则

### 用户侧

自然、简洁、贴近咨询，不堆术语。

坏例：

```text
用神方向先扶身还是先泄秀？
```

好例：

```text
这盘主线已经落在「食神制杀」，但日主承接还要看清。下一步更该先判断扶身承接，还是顺着食伤泄秀去完成制杀？
```

### 命理师侧

保留术语，明确证据和复核边界。

```text
当前原局为乙木日主，结构主链指向「食神制杀」，庚子大运与丙午流年同时牵动官杀、食伤和印比。用神复核应先看印比扶身承接，还是先看食伤泄秀能否完成制杀？
```

### 管理员侧

不做咨询包装，展示链路。

```text
问题锚点：乙木日主 / 食神制杀 / 庚子大运 / 丙午流年
推荐原因：主链存在官杀压力与食伤制化，当前缺口是日主承接与岁运触发顺序。
```

## 提问系统职责拆分

### QuestionAtom

只负责问题类型：

```text
问用神路径
问结构主链
问事业压力来源
问财星承接
问岁运触发
```

不负责最终标题。

### BaziQuestionAnchorBuilder

负责把问题类型绑定到当前盘：

```text
chart_facts
time_context
structure_dynamics.primary_dynamic_chain
mainline_arbitration.primary_mainline
decision_report
feature_layer
portrait_projection
question_session_state
```

### RoleQuestionRenderer

负责把锚点转成不同角色可读的问题：

```text
guest: 少术语、入口式
user: 生活化、说明为什么问
practitioner: 专业术语、证据和边界
admin: 锚点、证据、策略、训练状态
```

### LLM SelectedQuestionContext

LLM 不只接收 `title`，还必须接收：

```text
selected_question_anchor
selected_question_why_now
selected_question_forbidden_drift
```

如果 LLM 回答改写日主、四柱、大运或流年，答案不得展示。

## 与知识库的关系

知识库负责提供命理概念、规则和结构机制，但不能直接生成测算页问题。

正确关系：

```text
知识库问题种子
-> 只作为 QuestionAtom / Seed 来源
-> 必须经过当前盘锚定
-> 才能成为 DisplayQuestion
```

也就是说，知识库问题可以告诉系统“这类结构通常需要问承接还是泄秀”，但不能直接问用户“用神先扶身还是泄秀”。

## 旧模块清理原则

新问答交互系统必须替换旧问题出口，不能让旧模块继续污染 UI 或 LLM 上下文。

### 保留的骨架

以下模块保留，但只作为底层能力：

```text
interaction/question_atoms.py
interaction/question_dag.py
interaction/role_question_click.py
learning/question_runtime_pointer.py
learning/question_dag_training.py
learning/question_dag_policy_replay.py
learning/role_question_click_training.py
decision/question_source_runtime.py
graph/question_source_graph.py
```

保留原因：

- 问题原子仍是“要问什么”的基础库。
- DAG 仍负责连续追问和合法跳转。
- 点击反馈和 runtime pointer 仍负责直接调优排序。
- question source graph 仍负责 Admin 解释来源。

### 必须替换的旧出口

以下逻辑不能再直接面向用户输出最终问题：

```text
interaction/questions.py::QUESTION_LABELS
interaction/questions.py::_personalized_question_title
interaction/questions.py::_applied_question_title
interaction/question_seed_registry.py::template_zh.format(...)
interaction/question_agent.py 旧 followup 模板出口
frontend/app.js::next_question_plan.recommended_atoms[].template_zh
decision/engine.py::question_seeds
knowledge/loader.py::question_seeds
```

处理方式：

```text
旧 title/template/question_seeds
-> 只进入 QuestionIntent / QuestionAtom / evidence source
-> 不允许作为 DisplayQuestion.title
```

### 废弃路径

`question_agent` 当前同时做三件事：已问 suppression、旧 followup 生成、标题 humanize。重构后拆分：

```text
answered suppression -> QuestionSessionState / NextQuestionPlan
followup generation -> QuestionAtom + DAG + AnchorBuilder
title humanize -> RoleQuestionRenderer
```

完成后 `interaction/question_agent.py` 应降级为兼容层，再从 runtime 移除。

### 前端清理

前端不再读取：

```text
question.title 作为唯一展示文本
next_question_plan.recommended_atoms[].template_zh
knowledge question_seeds
```

前端只读：

```text
questions[].display_title
questions[].question_narrative
questions[].question_anchor
next_question_plan.recommended_questions[].display_title
```

### 清理验收

```text
1. rg \"template_zh\" frontend 不再命中展示逻辑
2. `question_agent_state.generated_followup_count == 0`
3. 普通用户 projection 中不存在 anchor_status != bound 的问题
4. selected_question 进入 LLM 时必须包含 selected_question_anchor
5. KnowledgeUnit.question_seeds 只作为 source，不直接进入 UI
6. 旧泛问题测试样例不能再出现在用户页
```

## 验收规则

P0 必须新增测试：

```text
1. 所有展示问题必须有 question_anchor.anchor_status == bound
2. 时间类问题没有大运/流年时不能展示
3. 结构类问题没有 primary_dynamic_chain 时不能展示
4. 用神类问题必须引用当前日主、结构主线或承接证据之一
5. 同一测算中已问过的问题不重复展示
6. 乙木日主案例中，问题和回答不得出现“甲木日主”
7. 纯模板问题不能作为最终 display title
8. Admin UI 必须能看到 anchor、证据和 missing_requirements
```

## 实施计划

### P0：合同和测试

- 新增 `BaziQuestionAnchor` schema。
- 新增 anchor builder 单元测试。
- 新增 display question 不能直接等于 atom template 的测试。
- 新增日主漂移测试。

### P1：Anchor Builder

- 从 runtime 已有对象生成每个问题的 `question_anchor`。
- 把 `QuestionCandidate` 扩展为带 anchor 的候选。
- 对缺时间、缺结构、缺证据的问题做隐藏或降权。

### P2：角色化问题渲染

- 新增 `RoleQuestionRenderer`。
- 用户侧问题自然表达。
- 命理师侧问题保留专业术语。
- Admin 侧展示锚点和证据链。

### P3：运行时合流

- `next_question_plan` 不再只合并 atom 排序，也要合并 anchor。
- `_merge_next_question_plan_into_questions` 输出最终 `display_title` 和 `question_anchor`。
- UI 使用 `display_title`，不再直接使用 `template_zh`。

### P4：LLM 回答绑定

- LLM prompt 接收 `selected_question_anchor`。
- 日主、四柱、大运、流年漂移直接 fallback。
- 回答必须解释“为什么这个问题和当前盘有关”。

### P5：UI 对齐

- 用户页显示自然问题和轻量“围绕当前盘”提示。
- 命理师页显示证据边界。
- Admin 页显示 anchor、missing requirements、策略来源和训练权重。

### P6：训练与合成验证

- 合成八字验证覆盖常见结构主链。
- 518K 回放统计泛问题比例、anchor bound rate、日主漂移率。
- 训练只优化排序、角色表达、问题密度和追问连续性，不改命盘事实。

### P7：旧问答模块清理

- 从 runtime 移除 `question_agent` 旧 followup 生成。已完成：`question_agent` 不再生成 `agent_followup` 问题，旧 followup 模板函数已删除。
- 前端下一问摘要改读锚定后的 `display_title`。
- `QuestionCandidate.title` 降级为内部兼容字段。
- 清理旧知识库 question seed 直出路径。
- 删除或归档不再被 runtime 使用的旧测试。

状态：完成第一版。后续仅做 518K 质量统计和真实反馈扩容。

## 完成标准

```text
问题系统不再问“泛八字知识题”
每个推荐问题都能解释为什么和当前盘有关
问题链能围绕主线逐步深入
回答不会因为问题泛化而漂移命盘事实
Admin 能看到每个问题的锚点和证据
训练能直接优化问题排序和表达
旧标题生成和旧 followup 模板不再污染 UI 或 LLM 上下文
```
