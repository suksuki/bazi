# Antigravity 核心调优总纲 (Optimization Constitution)
**版本号**: V1.0 (The Tuning Protocol)  
**依赖文档**: `ALGORITHM_CONSTITUTION_v2.5`, `ALGORITHM_V6.1`, `SUPPLEMENT_L2`  
**参数来源**: `QUANTUM_LAB_SIDEBAR_PARAMETERS_CONFIG.md`  
**生效日期**: 2025-01-16

---

## 序言 (Preamble)

本总纲确立了 Antigravity 系统从"物理仿真"向"实证回归"进化的最高行动准则。  
我们将 60+ 个离散参数重组为严密的 **Layer 1 (Micro)** 与 **Layer 2 (Macro)** 双层调优架构。

---

## 第一章：Layer 1 微观物理层调优 (The Physics Kernel)
**目标**：确保从"八字粒子"到"十神能量"的转化符合物理直觉。  
**校准对象**：旺衰（Strong/Weak）、格局（Pattern）、五行分布。

### 第 1 条：基础场域定标 (Base Field Calibration)
* **参数集**: `Physics`
* **核心权重**:
    * `pg_month` (默认 1.2+): 月令是热力学基准，需通过大量案例回归确定其统治力边界。
    * `pg_year` / `pg_day` / `pg_hour`: 需验证"宫位引力透镜"效应，确认距离衰减是否符合 $1/r^2$。
* **垂直作用**:
    * `root_w` (通根, 默认 1.0): 验证天干对地支的依赖度。
    * `exposed_b` (透干, 默认 1.5): 验证地支能量显化后的爆发系数。
    * `same_pill` (自坐强根, 默认 1.2): 验证同柱时的能量加成。
    * `void_p` (空亡, 默认 0.5): 验证空亡对能量的折损率。

### 第 2 条：量子交互定标 (Interaction Calibration)
依据 `ALGORITHM_V6.1` 与 `L2_STOREHOUSE`。

* **合化 (Fusion)**:
    * `s5_th` (合化阈值, 默认 0.8) & `s5_bo` (合化增益, 默认 2.0): 需通过"化气格"案例调优。
    * `s5_pe` (合绊损耗, 默认 0.4): 验证未化气时的能量折损。
    * `jealousy_d` (争合损耗, 默认 0.3): 验证多对一合化时的能量折损率。
    
* **地支成局 (Combo)**:
    * `cp_tb` (三合, 默认 2.5) & `cp_db` (三会, 默认 3.0): 验证相位锁定后的能量倍增效应。
    * `cp_hb` (半合, 默认 1.5): 验证半三合的能量倍率。
    * `cp_rc` (解冲消耗, 默认 0.1): 验证贪合忘冲时的能量消耗。

* **冲战 (Clash)**:
    * `be_clash_d` (冲的折损, 默认 0.3): 验证冲战对能量的湮灭程度。
    * `score_clash_penalty` (六冲惩罚, 默认 -5.0): 验证六冲且未被化解时的基础扣分。

* **墓库隧穿 (Vault Tunneling)**:
    * `vp_th` (墓库阈值, 默认 20.0): 界定"库"与"墓"的能量分界线。
    * `vp_ob` (开库爆发, 默认 1.5): **关键调优项**。需通过马云等暴富案例，校准冲开财库后的能量释放倍率。
    * `vp_sd` (闭库折损, 默认 0.4): 验证闭库时的能量折损率。
    * `vp_bp` (破墓伤害, 默认 0.5): 验证冲破墓时的惩罚系数。
    * `score_treasury_bonus` (身强暴富分, 默认 20.0): 验证身强冲开财库时的爆发加成。
    * `score_treasury_penalty` (身弱风险分, 默认 -20.0): 验证身弱冲开财库时的风险惩罚。

* **特殊事件**:
    * `score_skull_crash` (三刑崩塌分, 默认 -50.0): 验证丑未戌三刑触发时的强制熔断分（乔布斯2011案例调优）。
    * `score_sanhe_bonus` (三合加成, 默认 15.0): 验证三合局且为喜用神时的强力加成。
    * `score_liuhe_bonus` (六合加成, 默认 5.0): 验证六合的基础加分。

### 第 3 条：能量流转定标 (Flow Dynamics)
* **阻抗与粘滞**:
    * `imp_base` (基础阻抗, 默认 0.3): 验证印星（生我）的基础阻抗系数。
    * `imp_weak` (虚不受补, 默认 0.5): **关键调优项**。调优身弱之人的印星吸收率。
    * `vis_rate` (最大泄耗, 默认 0.6): 调优食伤泄秀的极限，防止身弱者被泄死。
    * `vis_fric` (输出阻力, 默认 0.2): 验证食伤输出的阻力系数。
    
