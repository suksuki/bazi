# core/engines/harmony_engine.py

# Import config constants
from core.config_rules import (
    SCORE_SANHE_BONUS, SCORE_SANHE_PENALTY,
    SCORE_LIUHE_BONUS,
    SCORE_CLASH_PENALTY
)

class HarmonyEngine:
    """
    HarmonyEngine (合化引擎) - V7.3
    Handles the Chemical Reactions of Bazi:
    - Fusion (Combination): Three Harmonies (SanHe), Six Combinations (LiuHe)
    - Fission (Clash): Six Clashes (LiuChong)
    
    Architecture: Config-Driven Physics
    """

    def __init__(self, config=None):
        self.config = config or {}
        
        # --- 六冲 (The 6 Clashes) ---
        self.SIX_CLASHES = {
            '子': '午', '午': '子', '丑': '未', '未': '丑',
            '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'
        }

        # --- 六合 (The 6 Combinations) ---
        self.SIX_COMBINATIONS = {
            '子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
            '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
            '巳': '申', '申': '巳', '午': '未', '未': '午'
        }
        
        self.SIX_COMBINATIONS_ELEMENTS = {
            frozenset(['子', '丑']): 'earth', frozenset(['寅', '亥']): 'wood',
            frozenset(['卯', '戌']): 'fire',  frozenset(['辰', '酉']): 'metal',
            frozenset(['巳', '申']): 'water', frozenset(['午', '未']): 'earth' 
        }

        # --- 三合局 (San He) ---
        self.THREE_HARMONIES = {
            'Water': {'申', '子', '辰'}, 'Wood':  {'亥', '卯', '未'},
            'Fire':  {'寅', '午', '戌'}, 'Metal': {'巳', '酉', '丑'}
        }
        
        self.CARDINALS = {'子', '午', '卯', '酉'}
        
        # --- 天干五合 (Stem Five Combinations) ---
        self.STEM_COMBINATIONS = {
            '甲': '己', '己': '甲',
            '乙': '庚', '庚': '乙',
            '丙': '辛', '辛': '丙',
            '丁': '壬', '壬': '丁',
            '戊': '癸', '癸': '戊'
        }
        
        self.STEM_COMBO_ELEMENTS = {
            frozenset(['甲', '己']): 'Earth',
            frozenset(['乙', '庚']): 'Metal',
            frozenset(['丙', '辛']): 'Water',
            frozenset(['丁', '壬']): 'Wood',
            frozenset(['戊', '癸']): 'Fire'
        }
        
        # Branch Element Helper (for Transformation Check)
        self.BRANCH_SEASONS = {
            '寅': 'Wood', '卯': 'Wood', '辰': 'Earth',
            '巳': 'Fire', '午': 'Fire', '未': 'Earth', 
            '申': 'Metal', '酉': 'Metal', '戌': 'Earth',
            '亥': 'Water', '子': 'Water', '丑': 'Earth'
        }

    def update_config(self, new_config):
        self.config = new_config

    def get_combo_params(self):
        """Extract Combo Physics params"""
        inter = self.config.get('interactions', {})
        cp = inter.get('comboPhysics', {})
        # Fallback values
        return {
            'trineBonus': cp.get('trineBonus', 2.5),
            'halfBonus': cp.get('halfBonus', 1.5),
            'archBonus': cp.get('archBonus', 1.1),
            'directionalBonus': cp.get('directionalBonus', 3.0),
            'resolutionCost': cp.get('resolutionCost', 0.1)
        }

    def detect_interactions(self, chart_branches: list, year_branch: str) -> dict:
        """
        Detect all interactions between Chart and Annual Pillar.
        """
        results = {
            'san_he': [],      # Three Harmonies (Full)
            'ban_he': [],      # Half Harmonies
            'liu_he': [],      # Six Combinations
            'liu_chong': []    # Six Clashes
        }
        
        if not year_branch: return results

        # Construct the pool of available branches (Chart + Year)
        # Note: Using a multiset concept might be needed if multiple same branches matter, 
        # but for SanHe check existence is usually enough.
        # However, for specific pairings with the Year, we iterate the chart.
        
        # 1. Six Combinations & Six Clashes (Year vs Chart)
        for idx, branch in enumerate(chart_branches):
            if not branch: continue
            
            # Check Liu He
            if self.SIX_COMBINATIONS.get(year_branch) == branch:
                results['liu_he'].append({
                    'pair': (year_branch, branch),
                    'pillar_idx': idx,
                    'element': self._get_liu_he_element(year_branch, branch)
                })
            
            # Check Liu Chong
            if self.SIX_CLASHES.get(year_branch) == branch:
                results['liu_chong'].append({
                    'pair': (year_branch, branch),
                    'pillar_idx': idx
                })

        # 2. Three Harmonies (San He)
        # Check if the combined set {Chart... + Year} completes any Trinity
        # San He requires all 3 characters to be present in the pool.
        # The Year Branch MUST be part of the formation for it to be a "Year Triggered" event?
        # A: Yes, usually we look for events *triggered* by the year. 
        # But if the chart already has SanHe, the Year might reinforce or break it. 
        # Here we focus on: Year + Chart forms SanHe (that wasn't there or is activated).
        
        # We'll use a set of all present branches
        pool = set(chart_branches)
        pool.add(year_branch)
        
        for element, members in self.THREE_HARMONIES.items():
            # Strict San He: All 3 members must exist
            if members.issubset(pool):
                # Ensure the Year Branch is actually contributing (or duplicate/reinforce)?
                # Simplification: If the set exists, we count it. 
                # If the chart ALREADY had it, the Year triggering it again is still significant (Resonance).
                # But to distinguish "New" vs "Existing", strictly speaking we verify coverage.
                # Let's just report it if present.
                
                # Check if it involves the Year Branch? 
                # If Year Branch is NOT in members, then this SanHe is static in the chart, not dynamic.
                if year_branch in members:
                    results['san_he'].append({'element': element, 'members': members})
            
            # Half Harmony (Ban He)
            # Logic: 2 out of 3 members present AND one must be a Cardinal (Center).
            # AND Year Branch must be one of them.
            if year_branch in members:
                # Intersection of members and pool
                present = members.intersection(pool)
                if len(present) == 2:
                    # Check for Cardinal
                    has_cardinal = any(c in self.CARDINALS for c in present)
                    if has_cardinal:
                        results['ban_he'].append({'element': element, 'members': present})

        return results
        
    def detect_stem_interactions(self, stems: list, month_branch: str) -> list:
        """
        Detect Stem Combinations (Year-Month, Month-Day, Day-Hour).
        Returns list of transformed combos.
        """
        combos = []
        if len(stems) != 4: return combos
        
        # Adjacent Pairs: (0,1) Year-Month, (1,2) Month-Day, (2,3) Day-Hour
        # Note: Day Master (2) usually doesn't transform easily unless "Hua Qi Ge".
        # But we detect all structural matches first.
        
        pairs = [(0, 1), (1, 2), (2, 3)]
        
        month_elem = self.BRANCH_SEASONS.get(month_branch, 'Unknown')
        
        for idx1, idx2 in pairs:
            s1, s2 = stems[idx1], stems[idx2]
            if not s1 or not s2: continue
            
            target = self.STEM_COMBINATIONS.get(s1)
            if target == s2:
                # HIT!
                transform_to = self.STEM_COMBO_ELEMENTS.get(frozenset([s1, s2]))
                
                # Check Transformation Condition (Supported by Month)
                # Simplified: Transforming Element must match Month Element or be produced by it?
                # Usually: Same Element is strongest. Producing Element is okay.
                # Example: Wu-Gui (Fire) in Wu (Fire) Month -> Valid.
                
                is_transformed = False
                if transform_to and month_elem:
                   # Case 005: Wu-Gui (Fire) in Wu (Fire) -> True
                   # Strict check: Month must be SAME group.
                   if transform_to == month_elem:
                       is_transformed = True
                   # Looser check: Month generates Transform (e.g. Wood month generates Fire?)
                   # Traditional strict rule often requires Month COMMAND.
                
                # Get Config Params
                inter = self.config.get('interactions', {})
                sf = inter.get('stemFiveCombination', {})
                threshold = sf.get('threshold', 0.8) 
                
                # If Transformed, we add to list
                if is_transformed:
                     combos.append({
                         'stems': (s1, s2),
                         'indices': (idx1, idx2),
                         'transform_to': transform_to,
                         'is_successful': True,
                         'bonus': sf.get('bonus', 2.0)
                     })
        
        return combos

    def calculate_harmony_score(self, interactions: dict, favorable_elements: list) -> tuple:
        """
        V7.3 Physics Calculation
        """
        score = 0.0
        details = []
        tags = []
        
        cp = self.get_combo_params()
        
        # Base Unit Score (e.g., 5.0) which multipliers apply to
        BASE_UNIT = 5.0 
        
        fav_norm = [e.lower() for e in favorable_elements]
        
        # --- 1. San He (Grand Trinity) --- 
        for item in interactions['san_he']:
            elem = item['element'] # e.g. 'Water'
            elem_lower = elem.lower()
            members = item['members']
            
            is_fav = elem_lower in fav_norm
            msg = f"三合{elem}局"
            
            mult = cp['trineBonus'] # e.g. 2.5
            val = BASE_UNIT * mult
            
            if is_fav:
                score += val
                details.append(f"✨ {msg} (Energy x{mult})")
                tags.append("三合贵人")
            else:
                score -= val # Penalty
                details.append(f"⚠️ {msg} (Unfavorable x{mult})")
                tags.append("三合忌神")

        # --- 2. Ban He (Half Harmony) ---
        san_he_elements = {x['element'] for x in interactions['san_he']}
        
        for item in interactions['ban_he']:
            elem = item['element']
            if elem in san_he_elements: continue
            
            elem_lower = elem.lower()
            is_fav = elem_lower in fav_norm
            
            mult = cp['halfBonus'] # e.g. 1.5
            val = BASE_UNIT * mult
            
            msg = f"半合{elem}局"
            
            if is_fav:
                score += val
                details.append(f"🤝 {msg} (Energy x{mult})")
            else:
                score -= val
                details.append(f"🔗 {msg} (Drag x{mult})")

        # --- 3. Liu He (Six Combos) & Liu Chong (Six Clashes) ---
        has_liu_he = len(interactions['liu_he']) > 0
        has_san_he = len(interactions['san_he']) > 0 or len(interactions['ban_he']) > 0
        
        # Resolution State (Greedy for Combo)
        is_resolved = has_liu_he or has_san_he
        resolve_cost = cp['resolutionCost'] # e.g. 0.1 (10%)
        
        # Process Liu He
        for item in interactions['liu_he']:
            pair = item['pair']
            elem = item['element']
            
            # Liu He is generally good unless binding favorable
            # Simplification: Always bonus for now, or check transformed element?
            # Let's assume Liu He is "Alliance".
            val = BASE_UNIT # Standard 1.0 multiplier effectively
            score += val
            details.append(f"❤️ 六合 ({pair[0]}-{pair[1]} 化{elem})")
            tags.append("六合")
        
        # Process Liu Chong
        for item in interactions['liu_chong']:
            pair = item['pair']
            
            if is_resolved:
                # 贪合忘冲 - Resolution Logic
                # Pay the energy cost for resolution
                # Cost applies to what? The score? 
                # Let's deduct a small amount representing entropy of keeping peace.
                cost = BASE_UNIT * resolve_cost
                score -= cost
                details.append(f"🛡️ 贪合忘冲 (Clash Neutralized, Cost -{cost:.1f})")
            else:
                # Real Clash
                # Dynamic Favorability Check needed here?
                # We don't have target element easily here (pair is branches).
                # Need to map branches to elements. I'll use simple mapping.
                
                # Assume clash is normally bad (-1.0 * BASE)
                # But if we want V3.0 Parametric Logic (Unfavorable Relief):
                # We need logic to identify which branch is "Target" and if it's Favorable.
                # Simplified for now: Standard Penalty
                val = BASE_UNIT * 1.5 # Clash is strong
                score -= val
                details.append(f"💥 六冲 ({pair[0]}-{pair[1]})")
                tags.append("六冲")

        return score, details, tags

    def _get_liu_he_element(self, b1, b2):
        s = frozenset([b1, b2])
        return self.SIX_COMBINATIONS_ELEMENTS.get(s, 'unknown')
