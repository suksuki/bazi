import math
import random
from typing import Dict, List, Any, Tuple

class TemporalShuntingEngine:
    """
    MOD_16 Engine: Temporal Response & Strategic Intervention
    Focuses on 'Shunting Dynamics' - channeling structural stress through behavior/geo bypasses.
    """
    
    def __init__(self, day_master: str):
        self.day_master = day_master
        self.SAI_THRESHOLD = 2.0  # Singularity Point
        self.PULSE_DECAY = 1.2    # Behavioral damping factor
        
        # Base damping coefficients for behaviors (mock physics for V1)
        self.ACTION_DAMPING = {
            "STUDY": 0.4,       # Resource injection (印)
            "DONATION": 0.3,    # Wealth output (财)
            "TRAVEL": 0.2,      # Kinetic release (马)
            "MEDITATION": 0.25, # Void state (空)
            "NONE": 0.0
        }

    def scan_singularities(self, start_year: int = 2024, horizon_months: int = 120, baseline_sai: float = 1.0, birth_year: int = 1990, social_damping: float = 1.0, profile=None) -> Dict[str, Any]:
        """
        Scans timeline for Singularity Points (SAI > Threshold).
        Phase 4.0: Includes social_damping (Platform Impedance).
        Phase 5.0: Integrates BaziProfile for accurate Luck Pillar lookups.
        """
        from core.trinity.core.nexus.definitions import ArbitrationNexus
        
        singularities = []
        timeline = []
        
        # Bazi Plain Translation Map
        BAZI_TRANSLATION = {
            "OVERFLOW": {
                "title": "能级溢出",
                "plain": "官非动荡/名利波折",
                "desc": "岁运逢旺，火土燥热或金水泛滥，易因激进导致纠纷。"
            },
            "COLLAPSE": {
                "title": "结构坍塌",
                "plain": "根基动摇/财运压抑",
                "desc": "地支逢冲，原局气场失序，需注意长辈健康或财务缩水。"
            }
        }
        
        # Simulation parameters
        amp_year = 1.0
        amp_month = 0.5
        
        # Calculate full range: Birth -> Start + Horizon
        total_months = (start_year - birth_year) * 12 + horizon_months
        
        temp_singularities = []
        
        for t in range(total_months):
            # Absolute Time
            abs_year = birth_year + (t // 12)
            abs_month = (t % 12) + 1
            age = abs_year - birth_year
            
            # --- Physics Model V5.0: Real Pillar Interactions ---
            wave_val = 0.0
            interaction_boost = 0.0
            
            if profile:
                # Get actual pillars for this year
                luck_p = profile.get_luck_pillar_at(abs_year)
                annual_p = profile.get_year_pillar(abs_year)
                
                # Extract branches
                birth_pillars = profile.pillars
                day_branch = birth_pillars.get('day', 'XX')[1] if len(birth_pillars.get('day', '')) > 1 else ''
                luck_branch = luck_p[1] if len(luck_p) > 1 else ''
                annual_branch = annual_p[1] if len(annual_p) > 1 else ''
                
                # Check for clashes (high stress)
                chart_branches = [b[1] for k, b in birth_pillars.items() if len(b) > 1]
                
                for cb in chart_branches:
                    if ArbitrationNexus.CLASH_MAP.get(luck_branch) == cb:
                        interaction_boost += 0.8  # Luck clashes natal
                    if ArbitrationNexus.CLASH_MAP.get(annual_branch) == cb:
                        interaction_boost += 0.5  # Annual clashes natal
                
                # Luck-Annual clash
                if ArbitrationNexus.CLASH_MAP.get(luck_branch) == annual_branch:
                    interaction_boost += 0.6
                
                # Penalty check (simplified)
                if luck_branch in ArbitrationNexus.HARM_MAP and ArbitrationNexus.HARM_MAP.get(luck_branch) in chart_branches:
                    interaction_boost += 0.3
                
                wave_val = interaction_boost
            else:
                # Fallback: Placeholder sine wave (legacy)
                wave_val = amp_year * math.sin(2 * math.pi * t / 120) + \
                           amp_month * math.sin(2 * math.pi * t / 12)
            
            # Add noise
            random.seed(self.day_master + str(t))
            noise = random.lognormvariate(0, 0.1) * 0.2 if random.random() > 0.8 else 0
            
            # [PATCH] Social Damping Logic
            raw_sai = baseline_sai + abs(wave_val) + noise
            total_sai = raw_sai / social_damping
            
            # Event Classification
            evt_type = "NONE"
            assertion = ""
            plain_assertion = ""
            
            if total_sai > self.SAI_THRESHOLD:
                evt_type = "OVERFLOW" if wave_val > 0 else "COLLAPSE"
                trans = BAZI_TRANSLATION.get(evt_type, {})
                assertion = f"{abs_year}年: {trans.get('title')} (SAI={total_sai:.2f})"
                plain_assertion = f"{trans.get('plain')}: {trans.get('desc')}"
            
            timeline_node = {
                "t": t, 
                "year": str(abs_year),
                "month": str(abs_month),
                "age": age,
                "sai": round(total_sai, 4),
                "is_singularity": total_sai > self.SAI_THRESHOLD,
                "is_future": abs_year >= start_year,
                "type": evt_type,
                "assertion": assertion,
                "plain_assertion": plain_assertion
            }
            timeline.append(timeline_node)
            if timeline_node["is_singularity"]:
                temp_singularities.append(timeline_node)
        
        # --- Singularity Clustering (Only keep peak in contiguous blocks) ---
        if temp_singularities:
            clustered = []
            curr_cluster = [temp_singularities[0]]
            
            for i in range(1, len(temp_singularities)):
                # If gap is 1 month, it's the same block
                if temp_singularities[i]['t'] - temp_singularities[i-1]['t'] <= 1:
                    curr_cluster.append(temp_singularities[i])
                else:
                    # Find peak in curr_cluster
                    peak = max(curr_cluster, key=lambda x: x['sai'])
                    clustered.append(peak)
                    curr_cluster = [temp_singularities[i]]
            
            # Don't forget last cluster
            if curr_cluster:
                peak = max(curr_cluster, key=lambda x: x['sai'])
                clustered.append(peak)
            
            singularities = clustered
                
        return {"timeline": timeline, "singularities": singularities}

    def calibrate_model(self, feedback_data: List[Dict[str, Any]]):
        """
        Adjusts physics parameters based on user truth feedback.
        feedback_data: [{"year": 2018, "is_accurate": True}, ...]
        """
        # Simple feedback loop: 
        # If user says "Inaccurate" for a singularity (False Positive), raise Threshold (He tougher).
        # If user says "Inaccurate" for non-singularity (False Negative - not implemented in this simplified UI yet), lower Threshold.
        
        for fb in feedback_data:
            if not fb.get("is_accurate", True):
                # User denies the predicted stress
                self.SAI_THRESHOLD *= 1.05 # Increase threshold by 5%
                self.PULSE_DECAY *= 1.02   # Faster decay
                
        # Clamp
        self.SAI_THRESHOLD = min(3.0, max(1.5, self.SAI_THRESHOLD))
        
        return {
            "new_threshold": self.SAI_THRESHOLD,
            "new_decay": self.PULSE_DECAY
        }

    def simulate_intervention(self, current_sai: float, action_type: str, geo_factor: float, social_damping: float = 1.0) -> Dict[str, float]:
        """
        Calculates the Shunted SAI.
        Phase 4.0: Social Damping inclusion.
        Input 'current_sai' is assumed to be the ALREADY DAMPED peak value from scan_singularities.
        Interventions (Action/Geo) provide additional SUBTRACTIVE reduction.
        """
        # Base efficiency
        efficiencies = {"STUDY": 0.5, "DONATION": 0.4, "TRAVEL": 0.6, "MEDITATION": 0.3, "NONE": 0.0}
        R_action = efficiencies.get(action_type, 0.0)
        
        # Intervention boost (Subtractive damping on the damped signal)
        action_reduction = R_action * self.PULSE_DECAY
        geo_reduction = math.log10(geo_factor + 0.1) * 0.5 
        
        final_sai = current_sai - action_reduction - geo_reduction
        final_sai = max(0.2, final_sai) # Ground state
        
        return {
            "initial_sai": round(current_sai, 4),
            "final_sai": round(final_sai, 4),
            "reduction_pct": round((current_sai - final_sai) / current_sai * 100, 2) if current_sai > 0 else 0
        }

    def sensitivity_search(self, peak_sai: float, social_damping: float = 1.0) -> List[Dict[str, Any]]:
        """
        Finds optimal paths considering social_damping.
        Returns bilingual labels and recommendations.
        """
        options = []
        # Extended labels for UI display
        act_labels = {
            "STUDY": "📚 学习/印星 (Resource)",
            "DONATION": "💸 布施/财星 (Wealth)",
            "TRAVEL": "✈️ 迁移/马星 (Kinetic)",
            "MEDITATION": "🧘 闭关/空亡 (Void)",
            "NONE": "无干预 (None)"
        }
        geo_labels = {
            "Local": "本地场 (Local)",
            "Sanctuary": "避风港 (Sanctuary/High K)",
            "Hazard": "风险区 (Hazard/Low K)"
        }
        
        actions = ["STUDY", "DONATION", "TRAVEL", "MEDITATION", "NONE"]
        geos = {"Local": 1.0, "Sanctuary": 2.0, "Hazard": 0.5}
        
        for act in actions:
            for g_name, g_k in geos.items():
                metrics = self.simulate_intervention(peak_sai, act, g_k, social_damping)
                options.append({
                    "action": act,
                    "action_label": act_labels.get(act, act),
                    "geo": g_name,
                    "geo_label": geo_labels.get(g_name, g_name),
                    "geo_k": g_k,
                    "metrics": metrics
                })
        
        # Sort by final SAI
        options.sort(key=lambda x: x['metrics']['final_sai'])
        
        # Add synthesized recommendation string to top options
        for opt in options:
            if opt['metrics']['final_sai'] < 2.0:
                s_text = f"建议采取【{opt['action_label']}】行为，并寻找【{opt['geo_label']}】环境进行能量对冲，预计可将应力降至 {opt['metrics']['final_sai']:.2f} 的安全水平。"
            else:
                s_text = f"单一干预【{opt['action_label']}】不足以完全化解，建议叠加地理或社交阻尼调节。"
            opt['recommendation'] = s_text
            
        return options[:5] # Return top 5
