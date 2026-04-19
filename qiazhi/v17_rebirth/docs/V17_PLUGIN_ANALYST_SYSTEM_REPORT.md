# V17 插件系统审计总报告

## 1. 报告目的

本报告面向分析师，目标不是解释某一支插件的单点代码，而是给出当前 V17 插件系统的完整、可审计视图：

1. 当前到底有哪些插件。
2. 哪些插件带参数，参数默认值是什么，配置文件在哪里。
3. 插件“命中”之后，如何进入 `fact -> claim -> proposal -> conflict -> settlement` 链路。
4. 当前匹配度量化、统一结算、冲突裁决分别采用什么算法。
5. 当前系统还存在哪些已知偏差、制度缺口与下一步校准重点。

本报告聚焦 **插件系统本身**，不展开 UI、LLM Prompt 编排、Decision Inbox 交互等外围问题。

---

## 2. 总体结论

当前 V17 插件系统已经从“散乱规则堆”进入“可维护、可审计、可扩展”的阶段。

可以确认成立的点：

1. 插件已经按家族化分层。
2. 关键缺失插件已补成正式入口。
3. 参数化核心插件已有配置文件与测试保护。
4. 关系类插件已具备 `condition_state` 与 `match_ratio`。
5. 统一结算已从“沿 runtime 叠乘”改为 **按 L0 Base 重算 L1 Runtime**。
6. 格局候选已经能进入冲突层，而不是只在页面上并列显示。

但也必须明确：

1. 这不意味着所有命理专题都已达到终局模型。
2. 当前的 `match_ratio` 不是统计学概率，而是工程化的“成立程度”量化。
3. 现阶段最适合优化的是 **插件匹配公式、冲突法理、重算稳定性**，不是试图让系统自动学习所有八字常数。

---

## 3. 插件执行总链路

当前插件链路分为八段：

### 3.1 L0 物理基线生成

入口：

- `ten_gods_engine.calc_deity_scores()`
- 文件：`backend/logic/L0_physics_fields/ten_gods_engine.py`

职责：

- 以四柱 / 大运 / 流年为输入，计算 `ten_gods_base_l0`
- 输出月令、藏干、通根、透干、旬空、性别微调等基础能量

### 3.2 Hydration 几何层

入口：

- `hydrate_v17_physics_tensor()`
- 文件：`backend/logic/L1_atomic_ops/l1_meta_hydration.py`

职责：

- 从 `four_pillars/luck_pillar/flow_pillar` 推导 `interaction_v2`
- 几何探测：
  - 六冲
  - 六合
  - 六害
  - 六破
  - 三合 / 半合
  - 三刑
  - 天干五合 case
- 建立 manifest hit / geometry rows / pending decisions 的原始池

### 3.3 插件事实采集

入口：

- `collect_all_spec_facts()`
- 文件：`backend/logic/plugin_discovery.py`

职责：

- 自动扫描 L0~L3 插件
- 调用各插件 `collect_v17_facts()`
- 产出统一 `V17Fact`

### 3.4 Claim 编译

入口：

- `compile_claims()`
- 文件：`backend/services/claim_protocol.py`

职责：

- 把 `V17Fact` 变为结构化 `Claim`
- 注入：
  - `claim_type`
  - `entity_scope`
  - `logic_level`
  - `exclusivity_key`
  - `intent_vector`
  - `confidence`
  - `match_ratio`

### 3.5 Proposal 编译

入口：

- `compile_modifier_proposals()`
- 文件：`backend/services/decision_compiler.py`

职责：

- 只对带 `impact_ratio` 的 Fact 生成 proposal
- 现在的关键公式：

```text
proposal.impact_ratio = raw_impact_ratio × match_ratio
```

也就是说：

- 插件原始位移是“理论最大位移”
- `match_ratio` 决定这次命中的实际落地比例

### 3.6 冲突检测与裁决建议

入口：

- `detect_claim_conflicts()`
- `recommend_conflict_resolutions()`
- 文件：`backend/services/conflict_detector.py`

职责：

- 检测重复、互斥、方向相反、格局家族冲突等问题
- 当前已正式支持：
  - `pattern_family_exclusive`

