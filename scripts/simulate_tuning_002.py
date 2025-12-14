import sys
import os
sys.path.append(os.getcwd())
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def run_sim_002():
    print("=== Case 002 Simulation: Star Actress ===")
    # Pillars: Bing Yin, Gui Si, Xin Chou, Gui Si
    # DM: Xin (Metal)
    # Month: Si (Fire). Year: Yin (Wood). Hour: Si (Fire).
    # Fire is overwhelmingly strong. Official Star.
    # Day Branch: Chou (Earth). This is wet earth.
    
    bazi_list = [("丙", "寅"), ("癸", "巳"), ("辛", "丑"), ("癸", "巳")]
    dm = "辛"
    
    engine = QuantumEngine()
    
    # 1. Baseline
    print("\n[Baseline] Using Default Parameters")
    ws_base, score_base = engine._evaluate_wang_shuai(dm, bazi_list)
    print(f"Result: {ws_base} (Score: {score_base:.2f})")
    
    # Check if Follower
    # Follower usually means Weak but score is extreme? Or logic explicitly checks for Follower?
    # engine returns "Weak" or "Strong" or "Follower"?
    # The output string usually contains "Weak" or "Strong".
    
    # 2. Tuning: Maximize Wet Earth (Chou)
    print("\n[Tuning Phase] Boosting Wet Earth & Rooting")
    new_conf = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # Increase Rooting (Chou is root for Xin)
    new_conf['structure']['rootingWeight'] = 2.0
    
    # Increase Same Pillar Bonus (Xin Chou is self-sitting)
    new_conf['structure']['samePillarBonus'] = 1.5
    
    # Macro Physics: Latitude Cold?
    # Maybe reduce Season Weights for "Si" (Fire)?
    
    engine.update_full_config(new_conf)
    
    ws_tuned, score_tuned = engine._evaluate_wang_shuai(dm, bazi_list)
    print(f"Result: {ws_tuned} (Score: {score_tuned:.2f})")

if __name__ == "__main__":
    run_sim_002()
