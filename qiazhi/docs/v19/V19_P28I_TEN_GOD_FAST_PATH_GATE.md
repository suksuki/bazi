# V19 P28I 十神组合快审门禁

## 目标

P28I 把 P28H 标出的 4 条低风险“组合存在”候选接入自动快审门禁，用合成盘验证它们能否从知识库进入规则库信号层。

本阶段只处理 R1 存在类规则：

- 伤官见官组合存在
- 比劫分财组合存在
- 食伤混杂组合存在
- 印枭混杂组合存在

机制解释、格局成败、传统断语和应事结论继续留在规则候选或资料归档层。

## 快审条件

每条候选必须同时满足：

- 风险等级为 R1。
- Rule DB 记录存在，状态为 active_in_rule_db。
- domain 为 ten_god_relation，category 为 ten_god_interaction。
- confidence 不低于 0.72。
- allowed_usage 包含 rule_db 与 engine_adapter_candidate。
- forbidden_usage 至少阻断 fortune 或 direct_fortune_output。
- structured_facts 必须包含 interaction_name 与 involved_ten_gods。

## 适配器修正

P28I 同步修正了十神组合规则的匹配方式：十神组合不再允许通过宽泛的 ten_god_relation 兜底命中，必须匹配 involved_ten_gods 中的具体十神标签。

新增匹配边界：

- 伤官见官需要可见层同时出现伤官与正官。
- 比劫分财需要可见层出现比劫类信号与财星类信号。
- 食伤混杂需要可见层同时出现食神与伤官。
- 印枭混杂需要可见层同时出现正印与偏印。

这样可以避免藏干中的弱背景信号把专题规则误触发为主问题。

## 合成验证

P28I 对 4 个 fast-path 合成盘做模拟启用验证：

| 合成盘 | 预期命中 | 结果 |
| --- | --- | --- |
| syn.p28g.shangguan_see_official | p28.interaction.shangguan_see_official.existence | pass |
| syn.p28g.peer_share_wealth | p28.interaction.peer_share_wealth.existence | pass |
| syn.p28g.output_mixed | p28.interaction.output_mixed.existence | pass |
| syn.p28g.resource_mixed | p28.interaction.resource_mixed.existence | pass |

审计结论：

- 4 条候选均可进入快审启用。
- 每个合成盘只命中自己的 fast-path 规则。
- 没有启用 mechanism_boundary。
- 没有引入官非、灾祸、发财、破财等传统断语。

## 输出

代码入口：

```text
v19.synthetic_validation.ten_god_conflict_matrix.run_p28i_ten_god_fast_path_gate
```

默认 dry-run；传入 activate=True 时才会把通过门禁的 4 条规则标记为 p28i_fast_path_active。

## 下一步

P28J 开始处理非 fast-path 的 18 条十神组合机制候选。它们不能直接启用，需要先补来源层、强弱承载、救应、宫位与时间层条件模型。
