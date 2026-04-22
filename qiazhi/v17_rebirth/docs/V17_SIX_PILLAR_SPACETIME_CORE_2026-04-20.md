# V17 六柱时空作用核心设计

日期：2026-04-20  
状态：已立项，进入第一版骨架落地  
定位：核心引擎，不属于普通插件

## 1. 核心结论

“用神 / 忌神” 不应由十神强弱排序直接代替，而应由一套独立的核心求解器裁决：

- 基于六柱静态结构
- 基于大运、流年的引动
- 基于干支分层与合法传导
- 基于做功路径的正负效应
- 最终输出多候选、带置信度的体用裁决

这套能力不仅服务于 `用神 / 忌神`，也将反向约束：

- 关系插件的传播算法
- 动态做功的统一量化
- 插件冲突裁决的证据来源
- 主页面叙事的体用锚点

## 2. 架构定位

它不是插件家族的一员，而是：

- 插件之上的“核心求解层”
- 物理层与专题插件之间的桥梁
- Admin 中应单独展示的 Core Engine

推荐拓扑：

1. `pillar_graph_kernel.py`
2. `work_path_engine.py`
3. `effect_resolver.py`
4. `god_ring_resolver.py`

## 3. 六柱图模型

### 3.1 节点

- 年干、年支
- 月干、月支
- 日干、日支
- 时干、时支
- 运干、运支
- 流干、流支
- 必要时扩展至藏干节点

### 3.2 边

- `intra_pillar`：同柱干支
- `adjacent_pillar`：相邻柱
- `skip_pillar`：隔柱
- `dynamic_trigger`：运、流对原局的引动
- `projection_bridge`：透干、通根、藏干显影形成的合法桥

### 3.3 核心权重

- `position_weight`
- `distance_weight`
- `origin_weight`
- `transmission_gain`
- `damping`

## 4. 柱位与距离权重

第一版工程默认：

### 4.1 柱位权重

- 月柱：`1.00`
- 日柱：`0.92`
- 时柱：`0.85`
- 年柱：`0.72`
- 大运：`0.88`
- 流年：`0.56`

### 4.2 距离权重

- 同柱：`1.00`
- 相邻：`0.78`
- 隔柱：`0.52`
- 远隔：`0.31`

### 4.3 运流引动权重

当前 runtime field 宪法（2026-04-22 对齐版）：

- 大运 -> 日柱：`1.00`，`background_core`
- 大运 -> 月柱：`0.96`，`background_field`
- 大运 -> 时柱：`0.80`，`background_periphery`
- 大运 -> 年柱：`0.74`，`background_periphery`
- 流年 -> 日柱：`0.90`，`yearly_trigger`
- 流年 -> 月柱：`0.84`，`seasonal_trigger`
- 流年 -> 时柱：`0.72`，`peripheral_trigger`
- 流年 -> 年柱：`0.64`，`peripheral_trigger`
- 大运 <-> 流年：`0.88`，`runtime_cascade`

补充说明：

- `大运 = 背景场`
- `流年 = 年度扰动`
- 核心锚点优先顺序：`日柱/日支 > 月柱/月令 > 时柱 > 年柱`
- 这里的 Core 图边权不等于 L0 根气层的 `ROOT_SCOPE_WEIGHTS`
- L0 根气层当前口径是：`month 1.00 > luck 0.92 > hour 0.82 > day 0.68 > year 0.48 > flow 0.42`

## 5. 三层求解

### 5.1 Graph Kernel

负责构建六柱时空图：

- 节点注册
- 边注册
- 柱位和距离矩阵
- 干支合法传导规则

### 5.2 Work Path Engine

负责枚举和评分做功路径：

- `七杀 -> 正印 -> 日主`
- `食神 -> 七杀`
- `伤官 -> 正官`
- `财 -> 官 -> 印 -> 身`

每条路径计算：

- `activation`
- `transmission`
- `loss`
- `stability`
- `net_effect`

公式建议：

`PathScore = SourceStrength × Activation × Transmission × Stability × (1 - Loss)`

### 5.3 Effect Resolver

按十神汇总：

