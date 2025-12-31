🏛️ QGA 正向拟合与建模规范 (FDS-V1.5 精密物理架构版)
—— 全格局通用统计力学仿真标准 ——
版本: V1.5 (Precision Physics & Statistical Manifolds)
修订: Schema V2.4 (Manifold Protocol)
生效日期: 2025-12-30
适用范围: Antigravity Engine 全量格局 (A-Z Series)
状态: ENFORCED (强制执行)

一、 建模核心哲学 (The Soul)
物理本质: 八字格局不是高维空间中的一个“点”，而是一个具有特定形状和概率分布的**“统计流形” (Statistical Manifold)**。
概率云 (Probability Cloud): 一个标准的“正财格”或“羊刃架杀”，在 5D 空间中表现为一个协方差椭球。不仅要看中心在哪，还要看它“胖瘦”如何（方差）以及各维度是否“联动”（协方差）。
精密识别: 摒弃简单的“余弦相似度”。识别一个格局，等同于计算该样本落入目标概率势阱 (Potential Well) 的深度。必须引入能量门控，剔除“有形无气”的伪格局。

二、 五维命运张量定义 ($\mathcal{T}_{fate}$)
所有格局的输出，最终都必须坍缩为以下 5 个维度的无量纲投影值 (0.0 - 1.0)。
维度轴
物理定义 (Physics)
通用命理意象 (Metaphysics)
E (Energy)
能级/振幅
生命力、抗压阈值、根基深浅、行动底气
O (Order)
熵减/有序度
权力、社会阶层、自律、管理能力、贵气
M (Material)
物质/做功
财富总量、资产控制力、现实资源、执行成果
S (Stress)
应力/剪切力
风险、灾难、内耗、突发意外、结构断裂
R (Relation)
纠缠/相干性
情感连接、人际网络、六亲缘分、社交耦合

三、 三大物理公理 (The Three Axioms)
为防止 AI 拟合出违反物理常识的矩阵，所有模型必须锁死以下公理。
公理 1：符号守恒 (Conservation of Sign)
微观粒子对宏观维度的**贡献方向（+/-）**通常由物理常识锁定。
示例: 冲/刑 默认增加 S (Stress)；合 默认增加 R (Relation)。
约束: 拟合器必须对权重矩阵实施 Projected Gradient Descent (投影梯度下降)，确保符号不反转。
公理 2：拓扑特异性 (Topological Override)
格局即法律。特定格局有权重定义粒子的物理属性。
规则: 核心反应堆粒子（如杀格之杀）对 E/O/M 的贡献权重必须显著高于背景噪声。允许特定条件下（如相变）发生符号翻转。
公理 3：正交解耦 (Orthogonality)
五维轴线必须在语义上互斥。高 M (财) 不代表高 O (贵)；高 E (寿) 不代表低 S (灾)。描述必须解耦。

四、 六步拟合标准化工作流 (The Standard Workflow)
此流程适用于任何新格局的开发。FDS-V1.5 重点升级了 Step 5 和 Step 6。
Step 1: 物理原型定义 (Prototype Definition)
输入: 古籍定义。
输出: 初始 转换矩阵结构 ($\mathcal{T}_{init}$) 与 公理掩码 (Axiom Mask)。
动作: 确定物理路径的强弱与正负。
Step 2: 样本分层与海选 (Data Stratification)
输入源 (Input Source): 全息 51.8 万全量样本库 (Holographic 518k DB)
说明: 包含从公元前至今的 518,000 例清洗后的八字结构数据。
挖掘漏斗 (Mining Funnel):
L1 结构过滤: 扫描 51.8 万样本，提取符合 A-03 物理特征（刃杀双显且能量 > 0.6）的样本。预计命中率约 2-3% ($\approx$ 10,000 - 15,000 例粗矿)。
L2 交叉验证: 匹配 人生轨迹数据库 (Bio-Data)。剔除只有八字没有人生反馈的“哑巴数据”。
L3 提纯 (Tier A): 最终锁定 500+ 例 具有明确人生标注（如“掌权”、“大富”、“暴败”）的黄金样本。
输出 (Output):
Tier A (Standard): 用于拟合矩阵和构建标准流形。
Tier X (Singularity): 用于构建激活态流形。

