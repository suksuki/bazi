#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 自动验证脚本
===================

自动运行 Phase 2 动态交互验证，并生成详细报告

使用方法:
    python scripts/auto_verify_phase2.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    加载算法配置
    
    Returns:
        配置字典
    """
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    
    # 尝试加载用户配置
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 深度合并配置
            def deep_merge(base: Dict, update: Dict):
                """递归合并配置"""
                for key, value in update.items():
                    if key.startswith('_'):
                        continue  # 跳过注释字段
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(config, user_config)
            logger.info(f"✅ 已加载用户配置: {config_path}")
        except Exception as e:
            logger.warning(f"⚠️  加载用户配置失败，使用默认配置: {e}")
    else:
        logger.info("ℹ️  使用默认配置（未找到用户配置文件）")
    
    return config


def load_test_cases() -> Dict[str, Any]:
    """
    加载 Phase 2 测试案例
    
    Returns:
        测试案例字典
    """
    test_cases_path = project_root / "data" / "phase2_test_cases.json"
    
    if not test_cases_path.exists():
        raise FileNotFoundError(f"测试案例文件不存在: {test_cases_path}")
    
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    logger.info(f"✅ 已加载测试案例: {test_cases_path}")
    return test_cases


def analyze_result(result: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析验证结果，与预期值比较
    
    Args:
        result: 验证结果
        case: 测试案例
        
    Returns:
        分析结果字典
    """
    if not result.get('success', False):
        return {
            'status': 'error',
            'error': result.get('error', 'Unknown error'),
            'case_id': case.get('id', 'N/A')
        }
    
    energy_ratio = result.get('energy_ratio', 0.0)
    expected_ratio = case.get('expected_energy_ratio', 0.0)
    
    # [V15.2] 优化：统一使用测试案例中指定的expected_energy_ratio作为预期比率
    # 如果测试案例没有指定，则根据组别使用默认值
    group = case.get('group', 'unknown')
    if expected_ratio <= 0:
        # 如果没有指定预期比率，根据组别使用默认值
        if group == 'group_f_combination':
            expected_ratio = 0.9  # 合局默认预期比率
        else:
            expected_ratio = 1.0  # 其他组默认预期比率
    
    # 计算误差
    if expected_ratio > 0:
        error_percent = abs(energy_ratio - expected_ratio) / expected_ratio * 100
    else:
        error_percent = 100.0
    
    # 判断是否通过（允许 20% 误差）
    tolerance = 0.2
    passed = error_percent <= (tolerance * 100)
    
    # 标准差变化分析
    std_change = result.get('std_change_ratio', 0.0)
    group = case.get('group', 'unknown')
    
    # 根据组别判断标准差变化是否符合预期
    std_check = None
    if group == 'group_e_control':
        # Group E (克): 受克者标准差应该增大（熵增）
        std_check = std_change > 0
    elif group == 'group_f_combination':
        # Group F (合): 合局者标准差应该减小（负熵）
        std_check = std_change < 0
    elif group == 'group_d_generation':
        # Group D (生): 波动率相对稳定
        std_check = abs(std_change) < 10.0
    
    return {
        'status': 'passed' if passed else 'failed',
        'case_id': case.get('id', 'N/A'),
        'energy_ratio': energy_ratio,
        'expected_ratio': expected_ratio,
        'error_percent': error_percent,
        'std_change': std_change,
        'std_check': std_check,
        'initial_energy': result.get('initial_energy', {}),
        'final_energy': result.get('final_energy', {}),
        'delta_energy': result.get('delta_energy', {}),
    }


