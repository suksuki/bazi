import sys
import os
from datetime import datetime

# 注入项目根目录
sys.path.append("/Users/liujin/DEV/AIProjects/bazi/qiazhi")

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores

four_pillars = {
    "year": "丁巳",
    "month": "乙巳",
    "day": "乙丑",
    "hour": "乙酉"
}

dt = datetime(1977, 5, 8, 18, 0, 0)
gender = "male"
flow_year = 2026

print(f"--- Simulating Physics for {dt} ---")
try:
    scores, top4, total, meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar="庚子",
        flow_pillar="丙午",
        gender=gender,
        birth_time=dt
    )
    print(f"Scores: {scores}")
    print(f"Total Energy: {total}")
    print(f"Meta: {meta}")
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
