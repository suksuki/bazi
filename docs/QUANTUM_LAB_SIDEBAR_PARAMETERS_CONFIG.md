# 量子验证（Quantum Lab）边栏参数配置文档

## 📋 文档说明

本文档详细记录了量子验证页面边栏上所有可调参数的完整配置信息。

**文档版本：** V91.0  
**生成时间：** 2025-01-16  
**参数来源：** `ui/pages/quantum_lab.py`

---

## 📊 参数统计

**总计参数数量：** 60+ 个可调参数

**参数分类：**
- 算法核心控制台：9 个参数
- 基础场域（Physics）：4 个参数
- 粒子动态（Structure）：4 个参数
- 几何交互（Interactions）：15 个参数
- 能量流转（Flow）：7 个参数
- 时空修正（Spacetime）：10 个参数
- 物理权重参数（高级）：15+ 个参数
- 粒子权重校准：10 个参数

---

## 1. 🎛️ 算法核心控制台

**大类：** 算法核心事件分数（Algorithm Core Event Scores）

### 1.1 基础事件分数

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| Skull Crash (三刑崩塌分) | 丑未戌三刑触发时的强制熔断分 | -50.0 | -100.0 ~ 0.0 | `score_skull_crash` | `SCORE_SKULL_CRASH` |
| Treasury Bonus (身强暴富分) | 身强冲开财库时的爆发加成 | 20.0 | 0.0 ~ 50.0 | `score_treasury_bonus` | `SCORE_TREASURY_BONUS` |
| Treasury Penalty (身弱风险分) | 身弱冲开财库时的风险惩罚 | -20.0 | -50.0 ~ 0.0 | `score_treasury_penalty` | `SCORE_TREASURY_PENALTY` |
| General Open (普通开库分) | 普通库开启时的基础分数 | 5.0 | 0.0 ~ 20.0 | `score_general_open` | `SCORE_GENERAL_OPEN` |

### 1.2 能量阈值线

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 身旺线 | 判定身旺的能量阈值 | 3.5 | 0.0 ~ 10.0 | `energy_strong` | `ENERGY_THRESHOLD_STRONG` |
| 身弱线 | 判定身弱的能量阈值 | 2.0 | 0.0 ~ 10.0 | `energy_weak` | `ENERGY_THRESHOLD_WEAK` |

### 1.3 合化与冲突

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| Trinity Bonus (三合加成) | 三合局且为喜用神时的强力加成 | 15.0 | 0.0 ~ 30.0 | `score_sanhe_bonus` | `SCORE_SANHE_BONUS` |
| Combo Bonus (六合加成) | 六合（羁绊/解冲）的基础加分 | 5.0 | 0.0 ~ 20.0 | `score_liuhe_bonus` | `SCORE_LIUHE_BONUS` |
| Clash Penalty (六冲惩罚) | 六冲且未被化解时的基础扣分 | -5.0 | -20.0 ~ 0.0 | `score_clash_penalty` | `SCORE_CLASH_PENALTY` |

---

## 2. 🌍 基础场域 (Physics)

**大类：** 宫位引力（Pillar Gravity）

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 年柱 (Year) | 年柱在能量计算中的权重系数 | 0.8 | 0.5 ~ 1.5 | `pg_year` | `fp['physics']['pillarWeights']['year']` |
| 月令 (Month) | 月令在能量计算中的权重系数（最重要） | 1.2 | 0.5 ~ 2.0 | `pg_month` | `fp['physics']['pillarWeights']['month']` |
| 日主 (Day) | 日主在能量计算中的权重系数 | 1.0 | 0.5 ~ 1.5 | `pg_day` | `fp['physics']['pillarWeights']['day']` |
| 时柱 (Hour) | 时柱在能量计算中的权重系数 | 0.9 | 0.5 ~ 1.5 | `pg_hour` | `fp['physics']['pillarWeights']['hour']` |

---

## 3. ⚛️ 粒子动态 (Structure)

**大类：** 垂直作用（Vertical）和特殊状态（Special）