### 3.7 Settlement 统一结算

入口：

- `settle_modifier_proposals()`
- 文件：`backend/services/physics_layers.py`

当前核心变更：

```text
L1 Runtime = Recompute(L0 Base, approved proposals)
```

而不是：

```text
L1 Runtime = Old Runtime × (1 + next proposal ...)
```

这意味着：

- 插件结算不再沿污染 runtime 累乘
- 每轮都以 `ten_gods_base_l0` 为起点重新归算

并留下：

- `plugin_recompute_contributions`
  - `before`
  - `after`
  - `ratio_total`
  - `delta_abs`

### 3.8 Runtime 同步与前端显影

入口：

- `sync_runtime_aliases()`
- 前端：
  - `frontend/app/v17/oracle/page.tsx`
  - `frontend/app/v17/admin/page.tsx`

职责：

- 把重算后的 runtime 同步回兼容字段
- 在页面上显示：
  - 插件命中度 %
  - 本轮 base recompute 贡献值

---

## 4. 插件注册总表

以下为当前自动扫描到的正式插件集合，按层级列出。

### 4.1 L5 / L0 基础与基线插件

| plugin_id | 类 | 文件 | priority | 说明 |
| --- | --- | --- | ---: | --- |
| `sys.core.physics` | `SysCorePhysicsStub` | `registry_parity_l0.py` | 0.996 | 核心物理基线显影 |
| `base.chronos` | `BaseChronosStub` | `registry_parity_l0.py` | 0.94 | 时间基线显影 |
| `l0.foundation.month_command.v1` | `MonthCommandFoundationPlugin` | `foundation_projection.py` | 0.72 | 月令主气可见化 |
| `l1.physics.op_status` | `ChangSheng12Plugin` | `chang_sheng_12.py` | 0.72 | 十二长生状态 / 抗性 |
| `l0.foundation.rooted_stems.v1` | `RootedStemsFoundationPlugin` | `foundation_projection.py` | 0.67 | 通根可见化 |
| `l0.foundation.hidden_stems.v1` | `HiddenStemsFoundationPlugin` | `foundation_projection.py` | 0.66 | 藏干可见化 |
| `l0.foundation.exposed_hidden_stems.v1` | `ExposedHiddenFoundationPlugin` | `foundation_projection.py` | 0.65 | 透干可见化 |

### 4.2 L4 / L1 原子关系插件

| plugin_id | 类 | 文件 | priority | 类型 |
| --- | --- | --- | ---: | --- |
| `l1.physics.op_geography` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.78 | manifest 动态算子 |
| `l1.physics.op_branch_liuchong` | `SixClashPlugin` | `six_clash.py` | 0.77 | 六冲 |
| `l1.physics.op_vertical_crush` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.77 | manifest 动态算子 |
| `l1.physics.op_branch_banhe` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.75 | 半合动态算子 |
| `l1.physics.op_branch_anhe` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.74 | 暗合动态算子 |
| `l1.physics.op_branch_sanhe` | `ThreeHarmonyPlugin` | `three_harmony.py` | 0.68 | 三合 / 半合 |
| `l1.physics.op_stem_fusion_stuck` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.67 | 五合羁绊 manifest |
| `l1.physics.op_stem_fusion_transform` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.66 | 五合化气 manifest |
| `l1.physics.op_blade_clash` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.65 | 羊刃冲突 manifest |
| `l1.physics.op_owl_food` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.64 | 枭神夺食 manifest |
| `l1.physics.op_robber_wealth` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.63 | 劫财夺财 manifest |
| `l1.physics.op_branch_liuhai` | `SixPiercePlugin` | `six_pierce.py` | 0.62 | 六害 / 六穿 |
| `l1.physics.op_gov_kill_mix` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.62 | 官杀混杂 manifest |
| `l1.physics.op_wealth_seal` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.61 | 财印结构 manifest |
| `l1.physics.op_connection` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.60 | 生助连接 manifest |
| `l1.physics.op_production` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.59 | 生出 manifest |
| `l1.physics.op_destruction` | `ManifestOperatorPlugin` | `dynamic_manifest_plugins.py` | 0.58 | 破坏 manifest |
| `l1.physics.op_branch_liuhe` | `SixHarmonyPlugin` | `six_harmony.py` | - | 六合 |
| `l1.physics.op_branch_liupo` | `SixBreakPlugin` | `six_break.py` | - | 六破 |
| `l1.physics.op_branch_muku` | `MukuGatePlugin` | `muku_gate.py` | - | 墓库门态 |
| `l1.physics.op_stem_fusion` | `StemFusionPlugin` | `stem_fusion.py` | - | 天干五合 |

