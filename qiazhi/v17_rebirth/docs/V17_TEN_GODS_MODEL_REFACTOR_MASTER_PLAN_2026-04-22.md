# V17 十神模型总重构主计划

日期：2026-04-22  
状态：执行中 / Phase 1-5 已推进，Phase 6 持续收口  
定位：十神物理层、关系层、运流层、核心求解层的统一重构总图

---

## 1. 结论

应该现在就做一次总体重构。

原因不是“代码有点乱”，而是系统已经从单一十神分数模型，演进到了：

- `manifest / root / momentum / hidden` 四段来源口径
- `relation formation` 关系成局摘要
- `relation dynamics` 能量轴 / 稳定性轴双轴口径
- `projection bridge` 通根 / 透干单次耦合协议
- `six-pillar spacetime core` 六柱时空核心层
- `authority judgement protocol`（bias / evidence / narrative hint）
- `synthetic lab` 合成样盘回归体系

这些能力都已经出现了，但它们还没有完成模块边界切分，导致：

- 代码实现已经先于结构设计膨胀
- 文档分散，各写各的宪法
- 测试逐渐全面，但仍依赖几个超大文件
- 新规则可以加进去，但不利于持续优化和学习

当前阶段如果继续靠局部补丁推进，后续每加一条命理规则，都会继续放大维护成本和口径漂移风险。

---

## 2. 当前问题画像

### 2.1 大文件集中度过高

立项时（2026-04-22 初）：

- `ten_gods_engine.py`：3315 行
- `branch_stem_geometry.py`：792 行
- `work_path_engine.py`：962 行
- `flux_solver.py`：958 行
- `test_ten_gods_energy_calibration.py`：827 行

当前执行面（2026-04-22 晚）：

- `ten_gods_engine.py`：2082 行
- `branch_stem_geometry.py`：78 行（已退为 facade）
- `work_path_engine.py`：579 行
- 已切出 6 个 L0 子模块 + 4 个 L1 relation runtime 模块：
  - `ten_gods_protocol_builders.py`
  - `ten_gods_decomposition.py`
  - `ten_gods_projection.py`
  - `ten_gods_static_basis.py`
  - `ten_gods_root_dynamics.py`
  - `ten_gods_relation_runtime.py`
  - `L1_atomic_ops/relation_structured_families.py`
  - `L1_atomic_ops/relation_penalty_families.py`
  - `L1_atomic_ops/relation_special_families.py`
  - `L1_atomic_ops/relation_runtime_collectors.py`（facade）
- 已切出 3 个 L1 geometry family 模块：
  - `L1_atomic_ops/relation_geometry_pairs.py`
  - `L1_atomic_ops/relation_geometry_structured.py`
  - `L1_atomic_ops/stem_fusion_geometry.py`
- 已建立统一 runtime field 协议模块：
  - `backend/logic/runtime_field_protocol.py`
- 已建立 authority judgement 协议模块：
  - `backend/services/authority_judgement_protocol.py`
- 已切出 work-path 子协议模块：
  - `backend/logic/core_engine/work_path_row_protocol.py`
  - `backend/logic/core_engine/work_path_graph_utils.py`

这意味着 L0 已从“单体大文件”转为“主引擎 + 子模块编排”结构，并开始正式消费 L1 relation runtime；Core 做功层也开始从 `work_path_engine.py` 单体转为“主引擎 + row protocol + graph utils”结构，后续继续推进 Phase 4/5 时，风险会显著下降。

这说明我们已经不是“小修小补”阶段，而是需要正式切模块。

### 2.2 物理口径与展示口径尚未完全同源

目前已经存在以下事实：

- L0 已经能产出 `relation_formation_summary`
- L0 已经能产出 `relation_dynamics_summary`
- Prompt 已经能读取这些摘要
- Core 图已经开始采用“背景场 / 扰动触发”的口径

但尚未完全统一：

- L0 十神总分结算公式
- Core 做功 / flux / authority 的双轴使用方式
- 前端 Admin / 主页面解释的来源一致性
- 文档之间的主从关系

