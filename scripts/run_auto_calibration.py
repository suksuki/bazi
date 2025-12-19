#!/usr/bin/env python3
"""
V13.2 自动校准执行脚本
直接运行自动校准器，寻找最优参数组合
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase1_auto_calibrator import Phase1AutoCalibrator
from core.models.config_model import ConfigModel
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def main():
    print("=" * 80)
    print("V13.2 自动校准器 - 开始运行")
    print("=" * 80)
    print()
    
    # 1. 加载配置和测试案例
    print("📥 正在加载配置和测试案例...")
    config_model = ConfigModel()
    config = config_model.load_config()
    
    # 加载测试案例
    test_cases_path = project_root / "data" / "phase1_test_cases.json"
    if not test_cases_path.exists():
        print(f"❌ 错误：未找到测试案例文件: {test_cases_path}")
        return
    
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"✅ 配置已加载")
    print(f"✅ 测试案例已加载: {len(test_cases.get('group_a_month', [])) + len(test_cases.get('group_b_rooting', [])) + len(test_cases.get('group_c_location', []))} 个案例")
    print()
    
    # 2. 显示当前关键参数
    print("📊 当前关键参数:")
    physics = config.get('physics', {})
    structure = config.get('structure', {})
    season_weights = physics.get('seasonWeights', {})
    pillar_weights = physics.get('pillarWeights', {})
    
    print(f"  泄气系数 (xiu): {season_weights.get('xiu', 0.9)}")
    print(f"  被克系数 (si): {season_weights.get('si', 0.45)}")
    print(f"  自坐强根加成: {structure.get('samePillarBonus', 3.0)}")
    print(f"  日柱权重: {pillar_weights.get('day', 1.35)}")
    print(f"  时柱权重: {pillar_weights.get('hour', 0.9)}")
    print(f"  年柱权重: {pillar_weights.get('year', 0.8)}")
    print()
    
    # 3. 初始化校准器
    print("🔧 初始化自动校准器...")
    calibrator = Phase1AutoCalibrator(config=config, test_cases=test_cases)
    print("✅ 校准器已初始化")
    print()
    
    # 4. 运行初始验证
    print("🔍 运行初始验证...")
    initial_result = calibrator.run_verification(config)
    print(f"初始状态:")
    print(f"  Group A: {'✅ 通过' if initial_result['group_a_passed'] else '❌ 失败'}")
    print(f"  Group B: {'✅ 通过' if initial_result['group_b_passed'] else '❌ 失败'}")
    print(f"  Group C: {'✅ 通过' if initial_result['group_c_passed'] else '❌ 失败'}")
    
    # V13.3: 检查权重倒挂（月令必须 >= 日柱）
    month_weight = config.get('physics', {}).get('pillarWeights', {}).get('month', 1.2)
    day_weight = config.get('physics', {}).get('pillarWeights', {}).get('day', 1.0)
    has_weight_inversion = month_weight < day_weight
    
    if has_weight_inversion:
        print(f"⚠️  检测到权重倒挂: 月令({month_weight:.2f}) < 日柱({day_weight:.2f})")
        print("   需要修正以维护'皇权约束'（月令必须最高）")
        print()
    elif initial_result['all_passed']:
        print()
        print("🎉 所有规则已通过，且权重层级正确！无需校准。")
        return
    
    print()
    print("=" * 80)
    if has_weight_inversion:
        print("🚀 开始自动校准（修正权重倒挂 + 优化参数）...")
    else:
        print("🚀 开始自动校准（模拟退火算法）...")
    print("=" * 80)
    print()
    
    # 5. 运行自动校准
    optimized_config, final_result, history = calibrator.calibrate(
        max_iterations=100,
        initial_temperature=10.0,
        cooling_rate=0.95,
        perturbation_scale=0.1
    )
    
    # 6. 显示结果
    print()
    print("=" * 80)
    print("📊 校准结果")
    print("=" * 80)
    print()
    
    print("✅ 最终验证状态:")
    print(f"  Group A: {'✅ 通过' if final_result['group_a_passed'] else '❌ 失败'}")
    print(f"  Group B: {'✅ 通过' if final_result['group_b_passed'] else '❌ 失败'}")
    print(f"  Group C: {'✅ 通过' if final_result['group_c_passed'] else '❌ 失败'}")
    print(f"  总体: {'✅ 全部通过' if final_result['all_passed'] else '❌ 部分失败'}")
    print()
    
    # 显示优化后的关键参数
    opt_physics = optimized_config.get('physics', {})
    opt_structure = optimized_config.get('structure', {})
    opt_season_weights = opt_physics.get('seasonWeights', {})
    opt_pillar_weights = opt_physics.get('pillarWeights', {})
    
    print("📈 优化后的关键参数:")
    print(f"  泄气系数 (xiu): {opt_season_weights.get('xiu', 0.9):.2f} (原: {season_weights.get('xiu', 0.9):.2f})")
    print(f"  被克系数 (si): {opt_season_weights.get('si', 0.45):.2f} (原: {season_weights.get('si', 0.45):.2f})")
    print(f"  自坐强根加成: {opt_structure.get('samePillarBonus', 3.0):.2f} (原: {structure.get('samePillarBonus', 3.0):.2f})")
    print(f"  日柱权重: {opt_pillar_weights.get('day', 1.35):.2f} (原: {pillar_weights.get('day', 1.35):.2f})")
    print(f"  时柱权重: {opt_pillar_weights.get('hour', 0.9):.2f} (原: {pillar_weights.get('hour', 0.9):.2f})")
    print()
    
    # 显示详细验证结果
    if 'group_a_results' in final_result:
        print("📋 Group A 详细结果:")
        for case in final_result['group_a_results']:
            print(f"  {case.get('id', 'N/A')}: 均值={case.get('energy', {}).get('mean', 0):.2f}, "
                  f"标准差={case.get('energy', {}).get('std', 0):.2f}")
        print()
    
    if 'group_b_results' in final_result:
        print("📋 Group B 详细结果:")
        for case in final_result['group_b_results']:
            print(f"  {case.get('id', 'N/A')}: 均值={case.get('energy', {}).get('mean', 0):.2f}, "
                  f"标准差={case.get('energy', {}).get('std', 0):.2f}")
        if 'probabilities' in final_result:
            for prob_info in final_result['probabilities']:
                if prob_info.get('group') == 'B':
                    print(f"  P(B3 > B2) = {prob_info.get('probability', 0)*100:.1f}%")
        print()
    
    # 显示 Loss 历史
    if history:
        print("📉 Loss 下降历史 (最后10次迭代):")
        for h in history[-10:]:
            loss = h.get('loss', 0)
            temp = h.get('temperature', 0)
            iter_num = h.get('iteration', 0)
            print(f"  迭代 {iter_num}: Loss={loss:.4f}, 温度={temp:.2f}")
        print()
    
    # 7. 保存优化后的配置（可选）
    if final_result['all_passed']:
        print("💾 是否保存优化后的配置到 config/parameters.json? (y/n): ", end='')
        # 自动保存
        save_config = True
        if save_config:
            # 深度合并优化后的参数
            current_config = config_model.load_config()
            
            # 合并优化后的参数
            def deep_merge(target, source):
                for key, value in source.items():
                    if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                        deep_merge(target[key], value)
                    else:
                        target[key] = value
            
            deep_merge(current_config, optimized_config)
            
            # 保存配置
            success = config_model.save_config(current_config, merge=False)
            if success:
                print("✅ 优化后的参数已保存到 config/parameters.json")
            else:
                print("❌ 保存失败，请检查文件权限")
        print()
    
    print("=" * 80)
    if final_result['all_passed']:
        print("🎉 Phase 1 全绿！所有规则通过！")
    else:
        print("⚠️  部分规则仍未通过，建议增加迭代次数或手动调整参数")
    print("=" * 80)

if __name__ == "__main__":
    main()

