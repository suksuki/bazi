# V20 角色化画像与问题设计

更新时间：2026-05-11

## 设计目标

同一份命盘事实、规则命中和中枢主线保持一致，但不同角色看到不同的画像深度和问题表达：

```text
ChartFacts / DecisionReport / BrainState
-> Role Projection
-> Role Portrait Profile
-> Role Question Profile
-> Role Runtime View
```

角色化只发生在 view/projection 层，不改四柱事实、不改规则结果、不改中枢策略版本。

## 角色视图

| 角色 | 画像深度 | 问题风格 | 说明 |
| --- | --- | --- | --- |
| guest | entry_overview | starter_questions | 只看入门摘要和少量起步问题，避免技术术语。 |
| user | guided_summary | guided_questions | 看引导式画像和用户可行动问题。 |
| analyst | technical_review | review_questions | 看命理师复核问题、证据边界和更完整画像轴。 |
| lab/admin | full/observation | observation_questions | 看完整观测数据、策略状态和审计字段。 |

## 已落地第一版

- `guest` 已成为正式 runtime projection role。
- `role_view/` 已成为独立角色视图模块，承接画像策略、问题策略和 RoleViewModel 生成。
- `project_runtime_for_role(...)` 现在调用 `role_view` 生成 `role_view_model`。
- `role_view_model.portrait_profile` 按角色输出不同画像深度。
- `role_view_model.question_profile` 按角色输出不同问题风格和问题数量上限。
- `role_view_model.explanation_profile` 已声明后续回答层的角色表达风格。
- `role_view_model.visibility_profile` 已声明角色可见性意图。
- `role_answer_profile` 已落地，答案正文会按 guest/user/analyst/admin 生成不同表达投影。
- 前端智能问题区已读取 `role_view_model.question_profile`，按角色显示入口/引导/复核/观测提示和问题数量。
- 命理师、实验室和管理员问题区已从单列表升级为分组队列：结构复核、证据边界、主题候选、系统观测等。
- 角色问题点击已接入 append-only 学习信号 `role_question_click_ledger`，只保存 role、question key、domain、策略和分组，不保存用户原文或问题标题。
- P4 第一段已落地：`/api/v20/learning/role-question-click` 会聚合角色、分组、domain、question_strategy 和问题 key，生成只读学习报告。
- P4 第二段已落地：`/api/v20/learning/role-view-policy-candidates` 会把学习报告转换为 role view policy 候选版本。
- P4 第三段已落地：`/api/v20/learning/role-view-policy-replay` 会比较 baseline 与候选策略差异。
- P4 第四段已落地：管理员/实验室观测页展示 role view learning，只读串联点击习惯、候选策略和 replay gate。
- P5 第一段已落地：`question_seed_registry` 提供结构化种子问题候选，使用现有合法 question key，并要求 feature/domain/time 信号匹配。
- P5 第二段已落地：`seed_source_key` 已进入角色点击 ledger 和训练聚合，用于观察不同角色对 seed 候选的选择习惯。
- P5 第三段已落地：seed 点击统计会生成 `role_view_seed_fit_policy` 候选，并进入 replay diff。
- P5 第四段已落地：观测页已展示 seed-fit 候选数量、top seed 和 seed replay 影响。
- SSE 流式答案已接入 `role_answer_profile`，done 事件会输出角色投影后的最终答案。
- P6 第一段已落地：`/api/v20/role-view/runtime-pointer` 提供只读 preflight pointer，明确 runtime gate 仍关闭。
- P6 第二段已落地：观测页已展示 role view runtime pointer 的 active/candidate/gate 状态。
- P6 第三段已落地：replay 已增加 impact summary，并同步给 runtime pointer。
- P5 第五段已落地：seed registry 已扩展到 20 条，补齐十神、五行、格局、健康和时间层入口。
- P7 已落地：role view runtime pointer 自动激活 replay-ready 候选，只重排角色问题视图，不改变命盘事实或底层裁决。
- Completion 已落地：`/api/v20/role-view/completion` 返回 P1-P7 机器可读完成状态，当前工程闭环为 100%。
- guest 的公开问题不再暴露原始标题、决策 key、规则 key 或特征 id。
- user 的公开问题保留少量可解释来源，但隐藏规则 key 和特征 id。

## Guardrails

- `ROLE_VIEW_MODEL_DOES_NOT_CHANGE_CHART_FACTS`
- `ROLE_PORTRAIT_IS_PROJECTION_ONLY`
- `ROLE_QUESTIONS_ARE_VIEW_LAYER_ONLY`

## 下一步

- 收集真实样本后继续校准 boost 权重和 seed 覆盖面。
- 将 SSE 流式答案也接入 `role_answer_profile`，避免流式完成后回到统一答案口径。
