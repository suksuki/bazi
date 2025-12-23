
"""
Quantum Trinity V2.0: The Oracle
================================
Elegant Facade and Orchestrator for the Bazi Physics system.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

from .nexus.definitions import PhysicsConstants, BaziParticleNexus
from .physics.wave_laws import WaveState, WaveLaws, PhaseTransitionTheory
from .engines.energy_flux import EnergyFlux
from .engines.resonance_field import ResonanceField, ResonanceProfile
from .intelligence.logic_arbitrator import LogicArbitrator
from core.logic_registry import LogicRegistry
from .intelligence.quantum_remedy import QuantumRemedy
from .intelligence.deconstructor import Deconstructor
from .engines.structural_stress import StructuralStressEngine
from .engines.wealth_fluid import WealthFluidEngine
from .engines.relationship_gravity import RelationshipGravityEngine
from .engines.quantum_dispersion import QuantumDispersionEngine
from .engines.causal_entanglement import CausalEntanglementEngine
from .intelligence.symbolic_stars import SymbolicStarsEngine

class TrinityOracle:
    """The Single Point of Truth and Analysis Orchestrator."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def analyze(self, 
                pillars: List[str], 
                day_master: str,
                luck_pillar: Optional[str] = None,
                annual_pillar: Optional[str] = None,
                t: float = 0.0,
                prev_sync: float = 1.0,
                injections: Optional[List[str]] = None,
                birth_date: Optional[datetime] = None,
                dispersion_mode: bool = False) -> Dict[str, Any]:
        """
        [UNIFIED V2.0 PIPELINE]
        Logic -> Field Init -> Flux -> Resonance -> Verdict -> Remediation -> Deconstruction
        """
        all_pillars = pillars.copy()
        if luck_pillar: all_pillars.append(luck_pillar)
        if annual_pillar: all_pillars.append(annual_pillar)
        
        # 1. Logic Analysis
        interactions = LogicArbitrator.match_interactions(all_pillars, day_master)
        
        # [NEW] 1b. Symbolic Stars Architecture (Shen Sha)
        # Collect branches from pillars AND injections
        branches_only = [p[1] for p in all_pillars if len(p) >= 2]
        if injections:
            branches_only.extend([i for i in injections if i in BaziParticleNexus.BRANCHES.keys()])
            
        star_engine = SymbolicStarsEngine()
        star_stats = star_engine.analyze_stars(day_master, branches_only)
        star_mods = star_engine.get_physical_modifiers(star_stats)
        
        # Inject active stars into interactions for UI visibility
        for star in star_stats['active_stars']:
             interactions.append({
                 "id": f"STAR_{star['name']}", "type": "SYMBOLIC_STAR", "name": f"星辰: {star['name']}",
                 "target_element": "Field", "q": 1.0, "phi": 0.0, "lock": False,
                 "priority": 15, "branches": {star['node']}
             })
        
        # [Phase B] 2. Field Initialization (with optional Quantum Dispersion)
        phase_progress = None
        dispersion_engine = None
        if dispersion_mode and birth_date:
            dispersion_engine = QuantumDispersionEngine()
            solar_terms = QuantumDispersionEngine.get_solar_term_times_for_year(birth_date.year)
            # Handle year boundary if birth is near January
            if birth_date.month == 1 and birth_date.day < 10:
                solar_terms.update(QuantumDispersionEngine.get_solar_term_times_for_year(birth_date.year - 1))
            elif birth_date.month == 12 and birth_date.day > 20:
                solar_terms.update(QuantumDispersionEngine.get_solar_term_times_for_year(birth_date.year + 1))
                
            phase_progress, current_term, next_term = dispersion_engine.calculate_phase_progress(birth_date, solar_terms)
            print(f"DEBUG: Quantum Dispersion Active. Progress in {current_term}: {phase_progress:.4f}")

        initial_waves = LogicArbitrator.initialize_field(
            all_pillars, 
            day_master, 
            phase_progress=phase_progress, 
            dispersion_engine=dispersion_engine
        )
        
        # 3. Apply Manual Injections (if any)
        if injections:
            for char in injections:
                 for elem in initial_waves:
                      initial_waves[elem] = QuantumRemedy.apply_injection(initial_waves[elem], char)
        
        # 4. Flux Rheology (Energy Flow)
        # Month branch is index 1 of pillars
        month_b = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) > 1 else '寅'
        final_waves = EnergyFlux.simulate_flow(initial_waves, month_b, steps=3)
        
        # 5. Resonance Analysis
        from core.bazi_profile import BaziProfile
        day_p = pillars[2] if len(pillars) > 2 else ""
        voids = BaziProfile.get_void_branches(day_p)
        is_void = month_b in voids
        
        dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "", 0))
        
        # Calculate DM's personal contribution (Source only)
        # We need the seasonal factors for the DM element
        month_b_for_season = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) > 1 else '寅'
        seasonal_factors = PhysicsConstants.SEASONAL_MATRIX.get(month_b_for_season, {e: 1.0 for e in PhysicsConstants.ELEMENT_PHASES})
        dm_w_prio = PhysicsConstants.PILLAR_WEIGHTS.get('day', 1.0)
        
        # [PHASE B] Apply Lu Gain modifier
        dm_amp = PhysicsConstants.BASE_SCORE * dm_w_prio * seasonal_factors.get(dm_elem, 1.0) * star_mods['lu_gain']
        dm_wave = WaveState(dm_amp, PhysicsConstants.ELEMENT_PHASES[dm_elem])
        
        # The 'Field' is the total system energy MINUS the Day Master's personal contribution
        # Note: We subtract from total before flux? No, let's use the total and treat DM as probe.
        # Better: Subtract normalized DM from the total final waves
        field_total_complex = sum(w.to_complex() for w in final_waves.values())
        field_net_complex = field_total_complex - dm_wave.to_complex()
        field_net_wave = WaveState.from_complex(field_net_complex)
        
        # Pass a list of element waves as field_list for phase dispersion calculation
        # But we must ensure the DM-element bucket in the list doesn't include the DM stem
        field_list = []
        for k, v in final_waves.items():
            if k == dm_elem:
                # Subtract DM component from its element's total
                net_v = WaveState.from_complex(v.to_complex() - dm_wave.to_complex())
                field_list.append(net_v)
            else:
                field_list.append(v)
        
        resonance = ResonanceField.evaluate_system(dm_wave, field_list, prev_sync=prev_sync, is_void=is_void)
        
        # 6. Verdict (Phase Transition)
        allies = [dm_elem]
        for m, c in PhysicsConstants.GENERATION.items():
            if c == dm_elem: allies.append(m)
            
        allies_energy = sum(final_waves[e].amplitude for e in allies if e in final_waves)
        total_energy = sum(final_waves[e].amplitude for e in final_waves)
        
        order_param = PhaseTransitionTheory.calculate_order_parameter(allies_energy, total_energy)
        
        if resonance.is_follow:
            order_param = -0.95
            label = "Extreme Weak (Follow)"
        else:
            label = PhaseTransitionTheory.map_to_label(order_param)
            
        if resonance.mode == "BEATING":
            label += " (Fake)"

        # 7. Integrated Unified Dynamics [PH29-31]
        from .engines.unified_dynamics import UnifiedDynamics
        unified_metrics = UnifiedDynamics.run_analysis(final_waves, interactions, day_master)

        # 8. Pattern Integration [PH17-PH28 Injection]
        # Inject global patterns into the interaction list for UI visibility
        if resonance.is_follow:
            interactions.append({
                "id": "PH17-20", "type": "CONG", "name": "Pattern: Follow (从旺/从强)",
                "target_element": dm_elem, "q": 2.5, "phi": 0.0, "lock": True,
                "priority": -1, "branches": set()
            })
            
        if resonance.mode == "BEATING":
            interactions.append({
                "id": "PH19", "type": "CONG", "name": "Pattern: Fake Follow (假从/拍频)",
                "target_element": dm_elem, "q": 1.2, "phi": 0.5, "lock": False,
                "priority": -0.5, "branches": set()
            })
            
        if is_void:
            interactions.append({
                "id": "PH27", "type": "VOID", "name": "Pattern: Void Energy Sink (空亡)",
                "target_element": "Gravity", "q": 0.45, "phi": 0.0, "lock": False,
                "priority": 10, "branches": set(voids)
            })

        # --- Phase 12-Wealth: Tomb/Treasury Logic ---
        if annual_pillar and len(annual_pillar) > 1:
            y_branch = annual_pillar[1]
            tomb_map = {'辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
            all_branches = [p[1] for p in pillars if len(p) > 1]
            for tb in tomb_map:
                if tb in all_branches and tomb_map[tb] == y_branch:
                    # Impulse Ratio (I/R) simulation
                    # Resistance R is higher if allies are strong
                    resistance = 0.5 + (allies_energy / total_energy) if total_energy > 0 else 1.0
                    impulse = 1.0 # Standard Annual Impulse
                    i_r_ratio = impulse / resistance
                    
                    if 0.8 < i_r_ratio < 1.5:
                         interactions.append({
                             "id": "TOMB_OPEN", "type": "TREASURY", "name": f"Treasury Opened ({tb} by {y_branch})",
                             "target_element": BaziParticleNexus.BRANCHES[tb][0], "q": 2.2, "phi": 0.0, "lock": False,
                             "priority": -4, "branches": {tb, y_branch}, "i_r": i_r_ratio
                         })
                    elif i_r_ratio >= 1.5:
                         interactions.append({
                             "id": "TOMB_CRASH", "type": "OPPOSE", "name": f"Treasury Collapsed ({tb} by {y_branch})",
                             "target_element": "Chaos", "q": 0.1, "phi": np.pi, "lock": False,
                             "priority": -5, "branches": {tb, y_branch}, "i_r": i_r_ratio
                         })

        if sum(1 for i in interactions if i['type'] == 'CLASH') >= 2:
            interactions.append({
                "id": "PH25-26", "type": "OPPOSE", "name": "Pattern: Structural Collapse (多重冲撞)",
                "target_element": "Structure", "q": 0.1, "phi": np.pi, "lock": False,
                "priority": -2, "branches": set()
            })
            
        if resonance.mode == "ANNIHILATION":
            interactions.append({
                "id": "PH28_CORE", "type": "OPPOSE", "name": "Pattern: Annihilation State (湮灭模式)",
                "target_element": "System", "q": 0.0, "phi": np.pi, "lock": False,
                "priority": -3, "branches": set()
            })

        # [NEW] 8b. Structural Stress (Penalty/Harm) - Phase 32
        # Extract branches from all pillars for stress analysis
        # Pillars are strings like "甲子"
        all_branches = [p[1] for p in all_pillars if len(p) >= 2]
        
        # [PHASE 33] Add Injected Particles to Structural Matrix
        # Injections can be stems (甲) or branches (子)
        valid_branches = BaziParticleNexus.BRANCHES.keys()
        if injections:
            for p in injections:
                 if p in valid_branches:
                      all_branches.append(p)
                      print(f"DEBUG: Injected Branch {p} into Lattice")
        
        # Determine Month Branch for Bond Energy Context
        # Standard: Month is index 1
        month_branch_s = all_pillars[1][1] if len(all_pillars) > 1 and len(all_pillars[1]) > 1 else '寅'
        
        stress_engine = StructuralStressEngine(resonance_context=resonance, day_master=day_master)
        sys_stress = stress_engine.calculate_micro_lattice_defects(all_branches, month_branch=month_branch_s)
        
        # [PHASE B] Apply Star SNR Boost to IC
        sys_stress['IC'] = round(sys_stress['IC'] / star_mods['snr_boost'], 4)
        
        # Risk Flags
        struct_risk = "STABLE"
        sig_integrity = "OPTIMAL"

        if sys_stress['SAI'] > 0.4:
             struct_risk = "HIGH_STRESS"
             # Add interaction for visualization if high stress
             interactions.append({
                "id": "PH_SHEAR", "type": "PENALTY", "name": f"Shear Stress Alert (SAI={sys_stress['SAI']})",
                "priority": 0, "branches": set() 
             })
        if sys_stress['IC'] > 0.5:
              sig_integrity = "COMPROMISED"
              interactions.append({
                "id": "PH_JITTER", "type": "HARM", "name": f"Phase Jitter Alert (IC={sys_stress['IC']})",
                "priority": 0.5, "branches": set() 
             })

        # [NEW] 8c. Wealth Fluid Dynamics (Phase 35)
        wealth_engine = WealthFluidEngine(dm_elem)
        wealth_flow = wealth_engine.analyze_flow(final_waves)

        # [NEW] 8d. Relationship Gravity Dynamics (Phase 36)
        # Default to Male if gender not specified
        relationship_engine = RelationshipGravityEngine(day_master, gender="男")
        relationship_gravity = relationship_engine.analyze_relationship(final_waves, pillars)

        # [NEW] 8e. Causal Entanglement & Emergence (Phase C)
        causal_engine = CausalEntanglementEngine()
        emergence_data = causal_engine.analyze_emergence(interactions, all_branches)
        
        # [PHASE B] Apply Tian Yi Entropy Damping
        emergence_data['causal_entropy'] = round(emergence_data['causal_entropy'] * star_mods['entropy_damping'], 4)

        # Re-sort to ensure priority patterns appear first
        interactions.sort(key=lambda x: x['priority'])

        # 9. Intelligence Layer (Remedy & Deconstruction)
        remedy = None
        if resonance.sync_state < 0.9:
             remedy = QuantumRemedy.find_optimal_remedy(dm_wave, field_list, prev_sync=prev_sync, unified_metrics=unified_metrics, day_master=day_master)
             
        breakdown = Deconstructor.simulate_breakdown(dm_wave, field_list, resonance.sync_state)

        return {
            "verdict": {
                "label": label,
                "order_parameter": order_param,
                "score": (allies_energy / total_energy * 100) if total_energy > 0 else 0,
                "structural_risk": struct_risk,
                "signal_integrity": sig_integrity
            },
            "resonance": resonance,
            "waves": final_waves,
            "interactions": interactions,
            "unified_metrics": unified_metrics,
            "interactions": interactions,
            "unified_metrics": unified_metrics,
            "structural_stress": sys_stress,
            "wealth_fluid": wealth_flow,
            "relationship_gravity": relationship_gravity,
            "remedy": remedy,
            "breakdown": breakdown,
            "emergence": emergence_data,
            "symbolic_stars": star_stats,
            "logic_stack": {
                "active_rules": [i['id'] for i in interactions if i.get('id')],
                "manifest_version": LogicRegistry().version
            },
            "metadata": {
                "engine": "Quantum Trinity V2.2 (Integrated)",
                "brittleness": resonance.brittleness,
                "void_active": is_void,
                "star_modifiers": star_mods
            }
        }
