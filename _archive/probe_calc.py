
import sys
import os
sys.path.append(os.getcwd())

from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.kernel import Kernel

print("--- PROBE START ---")
try:
    c = BaziCalculator(2024, 2, 10, 12)
    chart = c.get_chart()
    
    # 1. Check Logic
    ys = chart['year']['stem']
    print(f"Chart Year Stem: '{ys}' (Type: {type(ys)})")
    
    # 2. Check Flux Init
    flux = FluxEngine(chart)
    print(f"Particles Built (Init): {len(flux.particles)}")
    
    # Check if Kernel maps it
    print(f"Kernel Maps '甲'? {Kernel.STEM_PROPERTIES.get('甲')}")
    
    # 3. Set Environment (Like Dashboard)
    ln_dict = {'stem': '甲', 'branch': '辰'}
    flux.set_environment(None, ln_dict)
    print(f"Particles Built (Env): {len(flux.particles)}")
    
    if len(flux.particles) > 0:
        p0 = flux.particles[0]
        print(f"P0 Before Compute: {p0.id} Amp={p0.wave.amplitude}")
    
    # 4. Compute
    res = flux.compute_energy_state()
    print("Compute Finished.")
    
    if len(flux.particles) > 0:
        p0 = flux.particles[0]
        print(f"P0 After Compute: {p0.id} Amp={p0.wave.amplitude}")
        
    # 5. Check Spectrum
    if hasattr(flux, '_get_stem_spectrum'):
        spec = flux._get_stem_spectrum()
        print(f"Stem Spectrum: {spec}")
        
    # 6. Check Ten Gods
    if 'ZhengGuan' in res:
        print(f"ZhengGuan: {res['ZhengGuan']}")
    else:
        print("ZhengGuan MISSING")
        if 'ten_gods' in res:
             print(f"Ten Gods Subkey: {res['ten_gods']}")

except Exception as e:
    import traceback
    traceback.print_exc()

print("--- PROBE END ---")
