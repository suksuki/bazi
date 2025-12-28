"""
[QGA V25.0] 特征向量提取器 (Feature Vectorizer)
将八字物理指纹转化为标准化的数字向量，为神经网络路由提供高纯度燃料
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from .energy_operator import EnergyOperator

logger = logging.getLogger(__name__)


class FeatureVectorizer:
    """
    特征向量提取器
    将八字原局转换为标准化的特征向量矩阵
    """
    
    # 五行元素映射
    ELEMENT_MAP = {
        '甲': 'wood', '乙': 'wood',
        '丙': 'fire', '丁': 'fire',
        '戊': 'earth', '己': 'earth',
        '庚': 'metal', '辛': 'metal',
        '壬': 'water', '癸': 'water',
    }
    
    # 地支五行映射
    BRANCH_ELEMENT_MAP = {
        '子': 'water', '亥': 'water',
        '寅': 'wood', '卯': 'wood',
        '午': 'fire', '巳': 'fire',
        '申': 'metal', '酉': 'metal',
        '辰': 'earth', '戌': 'earth', '丑': 'earth', '未': 'earth',
    }
    
    # 宫位权重（用于计算能级）
    PILLAR_WEIGHTS = {
        'year': 0.7,
        'month': 1.42,  # 月令权重最高
        'day': 1.35,
        'hour': 0.77
    }
    
    def __init__(self):
        """初始化特征向量提取器"""
        self.energy_operator = EnergyOperator()  # RSS-V1.2规范：能量叠加算子
        logger.info("✅ 特征向量提取器初始化")
    
    def extract_elemental_fields(self, chart: List[Tuple[str, str]], 
                                 day_master: str,
                                 luck_pillar: Optional[Tuple[str, str]] = None,
                                 year_pillar: Optional[Tuple[str, str]] = None) -> Dict[str, float]:
        """
        提取五行场强分布（0.0-1.0标准化）
        
        Args:
            chart: 八字列表 [(年干,年支), (月干,月支), (日干,日支), (时干,时支)]
            day_master: 日主（如 "甲"）
            luck_pillar: 大运柱 (天干, 地支)
            year_pillar: 流年柱 (天干, 地支)
            
        Returns:
            五行场强分布字典 {"metal": 0.82, "wood": 0.14, ...}
        """
        element_counts = {
            'metal': 0.0,
            'wood': 0.0,
            'water': 0.0,
            'fire': 0.0,
            'earth': 0.0
        }
        
        pillar_names = ['year', 'month', 'day', 'hour']
        
        # 处理原局四柱
        for i, (gan, zhi) in enumerate(chart):
            pillar_name = pillar_names[i] if i < len(pillar_names) else 'unknown'
            weight = self.PILLAR_WEIGHTS.get(pillar_name, 1.0)
            
            # 天干元素
            gan_element = self.ELEMENT_MAP.get(gan, 'earth')
            element_counts[gan_element] += 1.0 * weight
            
            # 地支元素
            zhi_element = self.BRANCH_ELEMENT_MAP.get(zhi, 'earth')
            element_counts[zhi_element] += 1.0 * weight
        
        # RSS-V1.2规范：显性化实现能量叠加公式
        # E_total = [ (E_base ⊗ ω_luck) ⊕ ΔE_year ] × (1 ± δ_geo)
        
        # Step 1: 归一化原局能量场（E_base）
        total_base = sum(element_counts.values())
        if total_base > 0:
            base_energy = {k: v / total_base for k, v in element_counts.items()}
        else:
            base_energy = {k: 0.0 for k in element_counts.keys()}
        
        # Step 2: 提取大运和流年能量
        luck_energy = {}
        year_pulse = {}
        
        if luck_pillar:
            gan, zhi = luck_pillar
            gan_element = self.ELEMENT_MAP.get(gan, 'earth')
            zhi_element = self.BRANCH_ELEMENT_MAP.get(zhi, 'earth')
            # 大运能量（用于张量积）
            luck_energy[gan_element] = luck_energy.get(gan_element, 0.0) + 0.5
            luck_energy[zhi_element] = luck_energy.get(zhi_element, 0.0) + 0.5
        
        if year_pillar:
            gan, zhi = year_pillar
            gan_element = self.ELEMENT_MAP.get(gan, 'earth')
            zhi_element = self.BRANCH_ELEMENT_MAP.get(zhi, 'earth')
            # 流年脉冲能量（用于直和）
            year_pulse[gan_element] = year_pulse.get(gan_element, 0.0) + 0.3
            year_pulse[zhi_element] = year_pulse.get(zhi_element, 0.0) + 0.3
        
        # Step 3: 使用EnergyOperator显性化计算
        # 大运权重：最高优先级基准场修正（ω_luck = 1.0）
        luck_weight = 1.0
        
        # 计算总能量（包含地理修正）
        # 注意：地理修正将在vectorize_bazi中应用
        if luck_pillar or year_pillar:
            # 使用能量叠加算子
            total_energy = self.energy_operator.compute_total_energy(
                base_energy=base_energy,
                luck_weight=luck_weight,
                year_pulse=year_pulse if year_pillar else None,
                geo_damping=0.0  # 地理修正将在vectorize_bazi中单独应用
            )
        else:
            # 只有原局，无需叠加
            total_energy = base_energy
        
        return total_energy
    
    def extract_momentum_term(self, chart: List[Tuple[str, str]], 
                              day_master: str) -> Dict[str, float]:
        """
        提取动量项：十神之间的转化趋势（如：食神生财的指向性）
        
        Args:
            chart: 八字列表
            day_master: 日主
            
        Returns:
            动量项字典，包含十神转化趋势
        """
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
        except ImportError:
            logger.warning("⚠️ 无法导入BaziParticleNexus，使用简化逻辑")
            return {}
        
        # 提取所有天干
        stems = [p[0] for p in chart]
        
        # 统计十神分布
        shi_shen_counts = {
            '比肩': 0, '劫财': 0,
            '食神': 0, '伤官': 0,
            '正财': 0, '偏财': 0,
            '正官': 0, '七杀': 0,
            '正印': 0, '偏印': 0
        }
        
        for stem in stems:
            shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
            if shi_shen in shi_shen_counts:
                shi_shen_counts[shi_shen] += 1
        
        # 计算转化趋势（简化实现）
        # 食神生财：食神 -> 财星（食伤多，有转化趋势）
        shi_shen_count = shi_shen_counts['食神'] + shi_shen_counts['伤官']
        cai_count = shi_shen_counts['正财'] + shi_shen_counts['偏财']
        shi_to_cai = min(1.0, (shi_shen_count * 0.3 + cai_count * 0.2))
        
        # 财星生官：财星 -> 官星
        guan_count = shi_shen_counts['正官'] + shi_shen_counts['七杀']
        cai_to_guan = min(1.0, (cai_count * 0.3 + guan_count * 0.2))
        
        # 官星生印：官星 -> 印星
        yin_count = shi_shen_counts['正印'] + shi_shen_counts['偏印']
        guan_to_yin = min(1.0, (guan_count * 0.3 + yin_count * 0.2))
        
        # 归一化
        total_momentum = shi_to_cai + cai_to_guan + guan_to_yin
        if total_momentum > 0:
            normalized_momentum = {
                'shi_to_cai': shi_to_cai / total_momentum,
                'cai_to_guan': cai_to_guan / total_momentum,
                'guan_to_yin': guan_to_yin / total_momentum
            }
        else:
            normalized_momentum = {
                'shi_to_cai': 0.0,
                'cai_to_guan': 0.0,
                'guan_to_yin': 0.0
            }
        
        return normalized_momentum
    
    def extract_stress_tensor(self, chart: List[Tuple[str, str]], 
                              day_master: str,
                              synthesized_field: Optional[Dict] = None) -> float:
        """
        提取应力项：对冲相位产生的张力数值（0.0-1.0）
        
        Args:
            chart: 八字列表
            day_master: 日主
            synthesized_field: 合成场强信息（可选）
            
        Returns:
            应力值（0.0-1.0）
        """
        # 如果有合成场强信息，优先使用
        if synthesized_field:
            friction = synthesized_field.get('friction_index', 0.0)
            if isinstance(friction, (int, float)):
                # 归一化到0.0-1.0（假设friction_index在0-100范围）
                stress = min(1.0, max(0.0, friction / 100.0))
                return stress
        
        # 否则，基于格局冲突计算
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
        except ImportError:
            return 0.5  # 默认中等应力
        
        stems = [p[0] for p in chart]
        
        # 检测冲突格局
        has_shang_guan = False
        has_zheng_guan = False
        
        for stem in stems:
            shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
            if shi_shen == '伤官':
                has_shang_guan = True
            elif shi_shen == '正官':
                has_zheng_guan = True
        
        # 如果存在伤官见官冲突，应力较高
        if has_shang_guan and has_zheng_guan:
            stress = 0.8
        else:
            stress = 0.3  # 默认低应力
        
        return stress
    
    def extract_phase_coherence(self, chart: List[Tuple[str, str]], 
                                day_master: str) -> float:
        """
        提取相位干涉的一致性（0.0-1.0）
        值越高，相位关系越协调
        
        Args:
            chart: 八字列表
            day_master: 日主
            
        Returns:
            相位一致性（0.0-1.0）
        """
        # 简化实现：基于五行生克关系的一致性
        elements = []
        for gan, zhi in chart:
            elements.append(self.ELEMENT_MAP.get(gan, 'earth'))
            elements.append(self.BRANCH_ELEMENT_MAP.get(zhi, 'earth'))
        
        # 计算五行分布的均匀性（越均匀，一致性越高）
        element_counts = {}
        for elem in elements:
            element_counts[elem] = element_counts.get(elem, 0) + 1
        
        # 计算标准差（标准差越小，一致性越高）
        if len(element_counts) > 0:
            mean_count = sum(element_counts.values()) / len(element_counts)
            variance = sum((count - mean_count) ** 2 for count in element_counts.values()) / len(element_counts)
            std_dev = variance ** 0.5
            
            # 归一化到0.0-1.0（标准差越小，一致性越高）
            # 假设最大标准差为2.0
            coherence = max(0.0, 1.0 - (std_dev / 2.0))
        else:
            coherence = 0.5
        
        return coherence
    
    def apply_environment_damping(self, elemental_fields: Dict[str, float],
                                  geo_info: Optional[str] = None,
                                  micro_env: Optional[List[str]] = None) -> Dict[str, float]:
        """
        应用环境因子：地域、微环境对原始能级的阻尼系数（RSS-V1.2规范）
        
        RSS-V1.2规范：
        - δ_geo (修正因子)：地理修正算子
        - 基准值为[原局+大运+流年]的结果
        - 限制在±15%以内
        
        Args:
            elemental_fields: 原始五行场强分布（已包含原局+大运+流年）
            geo_info: 地理信息（如 "北方/北京"）
            micro_env: 微环境列表（如 ["近水"]）
            
        Returns:
            应用环境阻尼后的五行场强分布（限制在±15%以内）
        """
        # RSS-V1.2规范：使用EnergyOperator显性化实现地理修正
        # 计算地理阻尼系数（限制在±15%以内）
        geo_damping = self.energy_operator.calculate_geo_damping_from_info(geo_info or '中央')
        
        # 应用地理修正：E_total = E × (1 ± δ_geo)
        corrected_fields = self.energy_operator.geo_correction(
            total_energy=elemental_fields,
            geo_damping=geo_damping
        )
        
        logger.debug(f"📊 地理修正: geo_info={geo_info}, damping={geo_damping:.3f} (限制在±15%以内)")
        
        return corrected_fields
    
    def suggest_routing_hint(self, elemental_fields: Dict[str, float],
                            stress_tensor: float,
                            momentum_term: Dict[str, float]) -> Optional[str]:
        """
        基于物理特征提供初步路由暗示
        
        Args:
            elemental_fields: 五行场强分布
            stress_tensor: 应力值
            momentum_term: 动量项
            
        Returns:
            格局ID建议（如 "SHANG_GUAN_JIAN_GUAN"）
        """
        # 高应力 + 金属元素低 -> 可能伤官见官
        if stress_tensor > 0.7 and elemental_fields.get('metal', 0.0) < 0.2:
            return "SHANG_GUAN_JIAN_GUAN"
        
        # 火元素极高 -> 可能化火格或从儿格
        if elemental_fields.get('fire', 0.0) > 0.6:
            return "CONG_ER_GE"
        
        # 土元素极高 -> 可能建禄月劫
        if elemental_fields.get('earth', 0.0) > 0.5:
            return "JIAN_LU_YUE_JIE"
        
        return None
    
    def vectorize_bazi(self, 
                      chart: List[Tuple[str, str]],
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      geo_info: Optional[str] = None,
                      micro_env: Optional[List[str]] = None,
                      synthesized_field: Optional[Dict] = None) -> Dict[str, Any]:
        """
        [主入口点]
        将八字转化为特征向量矩阵
        
        Args:
            chart: 八字列表
            day_master: 日主
            luck_pillar: 大运柱
            year_pillar: 流年柱
            geo_info: 地理信息
            micro_env: 微环境列表
            synthesized_field: 合成场强信息
            
        Returns:
            特征向量字典，格式：
            {
                "elemental_fields": [0.82, 0.14, 0.43, ...],  # 金木水火土
                "stress_tensor": 0.75,
                "phase_coherence": 0.90,
                "routing_hint": "SHANG_GUAN_JIAN_GUAN",
                "momentum_term": {...}
            }
        """
        # 1. 提取五行场强
        elemental_fields = self.extract_elemental_fields(
            chart, day_master, luck_pillar, year_pillar
        )
        
        # 2. 应用环境阻尼
        elemental_fields = self.apply_environment_damping(
            elemental_fields, geo_info, micro_env
        )
        
        # 3. 提取动量项
        momentum_term = self.extract_momentum_term(chart, day_master)
        
        # 4. 提取应力项
        stress_tensor = self.extract_stress_tensor(
            chart, day_master, synthesized_field
        )
        
        # 5. 提取相位一致性
        phase_coherence = self.extract_phase_coherence(chart, day_master)
        
        # 6. 生成路由暗示
        routing_hint = self.suggest_routing_hint(
            elemental_fields, stress_tensor, momentum_term
        )
        
        # 7. 构建向量包（按固定顺序：金木水火土）
        elemental_vector = [
            elemental_fields.get('metal', 0.0),
            elemental_fields.get('wood', 0.0),
            elemental_fields.get('water', 0.0),
            elemental_fields.get('fire', 0.0),
            elemental_fields.get('earth', 0.0)
        ]
        
        result = {
            "elemental_fields": elemental_vector,
            "elemental_fields_dict": elemental_fields,  # 保留字典格式便于读取
            "stress_tensor": stress_tensor,
            "phase_coherence": phase_coherence,
            "routing_hint": routing_hint,
            "momentum_term": momentum_term
        }
        
        logger.info(f"✅ 特征向量提取完成: stress={stress_tensor:.3f}, coherence={phase_coherence:.3f}, hint={routing_hint}")
        
        return result

