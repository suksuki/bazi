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

### 1. 盲派只有单一占位插件

当前只有：

- `classical.blind_school.v1`

问题：

- 只是 `meta.blind_work_hint` 的显影器
- 不是盲派插件族

### 2. 子平/旺衰派只有底层计算，没有完整专题

当前已有：

- L0 `ten_gods_engine` 里的月令、通根、透干、藏干、盖头、截脚
- `classical.wangshuai.v1` 占位插件

问题：

- 物理做了，理论插件没长起来

### 3. 格局插件过于粗糙

当前已有：

- `ten_god_pattern`
- `classical.pattern_detector.v2`

问题：

- 只够做标题锚点
- 还没有格局专题

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

### C. 子平/旺衰插件家族

- `classical.ziping.month_command.v1`
- `classical.ziping.balance.v1`
- `classical.ziping.yongshen.v1`
- `classical.wangshuai.v1`

职责：

- 子平体系的“月令、旺衰、用神”解释层

### D. 格局插件家族

- `ten_god_pattern`
- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`
- `classical.pattern_detector.v2`

职责：

- 负责主轴格局、候选格局、特殊格局、财官协同等结构判定

### E. 盲派插件家族

- `classical.blind.work_axis.v1`
- `classical.blind.response_chain.v1`
- `classical.blind.symbol_trigger.v1`
- `classical.blind_school.v1`

职责：

- 把“做功、应期、触发象”从单句提示拆成结构化插件

### F. 风险与结构冲突插件家族

- `l2.risk.risk_matrix`
- `officer_see_hurt`
- `kong_wang`
- `shensha`
- `classical.conflict_auditor.v1`

职责：

- 负责高风险结构、解释性冲突和需要升级到裁决层的问题

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
