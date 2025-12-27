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
        
        # [QGA V24.0] 模式优先驱动：先捕获典型局（特殊格局）
        special_pattern = self._capture_special_patterns(detected_patterns, chart, bazi_profile)
        
        # 初始化prioritized_patterns（确保在所有分支中都有定义）
        prioritized_patterns = {}
        
        # 如果捕获到特殊格局，逻辑锁死
        if special_pattern:
            logger.info(f"🔒 检测到特殊格局: {special_pattern['name']}，逻辑已锁死")
            self._special_pattern_locked = special_pattern
            # 特殊格局下，冲突指数设为0（因为格局本身是超稳态结构）
            friction_index = 0.0
            conflicting_pairs = []
            coherence_level = "超稳态"
            # 即使有特殊格局，也建立优先级结构（用于后续分析）
            prioritized_patterns = {
                'primary': {
                    'name': special_pattern['name'],
                    'type': special_pattern['type'],
                    'pattern': special_pattern
                },
                'conflicts': [],
                'singularities': []
            }
        else:
            # [QGA V23.5] 格局优先级架构：建立层次结构
            prioritized_patterns = self._prioritize_patterns(detected_patterns, chart, bazi_profile)
            self._special_pattern_locked = None
            logger.info(f"共检测到 {len(detected_patterns)} 个格局，主格局: {prioritized_patterns.get('primary', {}).get('name', '无')}")
        
        # 保存格局信息（用于后续分析）
        self._prioritized_patterns = prioritized_patterns
        self._last_detected_patterns = detected_patterns
        
        # 3. 计算冲突指数（基于优先级权重）
        friction_index = 0.0
        conflicting_pairs = []
        
        primary_pattern = prioritized_patterns.get('primary')
        conflict_patterns = prioritized_patterns.get('conflicts', [])
        
        # [QGA V23.5] 如果存在相位冲突格局，这是最大应力点
        if conflict_patterns:
            for cp in conflict_patterns:
                if primary_pattern:
                    # 主格局与冲突格局的冲突（权重60%）
                    conflict_score = self._check_pattern_conflict(primary_pattern, cp, chart, bazi_profile.day_master)
                    if conflict_score > 0.3:
                        friction_index += conflict_score * 0.6
                        conflicting_pairs.append(f"{primary_pattern['name']} vs {cp['name']}")
                
                # 冲突格局之间的冲突（权重20%）
                for cp2 in conflict_patterns:
                    if cp['id'] != cp2['id']:
                        conflict_score = self._check_pattern_conflict(cp, cp2, chart, bazi_profile.day_master)
                        if conflict_score > 0.3:
                            friction_index += conflict_score * 0.2
                            if f"{cp['name']} vs {cp2['name']}" not in conflicting_pairs:
                                conflicting_pairs.append(f"{cp['name']} vs {cp2['name']}")
        else:
            # 传统冲突检测（降权到10%）
            for i, p1 in enumerate(detected_patterns):
                for j, p2 in enumerate(detected_patterns[i+1:], i+1):
                    conflict_score = self._check_pattern_conflict(p1, p2, chart, bazi_profile.day_master)
                    if conflict_score > 0.3:
                        friction_index += conflict_score * 0.1
                        conflicting_pairs.append(f"{p1['name']} vs {p2['name']}")
        
        # 归一化到0-100（特殊格局已锁死，跳过此步骤）
        if not special_pattern:
            friction_index = min(100.0, friction_index * 20.0)
            
            # 4. 确定相干性等级
            if friction_index < 30:
                coherence_level = "高"
            elif friction_index < 60:
                coherence_level = "中"
            else:
                coherence_level = "低"
        else:
            # 特殊格局：超稳态结构
            coherence_level = "超稳态"
        
        # 5. 生成语义解释
        if special_pattern:
            semantic = self._generate_special_pattern_semantic(special_pattern)
        else:
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
    
    def _prioritize_patterns(self, detected_patterns: List[Dict], chart: List, 
                            bazi_profile: BaziProfile) -> Dict[str, Any]:
        """
        [QGA V23.5] 格局优先级架构
        第一优先级：月令格神（60%权重）
        第二优先级：相位冲突（20%权重）
        第三优先级：空间奇点（10%权重）
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        result = {
            'primary': None,      # 主格局（月令格神）
            'conflicts': [],      # 相位冲突格局
            'singularities': []   # 空间奇点格局
        }
        
        month_pillar = chart[1]  # 月柱
        month_branch = month_pillar[1]  # 月支
        day_master = bazi_profile.day_master
        
        # 识别月令格神（基于月支藏干和日主的关系）
        month_hidden = BaziParticleNexus.get_branch_weights(month_branch)
        month_ten_gods = []
        for stem, weight in month_hidden:
            ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
            month_ten_gods.append((ten_god, weight))
        
        # 查找与月令相关的格局（优先级最高）
        for pattern in detected_patterns:
            pattern_name = pattern.get('name', '').lower()
            pattern_id = pattern.get('id', '').lower()
            
            # 检查是否是月令相关格局
            is_yue_ling_pattern = False
            if '伤官' in pattern_name or 'shang_guan' in pattern_id:
                if any('伤官' in tg[0] for tg in month_ten_gods):
                    is_yue_ling_pattern = True
            elif '正官' in pattern_name or 'zheng_guan' in pattern_id:
                if any('正官' in tg[0] for tg in month_ten_gods):
                    is_yue_ling_pattern = True
            elif '正财' in pattern_name or 'zheng_cai' in pattern_id:
                if any('正财' in tg[0] for tg in month_ten_gods):
                    is_yue_ling_pattern = True
            elif '偏财' in pattern_name or 'pian_cai' in pattern_id:
                if any('偏财' in tg[0] for tg in month_ten_gods):
                    is_yue_ling_pattern = True
            elif '正印' in pattern_name or 'zheng_yin' in pattern_id:
                if any('正印' in tg[0] for tg in month_ten_gods):
                    is_yue_ling_pattern = True
            
            if is_yue_ling_pattern and not result['primary']:
                result['primary'] = pattern
                pattern['priority'] = 'primary'
                pattern['weight'] = 0.6
                continue
            
            # 检查是否是相位冲突格局（如伤官见官）
            if '见' in pattern_name or 'jian' in pattern_id or 'conflict' in pattern_id:
                result['conflicts'].append(pattern)
                pattern['priority'] = 'conflict'
                pattern['weight'] = 0.2
                continue
            
            # 检查是否是空间奇点（拱夹、墓库）
            if '拱' in pattern_name or '墓' in pattern_name or '库' in pattern_name or \
               'gong' in pattern_id or 'mu' in pattern_id or 'ku' in pattern_id:
                result['singularities'].append(pattern)
                pattern['priority'] = 'singularity'
                pattern['weight'] = 0.1
                continue
        
        # 如果没有找到月令格神，选择第一个格局作为主格局（降权）
        if not result['primary'] and detected_patterns:
            result['primary'] = detected_patterns[0]
            result['primary']['priority'] = 'primary'
            result['primary']['weight'] = 0.4  # 降权
        
        return result
    
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
    
    def _capture_special_patterns(self, detected_patterns: List[Dict], chart: List,
                                 bazi_profile: BaziProfile) -> Optional[Dict]:
        """
        [QGA V24.0] 典型局捕获器
        识别特殊格局：伤官伤尽、从财格、化气格、羊刃驾杀等
        一旦识别，逻辑锁死，后续计算必须服从该格局的"标准答案"
        """
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        from typing import Optional
        
        day_master = bazi_profile.day_master
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
        
        # 1. 伤官伤尽（Shang Guan Shang Jin）
        # 判定：伤官多且无官星，或官星被完全制化
        shang_guan_count = ten_gods.count('伤官')
        zheng_guan_count = ten_gods.count('正官')
        qi_sha_count = ten_gods.count('七杀')
        
        if shang_guan_count >= 2 and (zheng_guan_count == 0 and qi_sha_count == 0):
            # 检查是否有官星被合化或冲掉
            for pattern in detected_patterns:
                pattern_name = pattern.get('name', '').lower()
                if '伤官' in pattern_name and ('尽' in pattern_name or 'shang_jin' in pattern.get('id', '').lower()):
                    return {
                        'type': 'shang_guan_shang_jin',
                        'name': '伤官伤尽',
                        'pattern': pattern,
                        'yong_shen_rule': 'shang_guan_or_wealth',  # 用神：伤官或行财运
                        'life_theme': '才华横溢，不受约束，适合自由职业或艺术创作'
                    }
        
        # 2. 从财格（From-Wealth Pattern）
        # 判定：财星极旺，日主极弱，从财
        cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
        if cai_count >= 3:
            # 检查日主是否极弱（无印比支撑）
            yin_count = ten_gods.count('正印') + ten_gods.count('偏印')
            bi_jie_count = ten_gods.count('比肩') + ten_gods.count('劫财')
            if yin_count == 0 and bi_jie_count <= 1:
                return {
                    'type': 'from_wealth',
                    'name': '从财格',
                    'pattern': None,
                    'yong_shen_rule': 'wealth',  # 用神：财星
                    'life_theme': '以财为用，善于经营，财富是人生核心追求'
                }
        
        # 3. 化气格（Transformation Pattern）
        # 判定：天干五合且合化成功
        for pattern in detected_patterns:
            pattern_name = pattern.get('name', '').lower()
            pattern_id = pattern.get('id', '').lower()
            if '化气' in pattern_name or 'hua_qi' in pattern_id or 'transform' in pattern_id:
                match_data = pattern.get('match_data', {})
                if match_data.get('transform', False):  # 合化成功
                    return {
                        'type': 'transformation',
                        'name': pattern.get('name', '化气格'),
                        'pattern': pattern,
                        'yong_shen_rule': 'transformed_element',  # 用神：合化后的元素
                        'life_theme': '性格转化，具有双重特质，人生多变'
                    }
        
        # 4. 羊刃驾杀（Yang Ren Jia Sha）
        # 判定：羊刃与七杀同时出现且力量相当
        day_master_yang_ren = {
            '甲': '卯', '乙': '寅',
            '丙': '午', '丁': '巳',
            '戊': '午', '己': '巳',
            '庚': '酉', '辛': '申',
            '壬': '子', '癸': '亥'
        }
        yang_ren = day_master_yang_ren.get(day_master)
        
        if yang_ren and yang_ren in branches and qi_sha_count >= 1:
            return {
                'type': 'yang_ren_jia_sha',
                'name': '羊刃驾杀',
                'pattern': None,
                'yong_shen_rule': 'sha_or_yin',  # 用神：七杀或印星
                'life_theme': '刚强果断，有领导力，但易冲动，需要制衡'
            }
        
        # 5. 超导体/奇点格局（Superconductor/Singularity）
        # 检查是否有高SAI、高纯度的格局
        for pattern in detected_patterns:
            pattern_id = pattern.get('id', '').lower()
            sai = pattern.get('sai', 0.0)
            # 确保sai是数值类型
            try:
                sai_float = float(sai) if sai is not None else 0.0
            except (ValueError, TypeError):
                sai_float = 0.0
            
            if 'superconductor' in pattern_id or 'singularity' in pattern_id or sai_float > 0.9:
                return {
                    'type': 'superconductor',
                    'name': pattern.get('name', '超导体格局'),
                    'pattern': pattern,
                    'yong_shen_rule': 'maintain_purity',  # 用神：维持纯度
                    'life_theme': '纯粹与秩序，追求完美，具有超常的专注力'
                }
        
        return None
    
    def _generate_special_pattern_semantic(self, special_pattern: Dict) -> str:
        """生成特殊格局的语义解释"""
        pattern_type = special_pattern.get('type')
        pattern_name = special_pattern.get('name')
        life_theme = special_pattern.get('life_theme', '')
        
        if pattern_type == 'shang_guan_shang_jin':
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。用神直接锁定伤官或行财运，不再考虑身强身弱的平衡。"
        elif pattern_type == 'from_wealth':
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。用神直接锁定财星，以财为用。"
        elif pattern_type == 'transformation':
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。用神为合化后的元素。"
        elif pattern_type == 'yang_ren_jia_sha':
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。用神为七杀或印星。"
        elif pattern_type == 'superconductor':
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。用神为维持纯度，避免杂质干扰。"
        else:
            return f"命局呈现**{pattern_name}**格局，这是超稳态结构。{life_theme}。"
    
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
                 geo_element: str = None, geo_factor: float = 1.0,
                 primary_pattern: Dict = None, conflict_patterns: List[Dict] = None,
                 special_pattern: Dict = None) -> OptimizationResult:
        """
        变分寻优（3年滚动窗口版本 + 定海神针逻辑）
        
        Args:
            bazi_profile: 八字档案对象
            year: 流年（可选）
            geo_element: 地理五行属性（可选）
            geo_factor: 地理因子（可选）
            primary_pattern: 主格局（用于定海神针逻辑）
            conflict_patterns: 冲突格局列表（用于定海神针逻辑）
            
        Returns:
            优化结果（确保用神在未来36个月内稳定）
        """
        if not year:
            year = 2024  # 默认年份
        
        # [优化2] 3年滚动窗口：扫描未来3年
        window_years = [year, year + 1, year + 2]
        
        # 1. 初始化引擎
        from core.engine_graph import GraphNetworkEngine
        
        # 2. 获取基础八字
        pillars = bazi_profile.pillars
        bazi = [
            pillars['year'],
            pillars['month'],
            pillars['day'],
            pillars['hour']
        ]
        
        # 3. 基准地理修正
        baseline_geo_modifiers = {}
        if geo_element:
            element_map = {
                'metal': 'metal', 'wood': 'wood', 'water': 'water',
                'fire': 'fire', 'earth': 'earth'
            }
            if geo_element in element_map:
                baseline_geo_modifiers[element_map[geo_element]] = geo_factor - 1.0
        
        # 4. 计算基准状态（当前年）
        baseline_engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        luck_pillar = bazi_profile.get_luck_pillar_at(year)
        year_pillar = bazi_profile.get_year_pillar(year)
        
        baseline_engine.initialize_nodes(
            bazi, bazi_profile.day_master,
            luck_pillar, year_pillar,
            geo_modifiers=baseline_geo_modifiers if baseline_geo_modifiers else None
        )
        baseline_engine.build_adjacency_matrix()
        baseline_engine.propagate()
        
        baseline_entropy = self._calculate_entropy(baseline_engine)
        baseline_stability = self._calculate_stability(baseline_engine)
        
        # [QGA V24.0] 用神判定优先级：格神优先 > 病药优先 > 平衡最后
        target_elements = []
        
        # [QGA V24.0] 优先级1：格神优先（特殊格局锁死）
        if special_pattern:
            yong_shen_rule = special_pattern.get('yong_shen_rule')
            target_elements = self._resolve_special_pattern_yong_shen(
                yong_shen_rule, bazi_profile.day_master
            )
            logger.info(f"🔒 特殊格局锁死，用神规则: {yong_shen_rule}, 目标元素: {target_elements}")
        # 优先级2：病药优先（格局冲突）
        elif primary_pattern is not None or (conflict_patterns is not None and len(conflict_patterns) > 0):
            target_elements = self._determine_yong_shen_direction(
                primary_pattern, conflict_patterns or [], bazi_profile.day_master
            )
            logger.info(f"💊 病药优先，目标元素: {target_elements}")
        # 优先级3：平衡最后（普通命局才计算五行平衡）
        else:
            logger.info("⚖️ 平衡最后，使用五行平衡算法")
        
        # 5. 变分搜索（3年滚动窗口）
        best_result = None
        best_score = float('inf')
        
        # 如果定海神针逻辑确定了方向，优先搜索这些元素
        search_elements = target_elements if target_elements else self.elements
        
        for element in search_elements:
            for injection_amount in np.arange(0.0, 1.0, self.step_size):
                # 测试该元素在未来3年的稳定性
                year_scores = []
                year_stabilities = []
                year_entropies = []
                
                for test_year in window_years:
                    test_luck = bazi_profile.get_luck_pillar_at(test_year)
                    test_year_pillar = bazi_profile.get_year_pillar(test_year)
                    
                    test_engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
                    test_geo_modifiers = baseline_geo_modifiers.copy()
                    test_geo_modifiers[element] = test_geo_modifiers.get(element, 0.0) + injection_amount
                    
                    test_engine.initialize_nodes(
                        bazi, bazi_profile.day_master,
                        test_luck, test_year_pillar,
                        geo_modifiers=test_geo_modifiers if test_geo_modifiers else None
                    )
                    test_engine.build_adjacency_matrix()
                    test_engine.propagate()
                    
                    entropy = self._calculate_entropy(test_engine)
                    stability = self._calculate_stability(test_engine)
                    
                    year_entropies.append(entropy)
                    year_stabilities.append(stability)
                    # 综合评分
                    year_scores.append(entropy - stability * 10.0)
                
                # 3年综合评分：要求稳定性不能大幅下降
                avg_score = np.mean(year_scores)
                avg_stability = np.mean(year_stabilities)
                stability_trend = year_stabilities[-1] - year_stabilities[0]  # 稳定性趋势
                
                # 如果稳定性下降超过20%，惩罚该方案
                if stability_trend < -0.2:
                    avg_score += 5.0  # 惩罚分
                
                # 如果未来年份熵值增加，说明会激化冲突，惩罚
                entropy_trend = year_entropies[-1] - year_entropies[0]
                if entropy_trend > 0.05:
                    avg_score += 3.0  # 惩罚分
                
                if avg_score < best_score:
                    best_score = avg_score
                    best_result = {
                        'element': element,
                        'amount': injection_amount,
                        'entropy': np.mean(year_entropies),
                        'stability': avg_stability,
                        'entropy_reduction': baseline_entropy - np.mean(year_entropies),
                        'stability_trend': stability_trend,
                        '3year_stable': stability_trend >= -0.1  # 3年稳定性标志
                    }
        
        # 6. 生成最优组合
        optimal_elements = {}
        if best_result:
            optimal_elements[best_result['element']] = best_result['amount']
        
        # 7. 生成语义解释（包含3年稳定性信息）
        semantic = self._generate_optimization_semantic(best_result, baseline_entropy, baseline_stability)
        
        return OptimizationResult(
            optimal_elements=optimal_elements,
            stability_score=best_result['stability'] if best_result else baseline_stability,
            entropy_reduction=best_result['entropy_reduction'] if best_result else 0.0,
            semantic_interpretation=semantic
        )
    
    def _determine_yong_shen_direction(self, primary_pattern: Dict, conflict_patterns: List[Dict],
                                      day_master: str) -> List[str]:
        """
        [QGA V23.5] 定海神针逻辑：基于格局冲突直接锁定用神方向
        
        如果主格局是[伤官见官]，矛盾点在"官星受损"：
        - 通关方向：财星（伤官生财，财生官）
        - 制衡方向：印星（印克伤官，保护官星）
        
        Returns:
            目标元素列表（优先搜索方向）
        """
        if not conflict_patterns:
            return []  # 没有冲突，不锁定方向
        
        # 检查是否是伤官见官格局
        for cp in conflict_patterns:
            pattern_name = cp.get('name', '').lower()
            pattern_id = cp.get('id', '').lower()
            
            if '伤官' in pattern_name and '官' in pattern_name or \
               'shang_guan' in pattern_id and 'guan' in pattern_id:
                # 伤官见官：通关用财，制衡用印
                # 根据日主确定财和印的元素
                day_master_elements = {
                    '甲': 'wood', '乙': 'wood',
                    '丙': 'fire', '丁': 'fire',
                    '戊': 'earth', '己': 'earth',
                    '庚': 'metal', '辛': 'metal',
                    '壬': 'water', '癸': 'water'
                }
                dm_element = day_master_elements.get(day_master, 'earth')
                
                # 财星：我克者为财
                # 印星：生我者为印
                generation_map = {
                    'wood': 'water',  # 水生木（印）
                    'fire': 'wood',   # 木生火（印）
                    'earth': 'fire',  # 火生土（印）
                    'metal': 'earth', # 土生金（印）
                    'water': 'metal' # 金生水（印）
                }
                control_map = {
                    'wood': 'earth',  # 木克土（财）
                    'fire': 'metal',   # 火克金（财）
                    'earth': 'water',  # 土克水（财）
                    'metal': 'wood',   # 金克木（财）
                    'water': 'fire'    # 水克火（财）
                }
                
                yin_element = generation_map.get(dm_element, 'earth')
                cai_element = control_map.get(dm_element, 'earth')
                
                # 优先通关（财），其次制衡（印）
                return [cai_element, yin_element]
        
        return []  # 其他冲突格局，不锁定方向
    
    def _resolve_special_pattern_yong_shen(self, yong_shen_rule: str, day_master: str) -> List[str]:
        """
        [QGA V24.0] 解析特殊格局的用神规则
        格神优先：直接锁定用神，不再考虑平衡
        """
        day_master_elements = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        dm_element = day_master_elements.get(day_master, 'earth')
        
        # 十神到五行的映射
        generation_map = {
            'wood': 'water',  # 水生木（印）
            'fire': 'wood',   # 木生火（印）
            'earth': 'fire',  # 火生土（印）
            'metal': 'earth', # 土生金（印）
            'water': 'metal'  # 金生水（印）
        }
        control_map = {
            'wood': 'earth',  # 木克土（财）
            'fire': 'metal',  # 火克金（财）
            'earth': 'water', # 土克水（财）
            'metal': 'wood',  # 金克木（财）
            'water': 'fire'   # 水克火（财）
        }
        output_map = {
            'wood': 'fire',   # 木生火（伤官/食神）
            'fire': 'earth',  # 火生土（伤官/食神）
            'earth': 'metal', # 土生金（伤官/食神）
            'metal': 'water', # 金生水（伤官/食神）
            'water': 'wood'   # 水生木（伤官/食神）
        }
        control_reverse_map = {
            'wood': 'metal',  # 金克木（官杀）
            'fire': 'water',  # 水克火（官杀）
            'earth': 'wood',  # 木克土（官杀）
            'metal': 'fire',  # 火克金（官杀）
            'water': 'earth'  # 土克水（官杀）
        }
        
        if yong_shen_rule == 'shang_guan_or_wealth':
            # 伤官伤尽：用神为伤官（我生）或财（我克）
            return [output_map.get(dm_element, 'fire'), control_map.get(dm_element, 'earth')]
        elif yong_shen_rule == 'wealth':
            # 从财格：用神为财（我克）
            return [control_map.get(dm_element, 'earth')]
        elif yong_shen_rule == 'sha_or_yin':
            # 羊刃驾杀：用神为七杀（克我）或印（生我）
            return [control_reverse_map.get(dm_element, 'metal'), generation_map.get(dm_element, 'water')]
        elif yong_shen_rule == 'maintain_purity':
            # 超导体：维持纯度，用神为日主本身
            return [dm_element]
        elif yong_shen_rule == 'transformed_element':
            # 化气格：用神为合化后的元素（需要从格局信息中获取）
            # 简化：返回日主元素（实际应该从合化信息中获取）
            return [dm_element]
        else:
            return []
    
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
        """生成优化语义解释（包含3年稳定性验证）"""
        if not best_result:
            return "当前系统已达到较优状态，无需大幅调整。"
        
        element_cn = self.element_cn.get(best_result['element'], best_result['element'])
        reduction = best_result['entropy_reduction']
        is_3year_stable = best_result.get('3year_stable', True)
        stability_trend = best_result.get('stability_trend', 0.0)
        
        base_msg = ""
        if reduction > 0.1:
            base_msg = f"系统通过注入{element_cn}元素（强度{best_result['amount']:.2f}）能够显著降低内耗，提升稳定性。"
        elif reduction > 0.05:
            base_msg = f"系统通过适度注入{element_cn}元素能够改善能量分布，减少内部冲突。"
        else:
            base_msg = "当前系统状态较为平衡，小幅调整即可维持稳定。"
        
        # [优化2] 添加3年稳定性验证
        if is_3year_stable:
            if stability_trend > 0.05:
                base_msg += " 经过3年滚动窗口验证，该用神在未来36个月内将带来持续稳定的增益，不会激化潜在冲突。"
            else:
                base_msg += " 经过3年滚动窗口验证，该用神在未来36个月内保持稳定，不会出现'今年发财，明年坐牢'的短视风险。"
        else:
            base_msg += f" ⚠️ 注意：该用神在未来3年内可能导致稳定性下降（趋势{stability_trend:.2f}），建议谨慎使用或寻找替代方案。"
        
        if reduction > 0.1:
            base_msg += " 这是最能平息内耗、开启财富的钥匙。"
        
        return base_msg


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
        
        # [优化4] 微环境修正系数（添加特定矢量偏移）
        # 例如：近水增加水元素15%，同时降低火元素稳定性
        self.micro_env_factors = {
            '近水': {'water': 1.15, 'fire': 0.85, 'earth': 0.95, 'wood': 1.05, 'metal': 1.0},
            '近山': {'earth': 1.15, 'wood': 1.10, 'fire': 0.90, 'water': 0.95, 'metal': 1.05},
            '高层': {'fire': 1.10, 'metal': 1.05, 'earth': 0.95, 'water': 0.90, 'wood': 1.0},
            '低层': {'earth': 1.10, 'water': 1.05, 'wood': 1.0, 'fire': 0.95, 'metal': 0.95},
        }
        
        # [优化4] 微环境矢量偏移（直接作用于五行能量分布）
        self.micro_env_vector_offsets = {
            '近水': {'water': +15.0, 'fire': -10.0},  # 近水：水+15%，火-10%
            '近山': {'earth': +15.0, 'wood': +10.0},  # 近山：土+15%，木+10%
            '高层': {'fire': +10.0, 'metal': +5.0, 'water': -10.0},  # 高层：火+10%，金+5%，水-10%
            '低层': {'earth': +10.0, 'water': +5.0},  # 低层：土+10%，水+5%
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
        
        # 2. 微环境修正（[优化4] 应用矢量偏移）
        micro_correction = {'metal': 1.0, 'wood': 1.0, 'water': 1.0, 'fire': 1.0, 'earth': 1.0}
        micro_vector_offsets = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
        
        if micro_env:
            for env in micro_env:
                if env in self.micro_env_factors:
                    factors = self.micro_env_factors[env]
                    for element, factor in factors.items():
                        micro_correction[element] *= factor
                
                # [优化4] 应用矢量偏移
                if env in self.micro_env_vector_offsets:
                    offsets = self.micro_env_vector_offsets[env]
                    for element, offset in offsets.items():
                        micro_vector_offsets[element] += offset
        
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
    
    def get_micro_env_vector_offsets(self, micro_env: List[str] = None) -> Dict[str, float]:
        """
        [优化4] 获取微环境的矢量偏移
        
        Args:
            micro_env: 微环境列表
            
        Returns:
            矢量偏移字典（百分比）
        """
        offsets = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
        
        if micro_env:
            for env in micro_env:
                if env in self.micro_env_vector_offsets:
                    env_offsets = self.micro_env_vector_offsets[env]
                    for element, offset in env_offsets.items():
                        offsets[element] += offset
        
        return offsets
    
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

