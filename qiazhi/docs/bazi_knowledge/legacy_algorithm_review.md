# Legacy Bazi Algorithm Review Report

Date: 2026-04-28

Scope: v17/v18 existing Bazi-related algorithms, plugins, rule assets, spatial/physics models, wealth models, body-use/pattern models.

Boundary: This report is an audit only. It does not create Knowledge Units, does not activate rules, and does not move legacy plugins into the new Core Bazi Knowledge Layer directly.

## 1. 总览

### 1.1 当前资产规模

当前项目中已经存在相当多的命理算法资产，主要集中在 `v17_rebirth/backend/logic` 与少量服务层文件中。

| 类型 | 估算数量 | 说明 |
| --- | ---: | --- |
| Python 逻辑文件 | 约 78 个 | 分布在 L0/L1/L2/L3/core_engine 等层 |
| JSON / config / knowledge 文件 | 约 68 个 | 包含 pattern、relation、physics、wealth code 等配置 |
| Plugin class | 约 82 个 | 覆盖五行十神、关系算子、格局、盲派、财富叙述等 |
| 相关测试文件 | 约 51 个 | 已覆盖 physics、relation、pattern、wealth、protocol 等旧系统能力 |

### 1.2 主要目录与职责

| 目录 / 文件 | 主要职责 | 资产性质 |
| --- | --- | --- |
| `v17_rebirth/backend/logic/L0_physics_fields/` | 日主、五行、十神、藏干、通根、得令、能量基础场 | 核心算法层 |
| `v17_rebirth/backend/logic/L1_atomic_ops/` | 天干地支关系、六合、三合、三会、冲刑害破、墓库、合化等 | 结构关系层 |
| `v17_rebirth/backend/logic/L2_structure_patterns/` | 子平格局、盲派体用、调候、用忌神、格局候选 | 格局 / 体用层 |
| `v17_rebirth/backend/logic/L3_modern_narrative/` | 财富画像、财富路径、宏观叙述、现代解释 | 主题叙述 / 产品表达层 |
| `v17_rebirth/backend/logic/core_engine/` | effect resolver、god ring、work path、pillar graph | 聚合与裁决辅助层 |
| `v17_rebirth/backend/services/physics_canonical.py` | 面向展示 / prompt / canonical text 的协议化输出 | UI / 叙述层 |
| `v17_rebirth/backend/logic/configs/` | 旧插件参数、格局配置、物理算子配置 | 规则参数资产 |
| `v17_rebirth/backend/logic/knowledge/` | symbolic primitives、wealth code knowledge | 结构化知识雏形 |

### 1.3 核心算法 vs UI / 叙述层

较接近 Core Bazi Feature 的资产：

| 模块 | 判断 |
| --- | --- |
| `ten_gods_engine.py` | 核心十神与绝对能量计算，可重构为基础特征层 |
| `ten_gods_static_basis.py` | 藏干、透干、通根、季令、根气累计逻辑，可重构 |
| `bazi_image_core.py` | 符号化命盘结构、宫位、藏干、库象，可作为 Core Feature 输入 |
| `relation_geometry_pairs.py` | 地支六合、冲、害、破、刑等纯几何检测，可直接复用 |
| `relation_geometry_structured.py` | 三合、三会、半合、拱合等结构检测，可直接复用或轻重构 |
| `stem_fusion_geometry.py` | 天干五合与合化条件，可重构复用 |
| `muku_gate.py` | 墓库 / 财库开闭模型，可重构为财富结构特征 |
| `runtime_field_protocol.py` | 大运 / 流年作为动态场的协议，可重构为岁运层 |

偏 UI / 叙述 / 产品表达的资产：

| 模块 | 判断 |
| --- | --- |
| `physics_canonical.py` | 面向解释展示，不应进入 Core |
| `narrative_clip.py` | 叙述素材，不应作为判断依据 |
| `wealth_profile_core.py` | 适合做主题表达，不适合作为第一层裁决 |
| `macro_theme_core.py` | 产品化宏观叙述，可参考，不应进入 Core 裁决 |
| L3 narrative plugins | 多数为叙述包装，需要拆出 evidence 后再复用 |

