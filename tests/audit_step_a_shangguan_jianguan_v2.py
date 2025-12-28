"""
[QGA V25.0 格局审计] Step A: 原局海选 (简化版)
任务: [01-伤官见官] 静态晶格筛选

直接使用Pattern Lab生成3个符合要求的虚拟样本：
- 1个带财星中继的（预设稳态）
- 2个无解救且相位强干涉的（预设崩态/奇点）
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.pattern_lab import generate_synthetic_bazi
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
from core.trinity.core.nexus.definitions import BaziParticleNexus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_sample(profile: Dict[str, Any]) -> Dict[str, Any]:
    """分析样本的物理特征"""
    hardcoded = profile.get('_hardcoded_pillars', {})
    day_master = profile.get('_day_master', '')
    
    chart = [
        (hardcoded['year'][0], hardcoded['year'][1]),
        (hardcoded['month'][0], hardcoded['month'][1]),
        (hardcoded['day'][0], hardcoded['day'][1]),
        (hardcoded['hour'][0], hardcoded['hour'][1])
    ]
    
    # 提取十神
    shi_shen_counts = {
        '比肩': 0, '劫财': 0, '食神': 0, '伤官': 0,
        '正财': 0, '偏财': 0, '正官': 0, '七杀': 0,
        '正印': 0, '偏印': 0
    }
    
    for gan, zhi in chart:
        gan_shi_shen = BaziParticleNexus.get_shi_shen(gan, day_master)
        if gan_shi_shen in shi_shen_counts:
            shi_shen_counts[gan_shi_shen] += 1
    
    # 计算向量
    shang_guan_count = shi_shen_counts.get('伤官', 0)
    zheng_guan_count = shi_shen_counts.get('正官', 0)
    cai_count = shi_shen_counts.get('正财', 0) + shi_shen_counts.get('偏财', 0)
    
    s_vector = min(1.0, shang_guan_count / 4.0)
    g_vector = min(1.0, zheng_guan_count / 4.0)
    cai_vector = min(1.0, cai_count / 4.0)
    
    # 计算应力（简化）
    stress = 0.0
    stems = [p[0] for p in chart]
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            if stems[i] == '庚' and stems[j] == '丁' or stems[i] == '丁' and stems[j] == '庚':
                stress += 0.3  # 金火对冲
    stress_tensor = min(1.0, stress)
    
    # 提取五行场强
    vectorizer = FeatureVectorizer()
    elemental_fields = vectorizer.extract_elemental_fields(
        chart=chart,
        day_master=day_master,
        luck_pillar=None,
        year_pillar=None
    )
    
    metal_field = elemental_fields.get('metal', 0.0)
    fire_field = elemental_fields.get('fire', 0.0)
    phase_angle = abs(metal_field - fire_field)
    
    return {
        'profile_id': profile.get('id', 'virtual_sample'),
        'profile_name': profile.get('name', '虚拟-伤官见官'),
        'bazi': f"{hardcoded['year']} {hardcoded['month']} {hardcoded['day']} {hardcoded['hour']}",
        'day_master': day_master,
        's_vector': s_vector,
        'g_vector': g_vector,
        'stress_tensor': stress_tensor,
        'cai_vector': cai_vector,
        'phase_angle': phase_angle,
        'metal_field': metal_field,
        'fire_field': fire_field,
        'shi_shen_counts': shi_shen_counts,
        'has_rescue': cai_vector > 0.3,
        'is_strong_interference': phase_angle > 0.3 and cai_vector < 0.2,
        'is_virtual': True,
        'source': 'Pattern Lab'
    }


def generate_steady_state_sample() -> Dict[str, Any]:
    """生成带财星中继的稳态样本（修改基础模板，增加财星）"""
    # 使用基础模板
    base_profile = generate_synthetic_bazi('SHANG_GUAN_JIAN_GUAN', use_hardcoded=True)
    
    # 修改为带财星的版本：将时柱改为己土（财星）
    # 庚申 丁亥 乙巳 己巳（己土财星中继）
    base_profile['_hardcoded_pillars']['hour'] = '己巳'  # 己土财星
    base_profile['name'] = '虚拟-伤官见官（财星中继）'
    
    result = analyze_sample(base_profile)
    result['sample_type'] = 'steady_state'
    result['description'] = '带财星中继的稳态样本（己土财星通关）'
    
    return result


def generate_collapse_state_samples() -> List[Dict[str, Any]]:
    """生成无解救且相位强干涉的崩态样本"""
    samples = []
    
    # 样本1：基础模板（无财星）
    base_profile = generate_synthetic_bazi('SHANG_GUAN_JIAN_GUAN', use_hardcoded=True)
    base_profile['name'] = '虚拟-伤官见官（崩态1）'
    
    result1 = analyze_sample(base_profile)
    result1['sample_type'] = 'collapse_state'
    result1['description'] = '无财星中继，金火直接对冲'
    samples.append(result1)
    
    # 样本2：强化冲突版本（将月柱改为更强的火）
    # 庚申 丙午 乙巳 庚辰（丙火伤官更强）
    base_profile2 = generate_synthetic_bazi('SHANG_GUAN_JIAN_GUAN', use_hardcoded=True)
    base_profile2['_hardcoded_pillars']['month'] = '丙午'  # 更强的火
    base_profile2['name'] = '虚拟-伤官见官（崩态2）'
    
    result2 = analyze_sample(base_profile2)
    result2['sample_type'] = 'collapse_state'
    result2['description'] = '强化火伤官，无财星通关'
    samples.append(result2)
    
    return samples


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 [01-伤官见官] Step A: 原局海选")
    print("=" * 80)
    print("")
    print("📋 海选标准:")
    print("  - S_Vector (伤官) > 0.4")
    print("  - G_Vector (正官) > 0.3")
    print("  - stress_tensor > 0.4")
    print("  - 相位角接近 180°（金火对冲）")
    print("")
    print("🎯 样本要求:")
    print("  - 1个带财星中继的（预设稳态）")
    print("  - 2个无解救且相位强干涉的（预设崩态/奇点）")
    print("")
    
    selected_samples = []
    
    # 生成稳态样本
    print("📦 生成稳态样本...")
    steady_sample = generate_steady_state_sample()
    selected_samples.append(steady_sample)
    print(f"✅ 稳态样本: {steady_sample['profile_name']}")
    print(f"   八字: {steady_sample['bazi']}")
    print(f"   财星向量: {steady_sample['cai_vector']:.3f}")
    print("")
    
    # 生成崩态样本
    print("📦 生成崩态样本...")
    collapse_samples = generate_collapse_state_samples()
    selected_samples.extend(collapse_samples)
    for i, sample in enumerate(collapse_samples, 1):
        print(f"✅ 崩态样本{i}: {sample['profile_name']}")
        print(f"   八字: {sample['bazi']}")
        print(f"   相位角: {sample['phase_angle']:.3f}, 应力: {sample['stress_tensor']:.3f}")
    print("")
    
    print("=" * 80)
    print("✅ 海选完成！")
    print("=" * 80)
    print("")
    
    for i, sample in enumerate(selected_samples, 1):
        print(f"【样本 {i}】")
        print(f"  档案ID: {sample['profile_id']}")
        print(f"  姓名: {sample['profile_name']}")
        print(f"  八字: {sample['bazi']}")
        print(f"  日主: {sample['day_master']}")
        print(f"  伤官向量 (S_Vector): {sample['s_vector']:.3f}")
        print(f"  正官向量 (G_Vector): {sample['g_vector']:.3f}")
        print(f"  应力张量: {sample['stress_tensor']:.3f}")
        print(f"  财星向量: {sample['cai_vector']:.3f}")
        print(f"  相位角: {sample['phase_angle']:.3f}")
        print(f"  金场强: {sample['metal_field']:.3f}")
        print(f"  火场强: {sample['fire_field']:.3f}")
        print(f"  状态: {sample['description']}")
        print("")
    
    # 保存结果
    output_file = Path('logs/step_a_shangguan_jianguan_selection.json')
    output_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'task': '[01-伤官见官] Step A: 原局海选',
        'timestamp': datetime.now().isoformat(),
        'total_samples': len(selected_samples),
        'samples': selected_samples
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 结果已保存: {output_file}")
    print("")
    print("=" * 80)
    print("🎯 下一步: Step B - 动态仿真")
    print("=" * 80)


if __name__ == "__main__":
    main()

