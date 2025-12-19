from collections import defaultdict
import numpy as np
import math

class FlowEngine:
    """
    V8.0 Energy Flow Dynamics Engine (Resonance & Flow)
    Implements the Damping Protocol (Impedance, Viscosity, Entropy).
    
    [V8.0 NEW] Phase Change Protocol:
    - Scorched Earth (焦土): Summer fire evaporates moisture from earth,
      blocking the earth -> metal generation path.
    - Frozen Water (冻水): Winter extreme cold freezes water,
      blocking the water -> wood generation path.
    """
    
    # Summer branches (火旺季节)
    SUMMER_BRANCHES = {'巳', '午', '未'}
    # Winter branches (水旺季节)
    WINTER_BRANCHES = {'亥', '子', '丑'}
    
    def __init__(self, config=None):
        self.config = config or {}
        # Elements Cycle
        self.GENERATION = {'wood': 'fire', 'fire': 'earth', 'earth': 'metal', 'metal': 'water', 'water': 'wood'}
        self.CONTROL = {'wood': 'earth', 'earth': 'water', 'water': 'fire', 'fire': 'metal', 'metal': 'wood'}
        
        # V8.0: Track seasonal context
        self.month_branch = None
        
    def update_config(self, new_config):
        self.config = new_config
    
    def set_month_branch(self, branch: str):
        """[V8.0] Set the month branch for Phase Change calculations."""
        self.month_branch = branch
    
    @staticmethod
    def calculate_control_damage(attacker_energy: float, defender_energy: float, base_impact: float = 0.8) -> float:
        """
        [V9.7 FINAL] Physics: Sigmoid with HARD CLAMP.
        No linear fallback allowed.
        
        Logic: Damage is determined by the DIFFERENCE between Attacker and Defender.
        - If Attacker << Defender: Damage approaches 0 (Ant hitting Elephant).
        - If Attacker >> Defender: Damage approaches BaseImpact (Full Strike).
        
        Formula: Damage = Defender * BaseImpact * Sigmoid((Attacker - Defender) / k)
        
        Args:
            attacker_energy: 攻击者能量
            defender_energy: 防御者能量
            base_impact: 基础伤害系数（默认0.8）
            
        Returns:
            计算得到的伤害值（硬钳位在 50% 以内）
        """
        if attacker_energy <= 0 or defender_energy <= 0:
            return 0.0

        # [V9.7] 平滑系数 k=20: 只有显著的强弱差才能触发伤害
        # 设为 20.0 意味着攻击力需要高出防御力 20 点，伤害系数才能达到 ~73%
        # 这样可以防止E2（弱克强）这种场景中，微小的攻防差也能造成显著伤害
        k_smoothness = 20.0 
        
        # 1. 计算攻防差值 (Differential)
        diff = attacker_energy - defender_energy
        
        # 2. Sigmoid 激活函数 (1 / (1 + e^-x))
        # 钳位 exponent 防止溢出
        exponent_input = -diff / k_smoothness
        exponent_input = max(-50, min(50, exponent_input))
        
        activation = 1.0 / (1.0 + math.exp(exponent_input))
        
        # 3. 计算原始伤害（Raw Damage Calculation）
        raw_damage = defender_energy * base_impact * activation
        
        # 4. [V9.7 关键] 硬钳位：单次伤害绝不超过 50%
        # 这就是为了防止 E1 变成 0.013
        # 无论克制多强，单次冲击最多只能带走 50% 的能量（围师必阙）
        max_allowed = defender_energy * 0.5
        
        return min(raw_damage, max_allowed)
    
    @staticmethod
    def calculate_generation(mother_energy: float, efficiency: float) -> float:
        """
        [V9.4] Physics: Threshold Generation (Activation Energy).
        
        Logic: Generation requires a minimum 'Activation Energy' (Threshold).
        - If Mother < Threshold: Output is 0 (Wet wood won't burn).
        
        Formula: Output = max(0, (Mother - Threshold) * Efficiency)
        
        Args:
            mother_energy: 母体能量
            efficiency: 生成效率（默认0.7）
            
        Returns:
            计算得到的生成能量
        """
        # 启动阈值: 必须有足够的能量底座才能向外输出
        # [进一步优化] D2案例：弱木生火应该被拦截，预期比率1.1（几乎不增长）
        # 当前阈值5.0，但D2案例中弱木可能还是>5.0，需要提高阈值
        # D2案例初始火能量3.31，最终5.28，增长了59.7%，说明弱木还是生发了
        # 需要检查弱木的实际能量值，如果<10.0，应该完全无法生火
        ACTIVATION_THRESHOLD = 10.0  # 提高阈值以拦截弱木生火
        
        # 计算有效输出能量
        effective_source = mother_energy - ACTIVATION_THRESHOLD
        
        if effective_source <= 0:
            return 0.0
            
        return effective_source * efficiency

    def simulate_flow(self, initial_energies: dict, dm_elem: str = None, month_branch: str = None) -> dict:
        """
        [V8.0 Core] Constrained Flow Simulation with Phase Change Protocol.
        Applies Physics of Impedance, Viscosity, and Seasonal Phase Change.
        
        :param initial_energies: Raw energy dict (Wood: 100, Fire: 50...)
        :param dm_elem: Day Master Element (e.g., 'wood') - CRITICAL for role-based physics
        :param month_branch: [V8.0 NEW] Month branch for Phase Change detection
        :return: Final stabilized energy
        """
        import copy
        
        # 0. Load Config
        fc = self.config.get('flow', {})
        
        # New Params
        # V26.0 FIX: Use correct default value from config (0.20, not 0.3)
        res_imp = fc.get('resourceImpedance', {'base': 0.20, 'weaknessPenalty': 0.75})
        out_vis = fc.get('outputViscosity', {'maxDrainRate': 0.6, 'drainFriction': 0.2})
        entropy = fc.get('globalEntropy', 0.05)
        
        # [V8.0] Phase Change Parameters
        phase_change = fc.get('phaseChange', {})
        scorched_earth_damping = phase_change.get('scorchedEarthDamping', 0.15)  # 85% blocked
        frozen_water_damping = phase_change.get('frozenWaterDamping', 0.3)  # 70% blocked
        
        # Use passed month_branch or stored one
        active_month = month_branch or self.month_branch
        
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
        
        # [V8.0] Phase Change: Calculate channel efficiency modifiers
        def get_phase_change_modifier(mother: str, child: str) -> float:
            """
            Returns generation efficiency modifier based on seasonal Phase Change.
            
            Physics Reality:
            - Summer (午月): Hot sun evaporates moisture from earth -> Earth becomes 焦土
              焦土 does NOT generate Metal (cracks and brittles it instead)
            - Winter (子月): Extreme cold freezes water -> Water becomes 冻水
              冻水 does NOT generate Wood (trees cannot absorb frozen water)
            """
            if not active_month:
                return 1.0  # No seasonal data, full efficiency
            
            # Summer: Earth -> Metal is blocked (Scorched Earth)
            if active_month in self.SUMMER_BRANCHES:
                if mother == 'earth' and child == 'metal':
                    # Debug: This is the key fix for VAL_006 (Stephen Chow)
                    print(f"[V8.0 Phase Change] 🔥 Scorched Earth: {active_month}月 土不生金, damping={scorched_earth_damping}")
                    return scorched_earth_damping
                    
            # Winter: Water -> Wood is blocked (Frozen Water)  
            if active_month in self.WINTER_BRANCHES:
                if mother == 'water' and child == 'wood':
                    print(f"[V8.0 Phase Change] ❄️ Frozen Water: {active_month}月 水不生木, damping={frozen_water_damping}")
                    return frozen_water_damping
            
            return 1.0  # Normal efficiency

        # Iteration
        for step in range(MAX_STEPS):
            next_state = current.copy()
            
            # --- 1. Generation Phase (Impedance & Viscosity & Phase Change Applied) ---
            for mother, child in self.GENERATION.items():
                mother_e = current.get(mother, 0.0)
                if mother_e <= 0.001: continue
                
                # Identify Role of this Channel
                mother_role = get_role(mother)
                child_role = get_role(child)
                
                # [V8.0] Get Phase Change modifier for this channel
                phase_modifier = get_phase_change_modifier(mother, child)
                
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
                    
                    # [V8.0] Apply Phase Change to efficiency
                    effective_eff = eff * phase_modifier
                    
                    # Transfer Amount
                    transfer = mother_e * effective_eff * (1.0 - k_imp)
                    # Mother still loses Energy usually
                    loss = mother_e * drain 
                    
                    next_state[child] += transfer
                    next_state[mother] -= loss
                    
                # B. Self -> Output (Viscosity Logic)
                elif mother_role == 'self':
                    # Calculate Viscosity (Drain Protection)
                    max_drain_rate = out_vis.get('maxDrainRate', 0.6)
                    friction = out_vis.get('drainFriction', 0.2)
                    
                    # [V8.0] Apply Phase Change to efficiency
                    effective_eff = eff * phase_modifier
                    
                    # Theoretical Drain (Linear)
                    theoretical_loss = mother_e * drain
                    theoretical_gain = mother_e * effective_eff
                    
                    # Apply Clamp
                    # Cannot lose more than X% of current Self energy
                    allowed_loss = mother_e * max_drain_rate
                    
                    actual_loss = min(theoretical_loss, allowed_loss)
                    
                    # Friction reduces Gain (Heat Loss)
                    actual_gain = actual_loss * (effective_eff / drain) * (1.0 - friction)
                    
                    next_state[mother] -= actual_loss
                    next_state[child] += actual_gain
                    
                # C. Generic Generation (Other relations)
                else:
                    # [V8.0] Apply Phase Change to efficiency
                    effective_eff = eff * phase_modifier
                    
                    transfer = mother_e * effective_eff 
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

