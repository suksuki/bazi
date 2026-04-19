# V17 格局插件：古典格局定义与动态来源评估（v1）

> 目的：回答“当前格局是否全面？”与“如何在大运/流年下动态表达格局来源？”

## 先说结论
- 当前是**“核心骨架已上线 + 古典全集仍未全部实现”**。
- 我们已经有：
  - 轴线主导（`classical.pattern.axis.v1`）
  - 建禄/月令（月劫）方向（`classical.pattern.jianlu_yuejie.v1`）
  - 从势候选（`classical.pattern.congshi.v1`）
  - 财官协同（`classical.pattern.finance_officer.v1`）
  - 冲突裁决链（`resolver / formation_gate / break_guard`）
  - 十神分层表述（`ten_god_pattern`）
  - 动态来源标签（本次新增 `classical.pattern.dynamic_scope.v1`）
- 现阶段仍是“分层骨架”，并未覆盖全部古典格局命名体系。
- 本版明确：**古典/格局类插件不直接修改十神数值**。其任务是输出结构观察、候选与置信度，再由决策层与统一融合层做智能加权。

## 已有格局插件清单与覆盖类型

| 模块 | 覆盖类型 | 说明 |
| --- | --- | --- |
| `classical.pattern.axis.v1` | 主轴识别（软判定） | 输出最强十神主轴与匹配度 |
| `classical.pattern.jianlu_yuejie.v1` | 月令候选 | 月令主气落在比劫支撑下，输出建禄/月劫方向 |
| `classical.pattern.congshi.v1` | 从势/从强候选 | 一枝独强条件门槛后输出 |
| `classical.pattern.finance_officer.v1` | 财官协同候选 | 正官/七杀与财星并举门槛 |
| `classical.pattern.resolver.v1` | 候选冲突显性化 | 处理候选并存冲突 |
| `classical.pattern.formation_gate.v1` | 成格成候检验 | 将候选收敛为成格信号 |
| `classical.pattern.break_guard.v1` | 破格风险预警 | 结合冲刑害/六害等干扰输出 |
| `classical.pattern.dynamic_scope.v1`（新增） | 动态来源标注 | 以原局/大运/流年来源权重标注动态格局来源 |
| `ten_god_pattern.py` | 统一主轴叙事 | 输出“格局表述”与 family mix |

## 尚未完整实现（优先级从高到低）
1. 子平系统中的古典格局命名体系（如部分从重/从弱、化气/扶抑路径）
2. 盲派核心细分类别到格局级输出的系统化映射
3. “同一个命局可多格并存”的连续权重化评分体系（目前有混合评分雏形）
4. 格局与十神分布之间的可学习映射（当前先以规则可解释为主）

## 古典格局定义建议（分层表达）

### 1）十神主轴族（已具备“候选+来源”框架）
- 食神格 / 伤官格 / 正官格 / 七杀格 / 财官格 / 比劫格 / 印绶格
- 实施路径：以 `pattern_specializations` 统一为候选族，统一进入冲突裁决与来源标注链路

### 2）关系生成型（需进一步拆分）
- 三合局、六合局、六合/三刑/六害、六冲的“格局化”输出
- 目前这部分主要仍保留在 L1/L2 结构插件（`l1.physics.*`）
- 下一步建议：对每个关系族新增独立 `pattern_*` 专题映射，统一到候选族标准字段

### 3）应期式格局（盲派/子平）
- 盲派做功主轴和应用链、应期窗与象法已存在
- 需把“格局归属”作为并行输出层挂接决策树（非再重复推高权重）

## 动态格局：大运/流年来源策略（本版）

### 来源定义
- `origin_type` 来自交互矩阵每条关系的 `pillars` 或 `origin_type` 字段
- 支持来源：`natal`, `luck_background`, `luck_only`, `flow_trigger`, `flow_only`, `runtime_pair`
- 插件输出层补充 `mixed`（混合）语义

### 动态来源输出
- 新插件：`classical.pattern.dynamic_scope.v1`
- 输出关键字段：
  - `pattern_scope`：`natal / luck_background / luck_only / flow_trigger / flow_only / runtime_pair / mixed`
  - `pattern_scope_label`：用户可读描述
  - `scope_weights`：来源权重归一化
  - `pattern_mix_mode: dynamic_scope`
  - `pattern_dynamic_candidates`：当期候选列表及得分

### 说明
- 当前实现是“关系参与层证据”加权，不等于强制决策。
- 后续可升级为“每个候选独立来源”

## 建议的下一步（你这条线直接落地）
1. 坚持“古典仅观察”协议：所有 `classical.*` 与 `ten_god_pattern` 插件只输出 `observe_only` 事实，不产生 `impact_ratio`。
2. 在 `decision_compiler` 加入二次守门：任何来自 `classical.*` 的已持久化行如带 `physical_impact`，都在装配到 `compile_pending_decisions` 时清空。
1. 用同一套 `claim/conflict` 元数据把“古典格局全集”补齐为候选目录（先完整列举命名，不追求一次全实现）。
2. 为每条古典格局定义默认阈值（`*_min`、`*_ratio`）与“来源依赖（natal/luck/flow）”。
3. 在 `classical.pattern.dynamic_scope.v1` 增加“候选级别来源”而非全局来源。
4. UI 先显示：**格局主张 + 来源权重** 两层，保留你当前“先读事实后读描述”的流向。
