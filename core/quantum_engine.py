import hashlib
import json
import os
from lunar_python import Solar, Lunar
from collections import Counter
from core.constants import GRAVE_TREASURY_CONFIG, HIDDEN_STEMS_MAP, EARTH_PUNISHMENT_SET
from core.interaction_service import InteractionService
from core.context import DestinyContext, create_context_from_v35_result
from core.bazi_profile import BaziProfile
from core.engines.luck_engine import LuckEngine
from core.engines.skull_engine import SkullEngine
from core.engines.treasury_engine import TreasuryEngine
from core.engines.harmony_engine import HarmonyEngine
from core.engines.flow_engine import FlowEngine

# === V6.0+ Parameterization: Import Algorithm Config ===
from core.config_rules import DEFAULT_CONFIG
# === V7.0 Architecture: Full Algo Schema ===
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

class QuantumEngine:
    """
    ⚠️ DEPRECATED - Use core.engine_v88.EngineV88 instead!
    
    Quantum Bazi V8.1 Physics Engine (Legacy)
    This class is kept for backward compatibility with tests and scripts.
    All UI now uses EngineV88 (core/engine_v88.py).
    
    Migration Guide:
        OLD: from core.quantum_engine import QuantumEngine
        NEW: from core.engine_v88 import EngineV88 as QuantumEngine
    
    [V8.1-Legacy] Phase Change Protocol + 得令保护 + 建禄加成
    """
    
    VERSION = "8.1-Legacy (DEPRECATED)"  # Use EngineV88 instead!
    
    def __init__(self, params=None):
        # ⚠️ DEPRECATION WARNING
        import warnings
        warnings.warn(
            "QuantumEngine is deprecated. Use EngineV88 instead: "
            "from core.engine_v88 import EngineV88",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Allow default params loading if None
        if params is None:
            params = self._load_default_params()
            
        self.params = params
        self.flat_params = self._flatten_params(params)
        
        # === V6.0+ Parameterization: Load Algorithm Config ===
        # 将 config_rules 默认配置与 params 中的覆盖值合并
        self.config = DEFAULT_CONFIG.copy()
        
        # === V7.0 Architecture: Load Full Algo Params ===
        self.full_config = self._deep_copy(DEFAULT_FULL_ALGO_PARAMS)
        
        # 允许 params 覆盖默认配置 (Legacy Shallow Merge)
        if params and isinstance(params, dict):
            for key, value in params.items():
                if key in self.config:
                    self.config[key] = value
            
            # Try to deep merge into full_config if params matches structure
            # (Assuming params might contain flat overrides for now, V7 will transition to structured)
            pass
        
        # Load Narrative Config
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../data/narrative_config.json')
            with open(config_path, 'r') as f:
                self.narrative_config = json.load(f).get('events', {})
        except Exception:
            self.narrative_config = {} # Fallback

        # Element Definitions
        self.ELEMENTS = {
            'wood': "甲乙寅卯",
            'fire': "丙丁巳午",
            'earth': "戊己辰戌丑未",
            'metal': "庚辛申酉",
            'water': "壬癸亥子"
        }
        self.GENERATION = {'wood': 'fire', 'fire': 'earth', 'earth': 'metal', 'metal': 'water', 'water': 'wood'}
        self.DESTRUCTION = {'wood': 'earth', 'earth': 'water', 'water': 'fire', 'fire': 'metal', 'metal': 'wood'}

        # Structural Clash Pairs (Branch)
        self.CLASH_PAIRS = [
            ('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), ('辰', '戌'), ('巳', '亥') # 6 Clashes Only
        ]

        # V3.0 Constants: The Four Vaults
        self.VAULT_MAPPING = GRAVE_TREASURY_CONFIG
        
        # V3.0 Sprint 3: Wealth Logic (Use config values)
        self.WEALTH_MAP = self.config.get('wealth_map', {
            'wood': 'earth',
            'fire': 'metal',
            'earth': 'water',
            'metal': 'wood',
            'water': 'fire'
        })
        self.TOMB_ELEMENTS = self.config.get('tomb_elements', {
            '辰': 'water', # Water Tomb
            '戌': 'fire',  # Fire Tomb
            '丑': 'metal', # Metal Tomb
            '未': 'wood'   # Wood Tomb
        })

        # === V6.0+ Initialize Engines with Config ===
        self.luck_engine = LuckEngine()
        self.skull_engine = SkullEngine(config=self.config)
        self.treasury_engine = TreasuryEngine(config=self.config)
        
        # [V7.0 Fix] Harmony Engine needs Full Config for Stem Interactions (V3.0 Schema)
        self.harmony_engine = HarmonyEngine(config=self.full_config)
        
        self.flow_engine = FlowEngine(config=self.full_config)
    
    def update_config(self, new_config: dict):
        """
        [V6.0+ Parameterization] 允许前端注入新参数，覆盖默认 config_rules
        热更新算法参数，无需重启引擎
        
        :param new_config: 新的配置字典，如 {'score_skull_crash': -40.0, 'score_treasury_bonus': 30.0}
        """
        # 更新主配置
        self.config.update(new_config)
        
        # 同步通知子引擎 - 重新初始化以应用新配置
        self.skull_engine = SkullEngine(config=self.config)
        self.treasury_engine = TreasuryEngine(config=self.config)
        self.harmony_engine = HarmonyEngine(config=self.config)
        
        # Explicitly update weights in partial reload scenarios if supported
        if hasattr(self.harmony_engine, 'update_weights'):
            self.harmony_engine.update_weights(
                sanhe_bonus=self.config.get('score_sanhe_bonus'),
                sanhe_penalty=self.config.get('score_sanhe_penalty'),
                liuhe_bonus=self.config.get('score_liuhe_bonus'),
                clash_penalty=self.config.get('score_clash_penalty')
            )
        
        # 返回更新后的配置供前端确认
        return self.config

    def _deep_copy(self, d):
        """Simple deep copy for dict/list structure."""
        if isinstance(d, dict):
            return {k: self._deep_copy(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._deep_copy(x) for x in d]
        else:
            return d

    def _deep_update(self, target, source):
        """Recursive update for nested dictionaries."""
        for k, v in source.items():
            if k in target and isinstance(target[k], dict) and isinstance(v, dict):
                self._deep_update(target[k], v)
            else:
                target[k] = v

    def update_full_config(self, new_full_config: dict):
        """
        [V7.0] Deep update for hierarchial params.
        """
        self._deep_update(self.full_config, new_full_config)
        
        # Sync back to flat config for V6.0 compatibility (Optional/Partial)
        # For now, we manually sync critical Harmony/Physics keys if needed.
        # But ideally, engines start reading from self.full_config directly.
        
        # Re-init engines with NEW config references if they support it
        # HarmonyEngine V6.1 reads flat config. We might need to update it to read full_config?
        # Or we map full_config values back to flat config here.
        
        # Map V7 Harmony -> V6 Flat
        if 'interactions' in self.full_config and 'harmony' in self.full_config['interactions']:
            h = self.full_config['interactions']['harmony']
            self.config['score_sanhe_bonus'] = h.get('sanHeBonus', 15.0)
            self.config['score_liuhe_bonus'] = h.get('liuHeBonus', 5.0)
            self.config['score_clash_penalty'] = h.get('clashPenalty', -5.0)
            
        # Trigger standard update
        self.update_config({}) # Refreshes engines with updated flat config
        
        # [V7.3] Ensure All Engines get FULL Config
        # This overrides the flat config passed by update_config
        self.flow_engine.update_config(self.full_config)
        self.treasury_engine.update_config(self.full_config)
        self.harmony_engine.update_config(self.full_config)
        
        return self.full_config

    def _calculate_energy_v7(self, bazi_list, dm_elem):
        """
        [V7.3 Core] Dynamic Energy Simulation (V2.5 Schema).
        Calculates energy map applying:
        1. Base Physics (Pillar Gravity)
        2. Particle Structure (Exposed Boost, Rooting)
        3. Void Penalty (TODO: Void detection logic)
        4. Flow Simulation
        """
        from collections import defaultdict
        
        # 1. Config Refs (V2.5 Schema)
        fc = self.full_config
        # Physics
        phy = fc.get('physics', {})
        pw = phy.get('pillarWeights', {'year': 0.8, 'month': 1.2, 'day': 1.0, 'hour': 0.9})
        # Structure
        struc = fc.get('structure', {})
        root_w = struc.get('rootingWeight', 1.0)
        exposed_boost = struc.get('exposedBoost', 1.5)
        # Flow
        flow = fc.get('flow', {})
        sp_decay = flow.get('spatialDecay', {'gap1': 0.6, 'gap2': 0.3})
        
        # 2. Build Initial State (Raw Energy)
        raw_energy = defaultdict(float)
        BASE_UNIT = 50.0 # Base unit per character
        
        # Indices: 0:Year, 1:Month, 2:Day, 3:Hour
        idx_map = {0: 'year', 1: 'month', 2: 'day', 3: 'hour'}
        
        # Pre-scan for Roots (simple logic: check if Stem element exists in Branches)
        # For simplicity, just gather all branch elements first.
        branch_elems = []
        for p in bazi_list:
             if len(p) > 1: branch_elems.append(self._get_element(p[1]))

        for idx, pillar in enumerate(bazi_list):
            if not pillar or len(pillar) < 2: continue
            
            stem, branch = pillar[0], pillar[1]
            s_elem = self._get_element(stem)
            b_elem = self._get_element(branch)
            
            # Key: Pillar Gravity (V2.5 New!)
            # Replaces old positionWeights
            p_key = idx_map.get(idx, 'year')
            p_weight = pw.get(p_key, 1.0)
            
            # --- Spatial Decay (Distance from Day Stem) ---
            dist = abs(idx - 2)
            k_dist = 1.0
            if dist == 1: k_dist = sp_decay.get('gap1', 0.6)
            elif dist >= 2: k_dist = sp_decay.get('gap2', 0.3)
            
            # --- Energy Calculation ---
            
            # Stem Energy
            if idx != 2: # Skip DM (Day Stem)
                # Check Rooting (is Stem supported by ANY branch? Simplified)
                is_rooted = s_elem in branch_elems
                k_root = root_w if is_rooted else 0.5 
                # Note: Exposed Boost concept is usually: hidden stem gets huge boost IF revealed.
                # Here we are calculating Stem directly. Is it boosted?
                # Let's say: if rooted, we apply exposedBoost relative to underground potential?
                # Simplified: Stem = Base * P_Weight * Dist * (ExposedBoost if Rooted)
                
                k_exposed = exposed_boost if is_rooted else 1.0
                
                s_score = BASE_UNIT * p_weight * k_dist * k_exposed
                raw_energy[s_elem] += s_score
                
            # Branch Energy
            # Branch is the source, usually stronger.
            b_score = BASE_UNIT * p_weight * k_dist # Branch distance also matters?
            # Usually Branch is 'Ground', less affected by distance for root support?
            # But for Energy Flow to DM, distance matters.
            
            raw_energy[b_elem] += b_score
        
        # [V8.1] 建禄加成 (Lu Bonus / In-Command Bonus)
        # When DM's element matches Month Branch element, DM is "得令" (In Command)
        # This gives a HUGE bonus to Self energy
        month_branch = bazi_list[1][1] if len(bazi_list) > 1 and len(bazi_list[1]) > 1 else ''
        mb_elem = self._get_element(month_branch)
        
        if mb_elem == dm_elem:
            # 得令 - In Command! Day Master controls the season
            LU_BONUS = BASE_UNIT * 3.0  # Major bonus: +150 points
            raw_energy[dm_elem] += LU_BONUS
            print(f"[V8.1] 建禄加成: {dm_elem} 得令 (Month: {month_branch}), +{LU_BONUS}")
        elif self.GENERATION.get(mb_elem) == dm_elem:
            # 印绶生身 - Month generates DM
            RESOURCE_BONUS = BASE_UNIT * 1.5  # Moderate bonus: +75 points
            raw_energy[dm_elem] += RESOURCE_BONUS
            print(f"[V8.1] 印绶得月: {mb_elem} 生 {dm_elem}, +{RESOURCE_BONUS}")
        # [V7.4] Inject Stem Fusion Physics (Alchemy)
        # Check for Warlord Case (Wu-Gui -> Fire) and others
        stems = [p[0] for p in bazi_list if len(p) > 0]
        month_branch = bazi_list[1][1] if len(bazi_list) > 1 and len(bazi_list[1]) > 1 else ''
        
        stem_combos = self.harmony_engine.detect_stem_interactions(stems, month_branch)
        if stem_combos:
            print(f"[DEBUG] Stem Combos Found: {len(stem_combos)}")
            for c in stem_combos: print(f" - {c['stems']} -> {c['transform_to']} (Bonus: {c['bonus']})")
            
        for combo in stem_combos:
            target_elem = combo['transform_to']
            bonus_mult = combo['bonus'] # e.g., 2.0
            
            # Apply Transformation Energy
            # We add significant energy to the Target Element
            added_energy = BASE_UNIT * bonus_mult
            raw_energy[target_elem] += added_energy
            print(f"[DEBUG] Boosted {target_elem} by {added_energy}")
            
            # [V7.4 Fix] Transformation COST (The Equivalent Exchange)
            # Remove energy from original elements to prevent Double Counting / Flow Drain
            s1_char, s2_char = combo['stems']
            e1 = self._get_element(s1_char)
            e2 = self._get_element(s2_char)
            
            # Deduct Base Energy (approx 1 unit)
            # If 2.0 Bonus is added to Target, we remove ~1.0 from originals?
            # Or remove whatever they had?
            # Stems usually have 1.0 * Weights (approx 50-80).
            # Let's remove BASE_UNIT (50).
            deduct = BASE_UNIT * 1.0 
            
            raw_energy[e1] -= deduct
            raw_energy[e2] -= deduct
            
            if raw_energy[e1] < 0: raw_energy[e1] = 0
            if raw_energy[e2] < 0: raw_energy[e2] = 0
            print(f"[DEBUG] Deducted {deduct} from {e1}, {e2}")

            
        # 3. [V7.4 Fix] Summer Earth Physics (Thermodynamic Correction)
        # "Dry Earth does not generate Metal" & "Hot Earth does not drain Fire"
        # If Month is Summer (Si, Wu, Wei), Earth is Dry/Hot -> Efficiency Drops.
        # We model this by reducing Effective Earth Energy.
        summer_branches = ['巳', '午', '未'] # Summer + Late Summer
        if month_branch in summer_branches:
            # Apply Penalty
            dry_earth_penalty = 0.6 # Reduce by 40%
            current_earth = raw_energy.get('earth', 0)
            if current_earth > 0:
                raw_energy['earth'] *= dry_earth_penalty
                print(f"[DEBUG] Summer {month_branch}: Damping Earth {current_earth:.1f} -> {raw_energy['earth']:.1f}")

        # 4. Simulate Flow
        # Update Flow Engine with current config (just in case)
        self.flow_engine.update_config(fc)
        # [V8.0] Pass month_branch for Phase Change Protocol
        final_state = self.flow_engine.simulate_flow(raw_energy, dm_elem=dm_elem, month_branch=month_branch)
        
        # [V3.0] Macro Physics: Geography & Era
        macro = fc.get('macroPhysics', {})
        
        # Geography
        lat_heat = macro.get('latitudeHeat', 0.0)
        lat_cold = macro.get('latitudeCold', 0.0)
        
        if lat_heat > 0:
            final_state['Fire'] *= (1.0 + lat_heat)
            final_state['Earth'] *= (1.0 + (lat_heat * 0.5))
            
        if lat_cold > 0:
            final_state['Water'] *= (1.0 + lat_cold)
            final_state['Metal'] *= (1.0 + (lat_cold * 0.3))
            
        # Era Ambient (Background Radiation)
        era_el = macro.get('eraElement', 'Fire')
        if era_el in final_state:
            final_state[era_el] *= 1.1 
        
        return final_state

    def _flatten_params(self, params):
        """Helper to flatten nested JSON params for easier access."""
        flat = {}
        for section, values in params.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    flat[k] = v
            else:
                flat[section] = values
        return flat

    def _get_narrative(self, key):
        """Helper to fetch and format narrative string from config."""
        ev = self.narrative_config.get(key)
        if not ev: return f""
        return f"{ev['icon']}【{ev['title']}】{ev['desc']}（断语：{ev['verdict']}）"

    def _get_element(self, char):
        if not char:  # Defensive check for None or empty string
            return None
        for e, chars in self.ELEMENTS.items():
            if char in chars: return e
        return None

    def _get_relation(self, dm_elem, target_elem):
        if dm_elem == target_elem: return 'self'
        if self.GENERATION[dm_elem] == target_elem: return 'output'
        if self.DESTRUCTION[dm_elem] == target_elem: return 'wealth'
        if self.DESTRUCTION[target_elem] == dm_elem: return 'officer'
        if self.GENERATION[target_elem] == dm_elem: return 'resource'
        return 'unknown'

    def calculate_energy(self, case_data, dynamic_context=None):
        """
        Core Calculation Logic - V2.6
        """
        fp = self.flat_params
        
        # Flags
        enable_mediation = fp.get('enable_mediation_exemption', True)
        enable_structural = fp.get('enable_structural_clash', True)

        # 1. Unpack Physics Params
        w_e_weight = fp.get("w_e_weight", 1.0)
        f_yy = fp.get("f_yy_correction", 1.0)
        
        # Thresholds
        t_follow = fp.get("T_Follow_Grid", -6.0)
        t_weak = fp.get("T_Weak_Self", -2.0)
        
        cid = case_data.get('id', 0)
        sources = case_data.get('physics_sources', {})
        wang_shuai = case_data.get('wang_shuai', '')
        is_follow = '从' in wang_shuai  
        
        # Initialize Raw Energies (Static State)
        if sources and 'self' in sources:
            s = sources['self']
            raw_e_self = s.get('month_command', 0) + s.get('day_root', 0) + s.get('other_roots', 0) + s.get('stem_support', 0)
            raw_e_output = sources.get('output', {}).get('base', 2.0)
            raw_e_cai = sources.get('wealth', {}).get('base', 2.0)
            raw_e_guan_sha = sources.get('officer', {}).get('base', 1.0)
            raw_e_resource = sources.get('resource', {}).get('base', 1.0)
        else:
            # Fallback Mock - Convert string ID to numeric hash for calculations
            if isinstance(cid, str):
                cid_num = hash(cid) % 100  # Convert string to stable number
            else:
                cid_num = cid if cid else 1
            raw_e_guan_sha = ((cid_num * 7) % 10) 
            raw_e_cai = ((cid_num * 5) % 9)
            raw_e_self = ((cid_num * 2) % 8) + 2 
            raw_e_output = ((cid_num * 3) % 8) 
            raw_e_resource = ((cid_num * 4) % 8)
            
            if '身极弱' in wang_shuai: 
                raw_e_self = -5.0
                sources = {'self': {'day_root': 1.0}} 
            elif '身弱' in wang_shuai: raw_e_self -= 3
            elif '身旺' in wang_shuai: raw_e_self += 3
        if is_follow: raw_e_self = -8 

        # Extract DM Element (Relocated for V3.0 Map Construction)
        dm_char = case_data.get('day_master', '甲')
        dm_elem = self._get_element(dm_char) or 'wood'

        # V3.0: Construct Global Elemental Energy Map
        # Map 10 Gods back to 5 Elements for Physics Calculations
        element_map = {}
        curr_elem = dm_elem
        # 1. Self -> Wood (if DM Wood)
        element_map[curr_elem] = raw_e_self
        # 2. Output -> Fire
        curr_elem = self.GENERATION[curr_elem]
        element_map[curr_elem] = raw_e_output
        # 3. Wealth -> Earth
        curr_elem = self.GENERATION[curr_elem]
        element_map[curr_elem] = raw_e_cai
        # 4. Officer -> Metal
        curr_elem = self.GENERATION[curr_elem]
        element_map[curr_elem] = raw_e_guan_sha
        # 5. Resource -> Water
        curr_elem = self.GENERATION[curr_elem]
        element_map[curr_elem] = raw_e_resource 

        # Narrative Storage (UI Payload)
        narrative_events = []
        # Legacy narrative for backward compatibility
        narrative = []

        # --- DYNAMIC LAYER ---
        if dynamic_context:
            year_str = dynamic_context.get('year', '')
            dm_char = case_data.get('day_master', '甲')
            dm_elem = self._get_element(dm_char) or 'wood'

            year_stem = year_str[0] if len(year_str) > 0 else ''
            year_branch = year_str[1] if len(year_str) > 1 else ''
            
            dy_str = dynamic_context.get('dayun', '')
            
            def fast_boost(char, major_mult):
                elem = self._get_element(char)
                if not elem: return
                rel = self._get_relation(dm_elem, elem)
                boost = 1.0 * major_mult
                
                nonlocal raw_e_self, raw_e_output, raw_e_cai, raw_e_guan_sha, raw_e_resource
                if rel == 'self': raw_e_self += boost
                elif rel == 'output': raw_e_output += boost
                elif rel == 'wealth': raw_e_cai += boost
                elif rel == 'officer': raw_e_guan_sha += boost
                elif rel == 'resource': raw_e_resource += boost

            fast_boost(year_stem, 1.5)
            fast_boost(year_branch, 3.0)
            if len(dy_str) > 1:
                fast_boost(dy_str[0], 1.0)
                fast_boost(dy_str[1], 2.0)
                
            if raw_e_guan_sha > 8.0 and raw_e_self < 2.0:
                 narrative.append(self._get_narrative("pressure_penalty"))
                 narrative_events.append({
                     "card_type": "pressure",
                     "level": "danger",
                     "title": "Pressure Overload",
                     "desc": "Killings attack Body.",
                     "score_delta": "-Penalty",
                     "animation_trigger": "red_flash"
                 })

        # --- CALCULATION OF POTENTIALS (Post-Dynamics) ---
        
        # K-Factors
        k_ctl = fp.get("K_Control_Conversion", 0.55)
        k_buf = fp.get("K_Buffer_Defense", 0.40)
        k_mutiny = fp.get("K_Mutiny_Betrayal", 1.8)
        k_leak = fp.get("K_Leak_Drain", 0.87)
        k_robbery = fp.get("K_Clash_Robbery", 1.2)
        k_burden = fp.get("K_Burden_Wealth", 1.0)
        k_pressure = fp.get("K_Pressure_Attack", 1.0)
        k_broken = fp.get("K_Broken_Collapse", 1.5)
        
        # 1. Career
        w_off = fp.get("W_Career_Officer", 0.8)
        w_res = fp.get("W_Career_Resource", 0.1)
        w_out_job = fp.get("W_Career_Output", 0.0)
        
        e_career = (raw_e_guan_sha * w_off) + (raw_e_self * 0.2) + (raw_e_resource * w_res) + (raw_e_output * w_out_job)
        
        if is_follow:
            if "儿" in wang_shuai: 
                 e_career -= raw_e_guan_sha * 0.5 
        else:
            if raw_e_guan_sha > 1.0 and raw_e_output > 1.0:
                if raw_e_self < t_weak and raw_e_guan_sha > 4.0 and raw_e_output > 4.0:
                     e_career -= min(raw_e_guan_sha, raw_e_output) * k_mutiny 
                     narrative.append("⚠️ 伤官见官 (Mutiny)")
                else:
                     e_career += min(raw_e_guan_sha, raw_e_output) * k_ctl 
                     narrative.append("⚡ 食神制杀 (Control)")
                     narrative_events.append({
                        "card_type": "control",
                        "level": "epic",
                        "title": "食神制杀",
                        "desc": "Chaos handled by Intelligence.",
                        "score_delta": "+Control",
                        "animation_trigger": "blue_beam"
                     })
            
            if raw_e_self < t_weak and raw_e_guan_sha > 5.0 and raw_e_resource < 2.0:
                 e_career -= (raw_e_guan_sha - 5.0) * k_pressure
                 narrative.append("⚠️ 七杀攻身 (Pressure)")

        # 2. Wealth
        w_cai = fp.get("W_Wealth_Cai", 0.6)
        w_out = fp.get("W_Wealth_Output", 0.4)
        
        e_wealth = (raw_e_cai * w_cai) + (raw_e_output * w_out)
        
        if is_follow:
            if "儿" in wang_shuai: e_wealth += raw_e_output * 0.5 
            elif "财" in wang_shuai: e_wealth += raw_e_cai * 0.5 
        else:
            if raw_e_self < 0.0 and raw_e_output > 5.0:
                e_wealth -= (raw_e_output - raw_e_self) * k_leak 
            
            # Wealth Burden (Case 3)
            if raw_e_self < -3.0 and raw_e_cai > 6.0:
                e_wealth -= (raw_e_cai - 4.0) * k_burden 
                narrative.append("💸 财多身弱 (Wealth Burden)")

            # Logic 1: Mediation Exemption (Case 1)
            # Robbery (Jie Cai Kills Wealth)
            if raw_e_self > 5.0 and raw_e_cai > 1.0:
                 # V2.9: Mountain Alliance (Earth Amnesty)
                 enable_mountain = fp.get('enable_mountain_alliance', True)
                 dm_char = case_data.get('day_master', '甲')
                 dm_elem = self._get_element(dm_char) or 'wood'
                 
                 is_mountain_alliance = False
                 if enable_mountain and dm_elem == 'earth' and raw_e_self > 6.0:
                      is_mountain_alliance = True
                      narrative.append("⛰️【积土成山】比劫助身，利合伙求财")
                      narrative_events.append({
                          "card_type": "mountain_alliance",
                          "level": "legendary",
                          "title": "积土成山 (Alliance)",
                          "desc": "Earth thrives on accumulation. Robbers become partners.",
                          "score_delta": f"+{round(raw_e_self * 0.3 * k_robbery, 2)} (Exempt)",
                          "animation_trigger": "earth_assemble"
                      })

                 if not is_mountain_alliance:
                     raw_penalty = (raw_e_self * 0.3) * k_robbery
                     
                     effective_penalty = raw_penalty
                     exempt = False
                     if enable_mediation:
                         if raw_e_output > 4.0:
                             effective_penalty = raw_penalty * 0.2
                             narrative.append("🌊 食伤通关 (Output Mediation)")
                             exempt = True
                         elif raw_e_guan_sha >= 3.0:
                             effective_penalty = 0.0
                             narrative.append("🛡️ 官杀护财 (Officer Shield)")
                             narrative_events.append({
                                "card_type": "mediation",
                                "level": "epic",
                                "title": "官杀护财 (Shield)",
                                "desc": "Authority protects Wealth from Robbers.",
                                "score_delta": "+Shield",
                                "animation_trigger": "shield_active"
                             })
                             exempt = True
                     
                     e_wealth -= effective_penalty
                     if not exempt:
                        narrative.append("⚔️ 比劫夺财 (Robbery)")
                     elif narrative[-1] == "🌊 食伤通关 (Output Mediation)": 
                         # Catching the mediation event if it wasn't added above
                         narrative_events.append({
                            "card_type": "mediation",
                            "level": "epic",
                            "title": "食伤通关 (Flow)",
                            "desc": "Talent bridges the gap between Self and Wealth.",
                            "score_delta": f"+{round(raw_penalty - effective_penalty, 2)} Saved",
                            "animation_trigger": "prism_flow"
                         })

        # 3. Relationship
        gender = case_data.get('gender', '男')
        e_spouse = raw_e_cai if "男" in gender else raw_e_guan_sha
        
        w_spouse = fp.get("W_Rel_Spouse", 0.35)
        w_self = fp.get("W_Rel_Self", 0.20)
        
        e_relationship = (w_spouse * e_spouse * 2.0) + (w_self * raw_e_self)
        
        if is_follow:
             pass 
        else:
            if raw_e_self > 6.0 and e_spouse < 4.0:
                 e_relationship -= (raw_e_self - e_spouse) * k_robbery 
            
            if "男" in gender and raw_e_cai > 0 and raw_e_self > 5.0:
                 # Male: Rob Wealth attacks Spouse checks Mediation too
                 raw_rel_penalty = (raw_e_self * 0.2) * k_robbery
                 if enable_mediation and (raw_e_output > 4.0 or raw_e_guan_sha >= 3.0):
                     raw_rel_penalty = 0.0 # Relationship is saved by character
                 e_relationship -= raw_rel_penalty

        # V2.7 Upgrade: The Harm Matrix
        self.HARM_PAIRS = [
            ('子', '未'), ('丑', '午'), ('寅', '巳'), 
            ('卯', '辰'), ('申', '亥'), ('酉', '戌')
        ]

        # Logic 2: Structural Clash & Harm Matrix (V2.7)
        if enable_structural:
            bazi = case_data.get('bazi', [])
            if len(bazi) >= 4:
                # Extract Branches from pillars: "庚子" -> "子"
                branches = [p[1] for p in bazi if len(p) > 1]
                day_branch = branches[2] # Day is 3rd pillar (0,1,2,3)
                
                # V2.7 Full Structural Scan (Multi-dimensional)
                clash_score = 0.0
                checked_pairs = set()
                
                # V2.8: Earth Branches Set
                EARTH_BRANCHES = {'辰', '戌', '丑', '未'}

                # === Sprint 5.3: Three Punishments (The Skull Protocol) ===
                # Logic: Check if {丑, 未, 戌} is a subset of (Chart Branches + Year Branch)
                
                # Get dynamic year branch (V5.3 Logic restored)
                current_year_branch = None
                if dynamic_context and 'year' in dynamic_context:
                    yp = dynamic_context['year']
                    if len(yp) > 1: current_year_branch = yp[1]

                if current_year_branch:
                    # Construct simple chart dict for engine
                    temp_chart = {
                        'year_pillar': ' ' + branches[0] if len(branches) > 0 else '  ',
                        'month_pillar': ' ' + branches[1] if len(branches) > 1 else '  ',
                        'day_pillar': ' ' + branches[2] if len(branches) > 2 else '  ',
                        'hour_pillar': ' ' + branches[3] if len(branches) > 3 else '  ',
                    }
                    
                    if self.skull_engine.detect_three_punishments(temp_chart, current_year_branch):
                        # TRIGGERED
                        clash_score += 50.0 # Massive penalty
                        narrative.append("💀 丑未戌三刑！结构性崩塌")
                        narrative_events.append({
                            "card_type": "punishment_collapse",
                            "level": "apocalypse",
                            "title": "三刑崩塌 (The Skull)",
                            "desc": "Chou-Wei-Xu Earth Punishment triggered. Structural Integrity Critical.",
                            "score_delta": "-50.0 (Collapse)",
                            "animation_trigger": "skull_shatter"
                        })
                        
                        # Apply immediate heavy damage
                        e_career -= 20.0
                        e_wealth -= 20.0
                        e_relationship -= 20.0

                for i in range(len(branches)):
                    for j in range(i + 1, len(branches)):
                        b1 = branches[i]
                        b2 = branches[j]
                        
                        # Sort for consistent pair check
                        pair = tuple(sorted((b1, b2)))
                        if pair in checked_pairs: continue
                        checked_pairs.add(pair)

                        # V3.0 Logic: Quantum Vault Tunneling (Replaces Earth Amnesty)
                        # Detect Earth Clashes: Chen-Xu, Chou-Wei
                        is_earth_clash = (b1 in self.treasury_engine.VAULT_MAPPING and b2 in self.treasury_engine.VAULT_MAPPING and 
                                         ((b1, b2) in self.CLASH_PAIRS or (b2, b1) in self.CLASH_PAIRS))
                        
                        if is_earth_clash:
                            # Process EACH side of the clash as a potential Vault opening
                            # Loop via set to handle duplicate branch case safely (though rare in collision pair)
                            for branch_key in [b1, b2]:
                                bonus, event = self.treasury_engine.process_quantum_tunneling(branch_key, element_map)
                                narrative_events.append(event)
                                
                                if "vault_open" in event['card_type']:
                                    # Bonus applies to Wealth and Career
                                    e_wealth += bonus
                                    e_career += bonus
                                    narrative.append(f"💰 {event['title']}")
                                else:
                                    # Penalty applies to Structure/Rel
                                    clash_score += abs(bonus) # Add to clash score for relation penalty
                                    narrative.append(f"⚠️ {event['title']}")
                            
                            # Skip standard clash penalty logic for these specific branches (they are handled as Vaults)
                            continue

                        # 1. Six Clashes (Crash)
                        if (b1, b2) in self.CLASH_PAIRS or (b2, b1) in self.CLASH_PAIRS:
                            clash_score += fp.get('Clash_Penalty_Weight', 5.0)
                            narrative.append(f"💥 地支相冲 ({b1}-{b2})")
                            
                        # 2. Six Harms (Harm) - V2.8 Modified Metric
                        elif (b1, b2) in self.HARM_PAIRS or (b2, b1) in self.HARM_PAIRS:
                            # Reduced from 4.0 to 2.0 (Harm is friction, not crash)
                            clash_score += fp.get('Harm_Penalty_Weight', 2.0)
                            narrative.append(f"🕸️ 地支相害 ({b1}-{b2})")
                        
                        # 3. Special: Hai-Wu Water/Fire War
                        elif {b1, b2} == {'亥', '午'}:
                            clash_score += 3.0
                            narrative.append(f"⚔️ 水火暗战 ({b1}-{b2})")
                
                if clash_score > 0:
                    # Apply Structural Penalty to Relationship
                    # (Represents systemic instability affecting the home)
                    penalty = clash_score * k_robbery 
                    
                    # [NEW] V2.9 Suffering Saturation / Penalty Cap
                    # Limit the maximum penalty to 6.0 so normal people don't get -10.0
                    max_struct_penalty = fp.get('Max_Structural_Penalty', 6.0)
                    if penalty > max_struct_penalty:
                        narrative_events.append({
                            "card_type": "penalty_cap",
                            "level": "epic",
                            "title": "痛苦上限 (Cap)",
                            "desc": f"Structural damage (-{round(penalty, 1)}) capped by system resilience.",
                            "score_delta": f"Limited to -{max_struct_penalty}",
                            "animation_trigger": "shield_ripple"
                        })
                    penalty = min(penalty, max_struct_penalty)
                    
                    e_relationship -= penalty

        # Logic 3: Fake Follow Collapse (Case 8)
        # Check root
        has_root = False
        if sources.get('self', {}).get('day_root', 0) > 0.5 or sources.get('self', {}).get('other_roots', 0) > 1.0:
            has_root = True
            
        if -6.0 < raw_e_self < -3.0 and has_root:
             # Fake Follow Dead Zone
             penalty = 8.0 * k_broken
             e_career -= penalty
             e_wealth -= penalty
             e_relationship -= penalty
             narrative.append("⚠️【格局崩塌】假从格破局")

        e_relationship *= f_yy

        # Final Formatting
        full_desc = " ".join(narrative[-3:]) if narrative else "Energy Stable" 
        
        pillar_energies = sources.get('pillar_energies', [0]*8)
        
        # FluxEngine Integration: Auto-Calculate if missing
        if all(v == 0 for v in pillar_energies) and 'bazi' in case_data:
            try:
                from core.flux import FluxEngine
                bazi_list = case_data['bazi'] 
                if len(bazi_list) >= 4:
                    def parse_pillar(s): return {'stem': s[0], 'branch': s[1]} if len(s) > 1 else {}
                    chart = {
                        'year': parse_pillar(bazi_list[0]),
                        'month': parse_pillar(bazi_list[1]),
                        'day': parse_pillar(bazi_list[2]),
                        'hour': parse_pillar(bazi_list[3])
                    }
                    fe = FluxEngine(chart)
                    
                    d_s, d_b, l_s, l_b = None, None, None, None
                    if dynamic_context:
                        dy = dynamic_context.get('luck', '')
                        ln = dynamic_context.get('year', '')
                        if len(dy)>1: d_s, d_b = dy[0], dy[1]
                        if len(ln)>1: l_s, l_b = ln[0], ln[1]
                    
                    flux_res = fe.calculate_flux(dy_stem=d_s, dy_branch=d_b, ln_stem=l_s, ln_branch=l_b)
                    
                    pe_map = [0.0] * 8
                    p_lookup = {p['id']: p['amp'] for p in flux_res['particle_states']}
                    
                    pe_map[0] = p_lookup.get('year_stem', 0)
                    pe_map[1] = p_lookup.get('year_branch', 0)
                    pe_map[2] = p_lookup.get('month_stem', 0)
                    pe_map[3] = p_lookup.get('month_branch', 0)
                    pe_map[4] = p_lookup.get('day_stem', 0)
                    pe_map[5] = p_lookup.get('day_branch', 0)
                    pe_map[6] = p_lookup.get('hour_stem', 0)
                    pe_map[7] = p_lookup.get('hour_branch', 0)
                    
                    pillar_energies = [round(x, 1) for x in pe_map]
            except Exception as e:
                # Fallback to silent fail if FluxEngine not available or error
                print(f"DEBUG: FluxEngine Integration Error: {e}")
                import traceback
                traceback.print_exc()
                pass

        tg = {
            "bi_jian": raw_e_self * 0.5, "jie_cai": raw_e_self * 0.5,
            "shi_shen": raw_e_output * 0.6, "shang_guan": raw_e_output * 0.4,
            "pian_cai": raw_e_cai * 0.6, "zheng_cai": raw_e_cai * 0.4,
            "qi_sha": raw_e_guan_sha * 0.4, "zheng_guan": raw_e_guan_sha * 0.6,
            "pian_yin": raw_e_resource * 0.4, "zheng_yin": raw_e_resource * 0.6
        }

        def clamp(val): return round(max(-10, min(10, val * w_e_weight)), 2)
        
        return {
            "career": clamp(e_career),
            "wealth": clamp(e_wealth),
            "relationship": clamp(e_relationship),
            "desc": full_desc, 
            "particles": {
                "self": round(raw_e_self, 1),
                "output": round(raw_e_output, 1),
                "wealth": round(raw_e_cai, 1),
                "officer": round(raw_e_guan_sha, 1),
                "resource": round(raw_e_resource, 1)
            },
            "ten_gods": tg,
            "pillar_energies": pillar_energies,
            "narrative_events": narrative_events
        }
        # Patch QuantumEngine with new methods for Verification Pipeline
        # This avoids rewriting the whole file drastically while adding the logic.

    def calculate_chart(self, birth_data: dict) -> dict:
                """
                Step 2: Pai Pan (排盘) - Calculate Chart & Analysis from Birth Data.
                Uses lunar_python for high precision.
                """
                try:
                    # 1. Parse Input
                    year = int(birth_data.get('birth_year', 2000))
                    month = int(birth_data.get('birth_month', 1))
                    day = int(birth_data.get('birth_day', 1))
                    hour = int(birth_data.get('birth_hour', 12))
                    minute = int(birth_data.get('birth_minute', 0))
                
                    # [V3.0] Solar Time Calibration
                    fc = getattr(self, 'full_config', {})
                    macro = fc.get('macroPhysics', {})
                    if macro.get('useSolarTime', False):
                        blon = birth_data.get('birth_lon')
                        if blon is not None:
                            # 4 minutes per degree. Standard: 120.0 E (Beijing)
                            try:
                                deg = float(blon)
                                offset_min = (deg - 120.0) * 4.0
                                total_min = hour * 60 + minute + offset_min
                                
                                # Normalize
                                import math
                                total_min = int(round(total_min))
                                new_h = (total_min // 60) % 24
                                new_m = total_min % 60
                                
                                hour, minute = new_h, new_m
                            except:
                                pass # Fallback to clock time
                                
                    # 2. Lunar Python Calculation
                    from lunar_python import Solar
                    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
                    lunar = solar.getLunar()
                    bazi = lunar.getEightChar()
            
                    # Get GantZhi (Pillars)
                    # lunar_python returns "甲子", "乙丑" etc.
                    # Note: lunar_python getYear() might return the year based on Lunar calendar or Solar terms.
                    # Standard Paipan relies on Solar Terms (Jie Qi). lunar_python handles this in getEightChar().
                    year_fz = bazi.getYear()
                    month_fz = bazi.getMonth()
                    day_fz = bazi.getDay()
                    hour_fz = bazi.getTime()
            
                    bazi_list = [year_fz, month_fz, day_fz, hour_fz]
                    day_master = day_fz[0] # Day Stem
            
                    # 3. Determine Strong/Weak (Wang Shuai)
                    # Simplified algorithm based on resource/friend scores
                    wang_shuai, energy_score = self._evaluate_wang_shuai(day_master, bazi_list)
            
                    # 4. Determine Favorable Elements (Xi Yong Shen)
                    favorable = self._determine_favorable(day_master, wang_shuai, bazi_list)
            
                    return {
                        "bazi": bazi_list,
                        "day_master": day_master,
                        "wang_shuai": wang_shuai, # e.g. "Body Strong", "Body Weak"
                        "energy_score": energy_score,
                        "favorable_elements": favorable, # e.g. ["Water", "Wood"]
                        "solar_date": f"{year}-{month}-{day} {hour}:{minute}"
                    }
            
                except Exception as e:
                    print(f"Error in calculate_chart: {e}")
                    return {
                        "bazi": [],
                        "error": str(e),
                        "favorable_elements": []
                    }

    def _evaluate_wang_shuai(self, dm: str, bazi: list) -> (str, float):
        """
        Internal: Evaluate Day Master strength.
        """
        dm_elem = self._get_element(dm)
        if not dm_elem: return "Unknown", 0.0
        
        score = 0.0
        
        # Weights (V7.3 Config Driven - V2.5 Schema)
        fc = getattr(self, 'full_config', {})
        phy = fc.get('physics', {})
        pw = phy.get('pillarWeights', {})
        
        # Map V2.5 weights to legacy relative weights for fallback calculation
        WEIGHT_MONTH_COMMAND = 0.40 * pw.get('month', 1.2)
        WEIGHT_DAY_BRANCH = 0.15 * pw.get('day', 1.0)
        WEIGHT_STEM = 0.10 * pw.get('year', 0.8)
        WEIGHT_BRANCH = 0.05 * pw.get('hour', 0.9)
        
        month_branch = bazi[1][1]
        BASE_UNIT = 50.0
        
        # 1. Month Command (Ling)
        mb_elem = self._get_element(month_branch)
        rel = self._get_relation(dm_elem, mb_elem)
        
        is_same_group = (rel == 'self' or rel == 'resource')
        if is_same_group: score += (WEIGHT_MONTH_COMMAND * BASE_UNIT)
        
        score = 0.0 
        
        # 2. Iterate all chars
        total_support = 0.0
        total_oppose = 0.0
        
        for idx, pillar in enumerate(bazi):
            if not pillar: continue
            stem, branch = pillar[0], pillar[1]
            
            # Stem
            if idx != 2: # Skip DM itself
                s_elem = self._get_element(stem)
                s_rel = self._get_relation(dm_elem, s_elem)
                
                w_val = WEIGHT_STEM * BASE_UNIT
                if s_rel in ['self', 'resource']: total_support += w_val
                else: total_oppose += w_val
                
            # Branch
            b_elem = self._get_element(branch)
            b_rel = self._get_relation(dm_elem, b_elem)
            
            # Select Weight based on Position
            if idx == 1: # Month
                w_val = WEIGHT_MONTH_COMMAND * BASE_UNIT
            elif idx == 2: # Day
                w_val = WEIGHT_DAY_BRANCH * BASE_UNIT
            else: # Year/Hour
                w_val = WEIGHT_BRANCH * BASE_UNIT
            
            if b_rel in ['self', 'resource']: total_support += w_val
            else: total_oppose += w_val
            
        final_score = score + total_support
        
        # Thresholds (Simplified)
        strength = "Strong" if (final_score > total_oppose) else "Weak"
        
        if is_same_group and (final_score * 1.2 > total_oppose): 
            strength = "Strong"
            
        # === V7.1 Flow Override ===
        try:
            flow_state = self._calculate_energy_v7(bazi, dm_elem)
            e_self = flow_state.get(dm_elem, 0)
            
            resource_elem = None
            for e, v in self.GENERATION.items():
                if v == dm_elem: resource_elem = e
                
            e_resource = flow_state.get(resource_elem, 0) if resource_elem else 0
            
            # === V8.0 Phase Change: Scorched Earth Correction ===
            # If month is summer AND DM is Metal AND Resource is Earth,
            # the Resource CANNOT effectively support Metal (焦土不生金)
            # Apply same damping to Resource contribution
            month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
            SUMMER_BRANCHES = {'巳', '午', '未'}
            
            if month_branch in SUMMER_BRANCHES and dm_elem == 'metal' and resource_elem == 'earth':
                # Scorched Earth: Resource is functionally useless to Metal
                # Only count the 15% that ACTUALLY transfers
                pc = self.full_config.get('flow', {}).get('phaseChange', {})
                scorched_damping = pc.get('scorchedEarthDamping', 0.15)
                
                original_resource = e_resource
                e_resource *= scorched_damping
                print(f"[V8.0] Scorched Earth: Resource {original_resource:.1f} → {e_resource:.1f} (Effective for Metal)")
            
            total_flow_support = e_self + e_resource
            total_flow_oppose = sum(flow_state.values()) - total_flow_support
            
            strength_v7 = "Strong" if (total_flow_support > total_flow_oppose) else "Weak"
            
            # === V8.1 得令保护 (In-Command Override) ===
            # When DM is "得令" (Month Branch element == DM element),
            # Month is the STRONGEST pillar. If DM controls the month,
            # this is a very strong indicator that should override flow simulation.
            mb_elem = self._get_element(month_branch)
            is_in_command = (mb_elem == dm_elem)
            
            if is_in_command:
                # Check if there's severe opposition (e.g., multiple fire pillars for metal DM)
                # But even then, month control is significant
                opposition_ratio = total_flow_oppose / max(total_flow_support, 1.0)
                
                if opposition_ratio < 5.0:  # Not overwhelmingly opposed
                    strength_v7 = "Strong"
                    strength = "Strong"  # V8.1: Force assignment!
                    # Recalculate score with month bonus
                    final_score = max(final_score, 80.0)  # Minimum score for 得令
                    print(f"[V8.1] 得令保护: {dm_elem} 得令于{month_branch}月, 判定为Strong (Override)")
            
            # Only override if significant difference and NOT protected by 得令
            elif final_score > 0 and abs(total_flow_support - final_score) > 5:
                final_score = total_flow_support 
                strength = strength_v7
                
        except Exception as e:
            print(f"V7 Flow Error: {e}")
        
        return strength, final_score

    def _determine_favorable(self, dm: str, wang_shuai: str, bazi: list) -> list:
            """
            Determine Xi Yong Shen based on Strong/Weak.
            Strong -> Needs Suppress (Officer), Drain (Output), Consume (Wealth)
            Weak -> Needs Support (Resource), Help (Friend)
            """
            dm_elem = self._get_element(dm)
            # Generation chain: Wood -> Fire -> Earth -> Metal -> Water -> Wood
    
            # Get all elements
            elements = ["wood", "fire", "earth", "metal", "water"]
    
            # Identify type relations relative to DM
            # Self, Output, Wealth, Officer, Resource
            relations = {}
            for e in elements:
                r = self._get_relation(dm_elem, e)
                relations[r] = e
        
            favorable = []
    
            if "Strong" in wang_shuai:
                # Favor: Output, Wealth, Officer
                favorable.append(relations.get('output'))
                favorable.append(relations.get('wealth'))
                favorable.append(relations.get('officer'))
            else:
                # Favor: Resource, Self
                favorable.append(relations.get('resource'))
                favorable.append(relations.get('self'))
        
            # Clean up None and capitalize
            return [f.capitalize() for f in favorable if f]

    def get_elements_for_year(self, year: int) -> list:
            """
            Get the Five Elements for a specific year (Gui Si -> Water, Fire).
            """
            try:
                # Use lunar_python to get GanZhi for the year
                # Create a date in that year (e.g., Mid-year) to get the year pillar
                solar = Solar.fromYmdHms(year, 6, 15, 12, 0, 0)
                lunar = solar.getLunar()
                year_gan_zhi = lunar.getYearInGanZhi() # e.g. "甲午"
        
                stem = year_gan_zhi[0]
                branch = year_gan_zhi[1]
        
                e1 = self._get_element(stem)
                e2 = self._get_element(branch)
        
                # Capitalize
                res = []
                if e1: res.append(e1.capitalize())
                if e2: res.append(e2.capitalize())
                return res
            except Exception:
                return []



    def get_year_pillar(self, year: int) -> str:
            """
            Get the GanZhi for a specific year.
            """
            try:
                from lunar_python import Solar
                # Use mid-year to avoid boundary issues
                solar = Solar.fromYmdHms(year, 6, 15, 12, 0, 0)
                lunar = solar.getLunar()
                return lunar.getYearInGanZhi()
            except Exception:
                return ""


        # Helper for default params
    def _load_default_params(self):
            """Load golden parameters from disk as default."""
            try:
                path = os.path.join(os.path.dirname(__file__), '../data/golden_parameters.json')
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            except Exception:
                pass
            return {}


    def calculate_year_score(self, year_pillar: str, favorable_elements: list, unfavorable_elements: list, birth_chart: dict = None) -> dict:
            """
            V3.5 Core Algorithm: Calculate Year Luck Score with Treasury Mechanics and Ethical Safety Valve.
            Returns dict with score, details, treasury_icon, treasury_risk
            """
            if not year_pillar or len(year_pillar) < 2:
                return {'score': 0.0, 'details': ["Invalid Pillar"], 'treasury_icon': None, 'treasury_risk': 'none'}
        
            stem = year_pillar[0]
            branch = year_pillar[1]
    
            # Get elements (lowercase)
            stem_element = self._get_element(stem)
            branch_element = self._get_element(branch)
    
            if not stem_element or not branch_element:
                return {'score': 0.0, 'details': ["Unknown Elements"], 'treasury_icon': None, 'treasury_risk': 'none'}
        
            # Normalize input lists to lowercase for comparison
            fav_norm = [f.lower() for f in favorable_elements]
            unfav_norm = [u.lower() for u in unfavorable_elements]
    
            details = []
    
            # 1. Base Score Calculation
            # Stem (Appearance)
            if stem_element in fav_norm:
                stem_score = 10.0
            elif stem_element in unfav_norm:
                stem_score = -10.0
            else:
                stem_score = 0.0 # Neutral
        
            # Branch (Root/Foundation)
            if branch_element in fav_norm:
                branch_score = 10.0
            elif branch_element in unfav_norm:
                branch_score = -10.0
            else:
                branch_score = 0.0 # Neutral
        
            # 2. Weighted Total (Stem 40%, Branch 60%)
            base_score = (stem_score * 0.4) + (branch_score * 0.6)
    
            # 3. Structural Mechanics (V2.0)
    
            # Check Generation Relationships
            stem_gen_branch = (self.GENERATION.get(stem_element) == branch_element)
            branch_gen_stem = (self.GENERATION.get(branch_element) == stem_element)
            same_element = (stem_element == branch_element)
    
            # 3.1 Penalty: Cut Feet / Cover Head (截脚/盖头)
            if stem_element in fav_norm and branch_element in unfav_norm:
                base_score -= 5.0
                details.append("⚠️ 截脚 (Cut Feet)")
        
            # 3.2 Reward: Synergy (相生/通气)
            if stem_gen_branch and (branch_element in fav_norm):
                base_score += 5.0
                details.append("🌟 盖头 (Cover Head - Good)")
        
            if branch_gen_stem and (stem_element in fav_norm):
                base_score += 5.0
                details.append("🌟 坐禄/印 (Root Support)")
        
            if same_element and (stem_element in fav_norm or branch_element in fav_norm):
                base_score += 5.0
                details.append("🔥 干支同气 (Pure Energy)")
        
            final_score = base_score
    
            # === V3.0 Sprint 3: Treasury Multiplier ===
            # === V3.5 Sprint 5: Ethical Safety Valve ===
            treasury_icon = None  # Will indicate icon type for frontend
            treasury_risk_level = "none"  # none, opportunity, warning
    
            if birth_chart:
                # === Delegated to TreasuryEngine (V6.0) ===
                # Calculate bonus score and details from Treasury Interactions
                final_score, t_details, t_icon, t_risk = self.treasury_engine.process_treasury_scoring(
                    birth_chart, branch, base_score,
                    birth_chart.get('dm_strength', 'medium'), # TODO: better estimation
                    self._get_element(birth_chart.get('day_master'))
                )
        
                # Append data
                details.extend(t_details)
                treasury_icon = t_icon
                treasury_risk_level = t_risk
        
                # === Delegated to SkullEngine (V6.0) ===
                if self.skull_engine.detect_three_punishments(birth_chart, branch):
                    # 使用配置中的 score_skull_crash (支持热更新)
                    final_score = self.config.get('score_skull_crash', -50.0)
                    treasury_icon = '💀'
                    treasury_risk_level = 'danger'
                    details.append("💀 丑未戌三刑！结构性崩塌 (Structure Collapse)")

            # V3.5: Return enhanced structure
            return {
                'score': round(final_score, 2),
                'details': details,
                'treasury_icon': treasury_icon,
                'treasury_risk': treasury_risk_level
            }


        # === V6.0 Final: Sub-Engine Delegation ===
        # Three Punishments detection is now handled by SkullEngine
        # Year pillar calculation is now handled by LuckEngine.get_year_ganzhi()


    def calculate_year_context(self, profile: BaziProfile, year: int) -> DestinyContext:
            """
            [V6.0 Final] 核心调度逻辑 (Facade Pattern)
    
            不再包含具体算法实现，只负责指挥子引擎协同工作：
            - LuckEngine: 处理流年干支与大运
            - TreasuryEngine: 处理财库与机遇检测
            - SkullEngine: 处理三刑等极端风控
            """
            # === 1. 运势层 (Luck Layer) ===
            year_pillar = self.luck_engine.get_year_ganzhi(year)
            current_luck = profile.get_luck_pillar_at(year)
    
            # === 2. 基础数据准备 ===
            bazi_list = [
                profile.pillars['year'],
                profile.pillars['month'],
                profile.pillars['day'],
                profile.pillars['hour']
            ]
    
            # 提取四柱地支
            chart_branches = [p[1] for p in bazi_list if len(p) > 1]
            year_branch = year_pillar[1] if len(year_pillar) > 1 else ''
    
            # 估算旺衰
            wang_shuai_str = "Medium"
            try:
                w_s, _ = self._evaluate_wang_shuai(profile.day_master, bazi_list)
                wang_shuai_str = "Strong" if "Strong" in w_s else "Weak"
            except:
                pass
    
            # 获取日主五行
            dm_element = self._get_element(profile.day_master)
            dm_element_cap = dm_element.capitalize() if dm_element else 'Wood'
    
            # === 3. 基础分数计算 ===
            # 构造适配数据
            adapter_chart = {
                'day_master': profile.day_master,
                'year': bazi_list[0],
                'month': bazi_list[1],
                'day': bazi_list[2],
                'hour': bazi_list[3],
                'dm_strength': wang_shuai_str
            }
    
            # 计算基础分 (使用现有的 calculate_year_score)
            favorable = self._determine_favorable(profile.day_master, wang_shuai_str, bazi_list)
            unfavorable = [e.capitalize() for e in ['wood', 'fire', 'earth', 'metal', 'water']
                           if e.capitalize() not in favorable]
    
            base_result = self.calculate_year_score(year_pillar, favorable, unfavorable, adapter_chart)
            base_score = base_result.get('score', 0.0)
            details = base_result.get('details', [])
    
            # === 4. 财库/机遇层 (Treasury Layer) ===
            t_score, t_details, t_icon, t_risk = self.treasury_engine.process_treasury_scoring(
                adapter_chart, year_branch, base_score, wang_shuai_str, dm_element_cap
            )
    
            # 合并结果
            if t_details:
                details.extend(t_details)
            final_score = t_score
            icon = t_icon
            risk_level = t_risk
    
            # === 4.5 Harmony Layer (Fusion & Fission) ===
            # V6.1: Chemical Reactions (SanHe, LiuHe, LiuChong)
            h_interactions = self.harmony_engine.detect_interactions(chart_branches, year_branch)
            h_score, h_details, h_tags = self.harmony_engine.calculate_harmony_score(h_interactions, favorable)
    
            final_score += h_score
            details.extend(h_details)
            # Merge Tags if useful, though Context usually uses details
    
            # Harmony Icon Logic (Priority over Treasury if significant)
            if h_score >= 15.0: # SanHe Favorable
                icon = "✨"
            elif h_score <= -15.0: # SanHe Unfavorable
                icon = "🌪️"
            elif "六合" in str(h_tags):
                # Only override if no Treasury
                if not t_icon: icon = "❤️"
            elif "六冲" in str(h_tags):
                if not t_icon: icon = "💥"

            # === 5. 骷髅/风控层 (Skull Layer) ===
            # 构造 SkullEngine 需要的 chart 格式
            skull_chart = {
                'year_pillar': bazi_list[0],
                'month_pillar': bazi_list[1],
                'day_pillar': bazi_list[2],
                'hour_pillar': bazi_list[3]
            }
    
            is_skull_triggered = self.skull_engine.detect_three_punishments(skull_chart, year_branch)
    
            if is_skull_triggered:
                # 💀 骷髅协议触发！强制覆盖一切！
                # 使用配置中的 score_skull_crash (支持热更新)
                final_score = self.config.get('score_skull_crash', -50.0)
                icon = "💀"
                details = ["三刑崩塌 (The Skull)", "结构性崩塌", "极度风险"]
                risk_level = "danger"
                energy_lvl = "Critical Risk (大凶)"
            else:
                # 正常能量等级判定
                if final_score <= -40:
                    energy_lvl = "Structural Collapse"
                elif final_score > 6:
                    energy_lvl = "High Opportunity"
                elif final_score < -6:
                    energy_lvl = "High Risk"
                else:
                    energy_lvl = "Neutral"
    
            # === 6. 三维度能量计算 (使用完整算法) ===
            # 构造 case_data 以调用 calculate_energy
            case_data = {
                'id': year,
                'day_master': profile.day_master,
                'wang_shuai': wang_shuai_str,
                'bazi': bazi_list,
                'physics_sources': {
                    'self': {'stem_support': 3.0 if wang_shuai_str == 'Strong' else -3.0},
                    'output': {'base': 2.0},
                    'wealth': {'base': 2.0},
                    'officer': {'base': 2.0},
                    'resource': {'base': 2.0}
                }
            }
            dynamic_context = {'year': year_pillar, 'dayun': current_luck or ''}
    
            try:
                energy_result = self.calculate_energy(case_data, dynamic_context)
                e_career = energy_result.get('career', final_score * 0.8)
                e_wealth = energy_result.get('wealth', final_score * 1.0)
                e_relationship = energy_result.get('relationship', final_score * 0.6)
            except Exception:
                # Fallback to simple mapping if calculate_energy fails
                e_career = final_score * 0.8
                e_wealth = final_score * 1.0
                e_relationship = final_score * 0.6
    
            # === 7. 构造 DestinyContext ===
            ctx = DestinyContext(
                year=year,
                pillar=year_pillar,
                luck_pillar=current_luck,
                score=final_score,
                raw_score=base_score,
                energy_level=energy_lvl,
                is_treasury_open=(icon in ["🏆", "🗝️"]),
                treasury_type="Wealth" if t_icon == "🏆" else "General" if t_icon else None,
                day_master_strength=wang_shuai_str,
                risk_level=risk_level,
                icon=icon,
                tags=details,
                description="; ".join(details[:2]) if details else "平稳流年",
                career=e_career,
                wealth=e_wealth,
                relationship=e_relationship,
                version="V6.0-Final"
            )
    
            # Auto-build narrative
            ctx.narrative_prompt = ctx.build_narrative_prompt()
            return ctx




        # === LuckEngine Proxy Methods ===
        # Delegate to internal LuckEngine for clean architecture

    def get_luck_timeline(self, profile_or_year, start_year_or_month=None, years_or_day=None,
                              hour=None, gender=None, num_steps=None):
            """
            [V6.0 Proxy] 生成包含大运信息的完整运势时间线
            支持两种调用方式：
            1. 新接口: get_luck_timeline(profile, start_year, years=12)
            2. 旧接口 (兼容): get_luck_timeline(birth_year, birth_month, birth_day, birth_hour, gender, num_steps=8)
    
            :return: 带大运信息的流年列表
            """
            from datetime import datetime
            import calendar
    
            # 检测调用方式
            if hasattr(profile_or_year, 'get_luck_pillar_at'):
                # 新接口: 传入的是 BaziProfile 对象
                profile = profile_or_year
                start_year = start_year_or_month
                years = years_or_day if years_or_day else 12
                birth_year = profile.birth_date.year if hasattr(profile, 'birth_date') and profile.birth_date else None
            else:
                # 旧接口: 传入的是出生年份等组件
                birth_year = profile_or_year
                birth_month = start_year_or_month
                birth_day = years_or_day
                birth_hour = hour or 12
                gender_val = gender or 1
                years = num_steps or 8
        
                try:
                    # 构造 BaziProfile
                    birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, 0)
                    profile = BaziProfile(birth_date, gender_val)
                    # 旧接口从当前年份开始
                    start_year = datetime.now().year
                except Exception as e:
                    return []  # 返回空列表表示失败
    
            # 公共逻辑：生成时间线
            timeline = []
            prev_luck = None
    
            for i in range(years):
                y = start_year + i
        
                # 获取当年大运 (使用 BaziProfile 的接口)
                current_luck = profile.get_luck_pillar_at(y)
        
                # 检测是否换运年
                is_handover = (prev_luck is not None and current_luck != prev_luck)
        
                # 计算年龄
                age = (y - birth_year) if birth_year else None
        
                # 使用 LuckEngine 获取流年干支
                year_ganzhi = self.luck_engine.get_year_ganzhi(y)
        
                timeline.append({
                    'year': y,
                    'age': age,
                    'year_pillar': year_ganzhi,
                    'stem': year_ganzhi[0] if year_ganzhi else None,
                    'branch': year_ganzhi[1] if len(year_ganzhi) > 1 else None,
                    'luck_pillar': current_luck,
                    'is_handover': is_handover,
                    'old_luck': prev_luck if is_handover else None,
                    'new_luck': current_luck if is_handover else None
                })
        
                prev_luck = current_luck
        
            return timeline


    def get_dynamic_luck_pillar(self, profile_or_year, year_or_month=None,
                                    day=None, hour=None, gender=None, target_year=None):
            """
            [V6.0 Proxy] 获取指定年份的动态大运干支
            支持两种调用方式：
            1. 新接口: get_dynamic_luck_pillar(profile, year)
            2. 旧接口 (兼容): get_dynamic_luck_pillar(birth_year, birth_month, birth_day, birth_hour, gender, target_year)
    
            :return: 大运干支 或 None
            """
            from datetime import datetime
    
            # 检测调用方式
            if hasattr(profile_or_year, 'get_luck_pillar_at'):
                # 新接口: 传入的是 BaziProfile 对象
                profile = profile_or_year
                year = year_or_month
                return profile.get_luck_pillar_at(year)
            else:
                # 旧接口: 传入的是出生年份等组件
                birth_year = profile_or_year
                birth_month = year_or_month
                birth_day = day
                birth_hour = hour or 12
        
                try:
                    # 构造 BaziProfile
                    birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, 0)
                    profile = BaziProfile(birth_date, gender or 1)
                    return profile.get_luck_pillar_at(target_year)
                except Exception as e:
                    return "计算异常"