## 2. 基础命理层

### 2.1 基础项审计表

| 项目 | 是否已实现 | 主要文件路径 | 输入 | 输出 | 当前可靠度 | 是否可复用为 Core Bazi Feature |
| --- | --- | --- | --- | --- | --- | --- |
| 日主 | 已实现 | `L0_physics_fields/ten_gods_engine.py`, `L0_physics_fields/bazi_image_core.py` | `four_pillars["day"]` | day master stem / element | 高 | 可直接复用，但需统一 schema |
| 五行 | 已实现 | `ten_gods_engine.py`, `climate_field_protocol.py`, `stem_fusion_geometry.py` | 天干、地支、藏干 | element / element vector | 高 | 可直接复用，建议集中到 Core constants |
| 十神 | 已实现 | `ten_gods_engine.py` | daymaster stem + target stem | ten god label | 高 | 可直接复用 |
| 藏干 | 已实现 | `ten_gods_engine.py`, `ten_gods_static_basis.py`, `bazi_image_core.py` | branch | hidden stems with weights/order | 高 | 可直接复用 |
| 透干 | 部分实现 | `ten_gods_static_basis.py`, `foundation_projection.py` | visible stems + hidden stems | exposed hidden gain / exposed hidden facts | 中高 | 可重构复用 |
| 通根 | 已实现 | `ten_gods_engine.py`, `ten_gods_static_basis.py`, `foundation_projection.py` | visible stems + branch hidden stems | root strengths / rooted stem facts | 中高 | 可重构复用 |
| 得令 | 已实现 | `ten_gods_engine.py`, `ziping_family.py` | month branch, daymaster, hidden stems | season multiplier / month command god | 中高 | 可重构复用 |
| 得地 | 部分实现 | `ten_gods_engine.py`, `chang_sheng_12.py`, `ten_gods_static_basis.py` | branch position, chang sheng stage, roots | branch support / stage bonus | 中 | 可重构复用 |
| 得助 | 部分实现 | `ten_gods_static_basis.py`, `ten_gods_engine.py` | peers, root support, cross-polarity roots | support bonus / peer factor | 中 | 可重构复用 |
| 旺衰 | 已有近似实现 | `ziping_family.py`, `ten_gods_engine.py`, `god_ring_resolver_core.py` | ten god absolute scores, month command, ratios | balance class / strength tendency | 中 | 暂作为参考，需重新定义 Core 判定 |
| 身强身弱 | 部分实现 | `ziping_family.py`, `pattern_specializations.py`, `god_ring_resolver_core.py` | 比印、食伤财官杀、月令、根气 | balance / body tendency / followable hints | 中低 | 仅参考，不能直接进入 Core |

### 2.2 说明

基础层已经不是空白，甚至有比较完整的“物理场式”十神能量系统。主要问题不是没有算法，而是旧算法输出偏向 V17 physics / plugin fact / narrative protocol，不是干净的 Core Feature Contract。

建议迁移时优先拆出以下稳定资产：

| 优先级 | 资产 | 迁移方式 |
| --- | --- | --- |
| P0 | 天干、地支、五行、阴阳、十神映射表 | 直接进入 Core constants |
| P0 | 藏干表、藏干权重 | 直接进入 Core constants，但保留版本号 |
| P1 | 通根、透干、得令 | 重构为纯函数 feature extractor |
| P1 | 月令与季节 multiplier | 重构为 season feature，不直接输出结论 |
| P2 | 旺衰、身强身弱 | 重新定义判定协议后再接入 |

## 3. 结构关系层

### 3.1 结构关系审计表

