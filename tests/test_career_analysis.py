#!/usr/bin/env python3
"""
测试 V30.0 事业物理定义 (Career & Power Analysis)
"""

from core.meaning import MeaningEngine

def test_qisha_shishen_special_forces():
    """测试七杀格+食神制杀 -> 特种兵式权威"""
    print("=" * 60)
    print("测试案例：七杀格 + 食神高透制杀")
    print("=" * 60)
    
    # Mock flux data: 七杀格 + 食神
    flux_data = {
        'particle_states': [
            # Day Master: 甲木
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40.0},
            
            # 七杀: 庚金 (Dynamic Shock)
            {'id': 'month_stem', 'char': '庚', 'type': 'stem', 'amp': 80.0},
            
            # 食神: 丙火 (Counter-Strike Tool)
            {'id': 'year_stem', 'char': '丙', 'type': 'stem', 'amp': 100.0},  # High energy!
            
            # Supporting
            {'id': 'hour_stem', 'char': '乙', 'type': 'stem', 'amp': 30.0},
        ],
        'log': [],
        'spectrum': {}
    }
    
    chart = {'day': {'stem': '甲'}}
    
    engine = MeaningEngine(chart, flux_data)
    report = engine.analyze_career_power()
    
    print(f"\n📊 负载分析 (Load Analysis):")
    print(f"   类型: {report['load_analysis']['type']}")
    print(f"   总负载: {report['load_analysis']['total_energy']:.1f} eV")
    for p in report['load_analysis']['particles']:
        print(f"   - {p['char']} ({p['type']}): {p['energy']:.1f} eV")
    
    print(f"\n🔧 解决机制 (Solution Mechanism):")
    print(f"   类型: {report['solution_mechanism']['type']}")
    print(f"   能力: {report['solution_mechanism']['strength']:.1f} eV")
    for t in report['solution_mechanism']['tools']:
        print(f"   - {t['char']} ({t['mechanism']}): {t['energy']:.1f} eV")
    
    print(f"\n{report['status']['icon']} 状态 (Status):")
    print(f"   类型: {report['status']['type']}")
    print(f"   负载比: {report['status']['load_ratio']:.2f}")
    print(f"   描述: {report['status']['desc']}")
    
    print(f"\n📜 判词 (Verdict):")
    print(report['verdict'])
    
    # Assertions
    assert report['load_analysis']['type'] == "Dynamic"
    assert report['solution_mechanism']['type'] == "Counter-Strike"
    assert report['status']['load_ratio'] > 1.0
    assert "特种兵式权威" in report['verdict']
    
    print("\n✅ 测试通过！")

def test_zhengguan_zhengyin_bureaucrat():
    """测试正官+正印 -> 体制内官僚"""
    print("\n" + "=" * 60)
    print("测试案例：正官 + 正印 -> 体制内稳定")
    print("=" * 60)
    
    flux_data = {
        'particle_states': [
            # Day Master: 甲木
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40.0},
            
            # 正官: 辛金 (Static Load)
            {'id': 'month_stem', 'char': '辛', 'type': 'stem', 'amp': 60.0},
            
            # 正印: 癸水 (Absorption Tool)
            {'id': 'year_stem', 'char': '癸', 'type': 'stem', 'amp': 70.0},
        ],
        'log': [],
        'spectrum': {}
    }
    
    chart = {'day': {'stem': '甲'}}
    
    engine = MeaningEngine(chart, flux_data)
    report = engine.analyze_career_power()
    
    print(f"\n📊 负载分析: {report['load_analysis']['type']}")
    print(f"🔧 解决机制: {report['solution_mechanism']['type']}")
    print(f"{report['status']['icon']} 状态: {report['status']['type']}")
    
    assert report['load_analysis']['type'] == "Static"
    assert report['solution_mechanism']['type'] == "Absorption"
    
    print("\n✅ 测试通过！")

def test_no_solution_consumable():
    """测试无解决工具 -> 系统耗材"""
    print("\n" + "=" * 60)
    print("测试案例：七杀无制 -> 系统耗材")
    print("=" * 60)
    
    flux_data = {
        'particle_states': [
            # Day Master: 甲木 (Weak)
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 20.0},
            
            # 七杀: 庚金 (Heavy Load)
            {'id': 'month_stem', 'char': '庚', 'type': 'stem', 'amp': 100.0},
            
            # No solution tools!
        ],
        'log': [],
        'spectrum': {}
    }
    
    chart = {'day': {'stem': '甲'}}
    
    engine = MeaningEngine(chart, flux_data)
    report = engine.analyze_career_power()
    
    print(f"\n📊 负载分析: {report['load_analysis']['total_energy']:.1f} eV")
    print(f"🔧 解决能力: {report['solution_mechanism']['strength']:.1f} eV")
    print(f"{report['status']['icon']} 状态: {report['status']['type']}")
    print(f"   负载比: {report['status']['load_ratio']:.2f}")
    
    assert report['status']['type'] == "Consumable (耗材)"
    assert report['status']['load_ratio'] < 0.8
    
    print("\n✅ 测试通过！")

if __name__ == "__main__":
    test_qisha_shishen_special_forces()
    test_zhengguan_zhengyin_bureaucrat()
    test_no_solution_consumable()
    print("\n" + "=" * 60)
    print("🎉 所有事业分析测试通过！")
    print("=" * 60)
