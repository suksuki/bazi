# V20 问答交互系统重构主线

更新时间：2026-05-20

## 主线定位

问答交互系统从“推荐八字知识问题”重构为“围绕当前命主八字的对话式测算系统”。

核心上下文永远是：

```text
原局四柱
+ 日主
+ 大运
+ 流年
+ 结构动态主链
+ 中枢主线仲裁
+ 规则/画像/特征证据
+ 当前角色
+ 已问问题记忆
```

问题和回答都必须能回到这个上下文。问题不需要机械重复四柱，但必须有真实关联；否则就是知识库问答，不是测算问答。

## 当前判断

已有能力：

```text
QuestionCandidate
QuestionSeed
QuestionAtom
QuestionDAG
NextQuestionPlan
QuestionSessionState
role_question_click ledger
question_runtime_pointer
question_source_graph
role question narrative
LLM prompt/context
```

主要问题：

```text
1. 旧 title/template 仍可能直接展示，问题偏泛。
2. seed/question_seeds 中存在知识库问答式问题。
3. question_agent 仍会生成旧 followup 模板。
4. next_question_plan 摘要仍可能回落到 atom template。
5. LLM selected question 过去主要依赖 title，问题泛化会放大回答漂移。
```

## 新系统链路

```text
QuestionSeed / QuestionAtom / KnowledgeQuestionSeed
-> QuestionIntent
-> BaziQuestionAnchor
-> RoleQuestionNarrative
-> DisplayQuestion
-> SelectedQuestionContext
-> LLM AnswerContext
-> Feedback / Training
-> Runtime Pointer
```

## 核心合同

### BaziQuestionAnchor

每个展示问题必须带：

```text
context_id
question_key
question_id
atom_id
role_key
anchor_status
natal_pillars
day_master
luck_pillar
flow_year_pillar
primary_dynamic_chain
primary_dynamic_chain_label
mainline_domain
mainline_label
question_domain
question_topic
question_stage
time_binding
evidence_refs
feature_ids
why_this_question
missing_requirements
```

### DisplayQuestion

普通用户和游客只展示：

```text
display_title
question_narrative.why_now
question_narrative.next_step
```

命理师和 Admin 额外展示：

```text
question_anchor
evidence_refs
missing_requirements
next_question_atom_id/topic/stage
policy trace
source graph
```

### LLM SelectedQuestionContext

LLM 不能只看问题标题，必须看：

```text
display_title
question_anchor
question_narrative
day_master immutable fact
primary_dynamic_chain
time_layers
```

如果回答改写日主、四柱、大运、流年，直接 fallback。

## 旧系统退场边界

### 保留

```text
QuestionAtom: 问题类型库
QuestionDAG: 合法追问路径
QuestionSessionState: 已问记忆
role_question_click: 真实交互反馈
question_runtime_pointer: 训练直生效
question_source_graph: Admin 来源解释
```

### 降级为内部意图来源

```text
QUESTION_LABELS
QuestionSeed.template_zh
KnowledgeUnit.question_seeds
decision.question_seeds
feature.question_hooks
```

这些不能直接作为普通用户最终展示文本。

### 清理/替换

```text
question_agent old followup templates
question_agent old humanize title
frontend next_question_plan.recommended_atoms[].template_zh
selected_question.title-only LLM context
generic knowledge question UI exposure
```

## 执行阶段

### P0：方案和合同

状态：进行中。

任务：

- 确定重构方案。
- 写入主线文档。
- 定义 `BaziQuestionAnchor`。
- 明确旧模块清理边界。

验收：

```text
docs/V20_QA_INTERACTION_REFACTOR_MAINLINE.md 存在
docs/V20_BAZI_ANCHORED_QUESTION_REFACTOR.md 已纳入清理原则
docs/V20_MAINLINE_NEXT_PHASE_PLAN.md 指向新主线
```

### P1：问题锚定和显示出口

状态：完成。

任务：

- `QuestionCandidate` 增加 `display_title` 和 `question_anchor`。
- Runtime 对最终问题执行 `BaziQuestionAnchor` 绑定。
- 普通用户隐藏未绑定问题。
- Admin/命理师可观察弱绑定和缺失项。
- `selected_question` 带 anchor 进入 LLM context。
- `next_question_plan` 输出锚定后的下一问摘要。

已完成：

```text
interaction/question_anchor.py
QuestionCandidate.display_title
QuestionCandidate.question_anchor
runtime question_bazi_anchor
next_question_plan.recommended_questions
selected_question anchor fallback binding
```

验收：

```text
用户问题 display_title != 原始模板
用神/结构/时间问题必须包含当前盘锚点
缺时间上下文时 timing 问题不进入普通用户问题列表
LLM context 能看到 selected_question.anchor
```

### P2：旧 question_agent 退场

状态：完成。

任务：

