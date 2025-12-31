
import sys
import os
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(os.getcwd())
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController
from core.physics_engine import compute_energy_flux

def verify_case():
    controller = HolographicPatternController()
    
    # Inputs for the case
    pattern_id = "SP_A03_STANDARD"
    chart = ["庚辰", "乙酉", "庚子", "丙戌"]
    day_master = "庚"
    
    # 2026 Bing Wu context
    context = {
        'luck_pillar': '癸巳',
        'annual_pillar': '丙午',
        'geo_city': 'Beijing'
    }
    
    print(f"--- Verifying Case: {pattern_id} ---")
    
    # Debug energy flux
    e_blade = compute_energy_flux(chart, day_master, "羊刃")
    e_kill = compute_energy_flux(chart, day_master, "七杀")
    print(f"Energies: E_blade={e_blade:.4f}, E_kill={e_kill:.4f}")
    if e_kill > 0:
        print(f"Ratio (Blade/Kill): {e_blade/e_kill:.4f}")
    
    result = controller.calculate_tensor_projection(
        pattern_id=pattern_id,
        chart=chart,
        day_master=day_master,
        context=context
    )
    
    recognition = result.get('recognition', {})
    print(f"SAI: {result.get('sai', 0):.4f}")
    print(f"Precision Score: {recognition.get('precision_score', 0):.4f}")
    print(f"Pattern Type: {recognition.get('pattern_type')}")
    print(f"Description: {recognition.get('description')}")

if __name__ == "__main__":
    verify_case()
