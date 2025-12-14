from core.processors.base import BaseProcessor
from typing import Dict, Any

class EraProcessor(BaseProcessor):
    """
    Layer 4: Era & Zeitgeist Processor
    
    Adjusts elemental weights based on the current Period (Three Cycles Nine Periods).
    e.g., Period 9 (Fire) starts 2024.
    """
    
    # Simple Period Map
    PERIODS = [
        {"start": 1984, "end": 2003, "period": 7, "element": "metal", "desc": "兑金运"},
        {"start": 2004, "end": 2023, "period": 8, "element": "earth", "desc": "艮土运"},
        {"start": 2024, "end": 2043, "period": 9, "element": "fire",  "desc": "离火运"},
        {"start": 2044, "end": 2063, "period": 1, "element": "water", "desc": "坎水运"}
    ]
    
    @property
    def name(self) -> str:
        return "Era Layer 4"
        
    def process(self, year: int) -> Dict[str, Any]:
        """
        Get Era modifiers for a specific year.
        """
        # Find period
        current_period = None
        for p in self.PERIODS:
            if p["start"] <= year <= p["end"]:
                current_period = p
                break
                
        if not current_period:
            return {}
            
        element = current_period["element"]
        
        # Era Bonus: The era element is stronger globally
        return {
            "era_element": element,
            "period": current_period["period"],
            "desc": current_period["desc"],
            "modifiers": {
                element: 1.2  # 20% Boost to the ruling element
            }
        }