| 项目 | 是否已实现 | 主要文件路径 | 输入 | 输出 | 当前可靠度 | 复用建议 |
| --- | --- | --- | --- | --- | --- | --- |
| 天干合 | 已实现 | `L1_atomic_ops/stem_fusion_geometry.py` | stems, pillar positions, runtime stems | fusion cases / target element / support score | 中高 | 可重构复用 |
| 天干冲 | 未见独立完整实现 | 部分散落在 relation / physics / config | stems | 可能作为 interference factor | 低 | 需要新 Core 定义 |
| 天干克 | 部分实现 | `ten_gods_engine.py`, `effect_resolver.py` | element cycle / ten god relation | control relation / pressure | 中 | 可参考，需抽象 |
| 地支六合 | 已实现 | `relation_geometry_pairs.py`, `six_harmony.py` | branch positions | liuhe hits / harmony facts | 高几何，中效果 | 几何直接复用，效果重构 |
| 地支三合 | 已实现 | `relation_geometry_structured.py`, `three_harmony.py` | branch set | sanhe group hits / element / strength | 高几何，中效果 | 几何直接复用 |
| 地支三会 | 已实现 | `relation_geometry_structured.py`, `three_meeting.py` | branch set | sanhui group hits / element / completeness | 高几何，中效果 | 几何直接复用 |
| 地支冲 | 已实现 | `relation_geometry_pairs.py`, `six_clash.py` | branch positions | clash hits / impact fact | 高几何，中效果 | 几何直接复用 |
| 地支刑 | 已实现 | `relation_geometry_pairs.py`, `triple_branch_penalty.py` | branch positions | sanxing / penalty facts | 中高 | 可重构复用 |
| 地支害 | 已实现 | `relation_geometry_pairs.py`, `six_pierce.py` | branch positions | harm / pierce hits | 高几何，中效果 | 几何直接复用 |
| 地支破 | 已实现 | `relation_geometry_pairs.py`, `six_break.py` | branch positions | break hits | 高几何，中效果 | 几何直接复用 |
| 墓库 | 已实现 | `muku_gate.py`, `bazi_image_core.py`, `wealth_code_core.py` | 辰戌丑未、冲合状态、财富相关十神 | storage / open / closed / vault facts | 中高 | 财富层重点重构 |
| 合化判断 | 已实现但偏物理化 | `stem_fusion_geometry.py`, `relation_geometry_structured.py` | 合局、支撑、干扰、月令、冲害破刑 | transform support / disturbance / state | 中 | 可重构为 stability feature |
| 稳定性 / 能量模型 | 已实现 | `flow_physics_engine.py`, `vector_physics_engine.py`, `effect_resolver.py`, `runtime_field_protocol.py` | relation hits, energy tensor, runtime scopes | pressure / activation / stability | 中 | 只保留结构化 feature，避免旧数值膨胀 |

### 3.2 关键发现

结构关系层是旧系统中最值得保留的资产之一，尤其是纯几何检测部分。

但是需要注意：

| 风险 | 说明 |
| --- | --- |
| 几何检测和效果解释混在一起 | 例如冲、合、刑害既输出命中，也直接给 impact ratio |
| key 命名可能不统一 | 例如旧插件中可能出现 `liu_he` 与几何层 `liuhe` 的适配差异 |
| 旧 impact ratio 不应直接继承 | 旧比例属于 V17 physics tuning，不一定适合 Core Knowledge Layer |
| 合化不应直接给结论 | 应只影响 stability、activation、risk、uncertainty |

建议迁移方式：

| 层级 | 迁移内容 |
| --- | --- |
| Core Structure Geometry | 六合、三合、三会、冲、刑、害、破、墓库存在性 |
| Structure Effect Layer | 开库、合化、冲动、扰动、稳定性变化 |
| Wealth Layer | 只消费 Structure Effect，不直接复写旧插件结论 |

## 4. 格局 / 体用层

### 4.1 已有格局资产

