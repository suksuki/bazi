# V17 插件家族重构总图

## 目标

本轮插件重构只做一件事：把目前零散的规则、占位、几何探测、底层物理，整理成可持续扩张的插件家族。

重构后，插件不再分散为：

- 只有底层计算、没有插件入口
- 只有 registry 占位、没有真实逻辑
- 只有几何命中、没有成立条件
- 只有事实输出、没有冲突裁决

而是统一落到“家族 + 子插件”的结构中。

## 当前缺口

### 1. 盲派曾经只有单一占位插件

已废弃：

- `classical.blind_school.v1`

现状：

- 已由 `classical.blind.work_axis.v1`
- `classical.blind.response_chain.v1`
- `classical.blind.symbol_trigger.v1`
- `classical.blind.timing_window.v1`
- `classical.blind.summary.v1`

完整接管。

### 2. 子平/旺衰派只有底层计算，没有完整专题

当前已有：

- L0 `ten_gods_engine` 里的月令、通根、透干、藏干、盖头、截脚
- `classical.ziping.month_command.v1`
- `classical.ziping.balance.v1`
- `classical.ziping.yongshen.v1`
- `classical.ziping.climate_bridge.v1`
- `classical.ziping.pattern_bridge.v1`
- `classical.ziping.god_ring_resolver.v1`
- `classical.ziping.summary.v1`

现状：

- 子平已从“月令 / 旺衰 / 用神”三件套升级为完整 umbrella。
- `pattern_specializations` 和 `climate_theme` 仍是独立专题家族，但子平通过 bridge 插件完成归口。

### 3. 格局插件过于粗糙

当前已有：

- `ten_god_pattern`
- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`
- `classical.pattern.resolver.v1`
- `classical.pattern.formation_gate.v1`
- `classical.pattern.break_guard.v1`

问题：

- 早期旧 headline 插件 `classical.pattern_detector.v2` 已废弃
- 现在已进入候选、裁决、成格、破格四层

### 4. 合化类缺少“成立条件专题”

当前已有：

- 三合 / 六合 / 六害 / 六破 / 墓库 / 天干五合

问题：

- 多数偏“检测命中即给 effect”
- 还没有统一的成立条件协议

### 5. 刑冲克害不成体系

当前已有：

- 三刑、六害、六破、六合、三合、天干五合

缺口：

- 六冲没有正式独立插件
- “克”仍主要是 L0 流转，不是正式插件家族

### 6. 冲突层有骨架，但未专题化

当前已有：

- claim / proposal / resolution / settlement 的后置过滤逻辑

问题：

- 更像内嵌逻辑，不像正式法庭模块

### 7. L0 基础规则不可见

当前已有：

- 藏干
- 通根
- 透干
- 月令
- 盖头 / 截脚

问题：

- 算了，但没有“基础插件家族”的可见输出

## 本轮补齐后的插件家族

### A. L0 基础插件家族

- `l0.foundation.hidden_stems.v1`
- `l0.foundation.rooted_stems.v1`
- `l0.foundation.exposed_hidden_stems.v1`
- `l0.foundation.month_command.v1`

职责：

- 把藏干、通根、透干、月令从“底层物理细节”提升为“可审计基础事实”

### B. L1 关系插件家族

- `l1.physics.op_branch_liuchong`
- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_branch_liuhai`
- `l1.physics.op_branch_liupo`
- `l1.physics.op_branch_sanxing`
- `l1.physics.op_branch_muku`
- `l1.physics.op_stem_fusion`

职责：

- 只负责结构关系与相对位移
- 不直接决定最终叙事

### C. 子平插件家族

- `classical.ziping.month_command.v1`
- `classical.ziping.balance.v1`
- `classical.ziping.climate_bridge.v1`
- `classical.ziping.pattern_bridge.v1`
- `classical.ziping.yongshen.v1`
- `classical.ziping.god_ring_resolver.v1`
- `classical.ziping.summary.v1`

职责：

- 子平体系的主裁决 umbrella。
- `month_command` 负责月令定盘。
- `balance` 负责扶抑 / 旺衰平衡轴。
- `climate_bridge` 把调候物理轴归口到子平，不直接改写 L0 base totals。
- `pattern_bridge` 把格局专题候选归口到子平，不取代独立格局插件。
- `yongshen` 给出传统用神观察轴。
- `god_ring_resolver` 是体用 / 用忌 / 通关主裁决。
- `summary` 收束月令、旺衰、调候、格局、体用裁决为子平总括。

