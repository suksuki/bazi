
import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class CollisionResult:
    survived: bool
    remaining_coherence: float  # New eta after collision
    entropy_increase: float     # Chaos generated
    description: str

class StructuralDynamics:
    """
    Phase 18: Dynamic Structural Integrity Manager.
    Models the binding energy of combinations vs external clashes.
    """
    
    # Physics Constants for V18
    K_BINDING = 1.0     # Binding Energy Coefficient
    K_ELASTICITY = 0.5  # Elasticity of the structure (0.0=Brittle, 1.0=Rubber)
    CRITICAL_PSI = 0.4  # Critical threshold for collapse
    CRITICAL_IMPEDANCE_RATIO = 4.2 # Threshold for Total Internal Reflection

    @dataclass
    class FusionState:
        eta: float
        transformed_energy: float
        residual_energy: float
        is_reflexion: bool
        description: str

    @staticmethod
    def trace_fusion_essence(eta: float, total_energy: float) -> FusionState:
        """
        Decompose energy into Transformed Spirit and Residual Essence.
        """
        # Transformed Spirit = Eta * Total
        # Residual Essence = (1 - Eta) * Total
        trans = eta * total_energy
        resid = (1.0 - eta) * total_energy
        return StructuralDynamics.FusionState(
            eta=eta,
            transformed_energy=trans,
            residual_energy=resid,
            is_reflexion=False,
            description=f"Fusion State: {eta*100:.1f}% Transformed, {(1-eta)*100:.1f}% Residual"
        )

    @staticmethod
    def calculate_impedance_mismatch(internal_energy: float, external_energy: float) -> float:
        """
        Calculate Impedance Ratio Z_ratio.
        """
        if internal_energy <= 0.001: return 999.0
        return max(internal_energy, external_energy) / min(internal_energy, external_energy)

    @staticmethod
    def simulate_fusion_reflexion(
        structure_eta: float, 
        structure_energy: float,
        incoming_energy: float,
        is_jealousy: bool = False
    ) -> FusionState:
        """
        Simulate Fusion Dynamics under stress.
        Handles Jealousy Damping and Impedance Reflection.
        """
        # 1. Apply Jealousy Damping
        effective_eta = structure_eta
        desc_prefix = ""
        if is_jealousy:
            effective_eta = 0.31 # Jealousy State
            desc_prefix = "[Jealousy Damping] "
        
        # 2. Trace Essence
        state = StructuralDynamics.trace_fusion_essence(effective_eta, structure_energy)
        state.description = desc_prefix + state.description
        
        # 3. Check Impedance Mismatch
        # If Incoming Energy is massive compared to Transformed Spirit (or vice versa)
        # Usually External Impact vs Transformed Structure
        ratio = StructuralDynamics.calculate_impedance_mismatch(state.transformed_energy, incoming_energy)
        
        if ratio > StructuralDynamics.CRITICAL_IMPEDANCE_RATIO:
            # Total Internal Reflection -> Self Destruction
            state.is_reflexion = True
            state.description += f" -> ⚠️ TOTAL REFLECTION (Ratio {ratio:.2f} > 4.2). Self-Destruction Imminent."
            # Reflexion destroys the structure
            state.transformed_energy = 0.0 
            state.residual_energy *= 1.5 # Chaos increase
        else:
            state.description += f" -> Impedance Match ({ratio:.2f}). Flow stable."
            
        return state
    
    @dataclass
    class DefusionResult:
        broken: bool
        initial_energy: float
        final_energy: float
        entropy_released: float
        description: str

    @staticmethod
    def simulate_defusion_event(
        fusion_energy: float,
        eta: float,
        clash_energy: float,
        resolution_cost: float = 0.1
    ) -> DefusionResult:
        """
        Plan C: De-Fusion Protocol.
        Simulate a Fusion Structure being hit by a Clash.
        """
        # 1. Calculate Binding Barrier (Energy required to break the bond)
        # E_bind = FusionEnergy * Eta^2 (Reinforced by coherence)
        binding_barrier = fusion_energy * (eta ** 2)
        
        # 2. Impact Interaction
        # Does the clash have enough energy to overcome the barrier + cost?
        effective_impact = clash_energy
        
        broken = False
        final_e = fusion_energy
        entropy = 0.0
        desc = ""
        
        if effective_impact > binding_barrier:
            # BREAKING THE BOND
            broken = True
            # Energy Drop: From Fusion State (High) to Scattering State (Low)
            # Assume Fusion Bonus was 2.0x, so base was 0.5 * FusionEnergy
            base_energy = fusion_energy * 0.5 
            
            # Final energy is Base - Collision Loss
            final_e = max(0.0, base_energy - (effective_impact - binding_barrier))
            
            # Massive Entropy Release due to phase transition
            entropy = (fusion_energy - final_e) * 1.5
            
            desc = f"💥 DE-FUSION TRIGGERED! Impact ({effective_impact:.2f}) > Barrier ({binding_barrier:.2f}). Energy crash: {fusion_energy:.2f} -> {final_e:.2f}"
            
        else:
            # RESISTANCE (Prime Directive: Fusion > Clash)
            broken = False
            # Pay Resolution Cost
            final_e = fusion_energy - resolution_cost
            entropy = resolution_cost * 0.1
            desc = f"🛡️ FUSION HOLDS. Impact ({effective_impact:.2f}) deflected by Barrier ({binding_barrier:.2f}). Cost paid: {resolution_cost}"

        return StructuralDynamics.DefusionResult(
            broken=broken,
            initial_energy=fusion_energy,
            final_energy=final_e,
            entropy_released=entropy,
            description=desc
        )
    
        return StructuralDynamics.DefusionResult(
            broken=broken,
            initial_energy=fusion_energy,
            final_energy=final_e,
            entropy_released=entropy,
            description=desc
        )
    
    # --- Multi-Branch & Spatial Logic (Phase 19) ---
    JEALOUSY_DAMPING = 0.3
    CAPTURE_THRESHOLD = 1.5 # Ratio required for Winner-Takes-All
    
    SPATIAL_COEFFS = {
        0: 1.0,  # Same Pillar
        1: 0.6,  # Adjacent
        2: 0.3,  # Gap 1 (One pillar between)
        3: 0.1   # Gap 2 (Two pillars between)
    }
    
    PALACE_WEIGHTS = {
        'year': 0.8,
        'month': 1.2,
        'day': 1.0,
        'hour': 0.9
    }
    
    @dataclass
    class AsymmetricResult:
        winner_idx: int         # -1 if no winner (Deadlock)
        ratio: float
        energies: List[float]   # Final energy per branch
        description: str

    @staticmethod
    def simulate_asymmetric_capture(
        total_energy: float,
        branches: List[Dict] # [{'gap': 1, 'palace': 'year'}, ...]
    ) -> AsymmetricResult:
        """
        Pressure Test A: Asymmetric Spatial Interference.
        Determines if one branch captures the core due to position advantage.
        """
        # 1. Calculate Strength Factors
        factors = []
        for b in branches:
            gap = b.get('gap', 0)
            palace = b.get('palace', 'year')
            
            s_coeff = StructuralDynamics.calculate_spatial_decay(gap)
            p_weight = StructuralDynamics.PALACE_WEIGHTS.get(palace, 1.0)
            
            factors.append(s_coeff * p_weight)
            
        # 2. Compare Top 2
        sorted_indices = np.argsort(factors)[::-1] # Descending
        idx_1 = sorted_indices[0]
        idx_2 = sorted_indices[1]
        
        f1 = factors[idx_1]
        f2 = factors[idx_2]
        
        ratio = f1 / (f2 + 1e-6)
        
        node_final_energies = [0.0] * len(branches)
        winner_idx = -1
        desc = ""
        
        if ratio > StructuralDynamics.CAPTURE_THRESHOLD:
            # WINNER TAKES ALL (Capture)
            winner_idx = idx_1
            # Winner avoids Jealousy Damping? 
            # "Capture Priority... locks... starving others".
            # Let's say Winner gets standard Single-Branch efficiency (Spatial Decay only), 
            # but NO Jealousy Damping because it successfully suppressed the rival.
            
            # Winner Logic:
            # E_eff = Total * (StrengthFactor / SumFactors)? No, that's just distribution.
            # Capture means it acts as if the other doesn't exist.
            # E_winner = Total * Spatial_Coeff(WinnerGap)
            
            win_gap = branches[idx_1].get('gap')
            win_spatial = StructuralDynamics.calculate_spatial_decay(win_gap)
            
            node_final_energies[idx_1] = total_energy * win_spatial
            node_final_energies[idx_2] = 0.0 # Starved
            
            desc = f"🏆 COMPETITIVE CAPTURE! Branch {idx_1} ({branches[idx_1]['palace']}) Dominates (Ratio {ratio:.2f} > {StructuralDynamics.CAPTURE_THRESHOLD}). Rival Starved."
            
        else:
            # DEADLOCK (Revert to Multi-Branch Jealousy)
            winner_idx = -1
            # Use typical Multi-Branch logic but weighted proportional to factors
            total_factor = sum(factors)
            
            # Distribute Total Energy based on factors
            # Then apply Jealousy Damping
            damped_total = total_energy * (1.0 - StructuralDynamics.JEALOUSY_DAMPING)
            
            for i, f in enumerate(factors):
                share = f / total_factor
                # Apply share implies spatial decay is already in 'f'? 
                # Careful not to double count.
                # Standard Multi-Branch: E_node = (E_total/N) * (1-Damp) * Spatial
                # Here: E_node = E_total * (Factor_i / Sum_Factors) * (1-Damp) ? 
                # Actually, Factor includes Spatial.
                # Let's say: E_node = damped_total * share
                
                node_final_energies[i] = damped_total * share
            
            desc = f"⚠️ JEALOUSY DEADLOCK. Ratio {ratio:.2f} insufficient for capture. System Damped."
            
        return StructuralDynamics.AsymmetricResult(
            winner_idx=winner_idx,
            ratio=ratio,
            energies=node_final_energies,
            description=desc
        )

    @dataclass
    class MultiBranchResult:
        total_original_energy: float
        num_branches: int
        energy_per_node: float
        total_effective_energy: float
        is_collapsed: bool
        description: str

    @staticmethod
    def calculate_spatial_decay(gap: int) -> float:
        """
        Get coefficient for spatial distance (Gap).
        Gap 0 = Same Pillar (Theoretical)
        Gap 1 = Adjacent (Year-Month)
        Gap 2 = Gap 1 Pillar (Year-Day)
        Gap 3 = Gap 2 Pillars (Year-Hour)
        """
        return StructuralDynamics.SPATIAL_COEFFS.get(gap, 0.05)

    @staticmethod
    def simulate_multi_branch_interference(
        total_energy: float,
        branches: List[int]  # List of Gaps for each branch interacting with the Core
    ) -> MultiBranchResult:
        """
        Pressure Test B: Multi-Branch Interference (Two Dragons Playing Pearl).
        E_node = (E_original / N) * (1 - Damping) * Spatial_Coeff
        """
        N = len(branches)
        if N <= 1:
            return StructuralDynamics.MultiBranchResult(
                total_original_energy=total_energy, num_branches=N, 
                energy_per_node=total_energy, total_effective_energy=total_energy, 
                is_collapsed=False, description="Single Branch - No Interference."
            )
        
        # 1. Base Split
        base_split = total_energy / N
        
        # 2. Apply Jealousy Damping
        damped_split = base_split * (1.0 - StructuralDynamics.JEALOUSY_DAMPING)
        
        node_energies = []
        for gap in branches:
            # 3. Apply Spatial Decay per branch
            spatial_k = StructuralDynamics.calculate_spatial_decay(gap)
            node_e = damped_split * spatial_k
            node_energies.append(node_e)
            
        total_effective = sum(node_energies)
        
        # 4. Collapse Check
        # If effective energy is too low (< 50% of original), system enters "Binding" (Jiban) state
        is_collapsed = total_effective < (total_energy * 0.5)
        
        state_desc = "BINDING (Jiban)" if is_collapsed else "FUSION (Weak)"
        desc = f"Interference N={N}. {state_desc}. Total Eff: {total_effective:.2f} (Orig: {total_energy:.2f}). Nodes: {[f'{e:.2f}' for e in node_energies]}"
        
        return StructuralDynamics.MultiBranchResult(
            total_original_energy=total_energy,
            num_branches=N,
            energy_per_node=damped_split, # Before spatial
            total_effective_energy=total_effective,
            is_collapsed=is_collapsed,
            description=desc
        )

    @staticmethod
    def calculate_binding_energy(eta: float, raw_energy: float) -> float:
        """
        Calculate E_bind based on coherence (eta) and raw energy.
        E_bind = k * eta^2 * raw_energy
        """
        # Non-linear binding: coherence squared implies cooperative reinforcement
        return StructuralDynamics.K_BINDING * (eta ** 2) * raw_energy

    @staticmethod
    def simulate_collision(
        structure_eta: float, 
        structure_energy: float, 
        clash_energy: float
    ) -> CollisionResult:
        """
        Simulate a high-energy particle (Year/Luck) hitting the structure.
        """
        e_bind = StructuralDynamics.calculate_binding_energy(structure_eta, structure_energy)
        
        # Shielding Factor: High eta provides "structural shielding" 
        # The effective clash energy is reduced by the coherence field?
        # No, let's keep it simple: E_clash vs E_bind + E_inertia
        
        # 1. Absorbed Energy
        # If structure is 'rubbery' (high elasticity), it absorbs more shock.
        # Let's say higher eta = higher elasticity.
        elasticity = structure_eta * StructuralDynamics.K_ELASTICITY
        absorbed = clash_energy * elasticity
        effective_impact = clash_energy - absorbed
        
        delta_eta = 0.0
        entropy = 0.0
        survived = True
        desc = ""
        
        # 2. Impact Analysis
        if effective_impact > e_bind:
            # COLLAPSE
            survived = False
            delta_eta = -structure_eta # Loss of all coherence
            entropy = effective_impact * 2.0 # Huge entropy release
            desc = f"💥 Structural Collapse! Impact ({effective_impact:.2f}) > Binding ({e_bind:.2f})"
        else:
            # OSCILLATION
            survived = True
            # Damage calculation
            damage_ratio = effective_impact / (e_bind + 1e-5)
            delta_eta = -0.1 * damage_ratio * structure_eta # Degradation
            entropy = effective_impact * 0.5
            desc = f"⚠️ Structural Oscillation. Damping impact. Eta change: {delta_eta:.3f}"
            
        final_eta = max(0.0, structure_eta + delta_eta)
        
        return CollisionResult(
            survived=survived,
            remaining_coherence=final_eta,
            entropy_increase=entropy,
            description=desc
        )

    @staticmethod
    def su_dongpo_test_case():
        """
        Test Case for Su Dongpo:
        Structure: Yi Mao (Day) + Xin Chou (Month) -> No strong bond?
        Wait, user said: "Yi Mao Day born in Xin Chou Month"
        Intervention: "You Gold (Rooster) clashes Mao (Rabbit)" or "Zi Water (Rat) combines Chou (Ox)"
        
        Let's model the "Mao-Xu" Combine-Breaker or similar.
        User specified: "You Gold (Year/Luck) clashes Mao".
        """
        return StructuralDynamics.simulate_1079_collapse()

    @staticmethod
    def simulate_1079_collapse():
        """
        1079 Ji Wei Year (Wutai Poem Case).
        Case C_04 Structure:
        - Weak Yi Wood rooted in Mao (Day).
        - Clash: Chou (Month) vs Wei (Year 1079).
        - Result: Root destabilization.
        """
        print("--- 1079 Ji Wei Year: Su Dongpo Collapse Simulation ---")
        
        # 1. Base Structure (Yi Wood Roots in Mao)
        # Without Wei, Mao is stable. Eta represents root stability.
        eta_struct = 0.85 # Good root
        energy_struct = 12.0
        
        # 2. Incoming Year: Ji Wei
        # Wei (Sheep) Clashes Chou (Ox) but also potentially Combines Mao (Half Wood).
        # HOWEVER, the prompt emphasizes "Collapse".
        # Let's assume the "Chou-Wei Clash" breaks the "Mao-Wei Combine"?
        # Or simply, the Wei Year brings massive Earth/Wood energy that destabilizes the fragile balance.
        # Let's model it as a High Energy Impact on the Root.
        
        energy_clash = 18.5 # Violent Clash Energy
        
        print(f"Structure (Yi-Mao Root): Eta={eta_struct}, Energy={energy_struct}")
        print(f"Incoming Year (Ji Wei): Clash Energy={energy_clash}")
        
        e_bind = StructuralDynamics.calculate_binding_energy(eta_struct, energy_struct)
        print(f"Calculated Binding Energy: {e_bind:.4f}")
        
        result = StructuralDynamics.simulate_collision(eta_struct, energy_struct, energy_clash)
        print(f"Result: {result.description}")
        print(f"Remaining Coherence: {result.remaining_coherence:.4f}")
        print(f"Entropy Generated (Collapse Entropy): {result.entropy_increase:.4f}")
        
        print(f"Entropy Generated (Collapse Entropy): {result.entropy_increase:.4f}")
        
        return result

    @staticmethod
    def generalized_collision(
        eta_struct: float, 
        energy_struct: float, 
        energy_clash: float
    ) -> CollisionResult:
        """
        Generic wrapper for global scanning.
        """
        # Calculate binding energy for current case
        e_bind = StructuralDynamics.calculate_binding_energy(eta_struct, energy_struct)
        
        # Simulate
        return StructuralDynamics.simulate_collision(eta_struct, energy_struct, energy_clash)


if __name__ == "__main__":
    StructuralDynamics.su_dongpo_test_case()
