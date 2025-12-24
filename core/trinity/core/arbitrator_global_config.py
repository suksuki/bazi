
from enum import Enum, auto
from typing import Dict, List, Any

class ExecutionTier(Enum):
    """
    分层调度总线 (Layered Dispatch Bus) 层级定义
    确保物理逻辑的因果律按序执行。
    """
    ENVIRONMENT = auto()  # 层级 A：时空背景层 (真太阳时、GEO)
    FUNDAMENTAL = auto()  # 层级 B：基础场态层 (五态、宫位权重)
    STRUCTURAL  = auto()  # 层级 C：结构干涉层 (合化相变、墓库隧穿)
    FLOW        = auto()  # 层级 D：流体力学层 (财富流体、生克传导)
    TEMPORAL    = auto()  # 层级 E：时间惯性层 (大运流年、百年脉冲)

class ArbitrationPolicy:
    """
    智能冲突仲裁器 (Conflict Arbitrator) 核心策略
    解决算法之间的互斥与叠加。
    """
    
    # 策略 1: 贪合忘冲逻辑 (Override Clash by Fusion)
    # 当合化触发时，挂起相关支的冲克计算权重
    OVERRIDE_CLASH_BY_FUSION = True
    
    # 策略 2: 结构优先准则 (Same Pillar Bonus)
    # 同柱自坐结构的算法优先级加成
    SAME_PILLAR_PRIORITY_BOOST = 50
    
    # 策略 3: 系统熵临界值 (Entropy Threshold)
    # 超过此值时，优先执行“降噪”算法
    CRITICAL_ENTROPY_LIMIT = 1.5

RULE_PRIORITY_MAP = {
    # 示例优先级映射
    "PH_HE_HUA": 100,           # 合化
    "PH_SAN_HE": 95,            # 三合
    "PH_LIU_HE": 90,            # 六合
    "PH_CHONG": 80,             # 冲
    "PH_PENALTY_3": 70,         # 三刑
    "PH_HARM_6": 60,            # 六害
    "PH_WEALTH_FLOW": 50,       # 财富流
}

TIER_MAPPING = {
    "MOD_00_SUBSTRATE": ExecutionTier.ENVIRONMENT,
    "MOD_01_TRIPLE": ExecutionTier.FUNDAMENTAL,
    "MOD_11_GRAVITY": ExecutionTier.FUNDAMENTAL,
    "MOD_03_TRANSFORM": ExecutionTier.STRUCTURAL,
    "MOD_09_COMBINATION": ExecutionTier.STRUCTURAL,
    "MOD_05_WEALTH": ExecutionTier.FLOW,
    "MOD_06_RELATIONSHIP": ExecutionTier.FLOW,
    "MOD_07_LIFEPATH": ExecutionTier.TEMPORAL,
    "MOD_12_INERTIA": ExecutionTier.TEMPORAL,
}
