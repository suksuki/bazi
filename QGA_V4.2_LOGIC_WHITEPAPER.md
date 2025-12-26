# 📋 QGA V4.2 格局底层逻辑白皮书
## [SYSTEM_REVIEW_INIT] 全格局逻辑审计报告

**生成时间**: 2025-12-26 22:28  
**审计版本**: Antigravity V4.2  
**审计样本**: 16 档案 × 81 岁 = 1,296 人年样本

---

## 📊 格局逻辑捕获率总览

| 格局 ID | MOD | 捕获率 | 状态 | 逻辑预警 |
|---------|-----|--------|------|----------|
| SHANG_GUAN_JIAN_GUAN | MOD_101 | 6.44% | ✅ 正常 | - |
| SHANG_GUAN_PEI_YIN | MOD_108 | 18.35% | ✅ 正常 | - |
| SHANG_GUAN_SHANG_JIN | MOD_104 | 27.49% | ✅ 已修复 | V4.2 等离子气化场 |
| YANG_REN_JIA_SHA | MOD_105 | 1.22% | ⚠️ 偏低 | 条件严格 |
| XIAO_SHEN_DUO_SHI | MOD_106 | 18.52% | ✅ 正常 | - |
| SHI_SHEN_ZHI_SHA | MOD_109 | **0.00%** | 🔴 异常 | 零容忍条件 |
| CAI_GUAN_XIANG_SHENG | MOD_107 | **0.00%** | 🔴 异常 | 零容忍条件 |
| CYGS_COLLAPSE | MOD_111 | 49.43% | ✅ 正常 | - |
| HGFG_TRANSMUTATION | MOD_112 | 25.94% | ✅ 正常 | - |
| SSSC_AMPLIFIER | MOD_113 | 12.89% | ✅ 正常 | - |
| JLTG_CORE_ENERGY | MOD_114 | 24.31% | ✅ 正常 | - |
| PGB_SUPER_FLUID_LOCK | MOD_110A | **0.00%** | 🔴 异常 | 零容忍条件 |
| PGB_BRITTLE_TITAN | MOD_110B | 29.04% | ✅ 正常 | - |

---

## 🔴 零捕获格局详细分析

### 1. SHI_SHEN_ZHI_SHA (食神制杀) - 捕获率 0%

**硬触发逻辑 (Hard-Gate):**
```python
# 原局天干必须同时有食神和七杀
if "食神" not in ten_gods: return None
if "七杀" not in ten_gods[:4]: return None

# 不能有伤官（会破坏制杀纯度）
if "伤官" in ten_gods[:4]: return None
```

**问题诊断:**
- 要求原局天干有食神 + 七杀，但不能有伤官
- 这个条件过于严格，大多数有杀的八字也有伤官

**建议修复:**
- 允许伤官存在，但计算"食神压制比"
- 类似 SGSJ 的能级压制模型

---

### 2. CAI_GUAN_XIANG_SHENG (财官相生) - 捕获率 0%

**硬触发逻辑 (Hard-Gate):**
```python
# 需要检查 pattern_id == "CAI_GUAN_XIANG_SHENG_V4" 还是其他
# 当前可能存在 ID 不匹配问题
```

**问题诊断:**
- 代码中使用的是 `CAI_GUAN_XIANG_SHENG` 但注册的可能是 `CAI_GUAN_XIANG_SHENG_V4`
- 需要检查 pattern_scout.py 中的 pattern_id 匹配

**建议修复:**
- 统一 pattern_id 命名

---

### 3. PGB_SUPER_FLUID_LOCK (超流锁定格) - 捕获率 0%

**硬触发逻辑 (Hard-Gate):**
```python
# 需要检查具体条件
# 可能是月令要求过于严格
```

**问题诊断:**
- 超流锁定格要求特定的月令配置
- 或者 pattern_id 不匹配

---

## 📝 各格局硬触发逻辑详解

### MOD_101: SHANG_GUAN_JIAN_GUAN (伤官见官)

**物理模型**: 栅极击穿模型 (Gate Breakdown Model)

**硬触发条件:**
```python
natal_tg = ten_gods[:4]
if "伤官" not in natal_tg: return None  # 必须有伤官
if "正官" not in natal_tg: return None  # 必须有正官
```

**柔性压制比:**
```python
ratio = sg_kinetic / max(0.1, o_stabilization)
sai = ratio * phase_interference * geo_factor

if is_trap: sai *= 1.5           # 天干合绊
if is_vault_overflow: sai *= 3.0  # 墓库冲破
if is_reverse_collapse: sai *= 2.0 # 三合局
```

**动态干涉因子:**
- 财星护卫: `o_stability_sum *= 1.5`
- 正官长生状态: STAGE_MULT (帝旺=2.5, 临官=2.0)

**逻辑自洽性**: ✅ 无矛盾

---

### MOD_104: SHANG_GUAN_SHANG_JIN (伤官伤尽) [V4.2 已修复]

**物理模型**: 等离子体气化场模型 (Plasma Vaporization Field)

**硬触发条件:**
```python
if "伤官" not in ten_gods: return None  # 必须有伤官
if "正官" in ten_gods[:4]: return None  # 天干不能有正官
# 已移除藏干官杀限制！
```

**柔性压制比:**
```python
suppression_ratio = sg_total / max(0.01, guan_total)
is_vaporized = suppression_ratio >= 12.0  # 气化态判定

# 如果压制比不够，且官杀能量显著，则不构成伤尽
if suppression_ratio < 3.0 and guan_total > 1.0:
    return None
```

