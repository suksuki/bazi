import hashlib
import json
import os

class QuantumEngine:
    """
    Quantum Bazi V2.4 Physics Engine (Unified)
    Calculates E_pred (Energy Potential) based on W (Weights) and C (Couplings).
    Supports Dynamic Time-Variable (Da Yun / Liu Nian) with Full Elemental Interaction.
    """
    def __init__(self, params):
        self.params = params
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

    def _get_narrative(self, key):
        """Helper to fetch and format narrative string from config."""
        ev = self.narrative_config.get(key)
        if not ev: return f""
        return f"{ev['icon']}【{ev['title']}】{ev['desc']}（断语：{ev['verdict']}）"

    def _get_element(self, char):
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
        Core Calculation Logic.
        """
        # 1. Unpack Physics Params
        w_e_weight = self.params.get("w_e_weight", 1.0)
        f_yy = self.params.get("f_yy_correction", 1.0)
        
        cid = case_data.get('id', 0)
        sources = case_data.get('physics_sources', {})
        
        # Initialize Raw Energies (Static State)
        if sources and 'self' in sources:
            s = sources['self']
            raw_e_self = s.get('month_command', 0) + s.get('day_root', 0) + s.get('other_roots', 0) + s.get('stem_support', 0)
            raw_e_output = sources.get('output', {}).get('base', 2.0)
            raw_e_cai = sources.get('wealth', {}).get('base', 2.0)
            raw_e_guan_sha = sources.get('officer', {}).get('base', 1.0)
            raw_e_resource = sources.get('resource', {}).get('base', 1.0)
        else:
            # Fallback Mock
            raw_e_guan_sha = ((cid * 7) % 10) 
            raw_e_cai = ((cid * 5) % 9)
            raw_e_self = ((cid * 2) % 8) + 2 
            raw_e_output = ((cid * 3) % 8) 
            raw_e_resource = ((cid * 4) % 8)
            
            ws = case_data.get('wang_shuai', '身中和')
            if ws == '身弱': raw_e_self -= 3
            elif ws == '身旺': raw_e_self += 3
            elif '极弱' in ws or '从' in ws: raw_e_self = -5 

        # Narrative Storage
        narrative = []

        # --- DYNAMIC LAYER: Apply Time Modifiers to Raw Energy ---
        # This MUST happen BEFORE calculating final Career/Wealth scores
        dynamic_desc = ""
        
        if dynamic_context:
            year_str = dynamic_context.get('year', '')
            dm_char = case_data.get('day_master', '甲') # Default to Jia if missing
            dm_elem = self._get_element(dm_char) or 'wood'

            # Parse Annual Pillar
            y_stem = year_str[0] if len(year_str) > 0 else ''
            y_branch = year_str[1] if len(year_str) > 1 else ''
            
            y_stem_elem = self._get_element(y_stem)
            y_branch_elem = self._get_element(y_branch)
            
            # Apply Influence
            # We treat Stem as superficial trigger (fast, light) and Branch as root support (strong, heavy)
            
            def apply_boost(elem, magnitude, note):
                rel = self._get_relation(dm_elem, elem)
                nonlocal raw_e_self, raw_e_output, raw_e_cai, raw_e_guan_sha, raw_e_resource
                
                applied = False
                if rel == 'self': 
                    raw_e_self += magnitude
                    applied = True
                elif rel == 'output': 
                    raw_e_output += magnitude
                    applied = True
                elif rel == 'wealth': 
                    raw_e_cai += magnitude
                    applied = True
                elif rel == 'officer': 
                    raw_e_guan_sha += magnitude
                    applied = True
                elif rel == 'resource': 
                    raw_e_resource += magnitude
                    applied = True
                    
                if applied:
                    narrative.append(f"[{note}] {rel.title()} Energy {magnitude:+.1f}")

            if y_stem_elem: apply_boost(y_stem_elem, 1.5, f"Year Stem {y_stem}")
            if y_branch_elem: apply_boost(y_branch_elem, 3.0, f"Year Branch {y_branch}")
            
            # Da Yun Influence (Background Field)
            dy_str = dynamic_context.get('dayun', '')
            if len(dy_str) >= 2:
                d_stem_elem = self._get_element(dy_str[0])
                d_branch_elem = self._get_element(dy_str[1])
                if d_stem_elem: apply_boost(d_stem_elem, 1.0, "DaYun Stem")
                if d_branch_elem: apply_boost(d_branch_elem, 2.0, "DaYun Branch")

            # Interaction Logic (Clashes/Combines - Simplified for Energy Physics)
            # If Year Branch Clashes with Day Master Root? (Complex, simplify to Energy Damping)
            
            # Special Case: Water Overload
            if raw_e_guan_sha > 8.0 and raw_e_self < 2.0:
                 narrative.append(self._get_narrative("pressure_penalty"))
                 
        # --- CALCULATION OF POTENTIALS (Post-Dynamics) ---
        
        # Load Weights
        w_off = self.params.get("w_career_officer", 0.8)
        w_res = self.params.get("w_career_resource", 0.1)
        w_out_job = self.params.get("w_career_output", 0.0)
        k_ctl = self.params.get("k_control", 0.55)
        k_buf = self.params.get("k_buffer", 0.40)
        k_mutiny = self.params.get("k_mutiny", 1.8)
        
        # 1. Career
        e_career = (raw_e_guan_sha * w_off) + (raw_e_self * 0.2) + (raw_e_resource * w_res) + (raw_e_output * w_out_job)
        
        # Interactions
        if raw_e_guan_sha > 1.0 and raw_e_output > 1.0:
            if raw_e_self < -2.0 and raw_e_guan_sha > 4.0 and raw_e_output > 4.0:
                 e_career -= min(raw_e_guan_sha, raw_e_output) * k_mutiny # Mutiny
                 narrative.append(self._get_narrative("mutiny_penalty") or "⚠️ 伤官见官 (Mutiny)")
            else:
                 e_career += min(raw_e_guan_sha, raw_e_output) * k_ctl # Control
                 narrative.append(self._get_narrative("control_success") or "⚡ 食神制杀 (Control)")
        
        if raw_e_self < -2.0 and raw_e_guan_sha > 5.0:
             if raw_e_resource > 3.0:
                 e_career += min(raw_e_guan_sha, raw_e_resource) * k_buf # Buffer
             else:
                 e_career -= raw_e_guan_sha * 0.5 # Crushing Pressure

        # 2. Wealth
        w_cai = self.params.get("w_wealth_cai", 0.6)
        w_out = self.params.get("w_wealth_output", 0.4)
        k_capture = self.params.get("k_capture", 0.0)
        k_leak = self.params.get("k_leak", 0.87)
        k_clash = self.params.get("k_clash", 0.0) # Robbery
        
        e_wealth = (raw_e_cai * w_cai) + (raw_e_output * w_out)
        
        if raw_e_self > 4.0 and raw_e_cai > 1.0:
            e_wealth += (raw_e_self - 4.0) * 0.3 # Natural Capture Bonus
            if k_capture > 0: e_wealth += (raw_e_self - 5.0) * k_capture

        if raw_e_self < 0.0 and raw_e_output > 5.0:
            e_wealth -= (raw_e_output - raw_e_self) * k_leak # Leak
            
        if raw_e_self > 6.0 and raw_e_cai < 3.0:
             e_wealth -= (raw_e_self - raw_e_cai) * 0.5 # Robbery (Hardcoded penalty if not in k_clash)

        # 3. Relationship
        gender = case_data.get('gender', '男')
        e_spouse = raw_e_cai if "男" in gender else raw_e_guan_sha
        
        w_spouse = self.params.get("w_rel_spouse", 0.35)
        w_self = self.params.get("w_rel_self", 0.20)
        w_output = self.params.get("w_rel_output", 0.15)
        
        e_relationship = (w_spouse * e_spouse * 2.0) + (w_self * raw_e_self) + (w_output * raw_e_output)
        
        if raw_e_self > 6.0 and e_spouse < 4.0:
            e_relationship -= (raw_e_self - e_spouse) * 0.4 # Dominance/Clash
            
        e_relationship *= f_yy

        # Final Formatting
        full_desc = " ".join(narrative[-3:]) if narrative else "Energy Stable" 
        
        # Pillar Energies (Mock or Passed)
        pillar_energies = sources.get('pillar_energies', [0]*8)

        # Re-calc Ten Gods (Approximate based on new raw values)
        # We can't perfectly reconstruct exact split without detailed physics, so we approximate
        tg = {
            "bi_jian": raw_e_self * 0.5, "jie_cai": raw_e_self * 0.5,
            "shi_shen": raw_e_output * 0.6, "shang_guan": raw_e_output * 0.4,
            "pian_cai": raw_e_cai * 0.6, "zheng_cai": raw_e_cai * 0.4,
            "qi_sha": raw_e_guan_sha * 0.4, "zheng_guan": raw_e_guan_sha * 0.6,
            "pian_yin": raw_e_resource * 0.4, "zheng_yin": raw_e_resource * 0.6
        }

        return {
            "career": round(max(-10, min(10, e_career * w_e_weight)), 2),
            "wealth": round(max(-10, min(10, e_wealth * w_e_weight)), 2),
            "relationship": round(max(-10, min(10, e_relationship)), 2),
            "desc": full_desc, 
            "particles": {
                "self": round(raw_e_self, 1),
                "output": round(raw_e_output, 1),
                "wealth": round(raw_e_cai, 1),
                "officer": round(raw_e_guan_sha, 1),
                "resource": round(raw_e_resource, 1)
            },
            "ten_gods": tg,
            "pillar_energies": pillar_energies
        }