### 4.3 L3 / L2 结构、格局、盲派、风险插件

| plugin_id | 类 | 文件 | priority | 类型 |
| --- | --- | --- | ---: | --- |
| `classical.climate_adjuster.v1` | `ClimateAdjusterStub` | `registry_parity_l2.py` | 0.88 | 调候 |
| `classical.conflict_auditor.v1` | `ConflictAuditorStub` | `registry_parity_l2.py` | 0.87 | 冲突审计 |
| `l1.physics.op_branch_sanxing` | `TripleBranchPenaltyPlugin` | `triple_branch_penalty.py` | 0.85 | 三刑 |
| `classical.pattern_detector.v2` | `PatternDetectorV2` | `registry_parity_l2.py` | 0.84 | 旧格局显影 |
| `classical.ziping.month_command.v1` | `ZiPingMonthCommandPlugin` | `ziping_family.py` | 0.83 | 子平月令法 |
| `classical.ziping.balance.v1` | `ZiPingBalancePlugin` | `ziping_family.py` | 0.82 | 子平旺衰平衡 |
| `classical.blind_school.v1` | `BlindSchoolV1` | `registry_parity_l2.py` | 0.81 | 旧盲派显影 |
| `classical.pattern.resolver.v1` | `PatternResolverPlugin` | `pattern_specializations.py` | 0.81 | 格局冲突裁决 |
| `classical.pattern.formation_gate.v1` | `PatternFormationGatePlugin` | `pattern_specializations.py` | 0.80 | 成格条件 |
| `classical.ziping.yongshen.v1` | `ZiPingYongShenPlugin` | `ziping_family.py` | 0.80 | 子平用神建议 |
| `classical.blind.work_axis.v1` | `BlindWorkAxisPlugin` | `blind_school_family.py` | 0.79 | 盲派做功主轴 |
| `classical.pattern.break_guard.v1` | `PatternBreakGuardPlugin` | `pattern_specializations.py` | 0.79 | 破格预警 |
| `classical.blind.response_chain.v1` | `BlindResponseChainPlugin` | `blind_school_family.py` | 0.78 | 盲派应链 |
| `classical.pattern.axis.v1` | `PatternAxisPlugin` | `pattern_specializations.py` | 0.77 | 格局轴线 |
| `classical.blind.symbol_trigger.v1` | `BlindSymbolTriggerPlugin` | `blind_school_family.py` | 0.76 | 盲派触发象 |
| `classical.blind.timing_window.v1` | `BlindTimingWindowPlugin` | `blind_school_family.py` | 0.75 | 盲派应期窗 |
| `classical.pattern.jianlu_yuejie.v1` | `JianLuYueJiePlugin` | `pattern_specializations.py` | 0.75 | 建禄 / 月劫 |
| `classical.blind.summary.v1` | `BlindSummaryPlugin` | `blind_school_family.py` | 0.74 | 盲派断口收束 |
| `classical.pattern.congshi.v1` | `CongShiPlugin` | `pattern_specializations.py` | 0.74 | 从势候选 |
| `classical.pattern.finance_officer.v1` | `FinanceOfficerPatternPlugin` | `pattern_specializations.py` | 0.73 | 财官协同 |
| `kong_wang` | `KongWangPlugin` | `kong_wang.py` | 0.58 | 空亡 |
| `ten_god_pattern` | `TenGodPatternPlugin` | `ten_god_pattern.py` | 0.55 | 十神主轴格局 |
| `shensha` | `ShenshaPlugin` | `shensha.py` | 0.52 | 神煞 |

