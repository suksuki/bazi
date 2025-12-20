import sys
import os
import json
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.math import ProbValue

def run_regression():
    print("🌊 [Antigravity V12.1] 启动历史案例波动力学回归...")
    
    # 1. Load Config
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    try:
        if os.path.exists('config/parameters.json'):
            with open('config/parameters.json', 'r') as f:
                config.update(json.load(f))
    except Exception as e:
        print(f"⚠️ Config load warning: {e}")

    # --- Case 1: Steve Jobs (2011) ---
    print("\n🍏 [Case 1] Steve Jobs: Structural Collapse (2011)")
    verifier_jobs = Phase2Verifier(config)
    # 乙未 戊寅 壬午 辛亥 (Oct 2011 death - Xin Mao year)
    # Actually Steve Jobs: 
    # Year: 乙未 (Wood Earth)
    # Month: 戊寅 (Earth Wood)
    # Day: 壬午 (Water Fire) -> Weak Water, relying on Xin (Metal) and Hai (Water).
    # Hour: 辛亥 (Metal Water) or 庚子? 
    # The prompt says: 乙未 戊寅 壬午 辛亥. Let's use this.
    # 2011 Year: 辛卯 (Metal Wood). 
    # Interaction: Hai-Mao-Wei San He Wood (亥卯未 三合木).
    # Water (Hai) is transformed to Wood. Xin (Metal) is weak on Mao.
    # Result: Water lost roots.
    
    jobs_bazi = ['乙未', '戊寅', '壬午', '辛亥']
    
    # Initialize nodes with Liunian (Year Pillar)
    # Phase1: Initialize nodes (Original + Liunian)
    # Note: verify_case() in Phase2Verifier doesn't support Liunian/Dayun args yet, so we call engine.initialize_nodes directly.
    verifier_jobs.engine.initialize_nodes(jobs_bazi, '壬', year_pillar='辛卯')
    
    # [V13.9] Apply Quantum Entanglement (Transformation)
    verifier_jobs.engine._apply_quantum_entanglement_once()
    
    # Build Matrix (Field Coupling)
    verifier_jobs.engine.build_adjacency_matrix()
    
    # Propagate
    verifier_jobs.engine.propagate(max_iterations=1, damping=1.0)
    
    # Check Result
    water_energy = ProbValue(0.0, 0.1)
    wood_energy = ProbValue(0.0, 0.1)
    
    for node in verifier_jobs.engine.nodes:
        if node.element == 'water':
            water_energy = water_energy + node.current_energy
        if node.element == 'wood':
            wood_energy = wood_energy + node.current_energy
            
    print(f"  💧 水能量 (Self): {water_energy.mean:.2f}")
    print(f"  🌲 木能量 (Output): {wood_energy.mean:.2f}")
    
    # Expectation: Water < 8.0 (Drained), Wood > 80.0 (San He Boost)
    if water_energy.mean < 8.0 and wood_energy.mean > 80.0:
        print("  ✅ 验证通过: 波动力学成功模拟了'根气被合化'与'强力泄耗'。")
    else:
        print(f"  ❌ 验证失败: 抽水效应不足 (Water={water_energy.mean:.2f}, Wood={wood_energy.mean:.2f})")


    # --- Case 2: Elon Musk (2020) ---
    print("\n🚀 [Case 2] Elon Musk: Resonance Surge (2020)")
    
    verifier_musk = Phase2Verifier(config)
    musk_bazi = ['辛亥', '甲午', '甲申', '丙寅']
    
    # Pillar 4: Dayun (Luck) = 丙子
    # Pillar 5: Liunian (annual) = 庚子
    # Note in NodeInitializer: 
    # luck_pillar -> index 4
    # year_pillar -> index 5
    verifier_musk.engine.initialize_nodes(musk_bazi, '甲', luck_pillar='丙子', year_pillar='庚子')

    verifier_musk.engine._apply_quantum_entanglement_once()
    verifier_musk.engine.build_adjacency_matrix()
    verifier_musk.engine.propagate(max_iterations=1, damping=1.0)
    
    # Verify: Fire (Eating God) vs Metal (Killings)
    fire_energy = ProbValue(0.0, 0.1)
    metal_energy = ProbValue(0.0, 0.1)
    
    for node in verifier_musk.engine.nodes:
        if node.element == 'fire':
            fire_energy = fire_energy + node.current_energy
        if node.element == 'metal':
            metal_energy = metal_energy + node.current_energy
    
    print(f"  🔥 火能量 (Eating God): {fire_energy.mean:.2f}")
    print(f"  ⚔️ 金能量 (Killings): {metal_energy.mean:.2f}")
    
    if fire_energy.mean > metal_energy.mean * 0.8: 
        print("  ✅ 验证通过: 食神制杀有力 (Fire >= 0.8 * Metal).")
    else:
        print(f"  ❌ 验证失败: 金多火熄 (Fire={fire_energy.mean:.2f}, Metal={metal_energy.mean:.2f})")

if __name__ == "__main__":
    run_regression()
