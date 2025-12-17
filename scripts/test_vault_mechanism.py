#!/usr/bin/env python3
"""
V59.1 墓库机制专项测试
测试财库冲开（量子隧穿）机制
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def test_vault_opening():
    """
    测试案例：乙未 丙戌 壬戌 辛亥
    日主：壬水
    财星：火（丙、丁）
    财库：戌（火库）
    测试年份：2024 (甲辰) - 辰冲戌，应该冲开财库
    """
    print("=" * 80)
    print("🏆 V59.1 墓库机制专项测试：财库冲开验证")
    print("=" * 80)
    print()
    
    # 测试案例
    test_case = {
        "name": "财库测试案例",
        "bazi": ["乙未", "丙戌", "壬戌", "辛亥"],
        "day_master": "壬",
        "gender": "男",
        "description": "壬水日主，戌为火库（财库）。2024年甲辰冲戌，应该冲开财库。"
    }
    
    print(f"👤 案例: {test_case['name']}")
    print(f"   八字: {' '.join(test_case['bazi'])}")
    print(f"   日主: {test_case['day_master']}水")
    print(f"   财库: 戌（火库）")
    print("-" * 80)
    print()
    
    # 初始化引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
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
    
    # 测试年份列表
    test_years = [
        {
            "year": 2023,
            "ganzhi": "癸卯",
            "dayun": "壬午",
            "expected": "无库开",
            "expected_wealth": "低（< 30）"
        },
        {
            "year": 2024,
            "ganzhi": "甲辰",
            "dayun": "壬午",
            "expected": "🏆 财库大开",
            "expected_wealth": "高（> 80）"
        },
        {
            "year": 2025,
            "ganzhi": "乙巳",
            "dayun": "壬午",
            "expected": "无库开",
            "expected_wealth": "中（30-60）"
        }
    ]
    
    print("📅 测试年份列表：")
    print()
    
    results = []
    for test_year in test_years:
        year = test_year['year']
        ganzhi = test_year['ganzhi']
        dayun = test_year['dayun']
        expected = test_year['expected']
        expected_wealth = test_year['expected_wealth']
        
        # 调用财富引擎
        try:
            result = engine.calculate_wealth_index(
                bazi=test_case['bazi'],
                day_master=test_case['day_master'],
                gender=test_case['gender'],
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            if isinstance(result, dict):
                wealth_index = result.get('wealth_index', 0.0)
                details = result.get('details', [])
                strength_score = result.get('strength_score', 0.0)
                strength_label = result.get('strength_label', 'Unknown')
            else:
                wealth_index = result
                details = []
                strength_score = 0.0
                strength_label = 'Unknown'
            
            # 检查是否触发财库冲开
            vault_opened = False
            vault_details = []
            for detail in details:
                if '冲开财库' in detail or '财库' in detail or '🏆' in detail or '🚀' in detail:
                    vault_opened = True
                    vault_details.append(detail)
            
            # 判断结果
            if year == 2024:
                # 2024年应该冲开财库
                is_correct = vault_opened and wealth_index > 80
                status = "✅" if is_correct else "❌"
            else:
                # 其他年份不应该冲开财库（或财富较低）
                is_correct = not vault_opened or wealth_index < 60
                status = "✅" if is_correct else "⚠️"
            
            results.append({
                'year': year,
                'wealth_index': wealth_index,
                'vault_opened': vault_opened,
                'is_correct': is_correct,
                'status': status
            })
            
            print(f"{year} ({ganzhi}) | 运: {dayun}")
            print(f"   预期: {expected} | 预期财富: {expected_wealth}")
            print(f"   AI预测: {wealth_index:>6.1f} | 身强: {strength_score:.1f} ({strength_label})")
            print(f"   财库状态: {'🏆 已冲开' if vault_opened else '🔒 未冲开'}")
            if vault_details:
                print(f"   库开详情: {', '.join(vault_details)}")
            if details:
                print(f"   触发机制: {', '.join(details[:3])}")  # 只显示前3个
            print(f"   结果: {status}")
            print("-" * 40)
            print()
            
        except Exception as e:
            print(f"⚠️ {year}年计算错误: {e}")
            import traceback
            traceback.print_exc()
            print("-" * 40)
            print()
    
    # 统计结果
    print("=" * 80)
    print("📊 测试结果统计")
    print("=" * 80)
    
    correct_count = sum(1 for r in results if r['is_correct'])
    total_count = len(results)
    
    print(f"✅ 通过: {correct_count}/{total_count}")
    print(f"   准确率: {correct_count/total_count*100:.1f}%")
    print()
    
    # 重点检查2024年
    if results:
        year_2024 = next((r for r in results if r['year'] == 2024), None)
        if year_2024:
            if year_2024['vault_opened'] and year_2024['wealth_index'] > 80:
                print("🏆 2024年财库冲开测试: ✅ 通过")
                print(f"   财富指数: {year_2024['wealth_index']:.1f}")
                print("   🎉 墓库机制运行正常！")
            else:
                print("🏆 2024年财库冲开测试: ❌ 失败")
                print(f"   财富指数: {year_2024['wealth_index']:.1f}")
                print(f"   财库状态: {'已冲开' if year_2024['vault_opened'] else '未冲开'}")
                print("   ⚠️ 需要检查墓库冲开逻辑")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_vault_opening()

