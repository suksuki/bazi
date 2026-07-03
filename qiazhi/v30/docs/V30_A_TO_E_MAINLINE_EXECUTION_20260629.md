# V30 A-E 主线执行记录：TOI / SPI / CBI 进入中枢闭环

更新时间：2026-06-29

## 结论

本轮从 A 到 E 已完成主线骨架落地。

TOI、SPI、CBI 不再是旁支任务，已经进入当前 V30 主线：

```text
SPI StagePoint
-> TOI Text-to-Option
-> PractitionerSelection
-> CBI belief delta / final synthesis priority
-> Admin intelligence replay
-> Synthetic validation / prompt profile audit
-> UI user/practitioner projection
```

本轮不是做一个临时按钮，而是把“文本变选项、命理师可校准、中枢可采用、Admin 可回放、验证可检查”的闭环打通。

## 当前完成度更新

| 模块 | 本轮前 | 本轮后 | 说明 |
| --- | ---: | ---: | --- |
| StagePoint 框架 | 72% | 78% | 增加 Admin replay、命理师 overlay、专项验证入口 |
| Text-to-Option 框架 | 68% | 78% | 增加命理师可操作、选择记录、synthetic tier |
| 命理师模式 | 28% | 55% | 已有 OptionSet 面板、采纳/优先/降权/排除/待问/备注 |
| Admin 观察台 | 62% | 70% | 增加 intelligence replay 与专项验证卡片 |
| LLM Prompt Profile | 70% | 75% | 增加离线质量审计，真实 live 对比待后续 |
| 用户 UI | 65% | 70% | 用户选项视觉更清楚，命理师控件不泄露给用户 |
| 训练/验证 | 76% | 80% | TOI/SPI/HF synthetic 和 prompt audit 可跑 |

整体判断：

```text
工程主线完成度：约 82%
智能体验完成度：约 70%
产品可打磨完成度：约 64%
```

## Phase A：命理师交互闭环

已完成：

- 新增 `v30.brain.practitioner_interaction`。
- 新增 `v30.practitioner_interaction_state.v1`。
- 新增 `v30.practitioner_selection_effect.v1`。
- 支持命理师动作：
  - 采纳 `select`
  - 优先 `rank`
  - 降权 `downrank`
  - 排除 `reject`
  - 待问 `needs_question`
  - 备注 `note`
- 选择结果生成 `PractitionerSelection`。
- 选择结果形成 belief delta、StagePoint priority delta、final synthesis priority delta。
- 明确禁止改写：
  - 四柱
  - 出生时间
  - 历法转换
  - 大运流年计算
  - 原始规则真假

新增 API：

```text
GET  /api/v30/readings/{reading_id}/practitioner/options
POST /api/v30/readings/{reading_id}/practitioner/selections
```

前端：

- practitioner 角色显示命理师校准面板。
- user 角色不显示命理师控件。
- 点击后只更新当前 thinking overlay，不刷新页面步骤。

## Phase B：Admin 中枢观察台

已完成：

- 新增 `v30.admin_intelligence_replay.v1`。
- Admin 可回放每一步：
  - StagePoint candidate / selected / discarded
  - Text-to-Option semantic units / option sets / discarded units
  - Brain Judge 摘要
  - Prompt profile
  - PractitionerSelection 分布

新增 API：

```text
GET /api/v30/admin/readings/{reading_id}/intelligence-replay
```

前端：

- 管理台测算详情页显示“中枢回放”摘要。
- 显示候选数、采用数、丢弃数、选项数、prompt profile。

## Phase C：专项合成验证

已完成：

- 新增 `v30.text_option_synthetic_validation.v1`。
- 覆盖：
  - `SPI-7A` StagePoint synthetic tier
  - `TOI-7B` Text-to-Option synthetic tier
  - `TOI-7C` Practitioner selection alignment tier
  - `HF-TOI-A` 隐藏属性 OptionSet tier
  - `VAL-518K-A` StagePoint / OptionSet 分布观察 smoke
  - 单问题对话 contract

新增 API：

```text
GET /api/v30/admin/validation/text-option-synthetic
GET /api/v30/admin/validation/stage-option-intelligence-replay
```

说明：

- 本轮只做 smoke distribution observation。
- 没有跑完整 518K。
- 完整 518K 放到大节点再跑。

## Phase D：LLM Prompt Profile 质量审计

已完成：

- 新增 `v30.llm_prompt_profile_quality_audit.v1`。
- 离线检查每个 thinking stage：
  - 是否有 prompt profile。
  - 是否 stage/scope bound。
  - 是否携带 StagePoint 和 OptionSet 上下文。
  - 是否禁止 chart fact mutation。
  - 是否包含自检模板语言风险。

新增 API：

```text
GET /api/v30/admin/llm/prompt-profile-quality-audit
```

说明：

- 本轮不调用真实 LLM。
- 下一步可以在同一结构上接 live smoke：latency、candidate count、hard failure、profile 对比。

## Phase E：用户体验收束

已完成：

- 用户问题增加 OptionSet 视觉提示。
- 命理师面板使用紧凑卡片，不在用户页展示。
- 手机端命理师动作和 Admin replay 单列显示。
- 页面交互不再把对话/选择动作混同为页面步骤跳转。
- 2026-06-29 明确补充：智能对话是独立 dialogue surface，可挂载在任意测算页面；不得再作为 `question_followup` 伪步骤、独立导航页或第 N+1 步出现。

## 本轮轻量验证

按“相关测试优先，不跑重测试”执行：

```text
py_compile passed
node --check frontend/app.js passed
tests/unit/test_text_to_option_interaction.py
tests/unit/test_practitioner_interaction_mainline.py
tests/unit/test_stage_option_validation_mainline.py

10 passed
```

未执行：

- 全量 unit。
- 完整 518K。
- live LLM profile 对比。

原因：

- 本轮修改集中在 TOI/SPI/CBI 闭环与前端投影。
- 重测试放到大节点再跑，避免日常迭代被测试成本拖住。

## 下一步主线

优先级一：

1. 让命理师选择真正进入 final synthesis 的最终用户报告排序。
2. 把 PractitionerSelection 持久化到数据库，而不是只在当前进程内存。
3. Admin replay 增加逐条展开详情。

优先级二：

1. 接 live LLM prompt profile smoke。
2. 记录每个 profile 的 latency、candidate point count、hard failure。
3. 以真实 Gemma 输出优化 prompt profile。

优先级三：

1. 把 TOI/SPI 指标接入训练 orchestrator 的正式质量指标。
2. 在大节点跑全量 unit 和 518K sample/shard/readiness。
3. 做命理师选择 alignment 的长期训练样本。

## 边界

本轮新增能力可以改变：

- 判断权重
- 显示顺序
- 追问优先级
- 训练信号
- final synthesis 排序线索

本轮新增能力不能改变：

- 四柱
- 大运
- 流年
- 出生资料
- 历法换算
- 原始规则事实

这条边界必须长期保持。
