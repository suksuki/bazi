from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.climate_field_protocol import (
    build_climate_field,
    climate_field_prompt_lines,
    climate_field_protocol_payload,
)


def test_build_climate_field_emits_hot_dry_profile_and_modifier_layer() -> None:
    climate = build_climate_field(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        daymaster="乙",
    )

    assert climate["contract"] == "v17.climate_field.v1"
    assert climate["thermal_index"] > 0.0
    assert climate["dryness"] >= 0.0
    assert climate["climate_tension"] > 0.0
    modifier = climate["climate_modifier_layer"]
    assert modifier["contract"] == "v17.climate_modifier_layer.v1"
    assert "正官" in modifier["ten_god_efficiency"]
    assert "比肩" in modifier["ten_god_stability"]
    assert "食伤财" in modifier["pattern_survival_delta"]


def test_calc_deity_scores_exports_climate_field_into_energy_meta() -> None:
    _scores, _top, _total, meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )

    assert meta["climate_field"]["contract"] == "v17.climate_field.v1"
    assert meta["climate_modifier_layer"]["contract"] == "v17.climate_modifier_layer.v1"
    assert isinstance(meta["climate_field"]["source_by_scope"], dict)


def test_climate_field_prompt_and_protocol_payload_export_canonical_contract() -> None:
    lines = climate_field_prompt_lines()
    payload = climate_field_protocol_payload()

    joined = "\n".join(lines)
    assert "调候先落为底层 climate field" in joined
    assert "thermal_index" in joined
    assert payload["contract"] == "v17.climate_field.protocol.v1"
    assert payload["stem_scope_weights"]["month"] > payload["stem_scope_weights"]["flow"]
    assert payload["branch_scope_weights"]["month"] > payload["branch_scope_weights"]["flow"]
