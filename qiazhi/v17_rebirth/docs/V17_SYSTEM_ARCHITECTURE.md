# V17 系统总架构

## 1. 目标

V17 不是一个“把规则堆在一起的八字程序”，而是一套分层的命理计算与推理系统。

它的目标有四个：

1. 把静态盘面和动态作用严格拆开。
2. 把插件从零散规则升级成统一协议下的插件家族。
3. 把命理师的判断轨迹沉淀成系统可读的推理层。
4. 把裁决、叙事、UI 都建立在同一套物理与法理之上。

---

## 2. 总体分层

### L0：静态底盘层

职责：

- 只计算盘面本体，不处理做功、冲合、刑害的动态后果
- 输出十神基础能量 `ten_gods_base_l0`
- 计算：
  - 月令
  - 透干
  - 藏干
  - 通根
  - 成局基础势
  - 运支/流支进入后的静态背景

代表模块：

- [ten_gods_engine.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py)
- [foundation_projection.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L0_physics_fields/foundation_projection.py)

原则：

- 当令可以放大本气与相生
- 月令“所克”不在 L0 直接压低目标元素本体
- 三合等强结构在 L0 只给基础结构回灌，不做高层解释

### L1：原子动态关系层

职责：

- 在 L0 底盘之上计算动态作用
- 关系必须建立在静态证据之上
- 输出原子级 fact / claim / proposal

典型关系：

- 六冲
- 六合
- 六害
- 六破
- 三合
- 天干五合
- 墓库

代表模块：

- [three_harmony.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L1_atomic_ops/three_harmony.py)
- [six_harmony.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L1_atomic_ops/six_harmony.py)
- [six_pierce.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L1_atomic_ops/six_pierce.py)
- [six_break.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L1_atomic_ops/six_break.py)
- [stem_fusion.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L1_atomic_ops/stem_fusion.py)

统一协议：

- `condition_state`
- `origin_type`
- `match_ratio`
- `target_god`
- `cluster_projection`
- `projection_share`
- `static_basis`

### L2：结构专题层

职责：

- 对 L1 原子事实做结构解释
- 形成格局、子平、盲派、风险等专题判断
- 默认负责描述、归纳、裁决建议
- 默认不直接改写十神物理值

代表专题：

- 格局
- 子平/旺衰
- 盲派
- 风险矩阵
- 神煞

代表模块：

- [pattern_specializations.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L2_structure_patterns/pattern_specializations.py)
- [ziping_family.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L2_structure_patterns/ziping_family.py)
- [blind_school_family.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L2_structure_patterns/blind_school_family.py)
- [risk_matrix.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/logic/L2_structure_patterns/risk_matrix.py)

### MasterReasoningLayer：命理师推理层

职责：

- 不改物理
- 记录命理师判盘轨迹
- 保存主导证据与被压制证据
- 为未来学习和反馈吸收提供结构入口

代表模块与协议：

- [master_reasoning.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/backend/services/master_reasoning.py)
- [V17_MASTER_REASONING_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_MASTER_REASONING_PROTOCOL.md)

### Decision / LLM / UI 层

职责：

- 呈现、裁决、叙事、追溯
- 不应越权改写物理底盘
- 用户手动裁决和系统自动处理在这里发生

代表模块：

- `decision_compiler`
- `verdict_orchestrator`
- `Decision Inbox`
- `TracePanel`
- `Oracle / Admin`

---

## 3. 数据主链

系统主链如下：

1. `L0` 计算 `ten_gods_base_l0`
2. hydration 生成 `interaction_v2`
3. `L1/L2` 插件产出 `fact / claim / proposal`
4. 冲突层检测互斥、跨层覆盖、同目标冲突
5. 结算层只读取批准 proposal
6. `L1 Runtime = Recompute(L0 Base, approved proposals)`
7. `MasterReasoningLayer` 生成判盘轨迹
8. UI / LLM / 裁决系统读取统一快照

---

## 4. 核心设计原则

### 4.1 先看盘面，再看动象

动态结果应遵循：

`动态结果 = 静态底盘 × 条件成立度 × 引动系数 × 破坏/阻尼系数`

### 4.2 高层默认不改物理

默认允许改写十神的，主要保留在：

- `L0`
- `L1`

以下层默认以描述、判断、裁决为主：

- `L2`
- `MasterReasoningLayer`
- LLM 叙事

### 4.3 运主背景，年主引动

系统当前法理：

- 大运：偏背景延续
- 流年：偏触发与引动

这不只是权重差别，也已固化到关系来源权重中（见
[V17_CROSS_LAYER_INTERACTION_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_CROSS_LAYER_INTERACTION_PROTOCOL.md)）：

- `natal=1.0`
- `luck_background=0.98`
- `mixed=0.94`
- `runtime_pair=0.95`
- `flow_trigger=0.9`
- `flow_only=0.78`

### 4.4 同一元素簇不等于同一十神角色

例如：

- `辛透`：纯七杀直透
- `庚透`：正官直透，对七杀仅为同元素旁助

系统不能只按五行元素簇平均分配，必须保留十神角色差异。

### 4.5 成局内部不平均

以三合为例：

- 中神：最高权重
- 墓库：次高权重
- 生地/起势支：最低权重

重复支也需按角色分开累计，而不能只有一个总 `duplicate_count`。

---

## 5. 当前协议版图

### 已正式进入主链的协议

- [V17_PLUGIN_MATCH_RECOMPUTE_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_MATCH_RECOMPUTE_PROTOCOL.md)
- [V17_MASTER_REASONING_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_MASTER_REASONING_PROTOCOL.md)

### 应继续建立的协议

- `V17_CROSS_LAYER_INTERACTION_PROTOCOL.md`
  用于定义：
  - 天干层
  - 地支层
  - 藏干层
  - 显化跨层层

---

## 6. UI 对应关系

当前 UI 的职责划分：

- `Oracle`：用户看盘主界面
- `Admin`：结构与协议观测台
- `TracePanel`：快照、因果链与调试
- `Decision Inbox`：手动入口与自动处理结果

这些界面应统一围绕以下字段说话：

- `target_god`
- `cluster_projection`
- `projection_share`
- `static_basis`
- `master_reasoning`

---

## 7. 下一阶段

当前插件主线已经基本完成，下一阶段重点不再是“补基础设施”，而是：

1. 跨层交互法理协议化
2. 命理师推理链持续吸收
3. 专题口感校准
4. 真实盘与合成盘双轨验证

---

## 8. 总结

V17 当前最重要的变化，不是插件变多了，而是系统开始具备：

- 分层
- 协议
- 因果链
- 可学习入口

这意味着它正在从“规则引擎”向“会按命理师思路走路径的系统”过渡。
