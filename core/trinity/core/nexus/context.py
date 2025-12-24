from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

class ArbitrationScenario(Enum):
    GENERAL = "GENERAL"
    WEALTH = "WEALTH"
    HEALTH = "HEALTH"
    RELATIONSHIP = "RELATIONSHIP"
    CAREER = "CAREER"
    ACADEMIC = "ACADEMIC"

@dataclass
class ContextSnapshot:
    """
    Captures the三维环境张量 (Spacetime Context Tensor).
    Injects dynamic environmental data into the core bazi arbitration logic.
    """
    luck_pillar: str = "甲子"
    annual_pillar: str = "甲子"
    geo_city: str = "Unknown"
    geo_bias: Dict[str, float] = field(default_factory=lambda: {"Wood": 1.0, "Fire": 1.0, "Earth": 1.0, "Metal": 1.0, "Water": 1.0})
    
    # Decadal background saturation (Luck Field)
    luck_influence: float = 1.0
    
    # Annual trigger pulses
    annual_intensity: float = 1.0
    
    # Metadata for scenario-based weighting
    scenario: ArbitrationScenario = ArbitrationScenario.GENERAL

class ContextInjector:
    """
    Manages the injection of context into the Arbitration Cluster.
    """
    @staticmethod
    def create_from_request(luck_pillar: str, annual_pillar: str, geo_city: str, scenario: str = "GENERAL") -> ContextSnapshot:
        try:
            scenario_enum = ArbitrationScenario(scenario.upper())
        except ValueError:
            scenario_enum = ArbitrationScenario.GENERAL
            
        geo_bias = ContextInjector._calculate_geo_bias(geo_city)
            
        return ContextSnapshot(
            luck_pillar=luck_pillar,
            annual_pillar=annual_pillar,
            geo_city=geo_city,
            geo_bias=geo_bias,
            scenario=scenario_enum
        )

    @staticmethod
    def _calculate_geo_bias(city: str) -> Dict[str, float]:
        """
        Simplified GEO bias calculation based on city elemental affinity.
        In a real system, this would query a global database.
        """
        default_bias = {"Wood": 1.0, "Fire": 1.0, "Earth": 1.0, "Metal": 1.0, "Water": 1.0}
        
        # Mapping cities to elemental dominance
        geo_map = {
            "Beijing": {"Water": 1.1, "Earth": 1.05},
            "Shanghai": {"Wood": 1.1, "Water": 1.05},
            "Guangzhou": {"Fire": 1.1, "Wood": 1.05},
            "Shenzhen": {"Fire": 1.1, "Wood": 1.05},
            "Taipei": {"Wood": 1.1, "Water": 1.05},
            "Tokyo": {"Water": 1.1, "Wood": 1.05},
            "Singapore": {"Fire": 1.1, "Earth": 1.05},
            "London": {"Metal": 1.1, "Water": 1.05},
            "Paris": {"Metal": 1.1, "Earth": 1.05},
            "New York": {"Metal": 1.1, "Water": 1.05},
        }
        
        bias = default_bias.copy()
        if city in geo_map:
            bias.update(geo_map[city])
            
        return bias
