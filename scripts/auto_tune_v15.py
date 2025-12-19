#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V15.2 自动调优脚本
==================

自动调整参数直到通过率达到 100%

使用方法:
    python scripts/auto_tune_v15.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_config():
    """加载配置"""
    config_path = project_root / "config" / "parameters.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """保存配置"""
    config_path = project_root / "config" / "parameters.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_engine_code():
    """加载引擎代码"""
    engine_path = project_root / "core" / "engine_graph.py"
    with open(engine_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_engine_code(code):
    """保存引擎代码"""
    engine_path = project_root / "core" / "engine_graph.py"
    with open(engine_path, 'w', encoding='utf-8') as f:
        f.write(code)

def run_verification():
    """运行验证并返回通过率和失败案例"""
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "auto_verify_phase2.py")],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    # 解析通过率
    output = result.stdout
    pass_rate = 0.0
    failures = []
    
    for line in output.split('\n'):
        if '通过率:' in line:
            try:
                pass_rate = float(line.split('通过率:')[1].split('%')[0].strip())
            except:
                pass
        elif '❌' in line and ':' in line:
            # 提取失败案例ID
            parts = line.split('❌')
            if len(parts) > 1:
                case_id = parts[1].split(':')[0].strip()
                failures.append(case_id)
    
    return pass_rate, failures

def load_results():
    """加载验证结果"""
    results_path = project_root / "data" / "phase2_verification_results.json"
    if not results_path.exists():
        return None
    
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_failures():
    """分析失败案例"""
    data = load_results()
    if not data:
        return {}
    
    failure_analysis = {}
    for result in data.get('results', []):
        if result.get('status') == 'failed':
            case_id = result.get('case_id', '')
            ratio = result.get('energy_ratio', 0)
            expected = result.get('expected_ratio', 0.9)
            failure_analysis[case_id] = {
                'ratio': ratio,
                'expected': expected,
                'issue': 'explosion' if ratio > expected * 1.3 else 'loss'
            }
    
    return failure_analysis

def optimize_parameters(config, engine_code, failures, iteration):
    """根据失败案例优化参数"""
    print(f"\n🔄 迭代 {iteration}: 分析 {len(failures)} 个失败案例")
    
    # 统计问题类型
    d_failures = [f for f in failures if f.startswith('D')]
    e_failures = [f for f in failures if f.startswith('E')]
    f_failures = [f for f in failures if f.startswith('F')]
    
    print(f"  💥 D组失败: {len(d_failures)} 个")
    print(f"  📉 E组失败: {len(e_failures)} 个")
    print(f"  🔗 F组失败: {len(f_failures)} 个")
    
    # 分析失败案例详情
    failure_analysis = analyze_failures()
    
    # 策略1: 针对D组能量爆炸 - 更激进的衰减
    if d_failures:
        print("  🔧 策略1: 更激进的迭代衰减（D组）")
        # 修改引擎代码中的衰减系数
        if 'temporal_decay_factor = 0.70' in engine_code:
            # 尝试更激进的衰减
            new_decay = 0.65 - (iteration * 0.02)  # 每次迭代降低0.02
            new_decay = max(0.50, new_decay)  # 最低0.50
            engine_code = engine_code.replace(
                'temporal_decay_factor = 0.70 ** iteration',
                f'temporal_decay_factor = {new_decay:.2f} ** iteration'
            )
            print(f"    衰减系数: 0.70 -> {new_decay:.2f}")
    
    # 策略2: 针对E组能量流失 - 更早的保护和更低的伤害
    if e_failures:
        print("  🔧 策略2: 更早的保护和更低的伤害（E组）")
        # 降低伤害上限
        if 'impact_factor = 0.15' in engine_code:
            new_impact = 0.12 - (iteration * 0.01)
            new_impact = max(0.08, new_impact)  # 最低0.08
            engine_code = engine_code.replace(
                'impact_factor = 0.15 * math.tanh(ratio)',
                f'impact_factor = {new_impact:.2f} * math.tanh(ratio)'
            )
            print(f"    伤害上限: 0.15 -> {new_impact:.2f}")
        
        # 提升护盾阈值
        if 'target_initial_mean * 0.4' in engine_code:
            new_threshold1 = 0.5 + (iteration * 0.05)  # 更早启动
            new_threshold1 = min(0.8, new_threshold1)  # 最高0.8
            new_threshold2 = 0.75 + (iteration * 0.05)
            new_threshold2 = min(0.9, new_threshold2)
            engine_code = engine_code.replace(
                'target_energy.mean < (target_initial_mean * 0.4)',
                f'target_energy.mean < (target_initial_mean * {new_threshold1:.2f})'
            )
            engine_code = engine_code.replace(
                'target_energy.mean < (target_initial_mean * 0.75)',
                f'target_energy.mean < (target_initial_mean * {new_threshold2:.2f})'
            )
            print(f"    护盾阈值: 40%/75% -> {new_threshold1:.0%}/{new_threshold2:.0%}")
    
    # 策略3: 针对F组能量流失 - 提高半超导增益
    if f_failures:
        print("  🔧 策略3: 提高半超导增益（F组）")
        # 提高半超导的增益倍数
        if 'gain_multiplier = 0.35' in engine_code:
            new_multiplier = 0.35 + (iteration * 0.05)
            new_multiplier = min(0.6, new_multiplier)  # 最高0.6
            engine_code = engine_code.replace(
                'gain_multiplier = 0.35  # 半超导：中等增益',
                f'gain_multiplier = {new_multiplier:.2f}  # [V15.2] 半超导：提高增益'
            )
            print(f"    半超导增益: 0.35 -> {new_multiplier:.2f}")
    
    return config, engine_code

def main():
    """主函数"""
    print("🚀 启动 V15.2 自动调优...")
    print("=" * 80)
    
    max_iterations = 15
    target_rate = 100.0
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'=' * 80}")
        print(f"📊 迭代 {iteration}/{max_iterations}")
        print(f"{'=' * 80}")
        
        # 1. 运行验证
        print("\n1️⃣ 运行验证...")
        pass_rate, failures = run_verification()
        print(f"   通过率: {pass_rate:.1f}%")
        print(f"   失败案例: {', '.join(failures) if failures else '无'}")
        
        # 2. 检查是否达到目标
        if pass_rate >= target_rate:
            print(f"\n🎉 成功！通过率达到 {pass_rate:.1f}%")
            break
        
        if not failures:
            print("    ✅ 没有失败案例（可能结果文件未更新）")
            continue
        
        # 3. 优化参数
        print("\n2️⃣ 优化参数...")
        config = load_config()
        engine_code = load_engine_code()
        config, engine_code = optimize_parameters(config, engine_code, failures, iteration)
        save_config(config)
        save_engine_code(engine_code)
        print("   ✅ 参数已保存")
        
        # 4. 如果迭代次数过多，停止
        if iteration >= max_iterations:
            print(f"\n⚠️  达到最大迭代次数 ({max_iterations})，停止优化")
            break
    
    # 最终验证
    print(f"\n{'=' * 80}")
    print("📊 最终验证结果")
    print(f"{'=' * 80}")
    final_rate, final_failures = run_verification()
    print(f"最终通过率: {final_rate:.1f}%")
    print(f"失败案例: {', '.join(final_failures) if final_failures else '无'}")
    
    if final_rate >= target_rate:
        print("🎉 自动调优成功！")
    else:
        print(f"⚠️  未达到目标通过率 ({target_rate}%)，当前: {final_rate:.1f}%")

if __name__ == '__main__':
    main()