| 项目 | 是否已实现 | 主要文件路径 | 输入 | 输出 | 当前可靠度 | 复用建议 |
| --- | --- | --- | --- | --- | --- | --- |
| 格局判断 | 已实现大量候选 | `L2_structure_patterns/pattern_specializations.py`, `ten_god_pattern.py` | ten god scores, month command, relation facts | pattern candidates / pattern summary | 中 | 参考为主，不能直接 Core 裁决 |
| 子平月令体系 | 已实现 | `ziping_family.py` | month command god, season power | month command fact / balance fact | 中高 | 可重构为 Structure Layer |
| 体用判断 | 部分实现 | `blind_school_core.py`, `blind_school_family.py`, `god_ring_resolver_core.py` | house roles, route roles, body candidates | body_mode / use candidates | 中低 | 参考为主 |
| 用神忌神 | 已实现启发式 | `ziping_family.py`, `god_ring_resolver_core.py`, `effect_resolver.py` | benefit/harm paths, ten god axis, balance state | use_candidates / taboo_candidates | 中 | 后置审核，不进第一批 Core |
| 调候 | 已实现 | `climate_field_protocol.py`, `climate_theme_core.py` | stems, branches, hidden stems, luck/flow | thermal/moisture state, climate modifier | 中高 | 可作为 Adjustment Layer |
| 病药 | 未见独立命名实现 | 部分散落在 `effect_resolver.py`, `risk_matrix.py`, `climate_field_protocol.py` | imbalance / tension / remedy | pressure / correction hints | 低 | 需要重新建模 |
| 盲派体用 | 已实现 | `blind_school_core.py`, `blind_school_family.py` | palace, route, body/use candidates | body mode / route / runtime switch | 中 | reference only |
| 家内家外 / 宫位逻辑 | 已实现 | `bazi_image_core.py`, `blind_school_core.py`, `wealth_code_core.py` | pillar palace, branch/stem position | palace roles / inside-outside / wealth source hints | 中 | 可重构为 Palace Feature |

### 4.2 格局资产清单摘要

旧系统已经覆盖很多格局或结构候选，包括但不限于：

| 类别 | 已见资产 |
| --- | --- |
| 正格 / 十神格 | 财格、官格、印格、食神、伤官、七杀等 |
| 财相关格局 | 财官协同、财星格、财破印、食神生财、伤官生财、从财格 |
| 杀印 / 官印 / 食伤制杀 | 官印、杀印、食神制杀、伤官配印 |
| 从格 / 化气 / 专旺 | 从财、从杀、从儿、从旺、从强、从弱、化气、曲直、炎上、稼穑、润下 |
| 格局守门 | pattern resolver、formation gate、break guard |

### 4.3 结论

格局 / 体用层的最大价值是“旧体系中已经积累了大量候选结构”，但它们不适合作为第一批 Core Bazi Feature 直接落地。

原因：

| 问题 | 说明 |
| --- | --- |
| 输出偏候选与叙述 | 很多 plugin 直接生成 pattern fact 或 bias，而不是低层 feature |
| 依赖旧 physics 分数 | 若直接迁移，会继承旧数值尺度与调参 |
| 格局本身需要审核制度 | 格局判断比结构几何更容易出现体系争议 |
| 容易越权生成结论 | 新架构要求算法只生成 feature/evidence，不生成用户结论 |

建议：

第一阶段只迁移“可验证的结构事实”，例如月令、透藏、根气、组合关系。格局候选进入第二阶段，并必须以 reviewed Knowledge Unit + Rule Candidate 形式接入。

## 5. 大运流年层

### 5.1 已有岁运资产

