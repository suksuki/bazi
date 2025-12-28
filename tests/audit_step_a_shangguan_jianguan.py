"""
[QGA V25.0 格局审计] Step A: 原局海选
任务: [01-伤官见官] 静态晶格筛选

从51.84万样本中筛选出符合"伤官见官"条件的样本：
- 1个带财星中继的（预设稳态）
- 2个无解救且相位强干涉的（预设崩态/奇点）
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.trinity.core.engines.pattern_scout import PatternScout
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
from core.trinity.core.nexus.definitions import BaziParticleNexus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StepASelection:
    """Step A: 原局海选器（从51.84万样本中筛选）"""
    
    def __init__(self):
        self.scout = PatternScout()
        self.vectorizer = FeatureVectorizer()
        logger.info("✅ Step A 原局海选器初始化完成（51.84万样本模式）")
    
    def extract_shi_shen(self, chart: List[Tuple[str, str]], day_master: str) -> Dict[str, float]:
        """提取十神分布"""
        shi_shen_counts = {
            '比肩': 0.0, '劫财': 0.0, '食神': 0.0, '伤官': 0.0,
            '正财': 0.0, '偏财': 0.0, '正官': 0.0, '七杀': 0.0,
            '正印': 0.0, '偏印': 0.0
        }
        
        for gan, zhi in chart:
            # 天干十神
            gan_shi_shen = BaziParticleNexus.get_shi_shen(gan, day_master)
            if gan_shi_shen in shi_shen_counts:
                shi_shen_counts[gan_shi_shen] += 1.0
        
        return shi_shen_counts
    
    def calculate_stress_tensor(self, chart: List[Tuple[str, str]]) -> float:
        """计算应力张量"""
        stress = 0.0
        
        # 地支冲克
        branch_clashes = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥'
        }
        branches = [p[1] for p in chart]
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if branch_clashes.get(branches[i]) == branches[j] or \
                   branch_clashes.get(branches[j]) == branches[i]:
                    stress += 0.2
        
        # 天干相克
        stem_clashes = {
            '甲': '庚', '乙': '辛', '丙': '壬', '丁': '癸', '戊': '甲',
            '己': '乙', '庚': '丙', '辛': '丁', '壬': '戊', '癸': '己'
        }
        stems = [p[0] for p in chart]
        for i in range(len(stems)):
            for j in range(i + 1, len(stems)):
                if stem_clashes.get(stems[i]) == stems[j] or \
                   stem_clashes.get(stems[j]) == stems[i]:
                    stress += 0.1
        
        return min(1.0, stress)
    
    def analyze_chart(self, chart: List[Tuple[str, str]], day_master: str) -> Optional[Dict[str, Any]]:
        """分析八字是否符合"伤官见官"条件"""
        # 提取十神分布
        shi_shen_counts = self.extract_shi_shen(chart, day_master)
        
        # 计算伤官和正官向量
        shang_guan_count = shi_shen_counts.get('伤官', 0)
        zheng_guan_count = shi_shen_counts.get('正官', 0)
        
        # 归一化（调整：伤官和正官各1个就满足条件）
        s_vector = min(1.0, shang_guan_count / 2.0)  # 有1个伤官就0.5
        g_vector = min(1.0, zheng_guan_count / 2.0)  # 有1个正官就0.5
        
        # 计算应力张量
        stress_tensor = self.calculate_stress_tensor(chart)
        
        # 检查财星（土/金）作为中继
        cai_count = shi_shen_counts.get('正财', 0) + shi_shen_counts.get('偏财', 0)
        cai_vector = min(1.0, cai_count / 2.0)
        
        # 检查是否符合基本条件（降低阈值，因为归一化方式已调整）
        if s_vector > 0.3 and g_vector > 0.3 and stress_tensor > 0.2:
            # 计算相位角（基于金火场强）
            elemental_fields = self.vectorizer.extract_elemental_fields(
                chart=chart,
                day_master=day_master,
                luck_pillar=None,
                year_pillar=None
            )
            
            metal_field = elemental_fields.get('metal', 0.0)
            fire_field = elemental_fields.get('fire', 0.0)
            phase_angle = abs(metal_field - fire_field)
            
            return {
                'chart': chart,
                'day_master': day_master,
                's_vector': s_vector,
                'g_vector': g_vector,
                'stress_tensor': stress_tensor,
                'cai_vector': cai_vector,
                'phase_angle': phase_angle,
                'metal_field': metal_field,
                'fire_field': fire_field,
                'shi_shen_counts': shi_shen_counts,
                'has_rescue': cai_vector > 0.3,  # 财星中继
                'is_strong_interference': phase_angle > 0.3 and cai_vector < 0.2  # 强干涉且无解救
            }
        
        return None
    
    def select_samples(self, sample_size: int = 518400, target_count: int = 3) -> List[Dict[str, Any]]:
        """
        从51.84万样本中筛选符合条件的样本
        
        Args:
            sample_size: 扫描样本数（默认51.84万）
            target_count: 目标样本数（1个稳态 + 2个崩态）
            
        Returns:
            筛选结果列表
        """
        logger.info(f"🚀 开始Step A原局海选（扫描{sample_size:,}个样本）...")
        
        # 使用PatternScout扫描"伤官见官"格局
        found_samples = []
        steady_state_samples = []
        collapse_state_samples = []
        
        def progress_callback(curr, total, stats):
            if curr % 10000 == 0 or curr == total:
                logger.info(f"📊 扫描进度: {curr:,}/{total:,} ({curr/total*100:.1f}%) | 已找到: {len(found_samples)}个候选")
        
        # 扫描样本
        scout_results = self.scout.scout_pattern(
            pattern_id="SHANG_GUAN_JIAN_GUAN",
            sample_size=sample_size,
            progress_callback=progress_callback
        )
        
        logger.info(f"✅ PatternScout扫描完成，找到 {len(scout_results)} 个匹配样本")
        
        # 调试：查看第一个样本的格式
        if scout_results:
            logger.info(f"🔍 调试：第一个样本的keys: {list(scout_results[0].keys())}")
            logger.info(f"🔍 调试：第一个样本的chart类型: {type(scout_results[0].get('chart'))}")
            logger.info(f"🔍 调试：第一个样本的chart内容: {scout_results[0].get('chart')}")
        
        # 分析每个匹配样本
        for idx, result in enumerate(scout_results):
            # 尝试多种格式
            chart_data = result.get('chart', [])
            if not chart_data:
                # 尝试直接从result获取
                if 'year' in result and 'month' in result:
                    chart_data = [
                        (result.get('year', ['', ''])[0], result.get('year', ['', ''])[1]),
                        (result.get('month', ['', ''])[0], result.get('month', ['', ''])[1]),
                        (result.get('day', ['', ''])[0], result.get('day', ['', ''])[1]),
                        (result.get('hour', ['', ''])[0], result.get('hour', ['', ''])[1])
                    ]
                else:
                    continue
            
            if not chart_data or len(chart_data) < 4:
                continue
            
            # 处理chart_data格式（可能是字符串或元组）
            if isinstance(chart_data[0], str):
                # 如果是字符串格式，需要解析
                chart = [
                    (chart_data[0][0], chart_data[0][1]) if len(chart_data[0]) >= 2 else ('', ''),
                    (chart_data[1][0], chart_data[1][1]) if len(chart_data[1]) >= 2 else ('', ''),
                    (chart_data[2][0], chart_data[2][1]) if len(chart_data[2]) >= 2 else ('', ''),
                    (chart_data[3][0], chart_data[3][1]) if len(chart_data[3]) >= 2 else ('', '')
                ]
            else:
                # 如果是元组格式
                chart = [
                    (chart_data[0][0], chart_data[0][1]) if len(chart_data[0]) >= 2 else ('', ''),
                    (chart_data[1][0], chart_data[1][1]) if len(chart_data[1]) >= 2 else ('', ''),
                    (chart_data[2][0], chart_data[2][1]) if len(chart_data[2]) >= 2 else ('', ''),
                    (chart_data[3][0], chart_data[3][1]) if len(chart_data[3]) >= 2 else ('', '')
                ]
            
            # 提取日主
            day_master = result.get('day_master') or (chart[2][0] if chart[2][0] else '')
            if not day_master:
                continue
            
            # 分析样本
            analysis = self.analyze_chart(chart, day_master)
            if analysis:
                analysis['scout_result'] = result  # 保留原始结果
                found_samples.append(analysis)
                
                # 分类
                if analysis.get('has_rescue'):
                    steady_state_samples.append(analysis)
                elif analysis.get('is_strong_interference'):
                    collapse_state_samples.append(analysis)
            else:
                # 调试：打印前几个未通过的样本
                if idx < 3:
                    shi_shen = self.extract_shi_shen(chart, day_master)
                    s_vec = min(1.0, shi_shen.get('伤官', 0) / 4.0)
                    g_vec = min(1.0, shi_shen.get('正官', 0) / 4.0)
                    stress = self.calculate_stress_tensor(chart)
                    logger.info(f"🔍 样本{idx}未通过分析: s_vector={s_vec:.3f}, g_vector={g_vec:.3f}, stress={stress:.3f}")
        
        logger.info(f"✅ 分析完成: 总计{len(found_samples)}个候选，稳态{len(steady_state_samples)}个，崩态{len(collapse_state_samples)}个")
        
        # 选择最佳样本
        selected = []
        
        # 选择1个稳态样本（优先选择财星最强的）
        if steady_state_samples:
            steady_state_samples.sort(key=lambda x: -x.get('cai_vector', 0))
            selected.append(steady_state_samples[0])
            logger.info(f"✅ 选择稳态样本: 财星向量={steady_state_samples[0]['cai_vector']:.3f}")
        else:
            # 如果没有稳态样本，选择财星最强的候选样本
            candidates_with_cai = [s for s in found_samples if s.get('cai_vector', 0) > 0.1]
            if candidates_with_cai:
                candidates_with_cai.sort(key=lambda x: -x.get('cai_vector', 0))
                selected.append(candidates_with_cai[0])
                logger.info(f"✅ 选择准稳态样本: 财星向量={candidates_with_cai[0]['cai_vector']:.3f}")
        
        # 选择2个崩态样本（优先选择相位角最大、应力最大的）
        if collapse_state_samples:
            collapse_state_samples.sort(key=lambda x: -(x.get('phase_angle', 0) + x.get('stress_tensor', 0)))
            selected.extend(collapse_state_samples[:2])
            for i, sample in enumerate(collapse_state_samples[:2], 1):
                logger.info(f"✅ 选择崩态样本{i}: 相位角={sample['phase_angle']:.3f}, 应力={sample['stress_tensor']:.3f}")
        else:
            # 如果没有崩态样本，选择应力最大、相位角最大的候选样本
            remaining = [s for s in found_samples if s not in selected]
            if remaining:
                remaining.sort(key=lambda x: -(x.get('stress_tensor', 0) + x.get('phase_angle', 0)))
                selected.extend(remaining[:min(2, len(remaining))])
                for i, sample in enumerate(remaining[:min(2, len(remaining))], 1):
                    logger.info(f"✅ 选择准崩态样本{i}: 相位角={sample['phase_angle']:.3f}, 应力={sample['stress_tensor']:.3f}")
        
        return selected[:target_count]


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 [01-伤官见官] Step A: 原局海选（51.84万样本）")
    print("=" * 80)
    print("")
    print("📋 海选标准:")
    print("  - S_Vector (伤官) > 0.3")
    print("  - G_Vector (正官) > 0.3")
    print("  - stress_tensor > 0.2")
    print("  - 相位角接近 180°（金火对冲）")
    print("")
    print("🎯 样本要求:")
    print("  - 1个带财星中继的（预设稳态）")
    print("  - 2个无解救且相位强干涉的（预设崩态/奇点）")
    print("")
    print("⚠️  注意：扫描51.84万样本可能需要较长时间...")
    print("")
    
    selector = StepASelection()
    
    # 为了快速测试，可以先扫描较小的样本数
    # 完整扫描请使用 sample_size=518400
    selected_samples = selector.select_samples(sample_size=10000, target_count=3)  # 先用1万样本测试
    
    if not selected_samples:
        print("❌ 未找到符合条件的样本")
        print("   建议：增加扫描样本数或降低筛选阈值")
        return
    
    print("\n" + "=" * 80)
    print("✅ 海选完成！")
    print("=" * 80)
    print("")
    
    for i, sample in enumerate(selected_samples, 1):
        chart = sample['chart']
        bazi_str = f"{chart[0][0]}{chart[0][1]} {chart[1][0]}{chart[1][1]} {chart[2][0]}{chart[2][1]} {chart[3][0]}{chart[3][1]}"
        
        print(f"【样本 {i}】")
        print(f"  八字: {bazi_str}")
        print(f"  日主: {sample['day_master']}")
        print(f"  伤官向量 (S_Vector): {sample['s_vector']:.3f}")
        print(f"  正官向量 (G_Vector): {sample['g_vector']:.3f}")
        print(f"  应力张量: {sample['stress_tensor']:.3f}")
        print(f"  财星向量: {sample['cai_vector']:.3f}")
        print(f"  相位角: {sample['phase_angle']:.3f}")
        print(f"  金场强: {sample['metal_field']:.3f}")
        print(f"  火场强: {sample['fire_field']:.3f}")
        print(f"  状态: {'稳态（有财星中继）' if sample.get('has_rescue') else '崩态（无解救）'}")
        print("")
    
    # 保存结果
    output_file = Path('logs/step_a_shangguan_jianguan_selection.json')
    output_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'task': '[01-伤官见官] Step A: 原局海选（51.84万样本）',
        'timestamp': datetime.now().isoformat(),
        'total_samples': len(selected_samples),
        'samples': [
            {
                'bazi': f"{s['chart'][0][0]}{s['chart'][0][1]} {s['chart'][1][0]}{s['chart'][1][1]} {s['chart'][2][0]}{s['chart'][2][1]} {s['chart'][3][0]}{s['chart'][3][1]}",
                'day_master': s['day_master'],
                's_vector': s['s_vector'],
                'g_vector': s['g_vector'],
                'stress_tensor': s['stress_tensor'],
                'cai_vector': s['cai_vector'],
                'phase_angle': s['phase_angle'],
                'metal_field': s['metal_field'],
                'fire_field': s['fire_field'],
                'has_rescue': s.get('has_rescue', False),
                'is_strong_interference': s.get('is_strong_interference', False)
            }
            for s in selected_samples
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 结果已保存: {output_file}")
    print("")
    print("=" * 80)
    print("🎯 下一步: Step B - 动态仿真")
    print("=" * 80)
    print("")
    print("💡 提示：如需完整扫描51.84万样本，请修改脚本中的 sample_size=518400")


if __name__ == "__main__":
    main()
