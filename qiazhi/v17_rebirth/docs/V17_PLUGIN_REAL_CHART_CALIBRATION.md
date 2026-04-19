# V17 真实盘插件校准

## 目标

在已经具备：

- `match_ratio`
- `base_recompute`
- `plugin_recompute_contributions`

之后，用少量真实盘样本去看三个问题：

1. 插件命中度看起来像不像人话。
2. 插件重算贡献是否过强或过弱。
3. 哪些插件的量化仍然明显偏硬编码。

## 当前校准工具

脚本：

- [calibrate_plugin_match_cases.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/calibrate_plugin_match_cases.py)

运行方式：

```bash
python3 /Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/calibrate_plugin_match_cases.py
```

输出内容：

- 每个样盘的四柱 / 大运 / 流年
- 插件 `match_ratio` 最高的主张
- 按插件聚合的平均命中度
- `plugin_recompute_contributions`

## 当前样盘

第一批样盘偏向“结构校准”而不是“命理定论”：

1. `1977-05-08 18:00`
   - 这就是当前主测盘，适合观察：
   - `三合`
   - `伤官见官`
   - `盲派/子平/格局` 命中度

2. `1982-11-15 05:30`
   - 用于观察冬令格局与官财结构

3. `2024-01-01 12:00`
   - 作为较中性的基线测试盘

## 校准口径

### 一. 命中度口感

优先看这些区间是否合理：

- `0.80 ~ 1.00`
  - 高度成立，通常应该是“强命中”
- `0.60 ~ 0.79`
  - 主要条件已满足，但未到非常强
- `0.35 ~ 0.59`
  - 弱成立或候选态
- `< 0.35`
  - 只适合作为提示，不适合强介入结算

### 二. 重算贡献

优先看：

- `delta_abs`
  - 是否明显超过同层其他插件
- `ratio_total`
  - 是否因为多个插件同向叠加而偏大
- `before → after`
  - 是否符合“从 L0 基线重算”的预期

### 三. 插件优先级

如果一个插件出现：

- `match_ratio` 很高
- 但 `delta_abs` 几乎没有

说明它更像“解释插件”。

如果一个插件出现：

- `match_ratio` 不高
- 但 `delta_abs` 很大

说明它的原始 `impact_ratio` 仍然过猛。

## 当前最值得继续校准的插件

1. `l2.risk.risk_matrix`
2. `l1.physics.op_branch_sanhe`
3. `l1.physics.op_stem_fusion`
4. `classical.pattern.*`
5. `classical.blind.*`

原因：

- 这些插件已经有了 `match_ratio`
- 同时又会对解释或结算产生真实影响

## 下一步

1. 增加更多真实盘样本
2. 给校准脚本增加“按插件聚合平均命中度”
3. 对明显偏硬的插件继续细化公式
