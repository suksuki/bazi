#!/usr/bin/env python3
"""
Step 6 格局识别 - 盲测 (Blind Fire Test)
测试pattern_recognition函数的实战能力

基于AI设计师指令执行
"""

import sys
from pathlib import Path
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import tensor_normalize, calculate_cosine_similarity


def blind_fire_test():
    """
    执行盲测：对两个模拟向量进行格局识别
    """
    loader = RegistryLoader()
    
    print("=" * 70)
    print("🎯 Step 6 格局识别 - 盲测 (Blind Fire Test)")
    print("=" * 70)
    print()
    
    # 获取A-03的feature_anchors作为参考
    pattern = loader.get_pattern('A-03')
    fa = pattern.get('feature_anchors', {})
    sc = fa.get('standard_centroid', {})
    standard_vec = sc.get('vector', {})
    
    print("【参考：A-03标准质心】")
    print(f"  {standard_vec}")
    print()
    
    # Case Alpha: 模拟标准A-03
    print("=" * 70)
    print("📊 Case Alpha: 模拟标准A-03")
    print("=" * 70)
    case_alpha_raw = {'E': 0.40, 'O': 0.32, 'M': 0.05, 'S': 0.18, 'R': 0.05}
    case_alpha = tensor_normalize(case_alpha_raw)  # 确保归一化
    print(f"输入向量: {case_alpha_raw}")
    print(f"归一化后: {case_alpha}")
    print()
    
    # 计算与标准质心的相似度（用于对比）
    sim_alpha_standard = calculate_cosine_similarity(case_alpha, standard_vec)
    print(f"与标准质心相似度: {sim_alpha_standard:.6f}")
    print()
    
    # 执行格局识别
    result_alpha = loader.pattern_recognition(case_alpha, 'A-03')
    print("【识别结果】")
    print(json.dumps(result_alpha, ensure_ascii=False, indent=2))
    print()
    
    # Case Beta: 模拟普通身强/非A-03
    print("=" * 70)
    print("📊 Case Beta: 模拟普通身强/非A-03")
    print("=" * 70)
    case_beta_raw = {'E': 0.45, 'O': 0.10, 'M': 0.35, 'S': 0.05, 'R': 0.05}
    case_beta = tensor_normalize(case_beta_raw)  # 确保归一化
    print(f"输入向量: {case_beta_raw}")
    print(f"归一化后: {case_beta}")
    print()
    
    # 计算与标准质心的相似度（用于对比）
    sim_beta_standard = calculate_cosine_similarity(case_beta, standard_vec)
    print(f"与标准质心相似度: {sim_beta_standard:.6f}")
    print()
    
    # 执行格局识别
    result_beta = loader.pattern_recognition(case_beta, 'A-03')
    print("【识别结果】")
    print(json.dumps(result_beta, ensure_ascii=False, indent=2))
    print()
    
    # 总结分析
    print("=" * 70)
    print("📋 盲测结果总结")
    print("=" * 70)
    print()
    print("【Case Alpha (模拟标准A-03)】")
    print(f"  ✅ 匹配状态: {result_alpha['matched']}")
    print(f"  ✅ 格局类型: {result_alpha['pattern_type']}")
    print(f"  ✅ 相似度: {result_alpha['similarity']:.6f}")
    print(f"  ✅ 锚点ID: {result_alpha['anchor_id']}")
    print(f"  ✅ 共振态: {result_alpha['resonance']}")
    alpha_success = result_alpha['matched'] and result_alpha['pattern_type'] == 'STANDARD'
    print(f"  ✅ 判定: {'✅ 成功识别为A-03' if alpha_success else '❌ 识别失败'}")
    print()
    
    print("【Case Beta (模拟普通身强/非A-03)】")
    print(f"  ✅ 匹配状态: {result_beta['matched']}")
    print(f"  ✅ 格局类型: {result_beta['pattern_type']}")
    print(f"  ✅ 相似度: {result_beta['similarity']:.6f}")
    print(f"  ✅ 锚点ID: {result_beta['anchor_id']}")
    beta_success = not result_beta['matched'] or result_beta['pattern_type'] in ['BROKEN', 'MARGINAL']
    print(f"  ✅ 判定: {'✅ 正确排除（未匹配A-03）' if beta_success else '❌ 误判（应该排除但被识别）'}")
    print()
    
    # 最终判定
    print("=" * 70)
    if alpha_success and beta_success:
        print("✅ 盲测通过！格局识别功能正常工作")
    else:
        print("❌ 盲测失败！需要检查识别逻辑")
    print("=" * 70)
    
    return {
        'case_alpha': result_alpha,
        'case_beta': result_beta,
        'alpha_success': alpha_success,
        'beta_success': beta_success,
        'overall_success': alpha_success and beta_success
    }


if __name__ == '__main__':
    result = blind_fire_test()
    
    # 保存结果
    output_file = project_root / "data" / "holographic_pattern" / "A-03_BlindFireTest_Results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_file}")