### 3.1 垂直作用

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 通根系数 (Rooting) | 天干在地支藏干中出现时的能量加成 | 1.0 | 0.5 ~ 2.0 | `root_w` | `fp['structure']['rootingWeight']` |
| 透干加成 (Exposed) | 天干透出时的能量增强系数 | 1.5 | 1.0 ~ 3.0 | `exposed_b` | `fp['structure']['exposedBoost']` |
| 自坐强根 (Sitting) | 天干与地支同柱时的加成系数 | 1.2 | 1.0 ~ 2.0 | `same_pill` | `fp['structure']['samePillarBonus']` |

### 3.2 特殊状态

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 黑洞/空亡 (Void) | 空亡对能量的折损率（0=空掉，1=不空） | 0.5 | 0.0 ~ 1.0 | `void_p` | `fp['structure']['voidPenalty']` |

---

## 4. ⚗️ 几何交互 (Interactions)

**大类：** 天干五合、地支成局、地支事件、墓库物理

### 4.1 天干五合 (Stem Fusion)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 合化阈值 (Threshold) | 天干五合成功化气的判定阈值 | 0.8 | 0.5 ~ 1.0 | `s5_th` | `fp['interactions']['stemFiveCombination']['threshold']` |
| 合化增益 (Bonus) | 天干五合成功化气时的能量增益倍率 | 2.0 | 1.0 ~ 3.0 | `s5_bo` | `fp['interactions']['stemFiveCombination']['bonus']` |
| 合绊损耗 (Binding) | 天干五合未化气时的能量折损率 | 0.4 | 0.0 ~ 1.0 | `s5_pe` | `fp['interactions']['stemFiveCombination']['penalty']` |
| 争合损耗 (Jealousy) | 多对一合化时的能量折损率 | 0.3 | 0.0 ~ 0.5 | `jealousy_d` | `fp['interactions']['stemFiveCombination']['jealousyDamping']` |

### 4.2 地支成局 (Branch Combo)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 三合(Trine) | 三合局（申子辰等）的能量倍率 | 2.5 | 1.5 ~ 5.0 | `cp_tb` | `fp['interactions']['comboPhysics']['trineBonus']` |
| 半合(Half) | 半三合的能量倍率 | 1.5 | 1.0 ~ 3.0 | `cp_hb` | `fp['interactions']['comboPhysics']['halfBonus']` |
| 三会(Dir) | 三会局（寅卯辰等）的能量倍率 | 3.0 | 2.0 ~ 6.0 | `cp_db` | `fp['interactions']['comboPhysics']['directionalBonus']` |
| 解冲消耗 | 贪合忘冲时的能量消耗率 | 0.1 | 0.0 ~ 0.5 | `cp_rc` | `fp['interactions']['comboPhysics']['resolutionCost']` |

### 4.3 地支事件 (Branch Events)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 冲的折损 (Clash Damp) | 六冲时的能量折损系数 | 0.3 | 0.1 ~ 1.0 | `be_clash_d` | `fp['interactions']['branchEvents']['clashDamping']` |

### 4.4 墓库物理 (Vault Physics)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 分界阈值 (Threshold) | 界定库vs墓的能量阈值 | 20.0 | 10.0 ~ 50.0 | `vp_th` | `fp['interactions']['vaultPhysics']['threshold']` |
| 闭库折损 (Sealed) | 闭库时的能量折损率 | 0.4 | 0.0 ~ 1.0 | `vp_sd` | `fp['interactions']['vaultPhysics']['sealedDamping']` |
| 开库爆发 (Open Bonus) | 冲开库后的能量爆发倍率 | 1.5 | 1.0 ~ 3.0 | `vp_ob` | `fp['interactions']['vaultPhysics']['openBonus']` |
| 破墓伤害 (Broken P) | 冲破墓时的惩罚系数 | 0.5 | 0.0 ~ 1.0 | `vp_bp` | `fp['interactions']['vaultPhysics']['breakPenalty']` |
| 刑可开库 (Punishment Opens) | 是否允许刑开库 | False | True/False | `vp_po` | `fp['interactions']['vaultPhysics']['punishmentOpens']` |

---

## 5. 🌊 能量流转 (Flow / Damping)

