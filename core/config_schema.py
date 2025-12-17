"""
[Antigravity V7.3] 终极全量参数模型 (Final Grand Unified Schema)
================================================================
Based on V2.5 Master Plan.
This file defines the FINAL structure for the Auto-Tuning Architecture.
Replaces all previous versions.
"""

from core.config_rules import (
    SCORE_SANHE_BONUS, SCORE_LIUHE_BONUS, SCORE_CLASH_PENALTY,
    ENERGY_THRESHOLD_STRONG, ENERGY_THRESHOLD_WEAK, SCORE_GENERAL_OPEN,
    SCORE_TREASURY_BONUS, SCORE_SKULL_CRASH
)

# Default Structure (V2.5)
DEFAULT_FULL_ALGO_PARAMS = {
    
    # === 面板 1: 基础场域 (Field Environment) ===
    "physics": {
        # [V2.4 第2条] 五行能量
        "seasonWeights": { 
            "wang": 1.20, "xiang": 1.00, "xiu": 0.80, "qiu": 0.60, "si": 0.40 
        },
        # [V2.4 第5条] 壳核模型 (藏干)
        "hiddenStemRatios": { 
            "main": 0.60, "middle": 0.30, "remnant": 0.10 
        },
        # [新增] 宫位引力 (Pillar Weights)
        "pillarWeights": {
            "year": 0.8, "month": 1.2, "day": 1.0, "hour": 0.9
        },
        # [NEW V2.5] 十二长生修正 (Optional)
        "lifeStageImpact": 0.2
    },

    # === 面板 2: 粒子动态 (Particle Dynamics) ===
    "structure": {
        # [V2.4 第7条] 垂直作用
        "rootingWeight": 1.0,      # 通根系数
        "exposedBoost": 1.5,       # 透干加成
        "samePillarBonus": 1.2,    # 自坐强根加权
        
        # [新增] 黑洞效应 (Void)
        "voidPenalty": 0.5         # 空亡折损 (0.0=Empty, 1.0=Full)
    },

    # === 面板 3: 几何交互 (Geometric Interactions) ===
    "interactions": {
        # [V2.4 第6条] 天干五合
        "stemFiveCombination": {
            "threshold": 0.8,
            "bonus": 2.0,
            "penalty": 0.4,
            "jealousyDamping": 0.3    # [NEW V3.0] 争合损耗
        },
        # [NEW V3.0] 地支合局物理 (Combo Physics)
        "comboPhysics": {
            "trineBonus": 2.5,        # 三合倍率
            "halfBonus": 1.5,         # 半三合倍率
            "archBonus": 1.1,         # 拱合倍率
            "directionalBonus": 3.0,  # 三会倍率
            "resolutionCost": 0.1     # 解冲消耗
        },
        # [NEW V3.0] 宏观时空物理 (Macro Physics)
        "macroPhysics": {
            "eraElement": "Fire",     # 九运离火
            "eraBonus": 0.2,          # 时代红利
            "eraPenalty": 0.1,        # 时代阻力
            
            "latitudeHeat": 0.0,      # 南方火气增益
            "latitudeCold": 0.0,      # 北方水气增益
            "invertSeasons": False,   # 南半球反转
            
            "useSolarTime": True      # 使用真太阳时
        },
        # [NEW V3.0] 墓库物理 (Vault Physics)
        "vaultPhysics": {
            "threshold": 20.0,       # 界定 库vs墓 的能量阈值
            "sealedDamping": 0.4,    # 闭库时的能量折损率
            "openBonus": 1.5,        # 冲开后的爆发倍率
            "punishmentOpens": False,# 是否允许刑开库
            "breakPenalty": 0.5      # 冲破墓的惩罚系数
        },
        # [V2.4 第6条] 地支事件 (Legacy Harmony Mapping)
        "branchEvents": {          
             "threeHarmony": SCORE_SANHE_BONUS, # 15.0
             "sixHarmony": SCORE_LIUHE_BONUS,   # 5.0
             "clashDamping": 0.3,               # 冲的折损系数 (New Scalar)
             "clashScore": SCORE_CLASH_PENALTY, # -5.0 (Legacy Score)
             "harmDamping": 0.2
        },
        # Legacy Treasury/Skull (Keep for compatibility)
        "treasury": { "bonus": SCORE_TREASURY_BONUS },
        "skull": { "crashScore": SCORE_SKULL_CRASH }
    },

    # === 面板 4: 能量流转 (Energy Flow) ===
    # [V8.0 Refactor] The Damping Protocol + Phase Change (阻尼协议 + 相变)
    # [V42.1] Added System Entropy and Output Drain
    "flow": {
        # Genesis Compliance Keys
        "generationEfficiency": 1.2, # 生的效率
        "controlImpact": 0.7,        # 克的影响
        "dampingFactor": 0.5,        # 衰减因子
        "systemEntropy": 0.05,       # [V42.1] 全局系统熵（每轮能量损耗5%）
        "outputDrainPenalty": 1.2,   # [V42.1] 食伤泄耗惩罚（日主生食伤时的额外损耗）
        
        # A. 输入阻抗 (Resource Impedance)
        "resourceImpedance": {
            "base": 0.3,           # 基础阻抗 (Base Resistance)
            "weaknessPenalty": 0.5 # 虚不受补 (Penalty for Weak Self)
        },
        
        # B. 输出粘滞 (Output Viscosity)
        "outputViscosity": {
            "maxDrainRate": 0.6,   # [Critical] 最大泄耗率 (Base Protection)
            "drainFriction": 0.2   # 输出阻力
        },
        
        # C. 全局熵 (System Entropy)
        "globalEntropy": 0.05,     # 每轮损耗 5%
        
        # D. [V8.0 NEW] 相变协议 (Phase Change Protocol)
        # 解决 VAL_006 (星爷) 的 "夏土生金" 悖论
        "phaseChange": {
            "scorchedEarthDamping": 0.15,  # 焦土不生金 (85% blocked in summer)
            "frozenWaterDamping": 0.3       # 冻水不生木 (70% blocked in winter)
        },
        
        # E. Legacy/Base Params (Optional preservation)
        "spatialDecay": { "gap1": 0.6, "gap2": 0.3 }
    },

    # === 面板 5: 时空修正 (Spacetime Modifiers) ===
    "spacetime": {
        "luckPillarWeight": 0.5,    # 大运背景场权重
        "solarTimeImpact": 0.0,     # 真太阳时修正 (0=Off)
        "regionClimateImpact": 0.0  # 地域寒暖修正 (0=Off)
    },
    
    # === Legacy Global (For Compatibility) ===
    "global_logic": {
        "energy_threshold_strong": ENERGY_THRESHOLD_STRONG,
        "energy_threshold_weak": ENERGY_THRESHOLD_WEAK,
        "score_general_open": SCORE_GENERAL_OPEN
    },
    
    # === 面板 6: 判定标准 (Grading Thresholds) ===
    # [V36.1] Dynamic Threshold Tuning
    "grading": {
        "strong_threshold": 60.0,  # Strong >= 此值
        "weak_threshold": 40.0     # Weak < 此值, Balanced 在此之间
    },
    
    # === 面板 7: 图注意力网络 (Graph Attention Network - GAT) ===
    # [V10.0] 从固定邻接矩阵转向动态注意力机制
    "gat": {
        "use_gat": True,               # [V10.0] 启用 GAT 动态注意力（实现局部隔离调优）
        "num_heads": 4,                # Multi-head Attention 头数
        "attention_dropout": 0.29,     # [V10.0] 注意力稀疏度（从敏感度分析得出）
        "leaky_relu_alpha": 0.2,       # LeakyReLU 参数
        "gat_mix_ratio": 0.5,          # GAT 动态矩阵与固定矩阵的混合比例
        "generation_efficiency": 0.3,  # 生的效率（作为先验知识）
        "control_impact": 0.7,         # 克的影响（作为先验知识）
        "combination_weight": 0.5,     # 合的权重
        "clash_weight": -0.8           # 冲的权重
    },
    
    # === 面板 8: Transformer 时序建模 (Transformer Temporal Modeling) ===
    # [V10.0] 时序建模，捕捉长程依赖
    "transformer": {
        "use_transformer": False,      # 是否启用 Transformer（默认 False）
        "d_model": 64,                 # 模型维度
        "num_heads": 4,                # 注意力头数
        "num_layers": 2,               # Transformer 层数
        "dropout": 0.1,                # Dropout 比率
        "max_seq_len": 100,            # 最大序列长度
        "year_weight": 1.0,            # 流年权重
        "month_weight": 0.3,           # 流月权重
        "day_weight": 0.1              # 流日权重
    },
    
    # === 面板 9: 强化学习反馈 (Reinforcement Learning from Human Feedback - RLHF) ===
    # [V10.0] 基于真实案例反馈的自适应进化
    "rlhf": {
        "use_rlhf": False,             # 是否启用 RLHF（默认 False）
        "learning_rate": 0.01,         # 学习率
        "accuracy_weight": 1.0,        # 准确率权重
        "error_penalty_weight": -0.5,  # 误差惩罚权重
        "hit_rate_bonus": 10.0,        # 命中率加成
        "error_threshold": 20.0,       # 误差阈值
        "feedback_file": "data/rlhf_feedback.json"  # 反馈历史文件路径
    },
    
    # === 面板 10: 概率能量值 (Probabilistic Energy Values) ===
    # [V10.1] 将能量值改为概率分布，符合量子八字本质
    "probabilistic_energy": {
        "use_probabilistic_energy": False,  # 是否启用概率能量值（默认 False）
        "monte_carlo_samples": 1000,       # 蒙特卡洛采样次数
        "parameter_perturbation": 0.1,     # 参数扰动范围（10%）
        "return_samples": False            # 是否返回所有采样值（默认 False，只返回统计量）
    },
    
    # === 面板 7.5: 旺衰判定参数 (Strength Determination) ===
    # [V10.0] 旺衰概率波、GAT 动态注意力、贝叶斯自校准
    "strength": {
        # 激活函数中心点（中性点）
        "energy_threshold_center": 2.89,      # 最优值（从敏感度分析得出）
        # 相变宽度（Softplus β 参数）
        "phase_transition_width": 10.0,      # 保持默认值，平滑过渡
        # 注意力稀疏度（GAT dropout）
        "attention_dropout": 0.29            # 最优值（从敏感度分析得出）
    },
    
    # === 面板 8: 非线性激活函数 (Nonlinear Activation) ===
    # [V10.0] 从硬编码 if/else 转向非线性 Soft-thresholding 模型
    "nonlinear": {
        # Softplus/Sigmoid 软阈值参数
        "threshold": 0.5,          # 临界点阈值
        "scale": 10.0,             # Softplus 缩放因子，控制过渡的陡峭程度
        "steepness": 10.0,         # Sigmoid 陡峭度，控制过渡的平滑程度
        
        # 相变能量模型参数
        "phase_point": 0.5,        # 相变点（临界点）
        "critical_exponent": 2.0,  # 临界指数（控制相变的陡峭程度）
        
        # 量子隧穿概率模型参数
        "barrier_height": 0.6,     # 屏障高度（库的封闭强度）
        "barrier_width": 1.0,      # 屏障宽度（库的厚度）
        
        # 多因素综合影响权重
        "clash_intensity_weight": 0.5,  # 冲的强度权重
        "trine_effect_weight": 0.3,     # 三刑效应权重
        "mediation_factor": 0.3,        # 通关缓解因子
        "help_factor": 0.6,             # 帮身缓解因子
        
        # [V10.0] 贝叶斯优化参数 - Jason B 案例优化结果
        "seal_bonus": 43.76,                    # 印星帮身直接加成（0-50）
        "seal_multiplier": 0.8538,              # 印星帮身乘数（0.8-1.2）
        "seal_conduction_multiplier": 1.7445,  # 印星传导乘数（1.0-2.0），用于食神制杀通道
        "opportunity_scaling": 1.8952,          # 机会加成缩放比例（0.5-2.0），用于冲提纲转为机会
        "clash_damping_limit": 0.2820,         # 身强时冲提纲减刑系数（0.1-0.3）
        
        # [V10.0] 非线性阻尼机制 - 防止过拟合（核心分析师建议）
        "nonlinear_damping": {
            "enabled": True,                    # 是否启用非线性阻尼
            "threshold": 80.0,                  # 阻尼阈值（能量超过此值后开始阻尼）
            "damping_rate": 0.3,                # 阻尼率（0-1，值越大阻尼越强）
            "max_value": 100.0                  # 最大允许值（硬上限）
        }
    }
}
