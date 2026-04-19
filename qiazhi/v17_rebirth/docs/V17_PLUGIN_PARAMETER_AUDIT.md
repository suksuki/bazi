# V17 插件参数审计（第一轮）

## 结论先行

当前最应该做的，不是让插件参数“自我学习”，而是先把参数系统整理成一套可信的工程契约：

1. 先确认参数有没有被真正使用。
2. 再确认它是不是能被配置覆盖。
3. 最后才讨论默认值是否合理。

这三件事里，前两件现在比第三件更紧急。因为如果参数根本没被读取，或者配置文件根本加载不到，讨论默认值优化没有意义。

## 当前审计结论

### A. 配置能力本身还不可靠

`get_plugin_config(plugin_id)` 只会读取：

`backend/logic/configs/<plugin_id>.json`

但当前 `configs/` 目录里只有：

- `three_harmony.json`
- `v17_core_constants.json`

其中 `three_harmony.json` 并不会被 `l1.physics.op_branch_sanhe` 自动读取，因为它期待的路径应当是：

`backend/logic/configs/l1.physics.op_branch_sanhe.json`

这意味着：

- 大多数插件虽然代码写了 `get_plugin_config(...)`
- 但运行时实际上仍然在吃 `DECLARED_PARAMS`
- 参数“看起来可配置”，实际上多数仍是“伪可配置”

### B. 多个插件存在“声明了参数，但实际未消费”的情况

第一轮人工抽查里，已经确认几类典型问题：

| 插件 | 参数 | 现状 |
| --- | --- | --- |
| `l1.physics.op_branch_sanhe` | `LOCK_RATIO`, `MIN_HARMONY_STRESS` | 已声明，但当前 `_collect_rows()` 未使用 |
| `l1.physics.op_branch_muku` | `OPEN_GATE_BOOST` | 已声明，但当前只使用 `STORAGE_EFFICIENCY` |
| `l1.physics.op_branch_liupo` | `FRICTION_COEFF` | 已声明，但当前未进入事实计算 |
| `l1.physics.op_branch_liuhe` | `STABILITY_WEIGHT` | 已声明，但当前未进入事实计算 |
| `l2.risk.risk_matrix` | `BLADE_CLASH_IMPULSE`, `OWL_FOOD_CAP`, `OFFICER_CRUSH_LIMIT` | 已声明，但当前逻辑仍然直接写死判断阈值与 impact |

这类参数现在会制造很大的认知噪音：

- 文档以为它存在
- 配置以为它能调
- 实际运行根本没用到

所以这类参数要么接入逻辑，要么删掉，不适合继续悬空。

### C. 默认值目前只能做“工程合理”，很难直接做“命理最优”

这个判断我认同你的直觉：

- 八字不是一个有标准答案的大规模监督学习问题
- 用户反馈往往是叙事满意度，不是物理真值
- 同一命盘的解释空间本身很大

所以插件参数不适合直接做“自动学习后替换默认值”的闭环，尤其是：

- 阈值类参数
- 做功倍率类参数
- 格局触发边界
- 抗性与折损系数

这些更适合通过：

- 规则一致性
- 数值稳定性
- 人工对照案例
- 小规模离线回放

去慢慢校正，而不是在线自进化。

## 参数分层建议

建议把插件参数分成三层：

### P0：物理常数型

例如：

- `FUSION_MID_GAIN`
- `BREAK_LOSS`
- `STORAGE_EFFICIENCY`
- `DEFENSE_CAP`

特点：

- 直接影响十神 runtime 或物理 proposal
- 不应该在线学习自动改写
- 只允许人工审定 + 离线回放验证

### P1：结构阈值型

例如：

- `OFFICER_THRESHOLD`
- `HURTING_THRESHOLD`
- `GUAN_THRESHOLD`
- `VOID_THRESHOLD`

特点：

- 决定插件是否命中
- 可以做离线校准，但不建议在线自适应
- 可以引入“建议阈值”，但不能自动生效

### P2：叙事优先级型

例如：

- `PRIORITY`
- `PATTERN_PRIORITY`
- `PRIORITY_STABLE`
- `PRIORITY_AGGRESSIVE`

特点：

- 更接近编排与提示词策略
- 适合未来做智能优化
- 可以通过用户行为、冲突路由、计划通过率做渐进调整