Step 3: 矩阵拟合 (Matrix Fitting)
工具: HolographicMatrixFitter
动作:
优化矩阵权重，最小化 $Loss = ||\mathcal{T} \cdot \vec{V}_{in} - \vec{y}_{true}||^2 + \lambda_{physics}$。
注意: 此步骤产出的是**“转换透镜” (Matrix)**，用于将 10 神转化为 5D 张量。
Step 4: 动态演化机制 (Dynamic Mechanics)
输入: 流年/大运介入。
定义状态机:
破格: 触发 collapse_rules。
激活/相变 (Activated): 触发 exceptions (基于 Schema V2.3)，允许调用物理算子（如 analyze_clash_dynamics）进行状态重映射。
Step 5: 全息封卷与流形构建 (Manifold Construction)
升级点: 从“计算质心”升级为“构建流形”。
动作:
将 500 个 Tier A 样本通过拟合好的矩阵投影到 5D 空间。
计算 均值向量 ($\vec{\mu}$)。
计算 协方差矩阵 ($\Sigma$) 及其 逆矩阵 ($\Sigma^{-1}$)，捕捉维度的相关性与分布形状。
打包为 registry.json，不再存储原始样本。
Step 6: 精密模式识别 (Precision Recognition)
升级点: 从“余弦相似度”升级为“概率密度判别”。
运行时逻辑:
能量门控: 计算 $G_{sai} = \tanh(SAI_{curr})$。若 $G_{sai} < Threshold$，直接判定为“气虚/不成格”。
马氏距离: 计算 $D_M = \sqrt{(\vec{x} - \vec{\mu})^T \Sigma^{-1} (\vec{x} - \vec{\mu})}$。
概率评分: $Score = G_{sai} \times \exp(-k \cdot D_M)$。
判定: 若 $Score > 0.65$，则激活格局引擎。

五、 附录：全息注册表通用 Schema (QGA-HR V2.4)
所有格局必须严格遵守此数据结构，支持协方差矩阵存储。
JSON
{
  "meta_info": {
    "pattern_id": "String (e.g., 'D-01')",
    "name": "String (e.g., '标准正财格')",
    "version": "String (e.g., '1.5')",
    "physics_prototype": "String (e.g., 'Gravity Capture System')"
  },

  "physics_kernel": {
    "description": "核心物理参数",
    
    // [1] 转换矩阵 (5x5 权重表)
    "transfer_matrix": {
      "E_row": { "parallel": "float", "resource": "float", ... },
      "O_row": { "power": "float", "output": "float", ... },
      "M_row": { "wealth": "float", ... },
      "S_row": { "clash": "float", "power": "float", ... },
      "R_row": { "combination": "float", ... }
    },

    // [2] 张量动力学 (物理补偿层)
    "tensor_dynamics": {
      "activation_function": "Enum: [tanh_saturation, log_saturation, linear]", 
      "parameters": {
        "k_factor": "float (饱和阈值)",
        "bias": "float (偏移量)"
      },
      "target_axes": ["Array of Strings"]
    },

    "integrity_threshold": "float (0.0-1.0)"
  },

  "feature_anchors": {
    "description": "基于 FDS-V1.5 马氏流形的统计包络",
    
    // [1] 标准态流形 (Standard Manifold)
    "standard_manifold": {
      // 质心 (Mean Vector, μ)
      "mean_vector": { "E": 0.xx, "O": 0.xx, "M": 0.xx, "S": 0.xx, "R": 0.xx },
      
      // 协方差矩阵 (Covariance Matrix, Σ) - 5x5 对称矩阵
      "covariance_matrix": [
        [0.xx, 0.xx, ...], 
        ... 
      ],
      
      // 逆协方差矩阵 (Inverse Σ) - 用于运行时快速计算马氏距离
      "inverse_covariance": [ ... ],

      // 判定阈值
      "thresholds": {
        "max_mahalanobis_dist": "float (e.g., 3.0)",
        "min_sai_gating": "float (e.g., 0.5)"
      }
    },

    // [2] 激活态流形 (Activated Manifold) - 可选
    // 用于处理开库、变格等特殊物理状态
    "activated_manifold": {
      "mean_vector": { ... },
      "covariance_matrix": [ ... ],
      "inverse_covariance": [ ... ],
      "thresholds": {
        "max_mahalanobis_dist": "float (e.g., 4.5)",
        "min_sai_gating": "float (e.g., 0.8)"
      }
    }
  },

  "dynamic_states": {
    "description": "状态机规则 (Schema V2.3)",
    
    "collapse_rules": [
      {
        "trigger_name": "String",
        "default_action": "COLLAPSE",
        "exceptions": [
          {
            "name": "String (e.g., 'Vault_Tunneling')",
            "conditions": [
              {
                "operator": "call_physics",
                "function": "analyze_clash_dynamics", // 物理算子
                "expect": { "entropy_delta": { "gt": 0 } }
              }
            ],
            "override_state": {
              "state": "ACTIVATED",
              "centroid_ref": "activated_manifold", // 切换识别锚点
              "tensor_modifier": { "E": 1.x, "M": 1.x }
            }
          }
        ]
      }
    ],

    "crystallization_rules": [ ... ]
  },

  "algorithm_implementation": {
    "paths": {
      "energy_calculation": "core.physics_engine.compute_energy_flux",
      "tensor_projection": "core.math_engine.project_tensor_with_matrix",
      "pattern_recognition": "core.registry_loader.pattern_recognition" // 必须支持马氏距离
    }
  }
}
