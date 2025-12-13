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
            elif is_follow: raw_e_self = -8 

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

                        # V2.8 Logic 0: Earth Amnesty (土之赦免)
                        # Clashes/Harms between Earth branches are often "Opening the Treasury", not destruction.
                        enable_earth_amnesty = fp.get('enable_earth_amnesty', True)
                        if enable_earth_amnesty and b1 in EARTH_BRANCHES and b2 in EARTH_BRANCHES:
                            narrative_events.append({
                                "card_type": "mountain_alliance",
                                "level": "rare",
                                "title": "土之赦免 (Amnesty)",
                                "desc": f"Earth clash ({b1}-{b2}) opens the treasury instead of destroying it.",
                                "score_delta": "Ignored",
                                "animation_trigger": "earth_tremor"
                            })
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
