"""
八字档案审计控制器 (Profile Audit Controller)
MVC Controller Layer - 负责档案审计的业务逻辑
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from core.models.profile_audit_model import ProfileAuditModel
from core.models.profile_audit_engines import (
    PatternFrictionAnalysisEngine,
    SystemOptimizationEngine,
    MediumCompensationEngine
)
from core.bazi_profile import BaziProfile
from core.engine_graph import GraphNetworkEngine

logger = logging.getLogger(__name__)


class ProfileAuditController:
    """
    八字档案审计控制器
    负责协调Model和Engine，处理档案审计业务逻辑
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化控制器
        
        Args:
            data_dir: 数据目录路径
        """
        self.model = ProfileAuditModel(data_dir)
        
        # 初始化三个核心引擎
        self.pfa_engine = PatternFrictionAnalysisEngine()
        self.soa_engine = SystemOptimizationEngine()
        self.mca_engine = MediumCompensationEngine()
        
        logger.info("ProfileAuditController initialized")
    
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """
        获取所有档案
        
        Returns:
            档案列表
        """
        return self.model.load_all_profiles()
    
    def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取档案
        
        Args:
            profile_id: 档案ID
            
        Returns:
            档案字典
        """
        return self.model.load_profile_by_id(profile_id)
    
    def perform_deep_audit(self, profile_id: str, year: int = None,
                           city: str = None, micro_env: List[str] = None) -> Dict[str, Any]:
        """
        执行深度审计
        
        Args:
            profile_id: 档案ID
            year: 流年（可选）
            city: 城市（可选）
            micro_env: 微环境列表（可选）
            
        Returns:
            完整的审计报告
        """
        # 1. 加载档案
        profile_data = self.get_profile_by_id(profile_id)
        if not profile_data:
            return {'error': '档案不存在'}
        
        # 2. 创建BaziProfile对象
        try:
            birth_date = datetime(
                profile_data['year'],
                profile_data['month'],
                profile_data['day'],
                profile_data.get('hour', 12),
                profile_data.get('minute', 0)
            )
            gender = 1 if profile_data.get('gender') == '男' else 0
            bazi_profile = BaziProfile(birth_date, gender)
        except Exception as e:
            logger.error(f"创建BaziProfile失败: {e}")
            return {'error': f'创建八字档案失败: {str(e)}'}
        
        # 3. 先执行MCA获取地理信息
        mca_result = self.mca_engine.compensate(bazi_profile, city, micro_env)
        
        # 从MCA结果提取地理信息
        geo_element = None
        geo_factor = 1.0
        if city and mca_result.geo_correction:
            # 找到最大的修正系数对应的元素
            max_correction = max(mca_result.geo_correction.items(), key=lambda x: x[1])
            geo_element = max_correction[0]
            geo_factor = max_correction[1]
        
        # 4. 执行三个核心分析（注入地理信息）
        pfa_result = self.pfa_engine.analyze(bazi_profile, year, geo_element, geo_factor)
        soa_result = self.soa_engine.optimize(bazi_profile, year, geo_element, geo_factor)
        
        # 4. 计算受力矢量（五行能量分布）
        force_vectors = self._calculate_force_vectors(bazi_profile, year, mca_result)
        
        # 5. 生成语义报告
        semantic_report = self._generate_semantic_report(
            profile_data, pfa_result, soa_result, mca_result, force_vectors, year
        )
        
        # 6. 组装完整报告
        return {
            'profile': profile_data,
            'bazi_profile': {
                'pillars': bazi_profile.pillars,
                'day_master': bazi_profile.day_master
            },
            'pfa': {
                'friction_index': pfa_result.friction_index,
                'coherence_level': pfa_result.coherence_level,
                'conflicting_patterns': pfa_result.conflicting_patterns,
                'semantic': pfa_result.semantic_interpretation
            },
            'soa': {
                'optimal_elements': soa_result.optimal_elements,
                'stability_score': soa_result.stability_score,
                'entropy_reduction': soa_result.entropy_reduction,
                'semantic': soa_result.semantic_interpretation
            },
            'mca': {
                'geo_correction': mca_result.geo_correction,
                'micro_env_correction': mca_result.micro_env_correction,
                'total_correction': mca_result.total_correction,
                'semantic': mca_result.semantic_interpretation
            },
            'force_vectors': force_vectors,
            'semantic_report': semantic_report,
            'audit_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _calculate_force_vectors(self, bazi_profile: BaziProfile, year: int,
                                mca_result) -> Dict[str, float]:
        """计算受力矢量（五行能量分布）"""
        try:
            from core.engine_graph import GraphNetworkEngine
            from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
            
            pillars = bazi_profile.pillars
            bazi = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
            
            luck_pillar = bazi_profile.get_luck_pillar_at(year) if year else None
            year_pillar = bazi_profile.get_year_pillar(year) if year else None
            
            engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
            
            # 应用介质修正
            geo_modifiers = {}
            if mca_result:
                for element, factor in mca_result.total_correction.items():
                    if factor != 1.0:
                        geo_modifiers[element] = factor - 1.0  # 转换为修正量
            
            engine.initialize_nodes(
                bazi, bazi_profile.day_master,
                luck_pillar, year_pillar,
                geo_modifiers=geo_modifiers if geo_modifiers else None
            )
            engine.build_adjacency_matrix()
            engine.propagate()
            
            # 计算五行能量
            element_energies = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
            
            for node in engine.nodes:
                element = node.element
                if element in element_energies:
                    if hasattr(node.current_energy, 'mean'):
                        energy = node.current_energy.mean
                    else:
                        energy = float(node.current_energy)
                    element_energies[element] += energy
            
            # 归一化
            total = sum(element_energies.values())
            if total > 0:
                for element in element_energies:
                    element_energies[element] = element_energies[element] / total * 100.0
            
            return element_energies
            
        except Exception as e:
            logger.error(f"计算受力矢量失败: {e}")
            return {'metal': 20.0, 'wood': 20.0, 'water': 20.0, 'fire': 20.0, 'earth': 20.0}
    
    def _generate_semantic_report(self, profile_data: Dict, pfa_result, soa_result,
                                 mca_result, force_vectors: Dict, year: int) -> Dict[str, str]:
        """生成语义报告（人话翻译）"""
        
        # 1. 核心矛盾
        core_conflict = self._generate_core_conflict(pfa_result, soa_result)
        
        # 2. 深度画像（300字左右）
        persona = self._generate_persona(profile_data, pfa_result, soa_result, force_vectors)
        
        # 3. 财富相预测
        wealth_prediction = self._generate_wealth_prediction(soa_result, force_vectors, year)
        
        # 4. 干预药方
        prescription = self._generate_prescription(soa_result, mca_result, pfa_result)
        
        return {
            'core_conflict': core_conflict,
            'persona': persona,
            'wealth_prediction': wealth_prediction,
            'prescription': prescription
        }
    
    def _generate_core_conflict(self, pfa_result, soa_result) -> str:
        """生成核心矛盾"""
        friction = pfa_result.friction_index
        stability = soa_result.stability_score
        
        if friction > 60 and stability < 0.5:
            return "命局中存在严重的格局冲突，系统稳定性极低，导致理想与现实的强烈撕裂，需要外部干预来调和矛盾。"
        elif friction > 40:
            return f"命局中存在格局冲突（{', '.join(pfa_result.conflicting_patterns[:2]) if pfa_result.conflicting_patterns else '内在矛盾'}），导致性格中的自我拆台，需要寻找平衡点。"
        elif stability < 0.5:
            return "系统能量分布不稳定，存在内耗，需要通过优化来提升稳定性。"
        else:
            return "命局基本协调，但存在微妙的平衡点需要维护。"
    
    def _generate_persona(self, profile_data: Dict, pfa_result, soa_result,
                         force_vectors: Dict) -> str:
        """生成深度画像（300字左右）"""
        name = profile_data.get('name', '此人')
        friction = pfa_result.friction_index
        stability = soa_result.stability_score
        
        # 基于受力矢量分析性格
        max_element = max(force_vectors.items(), key=lambda x: x[1])
        element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
        dominant_element = element_cn.get(max_element[0], max_element[0])
        
        parts = []
        parts.append(f"{name}的命局以{dominant_element}元素为主导，")
        
        if friction < 30:
            parts.append("格局体系高度协调，各格局力量相互支撑。")
        elif friction < 60:
            parts.append("格局体系基本协调，但存在微妙的相位干扰。")
        else:
            parts.append("格局体系存在显著冲突，能量场不稳定。")
        
        if stability > 0.7:
            parts.append("系统稳定性较高，能量分布相对均衡。")
        elif stability < 0.4:
            parts.append("系统稳定性较低，存在明显的内耗。")
        else:
            parts.append("系统稳定性中等，需要适度优化。")
        
        # 基于最优元素分析
        if soa_result.optimal_elements:
            best_element = list(soa_result.optimal_elements.keys())[0]
            best_cn = element_cn.get(best_element, best_element)
            parts.append(f"通过注入{best_cn}元素能够显著改善系统状态。")
        
        # 性格特征
        if dominant_element == '金':
            parts.append("性格刚毅果断，但可能过于刚硬，需要柔化。")
        elif dominant_element == '木':
            parts.append("性格生机勃勃，但可能过于急躁，需要沉稳。")
        elif dominant_element == '水':
            parts.append("性格灵活变通，但可能过于流动，需要定力。")
        elif dominant_element == '火':
            parts.append("性格热情奔放，但可能过于激烈，需要冷静。")
        elif dominant_element == '土':
            parts.append("性格稳重踏实，但可能过于保守，需要突破。")
        
        return " ".join(parts)
    
    def _generate_wealth_prediction(self, soa_result, force_vectors: Dict, year: int) -> str:
        """生成财富相预测"""
        stability = soa_result.stability_score
        entropy_reduction = soa_result.entropy_reduction
        
        # 基于稳定性和熵值降低判断财富类型
        if stability > 0.7 and entropy_reduction > 0.1:
            wealth_type = "稳定积累型"
            wealth_level = "大富"
            desc = "系统高度稳定，能量流动顺畅，财富能够稳定积累，属于大富之相。"
        elif stability > 0.6:
            wealth_type = "稳步增长型"
            wealth_level = "小康"
            desc = "系统稳定性良好，财富能够稳步增长，属于小康之相。"
        elif entropy_reduction > 0.05:
            wealth_type = "暗能吸积型"
            wealth_level = "中富"
            desc = "通过优化能够降低内耗，财富属于暗能吸积型，需要激活引力场。"
        elif stability < 0.4:
            wealth_type = "动荡泄漏型"
            wealth_level = "动荡"
            desc = "系统稳定性低，存在内耗，财富容易动荡泄漏，需要外部干预。"
        else:
            wealth_type = "平衡维持型"
            wealth_level = "小康"
            desc = "系统基本平衡，财富能够维持，属于小康之相。"
        
        # 地理建议
        if entropy_reduction > 0.1:
            desc += " 建议选择能够激活能量场的城市和环境。"
        
        return f"**财富类型**: {wealth_type} | **财富等级**: {wealth_level}\n\n{desc}"
    
    def _generate_prescription(self, soa_result, mca_result, pfa_result) -> str:
        """生成干预药方"""
        parts = []
        
        # 用神（最优元素）
        if soa_result.optimal_elements:
            best_element = list(soa_result.optimal_elements.keys())[0]
            element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
            best_cn = element_cn.get(best_element, best_element)
            amount = soa_result.optimal_elements[best_element]
            parts.append(f"**用神**: {best_cn}（强度{amount:.2f}）")
        
        # 喜神（相生元素）
        if soa_result.optimal_elements:
            best_element = list(soa_result.optimal_elements.keys())[0]
            generation_map = {
                'wood': '水', 'fire': '木', 'earth': '火',
                'metal': '土', 'water': '金'
            }
            like_element = generation_map.get(best_element)
            if like_element:
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                parts.append(f"**喜神**: {element_cn.get(like_element, like_element)}")
        
        # 忌神（相克元素）
        if soa_result.optimal_elements:
            best_element = list(soa_result.optimal_elements.keys())[0]
            control_map = {
                'wood': '金', 'fire': '水', 'earth': '木',
                'metal': '火', 'water': '土'
            }
            avoid_element = control_map.get(best_element)
            if avoid_element:
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                parts.append(f"**忌神**: {element_cn.get(avoid_element, avoid_element)}")
        
        # 调候建议
        if mca_result and mca_result.semantic_interpretation:
            parts.append(f"\n**环境调候**: {mca_result.semantic_interpretation}")
        
        # 具体建议
        if pfa_result.friction_index > 60:
            parts.append("\n**改运建议**: 命局存在严重冲突，建议通过环境调整和能量注入来调和矛盾，避免在冲突激化的年份做出重大决策。")
        elif soa_result.entropy_reduction > 0.1:
            parts.append("\n**改运建议**: 通过优化能够显著改善系统状态，建议在有利的年份和环境进行重要决策。")
        
        return "\n".join(parts) if parts else "当前系统状态较优，保持现状即可。"

