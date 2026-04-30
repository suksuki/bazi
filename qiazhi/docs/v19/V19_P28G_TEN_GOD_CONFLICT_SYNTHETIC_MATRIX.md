# V19 P28G 十神冲突专题合成矩阵

状态：已建立可运行矩阵

日期：2026-04-30

## 目标

为“十神冲突 / 牵制 / 混杂专题”建立合成盘碰撞矩阵，用来检查 P28E + P28F + P31B 相关十神机制的 48 条候选知识是否真正进入 Rule DB，并且保持候选未启用。

本阶段不验证真实命盘准确性，也不启用断语，只验证：

- 候选知识是否齐全。
- Rule DB 映射是否正确。
- 是否仍然禁止传统断语。
- 哪些对象只能进入条件模型，不能直接启用。

## 矩阵范围

矩阵共 24 个合成案例，每个案例对应 2 条知识：

| 分组 | 对象 |
|---|---|
| 直接冲突 | 伤官见官、伤官制杀、食神制杀、官杀攻身 |
| 夺破牵制 | 枭神夺食、印制食伤、比劫夺财、比劫分财、财破印、财多坏印、财滋杀 |
| 混杂 | 官杀混杂、食伤混杂、印枭混杂 |
| 去留 / 救应 / 路径 | 合杀留官、合官留杀、伤官配印、杀印相生、印化杀、官印相生、财生官、财官相生、食伤生财、羊刃驾杀 |

对应知识总数：

```text
24 cases * 2 knowledge drafts = 48 Rule DB candidates
```

## 运行入口

```text
v19.synthetic_validation.ten_god_conflict_matrix.run_p28g_ten_god_conflict_matrix
```

矩阵数据：

```text
v19.synthetic_validation.ten_god_conflict_matrix.P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES
```

## 验收标准

每个案例必须满足：

- 两条对应知识都存在于 Rule DB。
- 规则领域为 `ten_god_relation`。
- 规则类别为 `ten_god_interaction` 或 `ten_god_interaction_mechanism`。
- `engine_enabled` 必须为 `false`。
- `forbidden_usage` 必须包含 `fortune` 或 `direct_fortune_output`。

## 当前判断

P28G 只允许把这些知识保持在候选层：

- R1 组合存在：未来可在专题合成回归后进入低风险结构信号。
- R2 机制边界：必须等来源层、强弱、宫位、时间层条件模型完成。
- 传统断语：归档，不直接输出。

## 下一步

P28H：把 P28G 里的 24 个案例拆成可视化 review 表，标注每个对象的：

- 可立即规则化部分。
- 条件模型缺口。
- 合成盘需要增加的碰撞点。
- 禁止进入回答层的传统断语。
