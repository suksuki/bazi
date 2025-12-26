# SGJG 双向高能对撞模型 (Collider Model) V3.0 技术文档

**版本**: V3.0  
**发布日期**: 2025-12-26  
**状态**: CALIBRATED ✅

---

## 📋 模型概述

基于 113,631 个样本的数据驱动定标，彻底重构"伤官见官"的物理模型。

### 核心数据

| 指标 | 数值 |
|------|------|
| 样本数 | 113,631 |
| **崩塌率** | **99.98%** |
| **幸存率** | **0.02%** |
| 幸存者数 | 2 |

---

## 🛡️ 生存准则 V1.0

### 硬指标

| 逃生通道 | 效果 | 系数 |
|----------|------|------|
| **月干财星** | SAI 下降 84% | 0.16 |
| **双合冻结** | SAI 下降 33% | 0.67 |
| **空间距离 ≥ 3 柱** | 物理隔离 | - |
| **通关介质 ≥ 4** | 硬门槛 | - |

### 判定逻辑

```python
has_survival_criteria = (
    (total_passthrough >= 4 and collision_dist >= 3) or 
    has_month_stem_wealth or 
    double_combine
)

if not has_survival_criteria:
    verdict = "MELTDOWN"  # 熔断
```

---

## ⚡ 五行对撞系数

| 对撞类型 | K_clash | 危险度 |
|----------|---------|--------|
| **Wood-Earth** | **1.5** | ☠️ 最高危 |
| Metal-Wood | 1.4 | 高危 |
| Water-Fire | 1.2 | 高危 |
| 其他 | 1.0 | 标准 |

### Wood-Earth 结构失效

```python
if is_wood_earth:
    category = "结构失效 (Structural Failure)"  # 强制标记
```

---

## 📐 SAI 计算公式

```
SAI = (SG_E × ZG_E × DistFactor × MonthMult × K_clash) / Protection
      × Month_Stem_Shield(0.16)
      × Double_Combine_Freeze(0.67)
```

---

## 📊 财星位置敏感度

| 财星位置 | 平均 SAI | SAI 下降 |
|----------|----------|----------|
| **month_stem (月干)** | **15.45** | **-84%** |
| hidden_only (藏干) | 76.01 | -24% |
| hour_stem (时干) | 81.93 | -18% |
| year_stem (年干) | 86.81 | -13% |
| no_wealth (无财) | 99.99 | 基线 |

---

## 🔄 合化逃生通道

| 合化状态 | 平均 SAI | SAI 下降 | 幸存数 |
|----------|----------|----------|--------|
| **both_combine (双合)** | **58.27** | **-33%** | **2** |
| zg_combines (官被合) | 73.18 | -16% | 0 |
| sg_combines (伤被合) | 75.21 | -14% | 0 |
| no_combine (无合) | 87.65 | 基线 | 0 |

---

## 📁 输出参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `stress` | float | SAI 应力值 |
| `collapse_rate` | string | 坍缩倍率 |
| `survival_criteria` | string | MET / FAILED |
| `month_stem_wealth` | string | YES / NO |
| `double_combine` | string | YES / NO |
| `spatial_safe` | string | YES / NO (距离≥3) |
| `total_passthrough` | float | 财星+印星 |
| `category` | string | 分类判定 |

---

## 📂 相关文件

| 文件 | 用途 |
|------|------|
| `core/trinity/core/engines/pattern_scout.py` | V3.0 算法实现 |
| `core/logic_manifest.json` | 模块注册 |
| `docs/SGJG_COLLIDER_PHASE1_REPORT.md` | Phase 1 报告 |
| `docs/SGJG_COLLIDER_PHASE2_REPORT.md` | Phase 2 报告 |
| `docs/SGJG_COLLIDER_V3.0.md` | 本文档 |

---

**文档作者**: Antigravity V14.2.0  
**状态**: ✅ 11 万样本验证完成
