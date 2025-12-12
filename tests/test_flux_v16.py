
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flux import FluxEngine

def test_spacetime_dynamics():
    print("Testing Spacetime Dynamics V16.0...")
    
    # Chart: Needs repair
    # Year: Geng Shen (Metal)
    # Month: Jia Yin (Wood) <--- CLASH with Year
    # Day: Bing Wu (Fire)
    # Hour: Wu Chen (Earth)
    # Missing: WATER (Bridge between Metal and Wood)
    
    chart = {
        'year': {'stem': '庚', 'branch': '申'},
        'month': {'stem': '甲', 'branch': '寅'},
        'day': {'stem': '丙', 'branch': '午'},
        'hour': {'stem': '戊', 'branch': '辰'}
    }
    
    # Case 1: Da Yun = Water (Repair)
    print("\n--- Case 1: Da Yun Repair (Water) ---")
    engine = FluxEngine(chart)
    # Set Da Yun to Ren Zi (Water)
    engine.calculate_flux(dy_stem='壬', dy_branch='子')
    
    repaired = False
    for log in engine.log:
        if "Structural Repair" in log:
            print(f"✅ {log}")
            repaired = True
    if not repaired:
        print("❌ Repair failed")
        
    # Case 2: Liu Nian = Clash (Monkey vs Tiger)
    print("\n--- Case 2: Liu Nian Clash (Monkey) ---")
    engine2 = FluxEngine(chart)
    # Set Liu Nian to Geng Shen (Metal) again -> Double Clash on Month (Tiger)
    engine2.calculate_flux(ln_stem='庚', ln_branch='申')
    
    clashed = False
    for log in engine2.log:
        if "CRITICAL" in log and "CLASHES 寅" in log:
            print(f"✅ {log}")
            clashed = True
            
    # Check status of Tiger
    tiger = next((p for p in engine2.particles if p.char == '寅' and "month" in p.id), None)
    if tiger:
        print(f"Tiger Status: {tiger.status}")
        if "StructureBroken" in tiger.status:
            print("✅ Tiger Structure Broken (Expected)")
        else:
             print("❌ Tiger survived? (Unexpected)")

if __name__ == "__main__":
    test_spacetime_dynamics()
