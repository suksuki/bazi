from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Literal


@dataclass(frozen=True)
class ThreeLifeQualificationSpec:
    package_ref: str
    binding_fact_key: str
    binding_domain_key: str
    domain: Literal["career", "wealth", "relationship"]
    display_order: int
    actor_ref: str
    profile_ref: str
    case_ref: str
    tree_ref: str
    display_name: str
    public_alias: str
    premise: str
    gender: Literal["male", "female"]
    birth_date: date
    birth_time: time
    birth_location: str
    location: str
    activity: str


THREE_LIFE_QUALIFICATION_SPECS = (
    ThreeLifeQualificationSpec(
        package_ref="v60.episode-package.wenxi-archive-trial.v1",
        binding_fact_key="career_structure_fact_ref",
        binding_domain_key="career_life_domain_vector_ref",
        domain="career",
        display_order=1,
        actor_ref="v60-actor-wenxi-v1",
        profile_ref="v60-synthetic-profile-wenxi-v1",
        case_ref="v60-synthetic-case-wenxi-v1",
        tree_ref="v60-life-tree-wenxi-v1",
        display_name="闻溪",
        public_alias="馆页树",
        premise="一批修复样页刚被送进镇史馆，后续职责与署名仍未决定。",
        gender="female",
        birth_date=date(1988, 4, 23),
        birth_time=time(7, 40),
        birth_location="合成世界·石桥镇",
        location="stone-bridge-archive",
        activity="waiting-for-restoration-review",
    ),
    ThreeLifeQualificationSpec(
        package_ref="v60.episode-package.heyang-dyed-cloth.v1",
        binding_fact_key="wealth_structure_fact_ref",
        binding_domain_key="wealth_life_domain_vector_ref",
        domain="wealth",
        display_order=2,
        actor_ref="v60-actor-heyang-v1",
        profile_ref="v60-synthetic-profile-heyang-v1",
        case_ref="v60-synthetic-case-heyang-v1",
        tree_ref="v60-life-tree-heyang-v1",
        display_name="禾央",
        public_alias="染布树",
        premise="三匹新染布正在河岸铺试卖，订单与回款方式尚未稳定。",
        gender="male",
        birth_date=date(1994, 11, 5),
        birth_time=time(15, 10),
        birth_location="合成世界·河岸铺",
        location="riverside-cloth-shop",
        activity="observing-trial-sale",
    ),
    ThreeLifeQualificationSpec(
        package_ref="v60.episode-package.zhaoning-lantern-roster.v1",
        binding_fact_key="relationship_structure_fact_ref",
        binding_domain_key="relationship_life_domain_vector_ref",
        domain="relationship",
        display_order=3,
        actor_ref="v60-actor-zhaoning-v1",
        profile_ref="v60-synthetic-profile-zhaoning-v1",
        case_ref="v60-synthetic-case-zhaoning-v1",
        tree_ref="v60-life-tree-zhaoning-v1",
        display_name="照宁",
        public_alias="灯册树",
        premise="一份山灯轮值册刚开始共享，协作节奏与边界仍在形成。",
        gender="female",
        birth_date=date(1990, 2, 17),
        birth_time=time(21, 30),
        birth_location="合成世界·山灯驿",
        location="mountain-lantern-station",
        activity="coordinating-lantern-roster",
    ),
)