* **控制影响**:
    * `ctl_imp` (克-打击力, 默认 0.7): 验证官杀（克我）的打击力系数。
    
* **系统熵**:
    * `sys_ent` (全局熵增, 默认 0.05): 验证系统整体的熵增系数。
    
* **空间衰减**:
    * `sp_g1` (隔一柱, 默认 0.6) / `sp_g2` (隔两柱, 默认 0.3): 校准年柱对时柱的远程作用力。

* **能量阈值**:
    * `energy_strong` (身旺线, 默认 3.5): 判定身旺的能量阈值。
    * `energy_weak` (身弱线, 默认 2.0): 判定身弱的能量阈值。

---

## 第二章：Layer 2 宏观投影层调优 (The Macro Projector)
**目标**：将"十神能量"映射为"宏观之相"（财富、事业、感情）。  
**校准对象**：富贵层次、职业方向、人生大事件。

### 第 4 条：财富相调优 (Wealth Projection)
依据 `Wealth Physics` 参数组。

* **配比逻辑**: 财富 = (财星 + 源头) × 捕获效率 - 损耗。
* **参数调优**:
    * `w_wealth_cai` (财星权重, 默认 0.6): 传统财星在现代财富中的占比。
    * `w_wealth_output` (食伤权重, 默认 0.4): **关键调优项**。技术/流量变现的占比（需调高以适应现代社会）。
    * `k_capture` (身旺担财, 默认 0.0): 验证身旺对财星的直接捕获率。
    * `k_leak` (身弱泄气, 默认 0.87): 验证身弱泄气的漏耗系数。
    * `k_burden` (财多身弱, 默认 1.0): **关键调优项**。身弱财旺时的负债/压力系数。
    * `score_treasury_bonus` (默认 20.0): **爆发项**。验证"身强冲开财库"时的横财指数。
    * `score_general_open` (普通开库分, 默认 5.0): 验证普通库开启时的基础分数。

### 第 5 条：事业相调优 (Career Projection)
依据 `Career Physics` 参数组。

* **配比逻辑**: 权力 = 官杀压力 × (抗压 + 转化)。
* **参数调优**:
    * `w_career_officer` (官杀权重, 默认 0.8): 外部压力/机遇的大小。
    * `w_career_resource` (印星权重, 默认 0.1): **核心项**。验证"杀印相生"中印星的转化效率。
    * `w_career_output` (食伤权重, 默认 0.0): 技术创新的权重。
    * `k_control` (制杀系数, 默认 0.55): 食神制杀格的成功率与爆发力。
    * `k_buffer` (化杀系数, 默认 0.40): 验证化杀的防御系数。
    * `k_mutiny` (伤官见官, 默认 1.8): **关键调优项**。验证其在不同时代的破坏力（古代为祸，现代可能为创新）。
    * `k_pressure` (官杀攻身, 默认 1.0): 验证官杀攻身的压力系数。
    * `k_broken` (假从崩塌, 默认 1.5): 验证假从崩塌的系数。

### 第 6 条：感情相调优 (Relationship Projection)

* **配比逻辑**: 吸引力 vs 稳定性。
* **参数调优**:
    * `w_rel_spouse` (配偶星权重, 默认 0.35): 桃花旺度。
    * `w_rel_self` (日主权重, 默认 0.20): 日主在感情相中的权重（可为负值）。
    * `w_rel_output` (食伤权重, 默认 0.15): 食伤在感情相中的权重。
    * `k_clash` (比劫夺财/官, 默认 1.2): 验证第三者风险系数。

### 第 7 条：全局能量增益 (Global Energy Boost)

* **参数调优**:
    * `w_e_weight` (全局能量增益, 默认 1.0): 全局能量乘数（0.5 ~ 2.0）。
    * `f_yy_correction` (异性耦合效率, 默认 1.1): 阴阳异性之间的耦合效率（0.8 ~ 1.5）。

### 第 8 条：逻辑开关 (Logic Switches)

* **参数调优**:
    * `enable_mediation_exemption` (通关豁免, 默认 True): 是否启用通关豁免。
    * `enable_structural_clash` (地支互斥, 默认 True): 是否启用地支互斥。

### 第 9 条：时空环境修正 (Spacetime Context)
依据 `ALGORITHM_SUPPLEMENT_L2_SPACETIME`。

* **大运权重**:
    * `lp_w` (大运权重, 默认 0.5): 验证大运在时空修正中的权重。
    
