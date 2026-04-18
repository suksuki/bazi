import sys
import os
from datetime import datetime

# 注入项目根目录
sys.path.append("/Users/liujin/DEV/AIProjects/bazi/qiazhi")

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor

four_pillars = {
    "year": "丁巳",
    "month": "乙巳",
    "day": "乙丑",
    "hour": "乙酉"
}

dt = datetime(1977, 5, 8, 18, 0, 0)
gender = "male"

print(f"--- Full Engine Hydration Debug for {dt} ---")

# 1. L0 Phase
scores, top4, total, meta = calc_deity_scores(
    four_pillars=four_pillars,
    luck_pillar="庚子",
    flow_pillar="丙午",
    gender=gender,
    birth_time=dt
)

# 2. Construct PT (Physics Tensor)
pt = {
    "four_pillars": four_pillars,
    "ten_gods_absolute": scores,
    "energy_meta": meta,
    "gender": gender,
    "birth_time": dt.isoformat()
}

print(f"L0 Scores Pre-Hydration: {pt['ten_gods_absolute']}")

# 3. L1 Hydration (The suspects are here)
try:
    hydrate_v17_physics_tensor(pt)
    print("\n--- After Hydration ---")
    print(f"Ten Gods Absolute: {pt.get('ten_gods_absolute')}")
    
    # Check for NaN in values
    has_nan = any(str(v).lower() == "nan" for v in pt['ten_gods_absolute'].values())
    if has_nan:
        print("!!! ALERT: NaN DETECTED IN HYDRATED TENSOR !!!")
    else:
        print("Success: No NaN found in hydrated tensor.")

except Exception as e:
    print(f"CRASH during hydration: {e}")
    import traceback
    traceback.print_exc()