- `benefit_score`
- `harm_score`
- `activation_score`
- `purity_score`
- `net_utility`

最终给出：

- `use_candidates`
- `taboo_candidates`
- `dual_role_candidates`
- `authority_reason`
- `confidence`

## 6. 干支分层宪法

默认原则：

- 天干先独立算
- 地支先独立算
- 藏干属于地支内层，不自动等同明干
- 干支只有在“合法传导边”成立时才互相作用

合法传导边优先级：

1. 同柱呼应
2. 透干成立
3. 三合 / 三会 / 六合成势
4. 强冲 / 强刑 / 强合化改变结构

从 2026-04-21 起，L0 根气层已接入“动态关系量化”：

- 合向增益：`三合 / 三会 / 半合 / 六合 / 暗合`
- 冲耗折损：`六冲 / 六害 / 六破 / 三刑`
- 相克传导：按相邻关键柱位（年-月、月-日、日-时、月-运、运-流）计算“谁克谁”的正负位移
- 天干五合效率：不再二值化，改为独立协议，按 `可见支撑 + 地支根气 + 争合/支扰阻尼` 计算 `0~1` 的合化效率，再温和折算到根气增减

从 2026-04-22 起，关系类统一按双轴解释：

- `能量轴 (E)`：看是否激发、内耗、压制转移、组织化、绑定、解构
- `稳定性轴 (S)`：看结构是否变稳或变脆

对应口径：

- `冲`：`E` 常上升为事件激发，`S` 必降
- `刑`：`E` 多转为内耗，`S` 下降
- `克`：`E` 为方向性压制/转移，被克方 `S` 下降
- `害`：`E` 缓慢暗损，`S` 下降
- `破`：原结构 `S` 大幅下降，能量转为游离/重组
- `合`：`S` 常上升，但 `E` 更偏组织化/锁定，不视为总量线性增加

运流耦合改按“场模型”解释：

- `大运 = 背景场`
- `流年 = 扰动触发`
- Core 图中的优先耦合顺序为：`日柱/日支 > 月柱/月令 > 时柱 > 年柱`

补充约束：

- 旁支重复（同组三会/三合出现重复支）会提高强度
- 被冲刑的成员会触发合势衰减（冲后降效）
- 所有动态增减都会做“单神上限裁剪”，避免动态层吞掉静态根气主干
- `通根` 与 `透干` 虽然互为镜像，但协议上必须单向定义：
  - `通根` = `天干 <- 地支藏干`
  - `透干` = `地支藏干 -> 天干`
- 二者都只允许读取冻结盘面证据做单次耦合，禁止把结算后的结果重新回灌为下一轮根气/透干证据

从 2026-04-21 起，做功证据还应尽量显式标注 `actor / receiver`：

- `actor_members`
- `receiver_members`
- `actor_gods`
- `receiver_gods`

含义：

- `actor` 表示主动发力的一侧
- `receiver` 表示受作用的一侧
- 核心层会把二者映射到六柱图上，按柱位远近与有向边权计算传导强弱
- 同一关系下，`月 -> 日 / 时` 通常强于 `年 -> 时`
- 这套“方向距离”属于做功与传导层，不等同于根气

## 7. 对插件体系的要求

插件未来应从“直接判定结论”升级为“提供证据和路径片段”：

- 输出静态依据
- 输出关系成员
- 输出 actor / receiver
- 输出来源层（原局 / 运 / 流）
- 输出正负向影响
- 输出可传播目标

换句话说：

- 插件继续存在
- 但插件不再直接拥有最终解释权
- 核心层负责统一求解

## 8. Admin 展示原则

Core Engine 不应伪装成普通插件。

Admin 应单独有一块：

- `Six-Pillar Spacetime Core`
- 当前权重矩阵
- 做功路径计数
- 当前体用裁决来源
- 是否处于降级模式（fallback）

插件页继续展示插件，核心页展示核心。

## 9. 第一版落地范围

本轮只做骨架，不做全量命理完成版：

