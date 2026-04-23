# V17 门派架构对齐二次反馈（对分析师回复的 Review）

日期：2026-04-23

## 1. 目的

这份文档用于回应分析师对《V17 八字门派架构对齐反馈》的 review。

目标不是重复原有结论，而是：

- 明确哪些观点直接采纳
- 明确哪些观点需要工程化纠偏
- 明确下一阶段如果要实施，应该以什么顺序落地

## 2. 总体判断

分析师这份回复整体是高质量的，和 V17 当前架构方向基本一致，采纳度可定为：

- 总体方向采纳：`高`
- 具体实施细节：`需纠偏`

可以直接确认采纳的部分：

1. `ziping umbrella` 必须继续保留
2. `共享物理层 + 多专题并行 + authority 汇总` 是正确主结构
3. `blind = bias_only` 必须坚持，不允许进入主裁决
4. 系统当前真正缺的，不是更多门派标签，而是更底层的物理轴

## 3. 直接采纳的部分

### 3.1 ziping umbrella 收敛

这一点完全正确，不建议再做结构性讨论。

原因：

- `格局 / 扶抑 / 调候` 共用同一套底层状态变量
- 如果拆成多个平行门派，必然造成：
  - 重复计算
  - authority 冲突
  - UI 认知混乱

因此，当前系统继续保持：

- `ziping family`
  - `balance axis`
  - `pattern axis`
  - `future climate axis`

是正确做法。

### 3.2 多专题并行 + authority 汇总

这一点也完全正确。

当前 V17 已经明确采用：

- 底层统一物理层
- 上层多个专题并行解释
- 最终由 authority 汇总裁决

这本质上已经是：

- 多模型 ensemble
- 分层汇总
- 防止单专题夺权

这一结构应继续保持，不建议回退。

### 3.3 blind 只能 bias-only

这一点不仅正确，而且必须强化。

blind 的本质是：

- pattern matching
- 非守恒
- 强经验
- 强解释

因此它应该：

- 输出 `blind_theme`
- 输出 `blind_bias_protocol`
- 进入 authority 的 soft bias

但绝不允许：

- 覆盖 `god_ring_authority`
- 修改 L0/L1 底层物理

这一边界已经是当前实现状态，应继续坚持。

## 4. 需要纠偏的部分

## 4.1 调候轴不能只停留在“概念化四变量”

分析师提出的方向是对的：

- 调候必须成为真正的物理轴
- 不能继续停留在解释层

但分析师给出的四变量表达：

- `T_heat`
- `C_cold`
- `H_humidity`
- `D_dryness`

如果直接照搬，会带来工程问题：

- 状态重复计数
- 四变量之间缺少守恒和互斥约束
- 容易出现“既热又寒、既湿又燥”的无约束叠加

### 建议的工程化修正

第一阶段更适合先定义两条主轴：

- `thermal_index`：寒热轴
- `moisture_index`：燥湿轴

在此基础上再派生：

- `heat`
- `cold`
- `humidity`
- `dryness`
- `climate_tension`

这样更容易与当前 V17 已有结构对齐：

- `energy axis`
- `stability axis`
- `runtime field`
- `authority axis`

### 结论

分析师对“调候必须物理化”的判断完全正确，  
但在实现层，应采用：

- `两条主轴 + 派生状态`

而不是：

- `四个完全独立变量`

## 4.2 调候轴不能只在 authority Level 2 被讨论

分析师提出：

- Level 1：ziping 主裁决
- Level 2：pattern / future climate
- Level 3：blind / xiangfa / shensha

这个方向是对的，但这里有一个实现层纠偏：

### 调候的“解释层”可以是 Level 2

但调候的“物理场本身”不能只存在于 Level 2。

如果调候只出现在专题层或 authority 层，就会再次退化为：

- 文案噪声
- 解释补丁
- 非物理偏置

### 正确落位应该是

- `L0/L1`：建立调候场与来源分解
- `L2`：做调候专题解释
- `authority`：吸收调候对效率、稳定性、用神优先级的影响

### 结论

调候不应被理解为一个“未来专题”，  
它首先应是一个：

- 底层物理场

然后才是：

- 一个 L2 专题解释层

## 4.3 象法边界还要再收紧

分析师已经提出：

- 象法不能改五行能量
- 不能改十神结构
- 不能直接进入主 authority 分数

这条原则是对的。

但从当前系统演化安全性来看，还应更保守一步：

### 建议第一阶段的象法只做

- `semantic mapping`
- `event framing`
- `narrative hint`
- `evidence`

