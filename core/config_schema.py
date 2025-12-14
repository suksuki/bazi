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
    "flow": {
        # Genesis Compliance Keys
        "generationEfficiency": 1.2, # 生的效率
        "controlImpact": 0.7,        # 克的影响
        "dampingFactor": 0.5,        # 衰减因子
        
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
    }
}
