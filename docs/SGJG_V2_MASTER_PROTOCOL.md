# 伤官见官 (SGJG) Master Protocol V2.1 技术文档

**版本**: V2.1  
**更新日期**: 2025-12-26  
**状态**: CALIBRATED ✅

---

## 📐 物理模型概述

"伤官见官"是命理学中描述**伤官与正官直接碰撞**导致的高压失效状态。V2.1 Master Protocol 将这一古代概念转化为可计算的物理函数。

### 核心公式

```
SAI = (伤官能量 × 官星能量 × 距离因子 × 月令系数 × 五行克制系数) / (有效保护层 + 1.0)
坍缩率 = SAI / SAI_baseline
```

---

## 🔍 Phase 1: 古代硬判据 (Ancient Hard Rules)

| 规则 | 描述 | 代码实现 |
|------|------|----------|
| **伤官必存** | 原局四柱天干必须有"伤官" | `if "伤官" not in natal_tg: return None` |
| **官星存在** | 六柱中必须有"正官"或"七杀" | `if not any(g in ["正官", "七杀"] for g in all_tg): return None` |
| **严格定义** | 不允许"食神"代替"伤官" | 攻击者列表只含 `["伤官"]` |

---

## ⚡ Phase 2: 三维注入权重 (3D Injection Weights)

| 柱位 | 权重 | 物理含义 |
|------|------|----------|
| Year (年) | 0.5 | 祖辈背景场 |
| Month (月) | 3.0 | 月令主导 |
| Day (日) | 1.0 | 日主核心 |
| Hour (时) | 0.8 | 子女场 |
| **Luck (运)** | **0.5** | 静态电势 (10年期) |
| **Annual (年)** | **1.0** | 脉冲信号 (年度激励) |

### [V2.1 新增] 月令震源加权

```python
month_sg = any(p["pos"] == 1 and p["god"] == "伤官" for p in points)
month_zg = any(p["pos"] == 1 and p["god"] in ["正官", "七杀"] for p in points)
month_core_mult = 1.25 if (month_sg or month_zg) else 1.0
```

**物理意义**: 月令是命局的"震源中心"，月令有伤官或官星时，碰撞强度提升 25%。

---

## 🔥 [V2.1 新增] 五行克制系数 (Elemental Clash Coefficient)

| 对撞类型 | K_clash | 物理机制 |
|----------|---------|----------|
| **金木对撞** | **1.4** | 脆性折断，最为惨烈 |
| **水火对撞** | **1.2** | 汽化损耗，能量抵消 |
| **土水对撞** | 1.0 | 浑浊停滞，动态损耗 |
| **其他** | 1.0 | 默认值 |

```python
CLASH_COEFF_MAP = {
    ("Metal", "Wood"): 1.4, ("Wood", "Metal"): 1.4,
    ("Water", "Fire"): 1.2, ("Fire", "Water"): 1.2,
    ("Earth", "Water"): 1.0, ("Water", "Earth"): 1.0,
}
k_clash = CLASH_COEFF_MAP.get((sg_elem, zg_elem), 1.0)
```

---

## 🛡️ Phase 3: 动态保护层审计 (Dynamic Shield Audit)

### 护盾类型

| 护盾 | 权重 | 通关机制 |
|------|------|----------|
| 正财/偏财 | 0.8 | 伤官生财、财生官 (金字塔泄压) |
| 正印/偏印 | 0.5 | 泄官生身 (逆向引流) |

### [V2.1 更新] 动态衰减函数

```python
import math
decay = math.exp(-0.3 * dist_to_core)
protection_effective += (shield_value * decay)
```

**设计原理**: 护盾效果随距离指数衰减，λ = 0.3。

---

## 📉 Phase 4: 坍缩阈值检测 (Collapse Detection)

### 关键常量

| 常量 | 值 | 含义 |
|------|-----|------|
| `COLLAPSE_THRESHOLD` | 1.25 | SAI 超此值即判定坍缩 |
| `is_shielded` | protection > 1.5 | 护盾有效判定 |

### SAI 计算公式 (V2.1)

```python
distance_factor = max(0.5, 5 - collision_dist)
current_sai = (max_sg_e * max_zg_e * distance_factor * month_core_mult * k_clash) / (protection_effective + 1.0)
collapse_rate = current_sai / baseline_sai
```

---

## 🏷️ Phase 5: 分类判定

| 分类 | 条件 | 含义 |
|------|------|------|
| **高压击穿 (Critical Breakdown)** | SAI > 2.0 | 系统严重失效 |
| **结构坍缩 (Structural Collapse)** | SAI > 1.25 | 结构开始变形 |
| **防御虚化 (Ghost Shield)** | 总保护 > 0.8, 有效保护 < 0.5 | 护盾看似存在但无效 |
| **应力过载 (Stress Overload)** | 其他 | 临界状态 |

### 附加标记

- **+ 冲击**: 原局地支有冲 (SAI × 1.3)
- **⚡ 电压泵升**: 官星透干 (weight = 1.1)

---

## 📊 输出参数说明 (V2.1)

| 参数 | 类型 | 说明 |
|------|------|------|
| `stress` | float | 当前 SAI 值 |
| `baseline_sai` | float | 无官星时的基线 SAI |
| `collapse_rate` | string | 坍缩倍率 (如 "3.2x") |
| `k_clash` | float | 五行克制系数 |
| `month_core_mult` | float | 月令震源系数 |
| `sg_elem` | string | 伤官五行 |
| `zg_elem` | string | 官星五行 |
| `protection` | string | 有效/总保护层 |
| `shield_breakdown` | string | 财/印分解 |
| `dist` | int | 碰撞核心距离 (柱数) |
| `voltage_pump` | string | ACTIVE/INACTIVE |
| `geo_element` | string | 当前地理五行 |

---

## 📁 注册信息

### logic_manifest.json

```json
{
    "id": "MOD_101_SGJG_FAILURE",
    "name": "🏹 伤官见官失效模型 (SGJG Failure Model)",
    "version": "2.1",
    "theme": "PATTERN_PHYSICS",
    "linked_rules": [
        "PH_SGJG_COLLAPSE_THRESHOLD",
        "PH_SGJG_SHIELD_AUDIT",
        "PH_SGJG_GEO_IMPEDANCE",
        "PH_SGJG_ELEMENTAL_CLASH",
        "PH_SGJG_MONTH_CORE"
    ],
    "parameters": {
        "collapse_threshold": 1.25,
        "month_core_multiplier": 1.25,
        "distant_shield_decay_lambda": 0.3,
        "k_clash_metal_wood": 1.4,
        "k_clash_water_fire": 1.2
    },
    "status": "CALIBRATED"
}
```

---

## 📂 相关文件

| 文件 | 用途 |
|------|------|
| `core/trinity/core/engines/pattern_scout.py` | 算法实现 |
| `ui/pages/quantum_simulation.py` | UI 显示 |
| `core/logic_manifest.json` | 模块注册 |
| `tests/test_pattern_scout_v14.py` | 自动化测试 |
| `docs/SGJG_V2_MASTER_PROTOCOL.md` | 本文档 |

---

**文档作者**: Antigravity V14.2.0  
**审核状态**: ✅ Master Jin 已签署
