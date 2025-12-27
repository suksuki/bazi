"""
八字档案审计核心引擎
实现PFA、SOA、MCA三个核心算法
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from core.bazi_profile import BaziProfile
from core.engine_graph import GraphNetworkEngine
from core.trinity.core.engines.pattern_scout import PatternScout
from core.logic_registry import LogicRegistry
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

logger = logging.getLogger(__name__)


@dataclass
class PatternFrictionResult:
    """格局冲突分析结果"""
    friction_index: float  # 0-100，越高表示冲突越大
    conflicting_patterns: List[str]  # 冲突的格局列表
    coherence_level: str  # "高" / "中" / "低"
    semantic_interpretation: str  # 语义解释
    detected_patterns: List[Dict] = None  # 检测到的所有格局（用于详细分析）


@dataclass
class OptimizationResult:
    """变分寻优结果"""
    optimal_elements: Dict[str, float]  # 最优五行注入量
    stability_score: float  # 稳定性分数
    entropy_reduction: float  # 熵值降低
    semantic_interpretation: str  # 语义解释


@dataclass
class MediumCompensationResult:
    """介质修正结果"""
    geo_correction: Dict[str, float]  # 地理修正系数
    micro_env_correction: Dict[str, float]  # 微环境修正系数
    total_correction: Dict[str, float]  # 总修正系数
    semantic_interpretation: str  # 语义解释


class PatternFrictionAnalysisEngine:
    """
    [P.F.A] 格局冲突映射引擎
    检测命局中不同格局吸引子的"相位干扰"
    遍历物理模型仿真主题下所有注册的格局专题
    """
    
    def __init__(self):
        self.registry = LogicRegistry()
        self.scout = PatternScout()
        
        # 格局冲突规则表
        self.conflict_rules = {
            # 化气格见伤官 -> 相干性降低
            ("化气格", "伤官"): 0.6,
            # 从格见比劫 -> 纯度下降
            ("从格", "比劫"): 0.5,
            # 专旺见财星 -> 格局破坏
            ("专旺", "财星"): 0.4,
            # 正官格见伤官 -> 冲突
            ("正官格", "伤官"): 0.7,
        }
        
        # 预加载所有PATTERN_PHYSICS主题下的格局
        self._load_pattern_physics_topics()
    
    def _load_pattern_physics_topics(self):
        """加载物理模型仿真主题下的所有格局专题"""
        self.pattern_physics_topics = self.registry.get_active_modules(theme_id="PATTERN_PHYSICS")
        logger.info(f"加载了 {len(self.pattern_physics_topics)} 个物理模型仿真格局专题")
    
    def analyze(self, bazi_profile: BaziProfile, year: int = None, 
                geo_element: str = None, geo_factor: float = 1.0) -> PatternFrictionResult:
        """
        分析格局冲突
        
        Args:
            bazi_profile: 八字档案对象
            year: 流年（可选）
            geo_element: 地理五行属性（可选）
            geo_factor: 地理因子（可选）
            
        Returns:
            格局冲突分析结果
        """
        # 1. 获取所有格局
        pillars = bazi_profile.pillars
        chart = [
            (pillars['year'][0], pillars['year'][1]),
            (pillars['month'][0], pillars['month'][1]),
            (pillars['day'][0], pillars['day'][1]),
            (pillars['hour'][0], pillars['hour'][1])
        ]
        
        # 2. 获取大运和流年（用于格局探测）
        luck_pillar = bazi_profile.get_luck_pillar_at(year) if year else None
        year_pillar = bazi_profile.get_year_pillar(year) if year else None
        
        # 构建geo_context用于格局探测（总线注入方式）
        geo_context = {}
        if luck_pillar:
            geo_context['luck_pillar'] = luck_pillar
        if year_pillar:
            geo_context['annual_pillar'] = year_pillar
        if geo_element:
            geo_context['element'] = geo_element
        if geo_factor != 1.0:
            geo_context['factor'] = geo_factor
        
        # 3. 遍历所有PATTERN_PHYSICS主题下的格局专题
        detected_patterns = []
        
        logger.info(f"开始遍历 {len(self.pattern_physics_topics)} 个格局专题进行冲突分析...")
        
        for topic in self.pattern_physics_topics:
            topic_id = topic.get('id', '')
            topic_name = topic.get('name_cn') or topic.get('name', topic_id)
            
            # 只处理active的格局
            if not topic.get('active', True):
                continue
            
            try:
                # 解析逻辑ID
                registry_id, logic_ids = self.registry.resolve_logic_id(topic_id)
                
                # 对每个逻辑ID进行探测
                for logic_id in logic_ids:
                    match = self.scout._deep_audit(chart, logic_id, geo_context=geo_context)
                    if match:
                        detected_patterns.append({
                            'id': topic_id,
                            'logic_id': logic_id,
                            'name': topic_name,
                            'category': match.get('category', ''),
                            'stress': match.get('stress', 0.0),
                            'sai': match.get('sai', 0.0),
                            'match_data': match
                        })
                        logger.debug(f"检测到格局: {topic_name} ({topic_id})")
                        # 找到一个匹配就跳出（避免重复）
                        break
            except Exception as e:
                logger.debug(f"探测格局 {topic_id} 失败: {e}")
                continue
        
        # 保存检测到的格局（用于调试和后续分析）
        self._last_detected_patterns = detected_patterns
        logger.info(f"共检测到 {len(detected_patterns)} 个格局")
        
        # 3. 计算冲突指数
        friction_index = 0.0
        conflicting_pairs = []
        
        # 检查格局之间的冲突
        for i, p1 in enumerate(detected_patterns):
            for j, p2 in enumerate(detected_patterns[i+1:], i+1):
                conflict_score = self._check_pattern_conflict(p1, p2, chart, bazi_profile.day_master)
                if conflict_score > 0.3:
                    friction_index += conflict_score
                    conflicting_pairs.append(f"{p1['name']} vs {p2['name']}")
        
        # 归一化到0-100
        friction_index = min(100.0, friction_index * 20.0)
        
        # 4. 确定相干性等级
        if friction_index < 30:
            coherence_level = "高"
        elif friction_index < 60:
            coherence_level = "中"
        else:
            coherence_level = "低"
        
        # 5. 生成语义解释
        semantic = self._generate_friction_semantic(friction_index, conflicting_pairs, coherence_level)
        
        return PatternFrictionResult(
            friction_index=friction_index,
            conflicting_patterns=conflicting_pairs,
            coherence_level=coherence_level,
            semantic_interpretation=semantic,
            detected_patterns=detected_patterns
        )
    
    def get_detected_patterns(self) -> List[Dict]:
        """获取最近一次分析中检测到的所有格局（用于调试）"""
        return getattr(self, '_last_detected_patterns', [])
    
    def _check_pattern_conflict(self, p1: Dict, p2: Dict, chart: List, day_master: str) -> float:
        """检查两个格局之间的冲突程度"""
        # 简化版冲突检测
        conflict_score = 0.0
        
        # 检查十神冲突
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        stems = [p[0] for p in chart]
        ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
        
        # 如果格局1需要某种十神，而格局2破坏它
        if "伤官" in ten_gods and "正官" in ten_gods:
            conflict_score += 0.5
        
        return conflict_score
    
    def _generate_friction_semantic(self, friction: float, conflicts: List[str], coherence: str) -> str:
        """生成语义解释"""
        if friction < 30:
            return "格局体系高度协调，各格局力量相互支撑，形成稳定的能量场。"
        elif friction < 60:
            if conflicts:
                return f"命局中存在一定的格局冲突（{', '.join(conflicts[:2])}），导致理想与现实之间存在张力，需要调和。"
            else:
                return "格局体系基本协调，但存在微妙的相位干扰，需要关注内在平衡。"
        else:
            if conflicts:
                return f"命局中存在严重的格局冲突（{', '.join(conflicts[:2])}），导致性格中的自我拆台，理想与现实的撕裂感强烈，需要寻找平衡点。"
            else:
                return "格局体系存在显著冲突，能量场不稳定，需要外部干预来调和矛盾。"


class SystemOptimizationEngine:
    """
    [S.O.A] 变分寻优算法引擎
    在后台模拟注入金木水火土5种因子，寻找能让系统"熵值"最小、稳定性最高的组合
    """
    
    def __init__(self):
        self.step_size = 0.05
        self.elements = ['metal', 'wood', 'water', 'fire', 'earth']
        self.element_cn = {
            'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'
        }
    
    def optimize(self, bazi_profile: BaziProfile, year: int = None,
                 geo_element: str = None, geo_factor: float = 1.0) -> OptimizationResult:
        """
        变分寻优
        
        Args:
            bazi_profile: 八字档案对象
            year: 流年（可选）
            geo_element: 地理五行属性（可选）
            geo_factor: 地理因子（可选）
            
        Returns:
            优化结果
        """
        # 1. 初始化引擎
        from core.engine_graph import GraphNetworkEngine
        engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        
        # 2. 获取基础八字
        pillars = bazi_profile.pillars
        bazi = [
            pillars['year'],
            pillars['month'],
            pillars['day'],
            pillars['hour']
        ]
        
        # 3. 获取大运和流年
        luck_pillar = bazi_profile.get_luck_pillar_at(year) if year else None
        year_pillar = bazi_profile.get_year_pillar(year) if year else None
        
        # 4. 初始化节点（基准状态，包含地理修正）
        baseline_geo_modifiers = {}
        if geo_element:
            element_map = {
                'metal': 'metal', 'wood': 'wood', 'water': 'water',
                'fire': 'fire', 'earth': 'earth'
            }
            if geo_element in element_map:
                baseline_geo_modifiers[element_map[geo_element]] = geo_factor - 1.0
        
        engine.initialize_nodes(
            bazi, bazi_profile.day_master,
            luck_pillar, year_pillar,
            geo_modifiers=baseline_geo_modifiers if baseline_geo_modifiers else None
        )
        engine.build_adjacency_matrix()
        engine.propagate()
        
        baseline_entropy = self._calculate_entropy(engine)
        baseline_stability = self._calculate_stability(engine)
        
        # 5. 变分搜索
        best_result = None
        best_score = float('inf')
        
        # 简化版：只搜索单一元素注入
        for element in self.elements:
            for injection_amount in np.arange(0.0, 1.0, self.step_size):
                # 创建修正后的引擎（在基准地理修正基础上叠加）
                test_engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
                test_geo_modifiers = baseline_geo_modifiers.copy()
                test_geo_modifiers[element] = test_geo_modifiers.get(element, 0.0) + injection_amount
                
                test_engine.initialize_nodes(
                    bazi, bazi_profile.day_master,
                    luck_pillar, year_pillar,
                    geo_modifiers=test_geo_modifiers if test_geo_modifiers else None
                )
                test_engine.build_adjacency_matrix()
                test_engine.propagate()
                
                entropy = self._calculate_entropy(test_engine)
                stability = self._calculate_stability(test_engine)
                
                # 综合评分：熵值越低、稳定性越高越好
                score = entropy - stability * 10.0
                
                if score < best_score:
                    best_score = score
                    best_result = {
                        'element': element,
                        'amount': injection_amount,
                        'entropy': entropy,
                        'stability': stability,
                        'entropy_reduction': baseline_entropy - entropy
                    }
        
        # 6. 生成最优组合（简化版：只返回最佳单一元素）
        optimal_elements = {}
        if best_result:
            optimal_elements[best_result['element']] = best_result['amount']
        
        # 7. 生成语义解释
        semantic = self._generate_optimization_semantic(best_result, baseline_entropy, baseline_stability)
        
        return OptimizationResult(
            optimal_elements=optimal_elements,
            stability_score=best_result['stability'] if best_result else baseline_stability,
            entropy_reduction=best_result['entropy_reduction'] if best_result else 0.0,
            semantic_interpretation=semantic
        )
    
    def _calculate_entropy(self, engine: GraphNetworkEngine) -> float:
        """计算系统熵值"""
        energies = []
        if not engine.nodes:
            return 1.0
        
        # 检查第一个节点的能量类型
        first_node_energy = engine.nodes[0].current_energy
        is_probvalue = hasattr(first_node_energy, 'mean')
        
        for node in engine.nodes:
            if is_probvalue:
                # ProbValue类型
                energies.append(node.current_energy.mean)
            else:
                energies.append(float(node.current_energy))
        
        if not energies:
            return 1.0
        
        # 归一化
        total = sum(energies)
        if total == 0:
            return 1.0
        
        probs = [e / total for e in energies]
        # 计算信息熵
        entropy = -sum(p * np.log2(p + 1e-10) for p in probs if p > 0)
        return entropy
    
    def _calculate_stability(self, engine: GraphNetworkEngine) -> float:
        """计算系统稳定性"""
        # 简化版：基于能量分布的方差
        energies = []
        if not engine.nodes:
            return 0.0
        
        # 检查第一个节点的能量类型
        first_node_energy = engine.nodes[0].current_energy
        is_probvalue = hasattr(first_node_energy, 'mean')
        
        for node in engine.nodes:
            if is_probvalue:
                energies.append(node.current_energy.mean)
            else:
                energies.append(float(node.current_energy))
        
        if not energies:
            return 0.0
        
        # 稳定性 = 1 / (1 + 方差)
        variance = np.var(energies)
        stability = 1.0 / (1.0 + variance)
        return stability
    
    def _generate_optimization_semantic(self, best_result: Dict, baseline_entropy: float, 
                                       baseline_stability: float) -> str:
        """生成优化语义解释"""
        if not best_result:
            return "当前系统已达到较优状态，无需大幅调整。"
        
        element_cn = self.element_cn.get(best_result['element'], best_result['element'])
        reduction = best_result['entropy_reduction']
        
        if reduction > 0.1:
            return f"系统通过注入{element_cn}元素（强度{best_result['amount']:.2f}）能够显著降低内耗，提升稳定性。这是最能平息内耗、开启财富的钥匙。"
        elif reduction > 0.05:
            return f"系统通过适度注入{element_cn}元素能够改善能量分布，减少内部冲突。"
        else:
            return "当前系统状态较为平衡，小幅调整即可维持稳定。"


class MediumCompensationEngine:
    """
    [M.C.A] 介质修正模型引擎
    将地理（宏观）和居家环境（微观）定义为"场强修正系数"
    """
    
    def __init__(self):
        # 城市五行属性映射（参考量子真言页面的GEO_CITY_MAP）
        # 格式: "城市名": (geo_factor, "element_affinity")
        # 这里提取主要元素（取第一个）
        self.city_elements = {
            # 中国直辖市/一线城市
            '北京': 'fire', '上海': 'water', '深圳': 'fire', '广州': 'fire',
            '天津': 'water', '重庆': 'water',
            # 省会城市
            '石家庄': 'earth', '太原': 'metal', '呼和浩特': 'metal',
            '沈阳': 'water', '长春': 'water', '哈尔滨': 'water',
            '南京': 'fire', '杭州': 'water', '合肥': 'earth', '福州': 'water',
            '南昌': 'fire', '济南': 'water', '郑州': 'earth', '武汉': 'water',
            '长沙': 'fire', '南宁': 'wood', '海口': 'water', '成都': 'earth',
            '贵阳': 'wood', '昆明': 'wood', '拉萨': 'metal', '西安': 'metal',
            '兰州': 'metal', '西宁': 'water', '银川': 'metal', '乌鲁木齐': 'metal',
            # 其他重要城市
            '苏州': 'water', '无锡': 'water', '宁波': 'water', '青岛': 'water',
            '大连': 'water', '厦门': 'water', '珠海': 'water', '东莞': 'fire',
            '佛山': 'fire',
            # 港澳台
            '香港': 'water', '澳门': 'water', '台北': 'water', '高雄': 'fire',
            # 亚洲城市
            '东京': 'water', '大阪': 'water', '首尔': 'metal', '新加坡': 'fire',
            '吉隆坡': 'fire', '曼谷': 'fire', '马尼拉': 'fire', '雅加达': 'fire',
            '河内': 'water', '胡志明市': 'fire', '孟买': 'fire', '新德里': 'fire',
            '迪拜': 'fire',
            # 欧洲城市
            '伦敦': 'water', '巴黎': 'metal', '柏林': 'metal', '法兰克福': 'metal',
            '阿姆斯特丹': 'water', '苏黎世': 'metal', '米兰': 'fire', '莫斯科': 'water',
            # 北美城市
            '纽约': 'metal', '洛杉矶': 'fire', '旧金山': 'water', '西雅图': 'water',
            '芝加哥': 'metal', '多伦多': 'water', '温哥华': 'water',
            # 大洋洲城市
            '悉尼': 'fire', '墨尔本': 'water', '奥克兰': 'water',
        }
        
        # 微环境修正系数
        self.micro_env_factors = {
            '近水': {'water': 1.15, 'fire': 0.85, 'earth': 0.95, 'wood': 1.05, 'metal': 1.0},
            '近山': {'earth': 1.15, 'wood': 1.10, 'fire': 0.90, 'water': 0.95, 'metal': 1.05},
            '高层': {'fire': 1.10, 'metal': 1.05, 'earth': 0.95, 'water': 0.90, 'wood': 1.0},
            '低层': {'earth': 1.10, 'water': 1.05, 'wood': 1.0, 'fire': 0.95, 'metal': 0.95},
        }
    
    def compensate(self, bazi_profile: BaziProfile, city: str = None,
                   micro_env: List[str] = None) -> MediumCompensationResult:
        """
        介质修正
        
        Args:
            bazi_profile: 八字档案对象
            city: 城市名称
            micro_env: 微环境列表（如['近水', '高层']）
            
        Returns:
            修正结果
        """
        # 1. 地理修正
        geo_correction = {'metal': 1.0, 'wood': 1.0, 'water': 1.0, 'fire': 1.0, 'earth': 1.0}
        
        if city:
            city_element = self.city_elements.get(city, 'neutral')
            if city_element != 'neutral':
                # 同属性增强，相生增强，相克减弱
                geo_correction[city_element] = 1.15
                # 相生关系
                generation_map = {
                    'wood': 'fire', 'fire': 'earth', 'earth': 'metal',
                    'metal': 'water', 'water': 'wood'
                }
                if city_element in generation_map:
                    geo_correction[generation_map[city_element]] = 1.10
                # 相克关系
                control_map = {
                    'wood': 'earth', 'earth': 'water', 'water': 'fire',
                    'fire': 'metal', 'metal': 'wood'
                }
                if city_element in control_map:
                    geo_correction[control_map[city_element]] = 0.90
        
        # 2. 微环境修正
        micro_correction = {'metal': 1.0, 'wood': 1.0, 'water': 1.0, 'fire': 1.0, 'earth': 1.0}
        
        if micro_env:
            for env in micro_env:
                if env in self.micro_env_factors:
                    factors = self.micro_env_factors[env]
                    for element, factor in factors.items():
                        micro_correction[element] *= factor
        
        # 3. 总修正（取平均值）
        total_correction = {}
        for element in ['metal', 'wood', 'water', 'fire', 'earth']:
            total_correction[element] = (geo_correction[element] + micro_correction[element]) / 2.0
        
        # 4. 生成语义解释
        semantic = self._generate_compensation_semantic(city, micro_env, geo_correction, micro_correction)
        
        return MediumCompensationResult(
            geo_correction=geo_correction,
            micro_env_correction=micro_correction,
            total_correction=total_correction,
            semantic_interpretation=semantic
        )
    
    def _generate_compensation_semantic(self, city: str, micro_env: List[str],
                                      geo_correction: Dict, micro_correction: Dict) -> str:
        """生成修正语义解释"""
        parts = []
        
        if city:
            city_element = self.city_elements.get(city, 'neutral')
            if city_element != 'neutral':
                element_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}.get(city_element, '')
                if geo_correction.get(city_element, 1.0) > 1.1:
                    parts.append(f"当前城市（{city}）的{element_cn}属性补强了命局，形成有利的能量场。")
                elif geo_correction.get(city_element, 1.0) < 0.95:
                    parts.append(f"当前城市（{city}）的环境属性与命局存在一定冲突，可能激化内在矛盾。")
        
        if micro_env:
            env_desc = []
            for env in micro_env:
                if env == '近水':
                    if micro_correction.get('water', 1.0) > 1.1:
                        env_desc.append("近水环境增强了水元素")
                    elif micro_correction.get('fire', 1.0) < 0.9:
                        env_desc.append("近水环境抑制了火元素")
                elif env == '近山':
                    if micro_correction.get('earth', 1.0) > 1.1:
                        env_desc.append("近山环境增强了土元素")
                elif env == '高层':
                    if micro_correction.get('fire', 1.0) > 1.05:
                        env_desc.append("高层环境增强了火元素")
                elif env == '低层':
                    if micro_correction.get('earth', 1.0) > 1.05:
                        env_desc.append("低层环境增强了土元素")
            
            if env_desc:
                parts.append(f"微环境（{', '.join(micro_env)}）的影响：{', '.join(env_desc)}。")
        
        if not parts:
            return "当前环境对命局影响中性，无明显补强或削弱。"
        
        return " ".join(parts)

