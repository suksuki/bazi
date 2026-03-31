"""
[QGA V25.0] 纯物理稳定性计算器 (Physical Stability Calculator)
方案A优化：分离物理判定和语义分析

功能：
- 纯物理计算系统稳定性（不依赖LLM）
- 基于能量叠加公式计算稳定性
- 支持批量计算，输出全量物理数据包
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from .feature_vectorizer import FeatureVectorizer
from .energy_operator import EnergyOperator

logger = logging.getLogger(__name__)


class PhysicalStabilityCalculator:
    """
    纯物理稳定性计算器
    方案A：物理先导，语义后补
    """
    
    def __init__(self):
        """初始化物理稳定性计算器"""
        self.vectorizer = FeatureVectorizer()
        self.energy_operator = EnergyOperator()
        logger.info("✅ 纯物理稳定性计算器初始化完成（方案A优化）")
    
    def calculate_stability(self, 
                           chart: List[Tuple[str, str]],
                           day_master: str,
                           luck_pillar: Optional[Tuple[str, str]] = None,
                           year_pillar: Optional[Tuple[str, str]] = None,
                           geo_info: Optional[str] = None,
                           pattern_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        计算系统稳定性（纯物理计算，不依赖LLM）
        
        Args:
            chart: 八字列表 [(年干,年支), (月干,月支), (日干,日支), (时干,时支)]
            day_master: 日主
            luck_pillar: 大运柱 (天干, 地支)
            year_pillar: 流年柱 (天干, 地支)
            geo_info: 地理信息
            pattern_config: 格局配置（从registry.json读取）
            
        Returns:
            稳定性计算结果字典
        """
        # 1. 提取特征向量（纯物理计算）
        elemental_fields = self.vectorizer.extract_elemental_fields(
            chart=chart,
            day_master=day_master,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        # 2. 计算应力张量（纯物理计算）
        stress_tensor_value = self.vectorizer.extract_stress_tensor(
            chart=chart,
            day_master=day_master,
            synthesized_field=None
        )
        # 转换为字典格式（用于后续计算）
        stress_tensor = {
            'total': stress_tensor_value,
            'friction': stress_tensor_value
        }
        
        # 3. 计算能量叠加（RSS-V1.2规范：显性化实现）
        # base_energy是标量值，用于后续稳定性计算
        base_energy_value = self._calculate_base_energy(elemental_fields, stress_tensor)
        
        # 大运场能（静态场能）- 转换为字典格式
        luck_energy_dict = self._calculate_luck_energy_dict(luck_pillar, elemental_fields) if luck_pillar else {}
        
        # 流年脉冲（能量脉冲）- 转换为字典格式
        year_energy_dict = self._calculate_year_energy_dict(year_pillar, elemental_fields) if year_pillar else {}
        
        # 能量叠加（RSS-V1.2规范：E_total = [(E_base ⊗ ω_luck) ⊕ ΔE_year] × (1 ± δ_geo)）
        # 使用elemental_fields作为base_energy（字典格式）
        luck_weight = 0.5  # 大运权重
        total_energy = self.energy_operator.tensor_product(elemental_fields, luck_weight)
        if year_energy_dict:
            total_energy = self.energy_operator.direct_sum(total_energy, year_energy_dict)
        
        # 地理修正（±15%限制）
        geo_damping = self.energy_operator.calculate_geo_damping_from_info(geo_info) if geo_info else 0.0
        total_energy = self.energy_operator.geo_correction(total_energy, geo_damping)
        
        # 计算总能量标量值（用于稳定性计算）
        final_energy = sum(total_energy.values())
        
        # 4. 计算系统稳定性（基于能量分布和应力）
        stability = self._calculate_stability_from_energy(
            final_energy,
            stress_tensor,
            elemental_fields,
            pattern_config
        )
        
        # RSS-V1.3重构：显式引入能量阻尼系数
        # Resource_Factor（财星阻尼）：财星作为能量缓冲层
        # Protection_Factor（印星阻尼）：印星作为保护层
        damping_factor = self._calculate_damping_factor(elemental_fields, pattern_config)
        stability = stability * (1.0 + damping_factor)
        stability = min(1.0, stability)  # 确保不超过1.0
        
        # 5. 判断临界状态
        critical_state = self._determine_critical_state(stability, stress_tensor)
        
        # 6. 返回纯物理计算结果（不包含LLM生成的persona）
        return {
            'system_stability': stability,
            'base_energy': base_energy_value,
            'luck_energy': sum(luck_energy_dict.values()) if luck_energy_dict else 0.0,
            'year_energy': sum(year_energy_dict.values()) if year_energy_dict else 0.0,
            'total_energy': final_energy,
            'stress_tensor': stress_tensor,
            'elemental_fields': elemental_fields,
            'critical_state': critical_state,
            'geo_correction': 1.0 + geo_damping,
            'damping_factor': damping_factor,  # RSS-V1.3重构：能量阻尼系数
            # 物理数据包（用于后续LLM分析）
            'physical_data': {
                'chart': chart,
                'day_master': day_master,
                'luck_pillar': luck_pillar,
                'year_pillar': year_pillar,
                'geo_info': geo_info
            }
        }
    
    def _calculate_base_energy(self, elemental_fields: Dict[str, float], 
                              stress_tensor: Dict[str, float]) -> float:
        """计算基础能量"""
        # 基础能量 = 五行场强之和 - 应力损失
        total_field = sum(elemental_fields.values())
        stress_loss = stress_tensor.get('total', 0.0) * 0.1  # 应力损失系数
        return max(0.0, total_field - stress_loss)
    
    def _calculate_luck_energy_dict(self, luck_pillar: Tuple[str, str],
                                   elemental_fields: Dict[str, float]) -> Dict[str, float]:
        """计算大运场能（静态场能）- 字典格式"""
        # 大运场能 = 大运五行场强 × 权重（最高优先级）
        luck_element = self.vectorizer.ELEMENT_MAP.get(luck_pillar[0], 'earth')
        luck_field = elemental_fields.get(luck_element, 0.0)
        luck_energy_dict = {element: 0.0 for element in elemental_fields.keys()}
        luck_energy_dict[luck_element] = luck_field * 0.5  # 大运权重：0.5（基准修正）
        return luck_energy_dict
    
    def _calculate_year_energy_dict(self, year_pillar: Tuple[str, str],
                                    elemental_fields: Dict[str, float]) -> Dict[str, float]:
        """计算流年脉冲（能量脉冲）- 字典格式"""
        # 流年脉冲 = 流年五行场强 × 权重（关键触发）
        year_element = self.vectorizer.ELEMENT_MAP.get(year_pillar[0], 'earth')
        year_field = elemental_fields.get(year_element, 0.0)
        year_energy_dict = {element: 0.0 for element in elemental_fields.keys()}
        year_energy_dict[year_element] = year_field * 0.3  # 流年权重：0.3（关键触发）
        return year_energy_dict
    
    def _calculate_stability_from_energy(self,
                                         total_energy: float,
                                         stress_tensor: Dict[str, float],
                                         elemental_fields: Dict[str, float],
                                         pattern_config: Optional[Dict[str, Any]] = None) -> float:
        """
        从能量计算系统稳定性（0.0-1.0）
        
        稳定性公式：
        S = (1 - stress_ratio) × energy_balance × coherence_factor
        
        其中：
        - stress_ratio: 应力占比（应力/总能量）
        - energy_balance: 能量平衡度（1 - |最大场强 - 最小场强|）
        - coherence_factor: 相干因子（基于格局配置）
        """
        # 1. 计算应力占比
        total_stress = stress_tensor.get('total', 0.0)
        stress_ratio = min(1.0, total_stress / (total_energy + 1e-6))
        
        # 2. 计算能量平衡度（RSS-V1.3修正：使用标准差而非极差）
        # 原公式：energy_balance = 1.0 - abs(max_field - min_field)
        # 问题：当max和min差值很大时，energy_balance会过低（如max=0.8, min=0.0 -> 0.2）
        # 改进：使用归一化的标准差，更能反映整体分布特征
        field_values = list(elemental_fields.values())
        if field_values and len(field_values) > 1:
            std_dev = np.std(field_values)
            mean_val = np.mean(field_values)
            # 使用变异系数（CV）的倒数作为平衡度指标
            # CV = std/mean，平衡度 = 1/(1+CV)，CV越小（越平衡），平衡度越高
            cv = std_dev / (mean_val + 1e-6)  # 避免除零
            energy_balance = 1.0 / (1.0 + cv)
            # 确保在合理范围内（0.1-1.0）
            energy_balance = max(0.1, min(1.0, energy_balance))
        else:
            energy_balance = 0.5
        
        # 3. 计算相干因子（基于格局配置）
        # RSS-V1.3修正：使用非线性衰减模型，避免一刀切归零
        coherence_factor = 1.0
        if pattern_config:
            physical_axiom = pattern_config.get("physical_axiom", {})
            collapse_threshold = physical_axiom.get("collapse_threshold", 0.7)
            
            # 非线性衰减模型：使用指数衰减，避免线性截断导致的逻辑真空
            # 当stress_ratio接近collapse_threshold时，相干因子开始衰减
            # 使用Sigmoid函数：coherence = 1 / (1 + exp(k * (stress_ratio - threshold)))
            # 或者使用指数衰减：coherence = exp(-k * max(0, stress_ratio - threshold_start))
            
            # 衰减起始点：当应力占比超过阈值的70%时开始衰减
            threshold_start = collapse_threshold * 0.7
            # 衰减速率：k值控制衰减速度（k越大，衰减越快）
            # RSS-V1.3修正：从10.0降到5.0，使衰减更平缓，避免过度惩罚
            decay_rate = 5.0  # 可调参数
            
            if stress_ratio > threshold_start:
                # 指数衰减模型：coherence = exp(-k * (stress_ratio - threshold_start))
                excess_stress = stress_ratio - threshold_start
                coherence_factor = np.exp(-decay_rate * excess_stress)
                # 确保最小值不为0（保留0.01的最小值，避免完全归零）
                coherence_factor = max(0.01, coherence_factor)
            else:
                # 在安全范围内，保持完全相干
                coherence_factor = 1.0
        
        # 4. 计算稳定性
        stability = (1.0 - stress_ratio) * energy_balance * coherence_factor
        
        # 5. 标准化到0.0-1.0
        stability = max(0.0, min(1.0, stability))
        
        return stability
    
    def _determine_critical_state(self, stability: float, 
                                 stress_tensor: Dict[str, float]) -> str:
        """
        判断临界状态（纯物理判定）
        
        RSS-V1.2规范：
        - S < 0.15: 逻辑坍缩（奇点）
        - S < 0.3: 临界态（接近逻辑坍缩）
        - S >= 0.3: 波动态（系统存在波动但未达到临界）
        """
        if stability < 0.15:
            return "逻辑坍缩（奇点）"
        elif stability < 0.3:
            return "临界态（接近逻辑坍缩）"
        else:
            return "波动态（系统存在波动，但未达到临界）"
    
    def _calculate_damping_factor(self,
                                  elemental_fields: Dict[str, float],
                                  pattern_config: Optional[Dict[str, Any]] = None) -> float:
        """
        计算能量阻尼系数（RSS-V1.3重构）
        
        显式引入：
        - Resource_Factor（财星阻尼）：earth_field * 0.3
        - Protection_Factor（印星阻尼）：wood_field * 0.2
        
        Args:
            elemental_fields: 五行场强
            pattern_config: 格局配置
            
        Returns:
            阻尼系数（0.0-1.0）
        """
        # Resource_Factor（财星阻尼）：财星作为能量缓冲层，降低剪切力
        earth_field = elemental_fields.get('earth', 0.0)
        resource_damping = earth_field * 0.3
        
        # Protection_Factor（印星阻尼）：印星作为保护层，吸收外部压力
        # 注：印星通常是生助日主的，在五行中可能是木（生火）或其他
        # 这里简化处理，使用wood_field作为印星的代表
        wood_field = elemental_fields.get('wood', 0.0)
        protection_damping = wood_field * 0.2
        
        # 总阻尼系数
        total_damping = resource_damping + protection_damping
        
        # 限制在合理范围内（0.0-1.0）
        total_damping = max(0.0, min(1.0, total_damping))
        
        logger.debug(f"📊 能量阻尼系数: resource={resource_damping:.4f}, "
                    f"protection={protection_damping:.4f}, total={total_damping:.4f}")
        
        return total_damping
    
    def batch_calculate_stability(self,
                                 samples: List[Dict[str, Any]],
                                 pattern_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        批量计算系统稳定性（方案A：全量物理计算）
        
        Args:
            samples: 样本列表（来自Step A）
            pattern_config: 格局配置
            
        Returns:
            所有样本的稳定性计算结果列表
        """
        results = []
        
        logger.info(f"🔬 开始批量计算稳定性（方案A：纯物理计算，共{len(samples)}个样本）...")
        
        for i, sample in enumerate(samples):
            if i % 100 == 0:
                logger.info(f"📊 计算进度: {i}/{len(samples)} ({i/len(samples)*100:.1f}%)")
            
            try:
                # 解析样本数据
                chart = sample.get('chart', [])
                day_master = sample.get('day_master', '')
                
                if not chart or not day_master:
                    continue
                
                # 计算稳定性（纯物理计算）
                stability_result = self.calculate_stability(
                    chart=chart,
                    day_master=day_master,
                    luck_pillar=sample.get('luck_pillar'),
                    year_pillar=sample.get('year_pillar'),
                    geo_info=sample.get('geo_info'),
                    pattern_config=pattern_config
                )
                
                # 合并样本信息和稳定性结果
                result = {
                    **sample,  # 保留原始样本信息
                    **stability_result  # 添加稳定性计算结果
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ 计算样本 {i} 失败: {e}")
                continue
        
        logger.info(f"✅ 批量计算完成: {len(results)}/{len(samples)} 个样本")
        
        return results