1. 建立图节点 / 边模型
2. 建立路径枚举骨架
3. 建立按目标神汇总的效应裁决骨架
4. 建立 god ring resolver 的核心接口
5. Admin 显示为独立 Core Engine Panel

## 10. 后续阶段

### 阶段 A

- 接入现有关系插件产出的做功证据
- 替换掉“强弱排序 = 用忌”的旧链路

### 阶段 B

- 对齐三合、六合、刑冲克害、透干、通根、月令
- 引入更细的跨层传导条件

### 阶段 C

- 用真实样盘做参数校准
- 允许多用神 / 多忌神 / 双刃神并存
- 形成体用、做功、应期的一体化求解

## 11. 动态做功通量（M1）

从 2026-04-21 起，Core Engine 增加 `Dynamic Work Flux v2 (M1)`：

- 目标：
  - 把离散 `WorkPath` 升级为有方向、有符号、可回溯的做功链条
  - 在不破坏现有裁决链路的前提下，提供“正向传导 + 逆向归因”证据

- 实现位置：
  - `backend/logic/core_engine/flux_solver.py`
  - `resolve_god_ring_core` 中统一执行

- 输出：
  - `flux_meta.edge_count / chain_count / top_chains / sink_summary`
  - `effect_scores[*].flux_benefit / flux_harm / flux_net / flux_top_causes`
  - `effect_scores[*].resolved_utility_base / resolved_utility_flux`

- 当前策略（稳态优先）：
  - 不直接覆盖旧的 `resolved_utility`，先以扩展字段并行观察
  - 链路深度默认 `max_depth=3`
  - 每条链路使用有界效率，避免数值爆炸

## 12. 动态做功通量（M2）

从 2026-04-21 起继续扩展为“柱位节点级链路”：

- 在 God 链路之外，新增 Node 链路（`year/month/day/hour/luck/flow` 的 `stem/branch` 节点）。
- Node 边来源于 `actor_nodes -> receiver_nodes`（插件证据），并结合图内距离权重与方向因子。
- Node 链路先独立求解，再投影回十神，形成可解释的逆向归因。

新增输出：

- `flux_meta.node_edges / node_top_chains / node_sink_summary`
- `flux_meta.projected_top_chains / projected_sink_summary`
- `graph_meta.flux_node_edge_count / flux_node_chain_count`

意义：

- 能直接看到“年干 -> 月干 -> 日支 -> 目标十神”这类链条，不再只有抽象十神节点。

## 13. 动态做功通量（M3）

从 2026-04-21 起继续扩展“方向合力/抗力”分析：

- 在已有链路基础上，新增方向矩阵（source -> target）聚合：
  - 正向合力（benefit）
  - 负向抗力（harm）
  - 净方向效应（net）
  - 支配度与深度（dominance / avg_depth）
- 新增双向回路检测：
  - 同向放大（reinforce）
  - 对冲拉扯（tension）

新增输出：

- `flux_meta.interaction_count / interaction_matrix`
- `flux_meta.tension_pair_count / tension_pairs`
- `graph_meta.flux_interaction_count / flux_tension_pair_count`

意义：

- 从“看单条链”升级为“看系统力场”。
- 能快速定位谁在推动、谁在对冲，以及哪些双向关系会导致放大或拉扯。

Prompt 对齐：

- `PhysicsCanonicalService.materialize_prompt_lines()` 需将 M3 摘要前置到 LLM user prompt 前段。
- 至少应包含：
  - 一条“做功解释合同”
  - 一条“做功方向矩阵”摘要
  - 一条“做功回路”摘要
- 原因：
  - 当前 `llm_user_prompt` 只截取前 16 条事实，M3 若挂在末尾将无法被模型看到。

决策对齐：

- `effect_scores` 现已附带：
  - `flux_tension_load`
  - `flux_reinforce_load`
  - `flux_out_support / flux_out_resist / flux_out_net`
- `pick_god_candidates()` 应优先使用 `resolved_utility_flux` 并参考张力/放大载荷，而不再只看旧的 `net_utility / harm_score`。
- `build_knowledge_snapshot() / route_conflicts()` 应读取当前盘面的实时张力，作为冲突分流的现场证据。
