import sys
import os
import json
import logging
import math

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.math.distributions import ProbValue
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def run_tuning():
    print("🌊 [Phase 9] Wave Dynamics Tuning: Entropy & Recoil")
    
    # 1. Load Parameters (Simulate reading from config)
    # Default values from the user directive if not in file
    params = {
        "dampingFactor": 0.1,
        "transmissionNoise": 0.5,
        "recoilFactor": 0.3
    }
    
    # Try loading from actual file if updated
    try:
        with open('config/parameters.json', 'r') as f:
            full_config = json.load(f)
            flow = full_config.get('flow', {})
            medium = flow.get('medium', {})
            interaction = flow.get('interaction', {})
            
            if 'dampingFactor' in medium: params['dampingFactor'] = medium['dampingFactor']
            if 'transmissionNoise' in medium: params['transmissionNoise'] = medium['transmissionNoise']
            if 'recoilFactor' in interaction: params['recoilFactor'] = interaction['recoilFactor']
            
            print(f"  📂 Loaded params from config: {params}")
    except Exception as e:
        print(f"  ⚠️ Using default params: {e}")

    # --- Experiment F1: Nurturing (Water generates Wood) ---
    print("\n🌱 [Experiment F1] Nurturing (Water -> Wood)")
    
    # Source: Water (Strong)
    water = ProbValue(10.0, std_dev_percent=0.1) # Mean=10.0, Std=1.0
    print(f"  💧 Source (Water): {water}")
    
    # Target: Wood (Weak, waiting for support)
    wood = ProbValue(2.0, std_dev_percent=0.2) # Mean=2.0, Std=0.4
    print(f"  🌲 Target (Wood):  {wood}")
    
    # Action: Transmit
    # Energy transmitted = Source * (?) 
    # In physics, source emits a wave. The wave travels and hits target.
    # The magnitude of the wave depends on Source.
    # Let's say the potential coupling is maximal (1.0).
    # Then the energy arriving is water.transmit(damping, noise).
    
    # Note: In GNN, usually delta = Weight * Source.
    # Here, weight implies damping.
    # Let's simulate the packet arriving at Wood.
    
    incoming_wave = water.transmit(
        damping_factor=params['dampingFactor'],
        noise_floor=params['transmissionNoise']
    )
    print(f"  🌊 Incoming Wave:  {incoming_wave}")
    
    # Wood absorbs the wave (Addition)
    new_wood = wood + incoming_wave
    print(f"  🌲 New Wood:       {new_wood}")
    
    # Verification F1
    # 1. Energy conservation check (Mean should increase)
    # 2. Entropy check (Std should increase more than simple addition due to noise)
    
    print(f"     Delta Mean: {new_wood.mean - wood.mean:+.2f}")
    print(f"     Delta Std:  {new_wood.std - wood.std:+.2f}")
    
    if new_wood.mean > wood.mean and new_wood.std > wood.std:
        print("  ✅ F1 Passed: Energy increased, Entropy increased (Signal + Noise).")
    else:
        print("  ❌ F1 Failed: Physics violation.")

    # --- Experiment F2: War (Water controls Fire) ---
    print("\n⚔️ [Experiment F2] War (Water -> Fire)")
    
    # Attacker: Water
    water_atk = ProbValue(10.0, std_dev_percent=0.1)
    print(f"  💧 Attacker (Water): {water_atk}")
    
    # Defender: Fire
    fire_def = ProbValue(8.0, std_dev_percent=0.1)
    print(f"  🔥 Defender (Fire):  {fire_def}")
    
    # Action: Control (Attack)
    # Damage dealt (simplified) depends on Attacker strength.
    # Let's say direct hit.
    damage_potential = water_atk.transmit(params['dampingFactor'], 0.0) # Pure force transmission?
    # Or just use raw mean for calculation logic, but user said "Recoil" affects the attacker.
    
    damage_dealt = 5.0 # Assume calculated damage
    
    # Reaction: Attacker feels recoil
    new_water = water_atk.react(
        damage_dealt=damage_dealt,
        recoil_factor=params['recoilFactor']
    )
    print(f"  💧 New Water (Post-Recoil): {new_water}")
    
    # Verification F2
    # 1. Attacker loses energy (Recoil)
    # 2. Attacker stability collapses (Std increases significantly)
    
    print(f"     Delta Mean: {new_water.mean - water_atk.mean:+.2f}")
    print(f"     Delta Std:  {new_water.std - water_atk.std:+.2f}")
    
    if new_water.mean < water_atk.mean and new_water.std > water_atk.std * 1.2:
        print("  ✅ F2 Passed: Recoil damage taken, Stability collapsed (Volatility Surge).")
    else:
        print(f"  ❌ F2 Failed: Recoil/Entropy insufficient. (Ratio: {new_water.std/water_atk.std:.2f})")

if __name__ == "__main__":
    run_tuning()