### 第一阶段不建议直接开放

- `bias`

原因：

- 当前 blind 已经作为一个经验型 bias 进入 authority
- 如果象法也过早进入 bias，会出现双经验专题叠加
- 这会加速侵蚀 ziping 主裁决的稳定性

### 结论

象法应先作为：

- 语义层 / 叙事层专题

待 synthetic lab 和 benchmark 证明其稳定后，再讨论是否放开低权重 bias。

## 4.4 authority 分层必须变成正式协议，而不是文档分层

分析师提出 authority 三层：

- Level 1：ziping 主裁决
- Level 2：结构增强
- Level 3：软偏置

方向是对的，但如果只停留在文档描述，会很快失效。

### 建议正式协议化

建议未来若实施 authority 分层，应显式引入字段：

- `authority_level`
- `max_bias_ratio`
- `override_forbidden`
- `hard_constraint_source`
- `soft_bias_source`
- `structure_enhancement_source`

这样才不会把分层变成口头约定。

### 结论

authority 分层应作为：

- 协议层
- 元数据层
- 测试层

三层一起落地，而不是只写在设计文档中。

## 4.5 调候不宜第一阶段直接改 L0 十神原始总量

分析师提出调候要影响：

- 十神效率
- 用神优先级
- 格局稳定性

这一方向完全正确。

但为了和当前架构保持一致，建议增加一个实施限制：

### 第一阶段调候优先影响

- `ten_god_efficiency`
- `ten_god_stability`
- `yongshen_priority_delta`
- `pattern_survival_delta`

### 第一阶段不建议直接改

- `L0 base` 的十神原始总量

原因：

- 当前 V17 已经明确区分：
  - 能量轴
  - 稳定性轴
  - authority 轴
- 如果调候一上来直接改 L0 base，会把“环境因子”和“原始结构”重新混在一起

### 结论

调候第一阶段更适合作为：

- 效率修正项
- 稳定性修正项
- priority 修正项

而不是：

- 直接改写静态根本能量

## 5. 和当前系统的最终对齐结论

对齐当前 V17，我们建议保留以下结构：

### 5.1 已确认保留

- `ziping umbrella`
- `pattern_specializations`
- `blind = bias_only`
- `risk_matrix`
- `shensha`

### 5.2 下一步值得新增

不是更多门派，而是：

1. `调候物理轴`
2. `authority 分层协议`
3. `未来象法的语义专题边界`

## 6. 建议回复给分析师的正式版本

以下内容可直接作为回复建议：

---

你的 review 整体我们采纳，特别是以下三点：

1. `ziping umbrella` 继续作为主裁决 umbrella，不再拆分为多个平行门派
2. 当前 V17 继续坚持“共享物理层 + 多专题并行 + authority 汇总”
3. blind 继续保持 `bias_only`，不允许覆盖主裁决

但在实施层面，我们建议做三点纠偏：

### 1. 调候轴必须先做成底层物理场

调候不应只作为 future L2 topic 或 Level 2 authority 结构增强项。

建议顺序是：

- 先在 `L0/L1` 定义调候变量、来源分解、作用规则
- 再在 `L2` 做调候专题解释
- 最后让 authority 吸收其对效率、稳定性、用神优先级的影响

### 2. 调候变量建议采用“两条主轴 + 派生状态”

工程上更建议：

- `thermal_index`
- `moisture_index`

再派生：

- `heat / cold / humidity / dryness / climate_tension`

这样更容易和当前 V17 的能量轴、稳定性轴、runtime field 对齐，也更容易做约束。

### 3. 象法第一阶段应比 blind 更保守

建议象法在第一阶段只输出：

- semantic mapping
- evidence
- narrative hint

暂不直接进入 bias，待 synthetic lab 和 benchmark 证明稳定后，再讨论低权重 bias。

### 4. authority 分层必须协议化

建议未来 authority 分层不只写在文档里，而要真正形成协议字段，例如：

- `authority_level`
- `max_bias_ratio`
- `override_forbidden`

这样才能防止 soft bias 逐步侵蚀主模型。

### 5. 调候第一阶段优先影响效率/稳定性/优先级，不直接改 L0 原始十神总量

以保证：

- 原始结构
- 环境修正
- 上层裁决

继续分层清晰。

---

## 7. 最终结论

这份分析师回复值得采纳，但应增加两条实现纠偏：

1. **调候先建物理场，再进专题层**
2. **象法先做语义层，不急着进 bias**

一句话总结：

**当前 V17 下一阶段不应继续扩门派，而应优先收敛调候这一条底层物理轴。**
