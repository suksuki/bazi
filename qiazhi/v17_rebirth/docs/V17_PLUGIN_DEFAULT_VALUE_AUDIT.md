# V17 插件默认值审计框架

## 审计目标

默认值审计不追求“命理真值”，而追求三件事：

1. 数值量纲是否自洽。
2. 在当前物理链路下是否容易失真或失控。
3. 作为工程默认值，是否足够稳健。

## 审计口径

每个参数默认值统一按下面四档判断：

- `reasonable_default`
  量纲自洽，作为工程默认值可接受。
- `too_aggressive`
  默认值偏大，容易放大冲突或放大位移。
- `too_conservative`
  默认值偏小，容易让插件失去存在感。
- `needs_case_baseline`
  数值本身未明显失衡，但缺少足够案例基线，暂不宜拍板。

## 参数分层

### A. 物理倍率类

典型参数：

- `FUSION_MID_GAIN`
- `OPEN_GATE_BOOST`
- `TENSION_MULTIPLIER`
- `BLADE_CLASH_IMPULSE`

审计重点：

- 是否会把 `impact_ratio` 推到过激区间
- 是否会叠加后越过护栏
- 是否会导致单插件成为全局支配项

经验原则：

- 倍率 > `1.5` 要重点复查
- 倍率 < `1.05` 要确认是否还有存在意义

### B. 损耗/效率类

典型参数：

- `BREAK_LOSS`
- `STORAGE_EFFICIENCY`
- `EFFICIENCY`
- `OFFICER_CRUSH_LIMIT`
- `CLASH_LOSS_RATIO`

审计重点：

- 是否落在 `0.0 ~ 1.0` 的稳定区间
- 是否与输出的 `impact_ratio` 方向一致
- 是否存在“名字像比例，实际像倍率”的语义混乱

经验原则：

- 默认放在 `0.05 ~ 0.4` 通常更稳
- 超过 `0.5` 默认要高度警惕

### C. 阈值类

典型参数：

- `GUAN_THRESHOLD`
- `SHI_SHANG_THRESHOLD`
- `CAI_THRESHOLD`
- `VOID_THRESHOLD`
- `TIAN_YI_THRESHOLD`
- `YANG_REN_THRESHOLD`

审计重点：

- 命中率会不会过高或过低
- 是否和当前十神数值尺度匹配
- 是否导致插件长期“常开”或“常闭”

经验原则：

- 十神能量阈值要结合当前 runtime 常见区间看
- 比值阈值通常检查 `0.5 ~ 1.5` 是否更自然

### D. 优先级类

典型参数：

- `STAGE_PRIORITY`
- `PATTERN_PRIORITY`
- `PRIORITY_BASE`
- `PRIORITY`

审计重点：

- 是否挤压其他插件排序
- 是否使叙事型插件长期压过物理型插件

经验原则：

- `0.75 ~ 0.9` 一般是安全带
- 接近 `0.95` 以上需要确认是否真是“高优先级事实”

## 当前建议的审计顺序

### 第一批：最该先看

1. `l1.physics.op_status`
原因：参数都已接线，但默认值直接影响抗性表达与节律叙事。

2. `ten_god_pattern`
原因：阈值会决定格局标签的命中频率，是叙事主轴入口。

3. `shensha`
原因：阈值和倍率混合存在，容易出现“常亮”或“过度放大”。

4. `kong_wang`
原因：比值阈值和效率值需要结合实际命中率看是否偏激。

### 第二批：继续细化

1. `l2.risk.risk_matrix`
2. `l1.physics.op_branch_sanhe`
3. `l1.physics.op_branch_muku`
4. `l1.physics.op_branch_liuhe`
5. `l1.physics.op_branch_liupo`
6. `l1.physics.op_branch_liuhai`

## 审计输出模板

后续每个插件默认值审计统一按这个格式落：

```md
### 插件：<plugin_id>

| 参数 | 默认值 | 类型 | 当前判断 | 备注 |
| --- | ---: | --- | --- | --- |
| XXX | 0.85 | 优先级 | reasonable_default | 与同层插件排序相容 |
| YYY | 45.0 | 阈值 | needs_case_baseline | 缺少命中率样本 |

结论：
- ...
- ...
```

## 当前判断边界

这份审计不直接宣布“命理上正确”，只判断：

- 是否适合作为 V17 当前架构下的默认值
- 是否需要保守下调/上调
- 是否必须拿更多案例才能定

也就是说，它是一份工程默认值审计，不是假装解决“八字真值不可知”问题。