| 项目 | 是否已实现 | 主要文件路径 | 输入 | 输出 | 当前可靠度 | 复用建议 |
| --- | --- | --- | --- | --- | --- | --- |
| 大运 | 部分实现 | `ten_gods_engine.py`, `runtime_field_protocol.py`, `wealth_code_core.py` | `luck_pillar` | luck field / decade trend / runtime scope | 中 | 可重构为 Runtime Feature |
| 流年 | 部分实现 | `ten_gods_engine.py`, `runtime_field_protocol.py`, `wealth_code_core.py` | `flow_pillar` | flow field / yearly perturbation / watchlist | 中 | 可重构为 Runtime Feature |
| 大运与原局作用 | 已有协议 | `runtime_field_protocol.py`, `stem_fusion_geometry.py`, `relation_runtime_collectors.py` | natal + luck pillar | dynamic edge metadata / relation triggers | 中 | 可复用协议，效果重构 |
| 流年与大运作用 | 已有协议 | `runtime_field_protocol.py`, `stem_fusion_geometry.py` | luck + flow pillar | luck-flow edge / field interaction | 中 | 可复用协议 |
| 引动 | 已实现雏形 | `wealth_code_core.py`, `runtime_field_protocol.py`, `relation_runtime_collectors.py` | natal/luck/flow relation hits | activation / timing hook / watchlist | 中 | 可重构为 activation feature |
| 岁运中的冲合刑害触发 | 已实现雏形 | `stem_fusion_geometry.py`, `relation_runtime_collectors.py`, `runtime_field_protocol.py` | natal branches + luck/flow branches | dynamic relation hit / disturbance | 中 | 可重构复用 |
| 排大运 / 起运 | 本轮未确认核心实现 | 未在已审计核心文件中确认 | birth data | luck cycles | 未确认 | 需要单独审计 |

### 5.2 关键结论

旧系统已经把大运、流年建模为“动态场”，而不是简单地把岁运当作静态柱追加。这一点很有价值。

尤其是 `runtime_field_protocol.py` 中的思想值得保留：

| 设计 | 价值 |
| --- | --- |
| 大运是背景场 | 可作为长期趋势 feature |
| 流年是年度扰动 | 可作为短期 activation / risk feature |
| 流年发生在大运场中 | 避免“流年单独裁决”的过度简化 |
| natal-luck-flow edge | 可表达原局、大运、流年的联动 |

但当前实现仍需要注意：

| 风险 | 说明 |
| --- | --- |
| 排运生成链路未完整确认 | 本报告只确认了 luck/flow 输入后的作用模型 |
| 旧 timeline 叙述可能混入结论 | `wealth_code_core.py` 中的 decade trend/watchlist 需要拆成 evidence |
| relation trigger 与 effect 混合 | 应把“触发关系”和“影响财富稳定性”拆开 |

## 6. 财富模型层

### 6.1 财富相关资产总览

| 模块 | 主要文件路径 | 说明 | 复用建议 |
| --- | --- | --- | --- |
| 财富画像 | `L3_modern_narrative/wealth_profile_core.py` | 输出财富分数、风险、立场、渠道、source gods | 作为产品表达参考 |
| 财富密码 / 财富路径 | `L3_modern_narrative/wealth_code_core.py` | 输出财富路径、财富来源、财富库、泄漏点、趋势 | 可重构为 Wealth Evidence Layer |
| 财富格局 | `L2_structure_patterns/pattern_specializations.py` | 财格、财官、食伤生财、伤官生财、财破印、从财等 | 参考为主 |
| 财库 / 墓库 | `L1_atomic_ops/muku_gate.py`, `bazi_image_core.py`, `wealth_code_core.py` | 库存在、开闭、财富承载与释放 | 重构优先级高 |
| 十神财富基础 | `ten_gods_engine.py`, `ten_gods_static_basis.py` | 财星、食伤、比劫、官杀、印星等强弱基础 | 重构优先级高 |
| 风险 / 机会 | `wealth_profile_core.py`, `wealth_code_core.py`, `risk_matrix.py` | 收入稳定、风险、泄漏、机会通道 | 拆成 evidence 后复用 |

### 6.2 财富模型细项审计