def print_report(all_results: List[Dict[str, Any]], test_cases: Dict[str, Any]):
    """
    打印验证报告
    
    Args:
        all_results: 所有验证结果
        test_cases: 测试案例字典
    """
    print("\n" + "=" * 80)
    print("🧪 Phase 2 动态交互验证报告")
    print("=" * 80)
    print(f"📅 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 测试案例总数: {len(all_results)}")
    print()
    
    # 按组统计
    groups = {
        'group_d_generation': '🌱 Group D: 生成规则 (Generation)',
        'group_e_control': '⚔️ Group E: 克制规则 (Control)',
        'group_f_combination': '🔗 Group F: 合化规则 (Combination)',
        'group_g_directional': '🌐 Group G: 三会方局 (Directional Energy)',
        'group_h_resolution': '🔓 Group H: 贪合忘冲 (Clash Resolution)'
    }
    
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    for group_key, group_name in groups.items():
        group_cases = test_cases.get(group_key, [])
        if not group_cases:
            continue
        
        print("-" * 80)
        print(f"{group_name}")
        print("-" * 80)
        
        group_passed = 0
        group_failed = 0
        group_errors = 0
        
        for case in group_cases:
            case_id = case.get('id', 'N/A')
            # 找到对应的结果
            result = next((r for r in all_results if r.get('case_id') == case_id), None)
            
            if not result:
                print(f"  ❌ {case_id}: 未找到验证结果")
                group_errors += 1
                continue
            
            if result.get('status') == 'error':
                print(f"  ❌ {case_id}: 验证错误 - {result.get('error', 'Unknown')}")
                group_errors += 1
                total_errors += 1
                continue
            
            status_icon = "✅" if result.get('status') == 'passed' else "❌"
            energy_ratio = result.get('energy_ratio', 0.0)
            expected_ratio = result.get('expected_ratio', 0.0)
            error_percent = result.get('error_percent', 0.0)
            std_change = result.get('std_change', 0.0)
            std_check = result.get('std_check')
            
            # 状态标记
            if result.get('status') == 'passed':
                group_passed += 1
                total_passed += 1
            else:
                group_failed += 1
                total_failed += 1
            
            # 打印详细信息
            print(f"  {status_icon} {case_id}: {case.get('desc', 'N/A')}")
            print(f"     能量比率: {energy_ratio:.3f} (预期: {expected_ratio:.3f}, 误差: {error_percent:.1f}%)")
            
            # [V13.9] 打印调试信息
            debug_info = result.get('debug_info', {})
            if debug_info:
                detected = debug_info.get('detected_matches', [])
                node_changes = debug_info.get('node_changes', [])
                if detected:
                    print(f"     🔍 检测到的合局: {', '.join(detected)}")
                if node_changes:
                    print(f"     🔄 节点五行变化: {', '.join(node_changes)}")
            
            # 标准差检查
            if std_check is not None:
                std_icon = "✅" if std_check else "⚠️"
                std_status = "符合预期" if std_check else "不符合预期"
                print(f"     {std_icon} 标准差变化: {std_change:+.2f}% ({std_status})")
            
            # 能量详情
            initial = result.get('initial_energy', {})
            final = result.get('final_energy', {})
            print(f"     初始能量: μ={initial.get('mean', 0):.2f}, σ={initial.get('std', 0):.2f} ({initial.get('std_percent', 0):.1f}%)")
            print(f"     最终能量: μ={final.get('mean', 0):.2f}, σ={final.get('std', 0):.2f} ({final.get('std_percent', 0):.1f}%)")
            print()
        
        # 组统计
        group_total = group_passed + group_failed + group_errors
        if group_total > 0:
            pass_rate = (group_passed / group_total) * 100
            print(f"  📊 组统计: {group_passed}/{group_total} 通过 ({pass_rate:.1f}%)")
            print()
    
    # 总体统计
    print("=" * 80)
    print("📊 总体统计")
    print("=" * 80)
    total = total_passed + total_failed + total_errors
    if total > 0:
        overall_pass_rate = (total_passed / total) * 100
        print(f"✅ 通过: {total_passed}")
        print(f"❌ 失败: {total_failed}")
        print(f"⚠️  错误: {total_errors}")
        print(f"📈 通过率: {overall_pass_rate:.1f}%")
    print("=" * 80)
    print()


def main():
    """主函数"""
    try:
        print("🚀 启动 Phase 2 自动验证...")
        print()
        
        # 1. 加载配置
        config = load_config()
        
        # 2. 加载测试案例
        test_cases = load_test_cases()
        
        # 3. 创建验证器
        verifier = Phase2Verifier(config)
        logger.info("✅ Phase2Verifier 已初始化")
        
        # 4. 运行验证
        all_results = []
        
        # Group D: 生成规则
        if 'group_d_generation' in test_cases:
            logger.info("🌱 验证 Group D: 生成规则...")
            group_d_cases = test_cases['group_d_generation']
            for case in group_d_cases:
                case['group'] = 'group_d_generation'
                result = verifier.verify_case(case)
                analysis = analyze_result(result, case)
                all_results.append(analysis)
                logger.info(f"  ✅ {case.get('id', 'N/A')}: 完成")
        
        # Group E: 克制规则
        if 'group_e_control' in test_cases:
            logger.info("⚔️  验证 Group E: 克制规则...")
            group_e_cases = test_cases['group_e_control']
            for case in group_e_cases:
                case['group'] = 'group_e_control'
                result = verifier.verify_case(case)
                analysis = analyze_result(result, case)
                all_results.append(analysis)
                logger.info(f"  ✅ {case.get('id', 'N/A')}: 完成")
        
        # Group F: 合化规则
        if 'group_f_combination' in test_cases:
            logger.info("🔗 验证 Group F: 合化规则...")
            group_f_cases = test_cases['group_f_combination']
            for case in group_f_cases:
                case['group'] = 'group_f_combination'
                result = verifier.verify_case(case)
                analysis = analyze_result(result, case)
                all_results.append(analysis)
                logger.info(f"  ✅ {case.get('id', 'N/A')}: 完成")
        
        if 'group_g_directional' in test_cases:
            logger.info("🌐 验证 Group G: 三会方局...")
            group_g_cases = test_cases['group_g_directional']
            for case in group_g_cases:
                case['group'] = 'group_g_directional'
                result = verifier.verify_case(case)
                analysis = analyze_result(result, case)
                all_results.append(analysis)
                logger.info(f"  ✅ {case.get('id', 'N/A')}: 完成")
        
        if 'group_h_resolution' in test_cases:
            logger.info("🔓 验证 Group H: 贪合忘冲...")
            group_h_cases = test_cases['group_h_resolution']
            for case in group_h_cases:
                case['group'] = 'group_h_resolution'
                result = verifier.verify_case(case)
                analysis = analyze_result(result, case)
                all_results.append(analysis)
                logger.info(f"  ✅ {case.get('id', 'N/A')}: 完成")
        
        # 5. 生成报告
        print_report(all_results, test_cases)
        
        # 6. 保存结果到文件
        output_path = project_root / "data" / "phase2_verification_results.json"
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'results': all_results,
            'test_cases': test_cases
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 验证结果已保存: {output_path}")
        
        print("✅ Phase 2 验证完成！")
        
    except Exception as e:
        logger.exception(f"❌ 验证失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

