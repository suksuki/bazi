from v20.core.measure import build_time_context
from pprint import pprint

res = build_time_context(
    luck_pillar_str="",
    flow_year_pillar_str="丙午",
    flow_month_pillar_str="",
    natal_chart={"pillars": {"year": {"stem": "甲", "branch": "辰"}}}
)
pprint(res.model_dump())
