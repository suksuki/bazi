#!/usr/bin/env python3
"""
FDS-V1.4 Step 2: 全量海选与分层提纯（A-03 羊刃架杀）
遍历51.84万样本池，按照古典标签筛选，并进行纯度排序

执行标准：FDS-V1.4 Step 2
- 全量扫描：遍历51.84万样本池
- 奇点捕获：识别Tier X样本
- 纯度排序：截取前500名Tier A样本
"""

import sys
from pathlib import Path
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
from core.physics_engine import compute_energy_flux, check_clash, check_combination
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDSV14Step2Engine:
    """
    FDS-V1.4 Step 2 全量海选引擎
    遍历51.84万样本，按照A-03筛选条件进行海选
    """
    
    def __init__(self, pattern_id: str = 'A-03'):
        self.pattern_id = pattern_id
        self.engine = SyntheticBaziEngine()
        self.framework = QuantumUniversalFramework()
        self.yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        
        # A-03筛选条件（从registry获取）
        self.month_lock_required = True  # 月令锁：月支本气必须为日主之羊刃
        self.stem_reveal_required = True  # 天干透杀：天干必须透出七杀
        self.purity_filter = True  # 清纯度过滤
        
        logger.info(f"初始化FDS-V1.4 Step 2引擎: {pattern_id}")
    
    def generate_all_bazi_combinations(self):
        """
        生成所有八字组合（使用SyntheticBaziEngine）
        
        实际生成：518,400个组合
        - 年柱：60个（甲子循环）
        - 月柱：12个（受年柱影响，固定12个月）
        - 日柱：60个（独立循环）
        - 时柱：12个（受日柱影响，固定12个时辰）
        
        总计：60 * 12 * 60 * 12 = 518,400
        
        Returns:
            生成器，每次yield一个八字组合 [年柱, 月柱, 日柱, 时柱]
        """
        logger.info("生成所有八字组合（使用SyntheticBaziEngine）...")
        return self.engine.generate_all_bazi()
    
    def check_a03_criteria(self, chart: List[str], day_master: str) -> Tuple[bool, Dict[str, Any]]:
        """
        检查A-03筛选条件
        
        Args:
            chart: 四柱八字 ['年柱', '月柱', '日柱', '时柱']
            day_master: 日主
            
        Returns:
            (是否符合条件, 详细信息)
        """
        details = {
            'month_lock': False,
            'stem_reveal': False,
            'has_root': False,
            'purity_pass': True,
            'purity_reasons': []
        }
        
        # 1. 月令锁：月支本气必须为日主之羊刃
        month_branch = chart[1][1] if len(chart) > 1 and len(chart[1]) >= 2 else ""
        expected_blade = self.yang_ren_map.get(day_master)
        
        if expected_blade and month_branch == expected_blade:
            details['month_lock'] = True
        else:
            return False, details
        
        # 2. 天干透杀：天干必须透出七杀
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        
        has_kill = False
        kill_stem = None
        kill_pillar_idx = None
        
        for i, stem in enumerate(stems):
            if i == 2:  # 跳过日主
                continue
            ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
            if ten_god in ['七杀', '正官']:
                has_kill = True
                kill_stem = stem
                kill_pillar_idx = i
                break
        
        if not has_kill:
            return False, details
        
        details['stem_reveal'] = True
        
        # 3. 七杀必须有根（不可以是虚浮无力）
        has_root = False
        
        # 检查自坐
        if kill_pillar_idx < len(branches):
            branch = branches[kill_pillar_idx]
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            for hidden_stem, weight in hidden_stems:
                if hidden_stem == kill_stem and weight >= 5:  # 主气或中气
                    has_root = True
                    break
        
        # 检查其他地支
        if not has_root:
            for branch in branches:
                hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                for hidden_stem, weight in hidden_stems:
                    if hidden_stem == kill_stem and weight >= 5:
                        has_root = True
                        break
                if has_root:
                    break
        
        if not has_root:
            return False, details
        
        details['has_root'] = True
        
        # 4. 清纯度过滤
        # 剔除：重食伤制杀（这会变成A-02食神制杀）
        shi_shang_energy = compute_energy_flux(chart, day_master, "食神") + \
                          compute_energy_flux(chart, day_master, "伤官")
        qi_sha_energy = compute_energy_flux(chart, day_master, "七杀") + \
                       compute_energy_flux(chart, day_master, "正官")
        
        if shi_shang_energy > 0 and qi_sha_energy > 0:
            if shi_shang_energy / qi_sha_energy > 1.5:  # 食伤能量明显大于官杀
                details['purity_pass'] = False
                details['purity_reasons'].append("重食伤制杀")
        
        # 剔除：重财党杀（这会导致应力轴S爆表）
        cai_xing_energy = compute_energy_flux(chart, day_master, "正财") + \
                         compute_energy_flux(chart, day_master, "偏财")
        
        if cai_xing_energy > 0 and qi_sha_energy > 0:
            if cai_xing_energy / qi_sha_energy > 2.0:  # 财星能量明显大于官杀
                details['purity_pass'] = False
                details['purity_reasons'].append("重财党杀")
        
        if not details['purity_pass']:
            return False, details
        
        return True, details
    
    def calculate_purity_score(self, chart: List[str], day_master: str, details: Dict[str, Any]) -> float:
        """
        计算纯度分数
        
        加分：
        - 格局核心字有根 (+20)
        - 得令 (+10)
        - 通关有力 (+10)
        
        减分：
        - 混杂 (-15)
        - 刑冲破坏 (-10)
        - 党杀/耗能 (-15)
        """
        score = 0.0
        
        # 加分项
        # 1. 格局核心字有根（已在check_a03_criteria中检查）
        if details.get('has_root'):
            score += 20.0
        
        # 2. 得令（月令羊刃已在check_a03_criteria中检查）
        if details.get('month_lock'):
            score += 10.0
        
        # 3. 通关有力（印星能量）
        yin_xiao_energy = compute_energy_flux(chart, day_master, "正印") + \
                         compute_energy_flux(chart, day_master, "偏印")
        if yin_xiao_energy > 1.0:
            score += 10.0
        
        # 减分项
        # 1. 混杂（食伤、财星过多）
        shi_shang_energy = compute_energy_flux(chart, day_master, "食神") + \
                          compute_energy_flux(chart, day_master, "伤官")
        cai_xing_energy = compute_energy_flux(chart, day_master, "正财") + \
                         compute_energy_flux(chart, day_master, "偏财")
        
        if shi_shang_energy > 2.0 or cai_xing_energy > 2.0:
            score -= 15.0
        
        # 2. 刑冲破坏
        branches = [p[1] for p in chart]
        clash_count = 0
        for i, b1 in enumerate(branches):
            for j, b2 in enumerate(branches[i+1:], i+1):
                if check_clash(b1, b2):
                    clash_count += 1
        
        if clash_count > 0:
            score -= 10.0 * clash_count
        
        # 3. 党杀/耗能（已在purity_filter中处理，这里不再减分）
        
        return score
    
    def check_singularity(self, chart: List[str], day_master: str) -> Dict[str, Any]:
        """
        检查是否为Tier X（奇点）
        
        根据SVP（奇点判定法则）：
        1. 极值法则：关键物理参数偏离标准分布均值3σ以上
        2. 相变法则：物理属性发生态的突变
        3. 算法失效法则：标准算法结果与事实逻辑完全背离
        """
        singularity_protocol = {
            'law_of_extremum': False,
            'law_of_phase_change': False,
            'law_of_algorithm_failure': False,
            'sub_id': None,
            'reason': None
        }
        
        # 检查极值法则：地支三刃或更多
        expected_blade = self.yang_ren_map.get(day_master)
        if expected_blade:
            branches = [p[1] for p in chart]
            blade_count = branches.count(expected_blade)
            
            if blade_count >= 3:  # 三刃或更多
                singularity_protocol['law_of_extremum'] = True
                singularity_protocol['sub_id'] = 'A-03-X1'
                singularity_protocol['reason'] = f'地支{blade_count}刃（极值法则）'
                return singularity_protocol
        
        # 检查相变法则：七杀攻身无制
        qi_sha_energy = compute_energy_flux(chart, day_master, "七杀") + \
                       compute_energy_flux(chart, day_master, "正官")
        yin_xiao_energy = compute_energy_flux(chart, day_master, "正印") + \
                         compute_energy_flux(chart, day_master, "偏印")
        
        if qi_sha_energy > 3.0 and yin_xiao_energy < 0.5:  # 七杀极强且无印化
            singularity_protocol['law_of_phase_change'] = True
            singularity_protocol['sub_id'] = 'A-03-X2'
            singularity_protocol['reason'] = '七杀攻身无制（相变法则）'
            return singularity_protocol
        
        return singularity_protocol
    
    def step2_full_scan(self) -> Dict[str, Any]:
        """
        Step 2: 全量海选与分层提纯
        
        Returns:
            海选结果字典
        """
        logger.info("=" * 70)
        logger.info("Step 2: 全量海选与分层提纯（A-03 羊刃架杀）")
        logger.info("=" * 70)
        
        # 1. 生成所有八字组合（生成器）
        bazi_generator = self.generate_all_bazi_combinations()
        total = 518400  # 固定总数
        logger.info(f"总样本数: {total:,}")
        
        # 2. 全量扫描
        candidates = []
        tier_x_samples = []
        
        logger.info("开始全量扫描...")
        
        for i, chart in enumerate(tqdm(bazi_generator, total=total, desc="扫描进度")):
            day_master = chart[2][0]  # 日柱天干
            
            # 检查A-03筛选条件
            matches, details = self.check_a03_criteria(chart, day_master)
            
            if matches:
                # 计算纯度分数
                purity_score = self.calculate_purity_score(chart, day_master, details)
                
                # 检查是否为奇点
                singularity = self.check_singularity(chart, day_master)
                is_singularity = (singularity['law_of_extremum'] or 
                                 singularity['law_of_phase_change'] or 
                                 singularity['law_of_algorithm_failure'])
                
                sample_data = {
                    'chart': chart,
                    'day_master': day_master,
                    'purity_score': purity_score,
                    'details': details,
                    'singularity_protocol': singularity
                }
                
                if is_singularity:
                    tier_x_samples.append(sample_data)
                else:
                    candidates.append(sample_data)
            
            # 每10万样本输出一次进度
            if (i + 1) % 100000 == 0:
                logger.info(f"  进度: {i+1:,}/{total:,} ({(i+1)/total*100:.2f}%) - 候选: {len(candidates)}, 奇点: {len(tier_x_samples)}")
        
        logger.info(f"✅ 全量扫描完成")
        logger.info(f"  候选样本数: {len(candidates):,}")
        logger.info(f"  奇点样本数: {len(tier_x_samples):,}")
        
        # 3. 纯度排序
        candidates.sort(key=lambda x: x['purity_score'], reverse=True)
        
        # 4. 截取前500名Tier A样本
        tier_a_samples = candidates[:500]
        
        logger.info(f"✅ 纯度排序完成")
        logger.info(f"  Tier A样本数: {len(tier_a_samples)}")
        logger.info(f"  Tier X样本数: {len(tier_x_samples)}")
        
        return {
            'step': 2,
            'total_scanned': total,
            'candidates_count': len(candidates),
            'tier_a_count': len(tier_a_samples),
            'tier_x_count': len(tier_x_samples),
            'tier_a_samples': tier_a_samples,
            'tier_x_samples': tier_x_samples
        }
    
    def save_results(self, results: Dict[str, Any]) -> Path:
        """保存海选结果"""
        output_file = project_root / "data" / "holographic_pattern" / "A-03_Step2_FullScan_Results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 只保存关键信息，避免文件过大
        summary = {
            'pattern_id': self.pattern_id,
            'step': 2,
            'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fds_version': 'V1.4',
            'total_scanned': results['total_scanned'],
            'candidates_count': results['candidates_count'],
            'tier_a_count': results['tier_a_count'],
            'tier_x_count': results['tier_x_count'],
            'tier_a_samples': results['tier_a_samples'],
            'tier_x_samples': results['tier_x_samples']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 海选结果已保存: {output_file}")
        return output_file


def main():
    print("=" * 70)
    print("🚀 FDS-V1.4 Step 2: 全量海选与分层提纯（A-03 羊刃架杀）")
    print("=" * 70)
    print()
    print("⚠️  警告：此脚本将遍历所有八字组合（约260万），可能需要较长时间")
    print()
    
    engine = FDSV14Step2Engine('A-03')
    
    # 执行Step 2
    results = engine.step2_full_scan()
    
    # 保存结果
    output_file = engine.save_results(results)
    
    print()
    print("=" * 70)
    print("✅ Step 2 全量海选完成")
    print("=" * 70)
    print()
    print("【海选结果摘要】")
    print("-" * 70)
    print(f"总扫描样本数: {results['total_scanned']:,}")
    print(f"候选样本数: {results['candidates_count']:,}")
    print(f"Tier A样本数: {results['tier_a_count']}")
    print(f"Tier X样本数: {results['tier_x_count']}")
    print()
    print(f"✅ 结果已保存: {output_file}")
    print()
    print("【下一步】")
    print("-" * 70)
    print("执行Step 3，使用transfer_matrix重新计算质心：")
    print("  python3 scripts/fds_v14_refit_a03_v21.py")
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()

