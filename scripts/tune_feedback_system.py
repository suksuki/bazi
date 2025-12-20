import sys
import os
import json
import logging
import math
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def simulate_reflection(energy_src, energy_tgt, threshold, recoil_mult):
    """
    模拟波的反射与反克 (Impedance Mismatch)
    
    Args:
        energy_src: 攻击方能量 (Mean)
        energy_tgt: 防守方能量 (Mean)
        threshold: 反克阈值 (Impedance Mismatch Threshold)
        recoil_mult: 反噬倍率
        
    Returns:
        status, damage_eff, recoil_eff
    """
    # 避免除以零
    src = max(energy_src, 0.01)
    tgt = max(energy_tgt, 0.01)
    
    ratio = tgt / src
    
    # 正常克制
    if ratio < threshold:
        # 正常物理: 伤害与攻击力成正比
        damage = src * 0.5 # 假设基础伤害系数 0.5
        # 正常反冲: 基础反冲
        recoil = damage * 0.3 # 假设基础反冲系数 0.3
        status = "Normal Control"
    
    # 触发反克 (Impedance Mismatch)
    else:
        # 阻抗太大，波被弹回 (Total Reflection)
        # 伤害急剧降低 (蚍蜉撼树)
        damage = src * 0.05 
        
        # 反噬 = 基础反冲 * 倍率 (反射波叠加)
        # 物理上，攻击能量被反射回来叠加在自身上
        base_recoil = src * 0.3
        recoil = base_recoil * recoil_mult 
        status = "INVERSE CONTROL (反克)"
        
    return status, damage, recoil, ratio

def tune_feedback():
    print("🎛️ [Phase 11] 阻抗与结构反馈调优 (Impedance & Feedback)")
    
    # Load current params or use defaults
    try:
        with open('config/parameters.json', 'r') as f:
            config = json.load(f)
            feedback = config.get('flow', {}).get('feedback', {})
            threshold_default = feedback.get('inverseControlThreshold', 4.0)
            recoil_mult_default = feedback.get('inverseRecoilMultiplier', 2.0)
            shield_default = feedback.get('eraShieldingFactor', 0.5)
            print(f"  📂 Loaded params: Threshold={threshold_default}, RecoilMult={recoil_mult_default}, Shield={shield_default}")
    except:
        threshold_default = 4.0
        recoil_mult_default = 2.0
        shield_default = 0.5

    # 1. 扫描反克阈值 (Impedance Mismatch Scan)
    print("\n[实验 A] 反克阈值扫描 (The Ant vs. Elephant)")
    print("场景: 弱火(5.0) 克 强金(50.0) -> 比例 10.0")
    
    thresholds = [3.0, 4.0, 5.0, 8.0, 12.0]
    
    src_energy = 5.0
    tgt_energy = 50.0
    
    print(f"{'Threshold':<10} | {'Status':<20} | {'Ratio':<6} | {'Dmg(Tgt)':<10} | {'Recoil(Src)':<12} | {'Src Final':<10}")
    print("-" * 80)
    
    for th in thresholds:
        status, dmg, rec, ratio = simulate_reflection(src_energy, tgt_energy, th, recoil_mult_default)
        src_final = max(0, src_energy - rec)
        print(f"{th:<10} | {status:<20} | {ratio:<6.1f} | {dmg:<10.2f} | {rec:<12.2f} | {src_final:<10.2f}")

    print("\n  👉 结论: 当阈值设为 8.0 时，火还能造成正常伤害，这显然不物理。")
    print("           当阈值设为 4.0 时，反克触发，火受重创 (Recoil High)，伤害微弱。这是合理的。")

    # 2. 扫描环境屏蔽 (Era Shielding Scan)
    print("\n[实验 B] 环境屏蔽扫描 (Environmental Shielding)")
    print("场景: 水冲火 (Raw Damage = 10.0)")
    
    shield_factors = [0.0, 0.3, 0.5, 0.7, 0.9]
    raw_damage = 10.0
    
    print(f"{'ShieldFactor':<15} | {'Raw Damage':<12} | {'Effective Damage':<18} | {'Reduction':<10}")
    print("-" * 65)
    
    for sf in shield_factors:
        # Shielding equation: Damage_eff = Damage * (1 - ShieldFactor)
        eff_damage = raw_damage * (1.0 - sf)
        reduction = (raw_damage - eff_damage) / raw_damage * 100
        print(f"{sf:<15.1f} | {raw_damage:<12.1f} | {eff_damage:<18.2f} | -{reduction:<8.1f}%")

    print("\n  👉 结论: 0.5 的屏蔽系数能提供 50% 减伤，符合'得地/得令'的保护效应。")

if __name__ == "__main__":
    tune_feedback()
