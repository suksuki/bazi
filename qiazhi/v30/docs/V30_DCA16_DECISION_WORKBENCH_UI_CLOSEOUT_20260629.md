# V30 DCA-16 Decision Workbench 与页面流程收口

更新时间：2026-06-29

## 阶段目标

本阶段把前面已经完成的 DCA-13 到 DCA-15 接到真实页面流程：

```text
Signal Registry
-> DecisionCandidate
-> ConflictResolver
-> DecisionVerdict
-> Decision Workbench
-> 7 阶段页面 / 命理师校准 / 智能问答
```

本阶段不是增加新的命理事实算法，而是完成产品级产出编排：

- 用户能看到清爽的 Verdict、建议和必要分支。
- 命理师能看到冲突审计和可操作校准。
- 页面流程按 7 个阶段推进。
- 智能问答仍独立于步骤页面，只在中枢判断必要时挂载到当前阶段。
- 训练信号只对命理师/Admin 可见，不进入普通用户界面。

## 执行内容

### 1. ConflictResolver 进入命理师校准

`journey_branch_calibration` 阶段现在会从 `DecisionConflict` 生成显式 `option_hints`：

- 采纳主分支
- 保留备选
- 转为追问

这些分支进入现有 `TextOption / PractitionerSelection` 管线，因此命理师的选择仍然只更新中枢权重和训练信号，不改命盘事实。

### 2. Reading Surface 增补 Decision Workbench

`reading_surface` 新增：

```text
decision_workbench
```

它是页面消费的稳定入口，包含：

- `summary`
- `verdict_cards`
- `conflict_cards`
- `calibration`
- role-gated `training_signal`

普通用户：

- 只看 Verdict、建议、必要分支提示。
- 不看到内部 candidate id、训练字段、score adjustment。

命理师/Admin：

- 可看到 conflict audit 摘要。
- 可看到 top candidate、signal count、校准策略。
- 可看到训练信号和校准入口。

### 3. 前端页面流程接入

前端 7 阶段页面新增三个稳定区块：

- 第 5 阶段 `分支冲突与命理师校准`：显示冲突卡和校准摘要。
- 第 6 阶段 `Decision Engine 裁决`：显示 Verdict 裁决卡。
- 第 7 阶段 `最终断语、建议与智能对话`：显示最终收束和 Verdict 依据卡。

智能问答仍走：

```text
reading_surface.current_dialogue_turn
```

不会再混成导航步骤，也不会从 `questions[]` 自行抢入口。

## 关键边界

- `Decision Workbench` 不改 score。
- `Decision Workbench` 不改 Verdict。
- `PractitionerSelection` 不改四柱、大运、流年、原始规则事实。
- 普通用户界面不暴露 `training_signal`。
- LLM 仍只做表达，不做最终命理裁决。

## 验证结果

专项验证：

```text
../.venv312/bin/python -m py_compile v30/presentation/thinking.py v30/presentation/client_model.py v30/brain/practitioner_interaction.py
node --check frontend/app.js
../.venv312/bin/pytest tests/unit/test_sidebar_memory_useful_god.py tests/unit/test_presentation_projection.py tests/unit/test_practitioner_interaction_mainline.py tests/unit/test_decision_conflict_resolver.py tests/unit/test_signal_based_decision_candidate_builder.py -q

24 passed in 1.54s
```

Runtime smoke：

```text
journey_steps: 7
branch_option_sets: 4
verdict_count: 9
conflict_count: 13
user_training_signal_visible: False
practitioner_training_signal_visible: True
practitioner_option_sets: 52
current_dialogue_action: ask
```

## 当前完成度

本阶段完成后，DCA 主线已经进入可产品化打磨：

- 工程主线：约 96%
- 智能体验：约 86%
- 产品 UI：约 75%

剩余重点不再是大架构，而是：

- UI 细节打磨
- 真实案例回放
- Admin 质量 diff 聚合
- 518K 分布观察
- 训练策略晋级门禁
