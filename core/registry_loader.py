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
    calculate_centroid,
    calculate_mahalanobis_distance,
    calculate_precision_score
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
from core.trinity.core.middleware.influence_bus import InfluenceBus
from core.trinity.core.middleware.temporal_factors import TemporalInjectionFactor
from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine

logger = logging.getLogger(__name__)

def count_vaults_helper(chart: List[str]) -> int:
    """Calculates the number of earth branches (vaults) in a chart."""
    vaults = {'辰', '戌', '丑', '未'}
    count = 0
    for pillar in chart:
        if len(pillar) >= 2 and pillar[1] in vaults:
            count += 1
    return count


class RegistryLoader:
    """
    注册表驱动器
    
    职责：
    - 读取QGA-HR注册表配置
    - 自动调用数学和物理引擎进行计算
    - 支持任意格局的算法复原
    """
    
    def __init__(self, registry_path: Optional[Path] = None, theme_id: Optional[str] = None):
        """
        初始化注册表驱动器
        
        Args:
            registry_path: 注册表文件路径（可选，默认使用holographic_pattern注册表）
            theme_id: 主题ID（可选，用于自动选择注册表路径）
                - "HOLOGRAPHIC_PATTERN": 使用 holographic_pattern/registry.json
                - "BAZI_FUNDAMENTAL": 使用 bazi_fundamental/registry.json
                - "PATTERN_PHYSICS": 使用 physical_simulation/registry.json
        """
        if registry_path is None:
            project_root = Path(__file__).resolve().parents[1]
            if theme_id == "BAZI_FUNDAMENTAL":
                registry_path = project_root / "core" / "subjects" / "bazi_fundamental" / "registry.json"
            elif theme_id == "FRAMEWORK_UTILITIES":
                registry_path = project_root / "core" / "subjects" / "framework_utilities" / "registry.json"
            elif theme_id == "PATTERN_PHYSICS":
                registry_path = project_root / "core" / "subjects" / "physical_simulation" / "registry.json"
            else:
                # 默认使用 holographic_pattern
                registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
        
        self.registry_path = registry_path
        self.registry = None
        self.theme_id = theme_id
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
        获取格局配置，支持嵌套查找 (V2.5+)
        """
        if not self.registry:
            return None
        
        patterns = self.registry.get('patterns', {})
        
        # 1. 直接查找
        if pattern_id in patterns:
            return patterns[pattern_id]
        
        # 2. 嵌套查找
        for pid, data in patterns.items():
            sub_patterns_list = data.get('sub_patterns_registry') or data.get('sub_patterns') or []
            if sub_patterns_list:
                for sub in sub_patterns_list:
                    if sub.get('id') == pattern_id:
                        # 自动合并父格局属性
                        combined = sub.copy()
                        
                        # 核心继承：版本与物理规格
                        if 'version' not in combined:
                            combined['version'] = data.get('version', '2.5')
                        if 'meta_info' not in combined:
                            combined['meta_info'] = data.get('meta_info', {})
                        if 'physics_kernel' not in combined and 'physics_kernel' in data:
                            combined['physics_kernel'] = data['physics_kernel']
                        
                        # [V2.5.3] 动态状态映射继承
                        if 'dynamic_states' not in combined and 'dynamic_states' in data:
                            combined['dynamic_states'] = data['dynamic_states']
                        
                        # 元数据继承
                        combined['parent_pattern'] = pid
                        if 'category' not in combined:
                            combined['category'] = data.get('category')
                        if 'subject_id' not in combined:
                            combined['subject_id'] = sub.get('id')
                        
                        return combined
        
        return None
    
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
        version = pattern.get('version')
        if not version:
            version = pattern.get('meta_info', {}).get('version', '1.0')
            
        if not version.startswith('2.'):
            logger.warning(f"格局 {pattern_id} 版本为 {version}，不支持feature_anchors（需要V2.0+）")
            return None
        
        # 兼容性适配：检查是否有sub_patterns/sub_patterns_registry (Schema V2.5)
        sub_patterns = pattern.get('sub_patterns_registry') or pattern.get('sub_patterns')
        if sub_patterns:
            anchors = {'singularity_centroids': []}
            for sp in sub_patterns:
                # 扁平化 manifold_stats
                stats = sp.get('manifold_stats', {})
                # 复制sp内容到anchor
                anchor = sp.copy()
                anchor.update(stats) # mean_vector, covariance_matrix 等上浮
                anchor.pop('manifold_stats', None)
                
                # 映射 vector (兼容旧版代码)
                if 'mean_vector' in anchor:
                    anchor['vector'] = anchor['mean_vector']
                
                # 分类映射
                sp_id = sp.get('id', '')
                if 'STANDARD' in sp_id or sp.get('population_priority') == 'Tier A':
                    anchors['standard_manifold'] = anchor
                else:
                    # 任何非标准的都视为奇点/激活态
                    anchors['singularity_centroids'].append(anchor)
                    # 另外，特例映射: SP_A03_VAULT -> activated_manifold
                    if 'VAULT' in sp_id or 'ACTIVATED' in sp_id:
                        anchors['activated_manifold'] = anchor
                        # 确保 sub_id 存在 (用于 pattern_recognition)
                        anchor['sub_id'] = sp_id
            
            return anchors

        # [V2.5 Leaf Node Fix] 如果本身就是子格局，可能直接持有 manifold_stats
        manifold_stats = pattern.get('manifold_stats')
        if manifold_stats:
            anchor = pattern.copy()
            anchor.update(manifold_stats)
            anchor.pop('manifold_stats', None)
            if 'mean_vector' in anchor:
                anchor['vector'] = anchor['mean_vector']
            
            # 判断它是哪种流形
            sp_id = pattern.get('id', '')
            if 'VAULT' in sp_id or 'ACTIVATED' in sp_id:
                return {
                    'activated_manifold': anchor,
                    'standard_manifold': anchor, # 兜底，防止 recognition 找不到基准
                    'singularity_centroids': [anchor]
                }
            else:
                return {
                    'standard_manifold': anchor,
                    'singularity_centroids': []
                }

        return pattern.get('feature_anchors')
    
    def pattern_recognition(
        self,
        current_tensor: Dict[str, float],
        pattern_id: str,
        dynamic_state: Optional[str] = None,
        sai: float = 1.0
    ) -> Dict[str, Any]:
        """
        动态格局识别（Step 6）
        
        基于空间相似度的自动吸附机制，判断当前八字是否属于指定格局
        支持多态观测：根据 dynamic_state 自动切换锚点基准 (V2.3)
        [V1.5 Upgrade] 引入马氏距离 (Mahalanobis) 与概率密度 (PDF) 评分
        
        Args:
            current_tensor: 当前八字的5维投影值（原局基态，必须归一化）
            pattern_id: 格局ID（如'A-03'）
            dynamic_state: 当前动力学状态 (如 'STABLE', 'ACTIVATED')
            sai: 系统对齐指数（能量强度）
            
        Returns:
            识别结果字典
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
        
        # 3. 计算与目标锚点的相似度 (流形路由 V2.4)
        target_manifold_id = 'standard_manifold'
        manifold = feature_anchors.get('standard_manifold')
        
        # [V2.4 Manifold Protocol] 
        # 根据 dynamic_state 切换观测流形
        if dynamic_state in ['ACTIVATED', 'TRANSFORMED', 'VOLATILE']:
            activated_manifold = feature_anchors.get('activated_manifold')
            if activated_manifold:
                manifold = activated_manifold
                target_manifold_id = 'activated_manifold'
                logger.info(f"Observer: Switching to 'activated_manifold' for {pattern_id} due to Phase Transition.")

        if not manifold:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': 0.0,
                'anchor_id': None,
                'resonance': False,
                'description': f'格局 {pattern_id} 缺少观测流形 ({target_manifold_id})'
            }
        
        mean_vector = manifold.get('mean_vector', manifold.get('vector', {})) # 兼容旧版
        thresholds = manifold.get('thresholds', {})
        match_threshold = thresholds.get('match_threshold', manifold.get('match_threshold', 0.80))
        
        # [V1.5 Fix] 强制对齐特征锚点的尺度 (Scale Alignment)
        # 如果特征锚点的总像素不为1.0，则进行归一化，确保马氏距离计算在同一物理空间
        ref_total = sum(abs(v) for v in mean_vector.values())
        if abs(ref_total - 1.0) > 0.05:
            logger.info(f"Observer: Normalizing mean_vector scale ({ref_total:.4f} -> 1.0)")
            mean_vector = tensor_normalize(mean_vector)

        # 1. 计算余弦相似度 (Direction)
        standard_similarity = calculate_cosine_similarity(current_tensor, mean_vector)
        
        # 2. [V1.5] 计算马氏距离 (Statistical Distribution)
        m_dist = 0.0
        precision_score = standard_similarity 
        
        import numpy as np
        inv_cov = manifold.get('inverse_covariance')
        cov = manifold.get('covariance_matrix')
        
        inv_cov_np = np.array(inv_cov) if inv_cov else None
        cov_np = np.array(cov) if cov else None

        if inv_cov_np is not None or cov_np is not None:
            m_dist = calculate_mahalanobis_distance(
                current_tensor, 
                mean_vector, 
                covariance_matrix=cov_np, 
                inverse_covariance=inv_cov_np
            )
            
            # 3. [V1.5] 计算精密评分 (Precision Score)
            precision_score = calculate_precision_score(standard_similarity, m_dist, sai)
            logger.info(f"V1.5 Precision Check: Similarity={standard_similarity:.4f}, M-Dist={m_dist:.4f}, Final Score={precision_score:.4f}")

        # 4. 能量门控 (SAI Gating)
        min_sai = thresholds.get('min_sai_gating', 0.5)
        max_m_dist = thresholds.get('max_mahalanobis_dist', 3.0)
        
        is_matched = precision_score > match_threshold
        
        # V2.4 精密判定：必须满足马氏距离与能量门控约束
        if m_dist > max_m_dist:
            logger.warning(f"Precision Gating: M-Dist {m_dist:.4f} exceeds threshold {max_m_dist}")
            is_matched = False
            
        if sai < min_sai:
            logger.warning(f"SAI Gating: SAI {sai:.4f} below threshold {min_sai}")
            is_matched = False
            
        # 4. 判定决策 (Decision Logic V2.4)
        perfect_threshold = thresholds.get('perfect_threshold', 0.92)
        
        # Check for singularities first
        singularity_centroids = feature_anchors.get('singularity_centroids', [])
        best_singularity = None
        best_singularity_sim = 0.0
        
        for singularity in singularity_centroids:
            sing_vec = singularity.get('vector', {})
            sim = calculate_cosine_similarity(current_tensor, sing_vec)
            if sim > best_singularity_sim:
                best_singularity_sim = sim
                best_singularity = singularity
        
        if best_singularity and best_singularity_sim > 0.90:
            if best_singularity_sim > standard_similarity + 0.03:
                return {
                    'matched': True,
                    'pattern_type': 'SINGULARITY',
                    'similarity': best_singularity_sim,
                    'anchor_id': best_singularity.get('sub_id', 'unknown'),
                    'resonance': best_singularity_sim > perfect_threshold,
                    'description': f"高度匹配奇点变体 {best_singularity.get('sub_id', 'unknown')}",
                    'risk_level': best_singularity.get('risk_level', 'UNKNOWN'),
                    'special_instruction': best_singularity.get('special_instruction')
                }
        
        # Final Match Decision
        if is_matched:
            p_tag = 'STANDARD' if target_manifold_id == 'standard_manifold' else 'ACTIVATED'
            return {
                'matched': True,
                'pattern_type': p_tag,
                'similarity': standard_similarity,
                'mahalanobis_dist': m_dist,
                'precision_score': precision_score,
                'anchor_id': target_manifold_id,
                'resonance': precision_score > perfect_threshold,
                'description': f"精密观测匹配 ({p_tag})，评分 {precision_score:.4f}",
                'risk_level': None,
                'special_instruction': None
            }
        
        # 破格 (Broken) vs 边缘 (Marginal)
        if precision_score < 0.60:
            return {
                'matched': False,
                'pattern_type': 'BROKEN',
                'similarity': standard_similarity,
                'mahalanobis_dist': m_dist,
                'precision_score': precision_score,
                'anchor_id': None,
                'resonance': False,
                'description': f"物理破格，评分 {precision_score:.4f} < 0.60",
                'risk_level': None,
                'special_instruction': None
            }
        
        return {
            'matched': False,
            'pattern_type': 'MARGINAL',
            'similarity': standard_similarity,
            'mahalanobis_dist': m_dist,
            'precision_score': precision_score,
            'anchor_id': None,
            'resonance': False,
            'description': f"边缘状态，评分 {precision_score:.4f}",
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
        
        # 检查版本 (优先检查root，其次检查meta_info)
        version = pattern.get('version')
        if not version:
            version = pattern.get('meta_info', {}).get('version', '1.0')
            
        is_v2 = str(version).startswith('2.')
        has_matrix = pattern.get('physics_kernel', {}).get('transfer_matrix') is not None
        
        # V2.1+/V1.5+: 使用transfer_matrix (Protocol V2.1, V2.2, V2.3, V2.5+)
        if is_v2 or str(version) >= '1.5' or has_matrix:
            # [V2.5] Pattern Routing Protocol
            active_pattern = pattern
            sub_id = None
            
            router = pattern.get('matching_router', {})
            if router and router.get('strategies'):
                # Execute routing logic
                for strategy in router['strategies']:
                    target_id = strategy.get('target')
                    logic = strategy.get('logic', '')
                    
                    if strategy.get('priority') == 3 and logic == 'default':
                        # Standard Fallback
                        break
                    
                    # Compute preliminary projection (V1.5 Heuristic)
                    bj = compute_energy_flux(chart, day_master, "比肩")
                    jc = compute_energy_flux(chart, day_master, "劫财")
                    zy = compute_energy_flux(chart, day_master, "正印")
                    py = compute_energy_flux(chart, day_master, "偏印")
                    zc = compute_energy_flux(chart, day_master, "正财")
                    pc = compute_energy_flux(chart, day_master, "偏财")
                    
                    # E = bj + jc + 0.8*resource
                    # M = zc + pc
                    # E = bj + jc + 0.8*resource
                    # M = zc + pc
                    e_est = bj + jc + 0.5 * (zy + py)
                    m_est = zc + pc
                    
                    # O = dg + qg (Direct Officer + Seven Killings)
                    dg = compute_energy_flux(chart, day_master, "正官")
                    qg = compute_energy_flux(chart, day_master, "七杀")
                    o_est = dg + qg

                    # S & R Estimation (V2.4)
                    clash_cnt = calculate_clash_count(chart)
                    s_est = qg + 0.8 * clash_cnt - 0.5 * (zy + py) # Approx from D-02 Kernel

                    # R Estimation
                    # Simple combination count helper
                    comb_cnt = 0
                    branches = [p[1] for p in chart]
                    for i in range(len(branches)):
                        for j in range(i+1, len(branches)):
                            from core.physics_engine import check_combination # Ensure import availability
                            if check_combination(branches[i], branches[j]):
                                comb_cnt += 1
                                
                    r_est = comb_cnt * 1.0 + bj * 0.5 + jc * 0.3 # Approx from D-02 Kernel_Row_R
                    
                    v_count = count_vaults_helper(chart)
                    
                    match = False
                    
                    # Protocol V2.5: Support JSON Logic (D-02 Standard)
                    if isinstance(logic, list):
                        conditions_met = True
                        for cond in logic:
                            axis = cond.get("axis")
                            op = cond.get("operator")
                            val = cond.get("value", 0.0)
                            
                            current_val = 0.0
                            if axis == "E": current_val = e_est
                            elif axis == "M": current_val = m_est
                            elif axis == "O": current_val = o_est
                            elif axis == "S": current_val = s_est
                            elif axis == "R": current_val = r_est
                            
                            if op == "gt" and not (current_val > val): conditions_met = False
                            elif op == "gte" and not (current_val >= val): conditions_met = False
                            elif op == "lt" and not (current_val < val): conditions_met = False
                            elif op == "lte" and not (current_val <= val): conditions_met = False
                            
                            if not conditions_met: break
                        
                        if conditions_met: match = True

                    # Legacy String Logic
                    elif isinstance(logic, str):
                        # D-01 Logic
                        if "E < 0.15" in logic and e_est < 0.20 and m_est > 0.8: match = True
                        if "vault_count >= 3" in logic and v_count >= 3: match = True
                        
                        # A-03 Logic (FDS-V1.5.1)
                        if "vault_count >= 2" in logic and v_count >= 2: match = True
                        
                        if "E < 0.35" in logic and "O > 0.55" in logic:
                             # SP_A03_OVERKILL
                             if e_est < 0.40 and o_est > 0.50: match = True # Relaxed slightly for heuristics
                        
                        if "E > 0.65" in logic and "O < 0.25" in logic:
                             # SP_A03_NO_CONTROL
                             if e_est > 0.60 and o_est < 0.30: match = True
                    
                    if match:
                        sub_patterns = pattern.get('sub_patterns_registry') or pattern.get('sub_patterns') or []
                        for sp in sub_patterns:
                            if sp.get('id') == target_id:
                                active_pattern = sp
                                sub_id = target_id
                                # Apply matrix_override immediately for accurate final calculation
                                override = sp.get('matrix_override', {})
                                if override.get('transfer_matrix'):
                                    transfer_matrix = override['transfer_matrix']
                                logger.info(f"Router redirection triggered: {pattern_id} -> {sub_id}")
                                break
                        if sub_id: break

            physics_kernel = pattern.get('physics_kernel', {})
            # [V2.5] Support nested matrix_override
            transfer_matrix = active_pattern.get('matrix_override', {}).get('transfer_matrix') or \
                              physics_kernel.get('transfer_matrix')
            
            if transfer_matrix:
                res = self._calculate_with_transfer_matrix(
                    pattern_id, chart, day_master, transfer_matrix, context
                )
                if sub_id: res['sub_id'] = sub_id
                return res
        
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
        dynamic_state = "STABLE"
        
        # [V2.5 Phase Transition Logic]
        # 首先构建完整的Context用于状态检查
        day_branch = chart[2][1] if len(chart) > 2 and len(chart[2]) > 1 else ""
        luck_pillar = context.get('luck_pillar', "") if context else ""
        year_pillar = context.get('year_pillar', "") if context else ""
        
        # 调用 _check_pattern_state 获取动力学状态
        # Mock alpha=1.0 for initial check
        dynamic_result = self._check_pattern_state(
            pattern, chart, day_master, day_branch, luck_pillar, year_pillar, 1.0
        )
        
        if dynamic_result:
            dynamic_state = dynamic_result.get('state', 'STABLE')
            phase_change = dynamic_result # 保存完整结果
            logger.info(f"Dynamic State Determined: {dynamic_state} (Trigger: {dynamic_result.get('trigger')})")
        
        if activation and not phase_change:
            threshold = activation.get('parameters', {}).get('collapse_threshold', 0.8)
            # 简化：使用S_balance作为能量指标
            if s_balance:
                normalized_energy = min(s_balance / 2.0, 1.0)  # 归一化到0-1
                phase_change_val = phase_change_determination(
                    normalized_energy,
                    threshold=threshold,
                    trigger=False  # 这里需要根据context判断是否有触发
                )
                if phase_change_val:
                     phase_change = {'state': phase_change_val}

        # 10. V2.0: 如果存在feature_anchors，执行格局识别
        recognition_result = None
        if is_v2:
            # 归一化projection作为current_tensor（用于格局识别）
            normalized_projection = tensor_normalize(projection)
            # [Fix] Pass dynamic_state to enable Manifold Switching
            recognition_result = self.pattern_recognition(
                normalized_projection, 
                pattern_id, 
                dynamic_state=dynamic_state,
                sai=sai
            )
        
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
                # [V2.3] Check for exceptions
                exceptions = rule.get('exceptions', [])
                for exc in exceptions:
                    if self._check_exception(exc, context):
                        override = exc.get('override_state', {})
                        return {
                            "state": override.get('state', "ACTIVATED"),
                            "alpha": alpha,
                            "matrix": pattern.get('id'),
                            "trigger": trigger_name,
                            "exception": exc.get('name'),
                            "tensor_modifier": override.get('tensor_modifier'),
                            "centroid_ref": override.get('centroid_ref')
                        }
                
                return {
                    "state": rule.get('default_action', "COLLAPSED"),
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

    def _check_exception(self, exception_def: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        [V2.3] 检查异常豁免条件
        """
        conditions = exception_def.get('conditions', [])
        logic = exception_def.get('logic', 'AND')
        
        results = []
        for cond in conditions:
            operator = cond.get('operator')
            if operator == "call_physics":
                # 调用物理引擎算子
                func_name = cond.get('function')
                args_keys = cond.get('args', [])
                
                # 解析参数
                args = []
                for key in args_keys:
                    if key == "$day_branch":
                        args.append(context.get('day_branch'))
                    elif key == "$year_branch":
                        year_pillar = context.get('year_pillar')
                        args.append(year_pillar[1] if year_pillar and len(year_pillar) >= 2 else "")
                    else:
                        args.append(context.get(key.lstrip('$')))
                
                # 执行调用
                import core.physics_engine as physics
                if hasattr(physics, func_name):
                    func = getattr(physics, func_name)
                    res = func(*args)
                    
                    # 检查期望值
                    expect = cond.get('expect', {})
                    match = True
                    for k, v in expect.items():
                        if isinstance(v, dict):
                            if "gt" in v and not (res.get(k, 0) > v["gt"]): match = False
                            if "lt" in v and not (res.get(k, 0) < v["lt"]): match = False
                        elif res.get(k) != v:
                            match = False
                    results.append(match)
                else:
                    results.append(False)
        
        if not results:
            return False
            
        if logic == 'AND':
            return all(results)
        return any(results)
    
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
        bj = compute_energy_flux(chart, day_master, "比肩")
        jc = compute_energy_flux(chart, day_master, "劫财")
        ss = compute_energy_flux(chart, day_master, "食神")
        sg = compute_energy_flux(chart, day_master, "伤官")
        pc = compute_energy_flux(chart, day_master, "偏财")
        zc = compute_energy_flux(chart, day_master, "正财")
        qs = compute_energy_flux(chart, day_master, "七杀")
        zg = compute_energy_flux(chart, day_master, "正官")
        py = compute_energy_flux(chart, day_master, "偏印")
        zy = compute_energy_flux(chart, day_master, "正印")

        frequency_vector = {
            "bi_jian": bj,
            "jie_cai": jc,
            "shi_shen": ss,
            "shang_guan": sg,
            "pian_cai": pc,
            "zheng_cai": zc,
            "qi_sha": qs,
            "zheng_guan": zg,
            "pian_yin": py,
            "zheng_yin": zy,
            # [LEGACY COMPAT] 保持聚合字段
            "parallel": bj + jc,
            "resource": zy + py,
            "power": zg + qs,
            "wealth": zc + pc,
            "output": ss + sg
        }
        
        # 2. [V1.4] Use InfluenceBus for Environmental Arbitration (No Hardcoding)
        bus = InfluenceBus()
        bus.register(TemporalInjectionFactor())
        
        # Prepare context for the bus
        context = context or {}
        context['day_master'] = day_master
        
        # Convert frequency_vector to waves_dict for bus protocol
        waves_dict = {k: type('Wave', (), {'amplitude': v}) for k, v in frequency_vector.items()}
        
        # Arbitrate!
        from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
        framework = QuantumUniversalFramework()
        
        binfo = {'day_master': day_master}
        arbitration_res = framework.arbitrate_bazi(chart, binfo, context)
        
        # Get true physical SAI
        physics = arbitration_res.get('physics', {})
        stress = physics.get('stress', {})
        sai_framework = stress.get('SAI', 0.0)
        
        verdict = bus.arbitrate_environment(waves_dict, context)
        
        # [V1.4 Fusion] Calculate Interaction Energies (Clash/Comb)
        clash_energy = calculate_clash_count(chart) * 0.5 # Basic mapping
        # MOD_15: Use Vibration Engine to check impedance
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        vib_engine = StructuralVibrationEngine(day_master)
        v_metrics = vib_engine.calculate_vibration_metrics(stems, branches, context)
        
        # Adjust clash energy based on system entropy/impedance
        # Higher impedance = More "brittle" clash impact
        impedance = v_metrics.get('impedance_magnitude', 1.0)
        clash_energy *= (1.0 + (impedance - 1.0) * 0.2)
        
        # Update frequency_vector with arbitrated values + interactions
        frequency_vector = {
            "bi_jian": bj, "jie_cai": jc, "shi_shen": ss, "shang_guan": sg,
            "pian_cai": pc, "zheng_cai": zc, "qi_sha": qs, "zheng_guan": zg,
            "pian_yin": py, "zheng_yin": zy,
            # [FDS-V1.5 Spec Support]
            "Day_Master": bj,
            "Rob_Wealth": jc,
            "Food": ss,
            "Injuries": sg,
            "Indirect_Wealth": pc,
            "Direct_Wealth": zc,
            "Seven_Killings": qs,
            "Direct_Officer": zg,
            "Resource": zy + py, # Spec often aggregates
            "Parallel": bj + jc,
            "vault_count": count_vaults_helper(chart),
            "clash": round(clash_energy, 4),
            "combination": 0.0,
            # [LEGACY COMPAT] Restored
            "parallel": bj + jc,
            "resource": zy + py,
            "power": zg + qs,
            "wealth": zc + pc,
            "output": ss + sg
        }
        
        injection_logs = verdict.get('logs', {})
        
        # 3. 使用transfer_matrix进行矩阵投影
        # [V2.2 Policy] First, check for tensor_dynamics configuration
        pattern = self.get_pattern(pattern_id)
        physics_kernel = pattern.get('physics_kernel', {}) if pattern else {}
        dynamics_config = physics_kernel.get('tensor_dynamics')
        
        # Apply Input Transform (if any)
        processed_input = frequency_vector
        if dynamics_config and dynamics_config.get('activation_function') == "tanh_saturation":
            # [V2.2] Tanh Saturation applies BEFORE matrix projection as a gain control
            params = dynamics_config.get('parameters', {})
            k_val = params.get('k_factor', 3.0)
            
            from core.math_engine import apply_saturation_layer
            processed_input = {
                k: apply_saturation_layer(v, k_val) 
                for k, v in frequency_vector.items()
            }
            logger.debug(f"Applied tanh_saturation (k={k_val}) to input vector")

        # Core Projection
        projection = project_tensor_with_matrix(processed_input, transfer_matrix)
        
        # 4. 归一化投影（用于格局识别）
        normalized_projection = tensor_normalize(projection)
        
        # 5. 计算SAI（系统对齐指数）
        # SAI 优先使用框架计算的真实对齐力
        if sai_framework > 0:
            sai = sai_framework
            logger.debug(f"使用框架SAI: {sai:.4f}")
        else:
            # SAI = 投影向量的模长（L2范数）作为物理强度补偿
            import math
            sai_l2 = math.sqrt(sum(v ** 2 for v in projection.values()))
            sai = max(sai_l2, 1.0) # 兜底保护
            logger.debug(f"框架SAI缺失，使用L2模长补偿: {sai:.4f}")
        
        # 6. 获取格局信息
        pattern = self.get_pattern(pattern_id)
        pattern_name = pattern.get('name', pattern_id) if pattern else pattern_id
        
        # 7. 计算结构完整性alpha（如果需要）
        day_branch = chart[2][1] if len(chart) > 2 and len(chart[2]) >= 2 else ""
        luck_pillar = context.get('luck_pillar', '') if context else ''
        year_pillar = context.get('annual_pillar', '') if context else ''
        
        energy_flux = {
            "wealth": frequency_vector['wealth'],
            "resource": frequency_vector['resource'],
            "power": frequency_vector['power'],
            "parallel": frequency_vector['parallel'],
            "output": frequency_vector['output'],
            "E_blade": compute_energy_flux(chart, day_master, "羊刃"),
            "E_kill": compute_energy_flux(chart, day_master, "七杀")
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
        
        # 8. 检查成格/破格状态 (Step 4)
        pattern_state = None
        if pattern:
            pattern_state = self._check_pattern_state(
                pattern, chart, day_master, day_branch,
                luck_pillar, year_pillar, alpha
            )
        
        # 9. 格局识别 (Step 6) - 注入当前状态与能量强度 [V1.5]
        dynamic_state = pattern_state.get('state') if pattern_state else 'STABLE'
        recognition_result = self.pattern_recognition(
            normalized_projection, pattern_id, dynamic_state=dynamic_state, sai=sai
        )
            
        # [V2.3] Apply Tensor Modifiers if state is ACTIVATED
        if pattern_state and pattern_state.get('state') == "ACTIVATED":
            modifier = pattern_state.get('tensor_modifier', {})
            for axis, factor in modifier.items():
                if axis in projection:
                    projection[axis] *= factor
            
            # Recalculate normalized projection and SAI after modification
            normalized_projection = tensor_normalize(projection)
            sai = math.sqrt(sum(v ** 2 for v in projection.values()))
            logger.info(f"Applied V2.3 Tensor Modifiers: {modifier}, New SAI: {sai:.4f}")

        result = {
            'pattern_id': pattern_id,
            'pattern_name': pattern_name,
            'version': '2.5',
            'projection': normalized_projection,
            'raw_projection': projection,
            'sai': sai,
            'frequency_vector': frequency_vector,
            'alpha': alpha,
            'recognition': recognition_result,
            'pattern_state': pattern_state,
            'transfer_matrix': transfer_matrix
        }

        # [V2.5] 动态相变处理器 (Phase Transition Processor)
        context_for_trigger = {
            "chart": chart,
            "day_master": day_master,
            "day_branch": day_branch,
            "luck_pillar": luck_pillar,
            "year_pillar": year_pillar,
            "flux_events": flux_events,
            "energy_flux": energy_flux
        }
        
        dynamic_rules = pattern.get('dynamic_states', {})
        if dynamic_rules:
            # 1. 检查崩塌规则
            for rule in dynamic_rules.get('collapse_rules', []):
                if check_trigger(rule.get('trigger'), context_for_trigger):
                    result['recognition']['pattern_type'] = rule.get('default_action', 'COLLAPSED')
                    result['recognition']['matched'] = False
                    result['recognition']['description'] = f"⚠️ {rule.get('action', '结构崩塌')}"
                    result['phase_change'] = 'COLLAPSE'
                    break
            
            # 2. 检查晶化规则 (如果未崩塌)
            if result.get('phase_change') != 'COLLAPSE':
                for rule in dynamic_rules.get('crystallization_rules', []):
                    if check_trigger(rule.get('condition'), context_for_trigger):
                        result['recognition']['pattern_type'] = 'CRYSTALLIZED'
                        result['recognition']['matched'] = True
                        # 晶化态大幅提升Precision Score作为显示
                        p_score = result['recognition'].get('precision_score', 0)
                        result['recognition']['precision_score'] = max(0.96, p_score)
                        result['recognition']['description'] = f"💎 {rule.get('action', '极致成格')}"
                        result['phase_change'] = 'CRYSTALLIZATION'
                        break
        
        return result