### 4.4 L2 / L3 现代叙事与风险插件

| plugin_id | 类 | 文件 | priority | 类型 |
| --- | --- | --- | ---: | --- |
| `modern.will_proxy.v1` | `WillProxyV1Stub` | `registry_parity_l3.py` | 0.94 | 现代意图代理 |
| `modern.wealth_risk.v1` | `WealthRiskV1Stub` | `registry_parity_l3.py` | 0.56 | 现代财富风险 |
| `l2.risk.risk_matrix` | `RiskMatrixPlugin` | `risk_matrix.py` | - | 羊刃/枭神/官伤风险矩阵 |

---

## 5. 参数化插件总表

以下表格只列 **当前声明了 `DECLARED_PARAMS` 的插件**。没有出现在此表中的插件，当前视为“无显式参数插件”。

| plugin_id / 文件 | 参数 | 默认值 | 配置文件 |
| --- | --- | --- | --- |
| `l1.physics.op_status` / `chang_sheng_12.py` | `RESISTANCE_HIGH` | `1.2` | `configs/l1.physics.op_status.json` |
|  | `RESISTANCE_LOW` | `0.7` | 同上 |
|  | `STAGE_PRIORITY` | `0.85` | 同上 |
| `l1.physics.op_branch_sanhe` / `three_harmony.py` | `FUSION_MID_GAIN` | `1.45` | `configs/l1.physics.op_branch_sanhe.json` |
|  | `LOCK_RATIO` | `0.35` | 同上 |
|  | `MIN_HARMONY_STRESS` | `0.40` | 同上 |
| `l1.physics.op_branch_liuhe` / `six_harmony.py` | `HARMONY_GAIN` | `1.15` | `configs/l1.physics.op_branch_liuhe.json` |
|  | `STABILITY_WEIGHT` | `0.85` | 同上 |
| `l1.physics.op_branch_liupo` / `six_break.py` | `BREAK_LOSS` | `0.08` | `configs/l1.physics.op_branch_liupo.json` |
|  | `FRICTION_COEFF` | `0.25` | 同上 |
| `l1.physics.op_branch_liuhai` / `six_pierce.py` | `PENETRATION_RATIO` | `0.45` | `configs/l1.physics.op_branch_liuhai.json` |
|  | `CLASH_LOSS_RATIO` | `ref(global.CLASH_LOSS_RATIO)` | 同上 |
| `l1.physics.op_branch_muku` / `muku_gate.py` | `STORAGE_EFFICIENCY` | `0.35` | `configs/l1.physics.op_branch_muku.json` |
|  | `OPEN_GATE_BOOST` | `1.50` | 同上 |
| `l1.physics.op_stem_fusion` / `stem_fusion.py` | `TRANSFORM_EFFICIENCY` | `0.85` | `configs/l1.physics.op_stem_fusion.json` |
|  | `STUCK_DAMPING` | `0.35` | 同上 |
| `l1.physics.op_branch_sanxing` / `triple_branch_penalty.py` | `ENTROPY_LOSS` | `0.12` | `configs/l1.physics.op_branch_sanxing.json` |
|  | `PENALTY_PRIORITY` | `0.93` | 同上 |
| `kong_wang` / `kong_wang.py` | `VOID_THRESHOLD` | `0.75` | `configs/kong_wang.json` |
|  | `EFFICIENCY` | `0.30` | 同上 |
|  | `PRIORITY` | `0.82` | 同上 |
| `ten_god_pattern` / `ten_god_pattern.py` | `GUAN_THRESHOLD` | `40.0` | `configs/ten_god_pattern.json` |
|  | `SHI_SHANG_THRESHOLD` | `35.0` | 同上 |
|  | `CAI_THRESHOLD` | `35.0` | 同上 |
|  | `PATTERN_PRIORITY` | `0.78` | 同上 |
| `shensha` / `shensha.py` | `TIAN_YI_THRESHOLD` | `40.0` | `configs/shensha.json` |
|  | `YANG_REN_THRESHOLD` | `45.0` | 同上 |
|  | `RESISTANCE_BUFF` | `0.1` | 同上 |
|  | `TENSION_MULTIPLIER` | `1.4` | 同上 |
|  | `PRIORITY_BASE` | `0.94` | 同上 |
| `l2.risk.risk_matrix` / `risk_matrix.py` | `BLADE_CLASH_IMPULSE` | `2.2` | `configs/l2.risk.risk_matrix.json` |
|  | `OWL_FOOD_CAP` | `0.4` | 同上 |
|  | `OFFICER_CRUSH_LIMIT` | `0.5` | 同上 |