### D. 格局插件家族

- `ten_god_pattern`
- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`
- `classical.pattern.dynamic_scope.v1`
- `classical.pattern.resolver.v1`
- `classical.pattern.formation_gate.v1`
- `classical.pattern.break_guard.v1`

职责：

- 负责主轴格局、候选格局、特殊格局、财官协同等结构判定

### E. 盲派插件家族

- `classical.blind.work_axis.v1`
- `classical.blind.response_chain.v1`
- `classical.blind.symbol_trigger.v1`
- `classical.blind.timing_window.v1`
- `classical.blind.summary.v1`

职责：

- 把“做功、应期、触发象”从单句提示拆成结构化插件
- 当前已升级为“盲派主题 core + 多个视图插件”
- blind theme core 统一输出：
  - 体/用候选
  - 家里家外
  - 运行换挡
  - blind soft bias
- 子插件负责展示不同切面；authority 只并行吸收 `blind_bias_protocol`，不允许盲派覆盖子平主裁决

### F. 风险与结构冲突插件家族

- `l2.risk.risk_matrix`
- `officer_see_hurt`
- `kong_wang`
- `shensha`
- `classical.pattern.resolver.v1`
- `classical.pattern.break_guard.v1`

职责：

- 负责高风险结构、解释性冲突和需要升级到裁决层的问题

### G. 调候与象法专题家族

- `classical.climate.axis.v1`
- `classical.climate.ten_god_fit.v1`
- `classical.climate.pattern_survival.v1`
- `classical.climate.summary.v1`
- `classical.xiangfa.semantic_mapping.v1`
- `classical.xiangfa.evidence.v1`
- `classical.xiangfa.narrative_hint.v1`
- `classical.xiangfa.event_framing.v1`

职责：

- 调候专题建立在 `climate_field + climate_modifier_layer` 之上，只做 L2 解释，不回写 L0 base totals
- 象法专题只消费 authority / blind / climate / relation 的现成结果，输出 semantic mapping、evidence、narrative hint、event framing
- 象法当前明确保持 `semantic-only`：
  - 不进入 bias
  - 不改五行能量
  - 不覆盖 authority 主裁决

## UI 对齐状态

主页面 `/v17/oracle` 已拆成三层页面：

- `核心页面`：只保留六柱、体用中枢、判词与 Decision Inbox。
- `辅助页面`：承接解释合同、专题总览、格局、关系、来源账本和 God Ring 解释。
- `观测页面`：承接原调试侧栏的元数据、因果链路、Decision trace 与 LLM 审计。

辅助页面新增 `Topic Hub / 专题中枢`，集中显示六条专题线：

- `子平主裁决`：Level 1 hard constraint，显示用神、忌神、候选与置信度。
- `格局专题`：Level 2 structure enhancement，显示主格局、成局度、破格风险。
- `调候专题`：L0/L1 field + L2 bridge，显示寒热轴、燥湿轴、张力与顺/压十神。
- `盲派专题`：Level 3 soft bias，显示体态、运行换挡、推用/推忌。
- `象法专题`：semantic-only，显示语义、证据、事件主题，不入 bias。
- `风险专题`：guard rail，显示风险来源、判定偏置与稳定承压。

Admin Core 面板同步新增 `Topic Hub / 专题状态表`，用于审计各专题是否命中、所在 authority 层级、是否进入硬约束、结构增强或软偏置。

## 后续仍需深化的专题

### 1. 合化成立条件专题

统一判定四层条件：

- 几何成立
- 月令支持
- 通根透干支持
- 破格 / 争合 / 冲破

### 2. 格局专题

要从“单轴标签”升级为“多候选格局 + 冲突裁决”。

### 3. 冲突法庭专题

拆为正式模块：

- `claim_normalizer`
- `conflict_detector`
- `resolution_router`
- `settlement_arbiter`

## 实施顺序

1. 先把插件家族落成代码与注册表入口
2. 再为每个家族补参数、条件与统计
3. 最后才做默认值微调和命中率校准

## 本轮完成标准

- 缺失的大类插件都有正式入口
- 六冲成为正式插件
- 盲派不再只有单插件占位
- 子平/旺衰、格局、L0 基础都进入插件家族
- 自动扫描与测试可发现这些插件
