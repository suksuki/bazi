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
                           city: str = None, micro_env: List[str] = None,
                           use_llm: bool = False) -> Dict[str, Any]:
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
        
        # [QGA V23.5] 获取格局优先级信息，传递给SOA引擎
        prioritized_patterns = getattr(self.pfa_engine, '_prioritized_patterns', {})
        primary_pattern = prioritized_patterns.get('primary')
        conflict_patterns = prioritized_patterns.get('conflicts', [])
        
        # [QGA V24.0] 传递特殊格局信息给SOA引擎
        special_pattern = getattr(self.pfa_engine, '_special_pattern_locked', None)
        
        soa_result = self.soa_engine.optimize(
            bazi_profile, year, geo_element, geo_factor,
            primary_pattern=primary_pattern,
            conflict_patterns=conflict_patterns,
            special_pattern=special_pattern
        )
        
        # 4. 计算受力矢量（五行能量分布，包含微环境偏移）
        force_vectors = self._calculate_force_vectors(bazi_profile, year, mca_result, micro_env)
        
        # 5. [QGA V24.2] 流年格局全息审计：分析当前年份触发的所有格局（时空耦合）
        pattern_audit = self._analyze_year_patterns(
            bazi_profile, year, pfa_result, soa_result, geo_element, geo_factor
        )
        
        # 6. 生成语义报告（基于实时激活格局）
        # [QGA V24.3] 传递use_llm参数
        # [QGA V24.4] 传递额外信息用于结构化数据
        semantic_report = self._generate_semantic_report(
            profile_data, pfa_result, soa_result, mca_result, force_vectors, year, pattern_audit, use_llm,
            bazi_profile=bazi_profile, city=city, micro_env=micro_env
        )
        
        # 7. 组装完整报告
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
            'pattern_audit': pattern_audit,  # [QGA V24.1] 流年格局全息审计
            'audit_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # [QGA V24.3] 如果LLM生成了五行校准，添加到结果中
        if hasattr(self, '_llm_element_calibration'):
            result['llm_calibration'] = self._llm_element_calibration
            # 清除，避免影响下次审计
            delattr(self, '_llm_element_calibration')
        
        return result
        
        # [QGA V24.3] 如果LLM生成了五行校准，添加到结果中
        if hasattr(self, '_llm_element_calibration'):
            result['llm_calibration'] = self._llm_element_calibration
            # 清除，避免影响下次审计
            delattr(self, '_llm_element_calibration')
        
        return result
    
    def _calculate_force_vectors(self, bazi_profile: BaziProfile, year: int,
                                mca_result, micro_env: List[str] = None) -> Dict[str, float]:
        """
        计算受力矢量（五行能量分布）
        [优化4] 应用微环境的矢量偏移
        """
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
            
            # [QGA V23.5] 修正五行算法：能量衰减模型
            # 能量 E = 基础值 × 月令系数(1.5-2.0) × 位置衰减(坐下>月干>年时) × 合化变质
            element_energies = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
            
            pillars = bazi_profile.pillars
            month_branch = pillars['month'][1]  # 月支
            
            # 月令系数（根据季节）
            season_multiplier = self._get_season_multiplier(month_branch)
            
            # 位置衰减系数
            position_decay = {
                'year': 0.7,   # 年柱
                'month': 1.5,  # 月柱（月令，最高）
                'day': 1.2,    # 日柱（坐下）
                'hour': 0.8    # 时柱
            }
            
            # 计算基础能量（考虑位置衰减）
            pillar_map = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}
            for pillar_name, pillar_idx in pillar_map.items():
                for node in engine.nodes:
                    # 简化：根据节点位置判断（实际应该从node获取位置信息）
                    element = node.element
                    if element in element_energies:
                        if hasattr(node.current_energy, 'mean'):
                            base_energy = node.current_energy.mean
                        else:
                            base_energy = float(node.current_energy)
                        
                        # 应用位置衰减
                        decay = position_decay.get(pillar_name, 1.0)
                        # 如果是月柱，应用月令系数
                        if pillar_name == 'month':
                            decay *= season_multiplier
                        
                        element_energies[element] += base_energy * decay
            
            # [QGA V23.5] 合化变质判定
            element_energies = self._apply_combination_transformation(
                element_energies, pillars, bazi_profile.day_master
            )
            
            # 归一化
            total = sum(element_energies.values())
            if total > 0:
                for element in element_energies:
                    element_energies[element] = element_energies[element] / total * 100.0
            
            # [优化4] 应用微环境的矢量偏移
            if micro_env:
                vector_offsets = self.mca_engine.get_micro_env_vector_offsets(micro_env)
                for element, offset in vector_offsets.items():
                    if offset != 0.0:
                        element_energies[element] = max(0.0, min(100.0, element_energies[element] + offset))
                
                # 重新归一化（确保总和为100%）
                total = sum(element_energies.values())
                if total > 0:
                    for element in element_energies:
                        element_energies[element] = element_energies[element] / total * 100.0
            
            return element_energies
            
        except Exception as e:
            logger.error(f"计算受力矢量失败: {e}")
            return {'metal': 20.0, 'wood': 20.0, 'water': 20.0, 'fire': 20.0, 'earth': 20.0}
    
    def _get_element_from_stem(self, stem: str) -> str:
        """
        从天干获取五行元素
        
        Args:
            stem: 天干（如"甲"、"乙"等）
            
        Returns:
            五行元素（"木"、"火"、"土"、"金"、"水"）
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        element = BaziParticleNexus.get_element(stem)
        # 转换为中文
        element_map = {
            'Wood': '木',
            'Fire': '火',
            'Earth': '土',
            'Metal': '金',
            'Water': '水'
        }
        return element_map.get(element, '土')
    
    def _get_season_multiplier(self, month_branch: str) -> float:
        """
        [QGA V23.5] 获取月令系数（根据季节）
        春季木旺(2.0)，夏季火旺(2.0)，秋季金旺(2.0)，冬季水旺(2.0)
        """
        spring_branches = ['寅', '卯', '辰']  # 春
        summer_branches = ['巳', '午', '未']  # 夏
        autumn_branches = ['申', '酉', '戌']  # 秋
        winter_branches = ['亥', '子', '丑']  # 冬
        
        # [QGA V24.0] 月令权重提升到3倍（月令是系统的"太阳"）
        if month_branch in spring_branches:
            return 3.0  # 木旺（春季）
        elif month_branch in summer_branches:
            return 3.0  # 火旺（夏季）
        elif month_branch in autumn_branches:
            return 3.0  # 金旺（秋季）
        elif month_branch in winter_branches:
            return 3.0  # 水旺（冬季）
        return 2.0  # 默认（提升）
    
    def _apply_combination_transformation(self, element_energies: Dict[str, float],
                                         pillars: Dict, day_master: str) -> Dict[str, float]:
        """
        [QGA V23.5] 合化变质判定
        如果发生"甲己合化土"，原本木的能量清零，转化为土
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        # 天干五合
        stem_combinations = {
            ('甲', '己'): 'earth',  # 甲己合化土
            ('乙', '庚'): 'metal',  # 乙庚合化金
            ('丙', '辛'): 'water',  # 丙辛合化水
            ('丁', '壬'): 'wood',   # 丁壬合化木
            ('戊', '癸'): 'fire',   # 戊癸合化火
        }
        
        stems = [pillars['year'][0], pillars['month'][0], 
                 pillars['day'][0], pillars['hour'][0]]
        
        # 检查是否有合化
        for i, s1 in enumerate(stems):
            for j, s2 in enumerate(stems[i+1:], i+1):
                pair = (s1, s2)
                reverse_pair = (s2, s1)
                
                if pair in stem_combinations:
                    target_element = stem_combinations[pair]
                elif reverse_pair in stem_combinations:
                    target_element = stem_combinations[reverse_pair]
                else:
                    continue
                
                # 获取原始元素（天干五行映射）
                stem_elements = {
                    '甲': 'wood', '乙': 'wood',
                    '丙': 'fire', '丁': 'fire',
                    '戊': 'earth', '己': 'earth',
                    '庚': 'metal', '辛': 'metal',
                    '壬': 'water', '癸': 'water'
                }
                s1_element = stem_elements.get(s1, 'earth')
                s2_element = stem_elements.get(s2, 'earth')
                
                # 简化：将两个天干的能量转移到合化后的元素
                if s1_element in element_energies:
                    transfer_energy = element_energies[s1_element] * 0.3  # 转移30%
                    element_energies[s1_element] -= transfer_energy
                    element_energies[target_element] += transfer_energy
                
                if s2_element in element_energies:
                    transfer_energy = element_energies[s2_element] * 0.3
                    element_energies[s2_element] -= transfer_energy
                    element_energies[target_element] += transfer_energy
        
        return element_energies
    
    def _generate_semantic_report(self, profile_data: Dict, pfa_result, soa_result,
                                 mca_result, force_vectors: Dict, year: int,
                                 pattern_audit: Dict = None, use_llm: bool = False,
                                 bazi_profile: BaziProfile = None, city: str = None,
                                 micro_env: List[str] = None) -> Dict[str, str]:
        """
        生成语义报告（人话翻译）
        [QGA V24.2] 基于实时激活格局生成报告
        [QGA V24.3] 集成LLM语义合成器
        """
        
        # 1. 核心矛盾
        core_conflict = self._generate_core_conflict(pfa_result, soa_result)
        
        # 2. 深度画像（300字左右）
        # [QGA V24.3] 优先使用LLM生成，回退到规则生成
        persona = self._generate_persona_with_llm(
            profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit, use_llm,
            city=city, micro_env=micro_env
        )
        
        # 3. 财富相预测
        wealth_prediction = self._generate_wealth_prediction(soa_result, force_vectors, year, mca_result)
        
        # 4. 干预药方
        prescription = self._generate_prescription(soa_result, mca_result, pfa_result)
        
        result = {
            'core_conflict': core_conflict,
            'persona': persona,
            'wealth_prediction': wealth_prediction,
            'prescription': prescription
        }
        
        # [QGA V24.4] 如果LLM生成了debug信息，添加到结果中
        if hasattr(self, '_llm_debug_data'):
            debug_info = self._llm_debug_data
            result.update(debug_info)
            logger.info(f"✅ Debug数据已添加到报告: debug_data={debug_info.get('debug_data') is not None}, "
                       f"debug_prompt={bool(debug_info.get('debug_prompt'))}, "
                       f"debug_response={bool(debug_info.get('debug_response'))}")
            # 清除，避免影响下次审计
            delattr(self, '_llm_debug_data')
        else:
            logger.warning("⚠️ _llm_debug_data不存在，可能LLM未调用或调用失败")
        
        return result
    
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
    
    def _generate_persona_with_llm(self, profile_data: Dict, pfa_result, soa_result,
                                   force_vectors: Dict, mca_result=None, year: int = None,
                                   pattern_audit: Dict = None, use_llm: bool = False,
                                   city: str = None, micro_env: List[str] = None) -> str:
        """
        [QGA V24.3] 使用LLM生成画像（优先），回退到规则生成
        
        Args:
            use_llm: 是否使用LLM（从UI传入）
        """
        if not use_llm:
            # 直接使用规则生成
            return self._generate_persona(
                profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
            )
        
        try:
            from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
            
            synthesizer = LLMSemanticSynthesizer(use_llm=True)
            
            # 获取激活格局
            if pattern_audit:
                active_patterns = pattern_audit.get('patterns', [])
                synthesized_field = {
                    'has_luck': bool(pattern_audit.get('luck_pillar')),
                    'has_year': bool(pattern_audit.get('year_pillar')),
                    'geo_element': None  # 可以从mca_result获取
                }
            else:
                # 回退：从PFA结果获取格局
                active_patterns = getattr(self.pfa_engine, '_last_detected_patterns', [])
                synthesized_field = {}
            
            # 获取额外信息用于结构化数据
            bazi_profile = None
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
            except:
                pass
            
            # 构建地理信息
            geo_info_parts = []
            if city:
                geo_info_parts.append(f"城市{city}")
            if micro_env:
                geo_info_parts.extend(micro_env)
            geo_info = " | ".join(geo_info_parts) if geo_info_parts else None
            
            # 获取日主
            day_master = None
            if bazi_profile:
                day_master_stem = bazi_profile.pillars['day'][0]
                day_master_element = self._get_element_from_stem(day_master_stem)
                day_master_yinyang = "阴" if day_master_stem in ['乙', '丁', '己', '辛', '癸'] else "阳"
                day_master = f"{day_master_stem}{day_master_element} ({day_master_yinyang}{day_master_element})"
            
            # 获取大运和流年柱
            luck_pillar_str = None
            year_pillar_str = None
            if bazi_profile and year:
                try:
                    luck_pillar = bazi_profile.get_luck_pillar(year)
                    if luck_pillar:
                        luck_pillar_str = f"{luck_pillar[0]}{luck_pillar[1]}"
                    year_pillar = bazi_profile.get_year_pillar(year)
                    if year_pillar:
                        year_pillar_str = f"{year_pillar[0]}{year_pillar[1]}"
                except:
                    pass
            
            # 使用LLM合成（结构化协议）
            result = synthesizer.synthesize_persona(
                active_patterns,
                synthesized_field,
                profile_data.get('name', '此人'),
                day_master=day_master,
                force_vectors=force_vectors,
                year=year,
                luck_pillar=luck_pillar_str,
                year_pillar=year_pillar_str,
                geo_info=geo_info
            )
            
            persona = result.get('persona', '')
            element_calibration = result.get('element_calibration')
            
            # [QGA V24.4] 保存debug信息到类属性，供UI使用
            # 无论LLM成功还是失败，都保存debug_data
            self._llm_debug_data = {
                'debug_data': result.get('debug_data'),
                'debug_prompt': result.get('debug_prompt', ''),
                'debug_response': result.get('debug_response', ''),
                'debug_error': result.get('debug_error')
            }
            
            # [QGA V24.3] 如果LLM推导出五行偏移，存储到类属性，供后续使用
            if element_calibration:
                logger.info(f"LLM推导的五行偏移: {element_calibration}")
                # 将校准信息存储到类属性，供UI使用
                self._llm_element_calibration = element_calibration
            
            # 如果LLM生成失败，回退到规则生成
            if not persona or persona.startswith("LLM生成失败"):
                logger.warning("LLM生成失败，回退到规则生成")
                # 即使回退，也保留debug_data
                fallback_persona = self._generate_persona(
                    profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
                )
                # 确保debug_data仍然存在
                if not self._llm_debug_data.get('debug_data'):
                    # 如果没有debug_data，至少保存结构化数据的占位符
                    logger.warning("LLM结果中没有debug_data，但已尝试保存")
                return fallback_persona
            
            return persona
            
        except Exception as e:
            logger.error(f"LLM合成失败: {e}，回退到规则生成")
            # 即使异常，也尝试保存debug_data（如果有的话）
            # 构建一个基本的结构化数据
            try:
                from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
                synthesizer = LLMSemanticSynthesizer(use_llm=False)
                if pattern_audit:
                    active_patterns = pattern_audit.get('patterns', [])
                else:
                    active_patterns = getattr(self.pfa_engine, '_last_detected_patterns', [])
                
                if active_patterns:
                    synthesized_field = {
                        'has_luck': bool(pattern_audit.get('luck_pillar') if pattern_audit else False),
                        'has_year': bool(pattern_audit.get('year_pillar') if pattern_audit else False),
                        'geo_element': None
                    }
                    structured_data = synthesizer._build_structured_data(
                        active_patterns, synthesized_field, profile_data.get('name', '此人'),
                        None, force_vectors, year, None, None, None
                    )
                    self._llm_debug_data = {
                        'debug_data': structured_data,
                        'debug_prompt': f"LLM调用异常: {str(e)}",
                        'debug_response': '',
                        'debug_error': str(e)
                    }
            except:
                pass  # 如果构建失败，至少不阻塞
        
            return self._generate_persona(
                profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
            )
    
    def _generate_persona(self, profile_data: Dict, pfa_result, soa_result,
                         force_vectors: Dict, mca_result=None, year: int = None,
                         pattern_audit: Dict = None) -> str:
        """
        生成深度画像（300字左右）
        [QGA V23.5] 使用决策树逻辑，而非标签堆砌
        IF (Primary Pattern = X) AND (Conflict = Y) THEN Output [Persona A]
        """
        name = profile_data.get('name', '此人')
        friction = pfa_result.friction_index
        
        # [QGA V24.2] 基于实时激活格局生成画像
        # 优先使用时空耦合后的最终状态
        parts = []
        
        # 优先级0：检查是否有格局状态变化
        if pattern_audit:
            state_changes = pattern_audit.get('state_changes', [])
            if state_changes:
                change = state_changes[0]  # 取第一个状态变化
                parts.append(f"{name}的命局在{year}年发生了**格局状态变化**。")
                parts.append(f"原局格局【{change.get('original', '')}】")
                parts.append(f"在时空耦合（大运+流年+地理）作用下，")
                parts.append(f"已退化为【{change.get('current', '')}】。")
                parts.append(f"{change.get('impact', '')}")
                parts.append(f"因此，你的用神和应对策略必须立即调整。")
                return " ".join(parts)
        
        # [QGA V24.0] 模式优先驱动：先检查特殊格局
        special_pattern = getattr(self.pfa_engine, '_special_pattern_locked', None)
        
        # 决策树：先治病，再强身
        # [QGA V24.0] 优先级0：特殊格局锁死，围绕格局生命主题生成画像
        if special_pattern:
            pattern_name = special_pattern.get('name', '特殊格局')
            life_theme = special_pattern.get('life_theme', '')
            pattern_type = special_pattern.get('type')
            
            parts.append(f"{name}的命局呈现**{pattern_name}**格局，这是超稳态结构。")
            parts.append(life_theme)
            
            # 根据格局类型生成详细画像
            if pattern_type == 'shang_guan_shang_jin':
                parts.append("你具有极强的创造力和表达能力，不受传统规则约束。")
                parts.append("适合从事艺术、创作、自由职业等需要发挥才华的领域。")
                parts.append("财富来源主要是通过才华变现，而非传统意义上的稳定收入。")
            elif pattern_type == 'from_wealth':
                parts.append("你的人生以财富为核心追求，具有极强的商业头脑和经营能力。")
                parts.append("善于发现商机，能够快速积累财富。")
                parts.append("但需要注意平衡物质追求与精神追求，避免成为金钱的奴隶。")
            elif pattern_type == 'superconductor':
                parts.append("你追求纯粹与完美，具有超常的专注力和执行力。")
                parts.append("适合从事需要极致专注的领域，如科研、精密制造等。")
                parts.append("但需要注意避免过度追求完美导致的心理压力。")
            
            return " ".join(parts)
        
        # [QGA V23.5] 获取格局优先级信息
        prioritized_patterns = getattr(self.pfa_engine, '_prioritized_patterns', {})
        primary_pattern = prioritized_patterns.get('primary')
        conflict_patterns = prioritized_patterns.get('conflicts', [])
        
        # 第一优先级：如果有严重的相位冲突，必须先谈这个"痛点"
        if conflict_patterns and friction > 40:
            conflict_name = conflict_patterns[0].get('name', '格局冲突')
            
            # 根据冲突格局类型生成画像
            if '伤官' in conflict_name and '官' in conflict_name:
                # 伤官见官：权威与自由的冲突
                parts.append(f"{name}的命局核心矛盾是**权威与自由的撕裂**。")
                parts.append("伤官见官格局意味着你天生具有挑战权威、追求自由的冲动，")
                parts.append("但现实环境（官星）要求你遵守规则、服从秩序。")
                parts.append("这种内在冲突导致你时常在'反抗'与'妥协'之间摇摆，")
                parts.append("理想与现实的强烈撕裂感成为你人生的主旋律。")
            else:
                parts.append(f"{name}的命局存在严重的格局冲突（{conflict_name}），")
                parts.append("这是你人生最大的'痛点'。")
                parts.append("系统稳定性极低，导致理想与现实的强烈撕裂。")
        
        # 第二优先级：主格局（月令格神）
        elif primary_pattern:
            primary_name = primary_pattern.get('name', '主格局')
            parts.append(f"{name}的命局以{primary_name}为主导，")
            parts.append("这是你人生的底色和核心动力源。")
            
            # 基于主格局生成性格特征
            if '伤官' in primary_name:
                parts.append("你具有强烈的表达欲和创造力，但可能过于叛逆，需要适度收敛。")
            elif '正官' in primary_name:
                parts.append("你具有强烈的责任感和秩序感，但可能过于拘谨，需要适度突破。")
            elif '财' in primary_name:
                parts.append("你具有强烈的财富欲望和商业头脑，但可能过于功利，需要平衡精神追求。")
            elif '印' in primary_name:
                parts.append("你具有强烈的学习能力和包容心，但可能过于依赖，需要培养独立性。")
        
        # 第三优先级：如果没有格局，基于五行分析
        else:
            max_element = max(force_vectors.items(), key=lambda x: x[1])
            element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
            dominant_element = element_cn.get(max_element[0], max_element[0])
            parts.append(f"{name}的命局以{dominant_element}元素为主导，")
            
            behavior_map = {
                '金': '性格刚毅果断，但可能过于刚硬',
                '木': '性格生机勃勃，但可能过于急躁',
                '水': '性格灵活变通，但可能缺乏定力',
                '火': '性格热情奔放，但可能过于激烈',
                '土': '性格稳重踏实，但可能过于保守'
            }
            parts.append(behavior_map.get(dominant_element, '性格特征明显'))
        
        # 环境因子影响（如果有）
        if mca_result and mca_result.geo_correction:
            max_geo = max(mca_result.geo_correction.items(), key=lambda x: x[1])
            if max_geo[1] > 1.1:
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                geo_cn = element_cn.get(max_geo[0], max_geo[0])
                parts.append(f" 当前环境（{geo_cn}属性补强）进一步强化了这种特质。")
        
        return " ".join(parts)
    
    def _generate_wealth_prediction(self, soa_result, force_vectors: Dict, year: int, 
                                   mca_result=None) -> str:
        """
        生成财富相预测
        [优化3] 使用因果链逻辑：[物理原因 -> 行为效应 -> 命运结果]
        """
        stability = soa_result.stability_score
        entropy_reduction = soa_result.entropy_reduction
        
        # [优化3] 因果链生成
        parts = []
        
        # 1. 物理原因（If）
        if stability > 0.7 and entropy_reduction > 0.1:
            wealth_type = "稳定积累型"
            wealth_level = "大富"
            parts.append("由于系统高度稳定（稳定性{:.2f}），能量流动顺畅，")
            parts.append("通过优化能够显著降低内耗（熵值降低{:.3f}），")
        elif stability > 0.6:
            wealth_type = "稳步增长型"
            wealth_level = "小康"
            parts.append("由于系统稳定性良好（{:.2f}），")
            parts.append("能量分布相对均衡，")
        elif entropy_reduction > 0.05:
            wealth_type = "暗能吸积型"
            wealth_level = "中富"
            parts.append("由于通过优化能够降低内耗（熵值降低{:.3f}），")
            parts.append("系统处于暗能吸积状态，")
        elif stability < 0.4:
            wealth_type = "动荡泄漏型"
            wealth_level = "动荡"
            parts.append("由于系统稳定性极低（{:.2f}），存在明显内耗，")
            parts.append("能量场不稳定，")
        else:
            wealth_type = "平衡维持型"
            wealth_level = "小康"
            parts.append("由于系统基本平衡（稳定性{:.2f}），")
            parts.append("能量分布相对稳定，")
        
        # 2. 行为效应（Then）
        if wealth_type == "稳定积累型":
            parts.append("财富能够稳定积累，属于大富之相。")
        elif wealth_type == "稳步增长型":
            parts.append("财富能够稳步增长，属于小康之相。")
        elif wealth_type == "暗能吸积型":
            parts.append("财富属于暗能吸积型，需要激活引力场才能转化为实际收益。")
        elif wealth_type == "动荡泄漏型":
            parts.append("财富容易动荡泄漏，需要外部干预来调和矛盾。")
        else:
            parts.append("财富能够维持，属于小康之相。")
        
        # 3. 命运结果（Because）
        if mca_result and mca_result.geo_correction:
            max_geo = max(mca_result.geo_correction.items(), key=lambda x: x[1])
            if max_geo[1] > 1.1:
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                geo_cn = element_cn.get(max_geo[0], max_geo[0])
                parts.append(f" 当前环境（{geo_cn}属性补强）有助于财富积累。")
            elif max_geo[1] < 0.95:
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                geo_cn = element_cn.get(max_geo[0], max_geo[0])
                parts.append(f" ⚠️ 当前环境（{geo_cn}属性削弱）可能阻碍财富增长，建议调整。")
        
        if entropy_reduction > 0.1:
            parts.append(" 建议选择能够激活能量场的城市和环境，以最大化财富潜力。")
        
        desc = "".join(parts).format(stability, entropy_reduction, stability, entropy_reduction, stability)
        
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
    
    def _analyze_year_patterns(self, bazi_profile: BaziProfile, year: int,
                               pfa_result, soa_result, geo_element: str = None,
                               geo_factor: float = 1.0) -> Dict[str, Any]:
        """
        [QGA V24.2] 时空耦合格局审计
        计算【原局八字】+【当前大运】+【当前流年】+【地理/微环境因子】的最终合成状态
        识别实时激活格局，而非简单列出原局格局
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        pillars = bazi_profile.pillars
        chart = [
            (pillars['year'][0], pillars['year'][1]),
            (pillars['month'][0], pillars['month'][1]),
            (pillars['day'][0], pillars['day'][1]),
            (pillars['hour'][0], pillars['hour'][1])
        ]
        
        luck_pillar = bazi_profile.get_luck_pillar_at(year) if year else None
        year_pillar = bazi_profile.get_year_pillar(year) if year else None
        day_master = bazi_profile.day_master
        
        # [QGA V24.2] 步骤1：合成所有4个因子为单一矢量场
        synthesized_field = self._synthesize_field_strength(
            chart, luck_pillar, year_pillar, geo_element, geo_factor, day_master
        )
        
        # [QGA V24.2] 步骤2：检测格局状态变化
        pattern_state_changes = self._detect_pattern_state_changes(
            chart, luck_pillar, year_pillar, day_master
        )
        
        # [QGA V24.2] 步骤3：识别最终激活格局（基于合成场强）
        final_active_patterns = self._identify_final_active_patterns(
            chart, luck_pillar, year_pillar, geo_element, geo_factor,
            day_master, synthesized_field, pattern_state_changes
        )
        
        pattern_list = []
        for pattern in final_active_patterns:
            pattern_info = self._parse_pattern_details(
                pattern, chart, luck_pillar, year_pillar, day_master, year,
                pattern.get('type', 'active'), synthesized_field
            )
            pattern_list.append(pattern_info)
        
        return {
            'year': year,
            'year_pillar': year_pillar,
            'luck_pillar': luck_pillar,
            'patterns': pattern_list,
            'total_count': len(pattern_list),
            'synthesized_field': synthesized_field,
            'state_changes': pattern_state_changes
        }
    
    def _synthesize_field_strength(self, chart: List, luck_pillar: str, year_pillar: str,
                                   geo_element: str, geo_factor: float, day_master: str) -> Dict[str, Any]:
        """
        [QGA V24.2] 合成场强：将原局+大运+流年+地理合并为单一矢量场
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        # 收集所有干支（原局+大运+流年）
        all_stems = [p[0] for p in chart]
        all_branches = [p[1] for p in chart]
        
        if luck_pillar and len(luck_pillar) >= 2:
            all_stems.append(luck_pillar[0])
            all_branches.append(luck_pillar[1])
        
        if year_pillar and len(year_pillar) >= 2:
            all_stems.append(year_pillar[0])
            all_branches.append(year_pillar[1])
        
        # 计算十神分布（合成后）
        ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in all_stems if s]
        
        # 计算五行能量分布（合成后）
        element_counts = {'metal': 0, 'wood': 0, 'water': 0, 'fire': 0, 'earth': 0}
        
        # 天干五行
        stem_elements = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        
        for stem in all_stems:
            if stem in stem_elements:
                element_counts[stem_elements[stem]] += 1
        
        # 地支五行（简化：只计算地支本气）
        branch_elements = {
            '寅': 'wood', '卯': 'wood',
            '巳': 'fire', '午': 'fire',
            '申': 'metal', '酉': 'metal',
            '亥': 'water', '子': 'water',
            '辰': 'earth', '戌': 'earth', '丑': 'earth', '未': 'earth'
        }
        
        for branch in all_branches:
            if branch in branch_elements:
                element_counts[branch_elements[branch]] += 1
        
        # 应用地理修正
        if geo_element:
            element_counts[geo_element] = int(element_counts[geo_element] * geo_factor)
        
        return {
            'ten_gods': ten_gods,
            'element_counts': element_counts,
            'all_stems': all_stems,
            'all_branches': all_branches,
            'has_luck': luck_pillar is not None,
            'has_year': year_pillar is not None,
            'geo_element': geo_element
        }
    
    def _detect_pattern_state_changes(self, chart: List, luck_pillar: str,
                                     year_pillar: str, day_master: str) -> List[Dict]:
        """
        [QGA V24.2] 检测格局状态变化
        例如：原局伤官伤尽，但流年注入官星后变为伤官见官
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        state_changes = []
        
        if not year_pillar:
            return state_changes
        
        year_gan = year_pillar[0] if len(year_pillar) > 0 else ''
        year_ten_god = BaziParticleNexus.get_shi_shen(year_gan, day_master) if year_gan else ''
        
        # 检查原局是否有特殊格局
        special_pattern = getattr(self.pfa_engine, '_special_pattern_locked', None)
        
        if special_pattern:
            pattern_type = special_pattern.get('type')
            pattern_name = special_pattern.get('name', '')
            
            # 1. 伤官伤尽 → 伤官见官
            if pattern_type == 'shang_guan_shang_jin':
                if year_ten_god in ['正官', '七杀']:
                    state_changes.append({
                        'original': '伤官伤尽',
                        'current': '伤官见官（冲突状态）',
                        'trigger': f"流年[{year_pillar}]透出{year_ten_god}，破坏了伤官伤尽的超稳态结构",
                        'impact': '格局从超稳态退化为冲突状态，用神必须从伤官切换为财星通关'
                    })
            
            # 2. 化气格受阻
            elif pattern_type == 'transformation' and '化' in pattern_name:
                # 检查流年是否克制化气
                stem_elements = {
                    '甲': 'wood', '乙': 'wood',
                    '丙': 'fire', '丁': 'fire',
                    '戊': 'earth', '己': 'earth',
                    '庚': 'metal', '辛': 'metal',
                    '壬': 'water', '癸': 'water'
                }
                year_element = stem_elements.get(year_gan)
                
                # 如果化火格见水
                if '火' in pattern_name and year_element == 'water':
                    state_changes.append({
                        'original': pattern_name,
                        'current': '化火受阻（子格局）',
                        'trigger': f"流年[{year_pillar}]透出水，克制原局化火之引信",
                        'impact': '结构性动荡，原本顺遂的能量流突然发生相位偏移'
                    })
        
        return state_changes
    
    def _identify_final_active_patterns(self, chart: List, luck_pillar: str,
                                       year_pillar: str, geo_element: str,
                                       geo_factor: float, day_master: str,
                                       synthesized_field: Dict,
                                       state_changes: List[Dict]) -> List[Dict]:
        """
        [QGA V24.2] 识别最终激活格局
        优先级：状态变化后的格局 > 特殊格局 > 冲突格局 > 普通格局
        """
        final_patterns = []
        
        # 1. 如果有状态变化，使用变化后的格局（最高优先级）
        if state_changes:
            for change in state_changes:
                final_patterns.append({
                    'name': change['current'],
                    'id': 'state_changed',
                    'type': 'active',
                    'original': change['original'],
                    'state_change': change,
                    'priority': 1,
                    'synthesized_field': synthesized_field
                })
        
        # 2. 特殊格局（如果未被状态变化覆盖）
        special_pattern = getattr(self.pfa_engine, '_special_pattern_locked', None)
        if special_pattern:
            covered = any(
                change.get('original') == special_pattern.get('name', '')
                for change in state_changes
            )
            if not covered:
                final_patterns.append({
                    'name': special_pattern.get('name', ''),
                    'id': special_pattern.get('type', ''),
                    'type': 'primary',
                    'pattern': special_pattern,
                    'priority': 2,
                    'synthesized_field': synthesized_field
                })
        
        # 3. 冲突格局
        prioritized_patterns = getattr(self.pfa_engine, '_prioritized_patterns', {})
        conflict_patterns = prioritized_patterns.get('conflicts', [])
        for cp in conflict_patterns:
            final_patterns.append({
                'name': cp.get('name', ''),
                'id': cp.get('id', ''),
                'type': 'conflict',
                'pattern': cp,
                'priority': 3,
                'synthesized_field': synthesized_field
            })
        
        # 4. 其他激活格局（基于合成场强重新检测）
        detected_patterns = getattr(self.pfa_engine, '_last_detected_patterns', [])
        for pattern in detected_patterns:
            # 跳过已添加的格局
            if any(p.get('id') == pattern.get('id') for p in final_patterns):
                continue
            # 检查在合成场强下是否激活
            if self._check_pattern_active_in_synthesized_field(pattern, synthesized_field, day_master):
                final_patterns.append({
                    'name': pattern.get('name', ''),
                    'id': pattern.get('id', ''),
                    'type': 'normal',
                    'pattern': pattern,
                    'priority': 4,
                    'synthesized_field': synthesized_field
                })
        
        # 按优先级排序
        final_patterns.sort(key=lambda x: x.get('priority', 99))
        
        return final_patterns
    
    def _check_pattern_active_in_synthesized_field(self, pattern: Dict,
                                                   synthesized_field: Dict,
                                                   day_master: str) -> bool:
        """检查格局在合成场强下是否激活"""
        pattern_name = pattern.get('name', '').lower()
        ten_gods = synthesized_field.get('ten_gods', [])
        
        # 检查格局所需的条件是否在合成场强中满足
        if '伤官' in pattern_name:
            if '伤官' in ten_gods:
                return True
        elif '正官' in pattern_name or '七杀' in pattern_name or '官' in pattern_name:
            if '正官' in ten_gods or '七杀' in ten_gods:
                return True
        elif '财' in pattern_name:
            if '正财' in ten_gods or '偏财' in ten_gods:
                return True
        elif '印' in pattern_name:
            if '正印' in ten_gods or '偏印' in ten_gods:
                return True
        
        # 默认：如果原局检测到，合成场强下也激活
        return True
    
    def _parse_pattern_details(self, pattern: Dict, chart: List, luck_pillar: str,
                              year_pillar: str, day_master: str, year: int,
                              pattern_type: str, synthesized_field: Dict = None) -> Dict[str, Any]:
        """
        解析格局的详细信息：击中逻辑、特性、干预策略
        [QGA V24.2] 基于时空耦合的最终状态
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        pattern_name = pattern.get('name', '未知格局')
        pattern_id = pattern.get('id', '')
        match_data = pattern.get('match_data', {})
        state_change = pattern.get('state_change')
        
        # 1. 击中逻辑：基于时空耦合的最终状态
        matching_logic = self._extract_matching_logic(
            pattern, chart, luck_pillar, year_pillar, day_master, synthesized_field, state_change
        )
        
        # 2. 格局特性：物理表现和宏观相
        characteristics = self._extract_pattern_characteristics(
            pattern, match_data, pattern_type, state_change
        )
        
        # 3. 干预策略：针对该格局的解药
        intervention = self._extract_intervention_strategy(
            pattern, day_master, pattern_type, state_change
        )
        
        # 提取sai和stress（可能嵌套在pattern键下）
        nested_pattern = pattern.get('pattern', {})
        sai = pattern.get('sai') or nested_pattern.get('sai') or 0.0
        stress = pattern.get('stress') or nested_pattern.get('stress') or 0.0
        
        # 确保是数值类型
        try:
            sai = float(sai) if sai is not None else 0.0
        except (ValueError, TypeError):
            sai = 0.0
        try:
            stress = float(stress) if stress is not None else 0.0
        except (ValueError, TypeError):
            stress = 0.0
        
        # 如果没有sai值，尝试从match_data中获取
        if sai == 0.0 and match_data:
            sai = match_data.get('sai', 0.0)
            try:
                sai = float(sai) if sai is not None else 0.0
            except (ValueError, TypeError):
                sai = 0.0
        
        return {
            'name': pattern_name,
            'id': pattern_id,
            'type': pattern_type,
            'matching_logic': matching_logic,
            'characteristics': characteristics,
            'intervention': intervention,
            'sai': sai,
            'stress': stress,
            'is_state_changed': state_change is not None
        }
    
    def _extract_matching_logic(self, pattern: Dict, chart: List, luck_pillar: str,
                               year_pillar: str, day_master: str,
                               synthesized_field: Dict = None,
                               state_change: Dict = None) -> str:
        """提取格局的击中逻辑（基于时空耦合）"""
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        parts = []
        
        # [QGA V24.2] 如果有状态变化，优先描述变化
        if state_change:
            parts.append(f"【格局状态变化】")
            parts.append(f"原局格局：{state_change.get('original', '')} → ")
            parts.append(f"当前激活：{state_change.get('current', '')}")
            parts.append(f"\n触发原因：{state_change.get('trigger', '')}")
            return "".join(parts)
        
        # [QGA V24.2] 基于时空耦合的最终状态描述
        if synthesized_field:
            parts.append("【时空耦合状态】")
            coupling_parts = []
            if synthesized_field.get('has_luck'):
                coupling_parts.append(f"大运[{luck_pillar}]")
            if synthesized_field.get('has_year'):
                coupling_parts.append(f"流年[{year_pillar}]")
            if synthesized_field.get('geo_element'):
                coupling_parts.append(f"地理[{synthesized_field['geo_element']}]")
            if coupling_parts:
                parts.append(" + ".join(coupling_parts))
                parts.append(" + 原局八字 → ")
        
        # 检查是否是流年触发的格局
        if year_pillar:
            year_gan = year_pillar[0] if len(year_pillar) > 0 else ''
            year_ten_god = BaziParticleNexus.get_shi_shen(year_gan, day_master) if year_gan else ''
            pattern_name = pattern.get('name', '')
            
            if '伤官' in pattern_name and '见官' in pattern_name:
                parts.append(f"流年[{year_pillar}]透出{year_ten_god}，")
                parts.append(f"与原局伤官形成【{pattern_name}】格局。")
            elif '化' in pattern_name:
                parts.append(f"流年天干[{year_gan}]参与天干五合，")
                parts.append(f"触发【{pattern_name}】格局。")
            elif '拱' in pattern_name:
                year_zhi = year_pillar[1] if len(year_pillar) > 1 else ''
                parts.append(f"流年地支[{year_zhi}]与原局地支构成拱局，")
                parts.append(f"触发【{pattern_name}】格局。")
            else:
                parts.append(f"流年[{year_pillar}]与原局干支相互作用，")
                parts.append(f"在时空耦合状态下触发【{pattern_name}】格局。")
        else:
            parts.append(f"原局格局【{pattern.get('name', '')}】在时空耦合状态下持续生效。")
        
        return "".join(parts)
    
    def _extract_pattern_characteristics(self, pattern: Dict, match_data: Dict,
                                        pattern_type: str, state_change: Dict = None) -> Dict[str, str]:
        """提取格局特性：物理表现和宏观相"""
        pattern_name = pattern.get('name', '')
        sai = pattern.get('sai', 0.0)
        stress = pattern.get('stress', 0.0)
        
        physical_traits = []
        destiny_traits = []
        
        # [QGA V24.2] 如果有状态变化，描述变化后的特性
        if state_change:
            physical_traits.append(state_change.get('impact', '系统状态发生变化'))
            destiny_traits.append("此时格局状态已改变，需要调整应对策略")
        # 根据格局类型生成特性
        elif '伤官' in pattern_name and '尽' in pattern_name:
            physical_traits.append("能量极度聚焦于表达和创造，系统处于超稳态结构")
            destiny_traits.append("此时才华横溢，名誉极高，但易招小人嫉妒")
        elif '伤官' in pattern_name and '见官' in pattern_name:
            physical_traits.append("能量发生相位冲突，系统稳定性下降")
            destiny_traits.append("此时权威与自由产生撕裂，易有官非或职场冲突")
        elif '化' in pattern_name:
            physical_traits.append("系统发生化学变质，能量结构发生偏转")
            destiny_traits.append("此时性格和命运发生转化，人生出现重大转折")
        elif '拱' in pattern_name or '合' in pattern_name:
            physical_traits.append("能量通过空间奇点汇聚，形成局部高能区")
            destiny_traits.append("此时财富或机遇突然出现，但可能伴随突变")
        elif '从财' in pattern_name:
            physical_traits.append("系统完全服从财星，能量流向单一")
            destiny_traits.append("此时财富是人生核心，善于经营和积累")
        elif '羊刃' in pattern_name:
            physical_traits.append("能量极度刚强，系统处于临界状态")
            destiny_traits.append("此时具有极强的领导力和执行力，但易冲动")
        else:
            # 确保sai和stress是数值类型
            try:
                sai_float = float(sai) if sai is not None else 0.0
            except (ValueError, TypeError):
                sai_float = 0.0
            try:
                stress_float = float(stress) if stress is not None else 0.0
            except (ValueError, TypeError):
                stress_float = 0.0
            
            if sai_float > 0.8:
                physical_traits.append("系统能量高度聚焦，结构稳定")
                destiny_traits.append("此时运势极佳，各方面发展顺利")
            elif stress_float > 0.7:
                physical_traits.append("系统承受巨大压力，能量分布不均")
                destiny_traits.append("此时面临重大挑战，需要谨慎应对")
            else:
                physical_traits.append("系统能量分布相对均衡")
                destiny_traits.append("此时运势平稳，无明显波动")
        
        return {
            'physical': " | ".join(physical_traits),
            'destiny': " | ".join(destiny_traits)
        }
    
    def _extract_intervention_strategy(self, pattern: Dict, day_master: str,
                                      pattern_type: str, state_change: Dict = None) -> Dict[str, str]:
        """提取干预策略：针对该格局的解药"""
        pattern_name = pattern.get('name', '')
        yong_shen_rule = pattern.get('yong_shen_rule', '')
        
        # [QGA V24.2] 如果有状态变化，用神必须切换
        if state_change:
            # 例如：伤官伤尽→伤官见官，用神从伤官切换为财星
            if '伤官见官' in state_change.get('current', ''):
                day_master_elements = {
                    '甲': 'wood', '乙': 'wood',
                    '丙': 'fire', '丁': 'fire',
                    '戊': 'earth', '己': 'earth',
                    '庚': 'metal', '辛': 'metal',
                    '壬': 'water', '癸': 'water'
                }
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
                dm_element = day_master_elements.get(day_master, 'earth')
                control_map = {
                    'wood': 'earth', 'fire': 'metal', 'earth': 'water',
                    'metal': 'wood', 'water': 'fire'
                }
                return {
                    'yong_shen': element_cn.get(control_map.get(dm_element, 'earth'), '土'),
                    'spatial': '建议去财星方位，避免官星方位',
                    'behavioral': '通过财富化解冲突，避免直接对抗权威'
                }
        
        # 十神到五行的映射
        day_master_elements = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
        
        intervention_elements = []
        spatial_suggestions = []
        behavioral_suggestions = []
        
        if yong_shen_rule == 'shang_guan_or_wealth':
            dm_element = day_master_elements.get(day_master, 'earth')
            output_map = {
                'wood': 'fire', 'fire': 'earth', 'earth': 'metal',
                'metal': 'water', 'water': 'wood'
            }
            control_map = {
                'wood': 'earth', 'fire': 'metal', 'earth': 'water',
                'metal': 'wood', 'water': 'fire'
            }
            intervention_elements.append(element_cn.get(output_map.get(dm_element, 'fire'), '火'))
            intervention_elements.append(element_cn.get(control_map.get(dm_element, 'earth'), '土'))
            spatial_suggestions.append("建议去南方（火）或中央（土）办公")
            behavioral_suggestions.append("发挥创造力，通过才华变现")
        elif yong_shen_rule == 'wealth':
            dm_element = day_master_elements.get(day_master, 'earth')
            control_map = {
                'wood': 'earth', 'fire': 'metal', 'earth': 'water',
                'metal': 'wood', 'water': 'fire'
            }
            intervention_elements.append(element_cn.get(control_map.get(dm_element, 'earth'), '土'))
            spatial_suggestions.append("建议去财星方位办公")
            behavioral_suggestions.append("专注于经营和财富积累")
        elif '伤官' in pattern_name and '见官' in pattern_name:
            dm_element = day_master_elements.get(day_master, 'earth')
            control_map = {
                'wood': 'earth', 'fire': 'metal', 'earth': 'water',
                'metal': 'wood', 'water': 'fire'
            }
            intervention_elements.append(element_cn.get(control_map.get(dm_element, 'earth'), '土'))
            spatial_suggestions.append("建议去财星方位，避免官星方位")
            behavioral_suggestions.append("通过财富化解冲突，避免直接对抗权威")
        elif '化' in pattern_name:
            spatial_suggestions.append("建议去合化后的元素方位")
            behavioral_suggestions.append("顺应转化，不要抗拒变化")
        else:
            intervention_elements.append("根据用神确定")
            spatial_suggestions.append("根据用神方位调整")
            behavioral_suggestions.append("根据格局特性调整行为")
        
        return {
            'yong_shen': ', '.join(intervention_elements) if intervention_elements else '待定',
            'spatial': ' | '.join(spatial_suggestions) if spatial_suggestions else '无特殊建议',
            'behavioral': ' | '.join(behavioral_suggestions) if behavioral_suggestions else '无特殊建议'
        }

