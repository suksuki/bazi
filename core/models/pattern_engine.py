"""
[QGA V24.7] 格局引擎基类与注册机制
将10+种物理格局封装成独立的Pattern_Engine类
每个格局引擎包含：matching_logic、semantic_definition、vector_bias
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PatternMatchResult:
    """格局匹配结果"""
    matched: bool
    confidence: float  # 0.0-1.0，匹配置信度
    match_data: Dict[str, Any]  # 匹配的详细信息
    sai: float = 0.0  # SAI值（格局强度）
    stress: float = 0.0  # Stress值（格局压力）


@dataclass
class VectorBias:
    """五行矢量偏移"""
    metal: float = 0.0
    wood: float = 0.0
    water: float = 0.0
    fire: float = 0.0
    earth: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'metal': self.metal,
            'wood': self.wood,
            'water': self.water,
            'fire': self.fire,
            'earth': self.earth
        }


class PatternEngine(ABC):
    """
    格局引擎基类
    
    每个格局引擎必须实现：
    - matching_logic: 判定规则
    - semantic_definition: 给LLM看的硬核物理判词
    - vector_bias: 预设的五行受力偏移方向
    """
    
    def __init__(self, pattern_id: str, pattern_name: str, pattern_type: str = "Normal"):
        """
        初始化格局引擎
        
        Args:
            pattern_id: 格局ID（如 "CONG_ER_GE"）
            pattern_name: 格局名称（如 "从儿格"）
            pattern_type: 格局类型（"Special" / "Conflict" / "Normal"）
        """
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.pattern_type = pattern_type
        self.priority_rank: Optional[int] = None  # 优先级（1=最高）
        self.base_strength: float = 0.5  # 基础强度（0.0-1.0）
    
    @abstractmethod
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str, 
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        判定规则：检查八字是否匹配此格局
        
        Args:
            chart: 八字列表 [(年干,年支), (月干,月支), (日干,日支), (时干,时支)]
            day_master: 日主（如 "甲"）
            luck_pillar: 大运柱 (天干, 地支)
            year_pillar: 流年柱 (天干, 地支)
            synthesized_field: 合成场强信息
            
        Returns:
            PatternMatchResult: 匹配结果
        """
        pass
    
    @abstractmethod
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        给LLM看的硬核物理判词
        
        Args:
            match_result: 匹配结果
            geo_context: 地理环境（如 "北方/北京" / "南方/火地" / "近水环境"）
            
        Returns:
            物理逻辑描述字符串
        """
        pass
    
    @abstractmethod
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        预设的五行受力偏移方向
        
        Args:
            match_result: 匹配结果
            geo_context: 地理环境
            
        Returns:
            VectorBias: 五行矢量偏移
        """
        pass
    
    def get_priority_rank(self) -> int:
        """获取优先级（1=最高）"""
        return self.priority_rank if self.priority_rank is not None else 999
    
    def get_base_strength(self) -> float:
        """获取基础强度"""
        return self.base_strength


class PatternEngineRegistry:
    """
    格局引擎注册表
    
    统一管理所有格局引擎实例
    """
    
    def __init__(self):
        self._engines: Dict[str, PatternEngine] = {}
        self._engines_by_name: Dict[str, PatternEngine] = {}
    
    def register(self, engine: PatternEngine):
        """注册格局引擎"""
        self._engines[engine.pattern_id] = engine
        self._engines_by_name[engine.pattern_name] = engine
        logger.info(f"✅ 注册格局引擎: {engine.pattern_id} ({engine.pattern_name})")
    
    def get_by_id(self, pattern_id: str) -> Optional[PatternEngine]:
        """根据ID获取引擎"""
        return self._engines.get(pattern_id)
    
    def get_by_name(self, pattern_name: str) -> Optional[PatternEngine]:
        """根据名称获取引擎"""
        return self._engines_by_name.get(pattern_name)
    
    def get_all_engines(self) -> List[PatternEngine]:
        """获取所有引擎"""
        return list(self._engines.values())
    
    def detect_patterns(self, chart: List[Tuple[str, str]], 
                       day_master: str,
                       luck_pillar: Optional[Tuple[str, str]] = None,
                       year_pillar: Optional[Tuple[str, str]] = None,
                       synthesized_field: Optional[Dict] = None) -> List[Tuple[PatternEngine, PatternMatchResult]]:
        """
        检测所有匹配的格局
        
        Returns:
            [(engine, match_result), ...] 列表，按置信度降序排列
        """
        results = []
        
        for engine in self._engines.values():
            try:
                match_result = engine.matching_logic(
                    chart, day_master, luck_pillar, year_pillar, synthesized_field
                )
                if match_result.matched:
                    results.append((engine, match_result))
            except Exception as e:
                logger.warning(f"格局引擎 {engine.pattern_id} 检测失败: {e}")
        
        # 按置信度降序排列
        results.sort(key=lambda x: x[1].confidence, reverse=True)
        
        return results


