import hashlib
import json
import os
from lunar_python import Solar, Lunar
from collections import Counter
from core.constants import GRAVE_TREASURY_CONFIG, HIDDEN_STEMS_MAP
from core.interaction_service import InteractionService

class QuantumEngine:
    """
    Quantum Bazi V2.4 Physics Engine (Unified)
    Calculates E_pred (Energy Potential) based on W (Weights) and C (Couplings).
    Supports Dynamic Time-Variable (Da Yun / Liu Nian) with Full Elemental Interaction.
    """
    def __init__(self, params=None):
        # Allow default params loading if None
        if params is None:
            params = self._load_default_params()
            
        self.params = params
        self.flat_params = self._flatten_params(params)
        
        
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
        
        # V3.0 Sprint 3: Wealth Logic
        self.WEALTH_MAP = {
            'wood': 'earth',
            'fire': 'metal',
            'earth': 'water',
            'metal': 'wood',
            'water': 'fire'
        }
        self.TOMB_ELEMENTS = {
            '辰': 'water', # Water Tomb
            '戌': 'fire',  # Fire Tomb
            '丑': 'metal', # Metal Tomb
            '未': 'wood'   # Wood Tomb
        }

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
    def get_hidden_stems(self, branch):
        """
        V3.0: Retrieve the internal microstructure of an Earthly Branch.
        Returns the Main Qi, Residual Qi, and Tomb Gas (if applicable).
        """
        return HIDDEN_STEMS_MAP.get(branch, {})

    def _is_wealth_treasury(self, day_master_element: str, treasury_branch: str) -> bool:
        """
        V3.0: Check if the opened treasury is the user's Wealth Treasury.
        """
        if not day_master_element: return False
        dm_elem = day_master_element.lower()
        wealth_element = self.WEALTH_MAP.get(dm_elem)
        tomb_content = self.TOMB_ELEMENTS.get(treasury_branch)
        
        # Special Logic for Wood DM: Earth is Wealth. 
        # Chen/Xu/Chou/Wei are all Earth branches partially.
        # But specifically, Dragon(Chen) and Dog(Xu) are the main "Pulse" of Earth clashing in water/fire cycles.
        # Simplified V3.0: If Wood DM, and treasury is one of the 4 Earths, treat as potential wealth source interaction.
        if dm_elem == 'wood' and treasury_branch in self.TOMB_ELEMENTS:
            # But the user spec says "Wood DM -> Wealth in Chen/Xu". 
            # Let's stick to strict user spec for Sprint 3?
            # User spec: "Wood DM -> Wealth in Chen/Xu/Chou/Wei (Earth is Wealth)".
            return True
            
        return wealth_element == tomb_content

    def scan_vault_state(self, branch, global_energy_map):
        """
        V3.0: Determine if a Vault is Alive (Vault) or Dead (Tomb)
        Based on the global energy of the stored element.
        """
        if branch not in self.VAULT_MAPPING: return "UNKNOWN"
        target_element = self.VAULT_MAPPING[branch]['element']
        energy_level = global_energy_map.get(target_element, 0)

        # Core Threshold: > 3.0 implies sufficient Qi to be a usable Vault
        if energy_level > 3.0:
            return "VAULT" # Alive, Bank Vault
        else:
            return "TOMB"  # Dead, Grave

    def process_quantum_tunneling(self, branch, energy_map):
        """
        V3.0: Handle the 'Opening' or 'Breaking' of a Storehouse.
        Returns (bonus_score, narrative_card)
        """
        vault_state = self.scan_vault_state(branch, energy_map)
        target_element = self.VAULT_MAPPING[branch]['element']
        e_inside = energy_map.get(target_element, 0)
        
        # Determine 10 God Type of the Vault for Narrative
        # (This context requires knowing DM, but for now we focus on physics)
        
        if vault_state == "VAULT":
            # Scenario A: Open the Vault (Quantum Tunneling)
            # Impact: Massive Energy Release
            bonus = e_inside * 2.0 # Critical Hit
            
            narrative = {
                "card_type": "vault_open",
                "level": "legendary",
                "title": f"🚪 墓库洞开 ({branch})",
                "desc": f"Quantum tunneling releases pent-up {target_element.title()} energy!",
                "score_delta": f"+{round(bonus, 1)} Wealth/Career",
                "animation_trigger": "gold_explosion"
            }
            return bonus, narrative
        
        else:
            # Scenario B: Break the Tomb (Structural Collapse)
            # Impact: Destruction of Roots
            penalty = -5.0 
            
            narrative = {
                "card_type": "tomb_break",
                "level": "danger",
                "title": f"⚰️ 根基崩塌 ({branch})",
                "desc": f"Protective walls collapse. Weak {target_element.title()} energy dissipates.",
                "score_delta": "-5.0 Structure",
                "animation_trigger": "rubble_collapse"
            }
            return penalty, narrative

    def analyze_year_interaction(self, birth_chart, year_branch):
        """
        V3.0 New: Analyze interaction between Annual Branch and Birth Chart (Treasury Opening Detection)
        """
        # Ensure birth_chart has the expected structure. 
        # Assuming birth_chart is a dict with keys like 'year_pillar', etc. containing strings like "甲子"
        # We need to extract the branch (2nd char) safety.
        try:
            chart_branches = {
                'year': birth_chart.get('year_pillar', '  ')[1],
                'month': birth_chart.get('month_pillar', '  ')[1],
                'day': birth_chart.get('day_pillar', '  ')[1],
                'hour': birth_chart.get('hour_pillar', '  ')[1]
            }
        except IndexError:
            # Fallback if pillars are malformed
            return []
        
        # Call Interaction Service
        interaction_service = InteractionService() 
        openings = interaction_service.detect_treasury_openings(year_branch, chart_branches)
        
        return openings

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
            # Fallback Mock
            raw_e_guan_sha = ((cid * 7) % 10) 
            raw_e_cai = ((cid * 5) % 9)
            raw_e_self = ((cid * 2) % 8) + 2 
            raw_e_output = ((cid * 3) % 8) 
            raw_e_resource = ((cid * 4) % 8)
            
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
                        is_earth_clash = (b1 in self.VAULT_MAPPING and b2 in self.VAULT_MAPPING and 
                                         ((b1, b2) in self.CLASH_PAIRS or (b2, b1) in self.CLASH_PAIRS))
                        
                        if is_earth_clash:
                            # Process EACH side of the clash as a potential Vault opening
                            # Loop via set to handle duplicate branch case safely (though rare in collision pair)
                            for branch_key in [b1, b2]:
                                bonus, event = self.process_quantum_tunneling(branch_key, element_map)
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
from core.quantum_engine import QuantumEngine
from lunar_python import Solar
from collections import Counter

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
        
        # 2. Lunar Python Calculation
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
    
    # Weights
    WEIGHT_MONTH_COMMAND = 0.40 # Month Branch is key
    WEIGHT_DAY_BRANCH = 0.15
    WEIGHT_STEM = 0.10
    WEIGHT_BRANCH = 0.05
    
    month_branch = bazi[1][1]
    
    # 1. Month Command (Ling)
    mb_elem = self._get_element(month_branch)
    rel = self._get_relation(dm_elem, mb_elem)
    
    is_same_group = (rel == 'self' or rel == 'resource')
    if is_same_group: score += 40
    
    # 2. Iterate all chars
    total_support = 0
    total_oppose = 0
    
    for idx, pillar in enumerate(bazi):
        stem, branch = pillar[0], pillar[1]
        
        # Stem
        if idx != 2: # Skip DM itself
            s_elem = self._get_element(stem)
            s_rel = self._get_relation(dm_elem, s_elem)
            if s_rel in ['self', 'resource']: total_support += 10
            else: total_oppose += 10
            
        # Branch
        b_elem = self._get_element(branch)
        b_rel = self._get_relation(dm_elem, b_elem)
        
        w = 1.0
        if idx == 1: w = 2.0 # Month branch weighted double in raw count too? Or simplified.
        
        if b_rel in ['self', 'resource']: total_support += (10 * w)
        else: total_oppose += (10 * w)
        
    final_score = score + total_support
    
    # Thresholds (Simplified)
    # A standard balanced chart axis is around 40-50% strength? 
    # Let's say arbitrary score:
    # If Support > Oppose -> Strong
    
    strength = "Strong" if (final_score > total_oppose) else "Weak"
    
    # Adjustment for Month Command
    if is_same_group and (final_score + 10 > total_oppose): strength = "Strong"
    
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

