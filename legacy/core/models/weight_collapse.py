"""
[QGA V24.7] P.F.A权重坍缩算法
当激活多个格局时，根据Strength和PriorityRank进行非线性加权
核心公式：主格局权重=0.7，其余格局瓜分剩余0.3
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class WeightCollapseAlgorithm:
    """
    P.F.A权重坍缩算法
    
    功能：
    1. 根据PriorityRank和Strength进行非线性加权
    2. 主格局获得0.7权重，其余格局瓜分剩余0.3
    3. 确保权重总和为1.0
    """
    
    PRIMARY_WEIGHT = 0.7  # 主格局权重
    SECONDARY_WEIGHT = 0.3  # 次格局总权重
    
    @staticmethod
    def collapse_pattern_weights(patterns: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        权重坍缩：为每个格局分配权重
        
        Args:
            patterns: 格局列表，每个格局包含：
                - name: 格局名称
                - PriorityRank: 优先级（1=最高）
                - Strength: 强度（0.0-1.0）
                - Type: 格局类型
                
        Returns:
            [(pattern, weight), ...] 列表，按权重降序排列
            weight: 0.0-1.0，该格局的权重
        """
        if not patterns:
            return []
        
        # 按PriorityRank和Strength排序
        sorted_patterns = sorted(
            patterns,
            key=lambda p: (
                p.get('PriorityRank', 999),  # PriorityRank越小越优先
                -p.get('Strength', 0.0)  # Strength越大越优先
            )
        )
        
        # 识别主格局（PriorityRank=1或Strength最高）
        primary_pattern = sorted_patterns[0]
        secondary_patterns = sorted_patterns[1:]
        
        # 分配权重
        result = []
        
        # 主格局获得0.7权重
        result.append((primary_pattern, WeightCollapseAlgorithm.PRIMARY_WEIGHT))
        
        # 次格局瓜分剩余0.3权重（按Strength比例分配）
        if secondary_patterns:
            total_secondary_strength = sum(p.get('Strength', 0.0) for p in secondary_patterns)
            
            if total_secondary_strength > 0:
                # 按Strength比例分配
                for pattern in secondary_patterns:
                    strength = pattern.get('Strength', 0.0)
                    weight = (strength / total_secondary_strength) * WeightCollapseAlgorithm.SECONDARY_WEIGHT
                    result.append((pattern, weight))
            else:
                # 如果所有次格局Strength都为0，平均分配
                avg_weight = WeightCollapseAlgorithm.SECONDARY_WEIGHT / len(secondary_patterns)
                for pattern in secondary_patterns:
                    result.append((pattern, avg_weight))
        
        # 按权重降序排列
        result.sort(key=lambda x: x[1], reverse=True)
        
        # 验证权重总和（应该接近1.0）
        total_weight = sum(w for _, w in result)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"权重总和异常: {total_weight}, 进行归一化")
            # 归一化
            result = [(p, w / total_weight) for p, w in result]
        
        logger.info(f"✅ 权重坍缩完成: 主格局={primary_pattern.get('name')} (权重={result[0][1]:.2f})")
        
        return result
    
    @staticmethod
    def get_primary_pattern(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取主格局（权重最高的格局）
        
        Args:
            patterns: 格局列表
            
        Returns:
            主格局字典
        """
        if not patterns:
            return {}
        
        weighted_patterns = WeightCollapseAlgorithm.collapse_pattern_weights(patterns)
        if weighted_patterns:
            return weighted_patterns[0][0]
        return patterns[0]  # 回退到第一个


class VectorFieldCalibration:
    """
    五行矢量反向校准 (V.F.I - Vector Field Indicator)
    
    功能：
    1. 根据格局引擎提供的vector_bias计算总偏移
    2. 应用权重坍缩后的格局权重
    3. 确保能量守恒（总和保持100%）
    4. 限制LLM修正幅度（最大±30%）
    """
    
    MAX_LLM_ADJUSTMENT = 0.3  # LLM最大修正幅度（30%）
    
    @staticmethod
    def calculate_weighted_bias(patterns_with_weights: List[Tuple[Dict[str, Any], float]],
                               pattern_engines: Dict[str, Any],
                               geo_context: Optional[str] = None) -> Dict[str, float]:
        """
        计算加权后的五行矢量偏移
        
        Args:
            patterns_with_weights: [(pattern, weight), ...] 权重坍缩后的格局列表
            pattern_engines: {pattern_name: PatternEngine} 格局引擎字典
            geo_context: 地理环境（如 "北方/北京"）
            
        Returns:
            五行矢量偏移字典 {metal: float, wood: float, water: float, fire: float, earth: float}
        """
        from core.models.pattern_engine import VectorBias
        
        total_bias = VectorBias()
        
        for pattern, weight in patterns_with_weights:
            pattern_name = pattern.get('name', '')
            engine = pattern_engines.get(pattern_name)
            
            if engine:
                # 构造简化的match_result（实际应该使用真实的match_result）
                from core.models.pattern_engine import PatternMatchResult
                match_result = PatternMatchResult(
                    matched=True,
                    confidence=pattern.get('Strength', 0.5),
                    match_data={},
                    sai=pattern.get('sai', 0.0),
                    stress=pattern.get('stress', 0.0)
                )
                
                # 获取格局的vector_bias
                bias = engine.vector_bias(match_result, geo_context)
                
                # 加权累加
                total_bias.metal += bias.metal * weight
                total_bias.wood += bias.wood * weight
                total_bias.water += bias.water * weight
                total_bias.fire += bias.fire * weight
                total_bias.earth += bias.earth * weight
        
        return total_bias.to_dict()
    
    @staticmethod
    def apply_llm_calibration(base_bias: Dict[str, float],
                             llm_calibration: Dict[str, float],
                             original_elements: Dict[str, float]) -> Dict[str, float]:
        """
        应用LLM校准（限制修正幅度）
        
        Args:
            base_bias: 格局引擎计算的基础偏移
            llm_calibration: LLM推导的校准值
            original_elements: 原始五行值（用于计算最大修正幅度）
            
        Returns:
            最终校准后的五行值字典（中文key: 金, 木, 水, 火, 土）
        """
        element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
        cn_to_en = {v: k for k, v in element_map.items()}
        
        # 限制LLM修正幅度
        max_adjustment = {}
        for cn_name, val in original_elements.items():
            max_adjustment[cn_name] = val * VectorFieldCalibration.MAX_LLM_ADJUSTMENT
        
        # 计算最终值
        final_elements = {}
        for cn_name, original_val in original_elements.items():
            en_name = cn_to_en[cn_name]
            
            # 基础偏移（来自格局引擎）
            base_offset = base_bias.get(en_name, 0.0)
            
            # LLM校准（限制幅度）
            llm_offset = llm_calibration.get(en_name, 0.0)
            llm_offset = max(-max_adjustment[cn_name], 
                           min(max_adjustment[cn_name], llm_offset))
            
            # 最终值
            final_val = original_val + base_offset + llm_offset
            final_val = max(0.0, final_val)  # 非负约束
            
            final_elements[cn_name] = final_val
        
        # 能量守恒：归一化到原始总和
        original_sum = sum(original_elements.values())
        final_sum = sum(final_elements.values())
        
        if final_sum > 0 and abs(final_sum - original_sum) > 0.01:
            scale_factor = original_sum / final_sum
            for key in final_elements:
                final_elements[key] *= scale_factor
        
        return final_elements

