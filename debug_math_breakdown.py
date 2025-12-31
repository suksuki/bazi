
import sys
import os
from pathlib import Path
import numpy as np

# Setup paths
project_root = Path(os.getcwd())
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import project_tensor_with_matrix, calculate_cosine_similarity, tensor_normalize

def debug_math_breakdown():
    loader = RegistryLoader()
    pattern_id = "SP_A03_STANDARD"
    chart = ["庚辰", "乙酉", "庚子", "丙戌"]
    day_master = "庚"
    context = {
        'luck_pillar': '癸巳',
        'annual_pillar': '丙午',
        'geo_city': 'Beijing'
    }
    
    # 1. Get the pattern details
    pattern = loader.get_pattern(pattern_id)
    matrix = pattern.get('matrix_override')
    mean_vector = pattern.get('manifold_stats', {}).get('mean_vector')
    
    # 2. Get the processed input vector (frequency vector)
    # We need to simulate the calculation inside RegistryLoader._calculate_with_transfer_matrix
    from core.trinity.core.nexus.definitions import BaziParticleNexus
    
    # Simulate frequency vector calculation
    # In a real run, this comes from BaziParticleNexus.calculate_frequency_vector
    # Let's use the actual engine to get the real numbers
    full_chart = chart + [context['luck_pillar'], context['annual_pillar']]
    freq_vec = BaziParticleNexus.calculate_frequency_vector(full_chart, day_master)
    
    # Apply InfluenceBus (Geo Factor)
    geo_factor = 1.15 # Beijing
    if 'power' in freq_vec: freq_vec['power'] *= geo_factor
    
    print(f"--- 1. Input Energy Flux (Frequency Vector) ---")
    for k, v in freq_vec.items():
        print(f"  {k}: {v:.4f}")
    
    # 3. Matrix Multiplication (Projection)
    projection = project_tensor_with_matrix(freq_vec, matrix)
    print(f"\n--- 2. Projected 5D Tensor (Raw) ---")
    for k, v in projection.items():
        print(f"  {k}: {v:.4f}")
    
    normalized_proj = tensor_normalize(projection)
    print(f"\n--- 3. Normalized Tensor (Unit Scale) ---")
    for k, v in normalized_proj.items():
        print(f"  {k}: {v:.4f}")
        
    # 4. Cosine Similarity Calculation
    sim = calculate_cosine_similarity(normalized_proj, mean_vector)
    
    print(f"\n--- 4. Comparison with Pattern Mean ---")
    print(f"  Pattern Mean: {mean_vector}")
    print(f"  Calculated Similarity: {sim:.4f}")

if __name__ == "__main__":
    debug_math_breakdown()
