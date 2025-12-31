
import sys
import os
from pathlib import Path
import math

# Setup paths
project_root = Path(os.getcwd())
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.physics_engine import compute_energy_flux, calculate_clash_count
from core.trinity.core.middleware.influence_bus import InfluenceBus
from core.trinity.core.middleware.temporal_factors import TemporalInjectionFactor
from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine
from core.math_engine import project_tensor_with_matrix, tensor_normalize, calculate_cosine_similarity

def breakdown_07288():
    loader = RegistryLoader()
    pattern_id = "SP_A03_STANDARD"
    chart = ["庚辰", "乙酉", "庚子", "丙戌"]
    day_master = "庚"
    context = {
        'luck_pillar': '癸巳',
        'annual_pillar': '丙午',
        'geo_city': 'Beijing',
        'day_master': '庚' # CRITICAL FIX
    }
    
    # 1. Base Energies
    parallel = compute_energy_flux(chart, day_master, "比肩") + compute_energy_flux(chart, day_master, "劫财")
    resource = compute_energy_flux(chart, day_master, "正印") + compute_energy_flux(chart, day_master, "偏印")
    power = compute_energy_flux(chart, day_master, "七杀") + compute_energy_flux(chart, day_master, "正官")
    wealth = compute_energy_flux(chart, day_master, "正财") + compute_energy_flux(chart, day_master, "偏财")
    output = compute_energy_flux(chart, day_master, "食神") + compute_energy_flux(chart, day_master, "伤官")
    
    freq_vec = {
        "parallel": parallel, "resource": resource, "power": power, 
        "wealth": wealth, "output": output
    }
    
    # 2. Influence Bus (Arbitration)
    bus = InfluenceBus()
    bus.register(TemporalInjectionFactor())
    
    # Fake wave objects for compatibility
    class MockWave:
        def __init__(self, val): self.amplitude = val
        
    waves_dict = {k: MockWave(v) for k, v in freq_vec.items()}
    verdict = bus.arbitrate_environment(waves_dict, context)
    
    # Update with arbitrated values
    freq_vec = {k: verdict['expectation'].elements.get(k, 0) for k in freq_vec.keys()}
    print(f"--- [Step 2] After Temporal Injection ---")
    for k, v in freq_vec.items():
        print(f"  {k:15}: {v:.4f}")

    # 3. Interactions (Clash)
    clash_energy = calculate_clash_count(chart) * 0.5
    stems = [p[0] for p in chart]
    branches = [p[1] for p in chart]
    vib_engine = StructuralVibrationEngine(day_master)
    v_metrics = vib_engine.calculate_vibration_metrics(stems, branches, context)
    impedance = v_metrics.get('impedance_magnitude', 1.0)
    clash_energy *= (1.0 + (impedance - 1.0) * 0.2)
    
    freq_vec['clash'] = round(clash_energy, 4)
    freq_vec['combination'] = 0.0

    # 4. Matrix Projection
    pattern = loader.get_pattern(pattern_id)
    matrix = pattern.get('matrix_override')
    
    projection = project_tensor_with_matrix(freq_vec, matrix)
    normalized_proj = tensor_normalize(projection)
    
    # 5. Matching
    mean_vector = pattern.get('manifold_stats', {}).get('mean_vector')
    sim = calculate_cosine_similarity(normalized_proj, mean_vector)
    
    print(f"\n--- Result ---")
    print(f"  SAI (L2): {math.sqrt(sum(v**2 for v in projection.values())):.4f}")
    print(f"  Similarity: {sim:.4f}")

if __name__ == "__main__":
    breakdown_07288()
