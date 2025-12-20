
from core.kernel import Kernel

class MeaningEngine:
    """
    Antigravity Meaning Engine - V24.0
    Translates Physics (Flux/State) into Meaning (Career/Wealth).
    Based on "Work" (Zuo Gong) and "Energy Capture".
    """
    def __init__(self, chart, flux_result):
        self.chart = chart
        self.flux = flux_result
        self.dm_stem = chart.get('day', {}).get('stem')
        self.god_map = self._build_god_map()
        
    def analyze(self):
        """
        Main Analysis Pipeline
        """
        work_modes = self._analyze_work_modes()
        wealth_data = self._calculate_wealth()
        macro_patterns = self._match_macro_patterns()
        
        report = {
            "work_modes": work_modes,
            "wealth_potential": wealth_data,
            "macro_patterns": macro_patterns,
            "summary": self._generate_summary(work_modes, wealth_data, macro_patterns)
        }
        return report

    def _build_god_map(self):
        """
        Maps every particle ID to its Ten God relative to DM.
        """
        if not self.dm_stem: return {}
        
        dm_elem = Kernel.STEM_PROPERTIES[self.dm_stem]['element']
        dm_pol = Kernel.STEM_PROPERTIES[self.dm_stem]['polarity']
        
        god_map = {}
        
        # Iterate particles in flux result
        for p in self.flux['particle_states']:
            p_char = p['char']
            p_id = p['id']
            
            # Determine Element & Polarity
            if "branch" in p_id:
                # Use main qi for branches
                core = Kernel.HIDDEN_STEMS.get(p_char, {})
                if not core: 
                    god_map[p_id] = "Unknown"
                    continue
                main_stem = max(core, key=core.get)
                elem = Kernel.STEM_PROPERTIES[main_stem]['element']
                pol = Kernel.STEM_PROPERTIES[main_stem]['polarity']
            else:
                elem = Kernel.STEM_PROPERTIES[p_char]['element']
                pol = Kernel.STEM_PROPERTIES[p_char]['polarity']
                
            god = self._get_god_name(dm_elem, dm_pol, elem, pol)
            god_map[p_id] = god
            
        return god_map

    def _get_god_name(self, dm_e, dm_p, me_e, me_p):
        e_list = ["Wood", "Fire", "Earth", "Metal", "Water"]
        
        # Get generation generation map
        gen_map = Kernel.ELEMENT_GENERATION
        
        relation = "Friend"
        if dm_e == me_e:
            relation = "Self"
        elif gen_map[dm_e] == me_e:
            relation = "Output"
        elif gen_map[me_e] == dm_e:
            relation = "Resource"
        else:
            # Check Wealth (Me controls X)
            # Me -> Output -> Wealth
            output = gen_map[dm_e]
            if gen_map[output] == me_e:
                relation = "Wealth"
            
            # Check Power (X controls Me)
            # Power -> Resource -> Me
            resource = gen_map[me_e] 
            if resource == dm_e:
                # Wait, X generates R, R generates Me. So X is Power? 
                # e.g. Metal -> Water -> Wood. Metal is Power to Wood. Correct.
                # Double check logic. 
                # Resource of Me is Water. Generator of Water is Metal. So X is Metal. Correct.
                relation = "Power" # Logic Error possibility: X generates Resource. X is Power? Yes.
                
                # Let's verify standard control cycle to be safe:
                # Wood controls Earth. Wood (Me). Earth (Wealth).
                # Wood -> Fire -> Earth. Correct.
                # Metal controls Wood. Metal (Power). Wood (Me).
                # Metal -> Water -> Wood. Correct.
                pass
            
            # If still Friend, check indices just in case of logic gap
            idx_dm = e_list.index(dm_e)
            idx_me = e_list.index(me_e)
            diff = (idx_me - idx_dm) % 5
            if diff == 2: relation = "Wealth"
            elif diff == 3: relation = "Power"

        # Polarity Check
        same_pol = (dm_p == me_p)
        
        # Ten Gods Name Map
        names = {
            "Self": ("BiJian", "JieCai"),      # Same Polarity, Digg
            "Output": ("ShiShen", "ShangGuan"),
            "Wealth": ("PianCai", "ZhengCai"),
            "Power": ("QiSha", "ZhengGuan"),
            "Resource": ("PianYin", "ZhengYin")
        }
        
        if relation in names:
            return names[relation][0] if same_pol else names[relation][1]
        return "Unknown"

    def _analyze_work_modes(self):
        """
        1. Four Dynamic Work Modes (四大做功模式)
        """
        modes = []
        particles = {p['id']: p for p in self.flux['particle_states']}
        logs = self.flux.get('log', [])
        
        # --- Mode 1: Balancing (Zhi Heng) ---
        # "Eating God controls Seven Killings" (Intellect capturing Power)
        # Check if QiSha exists and is being weakened/controlled by ShiShen
        has_qisha = False
        has_shishen = False
        
        for pid, p in particles.items():
            god = self.god_map.get(pid)
            if god == "QiSha" and p['amp'] > 10: has_qisha = True
            if god == "ShiShen" and p['amp'] > 10: has_shishen = True
            
        # Refined: Check if they are actually interacting? 
        # For macro definition, simultaneous presence of strong forces implies interaction structure.
        if has_qisha and has_shishen:
            modes.append({
                "type": "Zhi Heng (Balancing)",
                "desc": "ShiShen controlling QiSha (Intellect capturing Power). Potential for Authority.",
                "strength": 80 # Placeholder score
            })

        # --- Mode 2: Flow (Liu Tong) ---
        # "Output produces Wealth" (Skills -> Money)
        # Check logs for Flow from Output to Wealth elements
        # Or check generic synergy
        # Identify Output and Wealth Particles
        outputs = [pid for pid, god in self.god_map.items() if god in ["ShiShen", "ShangGuan"]]
        wealths = [pid for pid, god in self.god_map.items() if god in ["PianCai", "ZhengCai"]]
        
        flow_detected = False
        if outputs and wealths:
            # Check basic abundance first
            output_amp = sum(particles[pid]['amp'] for pid in outputs)
            wealth_amp = sum(particles[pid]['amp'] for pid in wealths)
            if output_amp > 15 and wealth_amp > 15:
                # Interpret as Flow Capacity
                modes.append({
                    "type": "Liu Tong (Flow)",
                    "desc": "Output generating Wealth (Skills converting to Money).",
                    "strength": min(output_amp, wealth_amp)
                })

        # --- Mode 3: Collision (Peng Zhang) ---
        # "Clashing open Tombs" (Explosive Release)
        tombs = ["辰", "戌", "丑", "未"]
        for p in particles.values():
            if p['char'] in tombs:
                # Check status for Rupture/Clash
                if "ShellRuptured" in p.get('status', []) or "StructureBroken" in p.get('status', []):
                     modes.append({
                        "type": "Collision (Peng Zhang)",
                        "desc": f"Tomb {p['char']} opened via Collision. Explosive energy release.",
                        "strength": 90
                    })

        # --- Mode 4: Entanglement (Jiu Chan) ---
        # "Punishment/Harm" (Work with Internal Friction)
        # Check for XiangXing (Shear Stress) or inferred Harm
        shear_count = 0
        for log in logs:
            if "Shear Stress" in log:
                shear_count += 1
        
        if shear_count > 0:
             modes.append({
                "type": "Entanglement (Jiu Chan)",
                "desc": f"Work achieved through Friction/Penalty ({shear_count} counts). Success comes with side effects.",
                "strength": 50
            })
            
        return modes

    def _calculate_wealth(self):
        """
        V31.0 - Unified Value Capture Protocol
        
        Axiom: Wealth is NOT just the Wealth Element. 
        It is the Net Mass of High-Energy Particles successfully CAPTURED and COLLAPSED by the Self.
        
        Pipeline:
        Step A: Source Detection (锁定矿源)
        Step B: Leverage Calculation (计算杠杆率)
        Step C: Friction Assessment (计算损耗)
        Step D: Storage Check (容器校验)
        """
        particles = {p['id']: p for p in self.flux['particle_states']}
        dm_stem_p = particles.get('day_stem')
        if not dm_stem_p: 
            return {"score": 0, "rating": "Unknown", "mode": "N/A"}
        
        dm_amp = dm_stem_p['amp']
        dm_health = dm_stem_p.get('health', 100.0)
        dm_strong = dm_amp >= 35  # Body strength threshold
        
        # ========== Step A: Source Detection (锁定矿源) ==========
        # Scan all particles with Energy > 40 (high-energy threshold)
        sources = {
            'wealth_ore': [],      # 财星 (Natural Mine)
            'power_ore': [],       # 七杀 (Risk Mine)
            'tech_ore': [],        # 食伤 (Technology Mine)
            'asset_ore': []        # 印星 (Asset Mine)
        }
        
        for pid, p in particles.items():
            god = self.god_map.get(pid)
            amp = p['amp']
            
            # Only consider high-energy particles (Energy > 40)
            if amp <= 40:
                continue
                
            if god in ["PianCai", "ZhengCai"]:
                sources['wealth_ore'].append({'id': pid, 'energy': amp, 'god': god})
            elif god in ["QiSha", "ZhengGuan"]:
                sources['power_ore'].append({'id': pid, 'energy': amp, 'god': god})
            elif god in ["ShiShen", "ShangGuan"]:
                sources['tech_ore'].append({'id': pid, 'energy': amp, 'god': god})
            elif god in ["ZhengYin", "PianYin"]:
                sources['asset_ore'].append({'id': pid, 'energy': amp, 'god': god})
        
        # ========== Step B: Leverage Calculation (计算杠杆率) ==========
        total_captured = 0.0
        profit_mode = "Unknown"
        leverage_details = []
        
        # Mode 1: Labor (日主克财) - Direct Control
        if sources['wealth_ore']:
            if dm_strong:
                leverage = 1.0
                mode_desc = "Labor Mode (身旺克财)"
            else:
                leverage = -0.5  # Weak body cannot control wealth
                mode_desc = "Overload (身弱财重)"
            
            for ore in sources['wealth_ore']:
                captured = ore['energy'] * leverage
                total_captured += captured
                leverage_details.append({
                    'source': ore['id'],
                    'mode': mode_desc,
                    'leverage': leverage,
                    'captured': captured
                })
            
            if dm_strong:
                profit_mode = "Asset Builder (资产型)"
        
        # Mode 2: Technology (食伤生财) - Tech Amplification
        if sources['tech_ore'] and sources['wealth_ore']:
            leverage = 1.5  # Technology multiplier
            mode_desc = "Technology Mode (食伤生财)"
            
            # Tech ore generates wealth through output
            for tech in sources['tech_ore']:
                # Technology converts to wealth with 1.5x efficiency
                captured = tech['energy'] * leverage * 0.7  # 70% conversion rate
                total_captured += captured
                leverage_details.append({
                    'source': tech['id'],
                    'mode': mode_desc,
                    'leverage': leverage,
                    'captured': captured
                })
            
            profit_mode = "Tech Entrepreneur (技术型)"
        
        # Mode 3: Power (食神制杀) - Risk Conversion (Venture Capital)
        has_shishen = any(self.god_map.get(pid) == "ShiShen" for pid in particles)
        if sources['power_ore'] and has_shishen:
            leverage = 3.0  # Highest leverage - converting risk to profit
            mode_desc = "Power Mode (食神制杀 - 风险转化)"
            
            for power in sources['power_ore']:
                # Converting chaos/risk into massive profit
                captured = power['energy'] * leverage
                total_captured += captured
                leverage_details.append({
                    'source': power['id'],
                    'mode': mode_desc,
                    'leverage': leverage,
                    'captured': captured
                })
            
            profit_mode = "Venture Capitalist (风投型)"
        
        # Mode 4: Dividend (印星流入) - Passive Income
        if sources['asset_ore']:
            leverage = 0.8  # Passive income, lower but stable
            mode_desc = "Dividend Mode (印星资产)"
            
            for asset in sources['asset_ore']:
                captured = asset['energy'] * leverage
                total_captured += captured
                leverage_details.append({
                    'source': asset['id'],
                    'mode': mode_desc,
                    'leverage': leverage,
                    'captured': captured
                })
            
            if profit_mode == "Unknown":
                profit_mode = "Dividend Receiver (红利型)"
        
        # ========== Step C: Friction Assessment (计算损耗) ==========
        friction_total = 0.0
        friction_details = []
        
        # Friction 1: Competition (比劫夺财)
        for pid, p in particles.items():
            god = self.god_map.get(pid)
            if god in ["JieCai", "BiJian"]:
                # Competition causes 30-50% loss depending on strength
                friction_rate = 0.3 if p['amp'] < 40 else 0.5
                friction = total_captured * friction_rate
                friction_total += friction
                friction_details.append({
                    'source': pid,
                    'type': 'Competition (比劫夺财)',
                    'rate': friction_rate,
                    'loss': friction
                })
        
        # Friction 2: Conflict (刑冲内耗)
        for pid, p in particles.items():
            if "ShearStress" in p.get('status', []) or "Clash" in p.get('status', []):
                # Conflict causes 20% overhead cost
                friction = total_captured * 0.2
                friction_total += friction
                friction_details.append({
                    'source': pid,
                    'type': 'Conflict (刑冲内耗)',
                    'rate': 0.2,
                    'loss': friction
                })
                break  # Only count once
        
        # ========== Step D: Storage Check (容器校验) ==========
        # Check if there's a Vault (库) or Strong Root (强根) to solidify wealth
        has_vault = False
        has_root = False
        storage_capacity = 0.0
        
        for pid, p in particles.items():
            if 'branch' in pid:  # Only branches can be vaults/roots
                # Check for vault status
                if "Vault" in p.get('status', []) or "ShellRuptured" in p.get('status', []):
                    has_vault = True
                    storage_capacity += p['amp'] * 0.5
                
                # Check for strong root (high energy branch)
                if p['amp'] >= 50:
                    has_root = True
                    storage_capacity += p['amp'] * 0.3
        
        # Calculate solidification rate
        if has_vault or has_root:
            solidification_rate = min(1.0, storage_capacity / 100.0)
            solidified_wealth = total_captured * solidification_rate
            dissipated_wealth = total_captured * (1 - solidification_rate)
            storage_status = "Solidified (固化为资产)"
        else:
            solidification_rate = 0.0
            solidified_wealth = 0.0
            dissipated_wealth = total_captured
            storage_status = "Dissipate (过路财)"
        
        # ========== Final Calculation ==========
        net_wealth = solidified_wealth - friction_total
        
        # Rating
        if net_wealth < 0:
            rating = "Debt / Struggle"
        elif net_wealth < 50:
            rating = "Modest"
        elif net_wealth < 100:
            rating = "Comfortable"
        elif net_wealth < 200:
            rating = "Wealthy"
        else:
            rating = "Tycoon"
        
        # Inferences
        inferences = []
        if profit_mode == "Venture Capitalist (风投型)":
            inferences.append("⚡ 食神制杀格局 - 通过解决危机获得暴利")
        if not (has_vault or has_root):
            inferences.append("⚠️ 缺乏库根 - 财富难以积累（过路财）")
        if friction_total > total_captured * 0.3:
            inferences.append("⚠️ 竞争损耗严重 - 需要减少内耗")
        if dm_amp < 30 and total_captured > 100:
            inferences.append("⚠️ 身弱财重 - 有财难守")
        
        return {
            "score": round(net_wealth, 2),
            "rating": rating,
            "mode": profit_mode,
            "components": {
                "total_captured": round(total_captured, 1),
                "friction": round(friction_total, 1),
                "solidified": round(solidified_wealth, 1),
                "dissipated": round(dissipated_wealth, 1),
                "net": round(net_wealth, 1)
            },
            "sources": sources,
            "leverage_details": leverage_details,
            "friction_details": friction_details,
            "storage": {
                "has_vault": has_vault,
                "has_root": has_root,
                "capacity": round(storage_capacity, 1),
                "solidification_rate": round(solidification_rate, 2),
                "status": storage_status
            },
            "inferences": inferences
        }

    def _match_macro_patterns(self):
        """
        3. Macro Dictionary
        """
        patterns = []
        particles = {p['id']: p for p in self.flux['particle_states']}
        
        # 1. Entrepreneur: QiSha (Risk) + ShiShen (Strategy)
        qisha_str = sum(p['amp'] for pid, p in particles.items() if self.god_map.get(pid) == "QiSha")
        shishen_str = sum(p['amp'] for pid, p in particles.items() if self.god_map.get(pid) == "ShiShen")
        
        if qisha_str > 20 and shishen_str > 15:
            patterns.append({
                "name": "Entrepreneurial Structure",
                "desc": "Combination of Risk-Taking (7K) and Strategy (EG). Suitable for business foundation.",
                "significance": "High"
            })
            
        # 2. Influencer: Output + Fire
        # User explicitly asked for "Output + Fire"
        fire_output_amp = 0.0
        for pid, p in particles.items():
            god = self.god_map.get(pid)
            if god in ["ShiShen", "ShangGuan"]:
                # Check element
                char = p['char']
                if "stem" in pid:
                    el = Kernel.STEM_PROPERTIES[char]['element']
                else: 
                     # Branch main
                     core = Kernel.HIDDEN_STEMS.get(char, {})
                     if core:
                         main = max(core, key=core.get)
                         el = Kernel.STEM_PROPERTIES[main]['element']
                     else: el = "Unknown"
                
                if el == "Fire":
                    fire_output_amp += p['amp']
        
        if fire_output_amp > 20:
             patterns.append({
                "name": "Digital Influencer / Fame",
                "desc": "Fire Output represents diffusion of information and visibility. Modern 'Net Celebrity' pattern.",
                "significance": "High"
            })
            
        return patterns

    def _generate_summary(self, modes, wealth, patterns):
        summary = []
        if modes:
            summary.append(f"Major Work Mode: {modes[0]['type']}")
        summary.append(f"Wealth Potential: {wealth['rating']} (Score: {wealth['score']})")
        if patterns:
            summary.append(f"Archetype: {patterns[0]['name']}")
        
        if wealth['inferences']:
            summary.append(f"Key Insight: {wealth['inferences'][0]}")
            
        return " | ".join(summary)

    def analyze_wealth_logic(self):
        """
        V27.1 Logic Trace Layer
        Generates a strict text-based accountability report for Wealth.
        """
        particles = {p['id']: p for p in self.flux['particle_states']}
        ledger = []
        
        # 1. Assign Roles & Calculate Net Contribution
        total_wealth_energy = 0.0
        
        roles = {
            "SOURCE": ["PianCai", "ZhengCai", "QiSha"], # Power is Source if controlled
            "TOOL": ["ShiShen", "ShangGuan", "PianYin", "ZhengYin"],
            "LEAK": ["JieCai"],
            "CONTAINER": ["Chen", "Xu", "Chou", "Wei"], # Store branches separately logic?
        }
        
        ledger_entries = []
        
        for pid, p in particles.items():
            god = self.god_map.get(pid, "Unknown")
            char = p['char']
            amp = p['amp']
            role = "NOISE"
            contribution = 0.0
            desc = god
            
            # Detect Role
            if god in roles["SOURCE"]:
                role = "SOURCE"
                # If QiSha but not controlled? Assuming controlled for now if tool exists.
                contribution = amp
            elif god in roles["TOOL"]:
                role = "TOOL"
                # Tool doesn't add energy directly, it enables capture. 
                # But for Ledger, we can show its 'Efficiency Value'
                contribution = amp * 0.5 
            elif god in roles["LEAK"]:
                role = "LEAK"
                contribution = -amp * 0.5
            elif p['type'] == 'branch' and char in ["辰", "戌", "丑", "未"]:
                # Tomb logic
                role = "CONTAINER"
                desc = f"{god} (Tomb)"
                # If it's a Wealth Tomb, high value
                contribution = amp * 0.8
            elif god == "BiJian":
                role = "NOISE" # Unless weak, then Helper. Assume Noise/Neutral default.
            
            # Refinement based on Interactions
            # If 7K (Source) is not controlled, it becomes Risk (Negative).
            if god == "QiSha":
                has_tool = any(self.god_map.get(oid) in ["ShiShen", "ShangGuan", "ZhengYin"] for oid in particles)
                if not has_tool:
                    role = "RISK"
                    contribution = -amp # Destructive
            
            # Format Ledger Entry
            # Style: Color based on contrib
            c_str = f"+{contribution:.1f}" if contribution > 0 else f"{contribution:.1f}"
            color = "green" if contribution > 0 else "red" if contribution < 0 else "gray"
            if role == "SOURCE": color = "gold"
            
            entry = {
                "label": f"[{self._get_pillar_name(pid)}·{char}]",
                "role": role,
                "god": desc,
                "desc": self._get_role_desc(role, god),
                "value_str": c_str,
                "color": color
            }
            ledger_entries.append(entry)
            
            if role in ["SOURCE", "CONTAINER"]:
                total_wealth_energy += max(0, contribution)
            elif role == "LEAK":
                total_wealth_energy += contribution # Negative
                
        # 2. Path Logic
        path = "Unknown"
        process = "No clear wealth path detected."
        # Heuristic Logic
        sources = [e for e in ledger_entries if e['role'] == "SOURCE"]
        tools = [e for e in ledger_entries if e['role'] == "TOOL"]
        
        if any(s['god'] == "QiSha" for s in sources) and any(t['god'] == "ShiShen" for t in tools):
            path = "[食神制杀格] (Intellect controlling Power)"
            process = "日主利用 **食神(工具)** 成功制衡了 **七杀(高能矿源)**，将其转化为有效权力/财富。"
        elif any(s['god'] in ["PianCai", "ZhengCai"] for s in sources):
             if any(t['god'] in ["ShiShen", "ShangGuan"] for t in tools):
                 path = "[食伤生财格] (Productivity generating Wealth)"
                 process = "日主利用 **食伤(工具)** 创造了价值，并成功流向 **财星(矿源)**。"
             elif any(t['god'] == "BiJian" for t in ledger_entries) and total_wealth_energy > 50:
                 path = "[身旺任财] (Strength carrying Wealth)"
                 process = "日主依靠自身 **强根(工具)** 直接担起了 **重财(矿源)**。"

        # 3. Conclusion - Use grading thresholds instead of hard-coded values
        # Thresholds: S级 > 200, A级 > 120, B级 > 60, D级 < 0 (proportional to energy scale)
        level = "普通 (Average)"
        if total_wealth_energy > 200: level = "S 级 (巨富)"
        elif total_wealth_energy > 120: level = "A 级 (富裕)"
        elif total_wealth_energy > 60: level = "B 级 (小康)"
        elif total_wealth_energy < 0: level = "D 级 (负债风险)"
        
        risk = "无显著风险"
        if any(e['role'] == "RISK" for e in ledger_entries):
            risk = "七杀无制，攻身之祸。"
        if any(e['role'] == "LEAK" for e in ledger_entries):
            risk = "比劫争夺，谨防破财。"

        return {
            "ledger": ledger_entries,
            "path_info": {"pattern": path, "process": process, "leverage": "High"},
            "conclusion": {"level": level, "mode": "Based on Structure", "risk": risk}
        }

    def _get_pillar_name(self, pid):
        if "year" in pid: return "年"
        if "month" in pid: return "月"
        if "day" in pid: return "日"
        if "hour" in pid: return "时"
        return "?"

    def _get_role_desc(self, role, god):
        if role == "SOURCE": return "高能矿源"
        if role == "TOOL": return "捕获工具"
        if role == "CONTAINER": return "财富仓库"
        if role == "LEAK": return "财富漏洞"
        return "普通"

    def analyze_career_power(self):
        """
        V30.0 Career & Power Analysis
        事业物理定义：系统负载能力分析 (Entropy Reduction Capacity)
        
        Returns:
            dict: {
                'load_analysis': {...},  # Step A: The Load
                'solution_mechanism': {...},  # Step B: The Solution
                'status': {...},  # Step C: The Status
                'verdict': str  # Final judgment
            }
        """
        # Step A: Identify The Load (官杀)
        load_particles = []
        total_load = 0.0
        load_type = "None"
        
        for p in self.flux['particle_states']:
            pid = p['id']
            if pid not in self.god_map:
                continue
            
            god = self.god_map[pid]
            
            if god == "ZhengGuan":  # 正官 - Static Load
                load_particles.append({
                    'char': p['char'],
                    'god': god,
                    'type': 'Static Load (Officer)',
                    'energy': p['amp'],
                    'desc': '常规责任、体制压力、稳定负载'
                })
                total_load += p['amp']
                if load_type == "None":
                    load_type = "Static"
            
            elif god == "QiSha":  # 七杀 - Dynamic Shock
                load_particles.append({
                    'char': p['char'],
                    'god': god,
                    'type': 'Dynamic Shock (Killings)',
                    'energy': p['amp'],
                    'desc': '突发危机、高压挑战、动态冲击'
                })
                total_load += p['amp']
                load_type = "Dynamic"
        
        # Step B: Identify Solution Mechanism
        solution_tools = []
        solution_type = "None"
        solution_strength = 0.0
        
        # First, add Day Master's own strength as baseline
        day_master_strength = 0.0
        for p in self.flux['particle_states']:
            if p['id'] == 'day_stem':
                day_master_strength = p['amp']
                break
        
        # Base solution strength = Day Master's own power
        solution_strength = day_master_strength * 0.5  # 50% of DM strength counts
        
        for p in self.flux['particle_states']:
            pid = p['id']
            if pid not in self.god_map:
                continue
            
            god = self.god_map[pid]
            
            # BiJian/JieCai - Self-Strength (身旺)
            if god in ["BiJian", "JieCai"]:
                solution_tools.append({
                    'char': p['char'],
                    'god': god,
                    'mechanism': 'Self-Strength (身旺)',
                    'energy': p['amp'],
                    'desc': '通过自身强大的能量场来直接承担压力。'
                })
                solution_strength += p['amp']
                if solution_type == "None":
                    solution_type = "Self-Strength"
            
            # 印 - Absorption
            elif god in ["ZhengYin", "PianYin"]:
                solution_tools.append({
                    'char': p['char'],
                    'god': god,
                    'mechanism': 'Absorption (融入体制)',
                    'energy': p['amp'],
                    'desc': '通过获得授权、融入体制来化解压力。稳定但创新性低。'
                })
                solution_strength += p['amp'] * 1.1  # Yin is very effective
                if solution_type == "None" or solution_type == "Self-Strength":
                    solution_type = "Absorption"
            
            # 食伤 - Counter-Strike
            elif god in ["ShiShen", "ShangGuan"]:
                solution_tools.append({
                    'char': p['char'],
                    'god': god,
                    'mechanism': 'Counter-Strike (技术方案)',
                    'energy': p['amp'],
                    'desc': '通过个人能力、技术创新来解决难题。高风险高回报。'
                })
                solution_strength += p['amp'] * 1.2  # Counter has bonus
                if solution_type in ["None", "Self-Strength"]:
                    solution_type = "Counter-Strike"
            
            # 财 - Support
            elif god in ["PianCai", "ZhengCai"]:
                solution_tools.append({
                    'char': p['char'],
                    'god': god,
                    'mechanism': 'Support (资源运作)',
                    'energy': p['amp'],
                    'desc': '通过资源调配、管理运作来换取地位。'
                })
                solution_strength += p['amp'] * 0.6  # Support is weaker
        
        # Step C: Determine Status (Pillar vs Consumable)
        # Logic: Can you handle the load?
        # Adjusted thresholds to be more realistic
        load_ratio = solution_strength / total_load if total_load > 0 else 999  # No load = infinite capacity
        
        if load_ratio > 0.8:
            status_type = "Pillar (支柱)"
            status_desc = "成功转化压力，成为系统的核心骨架。你拥有真正的权力。"
            status_icon = "🏛️"
            status_color = "gold"
        elif load_ratio > 0.5:
            status_type = "Load-Bearer (承重者)"
            status_desc = "能够承担责任，但余力不多。你有一定权力，但也很辛苦。"
            status_icon = "⚖️"
            status_color = "orange"
        else:
            status_type = "Consumable (耗材)"
            status_desc = "无法有效转化压力，被系统磨损。劳碌背锅，权力有限。"
            status_icon = "⚠️"
            status_color = "red"
        
        # Step D: Calculate Power Level (权力等级)
        power_level = self._calculate_power_level(
            load_type, total_load, solution_type, solution_strength, 
            load_ratio, load_particles, solution_tools
        )
        
        # Generate Verdict
        verdict = self._generate_career_verdict(load_type, load_particles, solution_type, solution_tools, status_type, load_ratio)
        
        return {
            'load_analysis': {
                'type': load_type,
                'total_energy': total_load,
                'particles': load_particles,
                'summary': f"承受 {load_type} 压力场，总负载 {total_load:.1f} eV"
            },
            'solution_mechanism': {
                'type': solution_type,
                'strength': solution_strength,
                'tools': solution_tools,
                'summary': f"采用 {solution_type} 机制，解决能力 {solution_strength:.1f} eV"
            },
            'status': {
                'type': status_type,
                'desc': status_desc,
                'icon': status_icon,
                'color': status_color,
                'load_ratio': load_ratio
            },
            'power_level': power_level,
            'verdict': verdict
        }
    
    def _calculate_power_level(self, load_type, total_load, solution_type, solution_strength, 
                               load_ratio, load_particles, solution_tools):
        """
        Calculate specific power level/rank
        
        Scoring system:
        - Base score = solution_strength
        - Bonus for high load_ratio
        - Bonus for 官印相生 (Officer + Seal)
        - Bonus for high total_load (bigger responsibility)
        """
        score = solution_strength
        
        # Bonus for handling load well
        if load_ratio > 1.5:
            score += 30  # Excellent capacity
        elif load_ratio > 1.0:
            score += 20  # Good capacity
        elif load_ratio > 0.8:
            score += 10  # Adequate capacity
        
        # Bonus for high total load (bigger stage)
        if total_load > 100:
            score += 25  # Major responsibility
        elif total_load > 70:
            score += 15  # Significant responsibility
        elif total_load > 40:
            score += 5  # Moderate responsibility
        
        # Bonus for 官印相生 (Officer + Seal synergy)
        has_officer = any(p['god'] in ['ZhengGuan', 'QiSha'] for p in load_particles)
        has_seal = any(t['god'] in ['ZhengYin', 'PianYin'] for t in solution_tools)
        if has_officer and has_seal:
            score += 25  # Classic power combination
        
        # Bonus for 杀印相生 (Killing + Seal - even stronger)
        has_qisha = any(p['god'] == 'QiSha' for p in load_particles)
        if has_qisha and has_seal:
            score += 10  # Extra bonus for taming chaos with authority
        
        # Determine rank based on score
        if score >= 250:
            rank_gov = "部级/省级 (Ministerial/Provincial)"
            rank_corp = "集团CEO/董事长 (Group CEO/Chairman)"
            level = "S级"
            desc = "顶级权力，影响一个行业或地区"
        elif score >= 180:
            rank_gov = "厅级/局级 (Bureau/Department Chief)"
            rank_corp = "上市公司总裁/事业部总经理 (Listed Co. President/Division GM)"
            level = "A级"
            desc = "高级管理者，掌控一个系统"
        elif score >= 120:
            rank_gov = "处级/科级 (Division/Section Chief)"
            rank_corp = "部门总监/分公司总经理 (Director/Branch GM)"
            level = "B级"
            desc = "中层骨干，管理一个部门"
        elif score >= 70:
            rank_gov = "副科/主任科员 (Deputy Section/Principal Staff)"
            rank_corp = "经理/主管 (Manager/Supervisor)"
            level = "C级"
            desc = "基层管理者，带领一个团队"
        else:
            rank_gov = "办事员/科员 (Staff/Clerk)"
            rank_corp = "员工/专员 (Employee/Specialist)"
            level = "D级"
            desc = "执行层，个人贡献者"
        
        return {
            'score': score,
            'level': level,
            'rank_government': rank_gov,
            'rank_corporate': rank_corp,
            'description': desc
        }
    
    def _generate_career_verdict(self, load_type, load_particles, solution_type, solution_tools, status_type, load_ratio):
        """Generate career verdict based on analysis"""
        
        # Special case 1: 七杀格 + 食神制杀
        has_qisha = any(p['god'] == 'QiSha' for p in load_particles)
        has_shishen = any(t['god'] == 'ShiShen' for t in solution_tools)
        
        if has_qisha and has_shishen and load_ratio > 0.8:
            return """
**特种兵式权威 (Special Forces Authority)**

你的命局是 **七杀格，食神高透制杀**。

**物理解读**：
- 你面对的是 **Dynamic Shock (七杀)** —— 最危险、最高能的社会压力。
- 你的解法是 **Counter-Strike (食神)** —— 用个人技术能力直接对抗。
- 结果：你成功驯服了最凶猛的野兽，获得了 **特种兵般的权威**。

**这意味着**：
- ❌ 你不是坐办公室的官僚（那是正官+正印的路线）。
- ✅ 你是能搞定最棘手麻烦的专家（危机处理、技术攻坚、特殊任务）。
- ✅ 你的权力来自于 **不可替代性**，而非职位等级。

**现实映射**：
特警队长、技术总监、项目救火队、创业核心、外科主刀医生。

**关键词**：高风险、高回报、技术权威、危机英雄。
"""
        
        # Special case 2: 正官 + 身旺/印 (传统仕途)
        has_zhengguan = any(p['god'] == 'ZhengGuan' for p in load_particles)
        has_self_strength = solution_type == "Self-Strength" or any(t['mechanism'] == 'Self-Strength (身旺)' for t in solution_tools)
        has_absorption = solution_type == "Absorption" or any(t['mechanism'] == 'Absorption (融入体制)' for t in solution_tools)
        
        if has_zhengguan and (has_self_strength or has_absorption) and load_ratio > 0.6:
            return """
**传统仕途 (Traditional Bureaucratic Path)**

你的命局是 **正官配身旺/印**，这是最经典的仕途组合。

**物理解读**：
- 你面对的是 **Static Load (正官)** —— 稳定的体制责任。
- 你的解法是 **Self-Strength/Absorption** —— 通过自身能量或体制授权来承担。
- 结果：你在系统内稳步上升，成为可靠的管理者。

**这意味着**：
- ✅ 你适合在成熟组织/政府体系内发展。
- ✅ 你的权力来自于 **职位等级** 和 **体制认可**。
- ✅ 稳定性高，但创新空间相对有限。

**现实映射**：
公务员、国企高管、大学教授、医院院长、军队军官。

**关键词**：稳定、体制内、等级权力、长期主义。
"""
        
        # General verdict based on status
        if status_type == "Pillar (支柱)":
            return f"""
**系统支柱 (System Pillar)**

你的负载能力比 ({load_ratio:.2f}) 表明你能轻松驾驭当前的社会压力。

你通过 **{solution_type}** 机制成功化解了 **{load_type}** 压力场，
成为了组织/系统中不可或缺的核心骨架。

**权力来源**：你解决了别人解决不了的问题。
**地位稳固度**：高 - 你是被需要的。
"""
        elif status_type == "Load-Bearer (承重者)":
            return f"""
**负重前行 (Load-Bearer)**

你的负载能力比 ({load_ratio:.2f}) 表明你能承担责任，但余力不多。

你通过 **{solution_type}** 机制勉强应对 **{load_type}** 压力场，
有一定权力，但也很辛苦。

**建议**：寻找更强的工具（提升技能/获得资源/争取授权）来提高负载能力。
"""
        else:
            return f"""
**系统耗材 (Consumable)**

你的负载能力比 ({load_ratio:.2f}) 表明你无法有效转化压力。

面对 **{load_type}** 压力场，你缺乏足够的 **{solution_type}** 工具，
导致被系统磨损，劳碌背锅，权力有限。

**风险**：长期处于这种状态会导致健康/财务问题。
**建议**：要么增强工具（学习/资源），要么降低负载（换赛道）。
"""
