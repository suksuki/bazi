# V17 十神算法与插件叠加审计报告

日期：2026-04-18

范围：
- `v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py`
- `v17_rebirth/backend/logic/L0_physics_fields/vector_physics_engine.py`
- `v17_rebirth/backend/logic/L0_physics_fields/flow_physics_engine.py`
- `v17_rebirth/backend/logic/L1_atomic_ops/l1_meta_hydration.py`
- `v17_rebirth/backend/logic/L0_physics_fields/chang_sheng_12.py`
- `v17_rebirth/backend/logic/L2_structure_patterns/risk_matrix.py`
- `v17_rebirth/backend/services/decision_compiler.py`
- `v17_rebirth/backend/logic/L1_atomic_ops/physics_kernel.py`

## 结论摘要

当前问题更像是“叠加体系失稳”，不是单一的“十神底层公式写错”。

L0 `calc_deity_scores()` 的建模口径是清楚的：四柱/运流按绝对能量累加，之后做排序、阻尼、护栏。
真正让结果变得难以解释的，是从 L1 开始出现了多种不同性质的改写同时作用于同一份 `ten_gods_absolute`：

1. 插件事实生成时直接读取当前张量。
2. 部分插件/仲裁会再次对当前张量做乘法位移。
3. Flow 引擎继续对当前张量做网络流转。
4. `will_proxy` 再做一次整组全局倍率放大。
5. manual decision / PhysicsKernel 也会对同一张量固化回写。

这导致“十神数值”已经不再只代表 L0 基础物理量，而是混合了：
- 出生命局基线
- 运流加成
- 插件规则后验干预
- 流转网络结果
- 意志态全局偏置
- 手动裁决扰动

在这种口径下，数值虽然还能算出来，但分析意义已经不稳定。

## 核心发现

### 1. 单一真源被破坏，`ten_gods_absolute` 同时承担“基线”和“现态”

L0 引擎输出的 `ten_gods_absolute` 原本是绝对强度基线。

但在 `l1_meta_hydration.py` 中，这个字段又被继续当作：
- 插件判定输入
- 自动裁决输出目标
- Flow 结算输入
- `will_proxy` 放大输入
- 最终快照输出

问题：
- 同一个字段既是“原始观测值”，又是“过程态工作内存”，又是“最终展示值”。
- 分析师无法回答“眼前的 74.28 到底是命盘本身，还是插件叠加后的瞬时态”。

影响：
- 同一命盘在不同调用链、不同 decision 历史、不同 `will_proxy` 下，十神值不再具可比性。

建议：
- 至少拆成三层：
  - `ten_gods_base_l0`
  - `ten_gods_runtime_preflow`
  - `ten_gods_runtime_final`

### 2. 插件计算具有顺序依赖，后插件消费的是“已被前插件改写”的状态

在 `hydrate_v17_physics_tensor()` 中，所有插件通过 `iter_all_plugin_specs()` 顺序执行。
每个插件读的是同一个 `pt`，而自动通过的插件还会直接改写 `_absolute`。

结果：
- 后面的插件不是在“同一基线”上判断，而是在“前面插件已经施加过影响”的张量上判断。
- 插件顺序改变，输出可能改变。

这类顺序依赖对规则系统是很危险的，因为：
- 它不是显式设计的因果图。
- 它只是执行顺序带来的副作用。

建议：
- 插件判定应统一读取冻结快照，例如 `analysis_input_scores`。
- 真正的位移结算应在所有事实收集完成后集中执行。

### 3. `arbiter/system/manual` 与“是否真正生效”不是一一对应，语义层和物理层分离不清

`l1_meta_hydration.py` 中：
- 插件事实先变成 decision
- 但 `ArbiterType.SYSTEM` 会被大量改写为 `USER`
- 同时又保留系统自动位移逻辑

这让“仲裁角色”和“是否已经改写物理态”之间没有稳定映射。

风险：
- 一条 decision 在 UI 上看像“待你确认”，但底层可能已经作为系统态影响了别的插件判断。
- 或者相反，已经展示成 auto resolution，但来源只是推断型影响。

建议：
- 强制建立规则：
  - `fact`: 只读事实
  - `proposal`: 可执行建议
  - `resolution`: 已固化动作
- 只有 `resolution` 才允许改写 runtime tensor。

### 4. `will_proxy` 是强全局乘法，物理解释最弱，但影响范围最大

在 `l1_meta_hydration.py` 中：
- `stable` 会整体放大官杀印比
- `aggressive` 会整体放大食伤财

问题：
- 这是最强的一类整体干预，但没有明确物理来源，只是状态偏置。
- 它不是局部修正，而是跨多个十神的批量乘法。
- 它发生在插件/flow 后，极易覆盖前面更细粒度的规则贡献。

影响：
- 用户只切换 decision 或 narrative，最后十神分布却像整体换盘。

建议：
- 把 `will_proxy` 从“改写十神值”改为“解释层偏置”。
- 如果必须保留物理效应，应改成单独的 `will_bias_vector`，不要直接覆盖主张量。

### 5. Flow 引擎与冲突应力引擎的量纲没有完成统一校准

`vector_physics_engine.py` 里：
- 应力来自 `Q_i * Q_j / d^k`

`flow_physics_engine.py` 里：
- 应力又被转成电阻调制
- 再通过 `I = (V_i - V_j) / R` 算流
- 再乘 `FLOW_CONDUCTIVITY_ALPHA` 回写十神

这里至少有三个量纲：
- Qi 强度
- Stress
- Current / dQ

目前代码是可以跑的，但没有看到完整的量纲闭环校准依据。

