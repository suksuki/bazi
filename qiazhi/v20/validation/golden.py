from __future__ import annotations

from v20.validation.synthetic_schema import SyntheticCase

GOLDEN_CASES = (
    SyntheticCase(
        case_id="v20.golden.branch_relation_wealth_material",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        expected_feature_domains=("strength", "branch", "wealth", "useful_god"),
        expected_question_keys=("q_strength_assessment", "q_branch_relation_detail"),
        expected_rule_candidate_domains=("strength",),
    ),
)
