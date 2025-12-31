
import numpy as np
import json
import logging
from typing import List, Dict

# Set up logging to show the process
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("IntegrationTest")

from core.physics_engine import compute_energy_flux, calculate_clash_count
from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter

def run_integration_test():
    # 1. Target Chart: "古墓丽影" (Tomb Raider)
    # 癸亥 己未 乙丑 辛巳, DM: 乙
    chart = ["癸亥", "己未", "乙丑", "辛巳"]
    day_master = "乙"
    
    logger.info(f"--- 🌉 Integration Test: '古墓丽影' (Tomb Raider) ---")
    logger.info(f"Chart: {' '.join(chart)} | DM: {day_master}\n")

    # 2. Step A: Feature Extraction (Vector Flux V9.5)
    # Mapping our 10-god logic to the 7D Input Vector
    # Input Mapping: [parallel, resource, power, wealth, output, clash, combination]
    
    # helper for parallel (比肩+劫财)
    parallel_score = compute_energy_flux(chart, day_master, "比肩") + \
                     compute_energy_flux(chart, day_master, "劫财")
    
    # helper for resource (正印+偏印)
    resource_score = compute_energy_flux(chart, day_master, "正印") + \
                     compute_energy_flux(chart, day_master, "偏印")
    
    # helper for power (七杀+正官)
    power_score = compute_energy_flux(chart, day_master, "七杀") + \
                  compute_energy_flux(chart, day_master, "正官")
    
    # helper for wealth (正财+偏财)
    wealth_score = compute_energy_flux(chart, day_master, "正财") + \
                   compute_energy_flux(chart, day_master, "偏财")
    
    # helper for output (食神+伤官)
    output_score = compute_energy_flux(chart, day_master, "食神") + \
                   compute_energy_flux(chart, day_master, "伤官")
    
    # clash energy (丑未冲)
    # calculate_clash_count includes Harms, but here we focus on the raw metric
    clash_energy = calculate_clash_count(chart) * 0.5
    
    combination_energy = 0.0 # Interaction logic for combinations to be refined
    
    x_input = np.array([
        parallel_score,
        resource_score,
        power_score,
        wealth_score,
        output_score,
        clash_energy,
        combination_energy
    ])
    
    logger.info("--- 1. Step A: Vector Flux Extraction ---")
    logger.info(f"parallel: {parallel_score:.4f}")
    logger.info(f"resource: {resource_score:.4f}")
    logger.info(f"power:    {power_score:.4f}")
    logger.info(f"wealth:   {wealth_score:.4f}")
    logger.info(f"output:   {output_score:.4f}")
    logger.info(f"clash:    {clash_energy:.4f}")
    logger.info(f"x_vector: {x_input}\n")

    # 3. Step B: Matrix Projection via RegistryLoader (FDS-V1.4 Workflow)
    from core.registry_loader import RegistryLoader
    
    # Initialize RegistryLoader - will load registry.json automatically
    loader = RegistryLoader()
    
    # Context (Luck/Annual for InfluenceBus)
    context = {
        "luck_pillar": "辛丑",
        "annual_pillar": "乙未"
    }

    # Execute Projection!
    # This will trigger: 
    # 1. Input Mapping
    # 2. InfluenceBus Arbitration
    # 3. Registry Dynamics (tanh_saturation k=3.0) 
    # 4. Matrix Projection
    result = loader.calculate_tensor_projection_from_registry(
        "A-03", chart, day_master, context=context
    )
    
    output_dict = result.get('raw_projection', {})
    sai = result.get('sai', 0.0)
    recognition = result.get('recognition', {})
    
    logger.info("--- 2. Step B: Registry-Driven Projection (A-03) ---")
    logger.info(f"FDS-V1.5 Schema: {result.get('version')}")
    logger.info(f"Pattern State: {result.get('pattern_state', {}).get('state')}")
    logger.info(f"Recognition: {recognition.get('pattern_type')} (Sim: {recognition.get('similarity', 0):.4f})")
    logger.info(f"M-Dist: {recognition.get('mahalanobis_dist', 0):.4f} | Prec-Score: {recognition.get('precision_score', 0):.4f}")
    logger.info(f"Matched Anchor: {recognition.get('anchor_id')}")
    logger.info(f"SAI (System Integrity): {sai:.4f}")
    logger.info(f"Tensor Projection (raw): {json.dumps(output_dict, indent=2)}")
    
    # 4. Step C: Physics Verification
    logger.info("\n--- 3. Step C: Physics Verification ---")
    o_val = output_dict.get('O', 0)
    e_val = output_dict.get('E', 0)
    
    if o_val > 0.6:
        logger.info(f"✅ O-Axis (Order) check passed: {o_val:.4f} > 0.6 (Established Authority)")
    else:
        logger.info(f"❌ O-Axis (Order) check failed: {o_val:.4f} <= 0.6 (Poor Command)")
        
    if e_val > 0.8:
        logger.info(f"✅ E-Axis (Energy) check passed: {e_val:.4f} > 0.8 (Tomb Release Explosion)")
    else:
        logger.info(f"❌ E-Axis (Energy) check failed: {e_val:.4f} <= 0.8 (Weak Foundation)")

if __name__ == "__main__":
    run_integration_test()