真正适合“学习”的，主要是 P2，不是 P0/P1。

## 建议的智能优化方向

与其让系统学习“八字参数真值”，不如让系统学习这些更可验证的智能层：

1. 学习哪些插件组合更容易冲突。
2. 学习哪些 decision 应该自动批处理，哪些必须手动。
3. 学习哪些 facts 更值得进入 Prompt。
4. 学习不同 Prompt 组织方式对断言质量的影响。
5. 学习什么情况下不该调用 LLM。

这些方向比“自动调 `OFFICER_THRESHOLD` 从 20 调到 18.7”更现实，也更安全。

## 第一轮参数台账

以下按“声明参数数 + 是否读取配置 + 当前配置文件是否存在”做首轮盘点。

| 插件 | 参数数 | 代码读取配置 | 有效配置文件 | 初步结论 |
| --- | ---: | --- | --- | --- |
| `l1.physics.op_branch_sanhe` | 3 | 是 | 否 | 实际仍吃默认值；且有未消费参数 |
| `l1.physics.op_branch_liuhe` | 2 | 是 | 否 | 实际仍吃默认值；存在未消费参数 |
| `l1.physics.op_branch_liupo` | 2 | 是 | 否 | 实际仍吃默认值；存在未消费参数 |
| `l1.physics.op_branch_muku` | 2 | 是 | 否 | 实际仍吃默认值；存在未消费参数 |
| `l1.physics.op_stem_fusion` | 2 | 是 | 否 | 需进一步核对参数是否全部接线 |
| `l1.physics.op_status` | 3 | 是 | 否 | 实际仍吃默认值；属于观察型参数 |
| `l2.risk.risk_matrix` | 3 | 否 | 否 | 参数已声明但当前未真正接入读取链 |
| `officer_see_hurt` | 4 | 是 | 否 | 可配置结构完整，但当前无配置文件 |
| `ten_god_pattern` | 4 | 是 | 否 | 可配置结构完整，但当前无配置文件 |
| `shensha` | 5 | 是 | 否 | 参数较多，适合下一轮重点审计 |
| `kong_wang` | 3 | 是 | 否 | 可配置结构完整，但当前无配置文件 |
| `narrative_clip` | 4 | 是 | 否 | 更适合未来做策略优化而非命理学习 |

## 下一步建议

### Step 1：先做“参数活性审计”

把每个 `DECLARED_PARAMS` 标记成三类：

- `used_and_configurable`
- `used_but_hardcoded`
- `declared_but_unused`

这一步优先级最高。

### Step 2：统一配置文件命名

把插件配置文件统一到：

`backend/logic/configs/<plugin_id>.json`

否则“可配置”永远只是表面契约。

### Step 3：只为高价值插件建立默认值基线

优先顺序建议：

1. `l1.physics.op_branch_sanhe`
2. `l1.physics.op_branch_liuhe`
3. `l1.physics.op_branch_liupo`
4. `l1.physics.op_branch_muku`
5. `l2.risk.risk_matrix`
6. `officer_see_hurt`
7. `ten_god_pattern`

## 第二轮：五个高价值插件的参数活性审计

本轮已对下面五个插件做逐参数审计：

- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_branch_liupo`
- `l1.physics.op_branch_muku`
- `l2.risk.risk_matrix`

分类口径如下：

- `used_and_configurable`：代码已使用，且已有同名配置文件可覆盖。
- `used_but_no_config_file`：代码已使用，但当前没有对应配置文件，实际仍吃默认值。
- `used_but_hardcoded`：代码已使用，但没有走配置读取。
- `mentioned_but_not_wired`：参数被声明或提到，但没有接入实际计算。
- `declared_but_unused`：参数只存在于声明里，运行逻辑不读它。

### 1. `l1.physics.op_branch_sanhe` 三合成局

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `FUSION_MID_GAIN` | `1.45` | `_collect_rows()` 直接读取并生成 `impact_ratio` | 默认值暂时合理，建议保留 |
| `LOCK_RATIO` | `0.35` | 只在 `run_three_harmony()` 中出现，主流程未接线 | 当前是伪参数 |
| `MIN_HARMONY_STRESS` | `0.40` | 主流程完全未读取 | 当前是伪参数 |

结论：

- 真正生效的只有 `FUSION_MID_GAIN`。
- `LOCK_RATIO` 和 `MIN_HARMONY_STRESS` 要么接入 `interaction_v2` 判定与位移计算，要么删掉，避免误导。

### 2. `l1.physics.op_branch_liuhe` 六合协同

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `HARMONY_GAIN` | `1.15` | 主流程已使用，影响六合增益 | 默认值暂时合理 |
| `STABILITY_WEIGHT` | `0.85` | 仅在声明中存在，未进入 `_collect_rows()` | 当前是伪参数 |

结论：

- `HARMONY_GAIN` 是有效参数。
- `STABILITY_WEIGHT` 当前没有任何做功路径，先不要把它当成真实可调项。

### 3. `l1.physics.op_branch_liupo` 六破关系

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `BREAK_LOSS` | `0.08` | 主流程已使用，直接映射为负向 `impact_ratio` | 默认值暂时合理 |
| `FRICTION_COEFF` | `0.25` | 只在注释与声明层存在，未进入计算 | 当前是伪参数 |

结论：

- `BREAK_LOSS` 是真实有效参数。
- `FRICTION_COEFF` 应当 either 接入平滑/阻尼模型，or 从当前版本移除。

### 4. `l1.physics.op_branch_muku` 墓库门态

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `STORAGE_EFFICIENCY` | `0.35` | 主流程已使用，影响墓库回笼收纳强度 | 默认值暂时合理 |
| `OPEN_GATE_BOOST` | `1.50` | 当前没有开库分支，未进入计算 | 当前是伪参数 |

结论：

- 现阶段插件只实现了“闭库收纳”，没有实现“开库释放”。
- 因此 `OPEN_GATE_BOOST` 现在只是未来设计，不应被当成已生效参数。

### 5. `l2.risk.risk_matrix` 官伤风险矩阵

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `BLADE_CLASH_IMPULSE` | `2.2` | 已接入配置读取，控制羊刃逢冲的 `impact_ratio` 幅度 | 现已有效 |
| `OWL_FOOD_CAP` | `0.4` | 已接入配置读取，控制枭神夺食的触发门槛与负向位移幅度 | 现已有效 |
| `OFFICER_CRUSH_LIMIT` | `0.5` | 已接入配置读取，控制伤官见官的负向位移幅度 | 现已有效 |

结论：

- `risk_matrix` 已从“声明参数但实际硬编码”整改为“已接线且可配置”。
- 当前仍保留部分经验阈值，例如伤官见官的基础触发值 `10.0 / 10.0`，后续若继续细化，应新增显式阈值参数，而不是再回到硬编码。

## 当前优先级排序

建议按下面顺序进入修整：

1. `l2.risk.risk_matrix`
原因：已整改完成，现可作为参数治理模板。

2. `l1.physics.op_branch_sanhe`
原因：表面上有 3 个参数，实际上只用了 1 个，容易误导后续调参。

3. `l1.physics.op_branch_muku`
原因：开库参数尚未实现，设计语义与当前代码不一致。

4. `l1.physics.op_branch_liuhe`
原因：`STABILITY_WEIGHT` 未接线，但主逻辑相对简单。

5. `l1.physics.op_branch_liupo`
原因：`FRICTION_COEFF` 未接线，但核心损耗逻辑已成立。

## 关于“自我学习调参数”的最终判断

这轮审计之后，这个结论更清楚了：

- 不建议把物理插件参数作为近期自学习目标。
- 至少在参数系统还存在“伪可配置”“声明未接线”的阶段，任何自动调参都会把错误结构学得更乱。

更适合优先学习的仍然是：

- 冲突检测与冲突裁决
- decision 批处理与路由
- facts 进入 Prompt 的筛选
- LLM 调用时机
- 叙事组织质量

参数本身更适合走：

- 工程清洗
- 离线回放
- 人工基线校准

## 已补工具

已新增脚本：

[`scripts/audit_plugin_params.py`](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/audit_plugin_params.py)

用途：

- 扫描插件 `DECLARED_PARAMS`
- 判断是否调用 `get_plugin_config`
- 判断目标配置文件是否存在
- 输出参数台账 JSON

运行方式：

```bash
python3 /Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/audit_plugin_params.py
```

---

这份文档的定位不是最终定案，而是把“参数问题”从模糊感受，变成一张可以逐项清理的工程清单。
