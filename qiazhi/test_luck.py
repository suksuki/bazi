from v20.api.runtime import run_runtime_from_pillars
from v20.server import project_runtime_for_role
from pprint import pprint

res = run_runtime_from_pillars(
    "甲辰", "戊辰", "乙亥", "丙子",
    flow_year_pillar="丙午",
    luck_pillar="戊午",
    locale="zh",
    llm_mode="deterministic"
)
proj = project_runtime_for_role(res, "user")
pprint(proj.get("time_context"))
