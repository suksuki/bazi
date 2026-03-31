
"""
🏛️ QGA Physics Axioms & Constraints (FDS-V1.4)
==============================================

Defines the ground-truth physical laws that the Matrix Fitter must respect.
Prevents overfitting by ensuring weight signs match reality.
"""

from typing import Dict, Any

# Standard Axioms (Universal)
# Format: { Row: { Input: (Min, Max) } }
AXIOM_CONSTRAINTS = {
    "STANDARD": {
        "E_row": {  # Energy/Survival axis
            "parallel": (0.0, 2.0),
            "resource": (0.0, 2.0),
            "clash": (-1.0, 0.0)
        },
        "O_row": {  # Order/Power axis
            "power": (0.0, 2.0),
            "resource": (0.0, 1.5),
            "output": (-1.5, 0.5)  # Output can hurt order if unconstrained
        },
        "M_row": {  # Material/Wealth axis
            "wealth": (0.0, 2.0),
            "output": (0.0, 1.5),
            "parallel": (-1.0, 0.5), # Rob wealth consumes
            "resource": (-0.2, 0.8)  # Resource can assist but might dampen flow
        },
        "S_row": {  # Stress/Risk axis
            "power": (0.0, 2.0),
            "clash": (0.0, 2.0),
            "wealth": (0.1, 1.5),      # Wealth often brings stress
            "combination": (-1.0, 0.5)  # Comb usually stabilizes
        },
        "R_row": {  # Relationship/Connection axis
            "combination": (0.0, 1.5),
            "clash": (-1.5, 0.0),
            "wealth": (0.0, 1.0)        # Wealth assists connection in social physics
        }
    },
    
    # Pattern Overrides (Axiom 2)
    "A-03": {
        "E_row": {
            "parallel": (1.0, 3.0),    # Reactor Fuel
            "resource": (0.2, 1.5)
        },
        "O_row": {
            "power": (0.8, 3.0),       # Magnetic Constraint (Killer)
            "parallel": (0.05, 0.8),   # Fuel stability
            "wealth": (-1.0, -0.1)     # M-Overload (Wealth hurts order)
        },
        "M_row": {
            "wealth": (0.0, 0.5),      # Suppression of standard wealth accretion
            "parallel": (-1.0, 0.0)    # High consumption
        },
        "S_row": {
            "clash": (0.5, 2.0),       # Natural high pressure
            "power": (-0.2, 0.5)       # Killer is constrained in successful state
        },
        "R_row": {
            "combination": (0.2, 1.5)  # Stabilization (Coolant)
        }
    },

    "D-01": { # Zheng Cai (Wealth Proper) - FDS-V1.5 Granular
        "M_row": {
            "zheng_cai": (1.2, 3.0),   # 主序星
            "jie_cai": (-1.8, -1.0),   # 强负贡献
            "shi_shen": (0.2, 1.2),    # 食神生财
            "zheng_guan": (0.1, 0.8)   # 护财
        },
        "E_row": {
            "bi_jian": (0.8, 2.0),     # 恒星质量
            "zheng_yin": (0.5, 1.5),   # 资源补给
            "zheng_cai": (-1.5, -0.2)  # 耗泄能级
        },
        "O_row": {
            "zheng_guan": (0.5, 2.0),
            "zheng_cai": (0.1, 1.0)    # 财旺生官
        },
        "S_row": {
            "clash": (0.5, 2.5),       # 轨道震荡
            "qi_sha": (0.3, 2.0)       # 压力源
        }
    },

    "D-02": { # Pian Cai (Indirect Wealth/Windfall)
        "M_row": {
            "wealth": (1.0, 4.0),   # Higher volatility/gain
            "output": (0.5, 2.0),   # Strong output needed for windfall
            "clash": (0.1, 1.5),    # Windfalls often come from "Clash" triggers (Opening tombs)
            "parallel": (-2.0, 0.0) # Peers rob windfall aggressively
        },
        "E_row": {
            "wealth": (-2.0, 0.0)   # Huge energy drain for huge gains
        },
        "S_row": {
            "wealth": (0.5, 2.5),   # High pressure/risk accompanywindalls
            "clash": (0.2, 2.0)
        }
    },

    "B-01": { # Shi Shen (Eating God / The Artist)
        "M_row": {
            "shi_shen": (0.05, 1.5),   # 财之源 (User suggest +0.3)
            "zheng_cai": (0.4, 2.0)    # 坐地取财 (User suggest +0.8)
        },
        "S_row": {
            "shi_shen": (-2.0, -0.1),  # 减震器 (User suggest -0.6)
            "qi_sha": (-1.0, 0.5)      # 杀受制 (User suggest -0.3)
        },
        "O_row": {
            "shi_shen": (-1.5, 0.5),   # 不喜约束 (User suggest -0.2)
            "zheng_guan": (0.05, 1.0)  # 维持基本秩序 (User suggest +0.3)
        },
        "E_row": {
            "bi_jian": (0.2, 1.5),     # 动力源 (User suggest +0.6)
            "shi_shen": (0.05, 1.0)    # 泄秀能级 (User suggest +0.4)
        },
        "R_row": {
            "shi_shen": (0.1, 1.5),    # 口才社交 (User suggest +0.5)
            "bi_jian": (0.1, 1.0)      # 同道中人 (User suggest +0.4)
        }
    }
}
