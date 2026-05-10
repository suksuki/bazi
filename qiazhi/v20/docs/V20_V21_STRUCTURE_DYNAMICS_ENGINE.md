# V20 / V21 Structure Dynamics Engine

Structure Dynamics Engine（SDE）是 V20 / V21 的命理动态结构引擎。

本文只定义上层架构、核心理念、系统边界、数据流、Contract 扩展和长期方向，不包含实现细节。

## 背景与问题

当前系统已经具备：

- Rule Kernel
- Feature Extraction
- Prediction Contract
- Profile System
- LLM Explanation Adapter

但整体仍偏静态命局分析：识别原局结构、命中规则、生成画像、输出解释。

系统目前更像“原局特征识别器”，而不是真正的“命理动态演化系统”。

真正的命理核心不是“原局是什么”，而是“结构如何随时间演化”：

- 大运如何引动原局
- 流年如何激活链条
- 合局如何稳定或失稳
- 冲如何改变结构稳定性
- 哪个结构成为阶段主线
- 哪个链条成为闭环
- 哪个阶段进入高波动状态
- 哪个阶段形成结构收束

因此系统必须新增 Structure Dynamics Engine。

## 核心定位

SDE 不是规则层、画像层或 LLM 推理层。

SDE 的本质是动态结构事实层，负责计算命局结构在时间轴上的动态演化。

## 系统位置

推荐主线：

```text
Knowledge Layer
-> Rule Kernel
-> Feature Extraction
-> Structure Dynamics Engine
-> Trajectory Builder
-> Prediction Contract
-> Profile System
-> LLM Explanation Adapter
```

SDE 应作为独立动态计算引擎，而不是 Profile、LLM 或 Recommendation 的子模块。

## 输入

SDE 只依赖三类输入。

### 原局事实

例如：

- 天干
- 地支
- 藏干
- 十神
- 宫位
- 月令
- 通根
- 透干

### Feature Extraction 输出

例如：

- 三合
- 六合
- 冲
- 刑
- 害
- 破
- 格局候选
- 链条候选
- dominant structures

### 时间上下文

例如：

- 大运
- 流年
- 流月

## 禁止依赖

### 禁止依赖 LLM

LLM 不允许参与动态裁决、合化判断、主链选择、强弱判断和稳定性判断。LLM 只能消费 SDE 输出。

### 禁止依赖画像系统

画像是解释层，不是动态事实来源。

禁止：

```text
Profile -> SDE
```

只允许：

```text
SDE -> Profile
```

### 禁止 Recommendation 反向影响 SDE

问题推荐系统只能消费动态状态，不能反向修改结构计算。

## 核心目标

SDE 不负责“命中规则”，而负责“结构如何变化”。

核心能力包括：

- 引动
- 合化
- 冲破
- 稳定性变化
- 能量变化
- 主链切换
- 结构闭环
- 阶段转移

## 建模方式

推荐使用 Weighted Dynamic Graph（加权动态图），而不是 if-else 命理树。

### Nodes

建议节点类型：

- StemNode
- BranchNode
- HiddenStemNode
- TenGodNode
- PalaceNode
- ElementNode
- StructureNode

### Edges

建议边类型：

- generate
- control
- combine
- clash
- harm
- punishment
- merge
- transform
- root
- reveal
- activate
- seal
- release

## 动态核心维度

系统不能只做强弱判断。至少需要以下维度。

### energy_strength

结构能量。

### stability_score

结构稳定性。

关键理念：

```text
冲 != 能量消失
冲 = 稳定性下降 + 能量释放
```

### visibility_score

显化度。

例如透干、引动、是否进入时间层。

### continuity_score

持续性。

例如通根、月令、是否得运。

## 动态结构概念

SDE 不应只看“有没有结构”，而要看结构是否稳定、失稳、闭环、泄漏、阻断或收束。

## Dominant Chain

SDE 必须支持动态主链提取。

例如：

```text
食伤 -> 财 -> 杀
杀 -> 印 -> 身
财 -> 官 -> 印
```

核心不是有没有链，而是链是否成立、闭环、泄漏或阻断。

## Chain State

建议链条状态：

- closed
- partial
- blocked
- leaking
- volatile
- collapsed
- overdriven

例如：

```text
食伤 -> 财 -> 杀
```

如果杀不生印，则可能是：

```text
closed_at_killing
```

这表示系统在七杀处完成收束，形成结构闭环。

## Trajectory

SDE 不只输出当前状态，还应输出时间演化轨迹。

例如：

- 庚子运：明杀高压结构，规则统治，系统刚性极高。
- 己亥运：暗杀稳定结构，财链增强，火被压制，自由度提升。
- 丙午流年：食伤爆发，波动性增强，系统非线性提升。

最终形成的是人生结构轨迹，而不是单点算命结果。

## Trajectory Builder

建议新增 Trajectory Builder，负责把多个动态状态串联为人生轨迹。

例如：

- childhood phase
- pressure phase
- wealth activation phase
- structure collapse phase
- reconstruction phase

## Prediction Contract 扩展

建议新增字段：

- dynamic_state
- trajectory_phase
- dominant_chain
- chain_state
- energy_shift
- stability_shift
- activated_structures
- suppressed_structures
- terminal_node
- volatility_score
- trajectory_summary

## 本质

SDE 本质上不是传统命理模块，而是复杂结构动力学系统。

它更接近：

- Structural Dynamics
- Complex Network Dynamics
- Dynamic Systems
- State Transition Systems
- Nonlinear Systems

命理只是结构语言。

## 长期方向

未来 SDE 不应只服务八字。

理论上，它可以统一：

- 八字
- 紫微
- 西占
- 人格模型
- 行为轨迹
- 用户反馈
- 长期决策模式

最终形成 Unified Structure Dynamics Platform。

## 当前阶段建议

P0 阶段不要优先投入黑箱 AI、强 ML 或端到端学习。

优先建设确定性动态结构系统：

```text
结构
-> 时间引动
-> 状态变化
-> 主链切换
-> 轨迹生成
```

这是 V20 / V21 最关键的新核心层。

## 核心理念

系统未来的核心不再是“命中了什么规则”，而是“结构如何随时间演化”。

这才是真正接近命理动态系统的方向。
