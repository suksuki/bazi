"""
Phase B: Quantum Dispersion Engine
===================================
Dynamic hidden stem energy allocation based on solar term progression.

Physical Model: Quantum Dispersion
- Three overlapping energy wave packets (Primary, Secondary, Residual)
- Energy distribution follows sinusoidal decay functions
- Smooth transitions at solar term boundaries (no abrupt jumps)

Mathematical Model: Non-linear Sinusoidal Decay
- Primary(t)   = sin²(πt/T)           # Peaks at mid-term
- Secondary(t) = sin²(πt/T + π/3)     # Phase offset 60°
- Residual(t)  = sin²(πt/T + 2π/3)    # Phase offset 120°
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from lunar_python import Lunar, Solar


class QuantumDispersionEngine:
    """
    Dynamic hidden stem energy allocation based on solar term progression.
    
    Replaces static 70/20/10 ratios with time-continuous quantum dispersion model.
    """
    
    # Standard hidden stems per branch (static reference)
    BRANCH_HIDDEN_STEMS = {
        "子": [("癸", 10)],
        "丑": [("己", 5), ("癸", 3), ("辛", 2)],
        "寅": [("甲", 5), ("丙", 3), ("戊", 2)],
        "卯": [("乙", 10)],
        "辰": [("戊", 5), ("乙", 3), ("癸", 2)],
        "巳": [("丙", 5), ("戊", 3), ("庚", 2)],
        "午": [("丁", 7), ("己", 3)],
        "未": [("己", 5), ("丁", 3), ("乙", 2)],
        "申": [("庚", 5), ("壬", 3), ("戊", 2)],
        "酉": [("辛", 10)],
        "戌": [("戊", 5), ("辛", 3), ("丁", 2)],
        "亥": [("壬", 7), ("甲", 3)]
    }
    
    # Solar term to branch mapping (节气 → 地支)
    # Each solar term corresponds to the "entry" point of a period
    SOLAR_TERM_BRANCHES = {
        "立春": "寅", "雨水": "寅",
        "惊蛰": "卯", "春分": "卯",
        "清明": "辰", "谷雨": "辰",
        "立夏": "巳", "小满": "巳",
        "芒种": "午", "夏至": "午",
        "小暑": "未", "大暑": "未",
        "立秋": "申", "处暑": "申",
        "白露": "酉", "秋分": "酉",
        "寒露": "戌", "霜降": "戌",
        "立冬": "亥", "小雪": "亥",
        "大雪": "子", "冬至": "子",
        "小寒": "丑", "大寒": "丑"
    }
    
    # 24 Solar terms in order
    SOLAR_TERMS = [
        "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
        "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
        "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
        "立冬", "小雪", "大雪", "冬至", "小寒", "大寒"
    ]
    
    def __init__(self, damping_factor: float = 1.0):
        """
        Initialize the Quantum Dispersion Engine.
        
        Args:
            damping_factor: Controls residual energy decay rate (higher = slower decay)
        """
        self.damping_factor = damping_factor

    @staticmethod
    def get_solar_term_times_for_year(year: int) -> Dict[str, datetime]:
        """
        Fetch exact times for all 24 solar terms in a given year.
        Uses lunar_python library.
        """
        # Create a lunar object for January 1st of that year (to get the year's context)
        # lunar_python handles the solar terms accurately
        lunar = Lunar.fromYmd(year, 1, 1)
        term_dict = lunar.getJieQiTable() # Dict[str, Solar]
        
        solar_term_times = {}
        for name, solar_obj in term_dict.items():
            # Convert lunar_python Solar object to standard python datetime
            dt = datetime(
                solar_obj.getYear(), 
                solar_obj.getMonth(), 
                solar_obj.getDay(), 
                solar_obj.getHour(), 
                solar_obj.getMinute(), 
                solar_obj.getSecond()
            )
            solar_term_times[name] = dt
            
        return solar_term_times
    
    def get_dynamic_weights(self, branch: str, phase_progress: float) -> Dict[str, float]:
        """
        Calculate dynamic weights for hidden stems based on solar term progress.
        
        Args:
            branch: The branch character (e.g., '丑')
            phase_progress: Progress within current solar term (0.0 to 1.0)
        
        Returns:
            dict: {stem: dynamic_weight} e.g., {'己': 6.2, '癸': 2.5, '辛': 1.3}
        """
        hidden_stems = self.BRANCH_HIDDEN_STEMS.get(branch, [])
        
        if not hidden_stems:
            return {}
        
        # Single hidden stem (pure branches like 子, 卯, 酉)
        if len(hidden_stems) == 1:
            return {hidden_stems[0][0]: 10.0}
        
        # Multi-stem branches: apply quantum dispersion
        num_stems = len(hidden_stems)
        
        # Calculate sinusoidal weights
        raw_weights = []
        for i in range(num_stems):
            # Phase offsets: 0, π/3, 2π/3 for primary/secondary/residual
            phase_offset = i * math.pi / 3
            
            # Sinusoidal decay with damping
            # sin²(πt/T + offset) - peaks at different times
            weight = self._sinusoidal_weight(phase_progress, phase_offset)
            
            # Apply damping to residual (last stem)
            if i == num_stems - 1:
                weight *= self.damping_factor
            
            raw_weights.append(weight)
        
        # Normalize to sum = 10 (standard Bazi scale)
        total_raw = sum(raw_weights)
        if total_raw == 0:
            total_raw = 1  # Avoid division by zero
        
        dynamic_weights = {}
        for i, (stem, _) in enumerate(hidden_stems):
            normalized_weight = (raw_weights[i] / total_raw) * 10.0
            dynamic_weights[stem] = round(normalized_weight, 2)
        
        return dynamic_weights
    
    def _sinusoidal_weight(self, t: float, phase_offset: float) -> float:
        """
        Calculate sinusoidal weight using sin² function.
        
        Args:
            t: Progress within period (0.0 to 1.0)
            phase_offset: Phase offset in radians
        
        Returns:
            float: Weight value (0.0 to 1.0)
        """
        # sin²(πt + offset) 
        # This gives smooth transitions with peaks at different phases
        angle = math.pi * t + phase_offset
        return math.sin(angle) ** 2
    
    def calculate_phase_progress(self, birth_datetime: datetime, 
                                  solar_term_times: Dict[str, datetime]) -> Tuple[float, str, str]:
        """
        Calculate the progress (0.0 to 1.0) within the current solar term.
        
        Args:
            birth_datetime: The birth date/time
            solar_term_times: Dict mapping solar term names to their exact times
                              e.g., {"立春": datetime(2024, 2, 4, 16, 27), ...}
        
        Returns:
            Tuple[float, str, str]: (progress, current_term, next_term)
        """
        # Find which solar term period the birth time falls into
        sorted_terms = sorted(solar_term_times.items(), key=lambda x: x[1])
        
        current_term = None
        next_term = None
        current_term_start = None
        next_term_start = None
        
        for i, (term_name, term_time) in enumerate(sorted_terms):
            if term_time > birth_datetime:
                if i > 0:
                    current_term = sorted_terms[i-1][0]
                    current_term_start = sorted_terms[i-1][1]
                    next_term = term_name
                    next_term_start = term_time
                break
        else:
            # Birth is after all terms in the dict (use last term)
            current_term = sorted_terms[-1][0]
            current_term_start = sorted_terms[-1][1]
            next_term = sorted_terms[0][0]  # Wrap to first term
            # Estimate next term as ~15 days later
            next_term_start = current_term_start.replace(
                day=current_term_start.day + 15
            ) if current_term_start.day <= 15 else current_term_start.replace(
                month=current_term_start.month + 1, day=1
            )
        
        if current_term_start is None or next_term_start is None:
            return 0.5, "Unknown", "Unknown"  # Fallback to mid-point
        
        # Calculate progress
        total_seconds = (next_term_start - current_term_start).total_seconds()
        elapsed_seconds = (birth_datetime - current_term_start).total_seconds()
        
        if total_seconds <= 0:
            return 0.5, current_term, next_term
        
        progress = max(0.0, min(1.0, elapsed_seconds / total_seconds))
        
        return progress, current_term, next_term
    
    def get_static_weights(self, branch: str) -> Dict[str, float]:
        """
        Get static (traditional) hidden stem weights for comparison.
        
        Args:
            branch: The branch character
        
        Returns:
            dict: {stem: weight}
        """
        hidden_stems = self.BRANCH_HIDDEN_STEMS.get(branch, [])
        return {stem: float(weight) for stem, weight in hidden_stems}
    
    def compare_static_vs_dynamic(self, branch: str, phase_progress: float) -> Dict:
        """
        Compare static vs dynamic weights for a given branch.
        
        Args:
            branch: The branch character
            phase_progress: Progress within solar term (0.0 to 1.0)
        
        Returns:
            dict: Comparison data including delta values
        """
        static = self.get_static_weights(branch)
        dynamic = self.get_dynamic_weights(branch, phase_progress)
        
        comparison = {
            "branch": branch,
            "phase_progress": round(phase_progress, 4),
            "static": static,
            "dynamic": dynamic,
            "delta": {}
        }
        
        for stem in static:
            static_val = static.get(stem, 0)
            dynamic_val = dynamic.get(stem, 0)
            comparison["delta"][stem] = round(dynamic_val - static_val, 2)
        
        return comparison


def demo_dispersion():
    """Demo function to show dynamic vs static weights."""
    engine = QuantumDispersionEngine(damping_factor=1.0)
    
    print("=== Phase B: Quantum Dispersion Demo ===\n")
    
    # Test with 丑 (three hidden stems: 己, 癸, 辛)
    branch = "丑"
    print(f"Branch: {branch}")
    print(f"Static weights: {engine.get_static_weights(branch)}")
    print()
    
    # Show progression
    print("Dynamic weights at different phase progress:")
    for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
        weights = engine.get_dynamic_weights(branch, progress)
        print(f"  Progress {progress:.2f}: {weights}")
    
    print()
    print("=== Comparison Chart ===")
    for progress in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        comp = engine.compare_static_vs_dynamic(branch, progress)
        print(f"t={progress:.1f}: 己={comp['dynamic']['己']:.2f} 癸={comp['dynamic']['癸']:.2f} 辛={comp['dynamic']['辛']:.2f}")


if __name__ == "__main__":
    demo_dispersion()