# 全局注册表实例
_pattern_registry = PatternEngineRegistry()


def get_pattern_registry() -> PatternEngineRegistry:
    """获取全局格局引擎注册表"""
    return _pattern_registry


# ============================================================================
# 示例：从儿格引擎实现
# ============================================================================

class CongErGeEngine(PatternEngine):
    """
    从儿格引擎
    [从儿格等离子喷泉 ✨]
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="CONG_ER_GE",
            pattern_name="从儿格",
            pattern_type="Special"
        )
        self.priority_rank = 1  # 特殊格局，高优先级
        self.base_strength = 0.85
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        从儿格判定：日主弱，食伤极旺，不见印比
        """
        # 简化实现（实际应该调用PatternScout）
        # 这里仅作为示例
        
        # 检查是否有食伤
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        stems = [p[0] for p in chart]
        shi_shen_list = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
        
        # 统计食伤数量
        shi_shang_count = sum(1 for ss in shi_shen_list if ss in ['食神', '伤官'])
        
        if shi_shang_count >= 2:
            # 简化的匹配逻辑
            return PatternMatchResult(
                matched=True,
                confidence=0.8,
                match_data={'shi_shang_count': shi_shang_count},
                sai=0.85,
                stress=0.3
            )
        
        return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        从儿格的物理判词（根据地理环境）
        """
        if geo_context in ["北方/北京", "近水环境"]:
            return "等离子喷泉遭遇极寒冷却，才华产出虽高但无法变现/受阻"
        elif geo_context in ["南方/火地"]:
            return "才华在火环境中得到充分激活，但需注意过度消耗"
        else:
            return "从儿格（火土）格局，才华如等离子喷泉般喷发，但需要适当的环境激活"
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        从儿格的五行偏移（根据地理环境调整）
        """
        if geo_context in ["北方/北京", "近水环境"]:
            # 火被水克，火元素减少
            return VectorBias(fire=-15.0, water=+10.0)
        elif geo_context in ["南方/火地"]:
            # 火得到激活，火元素增加
            return VectorBias(fire=+10.0)
        else:
            # 默认：火土增加
            return VectorBias(fire=+5.0, earth=+5.0)


# [QGA V24.7] 注册从儿格引擎（用于测试）
# 注意：实际使用时应该从logic_registry动态加载所有格局引擎
# 这里先手动注册一个示例引擎用于测试
def _register_default_engines():
    """注册默认格局引擎（用于测试）"""
    registry = get_pattern_registry()
    # 注册从儿格引擎
    if not registry.get_by_id("CONG_ER_GE"):
        registry.register(CongErGeEngine())
        logger.info("✅ 已注册从儿格引擎（默认）")

# 自动注册（模块导入时）
_register_default_engines()

# [QGA V24.7] 导入并注册所有格局引擎实现
try:
    from core.models.pattern_engine_implementations import register_all_pattern_engines
    register_all_pattern_engines()
except ImportError as e:
    logger.warning(f"⚠️ 无法导入格局引擎实现: {e}，仅使用默认引擎")
except Exception as e:
    logger.warning(f"⚠️ 格局引擎注册失败: {e}")