**大类：** 阻尼协议（Damping Protocol）

### 5.1 输入阻抗 (Resource Impedance)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 基础阻抗 (Base) | 印星（生我）的基础阻抗系数 | 0.3 | 0.0 ~ 0.9 | `imp_base` | `fp['flow']['resourceImpedance']['base']` |
| 虚不受补 (Weak Penalty) | 身弱时印星能量的折损率 | 0.5 | 0.0 ~ 1.0 | `imp_weak` | `fp['flow']['resourceImpedance']['weaknessPenalty']` |

### 5.2 输出粘滞 (Output Viscosity)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 最大泄耗 (Max Drain) | 食伤（我生）的最大泄耗率 | 0.6 | 0.1 ~ 1.0 | `vis_rate` | `fp['flow']['outputViscosity']['maxDrainRate']` |
| 输出阻力 (Friction) | 食伤输出的阻力系数 | 0.2 | 0.0 ~ 0.5 | `vis_fric` | `fp['flow']['outputViscosity']['drainFriction']` |

### 5.3 系统熵 (System Entropy)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 全局熵增 (Entropy) | 系统整体的熵增系数 | 0.05 | 0.0 ~ 0.2 | `sys_ent` | `fp['flow']['globalEntropy']` |

### 5.4 控制影响 (Control Impact)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 克-打击力 (Impact) | 官杀（克我）的打击力系数 | 0.7 | 0.1 ~ 1.0 | `ctl_imp` | `fp['flow']['controlImpact']` |

### 5.5 空间衰减 (Spatial Decay)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 隔一柱 (Gap 1) | 相邻柱之间的能量传递系数 | 0.6 | 0.1 ~ 1.0 | `sp_g1` | `fp['flow']['spatialDecay']['gap1']` |
| 隔两柱 (Gap 2) | 相隔一柱的能量传递系数 | 0.3 | 0.1 ~ 1.0 | `sp_g2` | `fp['flow']['spatialDecay']['gap2']` |

---

## 6. ⏳ 时空修正 (Spacetime)

**大类：** 大运权重、宏观场域

### 6.1 大运权重

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 大运权重 (Luck Pillar) | 大运在时空修正中的权重 | 0.5 | 0.0 ~ 1.0 | `lp_w` | `fp['spacetime']['luckPillarWeight']` |

### 6.2 宏观场域 (Macro Field)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 当前元运 (Era) | 九运离火/八运坤土等 | Fire | Period 9/8/1 | `era_el` | `fp['macroPhysics']['eraElement']` |
| 时代红利 (Bonus) | 符合时代元素的加成 | 0.2 | 0.0 ~ 0.5 | `era_bon` | `fp['macroPhysics']['eraBonus']` |
| 时代阻力 (Penalty) | 不符合时代元素的阻力 | 0.1 | 0.0 ~ 0.5 | `era_pen` | `fp['macroPhysics']['eraPenalty']` |
| ERA 五行调整 | 五行的百分比调整（-10% ~ +10%） | 0.0 | -0.1 ~ 0.1 | `era_adjustment` | `era_factor` (动态计算) |
| 出生城市 (Birth City) | 用于 GEO 修正的城市选择 | Unknown | 城市列表 | `p2_city_input` | `city_for_controller` |
| 南方火气 (South Heat) | 南方火气增益 | 0.0 | 0.0 ~ 0.5 | `geo_hot` | `fp['macroPhysics']['latitudeHeat']` |
| 北方水气 (North Cold) | 北方水气增益 | 0.0 | 0.0 ~ 0.5 | `geo_cold` | `fp['macroPhysics']['latitudeCold']` |
| 南半球 (S.Hemi) | 是否反转季节（南半球） | False | True/False | `inv_sea` | `fp['macroPhysics']['invertSeasons']` |
| 真太阳时 (True Solar) | 是否使用真太阳时 | True | True/False | `use_st` | `fp['macroPhysics']['useSolarTime']` |

---

## 7. 📊 物理权重参数（高级）

**大类：** 全局参数、事业相、财富相、感情相、逻辑开关