说明：

1. 上表是“参数存在性与默认值”台账，不代表参数一定已经达到终极合理值。
2. 参数合理性目前应理解为“工程合理默认值”，不是“古籍唯一真值”。
3. 当前更适合校准的是 **match_ratio 与重算贡献**，不是在线自学习修改这些常数。

补充：

- 代码库中还有参数化文件，但对应插件 **未进入当前正式扫描总表**，例如：
  - `officer_see_hurt.py`
  - `l1_physics_bandwidth.py`
  - `wangshuai_v1.py`
  - `narrative_clip.py`

这些更适合被视作“旁路能力 / 待并入正式家族”的候选模块。

---

## 6. 命中模型：从二元命中到连续匹配

### 6.1 旧问题

旧模型更像：

```text
命中 = true / false
```

问题：

1. 很多命理结构本来就不是全有或全无。
2. 合化、格局、风险结构都常常只有“部分成立”。
3. 若所有命中都按 100% 处理，结算会偏硬、偏脆。

### 6.2 当前模型

当前插件可以在 `fact.meta` 中输出：

- `match_ratio: 0.0 ~ 1.0`

语义：

- `1.0`：高度成立
- `0.6`：部分成立
- `0.3`：弱候选 / 提示态

若插件未显式给出 `match_ratio`，`compile_claims()` 会做保守推导：

- `pattern_candidate`：按置信度给 0.45~0.9
- 带 `impact_ratio` 的物理插件：按位移幅度给 0.4~0.92
- `l0.foundation.*`：默认 0.5~0.72
- 其他诊断插件：默认 0.35~0.78

这一步的目的，是避免“诊断型插件默认 100% 命中”的假满分现象。

### 6.3 进入 Proposal 的公式

文件：

- `backend/services/decision_compiler.py`

核心公式：

```text
proposal.impact_ratio = raw_impact_ratio × match_ratio
```

也就是：

- 参数常数定义理论位移上限
- `match_ratio` 决定这次命中的实际落地比例

---

## 7. 条件模型：合化不是命中就生效

文件：

- `backend/logic/L1_atomic_ops/plugin_condition_protocol.py`

当前已经进入条件协议的插件：

- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_stem_fusion`
- `l1.physics.op_branch_muku`

### 7.1 条件协议输出

关系插件会输出：

- `condition_state`
- `condition_blockers`
- `condition_trigger`
- `condition_multiplier`

当前关系状态：

- `supported`
- `contested`
- `formed`
- `stuck`

### 7.2 当前规则

若条件不足：

- 插件仍可输出 `fact`
- 但 **不再一定输出可结算 proposal**

也就是说：

- “结构被观察到”
- 不等于
- “它已经有资格改写 runtime”

这一步是避免数值爆炸、假合局、假化气的关键制度。

---

## 8. 统一结算算法：从 Base 重算，而不是继续叠污染 Runtime

文件：

- `backend/services/physics_layers.py`
- `backend/logic/L1_atomic_ops/l1_meta_hydration.py`

### 8.1 当前结算口径

当前系统采用：

```text
L1 Runtime = Recompute(L0 Base, approved proposals)
```

不是：

```text
L1 Runtime = Old Runtime × (1 + next proposal)
```

### 8.2 核心收益

这解决了两个老问题：

1. 插件顺序依赖
2. 上一轮污染 runtime 继续放大下一轮误差

### 8.3 当前重算结果显影

每轮结算都会留下：

- `plugin_recompute_contributions`

每项包含：

- `target_god`
- `before`
- `after`
- `ratio_total`
- `delta_abs`

因此现在已经可以直接追踪：

- 这轮到底是谁改了哪个十神
- 改了多少
- 是增强还是削弱

---

## 9. 冲突层算法

文件：

- `backend/services/conflict_detector.py`
- `backend/services/conflict_scoring.py`
- `backend/services/arbiter_router.py`

### 9.1 输入

冲突层输入是 `plugin_claims`，不是裸 Fact。

### 9.2 关键字段

每条 Claim 现在具备：

- `claim_type`
- `entity_scope`
- `exclusivity_key`
- `intent_vector`
- `confidence`
- `match_ratio`

### 9.3 当前已经正式支持的冲突

尤其重要的是：

- `pattern_family_exclusive`

这意味着多个格局候选已经不再只是“并列显示”，而是进入正式互斥裁决链。

### 9.4 当前限制

当前冲突层已经具备法理骨架，但仍然是第一阶段：

1. 对格局候选已有互斥裁决
2. 对一般关系类插件，更多仍依赖 `exclusivity_key` 与 intent 方向
3. “复杂因果闭环”与“跨层反证”仍需要下一阶段深化

---

## 10. 各插件家族的核心算法摘要

### 10.1 L0 基础家族

文件：

- `foundation_projection.py`

算法性质：

- 只做 **可见化投影**
- 不直接参与物理位移

输出内容：

- 藏干列表
- 通根天干
- 藏干外透
- 月令主气

### 10.2 原子关系家族

#### 六冲 `l1.physics.op_branch_liuchong`

- 读取 `interaction_v2.liu_chong`
- 识别冲对的主十神
- 当前输出负向 `impact_ratio`
- `match_ratio` 由冲强度估计

#### 三合 / 半合 `l1.physics.op_branch_sanhe`

- 参数：
  - `FUSION_MID_GAIN`
  - `LOCK_RATIO`
  - `MIN_HARMONY_STRESS`
- 算法：
  - 先判几何组
  - 再判条件支持
  - 再按 `strength × condition_multiplier` 计算 `match_ratio`
  - 只有 `supported` 才出 proposal

#### 六合 `l1.physics.op_branch_liuhe`

- 参数：
  - `HARMONY_GAIN`
  - `STABILITY_WEIGHT`
- 算法：
  - 对参与支做稳定协同估计
  - `match_ratio` 由稳定权重与条件状态共同决定

#### 六害 / 六穿 `l1.physics.op_branch_liuhai`

- 参数：
  - `PENETRATION_RATIO`
  - `CLASH_LOSS_RATIO`
- 算法：
  - 估计穿透损耗
  - `match_ratio` 由穿透比率给出

#### 六破 `l1.physics.op_branch_liupo`

- 参数：
  - `BREAK_LOSS`
  - `FRICTION_COEFF`
- 算法：
  - 估计裂解损耗
  - `match_ratio` 与摩擦系数相关

#### 墓库 `l1.physics.op_branch_muku`

- 参数：
  - `STORAGE_EFFICIENCY`
  - `OPEN_GATE_BOOST`
- 算法：
  - 识别闭库 / 开库
  - 闭库为收纳负效应
  - 开库为释放正效应
  - 当前 `match_ratio` 由开闭态与条件状态决定

#### 天干五合 `l1.physics.op_stem_fusion`

- 参数：
  - `TRANSFORM_EFFICIENCY`
  - `STUCK_DAMPING`
- 算法：
  - 区分 `stuck` 与 `transformed`
  - 化气时看月令与 branch_hua_ratio
  - 羁绊态不再默认强干预

### 10.3 子平家族

文件：

- `ziping_family.py`

插件：

- `month_command`
- `balance`
- `yongshen`

算法性质：

- 更偏“专题解释 + 结构判定”
- 当前也已输出 `match_ratio`
- 暂不直接给大幅物理位移

### 10.4 格局家族

文件：

- `pattern_specializations.py`
- `ten_god_pattern.py`
- `registry_parity_l2.py` 中的 `pattern_detector.v2`

当前已形成四层：

1. 候选
2. 裁决
3. 成格条件
4. 破格预警

其中：

- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`

