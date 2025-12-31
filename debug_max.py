
import sys
from pathlib import Path
project_root = Path("/home/jin/bazi_predict")
sys.path.insert(0, str(project_root))
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.intelligence.logic_arbitrator import LogicArbitrator

engine = SyntheticBaziEngine()
bazi_gen = engine.generate_all_bazi()

max_blade = 0
max_killings = 0

for i, chart in enumerate(bazi_gen):
    if i > 5000: break # Small sample
    day_master = chart[2][0]
    intensities = LogicArbitrator.calculate_field_intensities(chart, day_master)
    blade = intensities["比肩"] + intensities["劫财"] + intensities["正印"] + intensities["偏印"]
    killings = intensities["七杀"] + intensities["正官"]
    if blade > max_blade: max_blade = blade
    if killings > max_killings: max_killings = killings

print(f"Max Blade: {max_blade}")
print(f"Max Killings: {max_killings}")
