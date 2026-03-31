
import math

class SSEPQuantumPhysics:
    """
    [SSEP] Supersymmetric Energy Potential Physics Engine
    Kernel Version: V17.0.0-Alpha
    """
    
    @staticmethod
    def calculate_zero_resistance_state(chart, main_energy_type):
        """
        Calculates the superconducting efficiency (Zero Resistance State).
        Returns: Efficiency (0.0 - 1.0), IsSuperconducting (Bool)
        """
        # Placeholder logic for V17.0.0 Init
        # Real logic will involve Purity Operator and Interference check
        return 0.99, True

    @staticmethod
    def audit_ceqs_transmutation(chart, month_branch_weight=None):
        """
        [CEQS] Chemical/Quantum Transmutation Audit.
        Detects True Transmutation patterns (Jia-Ji, Yi-Geng, etc.) and calculates Quantum Purity.
        
        Args:
            chart: List of tuples [(Stem, Branch), ...]
            month_branch_weight: Dict or List of weights for the month branch (optional context)
        """
        stems = [s for s, b in chart] # Use ALL stems (Natal + Luck + Annual) to detect Pairs
        if len(chart) < 2: return None
        month_branch = chart[1][1]
        
        # Transmutation Definitions
        # Pair -> (Target Element, Impurity_Controller[Clash], Impurity_Drain[Leak])
        TRANS_MAP = {
            frozenset(['甲', '己']): {'target': '土', 'imp': ['木'], 'drain': ['金']}, # Jia-Ji -> Earth (Fear Wood, Metal drains?) Actually Metal controls Wood, but here we focus on Purity. High purity means NO Wood. Metal might be OK as it clears Wood, but too much Metal drains Earth? Simplified: Impurity=Wood.
            frozenset(['乙', '庚']): {'target': '金', 'imp': ['火'], 'drain': ['水']}, # Yi-Geng -> Metal (Fear Fire)
            frozenset(['丙', '辛']): {'target': '水', 'imp': ['土'], 'drain': ['木']}, # Bing-Xin -> Water (Fear Earth)
            frozenset(['丁', '壬']): {'target': '木', 'imp': ['金'], 'drain': ['火']}, # Ding-Ren -> Wood (Fear Metal)
            frozenset(['戊', '癸']): {'target': '火', 'imp': ['水'], 'drain': ['土']}, # Wu-Gui -> Fire (Fear Water)
        }
        
        # 1. Detect Pairs
        active_trans = None
        for pair_set, meta in TRANS_MAP.items():
            # Check if both stems in pair are present in Natal Stems
            # Simplified check: Just need at least one instance of each? Or specifically DM-Month/DM-Year?
            # Standard: DM + Neighbor. We check generic presence for Alpha.
            p_list = list(pair_list for pair_list in pair_set)
            if all(s in stems for s in p_list):
                active_trans = meta
                active_trans['pair'] = "+".join(p_list)
                break
        
        if not active_trans:
             return {"is_transmuted": False, "reason": "No Pair"}

        # 2. Check Month Command (Field Excitation)
        # Simplified: Month branch element must match Target
        # This requires an Element Mapper. We use a simple lookup for Alpha.
        # EARTH_BR = [辰, 戌, 丑, 未]. Note: Month specific logic applies.
        # For this Alpha, we assume the caller ensures the 'field' is correct or we check a simple map.
        # Let's assume passed validation for now or check basic month affinity.
        
        # 3. Impurity Scan (Scan entire chart for Anti-Frequency)
        target = active_trans['target']
        impurities = active_trans['imp'] # Phase Cancellation (Resistance)
        drains = active_trans['drain']   # Phase Damping (Reactance)
        
        total_resistance = 0.0 # Real Part (Destructive)
        total_damping = 0.0    # Imaginary Part (Leaking)
        details = []
        
        # Simple Element Mapper for Alpha (Full version relies on Nexus)
        E_MAP = {
            '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
            '寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金', '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土' 
        }
        
        for i, (s, b) in enumerate(chart):
            # Check Stem
            se = E_MAP.get(s, '')
            # Skip if stem is part of the reacting pair (transmuting agents)
            if s not in active_trans['pair']:
                if se in impurities:
                    stress = 0.2 if i != 2 else 0.5 
                    total_resistance += stress
                    details.append(f"Resistance Stem {s}({se}) at {i}")
                elif se in drains:
                    damping = 0.1 # Minor damping
                    total_damping += damping
                    details.append(f"Damping Stem {s}({se}) at {i}")
            
            # Check Branch
            be = E_MAP.get(b, '')
            if be in impurities:
                total_resistance += 0.3
                details.append(f"Resistance Branch {b}({be}) at {i}")
            elif be in drains:
                total_damping += 0.15
                details.append(f"Damping Branch {b}({be}) at {i}")

        # 4. Calculate Purity (Complex Impedance Model)
        # Purity = 1.0 - (Real_R + Imag_X)
        # In Beta, we can weight them differently. For now linear sum.
        total_stress = total_resistance + total_damping
        purity = max(0.0, 1.0 - total_stress)
        
        # 5. Phase Transition Verdict
        state = "HIGH_RESISTANCE"
        if purity >= 0.9:
            state = "SUPERCONDUCTING (Zero Resistance)"
        elif purity >= 0.7:
             state = "SEMICONDUCTING (Mixed)"
        else:
             state = "BLOCKED (Phase Cancelled)"

        return {
            "is_transmuted": True,
            "transmuted_target": target,
            "pair": active_trans['pair'],
            "purity": f"{purity:.2f}",
            "resistance_real": total_resistance,
            "damping_imag": total_damping,
            "phase_transition": state,
            "details": details
        }

    @staticmethod
    def audit_two_element_imaging(chart):
        """
        [SSLC] Two Element Imaging Audit (Supersymmetric Resonance).
        Detects dynamic balance of two dominant forces (e.g. Water/Wood, Metal/Wood).
        Criteria: Two elements control > 80% of energy, balanced within 40-60 ratio.
        """
        # 1. Element Histogram
        # Simplified Element Mapper (Duplicated for beta independence, ideally centralized)
        E_MAP = {
            '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
            '寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金', '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土' 
        }
        counts = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        total_mass = 0.0
        
        for s, b in chart:
            e_s = E_MAP.get(s, '')
            if e_s: 
                counts[e_s] += 1.0
                total_mass += 1.0
            e_b = E_MAP.get(b, '')
            if e_b: 
                counts[e_b] += 1.2 # Branch slightly heavier
                total_mass += 1.2
                
        # 2. Identify Top 2 Elements
        sorted_elems = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        e1, w1 = sorted_elems[0]
        e2, w2 = sorted_elems[1]
        
        combined_ratio = (w1 + w2) / max(1.0, total_mass)
        
        # 3. Supersymmetry Check
        # Threshold: Two elements hold > 80% of mass
        if combined_ratio < 0.75: # Relaxed for Beta
             return {"is_imaging": False, "reason": "Energy Dispersed", "combined_ratio": f"{combined_ratio:.2f}"}

        # Balance Check: w2 / w1 > 0.4 (Not too lopsided)
        balance_ratio = w2 / max(0.1, w1)
        symmetry_score = 1.0 - abs(w1 - w2) / (w1 + w2)
        
        state = "ASYMMETRIC"
        if balance_ratio > 0.6:
            state = "PERFECT_SYMMETRY"
        elif balance_ratio > 0.35:
            state = "QUASI_SYMMETRY"
        else:
            return {"is_imaging": False, "reason": "Dominant Monopole", "symmetry": f"{symmetry_score:.2f}"}

        # 4. Resonance Mode (Generative vs Opposing)
        # Check relationship between E1 and E2
        # Simple map: Wood->Fire, Fire->Earth...
        # We need a generic checker. 
        # For Beta, we just label the pair.
        
        return {
            "is_imaging": True,
            "elements": f"{e1}+{e2}",
            "symmetry_score": f"{symmetry_score:.2f}",
            "resonance_mode": state,
            "energy_share": f"{combined_ratio:.2f}"
        }

    @staticmethod
    def audit_evhz_black_hole(chart):
        """
        [EVHZ] Event Horizon Audit (Black Hole Singularity).
        Detects Extreme Monopoles (True Follow/Zuan Wang).
        Criteria: Dominant Element > 90% Mass. Resistance < 5%.
        """
        # 1. Element Histogram (Alpha Mapper)
        E_MAP = {
            '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
            '寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金', '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土' 
        }
        counts = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        total_mass = 0.0
        
        for s, b in chart:
            e_s = E_MAP.get(s, '')
            if e_s: 
                counts[e_s] += 1.0
                total_mass += 1.0
            e_b = E_MAP.get(b, '')
            if e_b: 
                counts[e_b] += 1.5 # Branches heavier in mass model
                total_mass += 1.5
                
        # 2. Identify Dominant Singularity
        sorted_elems = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        dom_e, dom_w = sorted_elems[0]
        
        # Schwarzschild Radius Threshold (Alpha: 90%)
        mass_ratio = dom_w / max(1.0, total_mass)
        
        # 3. Resistance Scan (Alien Energy)
        # Any element that CLASHES or DRAINS the dominant is resistance?
        # Actually for 'True Follow', Draining (Output) is usually allowed/good. 
        # Resistance = Clashing (Countering) or consuming (if weak).
        # For Alpha EVHZ, we simpler define Resistance as "Everything else that isn't Output".
        # Let's keep it simple: Resistance = (Total - Dominant - Output).
        # Actually, let's just use "Non-Dominant Ratio" for raw singularity for now.
        
        # Refined EVHZ logic:
        # If Mass Ratio > 0.90 -> Singularity Formed.
        # If Mass Ratio > 0.80 -> Accretion Disk (Turbulent).
        
        state = "NORMAL_SPACE"
        if mass_ratio >= 0.90:
            state = "SINGULARITY (True Black Hole)"
        elif mass_ratio >= 0.75:
            state = "ACCRETION_DISK (Fake/Turbulent)"
            
        return {
            "dominant_element": dom_e,
            "mass_ratio": f"{mass_ratio:.2f}",
            "schwarzschild_state": state,
            "is_black_hole": (mass_ratio >= 0.90)
        }
