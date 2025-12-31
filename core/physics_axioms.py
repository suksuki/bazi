
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

    "D-01": { # Zheng Cai (Wealth Proper)
        "M_row": {
            "wealth": (0.8, 3.0),  # Material-centric
            "output": (0.2, 1.2),  # Output feeds wealth
            "power": (-0.5, 0.5)   # Power consumes wealth (tax/status cost)
        },
        "E_row": {
            "parallel": (0.5, 2.0),
            "wealth": (-1.5, 0.2)  # Wealth consumes DM energy (Shen Ruo Cai Wang)
        },
        "O_row": {
            "wealth": (0.1, 1.0)   # Wealth creates status
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
    }
}
