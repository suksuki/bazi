"""
Antigravity Resonance Booster Logic (Phase B-10)
================================================
Core physics logic for Stem-Branch Resonance & Rooting Gain.
"""

from typing import List, Dict, Any, Optional

class ResonanceBooster:
    
    # Rooting Gain Matrix (G_res)
    GAIN_MATRIX = {
        "MAIN": 2.0,
        "MEDIUM": 1.5,
        "RESIDUAL": 1.2,
        "FLOATING": 0.5
    }

    # Standard Hidden Stems Mapping (Simplified for Logic Lookup)
    # Format: Branch -> {Stem: Type}
    HIDDEN_STEMS = {
        "子": {"癸": "MAIN"},
        "丑": {"己": "MAIN", "癸": "MEDIUM", "辛": "RESIDUAL"},
        "寅": {"甲": "MAIN", "丙": "MEDIUM", "戊": "RESIDUAL"},
        "卯": {"乙": "MAIN"},
        "辰": {"戊": "MAIN", "乙": "MEDIUM", "癸": "RESIDUAL"},
        "巳": {"丙": "MAIN", "戊": "MEDIUM", "庚": "RESIDUAL"},
        "午": {"丁": "MAIN", "己": "MEDIUM"},
        "未": {"己": "MAIN", "丁": "MEDIUM", "乙": "RESIDUAL"},
        "申": {"庚": "MAIN", "壬": "MEDIUM", "戊": "RESIDUAL"},
        "酉": {"辛": "MAIN"},
        "戌": {"戊": "MAIN", "辛": "MEDIUM", "丁": "RESIDUAL"},
        "亥": {"壬": "MAIN", "甲": "MEDIUM"}
    }

    @staticmethod
    def calculate_resonance_gain(stem: str, branches: List[str]) -> Dict[str, Any]:
        """
        Calculates the maximum resonance gain (G_res) for a given stem against a list of branches.
        
        Args:
            stem: The Heavenly Stem (e.g., '甲')
            branches: List of Earthly Branches (e.g., ['寅', '辰'])
            
        Returns:
            Dict: { 'gain': float, 'best_root': str, 'root_type': str, 'status': str }
        """
        max_gain = ResonanceBooster.GAIN_MATRIX["FLOATING"]
        best_root_branch = None
        best_root_type = "NONE"
        
        for br in branches:
            hidden = ResonanceBooster.HIDDEN_STEMS.get(br, {})
            if stem in hidden:
                rtype = hidden[stem]
                gain = ResonanceBooster.GAIN_MATRIX.get(rtype, 1.0)
                
                # "Strong Connection Priority": Take max gain
                if gain > max_gain:
                    max_gain = gain
                    best_root_branch = br
                    best_root_type = rtype
        
        status = "SUPER_STABLE" if max_gain >= 2.0 else "STABLE" if max_gain > 1.0 else "DAMPED" if max_gain > 0.5 else "CRITICAL_VOLATILE"
        
        return {
            "gain": max_gain,
            "best_root": best_root_branch,
            "root_type": best_root_type,
            "status": status,
            "energy_pumping": max_gain >= 2.0
        }

# Export functional alias
calculate_rooting_gain = ResonanceBooster.calculate_resonance_gain
