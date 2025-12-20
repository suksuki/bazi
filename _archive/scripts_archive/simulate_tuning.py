import sys
import os
sys.path.append(os.getcwd())
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def run_sim():
    print("=== Case 001 Simulation: Tech Tycoon ===")
    # Pillars: Yi Wei, Bing Xu, Ren Xu, Xin Hai
    # Note: We need to use create_profile_from_case equivalent or mock it manually.
    # But calculate_chart takes birth time. 
    # The pillars are fixed. We can use engine._evaluate_wang_shuai directly.
    
    bazi_list = [("乙", "未"), ("丙", "戌"), ("壬", "戌"), ("辛", "亥")]
    dm = "壬"
    
    engine = QuantumEngine()
    
    # 1. Baseline Run
    print("\n[Baseline] Using Default Parameters")
    ws_base, score_base = engine._evaluate_wang_shuai(dm, bazi_list)
    print(f"Result: {ws_base} (Score: {score_base:.2f})")
    
    # 2. Tuning: Increase Hour Weight & Rooting
    print("\n[Tuning Phase 1] Boosting Hour & Rooting")
    new_conf = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # Boost Hour Weight (def 0.9 -> 1.2)
    new_conf['physics']['pillarWeights']['hour'] = 1.2
    
    # Boost Rooting (def 1.0 -> 1.5)
    new_conf['structure']['rootingWeight'] = 1.5
    
    # Boost Exposed Boost (def 1.5 -> 2.0)
    new_conf['structure']['exposedBoost'] = 2.0
    
    engine.update_full_config(new_conf)
    
    ws_tuned, score_tuned = engine._evaluate_wang_shuai(dm, bazi_list)
    print(f"Result: {ws_tuned} (Score: {score_tuned:.2f})")
    
    if "Strong" in ws_tuned:
        print("✅ SUCCESS: Turned Strong!")
    else:
        print("❌ STILL WEAK: Need more power.")

if __name__ == "__main__":
    run_sim()
