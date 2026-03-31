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
        
        Returns:
            Dict containing:
            - era_element: 时代元素
            - period: 周期编号
            - desc: 描述（如"九紫离火运"）
            - modifiers: 修正系数
            - era_bonus: 时代红利系数
            - era_penalty: 时代折损系数
            - impact_description: 影响描述
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
        
        # [V9.3 MCP] 计算时代红利和折损
        era_bonus = 0.2  # 时代元素 +20%
        era_penalty = -0.1  # 被克元素 -10%
        
        # 确定被克元素（时代元素克制的元素）
        CONTROL = {
            'wood': 'earth', 'fire': 'metal', 'earth': 'water',
            'metal': 'wood', 'water': 'fire'
        }
        controlled_element = CONTROL.get(element)
        
        modifiers = {
            element: 1.0 + era_bonus  # 时代元素增强
        }
        if controlled_element:
            modifiers[controlled_element] = 1.0 + era_penalty  # 被克元素减弱
        
        # [V9.3 MCP] 生成影响描述
        element_names = {
            'wood': '木', 'fire': '火', 'earth': '土', 
            'metal': '金', 'water': '水'
        }
        element_name = element_names.get(element, element)
        controlled_name = element_names.get(controlled_element, controlled_element) if controlled_element else None
        
        impact_parts = [f"{element_name}能量增强 {era_bonus*100:.0f}%"]
        if controlled_name:
            impact_parts.append(f"{controlled_name}能量减弱 {abs(era_penalty)*100:.0f}%")
        impact_description = "；".join(impact_parts)
        
        # Era Bonus: The era element is stronger globally
        return {
            "era_element": element,
            "period": current_period["period"],
            "desc": current_period["desc"],
            "modifiers": modifiers,
            "era_bonus": era_bonus,  # [V9.3 MCP] 时代红利系数
            "era_penalty": era_penalty,  # [V9.3 MCP] 时代折损系数
            "impact_description": impact_description,  # [V9.3 MCP] 影响描述
            "start_year": current_period["start"],
            "end_year": current_period["end"]
        }