### 2.3 规则层与算法层还没有完全拆开

当前很多规则同时承担了三种职责：

1. 判定关系是否成立
2. 计算数值增减
3. 输出解释摘要

这会导致一个问题：

一次命理规则修改，往往同时冲击判定、数值、提示词、UI 和测试。

### 2.4 运流层仍有双口径风险

我们已经确立：

- `大运 = 背景场`
- `流年 = 扰动触发`
- 耦合优先级偏向 `日 > 月 > 时 > 年`

但这套口径仍分散在：

- `ten_gods_engine.py`
- `pillar_graph_kernel.py`
- `work_path_engine.py`
- `physics_canonical.py`

需要统一为一条明确的 runtime field 宪法。

---

## 3. 重构目标

本轮重构不只是“整理文件”，而是建立以下四件事：

### 3.1 单一事实源

同一条命理事实，只允许有一套主协议：

- 通根 / 透干
- 关系成局
- 关系动力学
- 运流耦合
- 做功路径
- 用神 / 忌神 / 通关神权威裁决

### 3.2 单向分层

必须继续坚持并强化：

- L0：静态基础物理
- L1：关系原子操作
- Core：时空图 / 做功 / flux / authority
- L2：专题与格局判定
- L3：叙事与提示词

高层可以读取低层，低层不能反向依赖高层结论。

### 3.3 解释与结算分离

同一条关系必须拆成两层：

- `settlement effect`：真正参与数值结算的物理效应
- `explanation summary`：提供给 UI / LLM / Admin 的解释合同

不再允许“因为要给 UI 看，顺手把物理层改了”。

### 3.4 可学习、可回归

所有关键规则都必须进入：

- 单元测试
- Synthetic Lab 合成样盘
- 真实命盘校盘样本
- Prompt 合同测试

系统的“学习能力”建立在可复现的回归机制上，不建立在临场调参上。

---

## 4. 目标架构

## 4.0 当前落地快照（2026-04-22）

L0 当前已经形成下面这组边界：

- `ten_gods_engine.py`
  - orchestration / 常量 / 少量共享 helper / final assembly
- `ten_gods_protocol_builders.py`
  - `projection_bridge_protocol`
  - `relation_dynamics_summary`
  - `relation_formation_summary`
- `ten_gods_decomposition.py`
  - `manifest / root / momentum / hidden` bucket 与 finalize
- `ten_gods_projection.py`
  - visible stems / cross polarity root / same-element projection
- `ten_gods_static_basis.py`
  - stem / branch static basis accumulation
- `ten_gods_root_dynamics.py`
  - runtime stems / dynamic root finalize
- `ten_gods_relation_runtime.py`
  - relation hit shell / trace append / conflict set
- `L1_atomic_ops/relation_structured_families.py`
  - `sanhe / sanhui / banhe / gonghe / liuhe / anhe`
- `L1_atomic_ops/relation_penalty_families.py`
  - `chong / hai / po / xing`
- `L1_atomic_ops/relation_special_families.py`
  - `ke / stem_fusion`
- `L1_atomic_ops/relation_runtime_collectors.py`
  - 兼容导出层，供旧调用桥接
- `L1_atomic_ops/relation_geometry_pairs.py`
  - `liuhe / anhe / chong / hai / po / xing`
- `L1_atomic_ops/relation_geometry_structured.py`
  - `sanhe / banhe / gonghe`
- `L1_atomic_ops/stem_fusion_geometry.py`
  - `stem fusion geometry / runtime pillar parsing`
- `L1_atomic_ops/branch_stem_geometry.py`
  - facade，仅供兼容导出与测试使用

这说明：

- Phase 1 已完成
- Phase 2 的代码切分目标已基本完成
- Phase 3 已进入“逻辑家族真正迁出 L0，并拆成 family 级 L1 模块”阶段
- Phase 4 已开始把 `L0 root scope / Core dynamic edge / Prompt 合同` 收到同一份 runtime-field 宪法里

## 4.1 L0：静态十神物理层

目标：只负责回答“十神本体为什么强/弱”。

