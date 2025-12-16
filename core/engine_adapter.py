"""
Engine Adapter - Graph Network Engine Integration Adapter
==========================================================

适配器模块，用于将图网络引擎的输出转换为现有UI格式，实现无缝集成。
"""

from typing import Dict, List, Any, Optional
from core.engine_graph import GraphNetworkEngine
from core.engine_v88 import EngineV88 as EngineV91  # Alias for compatibility
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


class GraphEngineAdapter:
    """
    图网络引擎适配器。
    
    将 GraphNetworkEngine 的输出转换为与 EngineV91 兼容的格式。
    """
    
    VERSION = "10.0-Graph-Adapter"
    
    def __init__(self, config: Dict = None):
        """
        初始化适配器。
        
        Args:
            config: 参数配置（使用 DEFAULT_FULL_ALGO_PARAMS 结构）
        """
        self.config = config or DEFAULT_FULL_ALGO_PARAMS
        self.graph_engine = GraphNetworkEngine(config=self.config)
    
    def calculate_energy(self, case_data: Dict, dynamic_context: Dict = None) -> Dict:
        """
        使用图网络引擎计算能量，并转换为标准格式。
        
        Args:
            case_data: 案例数据字典（包含 bazi, day_master 等）
            dynamic_context: 动态上下文（year, luck 等）
        
        Returns:
            与 EngineV91.calculate_energy() 兼容的结果字典
        """
        # 提取数据
        bazi = case_data.get('bazi', [])
        day_master = case_data.get('day_master', '甲')
        
        # 提取大运和流年
        luck_pillar = None
        year_pillar = None
        
        if dynamic_context:
            luck_pillar = dynamic_context.get('luck') or dynamic_context.get('dayun')
            year_pillar = dynamic_context.get('year')
        
        # 地理修正（如果有）
        geo_modifiers = None
        if 'city' in case_data:
            # 这里可以调用 GeoProcessor 获取修正系数
            pass
        
        # 调用图网络引擎
        graph_result = self.graph_engine.analyze(
            bazi=bazi,
            day_master=day_master,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            geo_modifiers=geo_modifiers
        )
        
        # 转换为标准格式
        return self._convert_to_standard_format(graph_result, case_data)
    
    def _convert_to_standard_format(self, graph_result: Dict, case_data: Dict) -> Dict:
        """
        将图网络引擎的结果转换为标准格式。
        
        Args:
            graph_result: 图网络引擎的原始输出
            case_data: 原始案例数据
        
        Returns:
            标准格式的结果字典
        """
        # 聚合元素能量
        element_energy = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 
                         'metal': 0.0, 'water': 0.0}
        
        nodes = graph_result.get('nodes', [])
        final_energy = graph_result.get('final_energy', [])
        
        for i, node in enumerate(nodes):
            if i < len(final_energy):
                element = node.get('element', 'earth')
                element_energy[element] = element_energy.get(element, 0.0) + final_energy[i]
        
        # 计算旺衰（使用标准化的占比法）
        dm_char = case_data.get('day_master', '甲')
        dm_element_map = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        dm_element = dm_element_map.get(dm_char, 'wood')
        
        # 优先使用引擎返回的标准化分数
        if 'strength_score' in graph_result:
            strength_score = graph_result['strength_score']
            strength = graph_result.get('strength_label', 'Balanced')
        else:
            # Fallback: 使用占比法计算（兼容旧版本）
            from core.processors.physics import GENERATION
            dm_element = dm_element_map.get(dm_char, 'wood')
            
            # 确定资源元素（生我的元素）
            resource_element = None
            for elem, target in GENERATION.items():
                if target == dm_element:
                    resource_element = elem
                    break
            
            # 计算日主阵营能量和全盘总能量
            self_team_energy = 0.0
            total_energy = 0.0
            
            for i, node in enumerate(nodes):
                if i >= len(final_energy):
                    continue
                node_energy = float(final_energy[i])
                total_energy += node_energy
                
                node_element = node.get('element', '')
                if node_element == dm_element:  # Self 或 Peer
                    self_team_energy += node_energy
                elif resource_element and node_element == resource_element:  # Resource
                    self_team_energy += node_energy
            
            # 计算占比分数
            if total_energy > 0:
                strength_score = (self_team_energy / total_energy) * 100.0
            else:
                strength_score = 0.0
            
            # 判断身强身弱
            if strength_score >= 60.0:
                strength = "Strong"
            elif strength_score >= 40.0:
                strength = "Balanced"
            else:
                strength = "Weak"
        
        # 获取宏观得分
        domain_scores = graph_result.get('domain_scores', {})
        
        # 计算十神强度（根据五行能量）
        # 日主元素索引
        elements = ['wood', 'fire', 'earth', 'metal', 'water']
        dm_idx = elements.index(dm_element) if dm_element in elements else 0
        
        # 计算相对位置的元素能量
        self_idx = dm_idx
        output_idx = (dm_idx + 1) % 5
        wealth_idx = (dm_idx + 2) % 5
        officer_idx = (dm_idx + 3) % 5
        resource_idx = (dm_idx + 4) % 5
        
        # 获取各元素能量
        self_energy = element_energy.get(elements[self_idx], 0.0)
        output_energy = element_energy.get(elements[output_idx], 0.0)
        wealth_energy = element_energy.get(elements[wealth_idx], 0.0)
        officer_energy = element_energy.get(elements[officer_idx], 0.0)
        resource_energy = element_energy.get(elements[resource_idx], 0.0)
        
        # 构建十神强度字典（简化：不使用粒子权重，直接使用能量）
        gods_strength = {
            'self': self_energy,
            'output': output_energy,
            'wealth': wealth_energy,
            'officer': officer_energy,
            'resource': resource_energy
        }
        
        # 构建 domain_details 格式（与 EngineV91 兼容）
        domain_details = {
            'career': {
                'score': domain_scores.get('career', 0.0)
            },
            'wealth': {
                'score': domain_scores.get('wealth', 0.0)
            },
            'relationship': {
                'score': domain_scores.get('relationship', 0.0)
            },
            'gods_strength': gods_strength
        }
        
        # 构建标准格式结果
        result = {
            'wang_shuai': strength,
            'wang_shuai_score': strength_score,
            'dm_element': dm_element,
            'favorable': [],  # TODO: 根据能量分布计算喜用神
            'raw_energy': element_energy,
            'energy_map': element_energy,  # 兼容字段
            'career': domain_scores.get('career', 0.0) / 10.0,  # 归一化到 0-10
            'wealth': domain_scores.get('wealth', 0.0) / 10.0,
            'relationship': domain_scores.get('relationship', 0.0) / 10.0,
            'domain_details': domain_details,  # 包含 gods_strength
            
            # 十神能量（直接从 gods_strength 获取）
            'e_self': gods_strength['self'],
            'e_output': gods_strength['output'],
            'e_wealth': gods_strength['wealth'],
            'e_officer': gods_strength['officer'],
            'e_resource': gods_strength['resource'],
            
            # 柱能量（简化：构造8个值的列表）
            'pillar_energies': self._construct_pillar_energies(nodes, final_energy),
            
            # 描述
            'desc': f'{case_data.get("day_master", "甲")}日主 {strength}',
            
            # 图网络特有数据（用于可视化）
            'graph_data': {
                'initial_energy': graph_result.get('initial_energy', []),
                'final_energy': graph_result.get('final_energy', []),
                'adjacency_matrix': graph_result.get('adjacency_matrix', []),
                'nodes': graph_result.get('nodes', [])
            }
        }
        
        return result
    
    def _construct_pillar_energies(self, nodes: List[Dict], final_energy: List[float]) -> List[float]:
        """
        构造柱能量列表（8个值：YearStem, YearBranch, MonthStem, MonthBranch, ...）
        
        Args:
            nodes: 节点列表
            final_energy: 最终能量列表
        
        Returns:
            8个能量值的列表
        """
        pillar_energies = [0.0] * 8
        pillar_order = ['year', 'month', 'day', 'hour']
        
        for i, node in enumerate(nodes):
            if i >= len(final_energy):
                continue
            
            pillar_name = node.get('pillar_name')
            node_type = node.get('node_type')
            
            if pillar_name in pillar_order:
                pillar_idx = pillar_order.index(pillar_name)
                offset = 1 if node_type == 'branch' else 0
                energy_idx = pillar_idx * 2 + offset
                
                if energy_idx < 8:
                    pillar_energies[energy_idx] = final_energy[i]
        
        return pillar_energies
    
    # === Legacy Compatibility Methods ===
    # 为了与现有代码兼容，添加这些方法
    
    def update_config(self, config: Dict) -> None:
        """更新配置（兼容方法）"""
        self.config = config
        if hasattr(self.graph_engine, 'config'):
            self.graph_engine.config = config
    
    def update_full_config(self, config: Dict) -> None:
        """更新完整配置（兼容方法）"""
        self.config = config
        if hasattr(self.graph_engine, 'config'):
            self.graph_engine.config = config
    
    def _evaluate_wang_shuai(self, day_master: str, bazi: List[str]) -> tuple:
        """
        评估旺衰（兼容方法）。
        
        Returns:
            (strength_str, score) tuple
        """
        case_data = {
            'day_master': day_master,
            'bazi': bazi,
        }
        result = self.calculate_energy(case_data)
        
        strength = result.get('wang_shuai', 'Unknown')
        score = result.get('wang_shuai_score', 0.0)
        
        return (strength, score)
    
    def calculate_year_context(self, profile, year: int):
        """
        计算流年上下文（兼容方法）。
        
        注意：图网络引擎的接口不同，这里需要适配。
        如果 profile 是 VirtualBaziProfile，提取信息后调用 analyze。
        """
        # 提取八字信息
        bazi = [
            profile.pillars.get('year', '甲子'),
            profile.pillars.get('month', '甲子'),
            profile.pillars.get('day', '甲子'),
            profile.pillars.get('hour', '甲子'),
        ]
        day_master = profile.day_master
        
        # 获取大运和流年
        luck_pillar = getattr(profile, 'static_luck', None)
        # 计算流年干支（使用 get_year_pillar，以便可以被动态替换）
        year_pillar = self.get_year_pillar(year)
        
        # 调用图网络引擎
        graph_result = self.graph_engine.analyze(
            bazi=bazi,
            day_master=day_master,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        # 转换为 DestinyContext 格式（简化实现）
        from core.context import DestinyContext
        
        # 提取结果
        domain_scores = graph_result.get('domain_scores', {})
        
        # 计算流年干支
        year_pillar_str = self.get_year_pillar(year)
        
        # 计算日主强度（从图网络结果中提取）
        # 简化：使用 domain_scores 中的 strength 或默认值
        strength = graph_result.get('strength', 'Medium')
        if isinstance(strength, str):
            # 标准化强度值
            if 'Strong' in strength:
                day_master_strength = 'Strong'
            elif 'Weak' in strength:
                day_master_strength = 'Weak'
            else:
                day_master_strength = 'Medium'
        else:
            day_master_strength = 'Medium'
        
        # 计算综合分数（使用财富得分作为基础）
        career_score = domain_scores.get('career', 0.0)
        wealth_score = domain_scores.get('wealth', 0.0)
        relationship_score = domain_scores.get('relationship', 0.0)
        composite_score = (career_score + wealth_score + relationship_score) / 3.0
        
        # 构建上下文
        ctx = DestinyContext(
            year=year,
            pillar=year_pillar_str,
            luck_pillar=luck_pillar,
            score=composite_score,
            raw_score=composite_score,
            energy_level="Neutral",  # 可以根据 score 计算
            day_master_strength=day_master_strength,
            career=career_score / 10.0,  # 归一化
            wealth=wealth_score / 10.0,
            relationship=relationship_score / 10.0,
            description="图网络引擎计算结果",
            version="10.0-Graph"
        )
        
        # 自动构建 narrative prompt
        ctx.narrative_prompt = ctx.build_narrative_prompt()
        ctx.energy_level = ctx.get_energy_category()
        
        return ctx
    
    def _get_year_pillar(self, year: int) -> str:
        """获取流年干支（简化实现）"""
        try:
            from lunar_python import Solar
            solar = Solar.fromYmd(year, 6, 15)  # 使用年中日期
            lunar = solar.getLunar()
            return lunar.getYearInGanZhiExact()
        except:
            # 如果失败，使用简化计算
            gan_list = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            gan_idx = (year - 4) % 10
            zhi_idx = (year - 4) % 12
            return f"{gan_list[gan_idx]}{zhi_list[zhi_idx]}"
    
    def get_year_pillar(self, year: int) -> str:
        """获取流年干支（兼容方法）"""
        return self._get_year_pillar(year)