* **宏观场域**:
    * `era_element` (当前元运, 默认 "Fire"): 九紫离火运等。
    * `era_bon` (时代红利, 默认 0.2): **关键调优项**。九紫离火运对"火"属性八字的加成。
    * `era_pen` (时代阻力, 默认 0.1): 不符合时代元素的阻力。
    * `era_adjustment` (ERA 五行调整): 动态调整五行能量基线（-10% ~ +10%）。
    
* **地理修正**:
    * `geo_hot` (南方火气, 默认 0.0): 出生地域对调候用神的修正幅度。
    * `geo_cold` (北方水气, 默认 0.0): 北方水气增益。
    * `city_selection` (出生城市): 用于 GEO 修正的城市选择。
    * `invert_seasons` (南半球, 默认 False): 是否反转季节（南半球）。
    * `use_solar_time` (真太阳时, 默认 True): 是否使用真太阳时。

### 第 10 条：粒子权重校准 (Particle Weights Calibration)

* **十神粒子权重**（默认均为 1.0，范围 0.5 ~ 1.5）:
    * 正印 (Zheng Yin)
    * 偏印 (Pian Yin)
    * 比肩 (Bi Jian)
    * 劫财 (Jie Cai)
    * 食神 (Shi Shen)
    * 伤官 (Shang Guan)
    * 正财 (Zheng Cai)
    * 偏财 (Pian Cai)
    * 正官 (Zheng Guan)
    * 七杀 (Qi Sha)

* **调优策略**: 通过调整不同十神的权重，微调模型对特定十神的敏感度。

---

## 第三章：调优执行策略 (Execution Strategy)

### 第 11 条：损失函数与回归 (Loss Function)
我们定义验证集的 **Ground Truth ($V_{real}$)**。

* **Loss Function**: 
  $$L = \alpha \sum (E_{phys} - E_{label})^2 + \beta \sum (S_{macro} - S_{label})^2$$
  
  其中：
  - $E_{phys}$: 物理层能量（身强身弱、格局判定）
  - $E_{label}$: 标注的物理层真值
  - $S_{macro}$: 宏观层得分（财富、事业、感情）
  - $S_{label}$: 标注的宏观层真值
  - $\alpha, \beta$: 权重系数

* **Layer 1 锁定**: 先用旺衰明确的案例（如专旺格、极弱格）校准物理层参数。确保：
    * 身强身弱的判定准确率 > 90%
    * 格局判定的准确率 > 85%
    * 五行能量分布的合理性

* **Layer 2 迭代**: 物理层参数冻结后，用富豪/高官/常人案例库，通过网格搜索 (Grid Search) 寻找最佳的宏观权重配比。确保：
    * 财富相的 MAE < 10 分
    * 事业相的 MAE < 10 分
    * 感情相的 MAE < 10 分

### 第 12 条：参数版本管理 (Versioning)

* **Base Profile**: 默认参数 (`DEFAULT_FULL_ALGO_PARAMS` in `core/config_schema.py`)。  
* **Tuned Profile**: 针对不同时代的特定参数集（如 "Modern_Era_v1.json" 调高食伤权重）。  
* **Golden Profile**: 通过大量案例调优后的黄金参数（保存在 `data/golden_parameters.json`）。  
* 所有调优后的参数需通过 UI 的 "💾 保存现有配置" 固化为 JSON。

### 第 13 条：调优优先级 (Priority)

**第一优先级（必须校准）**：
1. `pg_month` (月令权重) - 影响所有能量计算
2. `energy_strong` / `energy_weak` (能量阈值) - 影响身强身弱判定
3. `vp_ob` (开库爆发) - 影响暴富案例
4. `score_treasury_bonus` (身强暴富分) - 影响财富相
5. `w_wealth_output` (食伤权重) - 适应现代财富模式

**第二优先级（重要校准）**：
1. `imp_weak` (虚不受补) - 影响身弱案例
2. `k_mutiny` (伤官见官) - 影响事业相
3. `k_burden` (财多身弱) - 影响财富相
4. `era_bon` (时代红利) - 适应时代特征

**第三优先级（精细调优）**：
1. 其他交互参数（合化、冲战等）
2. 空间衰减参数
3. 粒子权重校准

### 第 14 条：调优流程 (Workflow)

1. **数据准备**：
   - 收集验证集案例（包含 Ground Truth）
   - 确保案例覆盖各类格局（身强、身弱、专旺、从格等）
   - 确保案例覆盖各时代特征

2. **Layer 1 调优**：
   - 冻结所有 Layer 2 参数
   - 使用物理层案例调优 Layer 1 参数
   - 验证身强身弱判定准确率
   - 保存 Layer 1 参数集

