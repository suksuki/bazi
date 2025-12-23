"""
Antigravity Pillar Gravitational Engine (Phase B-11)
====================================================
Core physics logic for Dynamic Pillar Weighting based on Solar Term Progress.
"""

from typing import Dict
import math

class PillarGravityEngine:
    
    @staticmethod
    def calculate_dynamic_weights(progress: float) -> Dict[str, float]:
        """
        Calculates the gravitational weights for Y/M/D/H based on solar term progress.
        Antigravity V10.1: Non-linear Gravity Weight Engine.
        
        Args:
            progress: Float (0.0 to 1.0), representing depth into the solar term.
            
        Returns:
            Dict: { 'Year', 'Month', 'Day', 'Hour' } weights summing to ~1.0.
        """
        # 1. Base Amplitude (Month Dominance V10.1)
        # Base increased to 0.42 (from 0.40) to reflect stronger "Ti Gang" (Outline) nature.
        base_month = 0.42
        
        # 2. Non-linear Gain (Sine Wave Modulation)
        # Peak at t=0.5 -> +0.18 (Max Month = 0.60)
        # Node at t=0.0 -> +0.00 (Min Month = 0.42)
        modulation = 0.18 * math.sin(math.pi * progress)
        
        # 3. Dynamic Month Weight
        w_month = base_month + modulation
        
        # 4. Remaining Energy Distribution (Gravity Decay)
        # Instead of fixed Day weight, we allocate remainder based on proximity/causality.
        remaining = 1.0 - w_month
        
        # Day (Interface): 55% of remainder (Closest to Self)
        w_day = remaining * 0.55
        
        # Hour (Outcome): 30% of remainder (Future Trajectory)
        w_hour = remaining * 0.30
        
        # Year (Background): 15% of remainder (Dissipating Ancestral Field)
        w_year = remaining * 0.15
        
        return {
            "Year": round(w_year, 3),
            "Month": round(w_month, 3),
            "Day": round(w_day, 3),
            "Hour": round(w_hour, 3)
        }

# Export functional alias
calculate_pillar_weights = PillarGravityEngine.calculate_dynamic_weights
