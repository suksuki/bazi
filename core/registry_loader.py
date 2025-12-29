"""
QGA 注册表驱动器 (Registry Loader)
实现从JSON注册表读取配置并自动调用引擎进行计算

基于QGA-HR V2.0规范，支持：
- feature_anchors（质心锚点系统）
- pattern_recognition（Step 6格局识别）
- Schema V2.0兼容
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from core.math_engine import (
    sigmoid_variant,
    tensor_normalize,
    calculate_s_balance,
    calculate_flow_factor,
    phase_change_determination,
    calculate_cosine_similarity,
    calculate_centroid
)
from core.physics_engine import (
    compute_energy_flux,
    calculate_interaction_damping,
    calculate_clash_count,
    check_trigger,
    calculate_integrity_alpha,
    check_clash,
    check_combination
)
from core.math_engine import project_tensor_with_matrix

logger = logging.getLogger(__name__)


class RegistryLoader:
    """
    注册表驱动器
    
    职责：
    - 读取QGA-HR注册表配置
    - 自动调用数学和物理引擎进行计算
    - 支持任意格局的算法复原
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        初始化注册表驱动器
        
        Args:
            registry_path: 注册表文件路径（可选，默认使用holographic_pattern注册表）
        """
        if registry_path is None:
            project_root = Path(__file__).resolve().parents[1]
            registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
        
        self.registry_path = registry_path
        self.registry = None
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
            logger.info(f"✅ 已加载注册表: {self.registry_path}")
        except Exception as e:
            logger.error(f"加载注册表失败: {e}")
            self.registry = {"patterns": {}, "metadata": {}}
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """
        获取格局配置
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            
        Returns:
            格局配置字典，如果不存在则返回None
        """
        if not self.registry:
            return None
        
        patterns = self.registry.get('patterns', {})
        return patterns.get(pattern_id)
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict]:
        """
        获取格局配置（别名方法，与get_pattern相同）
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            
        Returns:
            格局配置字典，如果不存在则返回None
        """
        return self.get_pattern(pattern_id)
    
    def get_feature_anchors(self, pattern_id: str) -> Optional[Dict]:
        """
        获取格局的feature_anchors（V2.0新增）
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            
        Returns:
            feature_anchors字典，包含standard_centroid和singularity_centroids
            如果不存在或版本不是V2.0，返回None
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return None
        
        # 检查版本
        version = pattern.get('version', '1.0')
        if not version.startswith('2.'):
            logger.warning(f"格局 {pattern_id} 版本为 {version}，不支持feature_anchors（需要V2.0+）")
            return None
        
        return pattern.get('feature_anchors')
    
    def pattern_recognition(
        self,
        current_tensor: Dict[str, float],
        pattern_id: str
    ) -> Dict[str, Any]:
        """
        动态格局识别（Step 6）
        
        基于空间相似度的自动吸附机制，判断当前八字是否属于指定格局
        
        Args:
            current_tensor: 当前八字的5维投影值（原局基态，必须归一化）
                          格式：{'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
            pattern_id: 格局ID（如'A-03'）
            
        Returns:
            识别结果字典，包含：
            - matched: bool - 是否匹配
            - pattern_type: str - 'STANDARD' | 'SINGULARITY' | 'BROKEN' | 'MARGINAL'
            - similarity: float - 相似度值（0.0-1.0）
            - anchor_id: str - 匹配的锚点ID（'standard' 或 'A-03-X1'等）
            - resonance: bool - 是否达到共振态（similarity > perfect_threshold）
            - description: str - 描述信息
        """
        # 1. 获取格局配置和feature_anchors
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': 0.0,
                'anchor_id': None,
                'resonance': False,
                'description': f'格局 {pattern_id} 不存在'
            }
        
        feature_anchors = self.get_feature_anchors(pattern_id)
        if not feature_anchors:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': 0.0,
                'anchor_id': None,
                'resonance': False,
                'description': f'格局 {pattern_id} 缺少feature_anchors（需要V2.0+）'
            }
        
        # 2. 验证current_tensor已归一化
        total = sum(abs(v) for v in current_tensor.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"current_tensor未归一化（总和={total:.6f}），自动归一化")
            current_tensor = tensor_normalize(current_tensor)
        
        # 3. 计算与标准锚点的相似度
        standard_centroid = feature_anchors.get('standard_centroid')
        if not standard_centroid:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': 0.0,
                'anchor_id': None,
                'resonance': False,
                'description': f'格局 {pattern_id} 缺少standard_centroid'
            }
        
        standard_vector = standard_centroid.get('vector', {})
        match_threshold = standard_centroid.get('match_threshold', 0.80)
        perfect_threshold = standard_centroid.get('perfect_threshold', 0.92)
        
        standard_similarity = calculate_cosine_similarity(current_tensor, standard_vector)
        
        # 4. 检查奇点锚点
        singularity_centroids = feature_anchors.get('singularity_centroids', [])
        best_singularity = None
        best_singularity_sim = 0.0
        
        for singularity in singularity_centroids:
            singularity_vector = singularity.get('vector', {})
            singularity_threshold = singularity.get('match_threshold', 0.90)
            
            sim = calculate_cosine_similarity(current_tensor, singularity_vector)
            if sim > best_singularity_sim:
                best_singularity_sim = sim
                best_singularity = singularity
        
        # 5. 判定逻辑（根据AI设计师裁定）
        # 优先检查奇点（如果相似度 > 0.90 且明显高于标准格局）
        if best_singularity and best_singularity_sim > 0.90:
            # 如果奇点相似度明显高于标准格局相似度（至少高3%），判定为奇点
            if best_singularity_sim > standard_similarity + 0.03:
                return {
                    'matched': True,
                    'pattern_type': 'SINGULARITY',
                    'similarity': best_singularity_sim,
                    'anchor_id': best_singularity.get('sub_id', 'unknown'),
                    'resonance': best_singularity_sim > perfect_threshold,
                    'description': f"匹配奇点变体 {best_singularity.get('sub_id', 'unknown')}，相似度 {best_singularity_sim:.4f}",
                    'risk_level': best_singularity.get('risk_level', 'UNKNOWN'),
                    'special_instruction': best_singularity.get('special_instruction')
                }
        
        # 检查标准格局
        if standard_similarity > match_threshold:
            return {
                'matched': True,
                'pattern_type': 'STANDARD',
                'similarity': standard_similarity,
                'anchor_id': 'standard',
                'resonance': standard_similarity > perfect_threshold,
                'description': f"匹配标准格局，相似度 {standard_similarity:.4f}",
                'risk_level': None,
                'special_instruction': None
            }
        
        # 破格
        if standard_similarity < 0.60:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': standard_similarity,
                'anchor_id': None,
                'resonance': False,
                'description': f"破格，相似度 {standard_similarity:.4f} < 0.60",
                'risk_level': None,
                'special_instruction': None
            }
        
        # 边缘状态
        return {
            'matched': False,
            'pattern_type': 'MARGINAL',
            'similarity': standard_similarity,
            'anchor_id': None,
            'resonance': False,
            'description': f"边缘状态，相似度 {standard_similarity:.4f}（0.60-0.80之间）",
            'risk_level': None,
            'special_instruction': None
        }
    
    def calculate_tensor_projection_from_registry(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        从注册表读取配置并计算五维张量投影
        
        这是核心函数：实现100%算法复原
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            chart: 四柱八字
            day_master: 日主
            context: 上下文（大运、流年等，可选）
            
        Returns:
            计算结果字典，包含：
            - projection: 五维投影 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
            - sai: 系统对齐指数
            - energies: 基础能量 {'E_blade': float, 'E_kill': float, 'E_seal': float}
            - s_balance: 平衡度
            - phase_change: 相变状态
        """
        # 1. 获取格局配置
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        # 检查版本（版本分流）
        version = pattern.get('version', '1.0')
        is_v2 = version.startswith('2.')
        is_v21 = version == '2.1'  # V2.1支持transfer_matrix
        
        # V2.1: 使用transfer_matrix
        if is_v21:
            physics_kernel = pattern.get('physics_kernel', {})
            transfer_matrix = physics_kernel.get('transfer_matrix')
            
            if transfer_matrix:
                # 使用矩阵投影
                return self._calculate_with_transfer_matrix(
                    pattern_id, chart, day_master, transfer_matrix, context
                )
        
        # V2.0/V1.0: 使用旧的tensor_operator逻辑
        tensor_operator = pattern.get('tensor_operator', {})
        if not tensor_operator:
            return {'error': f'格局 {pattern_id} 缺少tensor_operator配置'}
        
        # 2. 获取权重（V2.0优先使用feature_anchors.standard_centroid.vector，否则使用tensor_operator.weights）
        weights = None
        if is_v2:
            feature_anchors = self.get_feature_anchors(pattern_id)
            if feature_anchors and feature_anchors.get('standard_centroid'):
                weights = feature_anchors['standard_centroid'].get('vector')
                logger.debug(f"使用V2.0 feature_anchors.standard_centroid.vector作为权重")
        
        if not weights:
            weights = tensor_operator.get('weights', {})
            if not weights:
                return {'error': f'格局 {pattern_id} 缺少权重配置'}
        
        # 3. 验证归一化
        total = sum(abs(v) for v in weights.values())
        if abs(total - 1.0) > 0.01:
            weights = tensor_normalize(weights)
            logger.warning(f"格局 {pattern_id} 权重未归一化（总和={total:.6f}），已自动归一化")
        
        # 4. 计算基础能量（从注册表的核心方程获取变量）
        core_equation = tensor_operator.get('core_equation', '')
        
        # 解析核心方程，提取需要的能量类型
        # 例如：S_balance = E_blade / E_kill
        energies = {}
        
        if 'E_blade' in core_equation or 'blade' in core_equation.lower():
            # 计算羊刃能量
            energies['E_blade'] = compute_energy_flux(chart, day_master, '羊刃')
        
        if 'E_kill' in core_equation or 'kill' in core_equation.lower():
            # 计算七杀能量
            energies['E_kill'] = compute_energy_flux(chart, day_master, '七杀')
        
        # 检查是否有flow_factor需要E_seal
        flow_factor = tensor_operator.get('flow_factor', {})
        if flow_factor and 'E_seal' in flow_factor.get('formula', ''):
            # 计算印星能量（正印+偏印）
            energies['E_seal'] = (
                compute_energy_flux(chart, day_master, '正印') +
                compute_energy_flux(chart, day_master, '偏印')
            )
        
        # 5. 计算核心方程（如S_balance）
        s_balance = None
        if 'E_blade' in energies and 'E_kill' in energies:
            s_balance = calculate_s_balance(energies['E_blade'], energies['E_kill'])
        
        # 6. 计算Flow Factor（如果适用）
        s_base = None
        if 'E_seal' in energies and flow_factor:
            # 这里需要先计算基础应力，简化处理
            clash_count = calculate_clash_count(chart)
            s_base = abs(energies.get('E_blade', 0) - energies.get('E_kill', 0)) + 0.5 * clash_count
            s_risk = calculate_flow_factor(s_base, energies['E_seal'])
        else:
            s_risk = None
        
        # 7. 计算SAI（系统对齐指数）
        # 简化：使用基础能量计算SAI
        # 实际应该调用框架的arbitrate_bazi，这里先简化
        sai = sum(energies.values()) * 10.0  # 临时计算，实际应从框架获取
        
        # 8. 计算五维投影
        projection = {
            'E': sai * weights.get('E', 0.0),
            'O': sai * weights.get('O', 0.0),
            'M': sai * weights.get('M', 0.0),
            'S': sai * weights.get('S', 0.0),
            'R': sai * weights.get('R', 0.0)
        }
        
        # 9. 相变判定（如果配置了激活函数）
        activation = tensor_operator.get('activation_function', {})
        phase_change = None
        if activation:
            threshold = activation.get('parameters', {}).get('collapse_threshold', 0.8)
            # 简化：使用S_balance作为能量指标
            if s_balance:
                normalized_energy = min(s_balance / 2.0, 1.0)  # 归一化到0-1
                phase_change = phase_change_determination(
                    normalized_energy,
                    threshold=threshold,
                    trigger=False  # 这里需要根据context判断是否有触发
                )
        
        # 10. V2.0: 如果存在feature_anchors，执行格局识别
        recognition_result = None
        if is_v2:
            # 归一化projection作为current_tensor（用于格局识别）
            normalized_projection = tensor_normalize(projection)
            recognition_result = self.pattern_recognition(normalized_projection, pattern_id)
        
        result = {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name', pattern_id),
            'version': version,
            'projection': projection,
            'sai': sai,
            'energies': energies,
            's_balance': s_balance,
            's_risk': s_risk,
            'phase_change': phase_change,
            'weights': weights
        }
        
        # 添加V2.0识别结果
        if recognition_result:
            result['recognition'] = recognition_result
        
        return result
    
    def simulate_dynamic_event(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        event_type: str = 'clash',
        event_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        模拟动态事件（如流年冲刃）
        
        Args:
            pattern_id: 格局ID
            chart: 四柱八字
            day_master: 日主
            event_type: 事件类型（如'clash'）
            event_params: 事件参数（如{'clash_branch': '子'}）
            
        Returns:
            仿真结果字典
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        kinetic_evolution = pattern.get('kinetic_evolution', {})
        dynamic_sim = kinetic_evolution.get('dynamic_simulation', {})
        
        if not dynamic_sim:
            return {'error': f'格局 {pattern_id} 缺少dynamic_simulation配置'}
        
        # 获取lambda系数
        lambda_coefficients = dynamic_sim.get('lambda_coefficients', {})
        fracture_threshold = dynamic_sim.get('fracture_threshold', 50.0)
        
        # 计算基础应力（简化：从projection获取）
        result = self.calculate_tensor_projection_from_registry(pattern_id, chart, day_master)
        s_base = result['projection'].get('S', 0.0)
        
        # 根据事件类型计算lambda
        if event_type == 'clash' and event_params:
            month_branch = chart[1][1]  # 月支
            clash_branch = event_params.get('clash_branch')
            
            if clash_branch:
                # 提取lambda系数值（从嵌套字典中提取）
                lambda_dict = {}
                if isinstance(lambda_coefficients, dict):
                    for key, value in lambda_coefficients.items():
                        if isinstance(value, dict):
                            lambda_dict[key] = value.get('value', 1.8)
                        else:
                            lambda_dict[key] = value
                
                lambda_val = calculate_interaction_damping(
                    chart,
                    month_branch,
                    clash_branch,
                    lambda_dict
                )
                
                # 计算新应力
                s_new = s_base * lambda_val
                is_collapse = s_new >= fracture_threshold
                
                return {
                    'pattern_id': pattern_id,
                    'event_type': event_type,
                    's_base': s_base,
                    'lambda': lambda_val,
                    's_new': s_new,
                    'fracture_threshold': fracture_threshold,
                    'is_collapse': is_collapse,
                    'status': 'COLLAPSE' if is_collapse else 'SURVIVAL'
                }
        
        return {'error': '不支持的事件类型或缺少必要参数'}
    
    def _check_pattern_state(
        self,
        pattern: Dict[str, Any],
        chart: List[str],
        day_master: str,
        day_branch: str,
        luck_pillar: str,
        year_pillar: str,
        alpha: float
    ) -> Dict[str, Any]:
        """
        检查成格/破格状态（FDS-V1.4）
        
        Args:
            pattern: 格局配置
            chart: 四柱八字
            day_master: 日主
            day_branch: 日支
            luck_pillar: 大运干支
            year_pillar: 流年干支
            alpha: 结构完整性alpha值
            
        Returns:
            格局状态字典，包含state、alpha、matrix等
        """
        dynamic_states = pattern.get('dynamic_states', {})
        collapse_rules = dynamic_states.get('collapse_rules', [])
        crystallization_rules = dynamic_states.get('crystallization_rules', [])
        integrity_threshold = pattern.get('physics_kernel', {}).get('integrity_threshold', 0.45)
        
        # 构建context
        energy_flux = {
            "wealth": compute_energy_flux(chart, day_master, "偏财") + 
                      compute_energy_flux(chart, day_master, "正财"),
            "resource": compute_energy_flux(chart, day_master, "正印") + 
                       compute_energy_flux(chart, day_master, "偏印")
        }
        
        context = {
            "chart": chart,
            "day_master": day_master,
            "day_branch": day_branch,
            "luck_pillar": luck_pillar,
            "year_pillar": year_pillar,
            "energy_flux": energy_flux
        }
        
        # 检查破格条件
        for rule in collapse_rules:
            trigger_name = rule.get('trigger')
            if trigger_name and check_trigger(trigger_name, context):
                return {
                    "state": "COLLAPSED",
                    "alpha": alpha,
                    "matrix": rule.get('fallback_matrix', 'Standard'),
                    "trigger": trigger_name,
                    "action": rule.get('action')
                }
        
        # 检查成格条件
        for rule in crystallization_rules:
            condition_name = rule.get('condition')
            if condition_name and check_trigger(condition_name, context):
                return {
                    "state": "CRYSTALLIZED",
                    "alpha": alpha,
                    "matrix": rule.get('target_matrix', pattern.get('id')),
                    "trigger": condition_name,
                    "action": rule.get('action'),
                    "validity": rule.get('validity', 'Permanent')
                }
        
        # 根据alpha判断
        if alpha < integrity_threshold:
            return {
                "state": "COLLAPSED",
                "alpha": alpha,
                "matrix": "Standard",
                "trigger": "Low_Integrity"
            }
        
        return {
            "state": "STABLE",
            "alpha": alpha,
            "matrix": pattern.get('id', 'Standard')
        }
    
    def _calculate_with_transfer_matrix(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        transfer_matrix: Dict[str, Dict[str, float]],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        使用transfer_matrix计算五维张量投影（V2.1专用）
        
        Args:
            pattern_id: 格局ID
            chart: 四柱八字
            day_master: 日主
            transfer_matrix: 5x5转换矩阵
            context: 上下文（大运、流年等，可选）
            
        Returns:
            计算结果字典，包含projection、sai等
        """
        # 1. 计算十神频率向量
        parallel = compute_energy_flux(chart, day_master, "比肩") + \
                   compute_energy_flux(chart, day_master, "劫财")
        resource = compute_energy_flux(chart, day_master, "正印") + \
                   compute_energy_flux(chart, day_master, "偏印")
        power = compute_energy_flux(chart, day_master, "七杀") + \
                compute_energy_flux(chart, day_master, "正官")
        wealth = compute_energy_flux(chart, day_master, "正财") + \
                 compute_energy_flux(chart, day_master, "偏财")
        output = compute_energy_flux(chart, day_master, "食神") + \
                 compute_energy_flux(chart, day_master, "伤官")
        
        frequency_vector = {
            "parallel": parallel,
            "resource": resource,
            "power": power,
            "wealth": wealth,
            "output": output
        }
        
        # 2. 如果context中有流年信息，调整frequency_vector
        if context:
            year_pillar = context.get('annual_pillar')
            if year_pillar and len(year_pillar) >= 1:
                from core.trinity.core.nexus.definitions import BaziParticleNexus
                year_stem = year_pillar[0]
                year_ten_god = BaziParticleNexus.get_shi_shen(year_stem, day_master)
                
                if year_ten_god in ['七杀', '正官']:
                    frequency_vector['power'] += 0.5
                elif year_ten_god in ['正印', '偏印']:
                    frequency_vector['resource'] += 0.3
                elif year_ten_god in ['比肩', '劫财']:
                    frequency_vector['parallel'] += 0.3
        
        # 3. 使用transfer_matrix进行矩阵投影
        projection = project_tensor_with_matrix(frequency_vector, transfer_matrix)
        
        # 4. 归一化投影（用于格局识别）
        normalized_projection = tensor_normalize(projection)
        
        # 5. 计算SAI（系统对齐指数）
        # SAI = 投影向量的模长（L2范数）
        import math
        sai = math.sqrt(sum(v ** 2 for v in projection.values()))
        
        logger.debug(f"初始SAI计算: projection={projection}, sai={sai:.4f}")
        
        # 如果SAI太小或为0，使用频率向量的模长作为基准
        if sai < 0.1:
            base_sai = math.sqrt(sum(v ** 2 for v in frequency_vector.values()))
            logger.debug(f"频率向量: {frequency_vector}, 模长={base_sai:.4f}")
            if base_sai > 0:
                # 使用频率向量模长作为SAI基准，然后根据投影值调整
                sai = base_sai * 0.5  # 调整系数，确保SAI不为0
                logger.info(f"SAI过小({sai:.4f})，使用频率向量模长调整: {sai:.4f}")
            else:
                # 如果频率向量也是0，使用默认值
                logger.warning(f"频率向量和投影值都为0，使用默认SAI=1.0")
                sai = 1.0
        
        # 确保SAI不为0
        if sai == 0.0:
            logger.error(f"SAI仍为0，强制设置为1.0")
            sai = 1.0
        
        # 6. 获取格局信息
        pattern = self.get_pattern(pattern_id)
        pattern_name = pattern.get('name', pattern_id) if pattern else pattern_id
        
        # 7. 计算结构完整性alpha（如果需要）
        day_branch = chart[2][1] if len(chart) > 2 and len(chart[2]) >= 2 else ""
        luck_pillar = context.get('luck_pillar', '') if context else ''
        year_pillar = context.get('annual_pillar', '') if context else ''
        
        energy_flux = {
            "wealth": frequency_vector['wealth'],
            "resource": frequency_vector['resource']
        }
        
        flux_events = []
        if year_pillar and len(year_pillar) >= 2:
            year_branch = year_pillar[1]
            if check_clash(day_branch, year_branch):
                flux_events.append("Day_Branch_Clash")
            if check_combination(day_branch, year_branch):
                flux_events.append("Blade_Combined_Transformation")
        
        alpha = calculate_integrity_alpha(
            natal_chart=chart,
            day_master=day_master,
            day_branch=day_branch,
            flux_events=flux_events,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            energy_flux=energy_flux
        )
        
        # 8. 格局识别
        recognition_result = self.pattern_recognition(normalized_projection, pattern_id)
        
        # 9. 检查成格/破格状态
        pattern_state = None
        if pattern:
            pattern_state = self._check_pattern_state(
                pattern, chart, day_master, day_branch,
                luck_pillar, year_pillar, alpha
            )
        
        result = {
            'pattern_id': pattern_id,
            'pattern_name': pattern_name,
            'version': '2.1',
            'projection': normalized_projection,  # 使用归一化后的投影（用于格局识别）
            'raw_projection': projection,  # 保留原始投影（用于SAI计算）
            'sai': sai,
            'frequency_vector': frequency_vector,
            'alpha': alpha,
            'recognition': recognition_result,
            'pattern_state': pattern_state
        }
        
        logger.info(f"_calculate_with_transfer_matrix完成: sai={sai:.4f}, projection={normalized_projection}, raw_projection={projection}")
        
        return result

