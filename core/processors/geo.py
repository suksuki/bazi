import json
import os
from core.processors.base import BaseProcessor
from typing import Dict, Any

class GeoProcessor(BaseProcessor):
    """
    Layer 0: Geographic Correction Processor
    
    Adjusts elemental weights based on location (City or Latitude).
    Implements Hybrid Model: City Lookup Table + Latitude Linear Regression.
    """
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
        self.geo_data = self._load_data()
        
    def _load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                return json.load(f)
        return {"cities": {}, "formula": {}}

    @property
    def name(self) -> str:
        return "Geo Layer 0"
        
    def process(self, input_location: Any) -> Dict[str, float]:
        """
        Calculate geographic elemental modifiers.
        
        Args:
            input_location: City name (str) OR Latitude (float)
            
        Returns:
            Dict[str, float]: Multipliers for elements {'water': 1.1, ...}
        """
        cities = self.geo_data.get("cities", {})
        algo_params = self.geo_data.get("algorithm", {})
        
        modifiers = {}
        
        # 1. Option C: City Lookup
        if isinstance(input_location, str):
            city_info = cities.get(input_location)
            if city_info:
                return city_info.get("modifiers", {})
                
            # If city not found, return neutral (or implement geocoding later)
            # For now, if city unknown, return default
            return {"desc": "Unknown City - Neutral"}
            
        # 2. Option B: Latitude Calculation
        if isinstance(input_location, (int, float)):
            return self._calculate_by_lat(float(input_location), algo_params)
            
        return {}
        
    def _calculate_by_lat(self, lat: float, params: dict) -> dict:
        """
        Calculates elemental modifiers based on latitude using linear interpolation.
        
        Model:
        Interpolate between Equator Bonus (at 0 deg) and Polar Bonus (at max_lat deg).
        """
        abs_lat = abs(float(lat))
        max_lat = params.get("max_lat", 60.0)
        
        # Normalize ratio (0.0 to 1.0)
        ratio = min(abs_lat, max_lat) / max_lat
        
        eq_bonus = params.get("equator_bonus", {})
        pl_bonus = params.get("polar_bonus", {})
        
        modifiers = {"desc": f"Lat {lat} Approximation"}
        
        # Elements to adjust
        elements = ['wood', 'fire', 'earth', 'metal', 'water']
        
        for elem in elements:
            # Linear Interpolation: y = y1 + (y2 - y1) * x
            start_val = eq_bonus.get(elem, 0.0)
            end_val = pl_bonus.get(elem, 0.0)
            
            adjustment = start_val + (end_val - start_val) * ratio
            
            # Base is 1.0
            modifiers[elem] = round(1.0 + adjustment, 3)
            
        return modifiers