建议拆分：

1. `static_basis.py`
   - 天干显化
   - 日干参照轴
   - 柱位显化权重

2. `root_projection.py`
   - 通根
   - 透干
   - 单次耦合协议
   - 本根 / 异阴阳根 / 潜藏根

3. `momentum_fields.py`
   - 月令势
   - 长生阶段势
   - 禄 / 刃 / 帝旺
   - 结构势占位入口

4. `decomposition.py`
   - 四段分解字段
   - total score 合成
   - 排序与裁剪

5. `summary_protocols.py`
   - `projection_bridge_protocol`
   - `relation_formation_summary`
   - `relation_dynamics_summary`

原则：

- L0 只认“冻结盘面证据”
- 不做高层判词
- 不做 L2 专题裁决

## 4.2 L1：关系原子层

目标：只负责回答“关系是否成立，基础效应是多少”。

建议拆分：

1. `branch_relation_families.py`
   - 三会
   - 三合
   - 半合（生旺 / 墓旺）
   - 拱合
   - 六合
   - 暗合

2. `branch_conflict_families.py`
   - 六冲
   - 三刑
   - 六害
   - 六破
   - 支层相克

3. `stem_fusion.py`
   - 天干五合
   - 明化 / 暗化 / 羁绊
   - 根气回看
   - 争合 / 支扰

4. `relation_runtime.py`
   - 家族基础倍率
   - 位置因子
   - 距离因子
   - 重复支因子
   - 破局阻尼

原则：

- 关系是否成立与关系解释要同源
- 关系家族不要直接写死在 L0 总结算函数里

## 4.3 Core：六柱时空核心层

目标：只负责回答“能量如何流、怎么做功、谁对谁产生正负效应”。

建议结构：

1. `pillar_graph_kernel.py`
   - 节点
   - 边
   - distance / origin / coupling mode
   - 运流场规则

2. `work_path_engine.py`
   - actor / receiver
   - 合力 / 抗力
   - 正向 / 逆向传导
   - 路径评分

3. `flux_solver.py`
   - M1/M2/M3 动力学
   - 张力
   - 放大
   - 对冲
   - 回路

4. `effect_resolver.py`
   - benefit / harm / net utility
   - 稳定性加权
   - 双轴折算

5. `god_ring_resolver_core.py`
   - 用神 / 忌神 / 通关神候选
   - authority payload
   - core rationale

原则：

- Core 不直接改写 L0 静态基础
- Core 只消费冻结的 L0 / L1 事实
- Core 输出权威裁决与动态解释

## 4.4 L2：专题判定层

目标：只负责“判定性插件”，默认不直接改写十神静态分。

包括：

- 伤官见官 / 伤官伤尽
- 枭印夺食
- 官杀混杂
- 食伤制杀
- 格局拟合
- 盲派 / 子平家族

原则：

- L2 可以给 `authority bias`
- L2 可以影响 `用神 / 忌神 / 通关神` 候选解释
- L2 不应越权成为 L0 物理结算器

## 4.5 L3：叙事与提示词层

目标：只负责把结构化事实翻译给 UI 和 LLM。

包括：

- `physics_canonical.py`
- `semantic_fusion.py`
- 决策与计划摘要
- Prompt 合同

原则：

- L3 只能读，不反写物理
- 叙事百分比必须标注为“成局度 / 拟合度 / 权重”，不能伪装成绝对能量

---

## 5. 需要统一的核心宪法

本轮重构后，必须把以下几条确立为全局主规则：

### 5.1 四段式十神来源宪法

- `manifest`
- `root`
- `momentum`
- `hidden`

### 5.2 根透桥协议

- `通根 = 天干 <- 地支藏干`
- `透干 = 地支藏干 -> 天干`
- 单次耦合
- 禁止递归回写

### 5.3 关系双轴协议

每条关系都要有：

- `energy_axis`
- `stability_axis`

最低要求：

- 冲：激发 / 降稳
- 刑：内耗 / 降稳
- 克：压制转移 / 被克方降稳
- 害：暗损 / 降稳
- 破：解构 / 降稳
- 合：绑定/组织化 / 常提升结构稳定

