class AlchemyEngine:
    """
    Simulates Bazi interactions as Chemical Reactions.
    
    Concepts:
    - Atom: A Stem or Branch.
    - Bond (He): Affinity between two atoms (e.g., Jia-Ji).
    - Catalyst (Month Command): Required condition for Transformation (Hua).
    - Transformation (Hua): If Bond + Catalyst -> Change Element Identity.
    """
    
    # 1. Stem Combinations (He) -> Potential Product
    # 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火
    STEM_COMBINATIONS = {
        frozenset(["甲", "己"]): "Tu",
        frozenset(["乙", "庚"]): "Jin",
        frozenset(["丙", "辛"]): "Shui",
        frozenset(["丁", "壬"]): "Mu",
        frozenset(["戊", "癸"]): "Huo"
    }

    # 2. Branch Six Combinations (Liu He) -> Potential Product
    # 子丑合土, 寅亥合木, 卯戌合火, 辰酉合金, 巳申合水, 午未合土
    BRANCH_LIU_HE = {
        frozenset(["子", "丑"]): "Tu",
        frozenset(["寅", "亥"]): "Mu",
        frozenset(["卯", "戌"]): "Huo",
        frozenset(["辰", "酉"]): "Jin",
        frozenset(["巳", "申"]): "Shui",
        frozenset(["午", "未"]): "Tu"
    }

    # 3. Branch Three Harmony (San He) -> Strong Product (Bureau)
    # 申子辰合水局, 亥卯未合木局, 寅午戌合火局, 巳酉丑合金局
    BRANCH_SAN_HE = {
        frozenset(["申", "子", "辰"]): "Shui",
        frozenset(["亥", "卯", "未"]): "Mu",
        frozenset(["寅", "午", "戌"]): "Huo",
        frozenset(["巳", "酉", "丑"]): "Jin"
    }
    
    # 4. Catalyst Map: Reactant Product -> Required Month Element (Simplified)
    # To transform to Earth, Month must be Earth (or Fire generating Earth).
    CATALYST_RULES = {
        "Tu":  ["Tu", "Huo"], # Earth needs Earth or Fire month
        "Jin": ["Jin", "Tu"], # Metal needs Metal or Earth month
        "Shui": ["Shui", "Jin"], # Water needs Water or Metal month
        "Mu":  ["Mu", "Shui"], # Wood needs Wood or Water month
        "Huo": ["Huo", "Mu"]  # Fire needs Fire or Wood month
    }
    
    WU_XING_MAP = {
        "甲": "Mu", "乙": "Mu",
        "丙": "Huo", "丁": "Huo",
        "戊": "Tu",  "己": "Tu",
        "庚": "Jin", "辛": "Jin",
        "壬": "Shui", "癸": "Shui",
        "子": "Shui", "丑": "Tu", "寅": "Mu", "卯": "Mu",
        "辰": "Tu", "巳": "Huo", "午": "Huo", "未": "Tu",
        "申": "Jin", "酉": "Jin", "戌": "Tu", "亥": "Shui"
    }

    def __init__(self, chart):
        self.chart = chart
        self.reactions = [] # List of reaction events
        self.transformed_chart = {} # Placeholder for modifying energies

    def get_element(self, char):
        return self.WU_XING_MAP.get(char, "Unknown")

    def run_reactions(self):
        """
        Scan for adjacent pairs and check for reactions.
        """
        self.reactions = []
        
        # 1. Get Month Command (The Catalyst)
        month_branch = self.chart['month']['branch']
        month_element = self.get_element(month_branch)
        
        # 2. Check Stem Combinations (Year-Month, Month-Day, Day-Hour)
        stems = [
            ("year", self.chart['year']['stem']),
            ("month", self.chart['month']['stem']),
            ("day", self.chart['day']['stem']),
            ("hour", self.chart['hour']['stem'])
        ]
        
        # Scan adjacent pairs
        for i in range(len(stems) - 1):
            p1_name, s1 = stems[i]
            p2_name, s2 = stems[i+1]
            
            pair = frozenset([s1, s2])
            if pair in self.STEM_COMBINATIONS:
                product = self.STEM_COMBINATIONS[pair]
                is_bond = True
                is_transformed = False
                
                # Check Catalyst
                valid_catalysts = self.CATALYST_RULES.get(product, [])
                if month_element in valid_catalysts:
                    is_transformed = True
                
                # Special Case: Transformation creates new energy
                self.reactions.append({
                    "type": "Stem Combination",
                    "pair": f"{s1}-{s2}",
                    "position": f"{p1_name}-{p2_name}",
                    "product": product,
                    "status": "Transformed (Hua)" if is_transformed else "Bonded (He)",
                    "energy_change": "+50" if is_transformed else "0",
                    "desc": f"{s1} and {s2} combine to {product}. Catalyst ({month_branch}/{month_element}) is {'Active' if is_transformed else 'Inactive'}."
                })

        # 3. Check Branch Six Combinations
        branches = [
            ("year", self.chart['year']['branch']),
            ("month", self.chart['month']['branch']),
            ("day", self.chart['day']['branch']),
            ("hour", self.chart['hour']['branch'])
        ]
        
        for i in range(len(branches) - 1):
            p1_name, b1 = branches[i]
            p2_name, b2 = branches[i+1]
            
            pair = frozenset([b1, b2])
            if pair in self.BRANCH_LIU_HE:
                product = self.BRANCH_LIU_HE[pair]
                # Branch transformation usually harder, let's keep logic similar
                valid_catalysts = self.CATALYST_RULES.get(product, [])
                is_transformed = month_element in valid_catalysts
                
                self.reactions.append({
                    "type": "Branch Six Combine (Liu He)",
                    "pair": f"{b1}-{b2}",
                    "position": f"{p1_name}-{p2_name}",
                    "product": product,
                    "status": "Transformed (Hua)" if is_transformed else "Bonded (He)",
                    "energy_change": "+30" if is_transformed else "0",
                    "desc": f"{b1} and {b2} combine to {product}."
                })

        # 4. Check San He (Three Harmony) - Requires all 3 chars to be present
        # Get all branches in a set
        chart_branches = {
            self.chart['year']['branch'],
            self.chart['month']['branch'],
            self.chart['day']['branch'],
            self.chart['hour']['branch']
        }
        
        for trio, product in self.BRANCH_SAN_HE.items():
            if trio.issubset(chart_branches):
                # San He usually forms a powerful Bureau, rarely needs extensive catalyst conditions, 
                # but let's say it amplifies energy enormously.
                self.reactions.append({
                    "type": "Three Harmony Bureau (San He)",
                    "pair": "-".join(trio),
                    "position": "Global (Three Branches)",
                    "product": product,
                    "status": "Bureau Formed (Cheng Ju)",
                    "energy_change": "+100 (Massive)",
                    "desc": f"Complete Three Harmony Bureau detected: {list(trio)} form {product} Bureau."
                })
                
        return self.reactions
