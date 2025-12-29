#!/usr/bin/env python3
"""
测试脚本：A-03 羊刃架杀
1. 五维张量投影计算
2. 样本海选（500例）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController
import json

def test_tensor_projection():
    """测试1：五维张量投影计算"""
    print("=" * 70)
    print("测试1：五维张量投影计算")
    print("=" * 70)
    print()
    
    controller = HolographicPatternController()
    
    # 测试用例：甲日卯月，透庚金七杀（符合A-03格局）
    test_chart = ['甲子', '丁卯', '甲寅', '庚午']
    day_master = '甲'
    
    print(f"测试八字: {test_chart}")
    print(f"日主: {day_master}")
    print()
    
    result = controller.calculate_tensor_projection(
        pattern_id='A-03',
        chart=test_chart,
        day_master=day_master
    )
    
    if 'error' in result:
        print(f"❌ 错误: {result['error']}")
        return
    
    print("✅ 计算成功")
    print()
    print("【结果】")
    print("-" * 70)
    print(f"格局: {result['pattern_name']} ({result['pattern_id']})")
    print(f"SAI: {result['sai']:.4f}")
    print()
    print("五维投影:")
    projection = result['projection']
    for dim, value in projection.items():
        dim_name = {
            'E': '能级轴',
            'O': '秩序轴',
            'M': '物质轴',
            'S': '应力轴',
            'R': '关联轴'
        }.get(dim, dim)
        print(f"  {dim_name} ({dim}): {value:.4f}")
    print()
    print("权重:")
    weights = result['weights']
    for dim, weight in weights.items():
        dim_name = {
            'E': '能级轴',
            'O': '秩序轴',
            'M': '物质轴',
            'S': '应力轴',
            'R': '关联轴'
        }.get(dim, dim)
        print(f"  {dim_name} ({dim}): {weight}")
    print()

def test_sample_selection():
    """测试2：样本海选（500例）"""
    print("=" * 70)
    print("测试2：样本海选（按照FDS-V1.1 Step 2标准）")
    print("=" * 70)
    print()
    
    controller = HolographicPatternController()
    
    def progress_callback(current, total, stats):
        if current % 10000 == 0:
            pct = (current / total) * 100
            print(f"进度: {current:,}/{total:,} ({pct:.2f}%) | "
                  f"匹配: {stats['matched']} | "
                  f"月令拒绝: {stats['rejected_month_lock']} | "
                  f"透杀拒绝: {stats['rejected_stem_reveal']} | "
                  f"纯度拒绝: {stats['rejected_purity']}")
    
    print("开始样本海选...")
    print("目标: 500例")
    print()
    
    candidates = controller.select_samples(
        pattern_id='A-03',
        target_count=500,
        progress_callback=progress_callback
    )
    
    print()
    print("=" * 70)
    print(f"✅ 样本海选完成：找到 {len(candidates)} 个样本")
    print("=" * 70)
    print()
    
    # 显示前5个样本
    print("【前5个样本示例】")
    print("-" * 70)
    for i, sample in enumerate(candidates[:5], 1):
        chart = sample['chart']
        print(f"{i}. {chart[0]} {chart[1]} {chart[2]} {chart[3]} | "
              f"日主: {sample['day_master']} | "
              f"月支: {sample['month_branch']} | "
              f"七杀: {', '.join(sample['qi_sha_stems'])}")
    print()
    
    # 保存结果
    output_file = project_root / "data" / "holographic_pattern_a03_samples.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pattern_id': 'A-03',
            'pattern_name': '羊刃架杀',
            'total_samples': len(candidates),
            'samples': candidates
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 样本已保存到: {output_file}")
    print()

if __name__ == '__main__':
    print()
    print("=" * 70)
    print("🧪 A-03 羊刃架杀功能测试")
    print("=" * 70)
    print()
    
    # 测试1：五维张量投影计算
    try:
        test_tensor_projection()
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 测试2：样本海选
    try:
        test_sample_selection()
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

