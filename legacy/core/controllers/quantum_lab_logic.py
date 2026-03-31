"""
Quantum Lab Controller
======================
Manages simulation logic, arbitration caching, and ten gods calculation for the Quantum Lab UI.
Extracted from: ui/pages/quantum_lab.py
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.unified_arbitrator_master import quantum_framework
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants
from core.data.geo_cities import GEO_CITY_MAP
from controllers.quantum_lab_controller import QuantumLabController as BaseController # Inherit or wrap if needed, but for now we are REPLACING the old one or creating a new logic layer.
# Wait, existing import in UI says: `from controllers.quantum_lab_controller import QuantumLabController`
# This suggests there is ALREADY a controller. I should check if I am overwriting it or extending it.
# The user instruction said "Decouple ui/pages/quantum_lab.py -> core/controllers/quantum_lab_controller.py"
# Let's check if `controllers/quantum_lab_controller.py` exists first. 
# It seems the UI imports `controllers.quantum_lab_controller`.
# I will assume I am EXTENDING or REFACTORING that file, or creating `core/controllers` as a new standard.
# The plan says "Create core/controllers/quantum_lab_controller.py".
# I will create it in `core/controllers/` as a new standard location.

logger = logging.getLogger(__name__)

# Singleton Oracle instance
oracle = TrinityOracle()

class QuantumLabLogicController:
    """
    Controller for Quantum Lab UI Logic
    Handles:
    - Heavy Oracle Analysis (Cached)
    - Arbitration (Cached)
    - Ten Gods Calculation
    - Geo Data Access
    """
    
    def __init__(self):
        self.geo_map = GEO_CITY_MAP

    @staticmethod
    def get_geo_city_map():
        return GEO_CITY_MAP

    @staticmethod
    def get_ten_god(dm_char: str, target_char: str) -> str:
        """Calculates the Ten Gods relation between DM and target char."""
        if not dm_char or not target_char: return ""
        stems = BaziParticleNexus.STEMS
        if dm_char not in stems or target_char not in stems: return ""
        
        dm_elem, dm_pol, _ = stems[dm_char]
        t_elem, t_pol, _ = stems[target_char]
        
        gen = PhysicsConstants.GENERATION
        con = PhysicsConstants.CONTROL
        
        same_pol = (dm_pol == t_pol)
        
        if dm_elem == t_elem:
            return "比肩" if same_pol else "劫财"
        elif gen[dm_elem] == t_elem:
            return "食神" if same_pol else "伤官"
        elif gen[t_elem] == dm_elem:
            return "偏印" if same_pol else "正印"
        elif con[dm_elem] == t_elem:
            return "偏财" if same_pol else "正财"
        elif con[t_elem] == dm_elem:
            return "七杀" if same_pol else "正官"
        return ""

    @staticmethod
    @st.cache_data(ttl=3600)
    def run_heavy_oracle_analysis(
        bazi: Tuple[str], 
        dm: str, 
        luck: str, 
        annual: str, 
        t: float, 
        injections: Optional[Tuple[str]], 
        birth_dt: Optional[datetime], 
        disp_on: bool
    ) -> Dict[str, Any]:
        """
        Cached wrapper for TrinityOracle.analyze to prevent redundant physics calc.
        """
        return oracle.analyze(
            pillars=list(bazi), 
            day_master=dm, 
            luck_pillar=luck, 
            annual_pillar=annual, 
            t=t, 
            injections=injections, 
            birth_date=birth_dt,
            dispersion_mode=disp_on
        )

    @staticmethod
    @st.cache_data(ttl=3600)
    def run_arbitration_cached(
        bazi_tuple: Tuple[str], 
        binfo: Dict, 
        luck_p: str, 
        annual_p: str, 
        months_s: float, 
        city_name: str, 
        geo_f: float, 
        geo_e: str, 
        scenario_name: str, 
        gender_val: str
    ) -> Dict[str, Any]:
        """
        Cached wrapper for UnifiedArbitrator.arbitrate_bazi with explicit serializable keys.
        """
        ctx = {
            'luck_pillar': luck_p,
            'annual_pillar': annual_p,
            'months_since_switch': months_s,
            'scenario': scenario_name,
            'data': {
                'city': city_name,
                'geo_factor': geo_f,
                'geo_element': geo_e
            }
        }
        # Pass a copy of binfo to avoid side effects
        return quantum_framework.arbitrate_bazi(list(bazi_tuple), binfo.copy() if binfo else {}, ctx)