具体问题：
- `stress=0` 时也强制走 `max(0.1, f)`，意味着“无应力”并不是真正无调制。
- `current` 被硬钳在 `[-2000, 2000]`，说明上游量纲其实可能爆。
- `node_weight = val / potentials[idx]` 的按比例分摊是假设，不是验证过的模型。

建议：
- 分析师应先明确：
  - Stress 的自然范围
  - Current 的合理范围
  - 单次 flow step 对 dQ 的允许上限
- 在此之前，不建议继续增插件。

### 6. 护栏很多，但护栏是在“结果端”截断，不是在“模型端”约束

当前系统有大量护栏：
- NaN/Inf 过滤
- 能量最小/最大钳制
- 电流钳制
- 新值钳制

这能防炸，但不能说明结果正确。

风险：
- 业务看起来“没溢出”，其实只是被静默截断。
- 分析师看到的数值，可能是模型自然结果，也可能只是被 cap 过的结果。

建议：
- 把所有钳制都显式暴露进调试输出：
  - 哪一步被钳制
  - 原值多少
  - 截断到多少

### 7. 长生状态插件在写 meta，但主能量层并没有明确消费这个修正

`chang_sheng_12.py` 会写：
- `meta["qi_status_coeffs"] = {"stage": ..., "resistance": ...}`

但这一项当前更多是：
- 事实显影
- 兼容字段回填

它对主十神能量并没有形成一个可追踪的、统一的位移通道。

结果：
- 同样被称为“物理插件”，有的插件直接改十神，有的只改 meta，有的只产 decision。
- 不同插件的“力学位阶”不一致。

建议：
- 给插件分类：
  - Observation-only
  - Modifier
  - Decision-only
- 不同类别的插件应进入不同阶段，不要混跑。

## 不是首要问题，但值得记录

### 1. `risk_matrix.py` 等插件直接使用固定比例位移

例如：
- `0.2`
- `-0.15`
- `-0.25`

这些值很像经验参数，不像从底层量纲推导而来。
在单插件场景下问题不大，但一旦插件多了，就会形成乘法叠加失控。

### 2. L0 性别微调是常量平移，但跟整体量级相比过弱且解释含混

`ten_gods_engine.py` 中：
- 男命给正官/七杀 +1.2 / +0.8
- 女命给食神/伤官 +1.2 / +0.8

它不会引发爆炸，但会让“绝对能量模型”掺入一层经验叙事偏置。

### 3. 当前测试更偏单点 sanity check，缺少 stack-level golden test

现有测试能覆盖：
- L0 输出结构
- flow 守恒趋势
- decision 路由

但缺少：
- 同一命盘在全插件链下的固定快照基准
- 插件顺序变化是否导致结果漂移
- 一个 decision 前后各层张量的完整对比

## 研判

### 可以确认的事

1. L0 十神底算不是当前最主要的问题源。
2. 真正的问题在于多层系统都在改写同一个 `ten_gods_absolute`。
3. 当前数值已经不再适合被当作“单一物理指标”去解读。

### 暂不建议继续直接编码修复的原因

如果现在继续补 patch，大概率会发生：
- 修掉一条重复叠加
- 又引入新的顺序依赖
- 或让某些旧 UI / snapshot 契约继续漂移

这不是“多改几行”能彻底收住的问题，需要先明确口径。

## 建议交给分析师的任务

### A. 先画清楚物理分层

请分析师先明确以下三个对象的定义：

1. `Base Energy`
   - 出生命局 + 运流后的绝对强度
2. `Derived Runtime Energy`
   - 插件、flow、decision 作用后的运行态
3. `Narrative Bias`
   - `will_proxy`、语义裁决等解释偏置

这三者是否允许互相覆盖，必须先定。

### B. 建立插件分类法

建议所有插件标记为以下三类之一：

1. `observer`
   - 只读张量，只产 facts/meta
2. `modifier`
   - 可产物理位移，但不能直接写回，必须进入统一结算器
3. `decision`
   - 只产建议，等待仲裁

### C. 定一条唯一的结算链

建议目标链路：

1. L0 基线计算
2. 冻结输入快照
3. 所有 observer / decision / modifier 只读分析
4. 汇总 modifier 贡献
5. 统一结算
6. Flow
7. 生成最终 runtime snapshot
8. Narrative 层只读

### D. 给出量纲校准表

分析师应补一份参数表，至少包含：
- 单柱基础能量范围
- 单插件允许的 `impact_ratio` 范围
- 单次 flow 的 `dQ` 上限
- `will_proxy` 是否允许进入物理层

## 建议的后续实施顺序

1. 先冻结现有行为，录一组 golden snapshots。
2. 拆出 `ten_gods_base_l0` 与 `ten_gods_runtime_final`。
3. 禁止插件在 facts 收集阶段直接改写主张量。
4. 将 `will_proxy` 从物理层摘出去，先只做叙事偏置。
5. 最后再做 flow / stress 的量纲重校。

## 附：本次排查时重点确认过的文件

- `backend/logic/L0_physics_fields/ten_gods_engine.py`
- `backend/logic/L0_physics_fields/vector_physics_engine.py`
- `backend/logic/L0_physics_fields/flow_physics_engine.py`
- `backend/logic/L1_atomic_ops/l1_meta_hydration.py`
- `backend/logic/L0_physics_fields/chang_sheng_12.py`
- `backend/logic/L2_structure_patterns/risk_matrix.py`
- `backend/logic/L1_atomic_ops/physics_kernel.py`
- `backend/services/decision_compiler.py`