| 项目 | 是否已有 | 主要文件路径 | 输入 | 输出 | 当前可靠度 | 复用建议 |
| --- | --- | --- | --- | --- | --- | --- |
| 财星强弱 | 已有 | `ten_gods_engine.py`, `wealth_profile_core.py`, `pattern_specializations.py` | ten god absolute scores, roots, season | wealth score / source gods / wealth pattern candidate | 中高 | 可重构为 `wealth_strength` |
| 财库 | 已有 | `muku_gate.py`, `bazi_image_core.py`, `wealth_code_core.py` | 辰戌丑未、财星关系、冲合状态 | vault state / storage / wealth_vault | 中高 | 可重构为 `wealth_vault_activation` |
| 食伤生财 | 已有 | `pattern_specializations.py`, `wealth_code_core.py`, `wealth_profile_core.py` | output gods + wealth gods + sequence/nesting | output_to_wealth path / pattern candidate | 中 | 可重构为 `output_generate_wealth` |
| 比劫夺财 | 部分已有 | `wealth_code_core.py`, `risk_matrix.py`, `effect_resolver.py` | peer/rob wealth score, conflict pressure | leakage / contest / risk | 中 | 可重构为 wealth risk feature |
| 官杀制财 / 护财 | 部分已有 | `pattern_specializations.py`, `effect_resolver.py`, `god_ring_resolver_core.py`, `wealth_profile_core.py` | officer/killing scores, wealth relation, authority path | authority income / constraint / protection hints | 中低 | 需要重新定义 |
| 财印关系 | 已有候选 | `pattern_specializations.py`, `wealth_profile_core.py` | wealth + seal relation | 财破印 / knowledge asset / contradiction | 中 | 可参考，需拆 feature |
| 财富路径 | 已有 | `wealth_code_core.py`, `wealth_code_knowledge.v1.json` | ten god state, path templates, mechanism chains | primary_wealth_path / path_rankings / graph | 中高 | Wealth Layer 重点参考 |
| 收入稳定性 | 已有主题判断 | `wealth_profile_core.py`, `wealth_code_core.py`, `runtime_field_protocol.py` | wealth path, stability, relation disturbance | stance / risk / decade trend | 中 | 需重构为 stability evidence |
| 风险机会 | 已有主题判断 | `wealth_profile_core.py`, `wealth_code_core.py`, `risk_matrix.py` | leakage, clashes, runtime activation | risks / opportunities / watchlist | 中 | 拆成 risk/opportunity evidence |

### 6.3 财富模型关键发现

旧财富模型已经具备“财富路径类型”的雏形，这是下一阶段最有价值的资产。

可重点保留的结构：

| 旧结构 | 新系统建议形态 |
| --- | --- |
| `primary_wealth_path` | wealth path candidate evidence |
| `wealth_vault` | vault existence / activation / obstruction feature |
| `leakage_points` | wealth risk feature |
| `mechanism_chains` | evidence graph，不直接生成结论 |
| `decade_path_trends` | runtime activation evidence |
| `flow_year_watchlist` | yearly risk/opportunity trigger evidence |

必须避免的迁移方式：

| 禁止项 | 原因 |
| --- | --- |
| 直接复用旧财富 score 作为 prediction confidence | 旧 score 是 topic score，不是 Contract confidence |
| 直接输出旧 wealth stance 为用户结论 | 会绕过 Rule Kernel / Contract / Verifier |
| 直接使用 L3 narrative 文案 | 会把叙述层混入裁决层 |
| 将 wealth_code knowledge 直接变 active rule | 必须先进入 Knowledge Unit / sandbox candidate / review |

## 7. 可复用性评估

### 7.1 模块级评估

