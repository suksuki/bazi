"""
[Antigravity V7.3] 终极全量参数模型 (Final Grand Unified Schema)
================================================================
Based on V2.5 Master Plan.
This file defines the FINAL structure for the Auto-Tuning Architecture.
Replaces all previous versions.

[V13.1] 参数清洗说明：
- 已删除 season_dominance_boost：避免能量通胀，由 seasonWeights.wang 和 pillarWeights.month 决定
- 已删除 floating_peer_penalty：由通根饱和函数 (Tanh/Sigmoid) 处理无根虚弱
- 大运/流年参数保留（用于Phase 2+），但不在Phase 1 UI显示
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
        # [V13.1] 最终调优：泄气(xiu)从0.85提升到0.90，被克(si)从0.50降低到0.45，确保显著差异
        "seasonWeights": { 
            "wang": 1.20, "xiang": 1.00, "xiu": 0.90, "qiu": 0.60, "si": 0.45 
        },
        # [V2.4 第5条] 壳核模型 (藏干)
        "hiddenStemRatios": { 
            "main": 0.60, "middle": 0.30, "remnant": 0.10 
        },
        # [新增] 宫位引力 (Pillar Weights)
        # [V12.5] 强制纠正宫位权重倒挂：确保物理逻辑正确（Day >= 1.2 > Hour <= 0.9）
        # [V13.1] 最终调优：日支权重从1.2提升到1.35，解决Group C倒挂问题
        "pillarWeights": {
            "year": 0.7,   # V12.5: 年支权重
            "month": 1.42, # V13.1: 月令权重（最高，满足皇权约束）
            "day": 1.35,   # V13.1: 日支权重
            "hour": 0.77   # V13.1: 时支权重（修正位置倒挂）
        },
        # [NEW V2.5] 十二长生修正 (Optional)
        "lifeStageImpact": 0.2,
        # [V13.1] 参数清洗：删除 season_dominance_boost（避免能量通胀，由 seasonWeights.wang 和 pillarWeights.month 决定）
        # [V13.1] 参数清洗：删除 floating_peer_penalty（由通根饱和函数处理）
        "season_decay_factor": 0.3,     # V12.2: 失令衰减因子（被月令克制时的衰减系数）
        "self_punishment_damping": 0.2,  # 自刑惩罚（自刑地支能量保留比例，0.2=保留20%）
        # [V13.1] 大运/流年参数：保留在配置中（用于Phase 2+），但不在Phase 1 UI显示
        "dayun_branch_multiplier": 1.2,  # 大运地支权重倍数（相对于月令）
        "dayun_stem_multiplier": 0.8,    # 大运天干权重倍数（相对于月令）
        "liunian_power": 2.0,            # 流年权力系数（初始能量增强倍数）
        "liunian_decay_rate": 0.9        # 流年能量衰减率（每次迭代）
    },

    # === 面板 2: 粒子动态 (Particle Dynamics) ===
    "structure": {
        # [V2.4 第7条] 垂直作用
        # [V10.0 Normalized] 通根系数归一化 (1.0)
        "rootingWeight": 1.0,  # [V10.0] From 2.16/1.2 -> 1.0
        # [V12.2] 非线性饱和函数参数
        "rootingSaturationMax": 2.5,      # 通根最大加成上限（饱和函数 max_val）
        "rootingSaturationSteepness": 0.8, # 通根饱和曲线陡峭度（控制边际递减速度）      # 通根系数
        "exposedBoost": 1.5,       # 透干加成 [V10.0] Normalized to 1.5
        # [V10.0 Normalized] 自坐系数归一化 (1.5)
        "samePillarBonus": 1.5,    # 自坐强根加权 [V10.0] From 4.0/3.0 -> 1.5
        
        # [新增] 黑洞效应 (Void)
        "voidPenalty": 0.45         # 空亡折损 (0.0=Empty, 1.0=Full) - V13.5: 校准为 0.45
    },

    # === 面板 3: 几何交互 (Geometric Interactions) ===
    "interactions": {
        # [V2.4 第6条] 天干五合
        # [V13.3 Phase 2] 量子纠缠参数：用于计算干支的合化与刑冲（对应 Group F）
        "stemFiveCombination": {
            "//_COMMENT": "V11.1 Tuning: Normalized Energy Scale (~4.0)",
            "threshold": 3.0,     # [重校] 合化阈值: 必须有 3.0 以上的能量底座才能合化
            "bonus": 1.5,
            "penalty": 0.7        # 羁绊损耗
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
        # [NEW V11.0] 墓库物理 (Vault) - Realigned to Normalized Energy (~4.0)
        "vault": {
            "threshold": 3.5,       # 界定 库vs墓 的能量阈值
            "sealedDamping": 0.4,    # 闭库时的能量折损率
            "openBonus": 1.8,        # 冲开后的爆发倍率
            "punishmentOpens": False,# 是否允许刑开库
            "breakPenalty": 0.5      # 冲破墓的惩罚系数
        },
        # [V2.4 第6条] 地支事件 (Legacy Harmony Mapping)
        # [V13.5 Phase 2] 量子纠缠参数：解耦"合"的参数，区分三合/半合/拱合/六合的物理差异
        "branchEvents": {
             "clashScore": SCORE_CLASH_PENALTY,         # -5.0 (Legacy Score)
             "harmDamping": 0.2,                        # (Legacy)
             
             # [V13.5] Phase 2 精细参数
             "clashDamping": 0.4,                       # [Phase 2] 冲的折损：子午冲导致双方能量都大幅削减，且σ(不确定度)暴增
             
             # [V13.5] 三合 (Three Harmony) - 120°相位，共振质变
             "threeHarmony": {
                 "bonus": 1.6,                          # [V11.1] 1.6
                 "transform": True                      # 允许改变五行属性（化气）
             },
             
             # [V13.5] 半合 (Half Harmony) - 不完全共振
             "halfHarmony": {
                 "bonus": 1.25,                          # [V11.1] 1.25
                 "transform": False                     # 通常不彻底改变属性，除非月令支持
             },
             
             # [V13.5] 拱合 (Arch Harmony) - 缺中神，虚拱
             "archHarmony": {
                 "bonus": 1.1,                          # 能量微升（暗拱）
                 "transform": False
             },
             # [V12.0] Wave Physics Parameters
             "clashPhase": 2.618,                      # 150度 (相消)
             "clashEntropy": 0.6,
             "punishPhase": 2.513,                     # 144度
             "punishEntropy": 0.7,
             "resonanceQ": 1.5,                        # 土刑激旺
             
             # [V13.5] 六合 (Six Harmony) - 磁力吸附，物理羁绊
             "sixHarmony": {
                 "bonus": 1.15,                          # [V11.1] 1.15
                 "bindingPenalty": 0.2,                   # 羁绊惩罚：活性/对外输出降低 20%
                 "phase": 0.332                         # 19度 (相长)
             },
             
             # [V13.9] 三会局 (Three Meetings) - 方局，力量最强（纯暴力）
             "threeMeeting": {
                 "bonus": 2.5,                          # 能量最强（方局）
                 "transform": True                      # 必须改变五行（整个家族站在一起）
             },
             # [V11.1 新增] 土刑物理参数
             "earthlyPunishmentBonus": 1.3
        },
        # Legacy Treasury/Skull (Keep for compatibility)
        "treasury": { "bonus": SCORE_TREASURY_BONUS },
        "skull": { "crashScore": SCORE_SKULL_CRASH }
    },

    # === 面板 4: 能量流转 (Energy Flow) ===
    # [V8.0 Refactor] The Damping Protocol + Phase Change (阻尼协议 + 相变)
    # [V42.1] Added System Entropy and Output Drain
    "flow": {
        # [V13.3 Phase 2] 流体力学参数 (Fluid Dynamics)
        # 用于计算普通的生克泄耗（对应 Group D 和 E）
        "generationEfficiency": 0.7,  # [Phase 2] 生的效率：甲木生丙火，甲木付出100，丙火实际得到70（传输损耗30%）
        "generationDrain": 0.3,        # [Phase 2] 泄的程度：甲木生丙火，甲木自身减损30%（生别人很累）
        "controlImpact": 0.5,          # [Phase 2] 克的破坏力：水克火，火的能量直接打5折（防止克过头变成"斩尽杀绝"）
        "dampingFactor": 0.1,         # [Phase 2] 系统阻尼/熵增：每次能量传递的自然损耗，防止数值爆炸
        
        # [V13.3 Phase 2] 空间场参数 (Spatial Field)
        # 用于计算距离对生克的影响（对应 Group C 在动态中的表现）
        "spatialDecay": {
            "//_COMMENT": "V11.1 Tuning: Flatter Field for Low Energy Level",
            "gap0": 1.0,
            "gap1": 0.9,
            "gap2": 0.75,
            "gap3": 0.6
        },
        
        # Legacy/Compatibility Keys (保留向后兼容)
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
        }
    },

    # === 面板 5: 时空修正 (Spacetime Modifiers) ===
    "spacetime": {
        "luckPillarWeight": 1.5,    # [V11.0] 大运背景场权重 (Model D Fit)
        "annualPillarWeight": 0.5,  # [V11.0] 流年动态场权重 (Model D Fit)
        "geo": {
            "//_COMMENT": "V11.0 Module C: Macro Physics Boost",
            "latitudeHeat": 0.08,   # 每10度热力修正系数
            "latitudeCold": 0.08    # 每10度冷力修正系数
        },
        "era": {
            "eraElement": "fire",   # 当前九运五行
            "eraBonus": 0.25        # 时代红利系数
        },
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
        # [V10.0 新数据集调优] 从2.89调整到4.16，匹配率从45.2%提升到50.0%（91个案例）
        "energy_threshold_center": 4.16,      # 最优值（网格搜索得出，范围4.16-4.40都达到50.0%）
        # 相变宽度（Softplus β 参数）
        "phase_transition_width": 10.0,      # 保持默认值，平滑过渡
        # 注意力稀疏度（GAT dropout）
        "attention_dropout": 0.29,           # 最优值（从敏感度分析得出）
        # [V10.0 核心分析师建议] 从格阈值（Extreme Weak Lock）
        "follower_threshold": 0.15,          # 当 strength_probability < 此值时，判定为 Follower（从格）
        # [V12.1] 判定阈值（可调整，解决"概率高却判定为弱"的问题）
        "weak_score_threshold": 40.0,        # 分数 ≤ 此值，直接判定为弱（默认40.0）
        "strong_score_threshold": 50.0,      # 分数 > 此值 且 概率 ≥ 60%，判定为强（默认50.0）
        "strong_probability_threshold": 0.60  # 概率 ≥ 此值 且 分数 > 50，判定为强（默认0.60）
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
    },

    # === 面板 11: 谐振与从格 (Resonance & Follow Pattern) ===
    # [V21.0] 基于波动力学的从格判定与谐振增强
    "resonance": {
        "criticalLockingRatio": 1.8,       # 注入锁定阈值（从格判定门槛）
        "beatingThreshold": 0.5,          # 拍频阈值
        "coherentSyncThreshold": 0.95,    # 真从同步阈值
        "beatingSyncThreshold": 0.6,      # 假从同步阈值
        "superconductiveBoost": 0.5,      # 超导增强系数 (True Follow Bonus)
        "beatingBaseMultiplier": 0.6,     # 拍频基础倍率
        "beatingAmplitudeSwing": 0.5      # 拍频摆幅系数
    }
}