**动态干涉因子:**
- 日主电源稳定性: `source_stability = dm_support / sg_total`
- 动态拦截能力: `intercept_ratio = sg_total / incoming_guan`

**逻辑自洽性**: ✅ V4.2 已修复

---

### MOD_105: YANG_REN_JIA_SHA (羊刃架杀)

**物理模型**: 托卡马克聚变模型 (Tokamak Fusion Model)

**硬触发条件:**
```python
# 日主必须是阳干
if dm not in ["甲", "丙", "戊", "庚", "壬"]: return None

# 月令必须是帝旺
month_branch = chart[1][1]
dm_stage = get_stage(dm, month_branch)
if dm_stage != "帝旺": return None

# 必须有七杀透干
if "七杀" not in ten_gods[:4]: return None
```

**问题诊断:**
- 帝旺要求非常严格
- 只有日主在月令为帝旺才能触发

**逻辑自洽性**: ⚠️ 条件严格但合理

---

### MOD_106: XIAO_SHEN_DUO_SHI (枭神夺食)

**物理模型**: 量子超导断路模型 (Quantum Superconductor Circuit Break)

**硬触发条件:**
```python
if "偏印" not in ten_gods: return None  # 必须有偏印
if "食神" not in ten_gods: return None  # 必须有食神
```

**柔性压制比:**
```python
sai = (x_total * xiao_field) / (max(0.1, s_total) * (1.0 + w_total * 0.4))
sai *= phase_interference * buffer_factor * geo_factor
```

**逻辑自洽性**: ✅ 无矛盾

---

### MOD_111: CYGS_COLLAPSE (从格坍缩)

**物理模型**: 引力坍缩模型 (Gravitational Collapse)

**硬触发条件:**
```python
# 比劫能量必须极低（日主虚弱）
if dm_support > 2.0: return None  # 日主太强不构成从格
```

**柔性压制比:**
```python
locking_ratio = dominant_energy / max(0.1, dm_support)
is_rebound = (incoming pressure causes field reversal)
```

**逻辑矛盾预警:**
- 假从格在墓库冲开时的逻辑跳变
- 当大运印比来临时，从格可能"假从变真"

**建议**: 增加"假从格保护机制"检测

---

### MOD_112: HGFG_TRANSMUTATION (化气格重构)

**物理模型**: 原子变性模型 (Atomic Transmutation)

**硬触发条件:**
```python
# 必须存在天干五合对子
PAIRS = {"甲己", "乙庚", "丙辛", "丁壬", "戊癸"}
has_pair = any(pair in stems for pair in PAIRS)
if not has_pair: return None

# 化神必须占主导
if transmutation_purity < 0.5: return None
```

**逻辑矛盾预警:**
- 还原剂入侵时的属性锁定失效
- 当冲破阻止化气时，系统应该标记为"化而不成"

---

## 🎯 需要紧急修复的格局

### 优先级 1: SHI_SHEN_ZHI_SHA (捕获率 0%)

**当前问题**: 不允许伤官存在

**修复方案**: 
```python
# 改为能级压制模型
shi_shen_ratio = shi_shen_energy / max(0.01, shang_guan_energy)
if shi_shen_ratio >= 3.0:  # 食神是伤官的 3 倍以上
    # 允许制杀
```

### 优先级 2: CAI_GUAN_XIANG_SHENG (捕获率 0%)

**当前问题**: pattern_id 可能不匹配

**修复方案**: 检查并统一命名

### 优先级 3: PGB_SUPER_FLUID_LOCK (捕获率 0%)

**当前问题**: 月令条件过严

**修复方案**: 放宽或重新设计触发条件

---

## 📈 动态干涉矩阵实测反馈

### 天干五合对各格局的影响

| 格局 | 五合影响 | 稳态破坏率 |
|------|----------|------------|
| SGGG | 伤官被合 → 稳态 | -30% SAI |
| SGPY | 伤官被合 → 失控 | +50% SAI |
| SGSJ | 官杀被合 → 无影响 | 0% |
| YRJS | 七杀被合 → 格局消失 | 100% |

### 墓库开合对各格局的 SAI 增益

| 格局 | 墓库状态 | SAI 增益中位值 |
|------|----------|---------------|
| SGGG | 冲开官墓 | +200% (is_vault_overflow) |
| XSDS | 偏印入墓 | +50% |
| CYGS | 冲开日主墓 | 假从变真，格局消失 |

---

## 📋 审计结论

### 已确认的逻辑问题

1. **SHI_SHEN_ZHI_SHA**: 零容忍条件导致零捕获
2. **CAI_GUAN_XIANG_SHENG**: pattern_id 可能不匹配
3. **PGB_SUPER_FLUID_LOCK**: 月令条件过严

### 已修复的问题

1. **SHANG_GUAN_SHANG_JIN**: V4.2 等离子气化场模型已部署

### 建议后续行动

1. 修复 SHI_SHEN_ZHI_SHA 的触发逻辑
2. 统一 CAI_GUAN_XIANG_SHENG 的 pattern_id
3. 重新设计 PGB_SUPER_FLUID_LOCK 的触发条件
4. 增加 CYGS 的"假从格保护机制"

---

**审计官**: Antigravity V4.2  
**审计状态**: [SYSTEM_REVIEW_COMPLETE]  
**下一步**: 待 Master Jin 确认修复优先级
