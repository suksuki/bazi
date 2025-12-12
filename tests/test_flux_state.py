
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flux import FluxEngine

def test_state_management():
    print("Testing State Kernel V13.0 (Plastic Damage)...")
    
    # 1. Setup a chart susceptible to damage
    # Metal vs Wood Clash
    chart = {
        'year': {'stem': '庚', 'branch': '申'}, # Major Metal
        'month': {'stem': '甲', 'branch': '寅'}, # Major Wood (Target)
        'day': {'stem': '丙', 'branch': '午'},
        'hour': {'stem': '戊', 'branch': '辰'}
    }
    
    engine = FluxEngine(chart)
    
    # Year 1: Heavy Collision
    # Trigger: Liu Nian = Monkey (Shen) again.
    # Effect: Triple Metal (Year+LN) vs One Wood (Month)
    print("\n--- Year 1: The Impact ---")
    
    # We expect 'month_branch' (Tiger) to be Smashed.
    result1 = engine.calculate_flux(ln_stem='庚', ln_branch='申')
    
    state_map_y1 = result1['final_state_map']
    tiger_health_y1 = state_map_y1['month_branch']
    print(f"Tiger Health after Y1: {tiger_health_y1}")
    
    for log in result1['log']:
        if "PERMANENT DAMAGE" in log:
            print(f"✅ {log}")
            
    if tiger_health_y1 < 100.0:
        print("✅ Plastic Damage Applied Correctly")
    else:
        print("❌ Damage logic failed")
        
    # Year 2: Recovery Phase?
    # Trigger: Safe year (e.g. Rat / Water)
    print("\n--- Year 2: The Aftermath ---")
    engine2 = FluxEngine(chart)
    
    # Inject damaged state
    result2 = engine2.calculate_flux(ln_stem='壬', ln_branch='子', state_map=state_map_y1)
    
    # Check amplitude of Tiger
    tgt = next(p for p in engine2.particles if p.id == 'month_branch')
    print(f"Tiger Amplitude (Year 2): {tgt.wave.amplitude}")
    print(f"Tiger Health (Year 2): {tgt.health}")
    
    # Control Group: Healthy Year 2
    print("\n--- Control: Healthy Year 2 ---")
    engine_control = FluxEngine(chart)
    # Default health 100
    res_ctrl = engine_control.calculate_flux(ln_stem='壬', ln_branch='子') # No state map
    tgt_ctrl = next(p for p in engine_control.particles if p.id == 'month_branch')
    print(f"Tiger Amplitude (Healthy): {tgt_ctrl.wave.amplitude}")
    
    # Check suppression
    if tgt.wave.amplitude < tgt_ctrl.wave.amplitude:
        print(f"✅ Amplitude suppressed ({tgt.wave.amplitude:.1f} < {tgt_ctrl.wave.amplitude:.1f})")
    else:
        print(f"❌ Amplitude not suppressed ({tgt.wave.amplitude:.1f} >= {tgt_ctrl.wave.amplitude:.1f})")

if __name__ == "__main__":
    test_state_management()
