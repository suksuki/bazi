"""
[QGA V25.0] 格局引擎具体实现（逻辑真空化版本）
移除硬编码判定逻辑，改为从PatternDefinitionRegistry读取物理特性描述
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from core.models.pattern_engine import (
    PatternEngine, PatternMatchResult, VectorBias
)
from core.models.pattern_definition_registry import get_pattern_definition_registry

logger = logging.getLogger(__name__)


def _get_pattern_definition(pattern_id: str):
    """获取格局定义的辅助函数"""
    registry = get_pattern_definition_registry()
    return registry.get_by_id(pattern_id)


def _create_vacuum_matching_logic():
    """创建真空化的matching_logic方法"""
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        [QGA V25.0] 逻辑真空化：移除硬编码判定逻辑
        判定逻辑将由Phase 2的特征向量提取器负责
        """
        return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    return matching_logic


def _create_registry_semantic_definition():
    """创建从注册表读取的semantic_definition方法"""
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        [QGA V25.0] 从PatternDefinitionRegistry读取物理判词
        """
        definition = _get_pattern_definition(self.pattern_id)
        
        if definition:
            base_text = definition.core_conflict
            # 根据地理环境微调（保留原有逻辑）
            if geo_context:
                if geo_context in ["北方/北京", "近水环境"]:
                    return f"{base_text}，在寒性环境下，冲突进一步激化"
                elif geo_context in ["南方/火地"]:
                    return f"{base_text}，在火环境中得到一定缓解"
            return base_text
        
        return "格局物理特性待定义"
    return semantic_definition


def _create_registry_vector_bias():
    """创建从注册表读取的vector_bias方法"""
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        [QGA V25.0] 从PatternDefinitionRegistry读取五行偏移
        """
        definition = _get_pattern_definition(self.pattern_id)
        
        if definition:
            force_chars = definition.force_characteristics
            bias = VectorBias(
                metal=force_chars.get("metal", 0.0),
                wood=force_chars.get("wood", 0.0),
                water=force_chars.get("water", 0.0),
                fire=force_chars.get("fire", 0.0),
                earth=force_chars.get("earth", 0.0)
            )
            
            # 根据地理环境微调（保留原有逻辑）
            if geo_context in ["北方/北京", "近水环境"]:
                bias.water += 5.0
            elif geo_context in ["南方/火地"]:
                bias.fire += 5.0
            
            return bias
        
        return VectorBias()
    return vector_bias


# ============================================================================
# 格局引擎类定义（逻辑真空化版本）
# ============================================================================

class ShangGuanJianGuanEngine(PatternEngine):
    """
    伤官见官引擎 (Structural Failure Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="SHANG_GUAN_JIAN_GUAN",
            pattern_name="伤官见官",
            pattern_type="Conflict"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 2
            self.base_strength = 0.75
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


class HuaHuoGeEngine(PatternEngine):
    """
    化火格引擎 (Phase Transition Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="HUA_HUO_GE",
            pattern_name="化火格",
            pattern_type="Special"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 1
            self.base_strength = 0.85
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


class XiaoShenDuoShiEngine(PatternEngine):
    """
    枭神夺食引擎 (Biological Energy Supply Interruption Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="XIAO_SHEN_DUO_SHI",
            pattern_name="枭神夺食",
            pattern_type="Conflict"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 2
            self.base_strength = 0.7
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


class JianLuYueJieEngine(PatternEngine):
    """
    建禄月劫引擎 (Thermodynamic Positive Feedback Explosion Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="JIAN_LU_YUE_JIE",
            pattern_name="建禄月劫",
            pattern_type="Special"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 1
            self.base_strength = 0.8
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


class GuanYinXiangShengEngine(PatternEngine):
    """
    官印相生引擎 (Steady-State Laminar Flow Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="GUAN_YIN_XIANG_SHENG",
            pattern_name="官印相生",
            pattern_type="Normal"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 3
            self.base_strength = 0.65
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


class YangRenJiaShaEngine(PatternEngine):
    """
    羊刃架杀引擎 (High-Pressure Fusion Engine)
    [QGA V25.0] 逻辑真空化：判定逻辑已移除
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="YANG_REN_JIA_SHA",
            pattern_name="羊刃架杀",
            pattern_type="Special"
        )
        definition = _get_pattern_definition(self.pattern_id)
        if definition:
            self.priority_rank = definition.priority_rank
            self.base_strength = definition.base_strength
        else:
            self.priority_rank = 1
            self.base_strength = 0.9
    
    matching_logic = _create_vacuum_matching_logic()
    semantic_definition = _create_registry_semantic_definition()
    vector_bias = _create_registry_vector_bias()


# 注册所有格局引擎的函数
def register_all_pattern_engines():
    """注册所有格局引擎到全局注册表"""
    from core.models.pattern_engine import get_pattern_registry
    
    registry = get_pattern_registry()
    
    # 注册所有引擎
    engines = [
        ShangGuanJianGuanEngine(),
        HuaHuoGeEngine(),
        YangRenJiaShaEngine(),
        XiaoShenDuoShiEngine(),
        JianLuYueJieEngine(),
        GuanYinXiangShengEngine(),
    ]
    
    for engine in engines:
        if not registry.get_by_id(engine.pattern_id):
            registry.register(engine)
            logger.info(f"✅ 已注册格局引擎: {engine.pattern_id} ({engine.pattern_name})")


# 自动注册（模块导入时）
register_all_pattern_engines()

