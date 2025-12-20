#!/usr/bin/env python3
"""
V13.1 Phase 1 验证测试脚本
直接运行验证并查看效果
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase1_auto_calibrator import Phase1AutoCalibrator
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.models.config_model import ConfigModel
from core.math import ProbValue, prob_compare

def load_test_cases():
    """加载测试案例"""
    test_cases_path = project_root / "data" / "phase1_test_cases.json"
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_verification_result(result):
    """打印验证结果"""
    print("\n" + "="*80)
    print("Phase 1 验证结果 (V13.1)")
    print("="*80)
    
    # 总体状态
    print(f"\n总体状态: {'✅ 全部通过' if result['all_passed'] else '❌ 部分失败'}")
    print(f"Group A (月令): {'✅ 通过' if result['group_a_passed'] else '❌ 失败'}")
    print(f"Group B (通根): {'✅ 通过' if result['group_b_passed'] else '❌ 失败'}")
    print(f"Group C (宫位): {'✅ 通过' if result['group_c_passed'] else '❌ 失败'}")
    
    # Group A 详细结果
    if 'group_a_results' in result:
        print("\n" + "-"*80)
        print("Group A: 月令敏感度测试")
        print("-"*80)
        for i, r in enumerate(result['group_a_results']):
            energy = r.get('self_team_energy_prob', r.get('self_team_energy', 0.0))
            if not isinstance(energy, ProbValue):
                energy = ProbValue(float(energy), std_dev_percent=0.1)
            
            print(f"  {r.get('id', 'N/A'):20s} | 均值: {energy.mean:8.2f} | 标准差: {energy.std:6.2f} | 描述: {r.get('desc', 'N/A')}")
            
            # 与前一个比较
            if i > 0:
                prev_energy = result['group_a_results'][i-1].get('self_team_energy_prob', 
                                                                  result['group_a_results'][i-1].get('self_team_energy', 0.0))
                if not isinstance(prev_energy, ProbValue):
                    prev_energy = ProbValue(float(prev_energy), std_dev_percent=0.1)
                
                passed, prob = prob_compare(prev_energy, energy, threshold=0.85)
                status = "✅" if passed else "❌"
                print(f"    {status} P({result['group_a_results'][i-1].get('id', 'N/A')} > {r.get('id', 'N/A')}) = {prob*100:.1f}%")
    
    # Group B 详细结果
    if 'group_b_results' in result:
        print("\n" + "-"*80)
        print("Group B: 通根有效性测试")
        print("-"*80)
        for i, r in enumerate(result['group_b_results']):
            energy = r.get('self_team_energy_prob', r.get('self_team_energy', 0.0))
            if not isinstance(energy, ProbValue):
                energy = ProbValue(float(energy), std_dev_percent=0.1)
            
            print(f"  {r.get('id', 'N/A'):20s} | 均值: {energy.mean:8.2f} | 标准差: {energy.std:6.2f} | 描述: {r.get('desc', 'N/A')}")
            
            # 与前一个比较
            if i > 0:
                prev_energy = result['group_b_results'][i-1].get('self_team_energy_prob', 
                                                                  result['group_b_results'][i-1].get('self_team_energy', 0.0))
                if not isinstance(prev_energy, ProbValue):
                    prev_energy = ProbValue(float(prev_energy), std_dev_percent=0.1)
                
                passed, prob = prob_compare(prev_energy, energy, threshold=0.85)
                status = "✅" if passed else "❌"
                print(f"    {status} P({result['group_b_results'][i-1].get('id', 'N/A')} > {r.get('id', 'N/A')}) = {prob*100:.1f}%")
    
    # Group C 详细结果
    if 'group_c_results' in result:
        print("\n" + "-"*80)
        print("Group C: 宫位距离测试")
        print("-"*80)
        for i, r in enumerate(result['group_c_results']):
            energy = r.get('self_team_energy_prob', r.get('self_team_energy', 0.0))
            if not isinstance(energy, ProbValue):
                energy = ProbValue(float(energy), std_dev_percent=0.1)
            
            print(f"  {r.get('id', 'N/A'):20s} | 均值: {energy.mean:8.2f} | 标准差: {energy.std:6.2f} | 描述: {r.get('desc', 'N/A')}")
            
            # 与前一个比较
            if i > 0:
                prev_energy = result['group_c_results'][i-1].get('self_team_energy_prob', 
                                                                  result['group_c_results'][i-1].get('self_team_energy', 0.0))
                if not isinstance(prev_energy, ProbValue):
                    prev_energy = ProbValue(float(prev_energy), std_dev_percent=0.1)
                
                passed, prob = prob_compare(prev_energy, energy, threshold=0.85)
                status = "✅" if passed else "❌"
                print(f"    {status} P({result['group_c_results'][i-1].get('id', 'N/A')} > {r.get('id', 'N/A')}) = {prob*100:.1f}%")
    
    print("\n" + "="*80)

def main():
    """主函数"""
    print("正在加载配置和测试案例...")
    
    # 加载配置 - V13.1: 强制使用最新默认值
    import copy
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # V13.1: 尝试从配置文件加载
    config_model = ConfigModel()
    user_config = config_model.load_config()
    if user_config:
        # 深度合并
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        deep_merge(config, user_config)
    
    # V13.1: 强制应用修复后的参数（进一步微调，覆盖所有配置）
    config.setdefault('physics', {}).setdefault('seasonWeights', {})['xiu'] = 0.90  # 泄气系数（保持0.90，Group A已通过）
    config.setdefault('physics', {}).setdefault('seasonWeights', {})['si'] = 0.45   # 被克系数（保持0.45，Group A已通过）
    config.setdefault('structure', {})['samePillarBonus'] = 3.0                      # 自坐强根加成（从2.9提升到3.0，解决Group B）
    config.setdefault('physics', {}).setdefault('pillarWeights', {})['day'] = 1.35   # 日柱权重（从1.3提升到1.35，解决Group C）
    
    # 显示关键参数
    print("\n当前关键参数:")
    print(f"  泄气系数 (xiu): {config.get('physics', {}).get('seasonWeights', {}).get('xiu', 0.90)}")
    print(f"  被克系数 (si): {config.get('physics', {}).get('seasonWeights', {}).get('si', 0.45)}")
    print(f"  自坐强根加成: {config.get('structure', {}).get('samePillarBonus', 2.0)}")
    print(f"  日柱权重: {config.get('physics', {}).get('pillarWeights', {}).get('day', 1.3)}")
    print(f"  时柱权重: {config.get('physics', {}).get('pillarWeights', {}).get('hour', 0.9)}")
    print(f"  年柱权重: {config.get('physics', {}).get('pillarWeights', {}).get('year', 0.7)}")
    
    # 加载测试案例
    test_cases = load_test_cases()
    
    # 创建校准器
    calibrator = Phase1AutoCalibrator(config, test_cases, default_config=config.copy())
    
    # 运行验证
    print("\n正在运行验证...")
    result = calibrator.run_verification(config)
    
    # 打印结果
    print_verification_result(result)
    
    # 计算损失
    loss, loss_details = calibrator.calculate_loss(config)
    print(f"\n总损失: {loss:.2f}")
    print(f"  规则损失: {loss_details['rule_loss']:.2f}")
    print(f"  正则化损失: {loss_details['regularization_loss']:.2f}")
    print(f"  先验约束损失: {loss_details['prior_constraint_loss']:.2f}")

if __name__ == "__main__":
    main()

