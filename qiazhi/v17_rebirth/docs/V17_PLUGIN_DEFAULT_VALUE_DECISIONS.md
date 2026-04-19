# V17 插件默认值定案（V1）

## 目标

这份文档回答的不是“命理宇宙中的绝对真值”，而是：

1. 在 V17 当前三层物理架构下，哪些默认值可以先定为系统基线。
2. 哪些默认值有较强的古典/约定俗成依据。
3. 哪些默认值本质上仍然是工程化代理量，只能做保守定值，不能假装是古籍原文数值。

## 判定口径

### 来源层级

- `classical_rule`
  传统规则本身可以在公开资料中找到稳定共识，例如十二长生、地支三合/六合/六害/六破、空亡、得令/月令重要性。
- `modern_convention`
  现代命理整理资料中存在较稳定共识，但不是古籍直接给出数值。
- `engineering_proxy`
  参数是为了把传统语义映射到 V17 的能量张量与决策链路，属于工程代理量。

### 裁定标签

- `keep`
  现值可作为系统默认值继续保留。
- `soft_review`
  现值暂可保留，但后续应结合命中率或排序效果复查。
- `case_baseline`
  不建议现在就改，但需要以后结合更多样本做校准。

## 外部参考

以下资料主要用于确认“规则结构”和“语义强弱”，不是为了从网页里直接抄出倍率：