# Dynamically add methods to the class
QuantumEngine.calculate_chart = calculate_chart
QuantumEngine._evaluate_wang_shuai = _evaluate_wang_shuai
QuantumEngine._determine_favorable = _determine_favorable
QuantumEngine.get_elements_for_year = get_elements_for_year

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

QuantumEngine._load_default_params = _load_default_params

def calculate_year_score(self, year_pillar: str, favorable_elements: list, unfavorable_elements: list, birth_chart: dict = None) -> tuple:
    """
    V3.0 Core Algorithm: Calculate Year Luck Score with 'Cover Head/Cut Feet' logic AND Treasury Mechanics.
    Returns (score, details_list)
    """
    if not year_pillar or len(year_pillar) < 2:
        return 0.0, ["Invalid Pillar"]
        
    stem = year_pillar[0]
    branch = year_pillar[1]
    
    # Get elements (lowercase)
    stem_element = self._get_element(stem)
    branch_element = self._get_element(branch)
    
    if not stem_element or not branch_element:
        return 0.0, ["Unknown Elements"]
        
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
    if birth_chart:
        # 1. Detect Interaction
        interaction_results = self.analyze_year_interaction(birth_chart, branch)
        
        multiplier = 1.0
        bonus_points = 0.0
        
        # Get DM Element
        dm_char = birth_chart.get('day_master')
        dm_elem = self._get_element(dm_char)
        
        for status in interaction_results:
            if status.is_open:
                # 2. Check if Wealth Treasury
                if self._is_wealth_treasury(dm_elem, status.treasury_element):
                    # 💰 JACKPOT
                    multiplier = 2.0
                    bonus_points += 20.0
                    details.append(f"💰 财库[{status.treasury_element}]大开！(Vault Open)")
                    # V3.1: We might want to check if the Wealth Element inside is actually Favorable!
                    # If Wealth is Unfavorable (Wealth Burden), opening it might be bad.
                    # But per Sprint 3 instructions: "Just Multiplier".
                else:
                    details.append(f"🔓 杂气库[{status.treasury_element}]开启")
                    bonus_points += 2.0 # Small bonus for activity
        
        final_score = (base_score * multiplier) + bonus_points

    return round(final_score, 2), details

QuantumEngine.calculate_year_score = calculate_year_score