3. **Layer 2 调优**：
   - 冻结 Layer 1 参数（使用已校准值）
   - 使用宏观层案例调优 Layer 2 参数
   - 验证财富、事业、感情相的 MAE
   - 保存 Layer 2 参数集

4. **联合调优**（可选）：
   - 使用完整案例集进行联合调优
   - 微调关键参数
   - 最终验证

5. **参数固化**：
   - 将调优后的参数保存到 `data/golden_parameters.json`
   - 更新 `core/config_rules.py` 中的默认值（如需要）
   - 更新文档

---

## 第四章：调优案例参考 (Reference Cases)

### 物理层校准案例

* **专旺格案例**：验证 `pg_month` 和 `energy_strong` 的准确性
* **极弱格案例**：验证 `energy_weak` 和 `imp_weak` 的准确性
* **化气格案例**：验证 `s5_th` 和 `s5_bo` 的准确性
* **三刑案例**（如乔布斯2011）：验证 `score_skull_crash` 的准确性
* **墓库案例**（如马云2014）：验证 `vp_ob` 和 `score_treasury_bonus` 的准确性

### 宏观层校准案例

* **财富相案例**：
    * 富豪案例：验证 `w_wealth_cai`、`k_capture`、`score_treasury_bonus`
    * 技术富豪案例：验证 `w_wealth_output`
    * 财多身弱案例：验证 `k_burden`
    
* **事业相案例**：
    * 高官案例：验证 `w_career_officer`、`k_control`
    * 技术专家案例：验证 `w_career_output`、`k_mutiny`
    * 杀印相生案例：验证 `w_career_resource`、`k_buffer`

* **感情相案例**：
    * 桃花旺案例：验证 `w_rel_spouse`
    * 感情稳定案例：验证 `w_rel_self`、`k_clash`

---

## 附录：参数快速索引

### Layer 1 参数索引

| 参数类别 | 关键参数 | 默认值 | 调优优先级 |
|---------|---------|--------|-----------|
| 基础场域 | `pg_month` | 1.2 | P0 |
| | `pg_year` / `pg_day` / `pg_hour` | 0.8 / 1.0 / 0.9 | P1 |
| 垂直作用 | `root_w` / `exposed_b` / `same_pill` | 1.0 / 1.5 / 1.2 | P1 |
| | `void_p` | 0.5 | P2 |
| 合化 | `s5_th` / `s5_bo` / `s5_pe` | 0.8 / 2.0 / 0.4 | P1 |
| 地支成局 | `cp_tb` / `cp_db` | 2.5 / 3.0 | P1 |
| 冲战 | `be_clash_d` / `score_clash_penalty` | 0.3 / -5.0 | P1 |
| 墓库 | `vp_th` / `vp_ob` | 20.0 / 1.5 | P0 |
| | `score_treasury_bonus` / `score_treasury_penalty` | 20.0 / -20.0 | P0 |
| 特殊事件 | `score_skull_crash` | -50.0 | P0 |
| 能量流转 | `imp_base` / `imp_weak` | 0.3 / 0.5 | P0 |
| | `vis_rate` / `ctl_imp` | 0.6 / 0.7 | P1 |
| | `energy_strong` / `energy_weak` | 3.5 / 2.0 | P0 |

### Layer 2 参数索引

| 参数类别 | 关键参数 | 默认值 | 调优优先级 |
|---------|---------|--------|-----------|
| 全局 | `w_e_weight` / `f_yy_correction` | 1.0 / 1.1 | P1 |
| 财富相 | `w_wealth_cai` / `w_wealth_output` | 0.6 / 0.4 | P0 |
| | `k_capture` / `k_burden` | 0.0 / 1.0 | P0 |
| 事业相 | `w_career_officer` / `w_career_resource` | 0.8 / 0.1 | P0 |
| | `k_control` / `k_mutiny` | 0.55 / 1.8 | P0 |
| 感情相 | `w_rel_spouse` / `w_rel_self` | 0.35 / 0.20 | P1 |
| | `k_clash` | 1.2 | P1 |
| 时空 | `lp_w` / `era_bon` | 0.5 / 0.2 | P0 |
| | `geo_hot` / `geo_cold` | 0.0 / 0.0 | P2 |

**优先级说明**：
- P0: 第一优先级（必须校准）
- P1: 第二优先级（重要校准）
- P2: 第三优先级（精细调优）

---

**批准人**: Architect & Antigravity  
**执行代码库**: V9.1 Optimization Loop  
**最后更新**: 2025-01-16