### 5.4 运流场协议

- `大运 = 背景场`
- `流年 = 扰动触发`
- 优先耦合顺序：`日 > 月 > 时 > 年`
- 不再使用“流年先打大运再打原局”的线性误导表述

### 5.5 判定层越权限制

- 格局、专题、叙事类插件不得直接越权篡改 L0
- 只能提供：
  - evidence
  - bias
  - narrative hint
  - routing suggestion

---

## 6. 文档对齐矩阵

本轮要把文档分成三类：

### 6.1 宪法文档

长期有效、必须稳定引用：

- `V17_TEN_GODS_ENERGY_DECOMPOSITION_PROTOCOL_2026-04-21.md`
- `V17_CROSS_LAYER_INTERACTION_PROTOCOL.md`
- `V17_SIX_PILLAR_SPACETIME_CORE_2026-04-20.md`
- `V17_TEN_GODS_MODEL_REFACTOR_MASTER_PLAN_2026-04-22.md`

### 6.2 专项审计文档

用于校正或审计，不作为第一引用入口：

- `V17_PLUGIN_DEFAULT_VALUE_AUDIT.md`
- `V17_PLUGIN_PARAMETER_AUDIT.md`
- `V17_PLUGIN_REAL_CHART_CALIBRATION.md`
- 其他插件家族审计报告

### 6.3 测试与实验文档

- `V17_SYNTHETIC_LAB_PROTOCOL_2026-04-21.md`
- `TESTING.md`

要求：

- 宪法文档之间不重复写实现细节
- 专项审计文档引用宪法，不自己另立法
- 测试文档明确哪些规则已被 Synthetic 覆盖

---

## 7. 迁移阶段

## Phase 0：冻结基线

目标：

- 冻结当前通过的口径与关键样盘
- 不再继续往超大文件里塞新规则

动作：

1. 建立本主计划文档
2. 记录模块边界
3. 记录关键基线测试
4. 明确哪些规则“已立法、只允许迁移不允许偷改”

验收：

- 全量测试绿
- 文档有统一入口

## Phase 1：切出协议与汇总构建器

状态：已完成

目标：

- 先把“协议构建”从大文件里摘出去

动作：

1. 提取 `projection_bridge_protocol`
2. 提取 `relation_formation_summary`
3. 提取 `relation_dynamics_summary`
4. 提取 shared type / row builders

验收：

- `ten_gods_engine.py` 明显减重
- Prompt、Admin、前端字段不变

## Phase 2：切出 L0 静态基础

状态：代码切分已基本完成，待补文档与更细粒度测试

目标：

- 拆分 manifest / root / momentum / hidden 的结算

动作：

1. 提取显化计算
2. 提取根透桥
3. 提取势能字段
4. 保留统一 final assembler

验收：

- 四段来源单元测试独立
- 相同样盘分值不回退

## Phase 3：切出 L1 关系家族

状态：已进入 family 级模块阶段（runtime / geometry 双层 family 模块已拆分，并补了轻量单测）

阶段验收快照：

- `test_l1_relation_runtime_collectors.py`：新增 4 条
- `test_l1_branch_geometry_modules.py`：新增 3 条
- `test_runtime_field_protocol.py`：新增 4 条
- `test_authority_judgement_protocol.py`：新增 2 条
- 关键回归：`74 passed`（Phase 3）→ `23 passed`（Phase 4 runtime-field 对齐）→ `24 passed`（authority judgement / routing / prompt 对齐）
- 全量 `v17_rebirth/tests`：`314 passed`

目标：

- 让三会、三合、半合、拱合、六合、暗合、冲刑害破等都在独立 family 模块里

动作：

1. 关系家族统一返回 `hit + intensity + damping + trace`
2. 地支关系与天干五合完全分家
3. 关系基础倍率进入配置层

验收：

- 关系测试矩阵独立
- 合成样盘覆盖 family 差异

## Phase 4：统一运流与做功场