### 7.1 全局参数

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| We: 全局能量增益 | 全局能量乘数 | 1.0 | 0.5 ~ 2.0 | `w_e_val` | `w_e_weight` / `weights.w_e_weight` |
| F(阴阳): 异性耦合效率 | 阴阳异性之间的耦合效率 | 1.1 | 0.8 ~ 1.5 | `f_yy_val` | `f_yy_correction` / `weights.f_yy_correction` |

### 7.2 事业相 (Career)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| W_官杀 (Officer) | 官杀在事业相中的权重 | 0.8 | 0.0 ~ 1.0 | `w_career_officer` | `W_Career_Officer` / `weights.W_Career_Officer` |
| W_印星 (Resource) | 印星在事业相中的权重 | 0.1 | 0.0 ~ 1.0 | `w_career_resource` | `W_Career_Resource` / `weights.W_Career_Resource` |
| W_食伤 (Tech) | 食伤在事业相中的权重 | 0.0 | 0.0 ~ 1.0 | `w_career_output` | `W_Career_Output` / `weights.W_Career_Output` |
| K_制杀 (Control) | 制杀的转换系数 | 0.55 | 0.0 ~ 1.0 | `k_control` | `K_Control_Conversion` / `k_factors.K_Control_Conversion` |
| K_化杀 (Buffer) | 化杀的防御系数 | 0.40 | 0.0 ~ 1.0 | `k_buffer` | `K_Buffer_Defense` / `k_factors.K_Buffer_Defense` |
| K_伤官见官 (Mutiny) | 伤官见官的背叛系数 | 1.8 | 0.0 ~ 3.0 | `k_mutiny` | `K_Mutiny_Betrayal` / `k_factors.K_Mutiny_Betrayal` |
| K_官杀攻身 (Pressure) | 官杀攻身的压力系数 | 1.0 | 0.0 ~ 2.0 | `k_pressure` | `K_Pressure_Attack` / `k_factors.K_Pressure_Attack` |

### 7.3 财富相 (Wealth)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| W_财星 (Wealth) | 财星在财富相中的权重 | 0.6 | 0.0 ~ 1.0 | `w_wealth_cai` | `W_Wealth_Cai` / `weights.W_Wealth_Cai` |
| W_食伤 (Source) | 食伤在财富相中的权重 | 0.4 | 0.0 ~ 1.0 | `w_wealth_output` | `W_Wealth_Output` / `weights.W_Wealth_Output` |
| K_身旺担财 (Capture) | 身旺担财的捕获系数 | 0.0 | 0.0 ~ 0.5 | `k_capture` | `K_Capture_Wealth` / `k_factors.K_Capture_Wealth` |
| K_身弱泄气 (Leak) | 身弱泄气的漏耗系数 | 0.87 | 0.0 ~ 2.0 | `k_leak` | `K_Leak_Drain` / `k_factors.K_Leak_Drain` |
| K_财多身弱 (Burden) | 财多身弱的负担系数 | 1.0 | 0.5 ~ 2.0 | `k_burden` | `K_Burden_Wealth` / `k_factors.K_Burden_Wealth` |

### 7.4 感情相 (Relationship)

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| W_配偶星 (Spouse) | 配偶星在感情相中的权重 | 0.35 | 0.1 ~ 1.0 | `w_rel_spouse` | `W_Rel_Spouse` / `weights.W_Rel_Spouse` |
| W_日主 (Self) | 日主在感情相中的权重 | 0.20 | -0.5 ~ 0.5 | `w_rel_self` | `W_Rel_Self` / `weights.W_Rel_Self` |
| W_食伤 (Output) | 食伤在感情相中的权重 | 0.15 | 0.0 ~ 1.0 | `w_rel_output` | `W_Rel_Output` / `weights.W_Rel_Output` |
| K_比劫夺财 (Clash) | 比劫夺财的冲突系数 | 1.2 | 0.0 ~ 2.0 | `k_clash` | `K_Clash_Robbery` / `k_factors.K_Clash_Robbery` |

