import numpy as np
import math
from typing import Dict, List, Optional, Any, Union
from .math_engine import ProbValue, expit
from .wave_mechanics import WaveState, InterferenceSolver, ImpedanceModel

class FluxEngine:
    """
    Quantum Trinity: Flux Engine (V14.0)
    =====================================
    Advanced energy flow dynamics using Complex Impedance and Wave Interference.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        from .physics_engine import ParticleDefinitions
        self.gen_cycle = ParticleDefinitions.GENERATION_CYCLE
        self.con_cycle = ParticleDefinitions.CONTROL_CYCLE
        
        # V14.2 Configurable Physics Parameters
        # Golden Parameters from AutoTuner (2025-12-20)
        physics_cfg = self.config.get('physics', {})
        self.recoil_factor = physics_cfg.get('recoil_factor', 0.9) # Optimal: 0.9
        self.coherence_boost = physics_cfg.get('coherence_boost', 1.0) # Optimal: 1.0
        self.shielding_factor = physics_cfg.get('shielding_factor', 10.0) # Default 10.0
        self.entropy_guard = physics_cfg.get('entropy_guard', 0.98) # Default 0.98
    def simulate_wave_flow(self, initial_waves: Dict[str, WaveState], 
                           interactions: List[Dict[str, Any]],
                           month_branch: Optional[str] = None,
                           steps: int = 1) -> Dict[str, WaveState]:
        """
        Simulate energy flow using Complex Impedance and Phase Coherence.
        Incorporates Seasonal Medium Field (Wang/Si).
        """
        from .physics_engine import PhysicsEngine, ParticleDefinitions
        current = initial_waves.copy()
        
        # STRUCTURAL IMPEDANCE: Identify elements present in the pillars
        # Vacuum elements (1e-6) should act as insulators (High Loss)
        presence = {e: (1.0 if w.amplitude > 0.01 else 0.01) for e, w in initial_waves.items()}
        
        for _ in range(steps):
            # Apply interactions once to the current baseline
            # 'rule_applied' is the state AFTER interference but BEFORE transmission
            rule_applied = {k: v for k, v in current.items()}
            
            # 'rule_applied' is the state AFTER interference but BEFORE transmission
            rule_applied = {k: v for k, v in current.items()}
            
            # Determine Structural Locks
            lock_mask = {} # Elements that are locked by high-priority structures
            if _ == 0: 
                for rule in interactions:
                    target = rule.get('target_element')
                    if not target or target not in current: continue
                    
                    q = rule.get('resonance_q', 1.0)
                    phi = rule.get('phase_shift', 0.0)
                    is_lock = rule.get('lock', False)
                    
                    if is_lock:
                        lock_mask[target] = 1.0 # Fully locked
                    
                    # Accumulate effect by reading/writing to rule_applied
                    w = rule_applied[target]
                    shifted_w = InterferenceSolver.apply_phase_shift(w, phi)
                    rule_applied[target] = WaveState(shifted_w.amplitude * q, shifted_w.phase)
            
            # Persist locks across steps (Simplified: recalculate or carry over? 
            # For now, we only lock based on initial static analysis, which is fine)
            
            next_state = {k: v for k, v in rule_applied.items()}
            
            # --- 2. Transmission Rheology (Flux) ---
            # KEY FIX: Use 'rule_applied' frozen snapshot for inputs to prevent cascade
            
            for mother, child in self.gen_cycle.items():
                if mother not in rule_applied or child not in rule_applied: continue
                
                m_wave = rule_applied[mother]
                c_wave = rule_applied[child]
                
                # Impedance factor based on presence (Structural Barrier)
                # LOCK SHIELD: If child is locked, it resists external flux change (High Z)
                z_lock_factor = 1.0 + (lock_mask.get(child, 0.0) * self.shielding_factor)
                z_structural = (10.0 / presence[child]) * z_lock_factor
                
                # PHASE ALIGNMENT: To match child's intrinsic phase (+1.25 rad start shift)
                rho = 1.5 * z_structural * (1.0 + (c_wave.amplitude / max(m_wave.amplitude, 0.01))**2)
                
                # V14.8 Saturation Flow Control (Scorched Earth Logic)
                # If Mother is extremely strong (>8.0), the transmission channel saturates/scorches.
                # Impedance increases drastically to block flow.
                if m_wave.amplitude > 8.0:
                    excess = m_wave.amplitude - 8.0
                    # Impedance Multiplier: 1.0 -> 5.0+
                    impedance_boost = 1.0 + 0.6 * excess
                    rho *= impedance_boost
                
                z_transmission = rho * np.exp(-1.2566j)
                
                i_complex = m_wave.to_complex() / z_transmission
                i_wave = WaveState.from_complex(i_complex)
                
                # Phase Matching Filter
                target_phi = ParticleDefinitions.ELEMENT_PHASES.get(child, 0.0)
                phi_diff = abs(i_wave.phase - target_phi) % (2 * np.pi)
                if phi_diff > np.pi: phi_diff = 2 * np.pi - phi_diff
                match_factor = np.cos(phi_diff / 2.0) ** 2
                
                # Update next_state buffer, reading from frozen rule_applied
                # V14.2 Bose-Einstein Coherence: Boost coupling if phases align perfectly
                coherence = 1.0
                if match_factor > 0.9: # Near perfect alignment
                    coherence = self.coherence_boost
                
                next_state[child] = InterferenceSolver.solve_interference(next_state[child], i_wave, coupling=0.6 * match_factor * coherence)
                
                drain_factor = 0.02 * presence[child] + (0.05 / (rho / 1.5))
                # For mother, we read current next_state update but base drain on frozen m_wave amplitude logic
                cur_m_amp = next_state[mother].amplitude
                next_state[mother] = WaveState(cur_m_amp * (1.0 - drain_factor), next_state[mother].phase)
                
            for attacker, defender in self.con_cycle.items():
                if attacker not in rule_applied or defender not in rule_applied: continue
                
                a_wave = rule_applied[attacker]
                d_wave = rule_applied[defender]
                
                a_state = "Xiu"
                d_state = "Xiu"
                if month_branch:
                    a_state = PhysicsEngine.get_seasonal_state(attacker, month_branch)
                    d_state = PhysicsEngine.get_seasonal_state(defender, month_branch)
                
                damage = PhysicsEngine.calculate_control_damage(
                    a_wave.amplitude, d_wave.amplitude, a_state, d_state
                )
                
                # Structural Shielding and Logic
                # V14.5 Non-linear Shielding (Square Law)
                # p_factor: >1 means Attacker has structural advantage (Vacuum Defender)
                # p_factor: <1 means Defender has structural shield (Vacuum Attacker)
                # Square law exaggerates the advantage of the dominant structure.
                raw_p_factor = presence[attacker] / presence[defender]
                p_factor = raw_p_factor ** 2.0
                
                # Apply shielding to raw damage
                effective_damage = damage * p_factor
                
                # CAP: Cannot destroy more energy than exists (prevent phase inversion / phantom energy)
                final_damage = min(effective_damage, d_wave.amplitude)
                
                # DESTRUCTIVE PHASE LOCKING
                # We inject an 'Anti-Wave' exactly tuned to cancel the target energy
                target_phi = ParticleDefinitions.ELEMENT_PHASES.get(defender, 0.0)
                attack_phi = (target_phi + np.pi) % (2 * np.pi)
                
                # Create Cancellation Vector
                anti_wave = WaveState(final_damage, attack_phi)
                
                # Zero-Phase-Slip Interference (Perfect Destructive Injection)
                next_state[defender] = InterferenceSolver.solve_interference(next_state[defender], anti_wave, coupling=1.0)
                
                # V14.2 & V14.4 Dynamic Recoil Logic (Corrected)
                # Recoil should be proportional to Energy Spent / Attacker Mass
                # Energy Spent = Damage Dealt + Overhead
                
                # Base consumption for the act of control
                overhead = 0.05 * a_wave.amplitude
                
                # Physical Recoil (Newtonian)
                # If Defender Shield is high (p_factor low), more effort needed?
                # Actually, damage is already scaled by p_factor in the 'coupling'.
                # Let's say Attacker loses what it dealt, plus overhead.
                
                # If impedance mismatch (Defender >> Attacker), simple formulas break.
                impedance_ratio = d_wave.amplitude / max(a_wave.amplitude, 0.01)
                
                if impedance_ratio > 2.0: 
                    # V14.4 Inverse Control (Full Reflection)
                    mismatch_penalty = min(1.0, (impedance_ratio - 2.0) * 0.5)
                    scaled_recoil = max(0.05, mismatch_penalty)
                else:
                    # Normal Control
                    # Energy lost = Damage caused (Action=Reaction) * Factor
                    energy_loss = damage * self.recoil_factor + overhead
                    scaled_recoil = energy_loss / max(a_wave.amplitude, 0.01)
                
                # Clamp recoil to prevent negative energy
                scaled_recoil = min(scaled_recoil, 1.0)
                
                cur_a_amp = next_state[attacker].amplitude
                next_state[attacker] = WaveState(max(0.0, cur_a_amp * (1.0 - scaled_recoil)), next_state[attacker].phase)
                
            # 3. GLOBAL DAMPING (Entropy Guard)

            # 3. GLOBAL DAMPING (Entropy Guard)
            for e in next_state:
                next_state[e] = WaveState(next_state[e].amplitude * self.entropy_guard, next_state[e].phase)

            current = next_state
            
        return current
