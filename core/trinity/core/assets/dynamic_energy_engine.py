"""
Antigravity Logic Asset: Dynamic Hidden Stem Engine
===================================================
Version: 1.1 (Refined Asset Lock)
Status: IMMUTABLE

Description:
Standalone core logic for calculating time-dynamic weights of hidden stems
within the 12 earthly branches, using the Damped Sinusoidal Dispersion Model.

Mathematical Model:
P(t) = A * sin^2(π * t + φ) * e^(-τt)
"""

import math
from datetime import datetime
from typing import Dict, List, Optional

class AntigravityEngine:
    """Antigravity V10.0: 单体物理场论核心计算引擎"""
    
    # Official Hidden Stem Structures (Stem, Initial Energy A, Phase Shift φ, Decay τ)
    # Note: Phase Shift φ is in radians relative to π. 
    # Primary: 0, Secondary: π/3, Residual: 2π/3
    # Decay τ is applied to simulate "Qi" dissipation.
    BRANCH_CONFIG = {
        "子": {"癸": {"A": 10.0, "phi": 0.0, "tau": 0.0}},
        "丑": {"己": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "癸": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "辛": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "寅": {"甲": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "丙": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "戊": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "卯": {"乙": {"A": 10.0, "phi": 0.0, "tau": 0.0}},
        "辰": {"戊": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "乙": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "癸": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "巳": {"丙": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "戊": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "庚": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "午": {"丁": {"A": 7.0, "phi": 0.0, "tau": 0.1}, "己": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}},
        "未": {"己": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "丁": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "乙": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "申": {"庚": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "壬": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "戊": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "酉": {"辛": {"A": 10.0, "phi": 0.0, "tau": 0.0}},
        "戌": {"戊": {"A": 5.0, "phi": 0.0, "tau": 0.1}, "辛": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}, "丁": {"A": 2.0, "phi": 2*math.pi/3, "tau": 0.5}},
        "亥": {"壬": {"A": 7.0, "phi": 0.0, "tau": 0.1}, "甲": {"A": 3.0, "phi": math.pi/3, "tau": 0.2}}
    }

    def __init__(self):
        # 锁定物理常数 (V10.0 定稿)
        self.VOID_DAMPING = 0.45      # B-02: 空亡屏蔽系数
        self.EMERGENCE_THRESHOLD = 1.2 # C: 奇点熵阈值
        self.SHEAR_BURST = 2.26       # B-08: 羊刃相变增益
        self.LU_ANCHOR = 1.25        # B-03: 禄神稳定增益

    def calculate_qi_dispersion(self, progress: float, branch: str) -> Dict[str, float]:
        """
        B-01: 支藏干动态能量函数 (Progress: 0.0-1.0)
        实现能量在节气转换过程中的非线性弥散。
        """
        base_config = self.BRANCH_CONFIG.get(branch, {})
        results = {}
        
        # Ensure progress is within bounds [0, 1]
        t = max(0.0, min(1.0, progress))

        for stem, params in base_config.items():
            # A: 标称能级, phi: 相位(进气深度), tau: 衰减速度
            A, phi, tau = params['A'], params['phi'], params['tau']
            
            # 物理波动函数: P(t) = A * sin^2(π * t + φ) * e^(-τt)
            oscillation = math.sin(math.pi * t + phi) ** 2
            decay = math.exp(-tau * t)
            
            val = A * oscillation * decay
            results[stem] = round(val, 4)
            
        return results

    @staticmethod
    def get_solar_progress(target_time: datetime, term_start: datetime, term_end: datetime) -> float:
        """Helper to calculate normalized progress t."""
        total = (term_end - term_start).total_seconds()
        current = (target_time - term_start).total_seconds()
        if total <= 0: return 0.5
        return current / total

# 初始化单体引擎资产 (Singleton Instance)
engine = AntigravityEngine()

# Facade for backward compatibility
def calculate_dynamic_energy(target_time: datetime, term_start: datetime, term_end: datetime, branch: str) -> Dict[str, float]:
    progress = AntigravityEngine.get_solar_progress(target_time, term_start, term_end)
    return engine.calculate_qi_dispersion(progress, branch)
