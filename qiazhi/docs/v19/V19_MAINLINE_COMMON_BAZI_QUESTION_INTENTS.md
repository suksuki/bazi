# V19 Mainline Common Bazi Question Intents

## 目标

把命理用户最常问、但容易被泛化模型误处理的问题，纳入显式问题意图注册表：

- 身强身弱 / 日主强弱 / 旺衰
- 用神 / 忌神 / 喜神 / 喜用
- 格局 / 成格 / 破格
- 财、官、印、食伤等十神优先观察入口

这些问题不能依赖训练自然“长出来”。训练和静默进化可以负责排序、个性化和表达优化，但基础问法必须先有稳定的 intent、answer_kind、answer_scope 和禁止边界。

## 主线边界

新增问题只回答结构证据，不给断语：

- 强弱问题输出“证据束”，不直接断强弱结论。
- 用神忌神输出“候选路径”，不输出改运建议。
- 格局问题输出“结构索引”，不输出吉凶定论。
- 十神焦点问题只说明当前优先观察关系。

## 个性化排序

排序规则调整为：

```text
具体结构命中 / Rule Graph 动态问题
→ 常用基础命理问题
→ 通用兜底问题
```

这样可以避免“常用问题”把已经命中的收入、地支、十神互动等具体路径挤掉。

## Rule Graph 路由

常用问题已经接入规则图意图：

- `strength_assessment`：优先走 `core_strength_foundation`，再参考 `ten_god_mechanism` 和 `branch_time_activation`。
- `useful_god_boundary`：优先走 `core_strength_foundation`，再参考 `ten_god_mechanism`、`pattern_structure` 和时间结构。
- `pattern_structure`：走格局、十神和强弱基础路径。
- `metadata_boundary` / 十神焦点：走强弱基础、十神机制和地支时间路径。
- `time_boundary`：继续只作为时间背景，不改写本命结构。

## UI 对齐

前端首屏问题来源以后台 `guided_question_context.questions` 为准；后台不可用时，静态 fallback 库也包含强弱、用神、格局和十神焦点入口。

首屏排序仍然由命盘结构决定：命中地支、时间、十神互动、收入路径等具体结构时，这些具体问题优先；常用命理问题作为基础入口进入前十，不固定占据第一位。

## 验证

新增回归覆盖：

- 常用问题进入推荐列表前十。
- 手写问题“这个八字是强还是弱”“用神是什么”“格局怎么看”能路由到对应 answer_kind。
- Rule Graph 对同三类问题返回对应 question intent。
- 回答包含证据束、候选路径、结构索引。
- 回答不出现发财、破财、必然、应期等断语。
- 合成盘矩阵前五推荐问题保持差异，不会每个八字推荐同一组静态问题。
- UI fallback 库和缓存版本已包含新入口。
- P71 Runtime Rule DB 动态问题仍能进入前十，证明通用问题不会压掉具体规则路径。
