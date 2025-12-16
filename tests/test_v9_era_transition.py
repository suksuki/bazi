import sys
import os
sys.path.append(os.getcwd())
from core.engine_v88 import EngineV88 as EngineV91  # Alias for compatibility

def run_era_experiment():
    print("⏳ V9.1 Era Transition Test (Period 8 vs Period 9)")
    print("================================================")

    # 不用 Harbin，用标准位置，控制单一变量
    bazi = ["丙子", "庚子", "丙午", "壬辰"] 
    dm = "丙" # 弱火
    
    engine = EngineV91()
    
    years = [2023, 2024]
    
    print(f"{'Year':<6} | {'Period':<15} | {'Boosted Elem':<12} | {'🔥 Fire Score':<15} | {'⛰️ Earth Score':<15}")
    print("-" * 80)
    
    results = {}
    
    for year in years:
        # V9.0 analyze 接受 year 参数
        res = engine.analyze(bazi, dm, city="Unknown", year=year)
        
        # 获取 Era 信息
        fire = res.energy_distribution['fire']
        earth = res.energy_distribution['earth']
        
        # 简单判断 Period
        p_name = "Period 8 (Earth)" if year < 2024 else "Period 9 (Fire)"
        boost = "Earth" if year < 2024 else "Fire"
        
        results[year] = {'fire': fire, 'earth': earth}
        
        print(f"{year:<6} | {p_name:<15} | {boost:<12} | {fire:<15.2f} | {earth:<15.2f}")

    print("================================================")
    print("🔍 Analysis:")
    
    f_delta = results[2024]['fire'] - results[2023]['fire']
    e_delta = results[2023]['earth'] - results[2024]['earth']
    
    if f_delta > 0:
        print(f"✅ Fire Energy INCREASED in 2024: +{f_delta:.2f}")
    if e_delta > 0:
        print(f"✅ Earth Energy DECREASED in 2024 (relative to 2023): Gap is {e_delta:.2f}")
        # Note: In 2024 Earth loses the bonus, so it drops relative to 2023.

if __name__ == "__main__":
    run_era_experiment()