- [地支 - 维基百科](https://zh.wikipedia.org/wiki/%E5%9C%B0%E6%94%AF)
  说明地支、六合、三合局、相破等基础结构。
- [空亡 - 维基百科](https://zh.wikipedia.org/wiki/%E7%A9%BA%E4%BA%A1)
  说明空亡来自旬空配对缺位，语义指向“虚、无、落空”。
- [三合、六合、六冲、六害、相刑 - 易先生](https://www.yixiansheng.com/article/4803.html)
  现代整理资料，明确三合局由长生/帝旺/墓库构成，三合与六合、六害的结构关系较清楚。
- [八字讲解：八字旺衰中什么是得令、得时、得势？ - 搜狐](https://www.sohu.com/a/331451921_120269860)
  现代整理资料，强调月令在旺衰判断中的核心地位，并把长生、沐浴、冠带、临官、帝旺视为“得令”区间。
- [伤官见官讲解 - 搜狐](https://www.sohu.com/a/773661131_121060732)
  现代整理资料，用于确认“伤官克官”的结构语义。
- [八字命理解析：枭神夺食](https://www.tianjimingli.com/smyc/1007.html)
  现代整理资料，用于确认偏印与食神相克的方向性。
- [从命理“羊刃”看企业家领导力](https://dao.ahncjr.com/archives/9598)
  现代整理资料，引用《渊海子平》中的羊刃定义，可用于确认羊刃属于偏激、锋利、应力上扬的结构。
- [天干五合究竟如何影响命运？](https://www.yixiangqiankun.com/130746.htm)
  现代整理资料，用于确认五合化气成立依赖月令与环境支持，不宜默认设成“必然完全转化”。

## 总体结论

- 可以直接从古典/共识规则落地的，是“触发关系”和“方向”：
  十二长生、月令主导、三合/六合/六害/六破、空亡、羊刃、伤官见官、枭神夺食、天干五合、墓库、三刑。
- 不能直接从古籍抄数值的，是“倍率、阈值、优先级”：
  这些都是 V17 把传统语义映射为数值系统后的工程代理量。
- 因此本次定案采用“双轨制”：
  规则型参数尽量顺从传统语义；
  工程型参数优先满足稳定、不过激、可解释。

## 分插件定案

### `l1.physics.op_status`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `RESISTANCE_HIGH` | 1.2 | `classical_rule + engineering_proxy` | `keep` | 长生、冠带、临官、帝旺属强势阶段，1.2 只做温和上调，没有把高位直接推成爆发态。 |
| `RESISTANCE_LOW` | 0.7 | `classical_rule + engineering_proxy` | `keep` | 病、死、绝属衰弱区，0.7 为温和削弱，保留低谷但不至于归零。 |
| `STAGE_PRIORITY` | 0.85 | `engineering_proxy` | `keep` | 状态机是重要背景事实，但不应压过显性结构风险。 |

结论：
- 十二长生的“阶段顺序”有规则依据。
- 1.2 / 0.7 不是古典数字，但符合“强则稍扶、弱则稍抑”的保守工程口径。

### `ten_god_pattern`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `GUAN_THRESHOLD` | 40.0 | `modern_convention + engineering_proxy` | `keep` | 正官主轴比食伤/财星更偏结构性，阈值略高合理。 |
| `SHI_SHANG_THRESHOLD` | 35.0 | `modern_convention + engineering_proxy` | `keep` | 食伤在当前引擎里常较活跃，35 作为主轴门槛较稳。 |
| `CAI_THRESHOLD` | 35.0 | `modern_convention + engineering_proxy` | `keep` | 财星与食伤采用同级门槛，便于维持主轴判断对称性。 |
| `PATTERN_PRIORITY` | 0.78 | `engineering_proxy` | `keep` | 格局应作为标题锚点，但不应压过实体风险与物理事实。 |

结论：
- 月令/旺衰主导格局判断有资料支持。
- 三个阈值是工程切口，不是古典定值；当前分层合理，不建议先动。

### `shensha`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `TIAN_YI_THRESHOLD` | 40.0 | `modern_convention + engineering_proxy` | `case_baseline` | 天乙贵人本质是条件性吉助，40 作为高门槛合理，但仍需看命中率。 |
| `YANG_REN_THRESHOLD` | 45.0 | `modern_convention + engineering_proxy` | `keep` | 羊刃应偏“少而强”，阈值高于天乙是合理的。 |
| `RESISTANCE_BUFF` | 0.1 | `engineering_proxy` | `keep` | 贵人助力宜小幅提升，不宜直接覆盖主物理。 |
| `TENSION_MULTIPLIER` | 1.4 | `modern_convention + engineering_proxy` | `keep` | 羊刃语义本来偏锋利、偏激，1.4 有压迫感但未越过 1.5 警戒线。 |
| `PRIORITY_BASE` | 0.94 | `engineering_proxy` | `soft_review` | 神煞是解释性很强的层，0.94 略高，暂时保留，但应观察是否长期挤压 L1/L2 事实。 |

### `kong_wang`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `VOID_THRESHOLD` | 0.75 | `classical_rule + engineering_proxy` | `keep` | 空亡语义是“落空/虚耗”，0.75 作为比值门槛不算激进。 |
| `EFFICIENCY` | 0.3 | `engineering_proxy` | `keep` | 空亡后的执行效率应明显下降，但不能完全失效，0.3 合理。 |
| `PRIORITY` | 0.82 | `engineering_proxy` | `keep` | 空亡是重要风险背景，但应低于结构性冲突。 |

### `l2.risk.risk_matrix`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `BLADE_CLASH_IMPULSE` | 2.2 | `modern_convention + engineering_proxy` | `keep` | 实际会先除以 10 再钳制，最终有效影响约 0.22，仍属可控。 |
| `OWL_FOOD_CAP` | 0.4 | `modern_convention + engineering_proxy` | `keep` | 既用于偏印压制门槛，也用于负向位移，0.4 仍在稳定上界。 |
| `OFFICER_CRUSH_LIMIT` | 0.5 | `modern_convention + engineering_proxy` | `soft_review` | 伤官见官本就偏激，但 0.5 已到当前允许上限，先保留，后续应观察是否过重。 |

结论：
- 这组不是古籍数值，而是“风险显著度代理量”。
- 目前没有明显越界，但 `OFFICER_CRUSH_LIMIT` 是这组里最值得留意的一个。

### `officer_see_hurt`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `OFFICER_THRESHOLD` | 20.0 | `modern_convention + engineering_proxy` | `keep` | 作为独立结构插件，门槛低于格局插件是合理的。 |
| `HURTING_THRESHOLD` | 16.0 | `modern_convention + engineering_proxy` | `keep` | 伤官比正官更容易先起势，门槛略低合理。 |
| `DEFENSE_CAP` | 0.5 | `engineering_proxy` | `soft_review` | “封锁至 50%” 表达很重，暂可保留，但需要后续看是否过度戏剧化。 |
| `PRIORITY` | 0.94 | `engineering_proxy` | `soft_review` | 作为高风险结构可高优先，但 0.94 已接近顶格。 |

### `l1.physics.op_branch_sanhe`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `FUSION_MID_GAIN` | 1.45 | `classical_rule + engineering_proxy` | `keep` | 三合被视为强协同结构，且现代资料常把它看作强于六合；1.45 合理。 |
| `LOCK_RATIO` | 0.35 | `engineering_proxy` | `keep` | 三合应有绑定效应，但不应把资源完全锁死，0.35 偏稳。 |
| `MIN_HARMONY_STRESS` | 0.4 | `engineering_proxy` | `keep` | 可过滤弱感应命中，避免半合/边缘命中过度泛化。 |

### `l1.physics.op_branch_muku`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `STORAGE_EFFICIENCY` | 0.35 | `classical_rule + engineering_proxy` | `keep` | 墓库语义是收纳、收藏、归藏，0.35 体现明显锁定但不过分。 |
| `OPEN_GATE_BOOST` | 1.5 | `classical_rule + engineering_proxy` | `soft_review` | “开库即释放”符合语义，但 1.5 已到强刺激边界，建议观察实际命中效果。 |

### `l1.physics.op_branch_liuhe`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `HARMONY_GAIN` | 1.15 | `classical_rule + engineering_proxy` | `keep` | 六合应有协同，但通常弱于三合，1.15 与三合的 1.45 拉开了合理梯度。 |
| `STABILITY_WEIGHT` | 0.85 | `engineering_proxy` | `keep` | 六合强调粘合与稳定，0.85 很符合“稳而不爆”的定位。 |

### `l1.physics.op_branch_liupo`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `BREAK_LOSS` | 0.08 | `classical_rule + engineering_proxy` | `keep` | 六破应有损耗，但不应像六冲那样剧烈，8% 较稳。 |
| `FRICTION_COEFF` | 0.25 | `engineering_proxy` | `keep` | 作为干扰项是适中的。 |

### `l1.physics.op_branch_liuhai`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `PENETRATION_RATIO` | 0.45 | `classical_rule + engineering_proxy` | `keep` | 六害偏隐性渗透与牵制，0.45 有明显负面感，但仍可控。 |
| `CLASH_LOSS_RATIO` | 0.12 | `engineering_proxy` | `keep` | 害不应强于冲，0.12 保持了梯度。 |

### `l1.physics.op_stem_fusion`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `TRANSFORM_EFFICIENCY` | 0.85 | `modern_convention + engineering_proxy` | `keep` | 天干五合化气成立需环境支持，0.85 表示“高转化但非满额”很合适。 |
| `STUCK_DAMPING` | 0.35 | `modern_convention + engineering_proxy` | `keep` | 合而不化应表现为牵绊与阻尼，35% 的削减较稳。 |

### `l1.physics.op_branch_sanxing`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `ENTROPY_LOSS` | 0.12 | `classical_rule + engineering_proxy` | `keep` | 三刑可视为秩序耗散与内耗，12% 属于中等负荷。 |
| `PENALTY_PRIORITY` | 0.93 | `engineering_proxy` | `soft_review` | 三刑叙事确实重要，但 0.93 较高，后续应观察是否过多压过其他结构事实。 |

### `l1.physics.full_bandwidth`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `PRIORITY_NORMAL` | 0.62 | `engineering_proxy` | `keep` | 纯通道类事实应低优先。 |
| `PRIORITY_FIERCE` | 0.65 | `engineering_proxy` | `keep` | 比 normal 略高，层次关系清楚。 |

### `narrative_clip`

| 参数 | 默认值 | 来源层级 | 裁定 | 理由 |
| --- | ---: | --- | --- | --- |
| `SEAL_THRESHOLD` | 30.0 | `engineering_proxy` | `keep` | L3 叙事阈值应低于格局主轴阈值，否则 narrative 太难出现。 |
| `WEALTH_THRESHOLD` | 20.0 | `engineering_proxy` | `keep` | 扩张性叙事需要更低门槛合理。 |
| `PRIORITY_STABLE` | 0.85 | `engineering_proxy` | `keep` | 叙事层事实不应高于物理结构层。 |
| `PRIORITY_AGGRESSIVE` | 0.86 | `engineering_proxy` | `keep` | 仅略高于稳定叙事，差值合理。 |

## 本轮定案后的总判断

### 可以直接确认并保留

- `l1.physics.op_status`
- `ten_god_pattern`
- `kong_wang`
- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_branch_liupo`
- `l1.physics.op_branch_liuhai`
- `l1.physics.op_stem_fusion`
- `l1.physics.full_bandwidth`
- `narrative_clip`

### 可以先保留，但应列入下一轮复核

- `shensha.PRIORITY_BASE`
- `l2.risk.risk_matrix.OFFICER_CRUSH_LIMIT`
- `officer_see_hurt.DEFENSE_CAP`
- `officer_see_hurt.PRIORITY`
- `l1.physics.op_branch_muku.OPEN_GATE_BOOST`
- `l1.physics.op_branch_sanxing.PENALTY_PRIORITY`

## 建议的下一步

1. 先不大规模改默认值。
2. 给每个插件补“命中率/平均 impact/排序位置”的运行统计。
3. 把上面 `soft_review` 的 6 个参数纳入下一轮灰度审计。

也就是说：
- 本轮解决“默认值是否站得住”。
- 下一轮再解决“默认值是否要微调”。
