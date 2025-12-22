import numpy as np
from typing import Dict, List, Optional, Any, Union
from .math_engine import ProbValue
from .physics_engine import PhysicsEngine, ParticleDefinitions
from .flux_engine import FluxEngine
from .wave_mechanics import WaveState, ModulationEngine, PhaseTransitionEngine, InterferenceSolver
from .structural_dynamics import StructuralDynamics
from .entanglement_engine import EntanglementEngine
from .pattern_deconstructor import PatternDeconstructor
from .structural_reorganizer import StructuralReorganizer
from ..registry.logic_matrix import LogicMatrix

class QuantumEngine:
    """
    Quantum Trinity: Quantum Engine (V14.0)
    =======================================
    Orchestrates the Precision Revolution: High-dimensional non-linear physics.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.physics = PhysicsEngine()
        self.flux = FluxEngine(config=self.config)
        self.logic = LogicMatrix()
        
    def analyze_bazi(self, bazi: List[str], day_master: str, 
                     month_branch: str,
                     luck_pillar: Optional[str] = None,
                     year_pillar: Optional[str] = None,
                     t: float = 0.0,
                     injections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform a full V14.0 analysis using Wave Modulation and Phase Transition.
        """
        # 1. Initialize Waves: Hierarchy of Influence
        # Natal (4 Pillars)
        natal_bazi = bazi[:4] if len(bazi) >= 4 else bazi
        luck_p = bazi[4] if len(bazi) >= 5 else None
        annual_p = bazi[5] if len(bazi) >= 6 else None
        
        # Natal Base Field
        field_natal = natal_bazi.copy()
        if len(field_natal) > 2:
            dm_pillar = field_natal[2]
            field_natal[2] = dm_pillar[1] if len(dm_pillar) > 1 else "" 
        
        field_waves_init = self._initialize_waves(field_natal, day_master, month_branch)
        
        # Apply Luck as a BACKGROUND FIELD (Modulation)
        if luck_p:
            luck_waves = self._initialize_waves([luck_p], day_master, month_branch)
            for k in field_waves_init:
                # Luck modulates the field (1.2x theoretical weight as a 'Great Field')
                field_waves_init[k] = InterferenceSolver.solve_interference(field_waves_init[k], luck_waves[k], coupling=1.2)
        
        # DM particle is just the Day Stem
        dm_only_bazi = ["", "", day_master, ""]
        dm_waves_init = self._initialize_waves(dm_only_bazi, day_master, month_branch)
        dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(day_master, {}).get('element', 'Earth')
        dm_wave_init = dm_waves_init.get(dm_elem, WaveState(1e-6, 0))
        
        # Initial composite field for logic matching
        composite_initial = {e: InterferenceSolver.solve_interference(field_waves_init[e], dm_waves_init[e]) for e in field_waves_init}

        # 2. Match Geometric Interactions (Phase 2 Interference)
        interactions = self.logic.match_logic(bazi, day_master, composite_initial)
        
        # 3. Simulate Flux (Phase 3 Rheology)
        # We simulate the flow of the entire system
        final_system_waves = self.flux.simulate_wave_flow(
            initial_waves=composite_initial,
            interactions=interactions,
            month_branch=month_branch,
            steps=3
        )
        
        # Separate DM element field from Environment
        dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(day_master, {}).get('element', 'Earth')
        field_wave_list = []
        for k, v in final_system_waves.items():
            if k == dm_elem:
                env_complex = v.to_complex() - dm_wave_init.to_complex()
                field_wave_list.append(WaveState.from_complex(env_complex))
            else:
                field_wave_list.append(v)

        # 4. Resonance Analysis (Phase 21 Unified Call)
        # Phase 23/24: Entanglement Remediation & Active Filtering
        if injections:
            for particle in injections:
                # 1. Subjective Remediation (Day Master Injection)
                dm_wave_init = EntanglementEngine.inject_particle(dm_wave_init, particle, coupling=0.3)
                # 2. Objective Remediation (Active Field Filtering)
                field_wave_list = EntanglementEngine.apply_active_filtering(field_wave_list, particle, coupling=0.3)

        res_config = self.config.get('resonance', {})
        resonance_state = StructuralDynamics.evaluate_system_resonance(dm_wave_init, field_wave_list, t=t, config=res_config)
        
        # 4.5 Phase 24: Auto-Remediation (If Crisis or Damping Detected)
        suggestion = None
        if resonance_state.resonance_report.vibration_mode in ["BEATING", "DAMPED"]:
            # Pass dm_wave_init (pre-manual injection)
            suggestion = EntanglementEngine.find_optimal_injection(
                dm_wave_init, field_wave_list, t=t, config=res_config
            )

        # 4.6 Phase 25/26: Pattern Deconstruction (Violent Disassembly)
        # Hierarchy: Natal Graph triggered by Annual Pillar
        trigger_nodes = []
        if annual_p:
            trigger_nodes = PatternDeconstructor.identify_energy_nodes([annual_p])
            for tn in trigger_nodes: tn['is_trigger'] = True

        natal_nodes = PatternDeconstructor.identify_energy_nodes(natal_bazi)
        
        breakdown_check = PatternDeconstructor.simulate_violent_disassembly(
            dm_wave_init, field_wave_list, 
            energy_nodes=natal_nodes,
            trigger_nodes=trigger_nodes, # New: Annual triggers the natal
            threshold=self.config.get('collapse_threshold', 25.0)
        )
        
        # 4.7 Phase 27: Structural Reorganization (Suppression)
        # Feed actual conflicts to finding suppression particles
        reorg_strategy = []
        if breakdown_check['status'] == "CRITICAL" and 'conflicts' in breakdown_check:
             reorg_strategy = StructuralReorganizer.find_suppression_particles(
                 breakdown_check['conflicts'], 
                 dm_wave_init
             )

        # 5. Decision Layer (Phase 4 Phase Transition)
        verdict = self._collapse_verdict(final_system_waves, day_master, resonance_state)
        
        return {
            'waves': final_system_waves,
            'verdict': verdict,
            'resonance_state': resonance_state,
            'matched_rules': interactions,
            'suggestion': suggestion,
            'snr': resonance_state.resonance_report.snr,
            'breakdown': breakdown_check,
            'reorg_strategy': reorg_strategy,
            'engine': 'Quantum Trinity V27.0 (Structural Reorganization)'
        }
        
    def _initialize_waves(self, bazi: List[str], day_master: str, month_branch: str) -> Dict[str, WaveState]:
        """
        Initialize waves with Vacuum Damping (Energy Localization).
        """
        phases = ParticleDefinitions.ELEMENT_PHASES
        # Use near-zero amplitude for vacuum state
        waves = {e: WaveState(1e-6, phases.get(e, 0.0)) for e in ["Wood", "Fire", "Earth", "Metal", "Water"]}
        
        for p_idx, pillar in enumerate(bazi):
            if not pillar: continue
            stem, branch = pillar[0], pillar[1] if len(pillar) > 1 else ''
            
            # Stem energy (Carrier Wave)
            stem_info = ParticleDefinitions.STEM_WAVEFORMS.get(stem)
            if stem_info:
                elem = stem_info['element']
                pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']
                p_name = pillar_names[p_idx] if p_idx < len(pillar_names) else 'unknown'
                w = ParticleDefinitions.PILLAR_WEIGHTS.get(p_name, 1.0)
                amp = ParticleDefinitions.BASE_SCORE * w
                
                # Use intrinsic phase for the element
                source_phase = phases.get(elem, 0.0)
                source_wave = WaveState(amplitude=amp, phase=source_phase)
                
            # Superimpose on existing field (Resonance check)
                waves[elem] = InterferenceSolver.solve_interference(waves[elem], source_wave, coupling=1.0)

            # Branch energy (Rooting) - V14.3 Normalized Energy Density
            hidden_stems = ParticleDefinitions.GENESIS_HIDDEN_MAP.get(branch, [])
            num_stems = len(hidden_stems)
            
            # Determine weights based on stem count (Architect's Formula)
            # Pure (1) -> 1.0
            # Dual (2) -> 0.7, 0.3
            # Trinity (3) -> 0.6, 0.3, 0.1
            weights = []
            if num_stems == 1:
                weights = [1.0]
            elif num_stems == 2:
                weights = [0.7, 0.3]
            elif num_stems >= 3:
                weights = [0.6, 0.3, 0.1]
            
            pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            p_name = pillar_names[p_idx] if p_idx < len(pillar_names) else 'unknown'
            w_pillar = ParticleDefinitions.PILLAR_WEIGHTS.get(p_name, 1.0)
            base_amp = ParticleDefinitions.BASE_SCORE * w_pillar * 1.5 # 1.5x for Earthly Branch
            
            for i, (stem_char, _) in enumerate(hidden_stems):
                if i >= len(weights): break
                
                stem_data = ParticleDefinitions.STEM_WAVEFORMS.get(stem_char)
                if not stem_data: continue
                
                elem = stem_data['element']
                weight = weights[i]
                
                # Energy injection with Normalized Density
                amp = base_amp * weight
                source_phase = phases.get(elem, 0.0)
                source_wave = WaveState(amplitude=amp, phase=source_phase)
                
                waves[elem] = InterferenceSolver.solve_interference(waves[elem], source_wave, coupling=1.0)

        return waves
        
    def _collapse_verdict(self, waves: Dict[str, WaveState], day_master: str, 
                          resonance: Optional[StructuralDynamics.SystemState] = None) -> Dict[str, Any]:
        """
        Landau Phase Transition Judgment with Resonance Correction.
        """
        dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(day_master, {}).get('element', 'Earth')
        
        # Identify Allies (Self + Resource)
        allies = [dm_elem]
        for m, c in ParticleDefinitions.GENERATION_CYCLE.items():
            if c == dm_elem:
                allies.append(m)
        
        allies_energy = sum(waves[e].amplitude for e in allies if e in waves)
        total_energy = sum(waves[e].amplitude for e in waves)
        
        # Calculate Phase Transition Order Parameter
        order_param = PhaseTransitionEngine.calculate_order_parameter(allies_energy, total_energy)
        
        # V14.6 DM Survival Guard
        dm_amp = waves.get(dm_elem, WaveState(0,0)).amplitude
        
        # V21.0 Resonance Correction: Handle "Follow" Pattern
        if resonance and resonance.is_follow_pattern:
            # Resonance Synchronization implies "Superconductive Follow"
            # It should be treated as "Extreme Weak" (Follow) but with high Coherence
            base_label = "Extreme Weak (Follow)"
            # Adjust order_param to the "Follow" region
            order_param = -0.95
        elif dm_amp < 0.1 and order_param > 0:
            # Force collapse to Weak (Flip polarity)
            order_param = -0.5 # Weak
            base_label = PhaseTransitionEngine.collapse_to_label(order_param)
        else:
            base_label = PhaseTransitionEngine.collapse_to_label(order_param)
            
        label = base_label
        if resonance and resonance.resonance_report.vibration_mode == "BEATING":
            label += " (Beating/Fake)"

        return {
            'label': label,
            'order_parameter': order_param,
            'score': (allies_energy / total_energy * 100) if total_energy > 0 else 0
        }
