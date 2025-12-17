#!/usr/bin/env python3
"""
对比旧验证脚本和新系统的Musk案例预测结果
找出差异原因
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from controllers.wealth_verification_controller import WealthVerificationController
import copy

def test_old_way():
    """使用旧方式测试（直接读取golden_timeline.json）"""
    print("=" * 80)
    print("📊 旧方式测试（verify_wealth_timeline.py方式）")
    print("=" * 80)
    print()
    
    # 初始化引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 加载用户配置
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, user_config)
    
    engine = GraphNetworkEngine(config=config)
    
    # 加载旧数据
    data_path = project_root / 'data' / 'golden_timeline.json'
    if not data_path.exists():
        print("❌ 旧数据文件不存在，创建它...")
        from scripts.create_wealth_timeline import create_wealth_dataset
        create_wealth_dataset()
    
    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    musk = cases[0]
    print(f"👤 案例: {musk['name']} ({musk['day_master']}日主)")
    print(f"   八字: {' '.join(musk['bazi'])}")
    print(f"   事件数: {len(musk['timeline'])}")
    print()
    
    results_old = []
    for evt in musk['timeline']:
        year = evt['year']
        ganzhi = evt['ganzhi']
        dayun = evt.get('dayun', '')
        real_mag = evt.get('real_magnitude', 0.0)
        
        try:
            result = engine.calculate_wealth_index(
                bazi=musk['bazi'],
                day_master=musk['day_master'],
                gender=musk['gender'],
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            if isinstance(result, dict):
                predicted = result.get('wealth_index', 0.0)
                details = result.get('details', [])
            else:
                predicted = result
                details = []
            
            error = abs(predicted - real_mag)
            results_old.append({
                'year': year,
                'real': real_mag,
                'predicted': predicted,
                'error': error,
                'details': details,
                'dayun': dayun
            })
            
            print(f"{year}年 ({ganzhi}): 真实={real_mag:.1f}, 预测={predicted:.1f}, 误差={error:.1f}")
        except Exception as e:
            print(f"{year}年: 计算失败 - {e}")
            results_old.append({
                'year': year,
                'real': real_mag,
                'predicted': None,
                'error': None,
                'details': [],
                'dayun': dayun
            })
    
    return results_old

def test_new_way():
    """使用新方式测试（通过Controller）"""
    print()
    print("=" * 80)
    print("📊 新方式测试（MVC系统方式）")
    print("=" * 80)
    print()
    
    controller = WealthVerificationController()
    musk_case = controller.get_case_by_id('TIMELINE_MUSK_WEALTH')
    
    if not musk_case:
        print("❌ 未找到Musk案例")
        return None
    
    print(f"👤 案例: {musk_case.name} ({musk_case.day_master}日主)")
    print(f"   八字: {' '.join(musk_case.bazi)}")
    print(f"   事件数: {len(musk_case.timeline) if musk_case.timeline else 0}")
    print()
    
    results_new = controller.verify_case(musk_case)
    
    for r in results_new:
        year = r['year']
        real = r['real']
        predicted = r.get('predicted', 'N/A')
        error = r.get('error', 'N/A')
        dayun = r.get('dayun', 'N/A')
        
        if predicted != 'N/A' and error != 'N/A':
            print(f"{year}年 ({r['ganzhi']}): 真实={real:.1f}, 预测={predicted:.1f}, 误差={error:.1f}")
        else:
            print(f"{year}年 ({r['ganzhi']}): 真实={real:.1f}, 预测=计算失败")
    
    return results_new

def compare_results(results_old, results_new):
    """对比两种方式的结果"""
    print()
    print("=" * 80)
    print("🔍 结果对比分析")
    print("=" * 80)
    print()
    
    if not results_old or not results_new:
        print("❌ 无法对比：缺少结果数据")
        return
    
    # 创建年份映射
    old_dict = {r['year']: r for r in results_old}
    new_dict = {r['year']: r for r in results_new}
    
    print("📋 详细对比:")
    print()
    
    all_years = sorted(set(list(old_dict.keys()) + list(new_dict.keys())))
    
    differences = []
    for year in all_years:
        old_r = old_dict.get(year)
        new_r = new_dict.get(year)
        
        print(f"{'='*80}")
        print(f"📅 {year}年")
        print(f"{'='*80}")
        
        if old_r:
            old_pred = old_r.get('predicted', 'N/A')
            old_error = old_r.get('error', 'N/A')
            old_dayun = old_r.get('dayun', 'N/A')
            print(f"   旧方式: 预测={old_pred}, 误差={old_error}, 大运={old_dayun}")
        else:
            print(f"   旧方式: ❌ 无此事件")
        
        if new_r:
            new_pred = new_r.get('predicted', 'N/A')
            new_error = new_r.get('error', 'N/A')
            new_dayun = new_r.get('dayun', 'N/A')
            print(f"   新方式: 预测={new_pred}, 误差={new_error}, 大运={new_dayun}")
        else:
            print(f"   新方式: ❌ 无此事件")
        
        # 对比
        if old_r and new_r:
            old_pred = old_r.get('predicted')
            new_pred = new_r.get('predicted')
            old_dayun = old_r.get('dayun', '')
            new_dayun = new_r.get('dayun', '')
            
            if old_pred is not None and new_pred is not None:
                diff = abs(old_pred - new_pred)
                if diff > 0.1:
                    print(f"   ⚠️ 差异: {diff:.1f}分")
                    differences.append({
                        'year': year,
                        'old': old_pred,
                        'new': new_pred,
                        'diff': diff
                    })
                else:
                    print(f"   ✅ 一致")
            
            if old_dayun != new_dayun:
                print(f"   ⚠️ 大运不同: 旧={old_dayun}, 新={new_dayun}")
                print(f"      这可能是导致预测差异的原因！")
        
        print()
    
    # 总结
    print("=" * 80)
    print("📊 差异总结")
    print("=" * 80)
    print()
    
    if differences:
        print(f"发现 {len(differences)} 个事件的预测值不同:")
        for d in differences:
            print(f"   {d['year']}年: 旧={d['old']:.1f}, 新={d['new']:.1f}, 差异={d['diff']:.1f}")
        print()
        print("💡 可能原因:")
        print("   1. 大运计算不同（旧脚本可能使用固定大运，新系统使用BaziProfile计算）")
        print("   2. 数据格式不同（旧数据只有4个事件，新数据有6个事件）")
        print("   3. 引擎配置不同（可能加载了不同的参数）")
    else:
        print("✅ 所有事件的预测值一致")
    
    print("=" * 80)

def main():
    """主函数"""
    print("=" * 80)
    print("🔍 对比旧验证脚本和新系统的Musk案例预测结果")
    print("=" * 80)
    print()
    
    # 测试旧方式
    results_old = test_old_way()
    
    # 测试新方式
    results_new = test_new_way()
    
    # 对比结果
    if results_old and results_new:
        compare_results(results_old, results_new)
    else:
        print("❌ 无法完成对比：缺少结果数据")

if __name__ == "__main__":
    main()

