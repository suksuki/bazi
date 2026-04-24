"""
V17.13：L1 地支/天干几何命中 facade。

Phase 3 将结构关系命中、成对关系命中、天干五合几何拆入独立模块；
本文件保留兼容出口，避免上层调用在重构期抖动。
"""

from __future__ import annotations

from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import (
    ANHE_PAIR_SETS,
    LIUHE_PAIRS,
    LIU_CHONG_PAIRS,
    LIU_HAI_PAIRS,
    LIU_PO_PAIRS,
    SANXING_EDGES,
    eval_anhe_hits,
    eval_branch_pair_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    pillars_branches_set,
    sanxing_detect_geometry,
    summarize_sanxing_branches,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_structured import (
    BANHE_MUWANG_ROWS,
    BANHE_SHENGWANG_ROWS,
    GONGHE_ROWS,
    SANHE_GROUPS,
    SANHE_GROUP_ROWS,
    SANHUI_GROUP_ROWS,
    eval_banhe_hits,
    eval_gonghe_hits,
    eval_sanhe_hits,
    eval_sanhui_hits,
    sanhe_group_complete_for_pair,
)
from v17_rebirth.backend.logic.L1_atomic_ops.stem_fusion_geometry import (
    BRANCH_HIDDEN_STEMS,
    STEM_TO_ELEMENT,
    branches_and_stems_from_four_pillars,
    branches_and_stems_from_runtime_pillars,
    detect_stem_fusion_cases,
    parse_ganzhi_pillar,
)

__all__ = [
    "SANHE_GROUP_ROWS",
    "SANHE_GROUPS",
    "SANHUI_GROUP_ROWS",
    "SANXING_EDGES",
    "LIUHE_PAIRS",
    "ANHE_PAIR_SETS",
    "LIU_CHONG_PAIRS",
    "LIU_HAI_PAIRS",
    "LIU_PO_PAIRS",
    "BANHE_SHENGWANG_ROWS",
    "BANHE_MUWANG_ROWS",
    "GONGHE_ROWS",
    "STEM_TO_ELEMENT",
    "BRANCH_HIDDEN_STEMS",
    "pillars_branches_set",
    "eval_branch_pair_hits",
    "eval_liuhe_hits",
    "eval_anhe_hits",
    "eval_sanhe_hits",
    "eval_sanhui_hits",
    "sanhe_group_complete_for_pair",
    "eval_banhe_hits",
    "eval_gonghe_hits",
    "eval_liu_chong_hits",
    "eval_liu_hai_hits",
    "eval_liu_po_hits",
    "sanxing_detect_geometry",
    "detect_stem_fusion_cases",
    "parse_ganzhi_pillar",
    "branches_and_stems_from_four_pillars",
    "branches_and_stems_from_runtime_pillars",
    "summarize_sanxing_branches",
]
