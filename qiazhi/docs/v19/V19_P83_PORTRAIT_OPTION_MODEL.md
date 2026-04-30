# V19 P83 画像选项模型

## 目标

P83 修正 P82 的产品问题：画像不能只停留在“候选标签”和“问答式校准”。系统需要生成可选择、可确认、可回流的画像选项。

```text
命盘事实 / 规则图路径
→ 标签本体
→ 画像选项生成器
→ 用户 / 命理师直接选择
→ confirmed_portrait_assertions
→ 推荐问题 / 回答证据包
```

## 画像选项

每个画像标签都会生成 `selection_options`：

- `option_id`
- `title`
- `detail`
- `score`
- `evidence_refs`
- `selection_state`
- `boundary`

选项示例：

- 强弱：承载偏强、承载偏弱、中和待辨；
- 用神：先看扶身路径、先看输出通关、先看约束秩序、暂不定喜忌；
- 财富：财星可见、财弱或隐藏、食伤生财入口、财受牵制、财富波动明显；
- 地支：本命结构张力、时间层触发、地支关系较静；
- 格局：格局索引已建立、成格条件待验、破格条件待验、暂不以格局为主。

这些选项是画像，不是命运断语。

## 确认机制

Oracle 不再把校准入口做成问答，而是直接显示选项按钮：

- 用户选择“最像自己的那一项”；
- 命理师选择“最成立的命理画像”；
- 选择进入 `portrait_calibration` feedback；
- 后端按 `profile_id` 和 `option_id` 汇总。

正向选择会把选项状态推向：

- `user_confirmed`
- `analyst_confirmed`

并生成 `confirmed_portrait_assertions`。

## 边界

- 选择画像不改命盘事实；
- 选择画像不改规则库；
- 选择画像不直接产生喜忌、吉凶、应期或财富结果；
- 选择画像只影响个性化画像排序、推荐问题和回答证据路径。

## 验收

- 每个合成盘产生画像选项；
- 每个重点标签有 `selected_option`；
- UI 显示选项按钮而不是问答 hook；
- option feedback 进入 `by_option` 汇总；
- 确认后生成 `confirmed_portrait_assertions`；
- 回答证据包携带画像选项和确认画像；
- 回归测试不出现 forbidden text。
