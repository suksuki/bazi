"""
[QGA V25.0 Phase 4] 矩阵路由器核心实现
实现自动权重坍缩和全场能量状态审计
"""

import logging
from typing import Dict, List, Optional, Any
from .registry import get_neural_router_registry

logger = logging.getLogger(__name__)


class MatrixRouter:
    """
    矩阵路由器
    负责处理逻辑权重坍缩和全场能量状态审计
    """
    
    def __init__(self):
        """初始化矩阵路由器"""
        self.registry = get_neural_router_registry()
        logger.info("✅ 矩阵路由器初始化完成")
    
    def compute_weight_collapse(self, 
                                active_patterns: List[Dict[str, Any]],
                                feature_vector: Dict[str, Any],
                                llm_collapse_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        计算逻辑权重坍缩
        
        Args:
            active_patterns: 激活的格局列表
            feature_vector: 特征向量
            llm_collapse_weights: LLM返回的权重坍缩值（可选）
            
        Returns:
            格局ID到权重贡献百分比的字典
        """
        if not active_patterns:
            return {}
        
        # 如果LLM提供了权重，优先使用
        if llm_collapse_weights:
            # 验证权重总和是否合理（0.95-1.05）
            total_weight = sum(llm_collapse_weights.values())
            if 0.95 <= total_weight <= 1.05:
                logger.debug(f"✅ LLM权重坍缩验证通过，总和={total_weight:.3f}")
                return llm_collapse_weights
            else:
                logger.warning(f"⚠️ LLM权重总和异常（{total_weight:.3f}），进行归一化")
                # 归一化
                return {k: v / total_weight for k, v in llm_collapse_weights.items()}
        
        # 否则，使用基于优先级和强度的自动计算
        pattern_weights = {}
        total_strength = 0.0
        
        for pattern in active_patterns:
            pattern_id = pattern.get("id") or pattern.get("name")
            pattern_def = self.registry.get_pattern_definition(pattern_id)
            
            if pattern_def:
                # 权重 = base_strength × priority_weight × match_confidence
                base_strength = pattern_def.get("base_strength", 0.5)
                priority_rank = pattern_def.get("priority_rank", 999)
                priority_weight = 1.0 / (priority_rank + 1)  # Rank=1权重最高
                match_confidence = pattern.get("confidence", pattern.get("weight", 0.5))
                
                weight = base_strength * priority_weight * match_confidence
                pattern_weights[pattern_id] = weight
                total_strength += weight
        
        # 归一化到0.0-1.0
        if total_strength > 0:
            normalized_weights = {k: v / total_strength for k, v in pattern_weights.items()}
        else:
            normalized_weights = {k: 1.0 / len(pattern_weights) for k in pattern_weights.keys()}
        
        logger.debug(f"✅ 自动权重坍缩计算完成，格局数={len(normalized_weights)}")
        return normalized_weights
    
    def analyze_energy_state(self,
                            active_patterns: List[Dict[str, Any]],
                            feature_vector: Dict[str, Any],
                            llm_energy_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析全场能量状态
        
        Args:
            active_patterns: 激活的格局列表
            feature_vector: 特征向量
            llm_energy_report: LLM返回的能量状态报告（可选）
            
        Returns:
            能量状态报告字典
        """
        # 如果LLM提供了能量状态报告，优先使用
        if llm_energy_report:
            logger.debug("✅ 使用LLM能量状态报告")
            return llm_energy_report
        
        # 否则，基于特征向量自动计算
        stress_tensor = feature_vector.get("stress_tensor", 0.0)
        phase_coherence = feature_vector.get("phase_coherence", 0.5)
        elemental_fields = feature_vector.get("elemental_fields_dict", {})
        
        # 计算系统稳定性（基于应力和相位一致性）
        system_stability = phase_coherence * (1.0 - stress_tensor * 0.5)
        system_stability = max(0.0, min(1.0, system_stability))
        
        # 判断临界状态
        if stress_tensor > 0.7:
            critical_state = "崩态（系统不稳定，存在结构性冲突）"
        elif stress_tensor > 0.5:
            critical_state = "临界态（系统处于临界点，需要谨慎处理）"
        elif phase_coherence > 0.7:
            critical_state = "稳态（系统能量流平滑，处于稳定状态）"
        else:
            critical_state = "波动态（系统存在波动，但未达到临界）"
        
        # 计算能量流向（简化实现：基于五行场强分布）
        max_element = max(elemental_fields.items(), key=lambda x: x[1])[0] if elemental_fields else "未知"
        energy_flow_direction = f"能量主要流向{max_element}元素场"
        
        # 计算总能量（简化实现：五行场强总和）
        total_energy = sum(elemental_fields.values()) if elemental_fields else 0.0
        
        energy_report = {
            "system_stability": system_stability,
            "energy_flow_direction": energy_flow_direction,
            "critical_state": critical_state,
            "total_energy": total_energy,
            "stress_tensor": stress_tensor,
            "phase_coherence": phase_coherence
        }
        
        logger.debug(f"✅ 自动能量状态分析完成，稳定性={system_stability:.3f}，临界状态={critical_state}")
        return energy_report
    
    def process_matrix_routing(self,
                              active_patterns: List[Dict[str, Any]],
                              feature_vector: Dict[str, Any],
                              llm_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        [主入口点]
        处理矩阵路由，计算权重坍缩和能量状态
        
        Args:
            active_patterns: 激活的格局列表
            feature_vector: 特征向量
            llm_response: LLM响应（可选，包含logic_collapse和energy_state_report）
            
        Returns:
            包含权重坍缩和能量状态的字典
        """
        # 提取LLM返回的权重坍缩和能量状态报告
        llm_collapse_weights = None
        llm_energy_report = None
        
        if llm_response:
            llm_collapse_weights = llm_response.get("logic_collapse")
            llm_energy_report = llm_response.get("energy_state_report")
        
        # 计算权重坍缩
        collapse_weights = self.compute_weight_collapse(
            active_patterns=active_patterns,
            feature_vector=feature_vector,
            llm_collapse_weights=llm_collapse_weights
        )
        
        # 分析能量状态
        energy_state = self.analyze_energy_state(
            active_patterns=active_patterns,
            feature_vector=feature_vector,
            llm_energy_report=llm_energy_report
        )
        
        result = {
            "logic_collapse": collapse_weights,
            "energy_state_report": energy_state
        }
        
        logger.info(f"✅ 矩阵路由处理完成，格局数={len(active_patterns)}，权重坍缩格局数={len(collapse_weights)}")
        return result

