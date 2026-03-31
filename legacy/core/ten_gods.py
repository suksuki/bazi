class TenGodsEngine:
    """
    Calculates Ten Gods (Shi Shen) strengths based on Day Master and Wu Xing scores.
    Ten Gods map Element relationships to social/functional aspects of life.
    """
    
    # 0: Same (Friend), 1: Output (Food), 2: Wealth (Cai), 3: Control (Guan), 4: Resource (Yin)
    RELATION_OFFSET = {
        "Wood": 0, "Fire": 1, "Earth": 2, "Metal": 3, "Water": 4
    }
    
    # Ordered Elements cyclically
    ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
    
    # Ten Gods Mapping
    # Key: Relative Index (0-4), Value: Name
    GODS_MAP = {
        0: "Friend (Bi/Jie)",       # Same Element
        1: "Output (Shi/Shang)",    # Generates
        2: "Wealth (Zheng/Pian)",   # I Control
        3: "Officer (Guan/Sha)",    # Controls Me
        4: "Resource (Yin/Xiao)"    # Generates Me
    }
    
    def __init__(self, day_master_element, wuxing_scores):
        self.dm_elem = day_master_element
        self.scores = wuxing_scores
        
    def calculate_gods_strength(self):
        """
        Returns a dictionary of Ten Gods strengths.
        """
        dm_idx = self.ELEMENTS.index(self.dm_elem)
        
        gods_strength = {}
        
        for i, god_name in self.GODS_MAP.items():
            # Calculate actual element index for this God relative to Day Master
            target_idx = (dm_idx + i) % 5
            target_elem = self.ELEMENTS[target_idx]
            
            # Get Score
            score = self.scores.get(target_elem, 0)
            gods_strength[god_name] = score
            
        return gods_strength

    def get_life_aspects(self):
        """
        Maps Ten Gods to Modern Life Aspects.
        """
        gods = self.calculate_gods_strength()
        
        # Mapping Logic
        # Career: Officer (Status) + Resource (Authority/Support)
        # Wealth: Wealth + Output (Source of Wealth)
        # Marriage (For Male): Wealth (Wife Star)
        # Marriage (For Female): Officer (Husband Star) 
        # But for generic "Relationship" usually Wealth/Officer balance
        
        # Simplified Quantification for Prototype
        aspects = {
            "事业 (Career)": gods["Officer (Guan/Sha)"] * 0.7 + gods["Resource (Yin/Xiao)"] * 0.3,
            "财富 (Wealth)": gods["Wealth (Zheng/Pian)"] * 0.8 + gods["Output (Shi/Shang)"] * 0.2, # Output produces Wealth
            "学业 (Education)": gods["Resource (Yin/Xiao)"] * 0.8 + gods["Output (Shi/Shang)"] * 0.2,
            "人际 (Friendship)": gods["Friend (Bi/Jie)"],
            "子女/创造 (Creativity)": gods["Output (Shi/Shang)"],
            "压力/健康 (Stress)": gods["Officer (Guan/Sha)"] # Too much Officer = Stress
        }
        
        # Normalize to 0-100 scale? 
        # Raw scores are typically 0-200. Let's cap at 100 for UX or just return raw.
        # User wants "Quantified", raw numbers are fine, Radar chart will handle scaling.
        
        return aspects
