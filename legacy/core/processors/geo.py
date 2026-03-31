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
            Also includes:
            - desc: Description
            - temperature_factor: 温度系数（寒暖）
            - humidity_factor: 湿度系数（燥湿）
            - environment_bias: 环境修正偏向描述
        """
        cities = self.geo_data.get("cities", {})
        algo_params = self.geo_data.get("algorithm", {})
        
        modifiers = {}
        
        # 1. Option C: City Lookup
        if isinstance(input_location, str):
            city_info = cities.get(input_location)
            if city_info:
                modifiers = city_info.get("modifiers", {})
                # [V9.3 MCP] 添加环境信息
                modifiers['desc'] = city_info.get("desc", f"City: {input_location}")
                modifiers['temperature_factor'] = city_info.get("temperature_factor", 1.0)
                modifiers['humidity_factor'] = city_info.get("humidity_factor", 1.0)
                modifiers['environment_bias'] = self._get_environment_bias(modifiers)
                return modifiers
                
            # If city not found, return neutral (or implement geocoding later)
            # For now, if city unknown, return default
            return {
                "desc": "Unknown City - Neutral",
                "temperature_factor": 1.0,
                "humidity_factor": 1.0,
                "environment_bias": "未应用地理修正"
            }
            
        # 2. Option B: Latitude Calculation
        if isinstance(input_location, (int, float)):
            result = self._calculate_by_lat(float(input_location), algo_params)
            # [V9.3 MCP] 添加环境信息
            result['temperature_factor'] = self._estimate_temperature_factor(float(input_location))
            result['humidity_factor'] = 1.0  # 默认值，可根据需要扩展
            result['environment_bias'] = self._get_environment_bias(result)
            return result
            
        return {}
    
    def _estimate_temperature_factor(self, latitude: float) -> float:
        """估算温度系数（基于纬度）"""
        abs_lat = abs(latitude)
        # 纬度越高，温度越低（水能量增强，火能量减弱）
        # 纬度越低，温度越高（火能量增强，水能量减弱）
        if abs_lat < 20:  # 低纬度（热带）
            return 1.2  # 热辐射极值
        elif abs_lat < 40:  # 中纬度（温带）
            return 1.0  # 中性
        else:  # 高纬度（寒带）
            return 0.8  # 寒冷
    
    def _get_environment_bias(self, modifiers: Dict[str, float]) -> str:
        """生成环境修正偏向描述"""
        fire_mod = modifiers.get('fire', 1.0)
        water_mod = modifiers.get('water', 1.0)
        wood_mod = modifiers.get('wood', 1.0)
        metal_mod = modifiers.get('metal', 1.0)
        earth_mod = modifiers.get('earth', 1.0)
        
        biases = []
        if fire_mod > 1.1:
            biases.append(f"火能量增强({fire_mod:.2f}x)")
        if water_mod > 1.1:
            biases.append(f"水能量增强({water_mod:.2f}x)")
        if wood_mod > 1.1:
            biases.append(f"木能量增强({wood_mod:.2f}x)")
        if metal_mod > 1.1:
            biases.append(f"金能量增强({metal_mod:.2f}x)")
        if earth_mod > 1.1:
            biases.append(f"土能量增强({earth_mod:.2f}x)")
        
        if not biases:
            return "环境修正偏向：中性（无明显偏向）"
        return f"环境修正偏向：{', '.join(biases)}"
        
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
