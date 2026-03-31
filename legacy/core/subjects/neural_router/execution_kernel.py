"""
[QGA V25.0] 神经网络路由专题执行内核
将八字物理指纹投射到LLM的逻辑潜空间，实现格局智能路由
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .registry import get_neural_router_registry
from .feature_vectorizer import FeatureVectorizer
from .prompt_generator import PromptGenerator
from .matrix_router import MatrixRouter
from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer

logger = logging.getLogger(__name__)


class NeuralRouterKernel:
    """
    神经网络路由专题执行内核
    负责从注册表读取参数，执行神经网络路由逻辑
    """
    
    def __init__(self):
        """初始化执行内核"""
        self.registry = get_neural_router_registry()
        self._llm_synthesizer: Optional[LLMSemanticSynthesizer] = None
        self._feature_vectorizer = FeatureVectorizer()
        self._prompt_generator = PromptGenerator()
        self._matrix_router = MatrixRouter()
        
        # 从注册表读取路由参数
        self.field_strength_threshold = self._get_routing_param("field_strength_threshold", 0.6)
        self.coherence_weight = self._get_routing_param("coherence_weight", 0.75)
        self.entropy_damping = self._get_routing_param("entropy_damping", 0.3)
        
        logger.info(f"✅ 神经网络路由内核初始化完成")
        logger.info(f"   场强阈值: {self.field_strength_threshold}")
        logger.info(f"   相干权重: {self.coherence_weight}")
        logger.info(f"   熵值阻尼: {self.entropy_damping}")
        logger.info(f"   特征向量提取器已加载")
    
    def _get_routing_param(self, param_name: str, default_value: Any) -> Any:
        """
        从注册表获取路由参数值
        
        Args:
            param_name: 参数名称
            default_value: 默认值
            
        Returns:
            参数值
        """
        param_def = self.registry.get_routing_parameter(param_name)
        if param_def:
            return param_def.get("value", default_value)
        return default_value
    
    def _get_llm_synthesizer(self) -> LLMSemanticSynthesizer:
        """获取或创建LLM合成器（延迟初始化）"""
        if self._llm_synthesizer is None:
            self._llm_synthesizer = LLMSemanticSynthesizer()
        return self._llm_synthesizer
    
    def feature_to_latent(self, five_elements_field: Dict[str, float],
                         stress_tensor: Dict[str, float],
                         phase_relationships: List[Dict[str, Any]],
                         synthesized_field: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Feature_to_Latent算子]
        将八字物理指纹（五行、应力、相位）投射到LLM的逻辑潜空间
        
        Args:
            five_elements_field: 五行场强分布
            stress_tensor: 应力张量
            phase_relationships: 相位关系列表
            synthesized_field: 合成场强信息
            
        Returns:
            投射到潜空间的特征向量
        """
        model_config = self.registry.get_physics_model("feature_to_latent")
        output_dim = model_config.get("output_dimension", 256) if model_config else 256
        
        # 构建特征向量（简化实现，实际应该使用神经网络）
        feature_vector = {
            "five_elements": five_elements_field,
            "stress": stress_tensor,
            "phases": phase_relationships,
            "synthesized": synthesized_field,
            "latent_dim": output_dim
        }
        
        logger.debug(f"✅ Feature_to_Latent: 特征向量维度={output_dim}")
        return feature_vector
    
    def sai_collapse(self, pattern_sai_values: Dict[str, float],
                    pattern_weights: Dict[str, float]) -> float:
        """
        [SAI_Collapse算子]
        全量格局扫描后的综合SAI（应变张量）动态结算
        
        Args:
            pattern_sai_values: 各格局的SAI值
            pattern_weights: 各格局的权重
            
        Returns:
            综合SAI值
        """
        model_config = self.registry.get_physics_model("sai_collapse")
        aggregation_method = model_config.get("aggregation_method", "weighted_sum") if model_config else "weighted_sum"
        collapse_threshold = model_config.get("collapse_threshold", 0.7) if model_config else 0.7
        
        if aggregation_method == "weighted_sum":
            # 加权求和
            total_sai = 0.0
            total_weight = 0.0
            
            for pattern_id, sai in pattern_sai_values.items():
                weight = pattern_weights.get(pattern_id, 0.0)
                total_sai += sai * weight
                total_weight += weight
            
            if total_weight > 0:
                aggregated_sai = total_sai / total_weight
            else:
                aggregated_sai = 0.0
            
            # 应用阈值（坍缩）
            if aggregated_sai > collapse_threshold:
                aggregated_sai = collapse_threshold
            
            logger.debug(f"✅ SAI_Collapse: 聚合方法={aggregation_method}, 综合SAI={aggregated_sai:.3f}")
            return aggregated_sai
        else:
            logger.warning(f"⚠️ 未知的聚合方法: {aggregation_method}")
            return 0.0
    
    def process_bazi_profile(self, 
                           active_patterns: List[Dict[str, Any]],
                           synthesized_field: Dict[str, Any],
                           profile_name: str = "此人",
                           day_master: str = None,
                           force_vectors: Dict[str, float] = None,
                           year: int = None,
                           luck_pillar: str = None,
                           year_pillar: str = None,
                           geo_info: str = None) -> Dict[str, Any]:
        """
        [执行入口点]
        处理八字档案，执行神经网络路由逻辑
        
        Args:
            active_patterns: 激活的格局列表
            synthesized_field: 合成场强信息
            profile_name: 档案名称
            day_master: 日主
            force_vectors: 五行能量分布
            year: 流年
            luck_pillar: 大运
            year_pillar: 流年柱
            geo_info: 地理信息
            
        Returns:
            处理结果，包含persona、element_calibration等
        """
        try:
            # 1. 从注册表读取格局定义，构建格局语义
            pattern_semantics = []
            pattern_sai_values = {}
            pattern_weights = {}
            
            for pattern in active_patterns:
                pattern_id = pattern.get("id") or pattern.get("name")
                pattern_def = self.registry.get_pattern_definition(pattern_id)
                
                if pattern_def:
                    pattern_semantics.append({
                        "pattern_id": pattern_id,
                        "pattern_name": pattern_def.get("pattern_name"),
                        "core_conflict": pattern_def.get("core_conflict"),
                        "semantic_keywords": pattern_def.get("semantic_keywords", []),
                        "force_characteristics": pattern_def.get("force_characteristics", {}),
                        "priority_rank": pattern_def.get("priority_rank", 999),
                        "base_strength": pattern_def.get("base_strength", 0.5)
                    })
                    
                    # 收集SAI值和权重（用于SAI_Collapse）
                    sai = pattern.get("sai", pattern_def.get("base_strength", 0.5) * 100)
                    weight = pattern.get("weight", pattern_def.get("base_strength", 0.5))
                    pattern_sai_values[pattern_id] = sai
                    pattern_weights[pattern_id] = weight
            
            # 2. 提取特征向量（Phase 2核心）
            # 从active_patterns中提取chart信息（如果可用）
            chart = None
            luck_pillar_tuple = None
            year_pillar_tuple = None
            
            # 尝试从synthesized_field中提取chart信息
            if synthesized_field:
                # 这里假设synthesized_field包含chart信息
                # 实际使用时需要根据具体数据结构调整
                pass
            
            # 如果无法获取chart，使用force_vectors作为fallback
            if chart is None:
                # 使用force_vectors构建特征向量（简化版）
                feature_vector = {
                    "elemental_fields_dict": force_vectors or {},
                    "stress_tensor": synthesized_field.get("friction_index", 0.0) / 100.0 if synthesized_field else 0.5,
                    "phase_coherence": 0.5,  # 默认值
                    "routing_hint": None,
                    "momentum_term": {}
                }
            else:
                # 使用FeatureVectorizer提取完整特征向量
                feature_vector = self._feature_vectorizer.vectorize_bazi(
                    chart=chart,
                    day_master=day_master,
                    luck_pillar=luck_pillar_tuple,
                    year_pillar=year_pillar_tuple,
                    geo_info=geo_info,
                    micro_env=synthesized_field.get("micro_env") if synthesized_field else None,
                    synthesized_field=synthesized_field
                )
            
            # 从feature_vector中提取elemental_fields
            elemental_fields = feature_vector.get("elemental_fields_dict", force_vectors or {})
            
            # 执行Feature_to_Latent算子（使用提取的特征向量）
            latent_features = self.feature_to_latent(
                five_elements_field=elemental_fields,
                stress_tensor={"total_stress": feature_vector.get("stress_tensor", 0.5)},
                phase_relationships=[
                    {
                        "pattern_id": p.get("id"),
                        "pattern_type": self.registry.get_pattern_definition(p.get("id", "")).get("pattern_type") if p.get("id") else None
                    }
                    for p in active_patterns
                ],
                synthesized_field=synthesized_field
            )
            
            # 3. 执行SAI_Collapse算子
            aggregated_sai = self.sai_collapse(pattern_sai_values, pattern_weights)
            
            # 4. 生成逻辑内联Prompt（Phase 3核心）
            # 构建structured_data（兼容原有格式）
            structured_data = {
                "Context": {
                    "Name": profile_name,
                    "TimeSpace": f"{year}年 | {luck_pillar or '无大运'} | {year_pillar or '无流年'} | {geo_info or '无地理信息'}",
                    "DayMaster": day_master
                },
                "ActivePatterns": [
                    {
                        "Name": p.get("name", ""),
                        "Type": self.registry.get_pattern_definition(p.get("id", "")).get("pattern_type", "Unknown") if p.get("id") else "Unknown",
                        "PriorityRank": self.registry.get_pattern_definition(p.get("id", "")).get("priority_rank", 999) if p.get("id") else 999,
                        "Strength": p.get("weight", p.get("base_strength", 0.5))
                    }
                    for p in active_patterns
                ],
                "RawElements": {
                    "金": int(elemental_fields.get("metal", 0.0) * 100),
                    "木": int(elemental_fields.get("wood", 0.0) * 100),
                    "水": int(elemental_fields.get("water", 0.0) * 100),
                    "火": int(elemental_fields.get("fire", 0.0) * 100),
                    "土": int(elemental_fields.get("earth", 0.0) * 100)
                }
            }
            
            # 生成逻辑内联Prompt
            inline_prompt = self._prompt_generator.generate_inline_prompt(
                active_patterns=active_patterns,
                feature_vector=feature_vector,
                structured_data=structured_data
            )
            
            # 5. 调用LLM合成器生成persona（使用逻辑内联Prompt）
            llm_synthesizer = self._get_llm_synthesizer()
            
            # [Phase 3] 如果LLM合成器支持自定义Prompt，使用逻辑内联Prompt
            # 否则，使用原有方法（保持向后兼容）
            try:
                # 尝试使用逻辑内联Prompt（如果LLM合成器支持）
                if hasattr(llm_synthesizer, 'synthesize_with_custom_prompt'):
                    result = llm_synthesizer.synthesize_with_custom_prompt(
                        inline_prompt=inline_prompt,
                        structured_data=structured_data
                    )
                else:
                    # 回退到原有方法
                    result = llm_synthesizer.synthesize_persona(
                        active_patterns=active_patterns,
                        synthesized_field=synthesized_field,
                        profile_name=profile_name,
                        day_master=day_master,
                        force_vectors=force_vectors,
                        year=year,
                        luck_pillar=luck_pillar,
                        year_pillar=year_pillar,
                        geo_info=geo_info
                    )
            except Exception as e:
                logger.warning(f"⚠️ 逻辑内联Prompt调用失败，回退到原有方法: {e}")
                result = llm_synthesizer.synthesize_persona(
                    active_patterns=active_patterns,
                    synthesized_field=synthesized_field,
                    profile_name=profile_name,
                    day_master=day_master,
                    force_vectors=force_vectors,
                    year=year,
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar,
                    geo_info=geo_info
                )
            
            # 6. [Phase 4] 矩阵路由处理：计算权重坍缩和能量状态
            matrix_result = self._matrix_router.process_matrix_routing(
                active_patterns=active_patterns,
                feature_vector=feature_vector,
                llm_response=result  # LLM响应中可能包含logic_collapse和energy_state_report
            )
            
            # 将矩阵路由结果合并到result中
            result["logic_collapse"] = matrix_result.get("logic_collapse", {})
            result["energy_state_report"] = matrix_result.get("energy_state_report", {})
            
            # 7. 添加专题特定的元数据
            result["neural_router_metadata"] = {
                "field_strength_threshold": self.field_strength_threshold,
                "coherence_weight": self.coherence_weight,
                "entropy_damping": self.entropy_damping,
                "aggregated_sai": aggregated_sai,
                "latent_features_dim": latent_features.get("latent_dim"),
                "pattern_count": len(active_patterns),
                "feature_vector": feature_vector,  # [Phase 2] 添加特征向量
                "inline_prompt_length": len(inline_prompt),  # [Phase 3] 添加Prompt长度
                "matrix_routing": {  # [Phase 4] 添加矩阵路由信息
                    "collapse_weights_count": len(result.get("logic_collapse", {})),
                    "energy_stability": matrix_result.get("energy_state_report", {}).get("system_stability", 0.0)
                }
            }
            
            # 8. 逻辑自愈检查（如果启用）
            optimization_config = self.registry.get_optimization_config()
            if optimization_config.get("self_healing", {}).get("enabled", False):
                self._self_healing_check(result, elemental_fields)
            
            logger.info(f"✅ 神经网络路由处理完成: {profile_name}, 格局数={len(active_patterns)}, 综合SAI={aggregated_sai:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 神经网络路由处理失败: {e}", exc_info=True)
            # 返回错误结果
            return {
                "persona": f"处理失败: {str(e)}",
                "element_calibration": {},
                "error": str(e)
            }
    
    def _self_healing_check(self, result: Dict[str, Any], five_elements: Dict[str, float]):
        """
        逻辑自愈检查：当LLM输出违背物理守恒定律时，触发重读算子进行逻辑强制校准
        
        Args:
            result: LLM处理结果
            five_elements: 五行能量分布
        """
        optimization_config = self.registry.get_optimization_config()
        violation_detection = optimization_config.get("self_healing", {}).get("violation_detection", {})
        
        if violation_detection.get("energy_conservation_check", False):
            # 检查能量守恒（简化实现）
            element_calibration = result.get("element_calibration", {})
            total_energy = sum(abs(v) for v in element_calibration.values() if isinstance(v, (int, float)))
            
            # 如果总能量异常（例如超过阈值），进行校准
            if total_energy > 1000:  # 阈值可配置
                logger.warning(f"⚠️ 能量守恒检查失败: 总能量={total_energy}，触发逻辑自愈")
                # 这里可以添加校准逻辑
        
        # 其他检查可以在这里添加
        logger.debug("✅ 逻辑自愈检查完成")


def process_bazi_profile(*args, **kwargs) -> Dict[str, Any]:
    """
    专题执行入口点（兼容函数式调用）
    
    这个函数是registry.json中execution_kernel.entry_point指定的入口点
    """
    kernel = NeuralRouterKernel()
    return kernel.process_bazi_profile(*args, **kwargs)

