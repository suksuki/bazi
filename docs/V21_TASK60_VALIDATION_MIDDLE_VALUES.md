# V21.0 任务 60：算法一致性验证与中间值披露

## 🎯 目标

提供 C07（事业）和 C01（情感）案例的原始计算数据，供理论算法验证第一层算法的实现是否正确。

## 📋 背景

V21.0 验证结果显示模型崩塌（MAE 从 ≈ 5 暴涨到 ≈ 15），这强烈暗示代码实现与理论设计存在本质偏差。

**核心诊断：理论与实践的脱节**

1. **理论设计**：V18.0 到 V21.0 阶段的分层调优框架、理论驱动参数和能量流耦合算法
2. **代码实现**：Cursor 负责将指令转化为实际可执行的代码
3. **当前问题**：C07 事业相和 C01 情感相的崩塌，需要对比实际计算结果与理论算法预期

## 🔍 验证方案

### 1. 理论算法推算（AI 任务）

基于 V21.0 理论参数（例如：月令权重=2.0，三会倍率=4.0 等）以及能量流耦合的数学公式，重新计算 C07 和 C01 的理论得分。

### 2. 实际结果对比（错误隔离）

| 案例/维度 | GT 得分 | Cursor 实际计算 (V21.0 结果) | **理论算法预期得分 (AI 推算)** | **误差类型** |
| --- | --- | --- | --- | --- |
| **C07 事业** | 80.0 | 51.3 | 待计算 | **系统性能量压制** |
| **C01 情感** | ≈ 99.0 | ≈ 64.0 | 待计算 | **复杂交互逻辑错误** |

### 3. 指导修正（Correction）

如果 Cursor 实际计算和 AI 理论推算存在巨大差异，则证明 Cursor 在实现复杂交互（合冲刑害）或能量流耦合逻辑时存在错误。

---

## 📝 运行环境

使用 V21.0 任务 59 中已部署的**保守参数**和**已启用**的复杂交互/能量流耦合代码。

**关键参数配置：**
- 月令权重：2.0
- 三合倍率：3.0
- 三会倍率：4.0
- 能量流耦合：已启用
- 复杂交互：已启用

---

## 📊 数据披露要求

针对 **C07 (事业)** 和 **C01 (情感)**，披露以下**第一层**关键计算中间值：

### 1. Raw Energy 聚合前（应用禀赋特性修正后）

**含义**：天干地支的原始五行能量列表，应用了禀赋特性（如通根加成、月令权重）修正后，但**未应用**合冲刑害和墓库物理修正。

**格式**：
```json
{
  "case_id": "C07",
  "raw_energy_before_interactions": {
    "wood": 0.0,
    "fire": 0.0,
    "earth": 0.0,
    "metal": 0.0,
    "water": 0.0
  },
  "calculation_details": {
    "pillar_contributions": [
      {
        "pillar": "year",
        "stem_energy": {"wood": 8.0},
        "branch_energy": {"earth": 12.0, "water": 8.4, "metal": 3.6}
      },
      {
        "pillar": "month",
        "stem_energy": {"fire": 20.0},
        "branch_energy": {"fire": 20.0, "earth": 14.0, "metal": 6.0}
      },
      // ... 其他柱
    ],
    "rooting_bonuses": {
      "wood": 1.6,  // 通根加成
      "fire": 2.4
    },
    "era_multipliers": {
      "fire": 1.1,
      "earth": 0.95
    }
  }
}
```

### 2. Raw Energy 修正后（应用合冲刑害和墓库物理修正后）

**含义**：应用了**合冲刑害**和**墓库物理**修正后的五行能量最终值。

**格式**：
```json
{
  "case_id": "C07",
  "raw_energy_after_interactions": {
    "wood": 0.0,
    "fire": 0.0,
    "earth": 0.0,
    "metal": 0.0,
    "water": 0.0
  },
  "interaction_applications": [
    {
      "type": "stem_five_combination",
      "stems": ["甲", "己"],
      "transform_to": "earth",
      "bonus": 20.0,
      "deducted": {"wood": 10.0, "earth": 10.0}
    },
    {
      "type": "trine_harmony",
      "element": "water",
      "branches": ["申", "子", "辰"],
      "multiplier": 3.0,
      "energy_before": 50.0,
      "energy_after": 150.0
    },
    {
      "type": "clash",
      "branches": ["子", "午"],
      "damping": 0.7,
      "energy_before": {"water": 100.0, "fire": 80.0},
      "energy_after": {"water": 70.0, "fire": 56.0}
    },
    {
      "type": "vault_physics",
      "vault_branch": "辰",
      "vault_element": "water",
      "status": "open",
      "energy_before": 150.0,
      "energy_after": 225.0
    }
    // ... 其他交互
  ]
}
```

### 3. 能量流耦合修正后（Energy Flow Coupling Effects）

