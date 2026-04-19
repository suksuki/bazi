# V17 插件匹配度与重算法

## 目标

把插件命中从“全有或全无”升级成“部分匹配”，同时把插件结算从“顺手叠加”升级成“按已命中插件对 L0 基线重新归算”。

这解决两类问题：

1. 古典规则常常是条件集合，不适合只有命中/未命中两个状态。
2. 刑冲合化、透干、通根、墓库等结构存在先后影响与回看关系，不能简单沿着旧 runtime 继续乘下去。

## 核心协议

### 1. `match_ratio`

插件可在 `fact.meta` 中输出：

- `match_ratio: 0.0 ~ 1.0`

语义：

- `1.0`：高度成立或高度匹配
- `0.6`：部分成立，或仅满足主要条件
- `0.3`：弱匹配，仅作候选或风险提示

当前接线规则：

- `compile_modifier_proposals()` 会把 `impact_ratio` 视为原始位移
- 实际进入 proposal 的 `impact_ratio = raw_impact_ratio × match_ratio`

也就是说：

- `伤官见官` 原始冲击 `-0.4`
- 若匹配度 `0.6`
- 则结算 proposal 只带 `-0.24`

### 2. `base_recompute`

插件统一结算不再默认沿着当前 runtime 继续累乘，而是：

- 以 `ten_gods_base_l0` 为重新计算起点
- 收集当前轮所有通过裁决的 proposal
- 一次性算出新的 `ten_gods_runtime`

这意味着：

- 某个插件是否生效
- 某个插件是否被冲掉
- 某个插件是否因为条件不足降级为 fact-only

都会通过同一轮“重算”反映到 L1，而不是把旧的污染层继续往前推。

## 当前已接线插件

### 量化匹配度

- `l2.risk.risk_matrix`
  - 羊刃逢冲：按冲动事件密度估算匹配度
  - 枭神夺食：按超阈值幅度估算匹配度
  - 伤官见官：按伤官与正官重叠度估算匹配度
- `l1.physics.op_branch_sanhe`
  - 按结构强度与条件状态给出匹配度
- `l1.physics.op_branch_liuhe`
  - 按稳定权重与条件状态给出匹配度
- `l1.physics.op_stem_fusion`
  - 按化气支持度与 `branch_hua_ratio` 给出匹配度
- `l1.physics.op_branch_muku`
  - 按开库/闭库态与条件状态给出匹配度
- `l1.physics.op_branch_liuchong`
  - 按冲动强度给出匹配度
- `l1.physics.op_branch_liupo`
  - 按摩擦系数给出匹配度
- `l1.physics.op_branch_liuhai`
  - 按穿透比率给出匹配度
- `classical.pattern.*`
  - 主轴格、建禄月劫、从势、财官协同都开始输出候选匹配度

### 基线重算

- `l1_meta_hydration.py`
  - 插件统一结算已经切到 `plugin_settlement_mode = base_recompute`
  - 每轮会留下 `plugin_recompute_contributions`
  - 每个贡献项包含 `before / after / ratio_total / delta_abs`

## 设计边界

`match_ratio` 不是“命理真概率”，而是：

- 插件对自己成立程度的量化声明
- 用来削弱过于二元、过于刚性的默认位移

因此：

- 它适合表达“成局程度”“重叠程度”“结构稳定度”
- 不应该伪装成统计学上的真实概率

## 下一步

1. 让更多关系类插件输出 `match_ratio`
2. 给 admin / oracle 显示“命中度 %”
3. 对手动批准后的插件，支持显示“本轮 base_recompute 贡献值”