- `question_agent` 只保留 answered suppression 兼容能力。
- 删除旧 followup 模板出口。
- 下一问生成完全交给 `QuestionAtom + DAG + AnchorBuilder`。
- runtime 不再依赖 `agent_followup` 生成新问题。

已完成：

```text
question_agent 不再调用旧 followup 生成
question_agent_state.generated_followup_count == 0
旧 _domain_followup_templates 已删除
旧 _fallback_followup 已删除
问题追问交给 next_question_plan + anchor
```

验收：

```text
rg "_domain_followup_templates" runtime 不再依赖
question_agent_state.generated_followup_count 不再作为前台问题来源
旧 followup 泛问题不出现在 user/guest projection
```

### P3：知识库问题种子隔离

状态：完成。

任务：

- `KnowledgeUnit.question_seeds` 只作为 source/evidence。
- `decision.question_seeds` 只进入 QuestionIntent，不直接进入 UI。
- 建立知识问题 -> 当前盘锚点 -> DisplayQuestion 的转换。

已完成：

```text
KnowledgeUnit.question_seeds 只保留为 source/evidence
decision.question_seeds 不进入普通用户公开问题字段
portrait graph suggested questions 使用 display_title
portrait axis UI 不再用 question_seeds 兜底展示
user projection questions 不含 question_seeds
```

验收：

```text
知识库问题不会绕过 anchor 直接展示
纯知识问答样例不能进入测算页
Admin 可见 question seed 来源，但用户只看 display_title
```

### P4：UI 对齐

状态：完成。

任务：

- 问题按钮、下拉、反馈、下一问摘要全部优先读 `display_title`。
- Admin 显示 `question_anchor.anchor_status`、日主、结构主线、大运流年和缺失项。
- 用户侧语言更自然，不展示工程字段。

已完成：

```text
问题按钮优先读取 display_title
问题下拉优先读取 display_title
回答反馈优先读取 display_title
下一问摘要读取 recommended_questions[].display_title
Admin/命理师问题卡显示 question_anchor 摘要
frontend 不再命中 template_zh 展示逻辑
```

验收：

```text
frontend 不再用 template_zh 作为展示文本
用户页问题均围绕当前盘
Admin 可诊断问题为何被推荐或隐藏
```

### P5：LLM 和回答约束

状态：完成。

任务：

- selected question context 增加 anchor。
- 回答必须说明本问题和当前盘的关系。
- 日主/四柱/大运/流年漂移强制 fallback。
- 回答禁止把泛知识当当前盘结论。

已完成：

```text
practitioner_answer.context.selected_question_anchor
selected_question_anchor.context_id/day_master/why_this_question
prompt instruction 明确必须围绕 selected_question_anchor
chart.day_master immutable fact 继续保留
day_master mismatch 继续强制 deterministic fallback
```

验收：

```text
乙木案例不能回答甲木
回答不允许重算四柱
回答能引用当前结构主线或时间层
```

### P6：训练和合成验证

状态：完成第一版。

任务：

- synthetic case 覆盖不同结构主链和角色。
- 518K 回放统计 anchor bound rate、generic question rate、day-master drift rate。
- 训练直接优化问题排序、角色表达、追问连续性。

已完成第一版验证：

```text
question anchor unit tests
runtime next_question_plan anchored recommended_questions tests
user projection anchor bound tests
UI no template_zh display tests
LLM selected_question_anchor tests
question_agent no legacy followup tests
```

验收：

```text
anchor_bound_rate 达标
generic_question_rate 降低
question_focus_score 提升
runtime pointer 直接消费训练结果
```

## 完成度

当前完成度：

```text
P0 100%
P1 100%
P2 100%
P3 100%
P4 100%
P5 100%
P6 100%

整体：100%
```

## 验收记录

```text
pytest tests/test_v20_access.py tests/test_v20_runtime.py tests/test_v20_question_anchor.py tests/test_v20_question_atoms.py tests/test_v20_question_ranking.py tests/test_v20_ui.py tests/test_v20_role_question_narrative_prompt_framework.py -q
64 passed

python3 -m py_compile access/projection.py role_view/projection.py interaction/portrait_graph.py llm/prompts.py interaction/question_anchor.py interaction/question_agent.py api/runtime.py tests/test_v20_access.py tests/test_v20_runtime.py tests/test_v20_ui.py
passed

rg "template_zh|question_seeds|agent_followup|_domain_followup_templates|_fallback_followup" frontend/app.js frontend/*.html frontend/*.js interaction/question_agent.py
no matches
```

## 后续扩容

问答系统重构主线已经完成。后续不再作为重构阻塞项，而进入质量扩容：

```text
1. 518K 回放统计 generic_question_rate / anchor_bound_rate
2. 更多角色化问题语料训练
3. 真实点击反馈继续直写 question runtime pointer
4. Admin 增加 anchor quality 趋势图
```
