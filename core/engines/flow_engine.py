from collections import defaultdict
import numpy as np

class FlowEngine:
    """
    V7.4 Energy Flow Dynamics Engine (Resonance & Flow)
    Implements the Damping Protocol (Impedance, Viscosity, Entropy).
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        # Elements Cycle
        self.GENERATION = {'wood': 'fire', 'fire': 'earth', 'earth': 'metal', 'metal': 'water', 'water': 'wood'}
        self.CONTROL = {'wood': 'earth', 'earth': 'water', 'water': 'fire', 'fire': 'metal', 'metal': 'wood'}
        
    def update_config(self, new_config):
        self.config = new_config

    def simulate_flow(self, initial_energies: dict, dm_elem: str = None) -> dict:
        """
        [V7.4 Core] Constrained Flow Simulation (The Damping Protocol).
        Applies Physics of Impedance and Viscosity to prevent 'Over-Drain' and 'Over-Fill'.
        
        :param initial_energies: Raw energy dict (Wood: 100, Fire: 50...)
        :param dm_elem: Day Master Element (e.g., 'wood') - CRITICAL for role-based physics
        :return: Final stabilized energy
        """
        import copy
        
        # 0. Load Config
        fc = self.config.get('flow', {})
        
        # New Params
        res_imp = fc.get('resourceImpedance', {'base': 0.3, 'weaknessPenalty': 0.5})
        out_vis = fc.get('outputViscosity', {'maxDrainRate': 0.6, 'drainFriction': 0.2})
        entropy = fc.get('globalEntropy', 0.05)
        
        # Legacy Fallbacks (if new params missing)
        eff = fc.get('generationEfficiency', 0.7)
        drain = fc.get('generationDrain', 0.3)
        
        # Constants
        MAX_STEPS = 5     
        
        # Initialize State
        current = copy.deepcopy(initial_energies) # Working copy
        # Ensure all elements exist in dict
        for e in self.GENERATION.keys():
            if e not in current: current[e] = 0.0

        if not dm_elem:
            # Fallback for undefined DM (should rarely happen in core flow)
            pass

        # Roles helper
        def get_role(elem):
            if not dm_elem: return 'unknown'
            if elem == dm_elem: return 'self'
            if self.GENERATION[dm_elem] == elem: return 'output'
            if self.GENERATION[elem] == dm_elem: return 'resource'
            if self.CONTROL[dm_elem] == elem: return 'wealth'
            if self.CONTROL[elem] == dm_elem: return 'officer'
            return 'other'

        # Iteration
        for step in range(MAX_STEPS):
            next_state = current.copy()
            
            # --- 1. Generation Phase (Impedance & Viscosity Applied) ---
            for mother, child in self.GENERATION.items():
                mother_e = current.get(mother, 0.0)
                if mother_e <= 0.001: continue
                
                # Identify Role of this Channel
                mother_role = get_role(mother)
                child_role = get_role(child)
                
                # A. Resource -> Self (Impedance Logic)
                if child_role == 'self':
                    # Calculate Impedance
                    k_imp = res_imp.get('base', 0.3)
                    
                    # Weakness Penalty: If Self is Weak, Resistance Increases!
                    # E.g., Self < 30 (Arbitrary Unit), Imp Increases
                    if current[child] < 30.0:
                        k_imp += res_imp.get('weaknessPenalty', 0.5)
                        
                    # Clamp Impedance [0, 1.0]
                    k_imp = min(0.95, k_imp)
                    
                    # Transfer Amount
                    transfer = mother_e * eff * (1.0 - k_imp)
                    # Mother still loses Energy usually
                    loss = mother_e * drain 
                    
                    next_state[child] += transfer
                    next_state[mother] -= loss
                    
                # B. Self -> Output (Viscosity Logic)
                elif mother_role == 'self':
                    # Calculate Viscosity (Drain Protection)
                    max_drain_rate = out_vis.get('maxDrainRate', 0.6)
                    friction = out_vis.get('drainFriction', 0.2)
                    
                    # Theoretical Drain (Linear)
                    theoretical_loss = mother_e * drain
                    theoretical_gain = mother_e * eff
                    
                    # Apply Clamp
                    # Cannot lose more than X% of current Self energy
                    allowed_loss = mother_e * max_drain_rate
                    
                    actual_loss = min(theoretical_loss, allowed_loss)
                    
                    # Friction reduces Gain (Heat Loss)
                    actual_gain = actual_loss * (eff / drain) * (1.0 - friction)
                    
                    next_state[mother] -= actual_loss
                    next_state[child] += actual_gain
                    
                # C. Generic Generation (Other relations)
                else:
                    transfer = mother_e * eff 
                    loss = mother_e * drain
                    next_state[child] += transfer
                    next_state[mother] -= loss

            # --- 2. Control Phase (Simplified) ---
            # Attack reduces Defender. Attacker loses Exhaustion.
            for attacker, defender in self.CONTROL.items():
                att_e = current.get(attacker, 0)
                def_e = current.get(defender, 0)
                if att_e <= 0.001 or def_e <= 0.001: continue
                
                # Config
                impact = fc.get('controlImpact', 0.5)
                exhaust = fc.get('controlExhaust', 0.2)
                
                damage = att_e * impact
                # Cap damage to defender's energy?
                if damage > def_e: damage = def_e
                
                cost = damage * exhaust
                
                next_state[defender] -= damage
                next_state[attacker] -= cost
            
            # --- 3. Global Entropy (Cooling) ---
            k_entropy = entropy # 0.05
            for e in next_state:
                if next_state[e] > 0:
                    next_state[e] *= (1.0 - k_entropy)
                    # Floor clamp
                    if next_state[e] < 0.001: next_state[e] = 0.0
            
            # Update Current
            current = next_state
        
        return current
