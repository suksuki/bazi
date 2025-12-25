
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from core.trinity.core.physics.core_axioms import CRITICAL_SAI_THRESHOLD, PHASE_TRANSITION_DESTRUCTION

class InterventionEngine:
    """
    🚀 InterventionEngine (V14.0 - Universe Intervention Experiment)
    
    Simulates external energy injections or environmental modifications
    to reset a Bazi chart's position in the Universal Phase Diagram.
    """
    
    def __init__(self, framework):
        self.framework = framework
        self.logger = logging.getLogger("InterventionEngine")

    def simulate_intervention(self, 
                             bazi_chart: List[str], 
                             base_context: Dict[str, Any],
                             intervention_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies a delta to the causal parameters and re-arbitrates.
        
        intervention_params example:
        {
            "geo_shift": {"Wood": +0.5},
            "damping_reduction": -0.1,
            "energy_injection": 1.2 # Scalar boost to all operators
        }
        """
        # 1. Capture Baseline
        baseline = self.framework.arbitrate_bazi(bazi_chart, current_context=base_context)
        
        # 2. Construct Intervention Context
        intervened_context = base_context.copy()
        
        # Apply Damping Shift (The '改命' factor)
        current_damp = intervened_context.get("damping_override", 0.3)
        reduction = intervention_params.get("damping_reduction", 0.0)
        intervened_context["damping_override"] = max(0.01, current_damp + reduction)
        
        # Apply Geo/Elemental Shift
        if "geo_shift" in intervention_params:
            # Inject shifts into the influence bus or context data
            if "data" not in intervened_context: intervened_context["data"] = {}
            intervened_context["data"]["geo_intervention"] = intervention_params["geo_shift"]
        
        # 3. Re-Arbitrate
        intervened = self.framework.arbitrate_bazi(bazi_chart, current_context=intervened_context)
        
        # 4. Calculate Intervention Delta (The '改命' Efficiency)
        sai_diff = intervened["physics"]["stress"]["SAI"] - baseline["physics"]["stress"]["SAI"]
        re_diff = intervened["physics"]["wealth"]["Reynolds"] - baseline["physics"]["wealth"]["Reynolds"]
        
        # Rescue Status: Did we pull the chart out of the brittle zone?
        was_brittle = baseline["physics"]["stress"]["SAI"] > CRITICAL_SAI_THRESHOLD
        now_safe = intervened["physics"]["stress"]["SAI"] <= CRITICAL_SAI_THRESHOLD
        
        return {
            "baseline": baseline,
            "intervened": intervened,
            "delta": {
                "sai_reduction": -sai_diff if sai_diff < 0 else 0,
                "re_gain": re_diff if re_diff > 0 else 0,
                "rescue_success": was_brittle and now_safe
            },
            "params": intervention_params
        }
