"""
全息格局控制器 (Holographic Pattern Controller)
MVC Controller Layer - 负责全息格局的业务逻辑

严格遵循MVC架构原则：
- View层（holographic_pattern.py）只负责UI展示和用户交互
- Controller层封装所有算法逻辑，协调Engine和Model
- Engine层负责核心计算

注意：这是全新的"张量全息格局"系统，不依赖现有的物理模型仿真注册表
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.engine_graph.constants import TWELVE_LIFE_STAGES
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine

logger = logging.getLogger(__name__)


class HolographicPatternController:
    """
    全息格局控制器
    
    职责：
    - 封装全息格局相关的业务逻辑
    - 协调格局注册表的加载和查询（使用新的"张量全息格局"注册表）
    - 处理五维张量投影计算
    - 提供统一的数据接口给View层
    """
    
    def __init__(self):
        """初始化控制器"""
        # 使用新的"张量全息格局"注册表路径
        self.registry_path = Path(__file__).parent.parent / "core" / "subjects" / "holographic_pattern" / "registry.json"
        self.registry = None
        self.framework = QuantumUniversalFramework()
        logger.info("HolographicPatternController initialized (全新张量全息格局系统)")
    
    def load_registry(self) -> Dict:
        """
        加载格局注册表
        
        Returns:
            注册表字典
        """
        if self.registry is None:
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
                logger.info(f"✅ 已加载注册表: {len(self.registry.get('patterns', {}))} 个格局")
            except Exception as e:
                logger.error(f"加载注册表失败: {e}")
                self.registry = {"patterns": {}, "metadata": {}}
        
        return self.registry
    
    def get_all_patterns(self) -> List[Dict]:
        """
        获取所有格局列表（按QGA-HR V1.0层级命名规范）
        支持主格局和子格局的层级关系
        
        Returns:
            格局列表，按Category和Subject ID排序，子格局跟随主格局
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        # 分离主格局和子格局
        main_patterns = []
        sub_patterns = []
        
        for pattern_id, pattern_data in patterns.items():
            # 提取层级信息
            category = pattern_data.get('category', '')
            subject_id = pattern_data.get('subject_id', pattern_id)
            parent_pattern = pattern_data.get('parent_pattern')
            
            pattern_info = {
                'id': pattern_id,
                'category': category,
                'subject_id': subject_id,
                'name': pattern_data.get('name', pattern_id),
                'name_cn': pattern_data.get('name_cn', ''),
                'icon': pattern_data.get('icon', '🧬'),
                'description': pattern_data.get('description', ''),
                'version': pattern_data.get('version', 'N/A'),
                'active': pattern_data.get('active', False),
                'semantic_seed': pattern_data.get('semantic_seed', {}),
                'tensor_operator': pattern_data.get('tensor_operator', {}),
                'parent_pattern': parent_pattern,
                'is_sub_pattern': parent_pattern is not None
            }
            
            if parent_pattern:
                sub_patterns.append(pattern_info)
            else:
                main_patterns.append(pattern_info)
        
        # 主格局按Category和Subject ID排序
        main_patterns.sort(key=lambda x: (x.get('category', ''), x.get('subject_id', '')))
        
        # 子格局按父格局分组，然后按Subject ID排序
        sub_patterns_by_parent = {}
        for sub_pattern in sub_patterns:
            parent_id = sub_pattern['parent_pattern']
            if parent_id not in sub_patterns_by_parent:
                sub_patterns_by_parent[parent_id] = []
            sub_patterns_by_parent[parent_id].append(sub_pattern)
        
        # 对每个父格局的子格局排序
        for parent_id in sub_patterns_by_parent:
            sub_patterns_by_parent[parent_id].sort(key=lambda x: x.get('subject_id', ''))
        
        # 构建层级结果：主格局 + 其子格局
        result = []
        for main_pattern in main_patterns:
            # 添加主格局
            result.append(main_pattern)
            
            # 添加该主格局的子格局
            main_id = main_pattern['id']
            if main_id in sub_patterns_by_parent:
                for sub_pattern in sub_patterns_by_parent[main_id]:
                    result.append(sub_pattern)
        
        # 处理没有父格局的子格局（理论上不应该有，但为了健壮性）
        for sub_pattern in sub_patterns:
            if sub_pattern['parent_pattern'] not in [p['id'] for p in main_patterns]:
                result.append(sub_pattern)
        
        return result
    
    def get_pattern_hierarchy(self) -> Dict[str, Dict]:
        """
        获取格局层级结构（主格局 -> 子格局）
        
        Returns:
            字典：{主格局ID: {'main': 主格局信息, 'subs': [子格局列表]}}
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        hierarchy = {}
        
        # 先找出所有主格局
        for pattern_id, pattern_data in patterns.items():
            parent_pattern = pattern_data.get('parent_pattern')
            if not parent_pattern:  # 主格局
                category = pattern_data.get('category', '')
                subject_id = pattern_data.get('subject_id', pattern_id)
                
                hierarchy[pattern_id] = {
                    'main': {
                        'id': pattern_id,
                        'category': category,
                        'subject_id': subject_id,
                        'name': pattern_data.get('name', pattern_id),
                        'name_cn': pattern_data.get('name_cn', ''),
                        'icon': pattern_data.get('icon', '🧬'),
                        'description': pattern_data.get('description', ''),
                        'version': pattern_data.get('version', 'N/A'),
                        'active': pattern_data.get('active', False)
                    },
                    'subs': []
                }
        
        # 再找出所有子格局并归类
        for pattern_id, pattern_data in patterns.items():
            parent_pattern = pattern_data.get('parent_pattern')
            if parent_pattern and parent_pattern in hierarchy:
                category = pattern_data.get('category', '')
                subject_id = pattern_data.get('subject_id', pattern_id)
                
                hierarchy[parent_pattern]['subs'].append({
                    'id': pattern_id,
                    'category': category,
                    'subject_id': subject_id,
                    'name': pattern_data.get('name', pattern_id),
                    'name_cn': pattern_data.get('name_cn', ''),
                    'icon': pattern_data.get('icon', '🧬'),
                    'description': pattern_data.get('description', ''),
                    'version': pattern_data.get('version', 'N/A'),
                    'active': pattern_data.get('active', False)
                })
        
        # 对每个主格局的子格局排序
        for parent_id in hierarchy:
            hierarchy[parent_id]['subs'].sort(key=lambda x: x.get('subject_id', ''))
        
        return hierarchy
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict]:
        """
        根据ID获取格局详情
        
        Args:
            pattern_id: 格局ID
            
        Returns:
            格局详情字典，如果不存在则返回None
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        if pattern_id in patterns:
            return patterns[pattern_id]
        
        return None
    
    def calculate_tensor_projection(self, pattern_id: str, chart: List[str], 
                                   day_master: str, context: Optional[Dict] = None) -> Dict:
        """
        计算五维张量投影（基于FDS-V1.1规范）
        
        Args:
            pattern_id: 格局ID
            chart: 八字原局
            day_master: 日主
            context: 上下文（大运、流年等）
            
        Returns:
            五维张量投影结果
        """
        # 获取格局信息
        pattern = self.get_pattern_by_id(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        # 获取张量投影算子（模块II）
        tensor_operator = pattern.get('tensor_operator', {})
        weights = tensor_operator.get('weights', {})
        
        # 如果没有权重，返回错误（必须通过FDS-V1.1 Step 1注册）
        if not weights:
            return {
                'error': f'格局 {pattern_id} 尚未完成FDS-V1.1 Step 1注册（缺少张量投影算子）',
                'pattern_id': pattern_id,
                'pattern_name': pattern.get('name', pattern_id)
            }
        
        # 验证权重归一化（单位向量约束）
        if not tensor_operator.get('normalized', False):
            weights = self.normalize_weights(weights)
            logger.warning(f"格局 {pattern_id} 权重未归一化，已自动归一化")
        
        # 计算SAI（系统对齐指数）
        try:
            binfo = {'day_master': day_master}
            if context:
                ctx = {
                    'luck_pillar': context.get('luck_pillar'),
                    'annual_pillar': context.get('annual_pillar'),
                    'scenario': context.get('scenario', 'default')
                }
            else:
                ctx = {'scenario': 'default'}
            
            result = self.framework.arbitrate_bazi(chart, binfo, ctx)
            
            # SAI在result['physics']['stress']['SAI']中
            physics = result.get('physics', {})
            stress = physics.get('stress', {})
            sai = stress.get('SAI', 0.0)
            
            # 如果SAI为0，记录警告
            if sai == 0.0:
                logger.warning(f"SAI计算结果为0.0，可能的原因：1) 八字不匹配该格局 2) 计算异常 3) 结构过于稳定")
        except Exception as e:
            logger.error(f"计算SAI失败: {e}", exc_info=True)
            sai = 0.0
        
        # 计算五维投影（SAI × 权重）
        projection = {
            'E': sai * weights.get('E', 0.0),  # 能级轴
            'O': sai * weights.get('O', 0.0),  # 秩序轴
            'M': sai * weights.get('M', 0.0),  # 物质轴
            'S': sai * weights.get('S', 0.0),  # 应力轴
            'R': sai * weights.get('R', 0.0)   # 关联轴
        }
        
        # 获取语义意象（模块I）
        semantic_seed = pattern.get('semantic_seed', {})
        
        return {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name', pattern_id),
            'sai': sai,
            'projection': projection,
            'weights': weights,
            'semantic_seed': semantic_seed.get('description', ''),
            'tensor_operator': tensor_operator
        }
    
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        权重归一化（单位向量约束）
        
        Args:
            weights: 权重字典
            
        Returns:
            归一化后的权重字典
        """
        total = sum(abs(v) for v in weights.values())
        if total == 0:
            return weights
        
        return {k: round(v / total, 4) for k, v in weights.items()}
    
    def _check_strong_root(self, stem: str, branch: str) -> bool:
        """
        检查天干是否坐强根（简化版：检查地支本气是否为天干的同类五行）
        
        Args:
            stem: 天干
            branch: 地支
            
        Returns:
            是否坐强根
        """
        # 天干五行
        stem_wuxing = {
            '甲': '木', '乙': '木',
            '丙': '火', '丁': '火',
            '戊': '土', '己': '土',
            '庚': '金', '辛': '金',
            '壬': '水', '癸': '水'
        }
        
        # 地支本气五行
        branch_wuxing = {
            '子': '水', '丑': '土', '寅': '木', '卯': '木',
            '辰': '土', '巳': '火', '午': '火', '未': '土',
            '申': '金', '酉': '金', '戌': '土', '亥': '水'
        }
        
        stem_wx = stem_wuxing.get(stem, '')
        branch_wx = branch_wuxing.get(branch, '')
        
        # 强根：地支本气与天干同五行
        if stem_wx == branch_wx:
            return True
        
        # 检查地支藏干（简化：只检查主要藏干）
        # 这里可以扩展更详细的藏干检查
        return False
    
    def _calculate_purity_score(self, sample: Dict, day_master: str) -> float:
        """
        计算样本纯度得分（基于AI分析师最新规范）
        
        Args:
            sample: 样本字典
            day_master: 日主
            
        Returns:
            纯度得分（越高越纯净）
        """
        chart = sample['chart']
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        ten_gods = sample['ten_gods']
        
        # 基础分
        score = 100.0
        
        # 加分项
        # +20分：七杀坐强根（如庚申）
        qi_sha_stems = sample.get('qi_sha_stems', [])
        for qi_sha_stem in qi_sha_stems:
            # 找到七杀所在位置
            for i, s in enumerate(stems):
                if s == qi_sha_stem:
                    # 检查对应的地支是否强根
                    if self._check_strong_root(qi_sha_stem, branches[i]):
                        score += 20
                        break  # 只加一次分
        
        # +10分：印星贴身（有通关冷却）
        yin_count = ten_gods.count('正印') + ten_gods.count('偏印')
        if yin_count > 0:
            score += yin_count * 10
        
        # 减分项
        # -15分：食伤混杂（制杀太过或干扰磁场）
        shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
        if shi_shen_count > 0:
            score -= shi_shen_count * 15
        
        # -15分：财星党杀（增加应力风险）
        cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
        if cai_count > 0:
            score -= cai_count * 15
        
        # -10分：地支有刑/冲/穿（结构不稳）
        clash_pairs = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
                      ('辰', '戌'), ('巳', '亥')]
        harm_pairs = [('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'),
                     ('申', '亥'), ('酉', '戌')]
        
        has_clash = False
        has_harm = False
        for i, b1 in enumerate(branches):
            for j, b2 in enumerate(branches[i+1:], i+1):
                if (b1, b2) in clash_pairs or (b2, b1) in clash_pairs:
                    has_clash = True
                if (b1, b2) in harm_pairs or (b2, b1) in harm_pairs:
                    has_harm = True
        
        if has_clash or has_harm:
            score -= 10
        
        return score
    
    def _detect_singularity(self, sample: Dict, day_master: str) -> Tuple[bool, str]:
        """
        检测是否为奇点样本（基于AI分析师最新规范）
        
        Args:
            sample: 样本字典
            day_master: 日主
            
        Returns:
            (是否为奇点, 奇点类型)
        """
        chart = sample['chart']
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        ten_gods = sample['ten_gods']
        
        # 获取羊刃地支
        yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        yang_ren_branch = yang_ren_map.get(day_master)
        
        # 1. 能量溢出：地支羊刃数量 >= 3（如：地支三卯）
        yang_ren_count = branches.count(yang_ren_branch) if yang_ren_branch else 0
        if yang_ren_count >= 3:
            return True, "X1-聚变临界型（地支三刃）"
        
        # 2. 高压临界：天干透出2个或以上七杀，且四柱无食神（制）无印星（化），纯粹攻身
        qi_sha_count = ten_gods.count('七杀')
        yin_count = ten_gods.count('正印') + ten_gods.count('偏印')
        shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
        
        if qi_sha_count >= 2 and yin_count == 0 and shi_shen_count == 0:
            return True, "X2-结构高压型（众杀攻身无制）"
        
        return False, ""
    
    def select_samples(self, pattern_id: str, target_count: int = 500, 
                      progress_callback: Optional[callable] = None,
                      output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        按照FDS-V1.1 Step 2的数据选择标准进行样本海选（升级版：纯度排序+奇点捕获）
        
        Args:
            pattern_id: 格局ID
            target_count: 目标样本数量（默认500，用于Tier A标准集）
            progress_callback: 进度回调函数 (current, total, stats)
            output_dir: 输出目录（如果提供，将保存两个JSON文件）
            
        Returns:
            包含standard_set和singularities的字典
        """
        # 获取格局信息
        pattern = self.get_pattern_by_id(pattern_id)
        if not pattern:
            logger.error(f"格局 {pattern_id} 不存在")
            return []
        
        # 获取数据选择标准
        data_criteria = pattern.get('audit_trail', {}).get('data_selection_criteria', {})
        if not data_criteria:
            logger.error(f"格局 {pattern_id} 缺少数据选择标准")
            return []
        
        # 初始化生成器
        engine = SyntheticBaziEngine()
        bazi_gen = engine.generate_all_bazi()
        
        candidates = []
        total_scanned = 0
        stats = {
            'scanned': 0,
            'matched': 0,
            'rejected_month_lock': 0,
            'rejected_stem_reveal': 0,
            'rejected_purity': 0
        }
        
        logger.info(f"开始样本海选：格局={pattern_id}，目标={target_count}例，全量扫描518,400个样本")
        
        # 严格全量扫描：必须扫描所有518,400个样本
        for chart in bazi_gen:
            total_scanned += 1
            stats['scanned'] = total_scanned
            
            # 进度回调（每10,000个样本或每5%进度）
            if progress_callback and (total_scanned % 10000 == 0 or total_scanned % 25920 == 0):
                progress_callback(total_scanned, 518400, stats)
            
            # 注意：不提前退出，必须扫描全部518,400个样本
            
            # 提取基本信息
            year_pillar, month_pillar, day_pillar, hour_pillar = chart
            day_master = day_pillar[0]
            month_branch = month_pillar[1]
            
            # 1. 月令锁：月支本气必须为日主之帝旺（即羊刃）
            life_stage = TWELVE_LIFE_STAGES.get((day_master, month_branch))
            if life_stage != '帝旺':
                stats['rejected_month_lock'] += 1
                continue
            
            # 2. 天干透杀：天干必须透出七杀，且七杀必须有根
            stems = [year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0]]
            branches = [year_pillar[1], month_pillar[1], day_pillar[1], hour_pillar[1]]
            
            # 检查天干是否有七杀
            qi_sha_stems = []
            for i, stem in enumerate(stems):
                if i == 2:  # 跳过日主
                    continue
                ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
                if ten_god == '七杀':
                    qi_sha_stems.append((i, stem))
            
            if not qi_sha_stems:
                stats['rejected_stem_reveal'] += 1
                continue
            
            # 检查七杀是否有根
            has_root = False
            for _, qi_sha_stem in qi_sha_stems:
                # 检查自坐
                pillar_idx = qi_sha_stems[0][0]
                if pillar_idx < len(branches):
                    branch = branches[pillar_idx]
                    hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                    for hidden_stem, weight in hidden_stems:
                        if hidden_stem == qi_sha_stem and weight >= 5:  # 主气或中气
                            has_root = True
                            break
                
                # 检查其他地支
                if not has_root:
                    for branch in branches:
                        hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                        for hidden_stem, weight in hidden_stems:
                            if hidden_stem == qi_sha_stem and weight >= 5:
                                has_root = True
                                break
                        if has_root:
                            break
                
                if has_root:
                    break
            
            if not has_root:
                stats['rejected_stem_reveal'] += 1
                continue
            
            # 3. 清纯度过滤：剔除重食伤制杀、重财党杀
            ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
            
            # 统计食伤和财星数量
            shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
            cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
            qi_sha_count = ten_gods.count('七杀')
            
            # 剔除重食伤制杀（这会变成A-02食神制杀）
            if shi_shen_count >= 2 and qi_sha_count >= 1:
                stats['rejected_purity'] += 1
                continue
            
            # 剔除重财党杀（这会导致应力轴S爆表）
            if cai_count >= 2 and qi_sha_count >= 1:
                stats['rejected_purity'] += 1
                continue
            
            # 通过所有筛选条件
            candidates.append({
                'chart': chart,
                'day_master': day_master,
                'month_branch': month_branch,
                'qi_sha_stems': [s for _, s in qi_sha_stems],
                'ten_gods': ten_gods
            })
            stats['matched'] += 1
        
        # 验证是否扫描了全部样本
        if total_scanned < 518400:
            logger.warning(f"⚠️ 只扫描了 {total_scanned} 个样本，未达到全量518,400个")
        else:
            logger.info(f"✅ 已扫描全部518,400个样本")
        
        logger.info(f"Step A完成：扫描={total_scanned}，匹配={len(candidates)}，目标={target_count}")
        logger.info(f"统计：月令锁拒绝={stats['rejected_month_lock']}，透杀拒绝={stats['rejected_stem_reveal']}，纯度拒绝={stats['rejected_purity']}")
        
        # ========== Step B: 奇点捕获 (Tier X) ==========
        logger.info("=" * 70)
        logger.info("Step B: 奇点捕获 (Tier X)")
        logger.info("=" * 70)
        
        singularities = []
        standard_candidates = []
        
        for sample in candidates:
            day_master = sample['day_master']
            is_singularity, singularity_type = self._detect_singularity(sample, day_master)
            
            if is_singularity:
                sample['singularity_type'] = singularity_type
                sample['purity_score'] = self._calculate_purity_score(sample, day_master)
                singularities.append(sample)
            else:
                standard_candidates.append(sample)
        
        logger.info(f"✅ 发现奇点样本 {len(singularities)} 个，已隔离")
        logger.info(f"✅ 标准候选样本 {len(standard_candidates)} 个")
        
        # ========== Step C: 标准集优选 (Tier A) ==========
        logger.info("=" * 70)
        logger.info("Step C: 标准集优选 (Tier A) - 纯度加权排序")
        logger.info("=" * 70)
        
        # 计算纯度得分并排序
        for sample in standard_candidates:
            day_master = sample['day_master']
            sample['purity_score'] = self._calculate_purity_score(sample, day_master)
        
        # 按纯度得分降序排序
        standard_candidates.sort(key=lambda x: x['purity_score'], reverse=True)
        
        # 截取前target_count个作为Tier A标准集
        if len(standard_candidates) > target_count:
            standard_set = standard_candidates[:target_count]
            logger.info(f"✅ 从 {len(standard_candidates)} 个候选样本中，按纯度排序选取前 {target_count} 个作为Tier A标准集")
        else:
            standard_set = standard_candidates
            logger.info(f"✅ 候选样本 {len(standard_candidates)} 个（少于目标 {target_count}），全部作为Tier A标准集")
        
        # 输出统计
        if standard_set:
            avg_purity = sum(s['purity_score'] for s in standard_set) / len(standard_set)
            max_purity = max(s['purity_score'] for s in standard_set)
            min_purity = min(s['purity_score'] for s in standard_set)
            logger.info(f"Tier A纯度统计：平均={avg_purity:.2f}，最高={max_purity:.2f}，最低={min_purity:.2f}")
        
        # ========== 保存结果 ==========
        result = {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name_cn', pattern_id),
            'total_scanned': total_scanned,
            'tier_a': {
                'count': len(standard_set),
                'samples': standard_set
            },
            'tier_x': {
                'count': len(singularities),
                'samples': singularities
            },
            'stats': stats
        }
        
        # 如果提供了输出目录，保存文件
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存Tier A标准集
            standard_file = output_dir / f"QGA_{pattern_id}_TierA_Standard.json"
            with open(standard_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern.get('name_cn', pattern_id),
                    'tier': 'A',
                    'description': '标准纯净集（Tier A）- 最教科书级的样本',
                    'count': len(standard_set),
                    'samples': standard_set
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Tier A标准集已保存: {standard_file}")
            
            # 保存Tier X奇点集
            if singularities:
                singularity_file = output_dir / f"QGA_{pattern_id}_TierX_Singularity.json"
                with open(singularity_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'pattern_id': pattern_id,
                        'pattern_name': pattern.get('name_cn', pattern_id),
                        'tier': 'X',
                        'description': '奇点集（Tier X）- 极端样本，蕴含新的物理定律',
                        'count': len(singularities),
                        'samples': singularities
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Tier X奇点集已保存: {singularity_file}")
        
        logger.info("=" * 70)
        logger.info(f"✅ 样本海选完成：Tier A={len(standard_set)}个，Tier X={len(singularities)}个")
        logger.info("=" * 70)
        
        return result