| 模块 | 评估 | 理由 |
| --- | --- | --- |
| `ten_gods_engine.py` | reusable after refactor | 核心十神/能量资产丰富，但输出混合绝对能量、meta、runtime 与旧 physics 语义 |
| `ten_gods_static_basis.py` | reusable after refactor | 藏干、通根、透干、季令累计逻辑有价值，但需要从 mutation/callback 风格重构为纯 feature |
| `bazi_image_core.py` | reusable after refactor | 符号化命盘、宫位、库象、material facts 很适合转为 Core Feature |
| `relation_geometry_pairs.py` | directly reusable | 纯几何关系检测清晰，适合直接进入 Structure Geometry Layer |
| `relation_geometry_structured.py` | directly reusable | 三合、三会、半合、拱合结构清晰，效果强度需另层处理 |
| `stem_fusion_geometry.py` | reusable after refactor | 天干五合与合化条件完整，但 support/disturbance 语义需标准化 |
| `muku_gate.py` | reusable after refactor | 墓库/开库对财富层重要，但需拆分“存在、开闭、激活、风险” |
| `runtime_field_protocol.py` | reusable after refactor | 大运/流年动态场思想非常好，可作为 Runtime Feature 协议基础 |
| `climate_field_protocol.py` | reusable after refactor | 调候热湿模型可作为 adjustment layer，不应进入第一裁决层 |
| `ziping_family.py` | reference only | 子平体系有价值，但输出已接近判断/建议，需重新审查 |
| `pattern_specializations.py` | reference only | 格局资产丰富，但争议度高、启发式多，不宜直接 Core |
| `blind_school_core.py` | reference only | 盲派体用、家内家外值得研究，但不适合作为第一期硬规则 |
| `effect_resolver.py` | reusable after refactor | 聚合 benefit/harm/stability 的思想可保留，但输入输出要 Contract 化 |
| `god_ring_resolver_core.py` | reusable after refactor | 用忌神候选/authority layer 有参考价值，需后置使用 |
| `wealth_profile_core.py` | reference only | 适合产品表达与主题总结，不适合作为 Core 裁决 |
| `wealth_code_core.py` | reusable after refactor | 财富路径和机制链价值高，建议重构为 Wealth Evidence Layer |
| `physics_canonical.py` | reference only | 展示/prompt/canonical text，不应作为算法来源 |
| `narrative_clip.py` | discard for Core | 叙述素材，不应进入 Core Knowledge Layer |

### 7.2 判定标准

| 标记 | 含义 |
| --- | --- |
| directly reusable | 可以作为纯函数或常量表直接迁入，最多改 schema |
| reusable after refactor | 逻辑有价值，但必须拆除旧输出、副作用、叙述、bias 或旧 physics scale |
| reference only | 可供分析师理解旧体系，但不能直接进入 Core |
| discard | 不应进入 Core，最多作为 UI 文案历史参考 |

## 8. 建议迁移路径

### 8.1 第一批：Core Bazi Layer

目标：建立最稳定、最少争议、最高可计算性的基础命理特征层。

建议优先迁移：

| 优先级 | 资产 | 来源 | 新形态 |
| --- | --- | --- | --- |
| P0 | 天干/地支/五行/阴阳/十神映射 | `ten_gods_engine.py` | Core constants |
| P0 | 藏干表与藏干权重 | `ten_gods_engine.py`, `ten_gods_static_basis.py` | hidden stem feature |
| P0 | 日主与十神计算 | `ten_gods_engine.py` | pure function |
| P1 | 透干检测 | `ten_gods_static_basis.py`, `foundation_projection.py` | exposed stem feature |
| P1 | 通根检测 | `ten_gods_engine.py`, `ten_gods_static_basis.py` | rootedness feature |
| P1 | 得令/月令 | `ten_gods_engine.py`, `ziping_family.py` | month command feature |
| P1 | 宫位/家内家外基础位置 | `bazi_image_core.py` | palace position feature |

暂不直接迁移：

| 资产 | 原因 |
| --- | --- |
| 旧身强身弱结论 | 需要重新定义标准 |
| 旧用神忌神输出 | 容易直接越权成为裁决 |
| 旧格局 conclusion | 争议大，必须走 reviewed Knowledge Unit |

### 8.2 第二批：Structure Layer

目标：把命局关系变成稳定、可组合的结构 evidence。

建议迁移：

