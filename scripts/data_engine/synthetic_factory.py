"""
V11.1 合成数据工厂 (Synthetic Data Factory)
造血模组：按照八字物理学，生成完美的"教科书级"标准案例

生成规则：
1. 极纯生成：天干地支全一气（如四甲戌），Label = Special_Strong
2. 极克生成：日主无根，满盘七杀，Label = Follower (从杀)
3. 极泄生成：日主无根，满盘食伤，Label = Follower (从儿)
"""

import logging
import random
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# V11.9: 初始化随机种子（确保可复现性）
random.seed(42)

# 天干五行映射
STEM_ELEMENTS = {
    '甲': 'wood', '乙': 'wood',
    '丙': 'fire', '丁': 'fire',
    '戊': 'earth', '己': 'earth',
    '庚': 'metal', '辛': 'metal',
    '壬': 'water', '癸': 'water'
}

# 地支五行映射
BRANCH_ELEMENTS = {
    '子': 'water', '丑': 'earth', '寅': 'wood', '卯': 'wood',
    '辰': 'earth', '巳': 'fire', '午': 'fire', '未': 'earth',
    '申': 'metal', '酉': 'metal', '戌': 'earth', '亥': 'water'
}

# 地支藏干映射（简化版，只取主气）
BRANCH_HIDDEN_MAIN = {
    '子': '癸', '丑': '己', '寅': '甲', '卯': '乙',
    '辰': '戊', '巳': '丙', '午': '丁', '未': '己',
    '申': '庚', '酉': '辛', '戌': '戊', '亥': '壬'
}

# 月令得令对应（确保日主在月令有根）
# 格式：月支 -> 得令的天干（月支藏干主气）
MONTH_COMMAND = {
    '子': ['癸'],  # 子月，癸水得令
    '丑': ['己'],  # 丑月，己土得令
    '寅': ['甲'],  # 寅月，甲木得令
    '卯': ['乙'],  # 卯月，乙木得令
    '辰': ['戊'],  # 辰月，戊土得令
    '巳': ['丙'],  # 巳月，丙火得令
    '午': ['丁'],  # 午月，丁火得令
    '未': ['己'],  # 未月，己土得令
    '申': ['庚'],  # 申月，庚金得令
    '酉': ['辛'],  # 酉月，辛金得令
    '戌': ['戊'],  # 戌月，戊土得令
    '亥': ['壬'],  # 亥月，壬水得令
}


