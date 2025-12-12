
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.meaning import MeaningEngine

def test_meaning_v24_entrepreneur():
    print("\n--- Test 1: Entrepreneur (Fire DM, Earth EG, Water 7K) ---")
    # Day Master: Bing (Fire)
    # 7K: Ren (Water) - Strong
    # EG: Wu (Earth) - Strong
    
    chart = {'day': {'stem': '丙'}}
    
    # Mock Flux Result
    flux_result = {
        'particle_states': [
            {'id': 'day_stem', 'char': '丙', 'amp': 40.0, 'health': 100.0, 'status': []}, # Strong Self
            {'id': 'year_stem', 'char': '壬', 'amp': 30.0, 'health': 100.0, 'status': []}, # Strong 7K
            {'id': 'month_stem', 'char': '戊', 'amp': 25.0, 'health': 100.0, 'status': []}, # Strong EG
        ],
        'log': []
    }
    
    engine = MeaningEngine(chart, flux_result)
    report = engine.analyze()
    
    print("Work Modes:")
    for m in report['work_modes']:
        print(f"  - {m['type']}: {m['desc']}")
        
    print(f"Wealth Score: {report['wealth_potential']['score']} ({report['wealth_potential']['rating']})")
    
    print("Patterns:")
    for p in report['macro_patterns']:
        print(f"  - {p['name']}")
        
    # Validation
    modes = [m['type'] for m in report['work_modes']]
    if "Zhi Heng (Balancing)" in modes:
        print("✅ Zhi Heng detected")
    else:
        print("❌ Zhi Heng MISSING")
        
    patterns = [p['name'] for p in report['macro_patterns']]
    if "Entrepreneurial Structure" in patterns:
        print("✅ Entrepreneur Pattern detected")
    else:
        print("❌ Entrepreneur Pattern MISSING")

def test_meaning_v24_influencer():
    print("\n--- Test 2: Influencer (Wood DM, Fire Output) ---")
    # Day Master: Jia (Wood)
    # Output: Bing (Fire) - Strong
    
    chart = {'day': {'stem': '甲'}}
    
    flux_result = {
        'particle_states': [
            {'id': 'day_stem', 'char': '甲', 'amp': 30.0, 'health': 100.0, 'status': []}, 
            {'id': 'month_stem', 'char': '丙', 'amp': 50.0, 'health': 100.0, 'status': []}, # Fire Output
        ],
        'log': []
    }
    
    engine = MeaningEngine(chart, flux_result)
    report = engine.analyze()
    
    patterns = [p['name'] for p in report['macro_patterns']]
    if "Digital Influencer / Fame" in patterns:
         print("✅ Influencer Pattern detected")
    else:
         print(f"❌ Influencer Pattern MISSING. Found: {patterns}")

def test_meaning_v24_collision():
    print("\n--- Test 3: Collision Work (Tomb Opened) ---")
    # Day: Any
    # Branch: Chen (Tomb) -> Ruptured
    
    chart = {'day': {'stem': '甲'}}
    
    flux_result = {
        'particle_states': [
            {'id': 'day_stem', 'char': '甲', 'amp': 20.0, 'health': 100.0, 'status': []}, 
            {'id': 'year_branch', 'char': '辰', 'amp': 40.0, 'health': 80.0, 'status': ["ShellRuptured"]}, 
        ],
        'log': ["Collision ..."]
    }
    
    engine = MeaningEngine(chart, flux_result)
    report = engine.analyze()
    
    modes = [m['type'] for m in report['work_modes']]
    if "Collision (Peng Zhang)" in modes:
        print("✅ Collision Work detected")
    else:
        print("❌ Collision Work MISSING")
        
    # Check Wealth Cost?
    print(f"Acquisition Cost: {report['wealth_potential']['components']['friction']}")

if __name__ == "__main__":
    test_meaning_v24_entrepreneur()
    test_meaning_v24_influencer()
    test_meaning_v24_collision()
