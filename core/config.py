"""
Antigravity Engine V3.0 Core Configuration
==========================================
Role: Single Source of Truth for Numerical Parameters
Version: 3.0 (Pure Logic Support)

此文件承载了从文档和逻辑代码中剥离的所有物理阈值。
Logic Layer (代码) 必须通过 `from core.config import config` 引用这些值，
严禁在业务逻辑中出现任何 Magic Number。
"""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class PhysicsParams:
    """基础物理场参数"""
    k_factor: float = 1.0               # 标准物理常数 K
    time_decay_rate: float = 0.05       # 时间衰减系数
    entropy_baseline: float = 0.5       # 熵基准值

@dataclass
class GatingParams:
    """门控（安全阀）参数"""
    # E-Gating: 能量门控 (防止身弱假格)
    # V2.6 遗留值: 0.45
    weak_self_limit: float = 0.45       
    
    # R-Gating: 关联门控 (防止杂气混杂)
    # V2.6 遗留值: 0.60
    max_relation_limit: float = 0.60
    
    # M-Gating: 物质门控 (成格底线)
    min_wealth_level: float = 0.30

@dataclass
class SingularityParams:
    """奇点与拓扑参数"""
    # 距离判定阈值 (Mahalanobis Distance)
    # 超过此距离被视为"偏离标准流形"
    deviation_threshold: float = 1.35
    
    # 最小成团样本数 (DBSCAN)
    clustering_min_samples: int = 30
    
    # 奇点置信度下限
    confidence_floor: float = 0.75

@dataclass
class PatternSpecificParams:
    """格局专属参数 (可动态扩展)"""
    # A-01 正官格参数
    a01_officer: Dict[str, float] = None
    
    # D-02 偏财格参数
    d02_wealth: Dict[str, float] = None

    def __post_init__(self):
        self.a01_officer = {
            "purity_threshold": 0.55,    # 纯度要求
            "nobility_factor": 1.2       # 贵气加成
        }
        self.d02_wealth = {
            "risk_tolerance": 0.8,       # 风险承受力
            "leverage_cap": 2.0          # 杠杆上限 (奇点专用)
        }

@dataclass
class SystemConfig:
    """系统总配置"""
    version: str = "3.0.0"
    mode: str = "PRODUCTION"
    
    physics: PhysicsParams = field(default_factory=PhysicsParams)
    gating: GatingParams = field(default_factory=GatingParams)
    singularity: SingularityParams = field(default_factory=SingularityParams)
    patterns: PatternSpecificParams = field(default_factory=PatternSpecificParams)

# Global Singleton instance
config = SystemConfig()
