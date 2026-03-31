"""
Antigravity Spacetime Inertia Engine (Phase B-12)
=================================================
Core physics logic for Fluid Viscosity during Spacetime Transitions (Luck Pillar Handoff).
"""

import math
from typing import Dict, Tuple

class SpacetimeInertiaEngine:
    
    # Standard Inertia Constant (tau) in Months
    # Represents the "half-life" of the previous energy field.
    TAU_DEFAULT = 3.0 

    @staticmethod
    def calculate_inertia_weights(months_since_switch: float, tau: float = 3.0) -> Dict[str, float]:
        """
        Calculates the mixing weights of Previous vs Next energy fields during a transition.
        
        Args:
            months_since_switch: Float. 
                If < 0: Before switch (Prev=1.0, Next=0.0). 
                If >= 0: Time elapsed since the switch point (in months).
            tau: Float. The decay time constant (months).
            
        Returns:
            Dict: { 'Prev_Luck': float, 'Next_Luck': float, 'Viscosity': float }
        """
        if months_since_switch < 0:
            return {"Prev_Luck": 1.0, "Next_Luck": 0.0, "Viscosity": 0.0}
            
        # Fluid Viscosity Model: Exponential Decay
        # W_prev = exp(-t / tau)
        # W_next = 1.0 - W_prev (Conservation of Energy)
        
        # Determine effective weight
        w_prev = math.exp(-months_since_switch / tau)
        w_next = 1.0 - w_prev
        
        # Viscosity Metric: How "mixed" the state is (Max at 0.5/0.5)
        # S_mix ~ 4 * w1 * w2
        viscosity = 4 * w_prev * w_next
        
        return {
            "Prev_Luck": round(w_prev, 4),
            "Next_Luck": round(w_next, 4),
            "Viscosity": round(viscosity, 4)
        }

# Export functional alias
calculate_transition_inertia = SpacetimeInertiaEngine.calculate_inertia_weights
