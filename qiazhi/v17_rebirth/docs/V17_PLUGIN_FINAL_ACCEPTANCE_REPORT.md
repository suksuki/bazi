# V17 插件体系终验报告

## 验收结论

本轮插件重构已达到“可验收”状态。

结论不是“所有命理专题都已经做到终局版本”，而是：

1. 插件家族已经成体系。
2. 关键缺失插件已补齐为正式入口。
3. 条件不足不会再偷偷穿透到物理 proposal。
4. 格局候选已具备进入冲突层的法理身份。
5. L0 基础物理不再隐身。

换句话说，插件层已经从“散乱的规则堆”升级成“有家族、有层级、有条件、有冲突处理”的体系。

## 本轮完成内容

### 1. 家族化完成

已形成下列插件家族：

- L0 基础插件家族
- L1 关系插件家族
- 子平/旺衰插件家族
- 格局插件家族
- 盲派插件家族
- 风险 / 冲突插件家族

对应设计文档：

- [V17_PLUGIN_FAMILY_REFACTOR_PLAN.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_FAMILY_REFACTOR_PLAN.md)

### 2. 缺失核心插件补齐

本轮补齐的重要正式插件包括：

- `l0.foundation.hidden_stems.v1`
- `l0.foundation.rooted_stems.v1`
- `l0.foundation.exposed_hidden_stems.v1`
- `l0.foundation.month_command.v1`
- `l1.physics.op_branch_liuchong`
- `classical.blind.work_axis.v1`
- `classical.blind.response_chain.v1`
- `classical.blind.symbol_trigger.v1`
- `classical.blind.timing_window.v1`
- `classical.blind.summary.v1`
- `classical.ziping.month_command.v1`
- `classical.ziping.balance.v1`
- `classical.ziping.yongshen.v1`
- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`
- `classical.pattern.resolver.v1`
- `classical.pattern.formation_gate.v1`
- `classical.pattern.break_guard.v1`

### 3. 合化专题完成第一阶段硬化

已经做到：

- 插件具备 `condition_state`
- 条件状态会影响强度
- 条件不足时不再产出可结算 proposal

已接入条件协议的核心插件：

- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_stem_fusion`
- `l1.physics.op_branch_muku`

### 4. 格局专题完成第一阶段闭环

已经做到：

- 候选
- 裁决
- 成格
- 破格
- 互斥候选进入冲突层

这意味着格局不再只是一个单标签插件，而是已经具备专题结构。

### 5. 冲突层完成插件法理接线

已经做到：

- `pattern_candidate` 可以以互斥家族身份进入冲突层
- `pattern_family_exclusive` 已进入冲突检测
- 关系类插件可以因为条件不足而只保留 fact、不再生成 proposal

## 当前可确认的能力

### 插件扫描与发现

- 自动扫描可发现新老插件
- 插件已按层级排序执行
- 新插件已有发现性测试保护

### 参数治理

本轮活跃参数审计结果显示：

- 核心物理插件参数均为 `used_and_configurable`
- 已参数化的关系类/风险类插件均具备配置入口

参数审计文档：

- [V17_PLUGIN_PARAMETER_AUDIT.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_PARAMETER_AUDIT.md)
- [V17_PLUGIN_DEFAULT_VALUE_DECISIONS.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_DEFAULT_VALUE_DECISIONS.md)

### 插件显示与可读性

新插件家族的显示名、定义和说明已接入统一展示层：

- [plugin_display.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/services/plugin_display.py)

所以 admin / oracle 视图里，插件不再只是技术 ID。

## 仍然保留的后续项

这些不阻塞本轮插件验收，但属于下一阶段深化：

1. 盲派如果继续深化，可以再扩成更细的专项断口，但当前“做功 / 应期 / 象法 / 收束”链已经齐备。
2. 格局候选进入冲突层后，进一步把 winner / dropped 结果更直接投影回专题插件。
3. 合化专题继续向“条件不足时不仅不出 proposal，连 effect 文案也进一步分型”推进。

## 终验证据

本轮插件相关测试已通过：

- `python3 -m pytest v17_rebirth/tests/test_plugin_family_discovery.py v17_rebirth/tests/test_plugin_condition_protocol.py v17_rebirth/tests/test_spec_validator.py -q`

结果：

- `11 passed`

语法校验已通过：

- `py_compile` 通过

## 最终判断

如果以“插件体系是否已经从混乱状态进入可维护、可扩展、可审计状态”为标准，
那么答案是：**已经完成。**

如果以“所有命理专题都已经做到最终学术形态”为标准，
那么答案是：**还没有，但这已经不是插件基础设施问题，而是专题深化问题。**