| 优先级 | 资产 | 来源 | 新形态 |
| --- | --- | --- | --- |
| P0 | 六合、冲、害、破、刑 | `relation_geometry_pairs.py` | branch relation geometry feature |
| P0 | 三合、三会、半合、拱合 | `relation_geometry_structured.py` | group relation geometry feature |
| P1 | 天干五合 | `stem_fusion_geometry.py` | stem fusion feature |
| P1 | 墓库存在性 | `muku_gate.py`, `bazi_image_core.py` | storage/vault structure feature |
| P2 | 合化条件 | `stem_fusion_geometry.py`, `relation_geometry_structured.py` | transformation stability feature |
| P2 | 冲合刑害影响稳定性 | L1 plugins + `effect_resolver.py` | stability/risk modifier |
| P2 | 调候热湿 | `climate_field_protocol.py` | climate adjustment feature |

迁移原则：

| 原则 | 说明 |
| --- | --- |
| 先关系命中，后效果解释 | 先输出“发生了什么”，再输出“可能影响什么” |
| 不让关系直接生成结论 | 冲、合、刑害只能影响 stability/risk/activation |
| relation effect 要可审计 | 所有 effect ratio 必须有来源、版本与校准记录 |

### 8.3 第三批：Wealth Layer

目标：把旧财富模型拆成 feature-backed evidence，而不是继续使用 L3 narrative 结论。

建议迁移：

| 优先级 | 资产 | 来源 | 新形态 |
| --- | --- | --- | --- |
| P0 | 财星强弱 | `ten_gods_engine.py`, `wealth_profile_core.py` | `wealth_strength` feature |
| P0 | 财库/墓库 | `muku_gate.py`, `bazi_image_core.py`, `wealth_code_core.py` | `wealth_vault_activation` feature |
| P1 | 食伤生财 | `pattern_specializations.py`, `wealth_code_core.py` | `output_generate_wealth` feature |
| P1 | 比劫夺财 / 泄漏点 | `wealth_code_core.py`, `risk_matrix.py` | `wealth_risk` feature |
| P1 | 财富路径类型 | `wealth_code_core.py`, `wealth_code_knowledge.v1.json` | wealth path candidate evidence |
| P2 | 官杀制约/护财 | `effect_resolver.py`, `pattern_specializations.py` | `wealth_constraint` feature |
| P2 | 财印关系 | `pattern_specializations.py`, `wealth_profile_core.py` | conflict/uncertainty feature |
| P2 | 大运/流年引动财富 | `runtime_field_protocol.py`, `wealth_code_core.py` | `wealth_flow_activation` feature |

### 8.4 不建议迁移到 Core 的内容

| 内容 | 处理方式 |
| --- | --- |
| 旧 narrative text | 保留为 UI 参考，不进 Core |
| 旧 prompt/canonical display | 保留为解释层参考 |
| 旧 pattern verdict | 必须重新拆成 Knowledge Unit + Rule Candidate |
| 旧 confidence/score | 不能直接继承，需由 Contract evidence 重新计算 |
| 旧 plugin impact ratio | 可参考，但需重新校准与审计 |

## 9. 结论

旧系统的价值不在于可以“直接搬进新 Core”，而在于已经沉淀出三类很重要的资产：

| 资产类型 | 价值 |
| --- | --- |
| 稳定结构事实 | 天干地支、十神、藏干、通根、关系几何，适合进入 Core |
| 结构作用模型 | 合化、墓库、岁运引动、稳定性变化，适合进入 Structure Layer |
| 财富路径模型 | 财星、财库、食伤生财、泄漏点、财富路径，适合进入 Wealth Evidence Layer |

推荐的重构路线是：

```text
旧插件 / 旧算法
→ 拆出纯 feature extractor
→ 形成 Core Bazi Feature
→ 由 Knowledge Unit 审核语义
→ 生成 sandbox Rule Candidate
→ Rule Test / PR / Reviewer
→ Activate
→ Prediction Contract / Verifier / Ledger
```

明确不建议：

```text
旧插件
→ 直接变 Knowledge Unit
→ 直接生成 active rule
→ 直接进入 prediction conclusion
```

这份报告建议作为分析师重构 Core Bazi Knowledge Layer 的资产索引，而不是作为自动迁移清单。
