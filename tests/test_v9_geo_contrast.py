import sys
import os
import json

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.engine_v88 import EngineV88 as EngineV91  # Alias for compatibility

def run_geo_experiment():
    print("🌍 V9.1 Latitude Survival Test (Geo Contrast)")
    print("============================================")

    # 1. 准备实验对象：冬天的丙火 (急需火来调候)
    # 八字: 丙子年, 庚子月, 丙午日, 壬辰时 (典型的水旺火弱)
    bazi = ["丙子", "庚子", "丙午", "壬辰"]
    dm = "丙"
    
    # 初始化 V9.1 引擎
    engine = EngineV91()
    
    # 2. 定义对照组
    scenarios = [
        {"city": "Unknown", "lat_desc": "Baseline (None)", "year": 2024},
        {"city": "Harbin",   "lat_desc": "High Lat (45N)", "year": 2024},
        {"city": "Singapore","lat_desc": "Equator (1N)",   "year": 2024},
    ]

    results = []

    for case in scenarios:
        # 调用 V9.1 分析
        analysis = engine.analyze(
            bazi=bazi, 
            day_master=dm, 
            city=case['city'], 
            year=case['year']
        )
        
        # Extract Data
        # V8.8/9.0 returns AnalysisResponse object
        # energy_distribution is a dict
        dist = analysis.energy_distribution
        verdict = analysis.strength.verdict
        
        results.append({
            "loc": case['city'],
            "desc": case['lat_desc'],
            "fire": dist.get('fire', 0),
            "water": dist.get('water', 0),
            "verdict": verdict
        })

    # 3. 输出对比报告
    print(f"\n{'Location':<12} | {'Description':<16} | {'🔥 Fire':<10} | {'💧 Water':<10} | {'Verdict':<10}")
    print("-" * 75)
    
    base_fire = results[0]['fire']
    base_water = results[0]['water']
    
    for res in results:
        # Calc Diff
        fire_diff = ((res['fire'] - base_fire) / base_fire * 100) if base_fire > 0 else 0.0
        water_diff = ((res['water'] - base_water) / base_water * 100) if base_water > 0 else 0.0
        
        f_str = f"{res['fire']:.1f}"
        if res['loc'] != "Unknown":
            f_str += f" ({fire_diff:+.0f}%)"
            
        w_str = f"{res['water']:.1f}"
        if res['loc'] != "Unknown":
            w_str += f" ({water_diff:+.0f}%)"
        
        print(f"{res['loc']:<12} | {res['desc']:<16} | {f_str:<10} | {w_str:<10} | {res['verdict']}")

    print("=" * 75)
    print("🔍 Analysis:")
    
    harbin = results[1]
    sg = results[2]
    
    if sg['fire'] > harbin['fire']:
        print(f"✅ HYPOTHESIS CONFIRMED: Singapore Fire ({sg['fire']:.1f}) >> Harbin Fire ({harbin['fire']:.1f})")
        print("   -> V9.1 Geo Layer is correctly modifying elemental weights.")
    else:
        print("❌ HYPOTHESIS FAILED: No significant difference found.")

if __name__ == "__main__":
    run_geo_experiment()
