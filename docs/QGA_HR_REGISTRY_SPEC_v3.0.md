# QGA 全息注册表规范 (QGA-HR V3.0)
—— 格局数字化身份证、多态容器与精密路由协议 ——
**版本**: V3.0 (Logic Container & Config Router)
**生效日期**: 2025-12-31
**继承版本**: V2.5 (Container) → V2.4 (Manifold) → V2.3 (Operator) → V2.0 (Tensor)
**适用范围**: Antigravity Engine 全量格局 (A-Z Series)
**合规标准**: FDS-V3.0 (Precision Physics)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`
**状态**: ENFORCED (强制执行)

---

## 一、 规范定位与核心升级

### 1.1 规范定义
QGA-HR V3.0 是全息格局的最终数据载体。它继承了 V2.5 的 **“多态容器” (Multi-State Container)** 架构，并进一步升级为 **“纯逻辑容器”**。它不再包含硬编码的物理参数，而是作为连接 **FDS 物理模型** 与 **Config 配置中心** 的桥梁。

### 1.2 V3.0 核心升级 (Change Log)
相比 V2.5，V3.0 引入了决定性的架构变更，以彻底实现“逻辑与数据分离”：

| 特性 | V2.5 (旧版) | V3.0 (当前版) | 物理意义 |
| :--- | :--- | :--- | :--- |
| **数据结构** | 数组容器 (Array Container) | **数组容器 (保持不变)** | 支持一个格局拥有无限个子变体 (如大鳄、枭雄) |
| **参数定义** | 硬编码数值 (Hardcoded) | **配置引用 (@config)** | 实现物理定律的可热插拔调节，无需修改代码 |
| **元数据** | 基础信息 | **标准化枚举 (Enum)** | 强制分类 (WEALTH/POWER) 以适配前端渲染 |
| **物理修正** | 子格局矩阵重写 | **子格局矩阵重写 (保持不变)** | 允许奇点翻转物理法则 (e.g., 劫财变喜神) |

---

## 二、 五维命运张量 ($\mathcal{T}_{fate}$)
所有格局的物理输出，必须坍缩为以下 5 个无量纲投影值 (0.0 - 1.0)。

| 轴 | 符号 | 物理定义 (Physics) | 命理意象 (Metaphysics) |
| :--- | :--- | :--- | :--- |
| **能级** | **E** | Amplitude / Potential | 生命力、抗压阈值、根基 |
| **秩序** | **O** | Entropy Reduction | 权力、地位、自律、贵气 |
| **物质** | **M** | Work / Mass | 财富、资产、执行成果 |
| **应力** | **S** | Shear Stress | 风险、灾难、内耗、突发 |
| **关联** | **R** | Entanglement | 情感、人脉、六亲、合作 |

---

## 三、 标准 JSON Schema V3.0 (The Container Structure)
这是核心部分。所有新格局 (registry.json) 必须严格匹配此结构。

```json
{
  "id": "String (e.g., 'D-02')",
  "name": "String (e.g., '偏财格')",
  "version": "3.0",
  "active": true,

  // [1] 元信息 (Metadata Normalization - FDS V3.0 Enhanced)
  "meta_info": {
    "pattern_id": "String",
    "name": "String",
    "display_name": "String (e.g., 'Indirect Wealth')", // [V3.0 NEW] 纯英文索引
    "chinese_name": "String (e.g., '偏财格')",         // [V3.0 NEW] 纯中文标题
    "category": "Enum: [WEALTH, POWER, TALENT, SELF]", // [V3.0 NEW] 强制分类
    "physics_prototype": "String (e.g., 'Dynamic Venture Field')",
    "description": "String",
    "compliance": "FDS-V3.0",
    "calibration_date": "YYYY-MM-DD",
    "mining_stats": {
      "seed_count": "Integer",
      "singularity_count": "Integer"
    }
  },

  // [2] 物理内核 (全局默认物理法则)
  "physics_kernel": {
    "version": "3.0",
    "description": "Default Physics Laws",
    
    // 基础转换矩阵 (5x10+ Weights)
    // 注意：权重矩阵属于训练结果，保留 Float 数值
    "transfer_matrix": {
      "E_row": { "Day_Master": "float", "Resource": "float", ... },
      "O_row": { "Eating_God": "float", ... },
      "M_row": { "Wealth": "float", "Clash": "float", ... },
      "S_row": { "Seven_Killings": "float", "Clash": "float", ... },
      "R_row": { "Combination": "float", ... }
    },

    // 张量动力学 (饱和函数) - [V3.0 Upgrade: Config Reference]
    "tensor_dynamics": {
      "activation_function": "Enum: [sigmoid_variant, tanh, linear]",
      "parameters": { 
          "k_factor_ref": "String (e.g., '@config.physics.k_factor')" 
      }
    },
    "integrity_threshold_ref": "String (e.g., '@config.integrity.threshold')"
  },

  // [3] 特征锚点 (仅保留对标准流形的引用，用于向下兼容)
  "feature_anchors": {
    "description": "Reference to Standard Manifold",
    "standard_manifold": {
      "mean_vector": { "E": 0.xx, "M": 0.xx, ... },
      "covariance_matrix": [ [0.xx, ...], ... ],
      "thresholds": {
        "max_mahalanobis_dist_ref": "String (@config...)",
        "min_sai_gating_ref": "String (@config...)"
      }
    }
  },

  // [4] V3.0 核心：子格局容器 (The Sub-Pattern Container)
  "sub_patterns_registry": [
    {
      "id": "String (e.g., 'SP_D02_LEVERAGE')",
      "name": "String",
      "type": "Enum: [DEFAULT, SINGULARITY]",
      "description": "String",

      // [关键] 矩阵重写：允许奇点修改物理法则
      "matrix_override": {
        "transfer_matrix": {
          "M_row": { "Rob_Wealth": "float (e.g., 0.8)" }, // 翻转示例
          "R_row": { "Rob_Wealth": "float" }
        }
      },

      // 该子格局的独立统计流形
      "manifold_data": {
        "mean_vector": { "E": 0.xx, "M": 0.xx, ... },
        "covariance_matrix": [ ... ], // 可选，若无则使用全局
        "trigger_logic": "String (Documentation only)"
      }
    },
    {
      "id": "String (e.g., 'SP_D02_TURBULENCE')",
      "..." : "..."
    }
  ],

  // [5] V3.0 核心：运行时路由协议 (The Router)
  "matching_router": {
    "strategy_version": "3.0",
    "description": "Runtime Logic Gates",
    "strategies": [
      {
        "priority": "Integer (1=Highest)",
        "target": "String (Must match sub_patterns_registry.id)",
        "description": "String",
        
        // 逻辑定义
        "logic": {
          // 条件类型：AND (全满足), OR (任一满足), MAHALANOBIS (距离)
          "condition": "Enum: [AND, OR, MAHALANOBIS]",
          
          // 物理规则列表 (for AND/OR) - [V3.0 Upgrade: Param Reference]
          "rules": [
            {
              "axis": "Enum: [E, O, M, S, R]",
              "operator": "Enum: [gt, lt, eq]",
              "param_ref": "String (e.g., '@config.gating.weak_self_limit')" // 严禁写死数值
            }
          ],
          
          // 距离阈值 (for MAHALANOBIS)
          "threshold_ref": "String (e.g., '@config.singularity.threshold')"
        }
      }
    ]
  }
}