### 7.5 逻辑开关

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| K_假从崩塌 (Broken) | 假从崩塌的系数 | 1.5 | 1.0 ~ 3.0 | `k_broken` | `K_Broken_Collapse` / `k_factors.K_Broken_Collapse` |
| 通关豁免 (Mediation) | 是否启用通关豁免 | True | True/False | `enable_mediation` | `enable_mediation_exemption` / `logic_switches.enable_mediation_exemption` |
| 地支互斥 (Structural) | 是否启用地支互斥 | True | True/False | `enable_structural` | `enable_structural_clash` / `logic_switches.enable_structural_clash` |

---

## 8. ⚛️ 粒子权重校准 (Particle Weights)

**大类：** 十神粒子权重（Ten Gods Particle Weights）

所有粒子权重范围为 50% ~ 150%（即 0.5 ~ 1.5），默认值为 100%（即 1.0）。

| 参数名称 | 参数意义 | 默认值 | 范围 | 变量名 | 引用变量名 |
|---------|---------|--------|------|--------|-----------|
| 正印 (Zheng Yin) | 正印粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[0]]` | `config_weights.get('正印', 1.0)` |
| 偏印 (Pian Yin) | 偏印粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[1]]` | `config_weights.get('偏印', 1.0)` |
| 比肩 (Bi Jian) | 比肩粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[2]]` | `config_weights.get('比肩', 1.0)` |
| 劫财 (Jie Cai) | 劫财粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[3]]` | `config_weights.get('劫财', 1.0)` |
| 食神 (Shi Shen) | 食神粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[4]]` | `config_weights.get('食神', 1.0)` |
| 伤官 (Shang Guan) | 伤官粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[5]]` | `config_weights.get('伤官', 1.0)` |
| 正财 (Zheng Cai) | 正财粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[6]]` | `config_weights.get('正财', 1.0)` |
| 偏财 (Pian Cai) | 偏财粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[7]]` | `config_weights.get('偏财', 1.0)` |
| 正官 (Zheng Guan) | 正官粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[8]]` | `config_weights.get('正官', 1.0)` |
| 七杀 (Qi Sha) | 七杀粒子权重 | 1.0 | 0.5 ~ 1.5 | `particle_weights[consts.TEN_GODS[9]]` | `config_weights.get('七杀', 1.0)` |

---

## 📝 配置文件位置

参数配置保存在以下位置：

1. **算法核心参数（常量）：** `core/config_rules.py`
   - 定义所有 `SCORE_*` 和 `ENERGY_THRESHOLD_*` 常量

2. **全量算法参数（默认结构）：** `core/config_schema.py`
   - 定义 `DEFAULT_FULL_ALGO_PARAMS` 字典结构

3. **黄金参数（用户保存值）：** `data/golden_parameters.json`
   - 保存用户调整后的权重参数（weights、k_factors、logic_switches）

4. **粒子权重配置：** `config/parameters.json`
   - 保存十神粒子的权重值（通过 Controller 管理）

---

## 🔧 参数使用说明

### 参数更新流程

1. **算法核心参数：** 通过 "🔄 应用并回测" 按钮更新，参数存储在 `st.session_state['algo_config']` 和 `st.session_state['full_algo_config']` 中

2. **物理权重参数：** 通过 "💾 保存现有配置" 按钮保存到 `data/golden_parameters.json`

3. **粒子权重：** 通过 "💾 保存粒子权重到配置" 按钮保存到 `config/parameters.json`

### 参数优先级

- **运行时参数：** `st.session_state` 中的参数 > 文件中的参数
- **文件参数：** `golden_parameters.json` > `config_rules.py` 默认值
- **粒子权重：** `config/parameters.json` > 默认值 1.0

---

## 📌 注意事项

1. 所有参数值在 UI 中修改后，需要点击相应的保存按钮才会持久化到磁盘
2. 算法核心参数需要点击 "🔄 应用并回测" 才会生效
3. 部分参数（如 ERA 五行调整）是动态计算的，不会直接保存
4. 城市选择参数会影响 GEO 修正计算，但不会持久化保存（每次加载需要重新选择）

---

**文档维护：** 如参数有变更，请及时更新本文档。

