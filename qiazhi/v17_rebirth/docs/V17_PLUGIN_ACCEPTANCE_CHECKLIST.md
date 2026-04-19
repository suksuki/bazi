# V17 插件验收清单

## 验收范围

本清单只覆盖插件体系，不覆盖 UI、LLM、自动化、叙事编排等外围链路。

## 家族级验收

### L0 基础插件家族

- [x] `l0.foundation.hidden_stems.v1`
- [x] `l0.foundation.rooted_stems.v1`
- [x] `l0.foundation.exposed_hidden_stems.v1`
- [x] `l0.foundation.month_command.v1`

### L1 关系插件家族

- [x] `l1.physics.op_branch_liuchong`
- [x] `l1.physics.op_branch_sanhe`
- [x] `l1.physics.op_branch_liuhe`
- [x] `l1.physics.op_branch_liuhai`
- [x] `l1.physics.op_branch_liupo`
- [x] `l1.physics.op_branch_sanxing`
- [x] `l1.physics.op_branch_muku`
- [x] `l1.physics.op_stem_fusion`

### 子平插件家族

- [x] `classical.ziping.month_command.v1`
- [x] `classical.ziping.balance.v1`
- [x] `classical.ziping.yongshen.v1`

### 格局插件家族

- [x] `ten_god_pattern`
- [x] `classical.pattern.axis.v1`
- [x] `classical.pattern.jianlu_yuejie.v1`
- [x] `classical.pattern.congshi.v1`
- [x] `classical.pattern.finance_officer.v1`
- [x] `classical.pattern.resolver.v1`
- [x] `classical.pattern.formation_gate.v1`
- [x] `classical.pattern.break_guard.v1`

### 盲派插件家族

- [x] `classical.blind.work_axis.v1`
- [x] `classical.blind.response_chain.v1`
- [x] `classical.blind.symbol_trigger.v1`
- [x] `classical.blind.timing_window.v1`
- [x] `classical.blind.summary.v1`

### 风险 / 冲突插件家族

- [x] `l2.risk.risk_matrix`
- [x] `officer_see_hurt`
- [x] `kong_wang`
- [x] `shensha`

## 能力级验收

- [x] 插件可以被自动扫描发现
- [x] 核心插件均有正式 `plugin_id`
- [x] 核心插件参数均可配置
- [x] 六冲已正式插件化
- [x] 六破已进入 `interaction_v2`
- [x] 天干五合已进入统一条件源
- [x] 合化类插件具备 `condition_state`
- [x] 合化类插件的条件状态会影响强度
- [x] 合化专题在条件不足时不再产出可结算 proposal
- [x] 格局专题具备候选、裁决、成格、破格四层输出
- [x] 格局候选之间已可进入互斥冲突层
- [x] L0 藏干、通根、透干、月令均可见
- [x] 新插件家族已有发现性测试

## 观测级验收

- [x] 插件输出统一具备 `target_god`
- [x] 关系类与专题类插件统一具备 `cluster_projection`
- [x] 关键插件输出统一具备 `projection_share`
- [x] `/v17/oracle` 已显示主落点与簇投影摘要
- [x] `/v17/admin` 已显示主落点、占比与投影簇
- [x] `TracePanel / Decision Inbox` 已同步主落点与簇投影语义

## 后续深化，但不阻塞本轮验收

- [ ] 盲派可继续增加更细的专项断口，但当前“做功 / 应期 / 象法 / 收束”链已齐备
- [ ] 已废弃兼容壳插件的文档与历史报告继续逐步清理