class SyntheticDataFactory:
    """合成数据工厂：生成完美的理论案例"""
    
    def __init__(self):
        self.generated_count = 0
    
    def generate_perfect_cases(self, target_count: int = 300) -> List[Dict]:  # V11.8: 大规模增兵，从50提升到300
        """
        生成完美的合成数据案例
        
        Args:
            target_count: 目标生成数量（默认50个）
        
        Returns:
            合成案例列表，每个案例包含完整的八字信息和ground_truth标签
        """
        synthetic_cases = []
        
        # V11.8: 大规模增兵策略 - 用300个合成数据压倒真实数据的噪声
        # 1. Special_Strong (专旺格) - 150个案例（大幅增加）
        # 覆盖更多边缘情况：Score=70的假专旺，Score=90的真专旺等
        special_strong_cases = self._generate_special_strong_cases(count=150)
        synthetic_cases.extend(special_strong_cases)
        
        # 2. Follower (从格) - 100个案例（大幅增加）
        # 覆盖更多边缘情况：Score=30的假从格，Score=10的真从格等
        follower_cases = self._generate_follower_cases(count=100)
        synthetic_cases.extend(follower_cases)
        
        # 3. Balanced (中和格) - 30个案例
        balanced_cases = self._generate_balanced_cases(count=30)
        synthetic_cases.extend(balanced_cases)
        
        # 4. Strong (身强) - 10个案例
        strong_cases = self._generate_strong_cases(count=10)
        synthetic_cases.extend(strong_cases)
        
        # 5. Weak (身弱) - 10个案例
        weak_cases = self._generate_weak_cases(count=10)
        synthetic_cases.extend(weak_cases)
        
        self.generated_count = len(synthetic_cases)
        logger.info(f"✅ 生成了 {len(synthetic_cases)} 个完美的合成数据案例（V11.8大规模增兵）")
        logger.info(f"   - Special_Strong: {len(special_strong_cases)} 个")
        logger.info(f"   - Follower: {len(follower_cases)} 个")
        logger.info(f"   - Balanced: {len(balanced_cases)} 个")
        logger.info(f"   - Strong: {len(strong_cases)} 个")
        logger.info(f"   - Weak: {len(weak_cases)} 个")
        
        return synthetic_cases
    
    def _generate_special_strong_cases(self, count: int = 30) -> List[Dict]:
        """生成专旺格合成案例"""
        cases = []
        
        # 五行专旺格配置
        # 格式：(日主, 同党天干列表, 同党地支列表, 月令地支, 格局名称)
        special_configs = [
            # 木专旺（曲直仁寿格）
            ('甲', ['甲', '乙'], ['寅', '卯'], '寅', '曲直仁寿格-木专旺'),
            ('甲', ['甲', '甲'], ['寅', '寅'], '寅', '纯木专旺-寅月'),
            ('甲', ['甲', '乙', '甲'], ['寅', '卯', '寅'], '寅', '木专旺-三木'),
            ('乙', ['乙', '甲'], ['卯', '寅'], '卯', '木专旺-乙日'),
            ('乙', ['乙', '乙'], ['卯', '卯'], '卯', '纯木专旺-卯月'),
            
            # 火专旺（炎上格）
            ('丙', ['丙', '丁'], ['午', '巳'], '午', '炎上格-火专旺'),
            ('丙', ['丙', '丙'], ['午', '午'], '午', '纯火专旺-午月'),
            ('丙', ['甲', '丙', '丁'], ['寅', '午', '巳'], '午', '火专旺-三火'),
            ('丁', ['丁', '丙'], ['午', '巳'], '午', '火专旺-丁日'),
            ('丁', ['丁', '丁'], ['午', '午'], '午', '纯火专旺-丁日'),
            
            # 土专旺（稼穑格）
            ('戊', ['戊', '己'], ['戌', '未'], '戌', '稼穑格-土专旺'),
            ('戊', ['戊', '戊'], ['戌', '戌'], '戌', '纯土专旺-戌月'),
            ('戊', ['己', '戊', '己'], ['未', '戌', '未'], '戌', '土专旺-三土'),
            ('己', ['己', '戊'], ['未', '戌'], '未', '土专旺-己日'),
            ('己', ['己', '己'], ['未', '未'], '未', '纯土专旺-己日'),
            
            # 金专旺（从革格）
            ('庚', ['庚', '辛'], ['申', '酉'], '申', '从革格-金专旺'),
            ('庚', ['庚', '庚'], ['申', '申'], '申', '纯金专旺-申月'),
            ('庚', ['辛', '庚', '辛'], ['酉', '申', '酉'], '申', '金专旺-三金'),
            ('辛', ['辛', '庚'], ['酉', '申'], '酉', '金专旺-辛日'),
            ('辛', ['辛', '辛'], ['酉', '酉'], '酉', '纯金专旺-辛日'),
            
            # 水专旺（润下格）
            ('壬', ['壬', '癸'], ['子', '亥'], '子', '润下格-水专旺'),
            ('壬', ['壬', '壬'], ['子', '子'], '子', '纯水专旺-子月'),
            ('壬', ['癸', '壬', '癸'], ['亥', '子', '亥'], '子', '水专旺-三水'),
            ('癸', ['癸', '壬'], ['子', '亥'], '子', '水专旺-癸日'),
            ('癸', ['癸', '癸'], ['子', '子'], '子', '纯水专旺-癸日'),
            
            # 极端纯局（四柱同气）
            ('丙', ['丙', '丙'], ['午', '午'], '午', '四火专旺-极纯'),
            ('庚', ['庚', '庚'], ['申', '申'], '申', '四金专旺-极纯'),
            ('甲', ['甲', '甲'], ['寅', '寅'], '寅', '四木专旺-极纯'),
            ('壬', ['壬', '壬'], ['子', '子'], '子', '四水专旺-极纯'),
            ('戊', ['戊', '戊'], ['戌', '戌'], '戌', '四土专旺-极纯'),
        ]
        
        # V11.8: 扩展生成，支持循环生成更多变体
        generated = 0
        config_idx = 0
        while generated < count and len(special_configs) > 0:
            day_master, team_stems, team_branches, month_branch, pattern_name = special_configs[config_idx % len(special_configs)]
            case_id = f"SYNTHETIC_SPECIAL_STRONG_{generated+1:03d}"
            
            # V11.8: 为每个配置生成多个变体（通过改变年柱和时柱）
            variant_idx = generated // len(special_configs)
            if variant_idx > 0:
                # 生成变体：改变年柱和时柱的组合
                pattern_name = f"{pattern_name}-变体{variant_idx+1}"
            
            # 构建八字：年柱、月柱、日柱、时柱
            # 月柱：确保日主得月令
            month_stem = day_master  # 月干透日主，确保得令
            month_pillar = f"{month_stem}{month_branch}"
            
            # 年柱：同党
            year_stem = team_stems[0] if len(team_stems) > 0 else day_master
            year_branch = team_branches[0] if len(team_branches) > 0 else month_branch
            year_pillar = f"{year_stem}{year_branch}"
            
            # 日柱：日主 + 同党地支（确保天干地支匹配）
            day_branch = team_branches[1] if len(team_branches) > 1 else month_branch
            # 检查日支是否与日主同五行，如果不同，使用月支
            day_branch_element = BRANCH_ELEMENTS.get(day_branch, 'earth')
            day_master_element = STEM_ELEMENTS.get(day_master, 'earth')
            if day_branch_element != day_master_element and month_branch != day_branch:
                day_branch = month_branch  # 使用月支，确保匹配
            day_pillar = f"{day_master}{day_branch}"
            
            # 时柱：同党
            hour_stem = team_stems[1] if len(team_stems) > 1 else day_master
            hour_branch = team_branches[2] if len(team_branches) > 2 else month_branch
            hour_pillar = f"{hour_stem}{hour_branch}"
            
            bazi_list = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            # V11.9: 添加高斯噪声，增加合成数据多样性
            # 为strength_score和self_team_ratio添加微小随机扰动
            noise_strength = random.uniform(0, 5)  # 0-5的噪声
            noise_ratio = random.uniform(0, 0.05)  # 0-0.05的噪声
            
            cases.append({
                'id': case_id,
                'name': f'[合成] {pattern_name}',
                'bazi': bazi_list,
                'day_master': day_master,
                'gender': '男',
                'ground_truth': {'strength': 'Special_Strong'},
                'characteristics': f'[合成数据-专旺格] {pattern_name}：满盘同党，日主{day_master}生于{month_branch}月得令，符合专旺格特征',
                'synthetic': True,
                'synthetic_type': 'theoretical',
                'source': 'synthetic',
                'category': 'synthetic',
                'weight': 2.0,  # Synthetic权重2.0
                'verified': True,
                # V11.9: 噪声标记（用于特征提取时应用）
                'synthetic_noise': {
                    'strength_noise': noise_strength,  # 将在100的基础上减去
                    'ratio_noise': noise_ratio  # 将在1.0的基础上减去
                }
            })
            
            generated += 1
            config_idx = (config_idx + 1) % len(special_configs)
        
        return cases
    
    def _generate_follower_cases(self, count: int = 15) -> List[Dict]:
        """生成从格合成案例"""
        cases = []
        
        # 从格配置
        # 格式：(日主, 异党天干列表, 异党地支列表, 格局名称, 从格类型)
        follower_configs = [
            # 从财格（5个）
            ('庚', ['甲', '乙', '甲'], ['寅', '卯', '寅'], '从财格-木旺', 'wealth'),
            ('辛', ['甲', '乙'], ['寅', '卯'], '从财格-木旺', 'wealth'),
            ('戊', ['壬', '癸'], ['子', '亥'], '从财格-水旺', 'wealth'),
            ('己', ['壬', '癸', '壬'], ['子', '亥', '子'], '从财格-水旺', 'wealth'),
            ('甲', ['戊', '己'], ['戌', '未'], '从财格-土旺', 'wealth'),
            
            # 从杀格（5个）
            ('甲', ['庚', '辛', '庚'], ['申', '酉', '申'], '从杀格-金旺', 'officer'),
            ('乙', ['庚', '辛'], ['申', '酉'], '从杀格-金旺', 'officer'),
            ('丙', ['壬', '癸'], ['子', '亥'], '从杀格-水旺', 'officer'),
            ('丁', ['壬', '癸', '壬'], ['子', '亥', '子'], '从杀格-水旺', 'officer'),
            ('戊', ['甲', '乙'], ['寅', '卯'], '从杀格-木旺', 'officer'),
            
            # 从儿格（5个）
            ('甲', ['丙', '丁', '丙'], ['午', '巳', '午'], '从儿格-火旺', 'child'),
            ('乙', ['丙', '丁'], ['午', '巳'], '从儿格-火旺', 'child'),
            ('庚', ['壬', '癸'], ['子', '亥'], '从儿格-水旺', 'child'),
            ('辛', ['壬', '癸', '壬'], ['子', '亥', '子'], '从儿格-水旺', 'child'),
            ('壬', ['甲', '乙'], ['寅', '卯'], '从儿格-木旺', 'child'),
        ]
        
        # V11.8: 扩展生成，支持循环生成更多变体
        generated = 0
        config_idx = 0
        while generated < count and len(follower_configs) > 0:
            day_master, enemy_stems, enemy_branches, base_pattern_name, follower_type = follower_configs[config_idx % len(follower_configs)]
            variant_idx = generated // len(follower_configs)
            
            case_id = f"SYNTHETIC_FOLLOWER_{generated+1:03d}"
            pattern_name = f"{base_pattern_name}" if variant_idx == 0 else f"{base_pattern_name}-变体{variant_idx+1}"
            
            # 构建八字：日主极弱，满盘异党
            # 月柱：异党当令
            month_stem = enemy_stems[0]
            month_branch = enemy_branches[0]
            month_pillar = f"{month_stem}{month_branch}"
            
            # 年柱：异党
            year_stem = enemy_stems[0]
            year_branch = enemy_branches[0]
            year_pillar = f"{year_stem}{year_branch}"
            
            # 日柱：日主 + 异党地支（确保日主无根）
            day_branch = enemy_branches[1] if len(enemy_branches) > 1 else enemy_branches[0]
            day_pillar = f"{day_master}{day_branch}"
            
            # 时柱：异党
            hour_stem = enemy_stems[1] if len(enemy_stems) > 1 else enemy_stems[0]
            hour_branch = enemy_branches[2] if len(enemy_branches) > 2 else enemy_branches[0]
            hour_pillar = f"{hour_stem}{hour_branch}"
            
            bazi_list = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            cases.append({
                'id': case_id,
                'name': f'[合成] {pattern_name}',
                'bazi': bazi_list,
                'day_master': day_master,
                'gender': '男',
                'ground_truth': {'strength': 'Follower'},
                'characteristics': f'[合成数据-从格] {pattern_name}：日主{day_master}极弱无根，满盘异党，符合从格特征',
                'synthetic': True,
                'synthetic_type': 'theoretical',
                'source': 'synthetic',
                'category': 'synthetic',
                'weight': 2.0,  # Synthetic权重2.0
                'verified': True
            })
            
            generated += 1
            config_idx = (config_idx + 1) % len(follower_configs)
        
        return cases
    
    def _generate_balanced_cases(self, count: int = 5) -> List[Dict]:
        """生成中和格合成案例"""
        cases = []
        
        # 中和格配置：日主有生有克，能量相对平衡
        balanced_configs = [
            ('甲', '寅', '子', '寅', '中和格-木火平衡'),
            ('丙', '午', '子', '寅', '中和格-火水平衡'),
            ('戊', '戌', '寅', '申', '中和格-土金平衡'),
            ('庚', '申', '午', '子', '中和格-金火平衡'),
            ('壬', '子', '午', '寅', '中和格-水火平衡'),
        ]
        
        # V11.8: 扩展生成，支持循环生成更多变体
        generated = 0
        config_idx = 0
        while generated < count and len(balanced_configs) > 0:
            day_master, month_branch, year_branch, hour_branch, base_pattern_name = balanced_configs[config_idx % len(balanced_configs)]
            variant_idx = generated // len(balanced_configs)
            
            case_id = f"SYNTHETIC_BALANCED_{generated+1:03d}"
            pattern_name = f"{base_pattern_name}" if variant_idx == 0 else f"{base_pattern_name}-变体{variant_idx+1}"
            
            # 构建八字：生克平衡
            # 月柱：日主得令
            month_stem = day_master
            month_pillar = f"{month_stem}{month_branch}"
            
            # 年柱：生我的（印星）
            year_stem = self._get_resource_stem(day_master)
            year_pillar = f"{year_stem}{year_branch}"
            
            # 日柱：日主 + 平衡地支
            day_branch = month_branch
            day_pillar = f"{day_master}{day_branch}"
            
            # 时柱：克我的（官杀）或我克的（财星），形成平衡
            hour_stem = self._get_control_stem(day_master)
            hour_pillar = f"{hour_stem}{hour_branch}"
            
            bazi_list = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            cases.append({
                'id': case_id,
                'name': f'[合成] {pattern_name}',
                'bazi': bazi_list,
                'day_master': day_master,
                'gender': '男',
                'ground_truth': {'strength': 'Balanced'},
                'characteristics': f'[合成数据-中和格] {pattern_name}：日主{day_master}有生有克，能量相对平衡',
                'synthetic': True,
                'synthetic_type': 'theoretical',
                'source': 'synthetic',
                'category': 'synthetic',
                'weight': 2.0,  # Synthetic权重2.0
                'verified': True
            })
            
            generated += 1
            config_idx = (config_idx + 1) % len(balanced_configs)
        
        return cases
    
    def _get_resource_stem(self, day_master: str) -> str:
        """获取生我的天干（印星）"""
        # 生木者水，生火者木，生土者火，生金者土，生水者金
        resource_map = {
            '甲': '壬', '乙': '癸',  # 木被水生
            '丙': '甲', '丁': '乙',  # 火被木生
            '戊': '丙', '己': '丁',  # 土被火生
            '庚': '戊', '辛': '己',  # 金被土生
            '壬': '庚', '癸': '辛',  # 水被金生
        }
        return resource_map.get(day_master, '甲')
    
    def _get_control_stem(self, day_master: str) -> str:
        """获取克我的天干（官杀）"""
        # 克木者金，克火者水，克土者木，克金者火，克水者土
        control_map = {
            '甲': '庚', '乙': '辛',  # 木被金克
            '丙': '壬', '丁': '癸',  # 火被水克
            '戊': '甲', '己': '乙',  # 土被木克
            '庚': '丙', '辛': '丁',  # 金被火克
            '壬': '戊', '癸': '己',  # 水被土克
        }
        return control_map.get(day_master, '庚')
    
    def _generate_strong_cases(self, count: int = 10) -> List[Dict]:
        """生成身强合成案例（V11.8新增）"""
        cases = []
        
        # 身强配置：日主得令且有根，但未达到专旺
        strong_configs = [
            ('甲', '寅', '甲', '寅', '身强-木得令有根'),
            ('丙', '午', '丙', '午', '身强-火得令有根'),
            ('戊', '戌', '戊', '戌', '身强-土得令有根'),
            ('庚', '申', '庚', '申', '身强-金得令有根'),
            ('壬', '子', '壬', '子', '身强-水得令有根'),
            # 更多变体
            ('乙', '卯', '乙', '卯', '身强-木得令有根'),
            ('丁', '巳', '丁', '巳', '身强-火得令有根'),
            ('己', '未', '己', '未', '身强-土得令有根'),
            ('辛', '酉', '辛', '酉', '身强-金得令有根'),
            ('癸', '亥', '癸', '亥', '身强-水得令有根'),
        ]
        
        for idx, (day_master, month_branch, year_stem, hour_branch, pattern_name) in enumerate(strong_configs[:count]):
            case_id = f"SYNTHETIC_STRONG_{idx+1:03d}"
            
            # 构建八字：日主得令且有根
            month_stem = day_master
            month_pillar = f"{month_stem}{month_branch}"
            
            year_pillar = f"{year_stem}{month_branch}"
            day_pillar = f"{day_master}{month_branch}"
            hour_pillar = f"{day_master}{hour_branch}"
            
            bazi_list = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            cases.append({
                'id': case_id,
                'name': f'[合成] {pattern_name}',
                'bazi': bazi_list,
                'day_master': day_master,
                'gender': '男',
                'ground_truth': {'strength': 'Strong'},
                'characteristics': f'[合成数据-身强] {pattern_name}：日主{day_master}得令且有根，符合身强特征',
                'synthetic': True,
                'synthetic_type': 'theoretical',
                'source': 'synthetic',
                'category': 'synthetic',
                'weight': 2.0,
                'verified': True
            })
        
        return cases
    
    def _generate_weak_cases(self, count: int = 10) -> List[Dict]:
        """生成身弱合成案例（V11.8新增）"""
        cases = []
        
        # 身弱配置：日主失令且无根，但未达到从格
        weak_configs = [
            ('甲', '申', '庚', '申', '身弱-木失令无根'),
            ('丙', '子', '壬', '子', '身弱-火失令无根'),
            ('戊', '寅', '甲', '寅', '身弱-土失令无根'),
            ('庚', '午', '丙', '午', '身弱-金失令无根'),
            ('壬', '戌', '戊', '戌', '身弱-水失令无根'),
            # 更多变体
            ('乙', '酉', '辛', '酉', '身弱-木失令无根'),
            ('丁', '亥', '癸', '亥', '身弱-火失令无根'),
            ('己', '卯', '乙', '卯', '身弱-土失令无根'),
            ('辛', '巳', '丁', '巳', '身弱-金失令无根'),
            ('癸', '未', '己', '未', '身弱-水失令无根'),
        ]
        
        for idx, (day_master, month_branch, enemy_stem, hour_branch, pattern_name) in enumerate(weak_configs[:count]):
            case_id = f"SYNTHETIC_WEAK_{idx+1:03d}"
            
            # 构建八字：日主失令且无根
            month_stem = enemy_stem
            month_pillar = f"{month_stem}{month_branch}"
            
            year_pillar = f"{enemy_stem}{month_branch}"
            day_pillar = f"{day_master}{month_branch}"  # 日主坐失令地支
            hour_pillar = f"{enemy_stem}{hour_branch}"
            
            bazi_list = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            cases.append({
                'id': case_id,
                'name': f'[合成] {pattern_name}',
                'bazi': bazi_list,
                'day_master': day_master,
                'gender': '男',
                'ground_truth': {'strength': 'Weak'},
                'characteristics': f'[合成数据-身弱] {pattern_name}：日主{day_master}失令且无根，符合身弱特征',
                'synthetic': True,
                'synthetic_type': 'theoretical',
                'source': 'synthetic',
                'category': 'synthetic',
                'weight': 2.0,
                'verified': True
            })
        
        return cases


if __name__ == '__main__':
    """测试生成合成数据"""
    logging.basicConfig(level=logging.INFO)
    
    factory = SyntheticDataFactory()
    cases = factory.generate_perfect_cases(target_count=50)
    
    print(f"\n✅ 生成了 {len(cases)} 个合成案例")
    print(f"\n前5个案例示例：")
    for i, case in enumerate(cases[:5]):
        print(f"\n{i+1}. {case['name']}")
        print(f"   八字: {case['bazi']}")
        print(f"   日主: {case['day_master']}")
        print(f"   Ground Truth: {case['ground_truth']['strength']}")