状态：执行中（runtime field 协议已抽成共享模块，双轴 authority 评分已开始落入候选排序与 UI）

目标：

- 让 L0、Core、Prompt 对 `背景场 / 扰动触发` 用同一口径

动作：

1. 对齐 `pillar_graph_kernel.py` 与 L0 运流权重
2. 统一 dynamic edge metadata
3. 把关系双轴正式接到 `work_path / flux / authority`

验收：

- “高能低稳”与“低能高稳”在 authority 上能区分

## Phase 5：专题层与权威裁决对齐

状态：执行中（authority judgement protocol 已落地，routing / prompt / Admin 已开始消费）

目标：

- 让 L2 插件只提供证据与偏置，不越权改物理

动作：

1. 审计判定型插件
2. 明确 bias / evidence / narrative 边界
3. 把 `use/taboo/tongguan` 统一接 authority

验收：

- 用神忌神解释链条可追溯
- 冲突层可读 L2 偏置但不混算

## Phase 6：文档与 UI 完整对齐

状态：执行中（Prompt 合同、Admin / Explain 卡、测试文档已开始同步）

目标：

- 主页面、Admin、LLM、测试文档引用同一套名词和协议

动作：

1. 清理过时 UI 文案
2. 更新 Admin Core 面板
3. 对齐 Prompt 合同
4. 更新 Synthetic Lab 文档

验收：

- 相同概念不再多名并存

---

## 8. 测试策略

本轮重构必须坚持“四层测试”：

### 8.1 单元测试

测试：

- 通根 / 透干
- 月令 / 长生 / 禄刃
- 三会 / 三合 / 半合 / 拱合 / 六合 / 暗合
- 冲 / 刑 / 害 / 破 / 克
- 天干五合

### 8.2 Synthetic Lab

测试：

- 单变量样盘
- 关系成局矩阵
- 动态透干矩阵
- L2 判定型样盘

### 8.3 真实命盘校盘

测试：

- 命理师争议盘
- 强格 / 弱格 / 从格 / 混格
- 高动态冲突盘

### 8.4 Prompt / UI 合同测试

测试：

- Prompt 是否正确解释“成局度 / 拟合度 / 双轴”
- 前端是否能稳定读取新字段

---

## 9. 风险控制

### 9.1 禁止一边切模块一边偷偷调参

迁移阶段必须优先做“等价迁移”，再做“参数优化”。

### 9.2 禁止低层反向依赖高层

不允许：

- L0 读取 L2 判词
- L0 读取 L3 提示词
- 关系家族直接读取 authority 结论

### 9.3 禁止一次性大爆炸改完

必须保持：

- 每个 Phase 可单独回归
- 每个 Phase 可单独验收

---

## 10. 本轮立刻执行的下一步

建议从以下顺序开始推进：

1. Phase 1：先切 `summary / protocol builders`
2. Phase 2：再切 `manifest/root/momentum/hidden`
3. Phase 3：再切 `relation families`

也就是说，先切“协议层”，再切“结算层”，最后切“关系层”。

原因：

- 协议层最稳定，先切风险最低
- 先把解释与构建器剥离，后续拆算法才不容易把 UI / Prompt 打断
- 切完协议层后，测试更容易挂钩

---

## 11. 最终验收标准

重构完成后，至少满足：

1. `ten_gods_engine.py` 不再是 3000+ 行单体
2. 通根 / 透干 / 关系家族 / 运流场 / 做功 / authority 都有明确模块边界
3. 文档中“根”“势”“合”“冲”“大运”“流年”不再多口径并存
4. Synthetic Lab 可以独立回归核心规则
5. Prompt、Admin、主页面引用的是同一套协议名词
6. 后续新增规则时，优先是“加模块 / 加测试”，而不是“继续往大文件里补 if”

---

## 12. 决策

本计划批准后，后续开发策略应切换为：

- 先重构整理
- 再继续推进新能力

也就是说，接下来一段时间的主线，不再是“继续叠新规则”，而是：

`冻结基线 -> 切模块 -> 对齐协议 -> 校准测试 -> 再继续扩展`
