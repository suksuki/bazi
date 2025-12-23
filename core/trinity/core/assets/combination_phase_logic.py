"""
Antigravity Combination Phase Logic (Phase B-09)
================================================
Core physics logic for determining Stem Combination Phase Transitions.
"""

from typing import List, Dict, Any

class CombinationPhaseEngine:
    
    # Critical Phase Change Threshold
    THRESHOLD = 0.65

    @staticmethod
    def check_combination_phase(stems: List[str], month_energy: float) -> Dict[str, Any]:
        """
        判定干合是否成功化气 (Determine if Stem Combination transforms Qi).
        
        Args:
            stems: List of combining stems (e.g., ['丁', '壬'])
            month_energy: The normalized energy coefficient of the target element in the month (0.0 - 1.0+)
            
        Returns:
            Dict: Status, Message, and Power Ratio.
        """
        # Threshold Logic
        if month_energy >= CombinationPhaseEngine.THRESHOLD:
            return {
                "status": "PHASE_TRANSITION", 
                "msg": "合化成功 (Transformation Success)", 
                "power_ratio": 1.0,
                "dynamic_gain": "SUPERCONDUCTING"
            }
        else:
            return {
                "status": "ENTANGLEMENT", 
                "msg": "合而不化 (Entanglement/Bound)", 
                "power_ratio": 0.3, # Residual binding interference
                "dynamic_gain": "INTERFERENCE"
            }

# Export functional alias
check_combination_phase = CombinationPhaseEngine.check_combination_phase
