import numpy as np
from typing import Dict, List, Optional, Any, Union
from .math_engine import ProbValue
from .physics_engine import PhysicsEngine, ParticleDefinitions
from .flux_engine import FluxEngine
from .wave_mechanics import WaveState, ModulationEngine, PhaseTransitionEngine, InterferenceSolver
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
                     year_pillar: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a full V14.0 analysis using Wave Modulation and Phase Transition.
        """
        # 1. Initialize Ground State (Wave Sources)
        initial_waves = self._initialize_waves(bazi, day_master, month_branch)
        
        # 2. Match Geometric Interactions (Phase 2 Interference)
        interactions = self.logic.match_logic(bazi, day_master, initial_waves)
        
        # 3. Simulate Flux (Phase 3 Rheology)
        final_waves = self.flux.simulate_wave_flow(
            initial_waves=initial_waves,
            interactions=interactions,
            month_branch=month_branch,
            steps=3 # Allow resonance to stabilize
        )
        
        # 4. Decision Layer (Phase 4 Phase Transition)
        verdict = self._collapse_verdict(final_waves, day_master)
        
        return {
            'waves': final_waves,
            'verdict': verdict,
            'matched_rules': interactions,
            'engine': 'Quantum Trinity V14.0 (Precision Revolution)'
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
                w = ParticleDefinitions.PILLAR_WEIGHTS.get(['year', 'month', 'day', 'hour'][p_idx], 1.0)
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
            
            w_pillar = ParticleDefinitions.PILLAR_WEIGHTS.get(['year', 'month', 'day', 'hour'][p_idx], 1.0)
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
        
    def _collapse_verdict(self, waves: Dict[str, WaveState], day_master: str) -> Dict[str, Any]:
        """
        Landau Phase Transition Judgment.
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
        # If Day Master is annihilated (Amp < 0.1), it cannot be Strong, regardless of Resource
        dm_amp = waves.get(dm_elem, WaveState(0,0)).amplitude
        if dm_amp < 0.1 and order_param > 0:
            # Force collapse to Weak (Flip polarity)
            order_param = -0.5 # Weak
            
        label = PhaseTransitionEngine.collapse_to_label(order_param)
        
        return {
            'label': label,
            'order_parameter': order_param,
            'score': (allies_energy / total_energy * 100) if total_energy > 0 else 0
        }
