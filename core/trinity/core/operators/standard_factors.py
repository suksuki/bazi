
"""
🎛️ Antigravity V13.6: Standard Influence Operators (VALIDATED MODE)
======================================================================
Operators with Empirically Validated Parameters from Legacy Code
"""

import math
from typing import Dict, Any, Optional, List
from ..middleware.influence_bus import (
    InfluenceFactor, 
    ExpectationVector, 
    NonlinearType
)
from ..nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus

# ============================================================
# 1. LUCK CYCLE FACTOR (大运 - VALIDATED)
# ============================================================

class LuckCycleFactor(InfluenceFactor):
    def __init__(self, luck_pillar: str, weight: float = 1.0, enabled: bool = True):
        super().__init__(
            name="LuckCycle/大运",
            nonlinear_type=NonlinearType.EXPONENTIAL_DECAY,
            weight=weight,
            enabled=enabled,
            metadata={"luck_pillar": luck_pillar}
        )
        self.luck_pillar = luck_pillar
        if len(luck_pillar) >= 2:
            self.luck_stem = luck_pillar[0]
            # Use local variable for element lookup to avoid property conflict
            _branch = luck_pillar[1]
            self.luck_element = BaziParticleNexus.BRANCHES.get(_branch, ("Unknown",))[0]
        else:
            self.luck_stem = ""
            self.luck_element = "Unknown"

    @property
    def luck_branch_name(self) -> str:
        return self.luck_branch

    @property
    def luck_branch(self) -> str:
        # For compatibility with engines checking factor.luck_branch
        _p = self.metadata.get("luck_pillar", "")
        return _p[1] if len(_p) > 1 else ""

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Optional[Dict[str, Any]] = None) -> ExpectationVector:
        result = base_e.clone()
        if self.luck_element == "Unknown": return result

        # [VALIDATED FORMULA] Luck weight on field
        branch_weight = 1.2 * self.weight

        # Inject into expectation vector
        elem_lower = self.luck_element.lower()
        if elem_lower in result.elements:
            result.elements[elem_lower] += branch_weight * 0.5
        
        self.log(f"Luck {self.luck_pillar} injected element {self.luck_element} with branch weight {branch_weight}")
        return result

# ============================================================
# 2. ANNUAL PULSE FACTOR (流年 - VALIDATED)
# ============================================================

class AnnualPulseFactor(InfluenceFactor):
    def __init__(self, annual_pillar: str, weight: float = 1.0, enabled: bool = True):
        super().__init__(
            name="AnnualPulse/流年",
            nonlinear_type=NonlinearType.IMPULSE,
            weight=weight,
            enabled=enabled,
            metadata={"annual_pillar": annual_pillar}
        )
        self.annual_pillar = annual_pillar
        if len(annual_pillar) >= 2:
            self.annual_stem = annual_pillar[0]
            _branch = annual_pillar[1]
            self.annual_element = BaziParticleNexus.BRANCHES.get(_branch, ("Unknown",))[0]
        else:
            self.annual_stem = ""
            self.annual_element = "Unknown"

    @property
    def annual_branch_name(self) -> str:
        return self.annual_branch

    @property
    def annual_branch(self) -> str:
        # For compatibility with engines checking factor.annual_branch
        _p = self.metadata.get("annual_pillar", "")
        return _p[1] if len(_p) > 1 else ""

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Optional[Dict[str, Any]] = None) -> ExpectationVector:
        result = base_e.clone()
        if self.annual_element == "Unknown": return result

        # [VALIDATED FORMULA] Annual weight on field
        effective_power = 1.2 * 1.5 * self.weight

        elem_lower = self.annual_element.lower()
        if elem_lower in result.elements:
            result.elements[elem_lower] += effective_power * 0.5
            
        self.log(f"Annual {self.annual_pillar} injected {self.annual_element} with power {effective_power}")
        return result

# ============================================================
# 3. GEO BIAS FACTOR (地域 - VALIDATED)
# ============================================================

class GeoBiasFactor(InfluenceFactor):
    def __init__(self, geo_factor: float = 1.0, geo_element: str = "Neutral", weight: float = 1.0, enabled: bool = True):
        super().__init__(
            name="GeoBias/地域",
            nonlinear_type=NonlinearType.GAUSSIAN_DAMPING,
            weight=weight,
            enabled=enabled,
            metadata={"geo_factor": geo_factor, "geo_element": geo_element}
        )
        self.geo_factor = geo_factor
        self.geo_element = geo_element

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Optional[Dict[str, Any]] = None) -> ExpectationVector:
        result = base_e.clone()
        
        # [VALIDATED FORMULA] Direct multiplier from QuantumUniversalFramework
        if self.geo_element != "Neutral":
            elem_lower = self.geo_element.lower()
            if elem_lower in result.elements:
                result.elements[elem_lower] *= self.geo_factor
                self.log(f"Geo Bias: {self.geo_element} multiplied by {self.geo_factor}")
        
        return result

# ============================================================
# 4. ERA FACTOR (九运 - PLACEHOLDER)
# ============================================================

class EraFactor(InfluenceFactor):
    def __init__(self, target_year: int = 2025, weight: float = 1.0, enabled: bool = False):
        super().__init__(
            name="Era9/九运",
            nonlinear_type=NonlinearType.LINEAR_SHIFT,
            weight=weight,
            enabled=enabled,
            metadata={"year": target_year}
        )

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Optional[Dict[str, Any]] = None) -> ExpectationVector:
        return base_e
