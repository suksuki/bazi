
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

# Mocking dependent classes for sandbox isolation
@dataclass
class WaveState:
    amplitude: float
    phase: float

class PhaseTransitionManager:
    """
    V17 (Sandbox): Quantum Phase Transition Manager
    ===============================================
    Handles non-linear combination dynamics:
    1. Coherence Index (eta): Degree of combination success.
    2. Lattice Decay: Spatial attenuation.
    3. Residual Essence: Partial phase transition.
    """

    def __init__(self):
        # Configuration for V17 Tuning
        self.DecayLambda = 0.7 # Spatial decay constant (Tuned for C_03)
        self.CatalystBoost = 0.3 # Boost from Stem Catalyst
        self.ConflictPenalty = 0.6 # Penalty for internal conflict

    def calculate_coherence(self, combination_type: str, 
                          branches: List[Dict], 
                          catalyst_stem: Optional[str] = None,
                          month_command: Optional[str] = None,
                          external_conflict: float = 0.0) -> float:
        """
        Calculates the Coherence Index (eta) [0.0 - 1.5]
        
        Args:
            combination_type: 'SanHe', 'SanHui', 'LiuHe'
            branches: List of branch dicts [{'name': '子', 'pos': 2}, ...]
            catalyst_stem: Element of the triggering stem (e.g., 'Water')
            month_command: Element of the month branch
            external_conflict: Energy of conflicting elements (e.g., Fire vs Metal)
        """
        
        # 1. Base Coherence
        base_eta = 0.0
        if combination_type == 'SanHui': base_eta = 1.0
        elif combination_type == 'SanHe': base_eta = 0.8
        elif combination_type == 'LiuHe': base_eta = 0.6
        else: return 0.0

        # 2. Lattice Decay (Spatial)
        # Calculate max distance between involved branches
        positions = sorted([b['pos'] for b in branches])
        max_dist = positions[-1] - positions[0] if len(positions) > 1 else 0
        
        # Compact (dist=1) -> Decay=1.0
        # Spaced (dist=3, Year-Hour) -> Decay=exp(-lambda * (3-1))
        # V17.0 Lattice Model: D(i,j)
        decay_factor = np.exp(-self.DecayLambda * (max_dist - (len(branches)-1)))
        # Adjust logic: max_dist is span. ideal span is len-1.
        # e.g. 3 branches ideally span 2 slots (0,1,2). dist=2.
        # If 0, 2, 3 -> span=3. excess=1.
        excess_gap = max_dist - (len(branches) - 1)
        if excess_gap < 0: excess_gap = 0
        
        lattice_efficiency = np.exp(-self.DecayLambda * excess_gap)

        # 3. Catalyst Boost (Stem)
        catalyst_factor = 0.0
        if catalyst_stem:
            catalyst_factor = self.CatalystBoost
        
        # 4. Month Command (Field)
        # Simplified: If Month supports, boost. If Month opposes, penalty.
        # This requires actual element checking, assuming pre-calculated factor for now
        # For Sandbox, we pass month_command validity externally or assume normalized input
        # Let's assume input 'month_command' is a support coefficient [0.5, 1.5]
        month_factor = 1.0 # Default neutral
        
        # 5. Multi-body Frustration (Conflict)
        # Conflict Penalty: Reduces eta
        conflict_mod = max(0.0, 1.0 - (external_conflict * self.ConflictPenalty))

        # Final Eta
        eta = (base_eta * lattice_efficiency + catalyst_factor) * conflict_mod
        
        return min(max(eta, 0.0), 1.5)

    def calculate_residual_essence(self, eta: float, original_energy: float) -> Tuple[float, float]:
        """
        Calculates the energy split between Transformed and Original state.
        
        Returns:
            (Transformed Energy, Residual Original Energy)
        """
        # Sigmoid transition centered at eta=0.5?
        # Or linear mixture?
        # V17.0 Hypothesis: Linear Mixture for simplicity first.
        
        # If eta >= 1.0: Full Transformation (Residual -> 0)
        if eta >= 1.0:
            return (original_energy, 0.0)
        
        # Partial Transition
        # Transformed part
        e_trans = original_energy * eta
        # Residual part
        e_resid = original_energy * (1.0 - eta)
        
        return (e_trans, e_resid)