**含义**：应用了能量流耦合效应（顺生链放大、合力共振、多重力量抵消）后的五行能量。

**格式**：
```json
{
  "case_id": "C07",
  "raw_energy_after_coupling": {
    "wood": 0.0,
    "fire": 0.0,
    "earth": 0.0,
    "metal": 0.0,
    "water": 0.0
  },
  "coupling_effects": [
    {
      "type": "sequential_amplification",
      "chain": ["year", "month", "day"],
      "dm_element": "water",
      "amplification": 1.44,
      "energy_before": 100.0,
      "energy_after": 144.0
    },
    {
      "type": "coherent_resonance",
      "support_count": 2,
      "dm_element": "water",
      "resonance_boost": 1.15,
      "energy_before": 144.0,
      "energy_after": 165.6
    },
    {
      "type": "multi_force_cancellation",
      "support_count": 2,
      "control_count": 1,
      "net_energy_ratio": 0.733,
      "energy_before": 165.6,
      "energy_after": 121.4
    }
  ]
}
```

### 4. 十神波函数（Ten Gods Wave Function）

**含义**：最终生成的十神能量（应用了 Support_Factor, Control_Factor 等粒子权重后）。

**格式**：
```json
{
  "case_id": "C07",
  "ten_gods_strength": {
    "self": 50.0,
    "output": 30.0,
    "wealth": 80.0,
    "officer": 25.0,
    "resource": 15.0
  },
  "particle_weights": {
    "BiJian": 1.5,
    "JieCai": 1.5,
    "ShiShen": 1.4,
    "ShangGuan": 1.2,
    "ZhengCai": 1.3,
    "PianCai": 1.5,
    "ZhengGuan": 0.9,
    "QiSha": 1.15,
    "ZhengYin": 0.9,
    "PianYin": 0.9
  },
  "calculation_details": {
    "base_energies": {
      "wood": 50.0,
      "fire": 30.0,
      "earth": 80.0,
      "metal": 25.0,
      "water": 15.0
    },
    "dm_element": "water",
    "weighted_energies": {
      "self": 15.0 * 1.5,
      "output": 30.0 * 1.4,
      "wealth": 80.0 * 1.5,
      "officer": 25.0 * 1.15,
      "resource": 15.0 * 0.9
    }
  }
}
```

### 5. 宏观相基础得分（Macro Phase Base Score - S0_Base）

**含义**：宏观相聚合后的 S0_Base Score（在应用 BiasFactor、Corrector 之前）。

**格式**：
```json
{
  "case_id": "C07",
  "macro_phase_base_scores": {
    "career": {
      "S0_Base": 65.0,
      "calculation": {
        "officer_energy": 28.75,
        "resource_energy": 13.5,
        "output_energy": 42.0,
        "path_selected": "talent",
        "base_score": 50.4,
        "body_strength_bonus": 1.1,
        "s0_base": 55.44
      }
    },
    "wealth": {
      "S0_Base": 72.0,
      "calculation": {
        "wealth_energy": 120.0,
        "body_strength": 55.44,
        "base_score": 72.0,
        "modifier": 1.0,
        "reason": "Normal"
      }
    },
    "relationship": {
      "S0_Base": 45.0,
      "calculation": {
        "spouse_star": 28.75,
        "body_strength": 55.44,
        "base_score": 45.0,
        "modifier": 1.0,
        "reason": "Normal"
      }
    }
  }
}
```

---

## 📤 提交报告

提交包含上述所有中间值的详细数据报告，保存为 JSON 格式：

**文件路径**：`docs/V21_TASK60_MIDDLE_VALUES_REPORT.json`

**结构**：
```json
{
  "report_metadata": {
    "task_id": "V21_TASK60",
    "generation_time": "2024-XX-XX",
    "config_version": "V21.0_Task59_Conservative",
    "engine_version": "EngineV91"
  },
  "cases": [
    {
      "case_id": "C07",
      "target_dimension": "career",
      "raw_energy_before_interactions": {...},
      "raw_energy_after_interactions": {...},
      "raw_energy_after_coupling": {...},
      "ten_gods_strength": {...},
      "macro_phase_base_scores": {...}
    },
    {
      "case_id": "C01",
      "target_dimension": "relationship",
      "raw_energy_before_interactions": {...},
      "raw_energy_after_interactions": {...},
      "raw_energy_after_coupling": {...},
      "ten_gods_strength": {...},
      "macro_phase_base_scores": {...}
    }
  ]
}
```

---

## ✅ 验收标准

1. ✅ 所有中间值均已正确提取
2. ✅ 数据格式符合规范
3. ✅ 计算步骤可追溯（每个中间值都有对应的计算细节）
4. ✅ JSON 文件可正确解析
5. ✅ 报告包含完整的元数据信息

---

**报告生成时间**：V21.0 Task 60 (Middle Values Extraction)  
**验证状态**：🔄 待执行

