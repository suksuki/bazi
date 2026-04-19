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

`configs/` 目录里已覆盖到多数高频插件，包括：

- `l1.physics.op_branch_sanhe.json`
- `l1.physics.op_branch_liuhe.json`
- `l1.physics.op_branch_liupo.json`
- `l1.physics.op_branch_muku.json`
- `l1.physics.op_branch_sanxing.json`
- `l1.physics.op_status.json`
- `l1.physics.op_stem_fusion.json`
- `l2.risk.risk_matrix.json`
- `classical.pattern.axis.v1.json`
- `classical.pattern.jianlu_yuejie.v1.json`
- `classical.pattern.congshi.v1.json`
- `classical.pattern.finance_officer.v1.json`
- `classical.blind.work_axis.v1.json`
- `classical.blind.response_chain.v1.json`
- `classical.blind.symbol_trigger.v1.json`
- `classical.blind.timing_window.v1.json`
- `classical.blind.summary.v1.json`
- `classical.ziping.month_command.v1.json`
- `classical.ziping.balance.v1.json`
- `classical.ziping.yongshen.v1.json`
- `v17_core_constants.json`

这意味着：

- 很多插件已经完成了配置文件就位和读取链条，但仍有一批核心插件（例如 `shensha`、`kong_wang`）暂未补齐配置文件。
- 需要继续把“可读可控”从少数高频插件扩展到全部高价值插件。

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
| `l2.risk.risk_matrix` | 3 | 是 | 是 | 已外置配置并通过 `get_plugin_config` 接入 |
| `classical.pattern.axis.v1` | 8 | 是 | 是 | 参数已外置，阈值/比例可配置 |
| `classical.pattern.jianlu_yuejie.v1` | 2 | 是 | 是 | 参数已外置 |
| `classical.pattern.congshi.v1` | 5 | 是 | 是 | 参数已外置，强度口径可配置 |
| `classical.pattern.finance_officer.v1` | 2 | 是 | 是 | 参数已外置 |
| `classical.pattern.resolver.v1` | 0 | 否 | 否 | 纯规则整合插件 |
| `classical.pattern.formation_gate.v1` | 0 | 否 | 否 | 纯规则整合插件 |
| `classical.pattern.break_guard.v1` | 0 | 否 | 否 | 纯规则整合插件 |
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
8. `classical.pattern.axis.v1`
9. `classical.pattern.congshi.v1`
10. `classical.pattern.finance_officer.v1`

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
| `FUSION_MID_GAIN` | `1.45` | `_collect_rows()` 直接读取并生成聚势增益 | 现已有效 |
| `LOCK_RATIO` | `0.35` | 已接入锁定能量计算，产出 `locked_energy` | 现已有效 |
| `MIN_HARMONY_STRESS` | `0.40` | 已接入命中过滤，低于阈值的半合/三合不产出 facts | 现已有效 |

结论：

- `sanhe` 已从“3 个参数里只活 1 个”整改为“3 个参数全部已接线且可配置”。
- 当前 `MIN_HARMONY_STRESS` 采用的是兼容性实现：优先读 hit 自带 `stress/strength`，若上游未提供，则按三合/半合给安全回退值。后续若 `interaction_v2` 输出更完整的强度字段，可以无缝升级。

### 2. `l1.physics.op_branch_liuhe` 六合协同

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `HARMONY_GAIN` | `1.15` | 主流程已使用，影响六合增益 | 现已有效 |
| `STABILITY_WEIGHT` | `0.85` | 已接入锁定能量与增益折算 | 现已有效 |

结论：

- `liuhe` 已从“半参数化”整改为“双参数真接线”。
- `STABILITY_WEIGHT` 现在不只是文案参数，而会直接影响 `locked_energy` 与 `impact_ratio`。

### 3. `l1.physics.op_branch_liupo` 六破关系

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `BREAK_LOSS` | `0.08` | 主流程已使用，控制六破基础损耗 | 现已有效 |
| `FRICTION_COEFF` | `0.25` | 已接入损耗放大与优先级调节 | 现已有效 |

结论：

- `liupo` 已完成双参数接线，`FRICTION_COEFF` 不再是摆设。
- 当前它表达的是“破局摩擦导致的损耗放大”，后续如果要更细分，可以拆成“损耗”和“决策阻尼”两类参数。

### 4. `l1.physics.op_branch_muku` 墓库门态

| 参数 | 默认值 | 现状 | 判断 |
| --- | ---: | --- | --- |
| `STORAGE_EFFICIENCY` | `0.35` | 主流程已使用，控制墓库回笼收纳强度 | 现已有效 |
| `OPEN_GATE_BOOST` | `1.50` | 已接入开库分支，控制冲开墓库时的正向释放幅度 | 现已有效 |

结论：

- `muku` 已从“只实现闭库”升级为“闭库收纳 + 开库释放”双态模型。
- 当前开库触发基于 `interaction_v2.liu_chong` 命中墓库支，后续如要更细分，可继续纳入刑、破等开门条件。

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

2. `l1.physics.op_branch_liuhai`
原因：已整改完成，现支持配置读取与全局常量引用解析，可作为 `ref(global.KEY)` 的治理模板。

3. `l1.physics.op_status`
原因：已补同名配置文件，并统一回正式 `plugin_id`，当前主要工作转向默认值案例基线。

4. `ten_god_pattern`
原因：已补同名配置文件，当前主要工作转向阈值基线与案例校准。

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

## 第二批规范化进展

以下插件已完成“同名配置文件补齐”：

- `l1.physics.op_status`
- `ten_god_pattern`
- `shensha`
- `kong_wang`

其中：

- `l1.physics.op_status` 还额外完成了历史遗留规范化：
  - facts 内的 `plugin` 已从旧别名 `chang_sheng_12` 统一回正式 `l1.physics.op_status`
- `ten_god_pattern / shensha / kong_wang` 原本参数就已接线，这次重点是把它们从“默认值驱动”升级为“标准配置治理”

当前这四支的工作重点，已经不再是“有没有接线”，而是：

- 默认值是否合理
- 阈值是否过宽或过窄
- 是否需要更细的案例基线

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
