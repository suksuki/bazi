
class PatternRecognizer:
    """
    Detects Special Bazi Structures (Ge Ju).
    Refines the "Strong/Weak" binary into specific frameworks.
    """
    
    def __init__(self, wuxing_report):
        """
        wuxing_report: The output dict from WuXingEngine.calculate_strength()
        Contains 'scores', 'total', 'day_master', 'strong_side_pct'
        """
        self.report = wuxing_report
        self.scores = wuxing_report['scores']
        self.total = wuxing_report['total'] or 1.0 # Prevent div by zero
        self.dm_element = wuxing_report['day_master']['element']
        self.strong_side_pct = wuxing_report['strong_side_pct']
        
    def detect_structure(self):
        """
        Returns:
            structure_name (str): e.g., "Standard", "Cong Sha", "Zhuan Wang"
            useful_gods (list): List of Elements/TenGods that are favorable
        """
        
        # 1. Cong Ge Check (Follow Pattern)
        # Condition: Self is extremely weak (e.g. < 20%), support is negligible.
        # Use a threshold. Standard is ~20%.
        if self.strong_side_pct < 20.0:
            # Find the dominant element
            dominant_element = max(self.scores, key=self.scores.get)
            dominant_score = self.scores[dominant_element]
            dominant_pct = (dominant_score / self.total) * 100
            
            # If dominant is strong enough (> 40% usually if strictly following)
            if dominant_pct > 35.0:
                relation = self._get_relation_to_dm(dominant_element)
                
                if relation == "Power": # Guan/Sha
                    return "Cong Sha Ge (Follow Killing)", ["Power", "Wealth"] # Wealth generates Power
                elif relation == "Wealth": # Cai
                    return "Cong Cai Ge (Follow Wealth)", ["Wealth", "Output"] # Output generates Wealth
                elif relation == "Output": # Shi/Shang
                    return "Cong Er Ge (Follow Child)", ["Output", "Wealth"]
                
        # 2. Zhuan Wang Check (Dominant/Vibrant Pattern)
        # Condition: Self is extremely strong (> 80%).
        if self.strong_side_pct > 80.0:
            return "Zhuan Wang Ge (Dominant)", ["Self", "Resource", "Output"] # Output allows flow (Xiu Qi)

        # 3. Standard
        return "Standard", [] # Handled by standard Strong/Weak logic
        
    def _get_relation_to_dm(self, element):
        # Need relation map
        # Simplified:
        # Same = Self
        # Gen by DM = Output
        # Con by DM = Wealth
        # Con DM = Power
        # Gen DM = Resource
        
        # Hardcoding the cycle relative to DM for robustness
        elements = ["Mu", "Huo", "Tu", "Jin", "Shui"]
        if self.dm_element not in elements: return "Unknown"
        
        idx_dm = elements.index(self.dm_element)
        idx_e = elements.index(element)
        
        diff = (idx_e - idx_dm) % 5
        
        mapping = {
            0: "Self",
            1: "Output",    # DM generates E
            2: "Wealth",    # DM controls E
            3: "Power",     # E controls DM
            4: "Resource"   # E generates DM
        }
        return mapping.get(diff, "Unknown")
