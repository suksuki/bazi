import numpy as np
import json
from learning.db import LearningDB

class Vectorizer:
    """
    Antigravity Engine V2.0 - Core Vectorizer
    
    Transforms Bazi Charts into the '3D Mesh Quantum Field' representation.
    Calculates Energy Potential (E_energy) and Coupling Strength (C_coupling).
    """
    def __init__(self, use_db_weights=True):
        self.db = LearningDB()
        
        # --- Physics Constants (Initial Priors / Default Heuristics) ---
        
        # 1. Potential Energy Sources (E_god)
        self.W_E = {
            "month_command": 4.0,  # 月令 (Time Resonance)
            "root_main": 3.0,      # 通根/主气 (Grounding)
            "birth_support": 1.0,  # 得生 (Catalyst)
            "same_element": 0.5    # 比劫 (Support)
        }
        
        # 2. Coupling Factors (C_final)
        self.GAMMA_DECAY = 1.5     # Distance decay exponent
        
        # 3. Macro Weights (W_career) for 'Career/Status'
        self.W_CAREER = {
            "zheng_guan": 0.30, 
            "qi_sha": 0.25,     
            "zheng_yin": 0.15,  
            "shi_shang": 0.13,  
            "pian_yin": 0.08,   
            "cai_xing": 0.07,   
            "bi_jie": 0.02      
        }

        # Load learned weights from DB if available
        if use_db_weights:
            try:
                learned = self.db.get_latest_weights() # Returns dict or None
                if learned:
                    self.update_weights(learned)
            except Exception:
                pass # Fallback to defaults

        # --- Standard Mappings ---
        self.stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        self.branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        # 5 Elements Mapping
        self.stem_elements = {"甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire", 
                              "戊": "earth", "己": "earth", "庚": "metal", "辛": "metal", 
                              "壬": "water", "癸": "water"}
                              
        # Branch Main Qi (Hidden Stems)
        self.branch_roots = {
            "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], 
            "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "戊", "庚"], 
            "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"], 
            "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]
        }
        
        self.pillars = ["year", "month", "day", "hour"]

    def update_weights(self, new_weights):
        """
        Dynamically updates model parameters.
        new_weights: dict containing 'W_E' or 'W_CAREER' sub-dictionaries.
        """
        if 'W_E' in new_weights:
            self.W_E.update(new_weights['W_E'])
        if 'W_CAREER' in new_weights:
            self.W_CAREER.update(new_weights['W_CAREER'])
        if 'GAMMA_DECAY' in new_weights:
            self.GAMMA_DECAY = new_weights['GAMMA_DECAY']

    # --- 1. Field Calculation: Energy Potential (Z-Axis) ---

    def calculate_energy(self, element, chart):
        """
        Calculates E_god (Potential) for a given element (e.g., 'wood') 
        based on the V2.0 formula: Sum(W_E * Sources)
        """
        score = 0.0
        
        # Source 1: Month Command (Ling) - Highest Weight
        month_branch = chart.get('month', {}).get('branch', '')
        if self._is_season_support(element, month_branch):
            score += self.W_E["month_command"]
            
        # Source 2: Rooting (Tong Gen)
        # Scan all branches for presence of this element
        for p in self.pillars:
            branch = chart.get(p, {}).get('branch', '')
            if self._has_root(element, branch):
                # We can sum multiple roots or just count once. 
                # Blueprint says "Tong Gen" generally. Let's add once per root found?
                # Or simplistic: If grounded at all => +3.0. Let's do accumulate for density.
                # Justification: More roots = Stronger Z-axis.
                score += (self.W_E["root_main"] * 0.5) # Splitting 3.0 across potential roots if multiple lines?
                # Actually, let's stick to simple: If it has *any* root, add 3.0. 
                # If multiple, maybe bonus? Let's stick to discrete rule first.
        
        # Re-eval: "Tong Gen (Main Qi) -> +3.0". 
        # Let's count how many branches have this element as Main Qi.
        roots = 0
        for p in self.pillars:
            branch = chart.get(p, {}).get('branch', '')
            if self._is_main_qi(element, branch):
                roots += 1
        
        if roots > 0:
            score += (self.W_E["root_main"] + (roots-1)*1.0) # Base 3 + Bonus for extra roots

        # Source 3: Birth Support (Sheng) - Neighboring Stems/Branches generating it
        # This requires relational check. Simplified: Is there a Parent element adjacent?
        # TODO: Implement adjacency check. For now, random static noise or 0.
        
        return score

    # --- 2. Field Calculation: Coupling (X/Y Plane) ---

    def calculate_coupling(self, elem1, elem2, distance_steps):
        """
        Calculates C_final = (C_base * F_yinyang) * F_distance
        """
        # C_base: Physics of Wuxing (Interaction Strength).
        # Water->Fire (Clash) is High Energy. Wood->Fire (Birth) is Medium.
        # Simplified: Base = 1.0
        c_base = 1.0 
        
        # F_yinyang
        # If same polarity -> Intense (+1.2)
        # If diff polarity -> Sticky/Soft (0.8)
        # Placeholder: Assume 1.0 for now.
        f_yinyang = 1.0
        
        # F_distance
        # D_ij = distance_steps (0 = Same Pillar, 1 = Adjacent, 2 = Far, 3 = Very Far)
        # Formula: 1 / (D_ij ^ Gamma)
        # Avoid division by zero: if D=0, treat as extremely close (max coupling).
        if distance_steps < 0.1: 
             f_dist = 2.0 # Max clamp
        else:
             f_dist = 1.0 / (float(distance_steps) ** self.GAMMA_DECAY)
             
        c_final = (c_base * f_yinyang) * f_dist
        return c_final

    # --- 3. Vectorization & Aspect Prediciton ---

    def calculate_aspects(self, chart):
        """
        Predicts high-level life outcomes (Wealth, Career) based on computed Field Energies
        and Learnable Weights (W_CAREER).
        """
        # 1. Identify Day Master Element
        dm_stem = chart.get('day', {}).get('stem')
        if not dm_stem: return {}
        dm_elem = self.stem_elements.get(dm_stem, 'wood') 
        
        # 2. Calculate Energies for all 5 Elements
        elements = ["wood", "fire", "earth", "metal", "water"] 
        energies = {el: self.calculate_energy(el, chart) for el in elements}
        
        # 3. Map Energies to Ten Gods (Simplified 5-God View for Physics)
        elem_order = ["wood", "fire", "earth", "metal", "water"]
        dm_idx = elem_order.index(dm_elem)
        
        gods_score = {}
        # 0:Peer, 1:Output, 2:Wealth, 3:Officer, 4:Resource
        # Keys match logical roles
        god_names = {
            0: "bi_jie", 1: "shi_shang", 2: "cai_xing", 3: "zheng_guan", 4: "zheng_yin" 
        }
        
        for offset, g_name in god_names.items():
            target_idx = (dm_idx + offset) % 5
            target_elem = elem_order[target_idx]
            gods_score[g_name] = energies[target_elem]
            
        # 4. Calculate Aspects using Learnable Weights
        # Note: self.W_CAREER contains fine-grained weights. We aggregate them for these broad categories.
        # This allows the Optimizer to tune 'zheng_guan' vs 'qi_sha' weights, even if we group them here.
        
        aspects = {}
        
        # A. Career (Status)
        # Power comes from Officer (Guan) and Seal (Yin)
        w_guan = self.W_CAREER.get('zheng_guan', 0.3) + self.W_CAREER.get('qi_sha', 0.25)
        w_yin = self.W_CAREER.get('zheng_yin', 0.15) + self.W_CAREER.get('pian_yin', 0.08)
        aspects['career'] = gods_score['zheng_guan'] * w_guan * 3.0 + gods_score['zheng_yin'] * w_yin * 2.0
        
        # B. Wealth (Asset)
        # Wealth comes from Wealth (Cai) and Output (Shi/Shang)
        w_cai = self.W_CAREER.get('cai_xing', 0.3) 
        w_shi = self.W_CAREER.get('shi_shang', 0.2)
        aspects['wealth'] = gods_score['cai_xing'] * (w_cai * 4.0) + gods_score['shi_shang'] * (w_shi * 2.0)
        
        # C. Marriage / Relationship
        # Avg of Wealth and Officer
        aspects['marriage'] = (gods_score['cai_xing'] + gods_score['zheng_guan']) * 1.5
        
        # D. Health / Stability
        # Root (Peer) and Resource
        aspects['health'] = gods_score['bi_jie'] * 2.0 + gods_score['zheng_yin'] * 2.0
        
        # Scaling to 0-100 (Heuristic clamping)
        for k in aspects:
            aspects[k] = min(max(aspects[k] * 2.0, 0), 100.0)
            
        return aspects

    def vectorize_chart(self, chart_data):
        """
        Generates the sophisticated feature vector (X) based on Antigravity V2.0.
        Instead of raw One-Hot, this returns the calculated 'Energy Field' values
        for the 5 Elements or 10 Gods.
        
        Refined X Vector Structure (Example):
        [ E_wood, E_fire, E_earth, E_metal, E_water,  <-- Potentials (Z-axis)
          C_wood_fire, C_wood_earth...                <-- Key Couplings
          ... OneHot ...                              <-- Raw topology fallbacks
        ]
        """
        if isinstance(chart_data, str): chart_data = json.loads(chart_data)
        
        # 1. Calculate E-Potentials for 5 Elements
        elements = ["wood", "fire", "earth", "metal", "water"]
        energies = []
        for el in elements:
            e_val = self.calculate_energy(el, chart_data)
            energies.append(e_val)
            
        # 2. Append Raw One-Hot (to keep topological info that Physics might miss during cold start)
        raw_vec = self._encode_raw_one_hot(chart_data)
        
        # Concatenate: [Energies (5)] + [Raw (88)]
        # This gives the model both the high-level Physics hypothesis AND the raw data to learn residuals.
        return np.concatenate((np.array(energies), raw_vec))

    def _encode_raw_one_hot(self, chart_data):
        """
        Legacy One-Hot encoding (from V1) to serve as 'Raw Grid' data.
        """
        full_vector = []
        for p in self.pillars:
            pillar_data = chart_data.get(p, {})
            stem_val = pillar_data.get("stem", "") if isinstance(pillar_data, dict) else ""
            branch_val = pillar_data.get("branch", "") if isinstance(pillar_data, dict) else ""
            full_vector.extend(self._one_hot(stem_val, self.stems))
            full_vector.extend(self._one_hot(branch_val, self.branches))
        return np.array(full_vector)

    def _one_hot(self, value, category_list):
        vec = [0] * len(category_list)
        try:
            idx = category_list.index(value)
            vec[idx] = 1
        except: pass
        return vec

    # --- Helpers ---

    def _is_season_support(self, element, month_branch):
        # Simplified Season mapping
        season_map = {
            "寅": "wood", "卯": "wood", "辰": "earth", # Spring (Wood+Earth)
            "巳": "fire", "午": "fire", "未": "earth", # Summer
            "申": "metal", "酉": "metal", "戌": "earth", # Autumn
            "亥": "water", "子": "water", "丑": "earth"  # Winter
        }
        return season_map.get(month_branch) == element

    def _has_root(self, element, branch):
        # Check if branch contains hidden stem of that element
        hiddens = self.branch_roots.get(branch, [])
        for stem in hiddens:
            if self.stem_elements.get(stem) == element:
                return True
        return False
        
    def _is_main_qi(self, element, branch):
        # Check if the Main Qi (first hidden stem) matches element
        hiddens = self.branch_roots.get(branch, [])
        if not hiddens: return False
        main_stem = hiddens[0]
    # --- 4. Dataset Management ---

    def load_dataset(self, target_aspect="wealth"):
        """
        Loads all valid cases from DB and prepares X and Y arrays.
        target_aspect: The specific life domain to predict (e.g. 'wealth')
        """
        cases = self.db.get_all_cases()
        X_list = []
        y_list = []
        
        for case in cases:
            # 1. Parse Chart (X)
            # chart_data is stored as a Dict in the returned case object
            chart = case['chart']
            if not chart: continue
            
            vec = self.vectorize_chart(chart)
            
            # 2. Parse Truth (Y)
            truth = case['truth']
            if not truth: continue
            
            score = truth.get(target_aspect)
            if score is None: continue
            
            try:
                score = float(score)
            except:
                continue
                
            X_list.append(vec)
            y_list.append(score)
            
        if not X_list:
            return np.array([]), np.array([])
            
        return np.array(X_list), np.array(y_list)

    # --- 5. Ten Gods Physics (Relational Field) ---
    
    def calculate_ten_gods_strength(self, chart):
        """
        Calculates the strength of Ten Gods relative to the Day Master.
        Returns a dict { 'zheng_guan': 5.2, ... }
        This is crucial for applying W_CAREER weights.
        """
        # 1. Identify Day Master
        day_stem = chart.get('day', {}).get('stem')
        if not day_stem: return {}
        
        dm_element = self.stem_elements.get(day_stem)
        
        # 2. Calculate Element Energies first
        element_energies = {}
        for el in ["wood", "fire", "earth", "metal", "water"]:
            element_energies[el] = self.calculate_energy(el, chart)
            
        # 3. Map Elements to Ten Gods
        # Relationship Matrix (simplified):
        # Same = Friend (BiJie)
        # Generates Me = Seal (Yin)
        # Me Generates = Output (ShiShang)
        # Me Controls = Wealth (Cai)
        # Controls Me = Power (GuanSha)
        
        # Generating Order: Wood->Fire->Earth->Metal->Water->Wood
        gen_order = ["wood", "fire", "earth", "metal", "water"]
        dm_idx = gen_order.index(dm_element)
        
        gods_map = {
            "bi_jie": element_energies[dm_element],               # Same
            "shi_shang": element_energies[gen_order[(dm_idx+1)%5]], # Output
            "cai_xing": element_energies[gen_order[(dm_idx+2)%5]], # Wealth
            "guan_sha": element_energies[gen_order[(dm_idx+3)%5]], # Power
            "yin_xing": element_energies[gen_order[(dm_idx+4)%5]], # Seal
        }
        
        # Split into Zheng/Pian (Direct/Indirect) requires YinYang check of stems
        # For macro vector, we might just use the 5 elemental relative strengths roughly mapped.
        # To match W_CAREER keys exactly:
        # zheng_guan/qi_sha are both under 'guan_sha' element.
        # We split them 50/50 for now unless we do precise stem scanning.
        
        detailed_gods = {
            "zheng_guan": gods_map["guan_sha"] * 0.5,
            "qi_sha": gods_map["guan_sha"] * 0.5,
            "zheng_yin": gods_map["yin_xing"] * 0.5,
            "pian_yin": gods_map["yin_xing"] * 0.5,
            "cai_xing": gods_map["cai_xing"], # Merged in W_CAREER
            "shi_shang": gods_map["shi_shang"], # Merged
            "bi_jie": gods_map["bi_jie"]
        }
        
        return detailed_gods