都已作为 `pattern_candidate` 进入冲突层。

### 10.5 盲派家族

文件：

- `blind_school_family.py`

当前已形成五段：

1. `work_axis`
2. `response_chain`
3. `symbol_trigger`
4. `timing_window`
5. `summary`

算法性质：

- 不是直接物理结算插件
- 而是高阶结构观察与断口组织插件
- 当前已输出 `match_ratio`

### 10.6 风险家族

#### `l2.risk.risk_matrix`

文件：

- `risk_matrix.py`

当前风险支路：

1. 羊刃逢冲
2. 枭神夺食
3. 伤官见官

每一支都已具备：

- 参数
- `impact_ratio`
- `match_ratio`

---

## 11. 当前真实盘校准状态

文件：

- `scripts/calibrate_plugin_match_cases.py`
- `docs/V17_PLUGIN_REAL_CHART_CALIBRATION.md`

当前校准工具可以输出：

1. 样盘四柱 / 大运 / 流年
2. `match_top`
3. `plugin_match_summary`
4. `recompute_contributions`

这意味着现在已经可以做：

- 某个插件在样盘上的平均命中度观察
- 某个插件对 runtime 的绝对贡献观察

### 当前已发现的口感结论

1. `sanhe` 与部分 `pattern axis` 仍然偏容易打满分
2. 风险矩阵在部分基线盘上已经比此前更接近合理区间
3. 诊断型插件“假 100%”问题已经被压制，但仍需继续细调

---

## 12. 已知缺口与风险

### 12.1 仍存在大量 manifest 动态算子

例如：

- `l1.physics.op_geography`
- `l1.physics.op_vertical_crush`
- `l1.physics.op_branch_banhe`
- `l1.physics.op_branch_anhe`
- `l1.physics.op_blade_clash`
- `l1.physics.op_owl_food`
- `l1.physics.op_robber_wealth`

这类插件当前更像“中间桥接能力”，而不是完全专题化的正式插件。

### 12.2 不是所有插件都参数化

当前大量 L0 / 盲派 / 子平 / 格局插件没有 `DECLARED_PARAMS`，原因不一定是缺陷：

- 有些是解释型插件，本来不需要物理参数
- 有些是候选型插件，重点在 `match_ratio`，不是 `impact_ratio`

### 12.3 当前 `match_ratio` 仍属于工程拟合

它的角色是：

- 成立程度量化

不是：

- 命理真概率

因此对分析师的建议是：

- 不要把 0.78 当成统计学置信区间
- 要把它当成“系统内部的相对成立程度”

### 12.4 当前最值得继续校准的插件

建议优先顺序：

1. `l1.physics.op_branch_sanhe`
2. `classical.pattern.axis.v1`
3. `l2.risk.risk_matrix`
4. `l1.physics.op_stem_fusion`
5. `classical.blind.*`

---

## 13. 对分析师的建议

如果分析师要进一步分析系统，建议按以下顺序：

### 第一层：法理核验

先看这些问题：

1. 哪些插件应该只有 `fact`，不该出 `proposal`
2. 哪些插件之间天然互斥
3. 哪些专题插件应当优先于关系插件

### 第二层：量化核验

重点看：

1. `match_ratio` 的口感是否符合命理直觉
2. `delta_abs` 是否过大
3. 哪些插件容易假满分

### 第三层：参数核验

只在前两层稳定后，再看：

1. 参数默认值是否偏激进
2. 是否需要降低某些上限
3. 是否要把某些阈值抬高

---

## 14. 结语

当前插件系统已经不再是“到处硬编码、命中即叠加”的早期结构，而是具备：

1. 家族分层
2. 条件协议
3. 匹配度
4. 冲突法理
5. Base 重算
6. 贡献追踪

因此，这一版已经足够交给分析师做下一轮高层分析。

如果分析师要继续深入，最值得盯住的不是“还有没有插件”，而是：

- 哪些插件的 **法理应成立**
- 哪些插件的 **量化过猛或过弱**
- 哪些插件之间的 **裁决优先级** 还需要正式宪法化
