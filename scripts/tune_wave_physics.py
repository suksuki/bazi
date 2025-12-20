import json
import math
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 模拟 WavePhysicsEngine 逻辑
def simulate_wave(energy_a, energy_b, theta_deg, entropy=0.95):
    amp_a = math.sqrt(energy_a)
    amp_b = math.sqrt(energy_b)
    # E = A^2 + B^2 + 2ABcos(theta)
    interference = 2 * amp_a * amp_b * math.cos(math.radians(theta_deg))
    return (energy_a + energy_b + interference) * entropy

def simulate_resonance(energies, q_factor):
    return sum(energies) * q_factor

def tune_parameters():
    # 1. 加载数据
    data_path = 'data/wave_physics_cases.json'
    if not os.path.exists(data_path):
        print(f"❌ 找不到数据文件: {data_path}")
        return
        
    with open(data_path, 'r') as f:
        cases = json.load(f)
        
    print("🌊 启动波动力学参数网格搜索 (Grid Search)...")
    
    # 2. 定义搜索空间
    # 冲/刑的相位角: 150度 ~ 180度 (反相/相消)
    clash_thetas = np.arange(150, 185, 1) # 精细搜索
    # 共振Q值: 1.1 ~ 2.0
    resonance_qs = np.arange(1.1, 2.0, 0.05)
    # 合局相位角: 0度 ~ 30度 (同相/相长)
    combine_thetas = np.arange(0, 45, 1)
    
    # 3. 调优冲局 (Clash Phase Angle)
    print("\n[1] 正在调优冲局相位角 (Clash Phase Angle)...")
    clash_cases = [c for c in cases if c['type'] == 'clash']
    
    best_clash_error = float('inf')
    best_clash_theta = 0
    
    if clash_cases:
        for theta in clash_thetas:
            total_error = 0
            for case in clash_cases:
                energies = list(case['initial_energies'].values())
                e1, e2 = energies[0], energies[1]
                sim_e = simulate_wave(e1, e2, theta, entropy=0.9) # 假设 0.9 熵损
                target = case['expectation']['target_energy_sum']
                total_error += (sim_e - target) ** 2
                
            if total_error < best_clash_error:
                best_clash_error = total_error
                best_clash_theta = theta
        print(f"✅ 最佳冲相位角: {best_clash_theta}° (MSE: {best_clash_error:.4f})")

    # 4. 调优共振 (Resonance Q)
    print("\n[2] 正在调优土刑共振因子 (Resonance Q-Factor)...")
    res_cases = [c for c in cases if c['type'] == 'earth_punish']
    
    best_res_error = float('inf')
    best_q = 0
    
    if res_cases:
        for q in resonance_qs:
            total_error = 0
            for case in res_cases:
                energies = list(case['initial_energies'].values())
                sim_e = simulate_resonance(energies, q)
                target = case['expectation']['target_energy_sum']
                total_error += (sim_e - target) ** 2
                
            if total_error < best_res_error:
                best_res_error = total_error
                best_q = q
        print(f"✅ 最佳共振 Q因子: {best_q:.2f} (MSE: {best_res_error:.4f})")

    # 5. 调优合局 (Combine Phase Angle)
    print("\n[3] 正在调优合局相位角 (Combine Phase Angle)...")
    comb_cases = [c for c in cases if c['type'] == 'combine']
    
    best_comb_error = float('inf')
    best_comb_theta = 0
    
    if comb_cases:
        for theta in combine_thetas:
            total_error = 0
            for case in comb_cases:
                energies = list(case['initial_energies'].values())
                e1, e2 = energies[0], energies[1]
                sim_e = simulate_wave(e1, e2, theta, entropy=0.9)
                target = case['expectation']['target_energy_sum']
                total_error += (sim_e - target) ** 2
                
            if total_error < best_comb_error:
                best_comb_error = total_error
                best_comb_theta = theta
        print(f"✅ 最佳合相位角: {best_comb_theta}° (MSE: {best_comb_error:.4f})")

    print("\n--- 推荐物理常数 (V12.0) ---")
    print(f"clashPhase_rad: {math.radians(best_clash_theta):.4f} ({best_clash_theta}°)")
    print(f"resonanceQ: {best_q:.2f}")
    print(f"combinePhase_rad: {math.radians(best_comb_theta):.4f} ({best_comb_theta}°)")

if __name__ == "__main__":
    tune_parameters()
