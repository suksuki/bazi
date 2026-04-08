from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FourPillars, StemBranchPair
from app.skills.physics_calculations import (
    build_energy_fields,
    calculate_deity_scores,
    resolve_seasonal_factor,
    root_coupling_check,
)


def _metadata() -> BaziMetadata:
    return BaziMetadata(
        pillars=FourPillars(
            year=StemBranchPair(stem="庚", branch="午", energy_value=100),
            month=StemBranchPair(stem="壬", branch="子", energy_value=100),
            day=StemBranchPair(stem="甲", branch="子", energy_value=100),
            hour=StemBranchPair(stem="乙", branch="酉", energy_value=100),
        ),
        conflict_matrix=ConflictMatrix(points=[]),
    )


def test_root_coupling_check_marks_rootless_wood_day_master():
    metadata = _metadata()
    result, decay = root_coupling_check(metadata, floating_decay=0.2)
    assert result["no_root"] is True
    assert decay == 0.8


def test_resolve_seasonal_factor_derives_from_month_branch_when_no_solar_term():
    seasonal = resolve_seasonal_factor(
        cache_seasonal_matrix={},
        metadata=_metadata(),
        solar_term=None,
    )
    assert seasonal["water"] > 1.0


def test_build_energy_fields_and_deity_scores_return_traceable_payloads():
    metadata = _metadata()
    root_check, root_decay_factor = root_coupling_check(metadata, floating_decay=0.2)
    by_pillar, vector, raw_deity_energy, contribution_sources = build_energy_fields(
        metadata=metadata,
        position_weights={"year": 0.2, "month": 0.45, "day": 0.25, "hour": 0.1},
        seasonal_factor={"wood": 1.0, "fire": 1.0, "earth": 1.0, "metal": 1.0, "water": 1.0},
        day_stem="甲",
        stem_boost=1.05,
        root_decay=0.7,
        conflict_factor=1.0,
        protrusion=1.0,
        floating_deities={"比肩", "劫财"},
        root_decay_factor=root_decay_factor,
        dayun="庚申",
        liunian="丙午",
    )
    scores, components, axes, trace = calculate_deity_scores(
        raw_deity_energy=raw_deity_energy,
        interaction_params={
            "EFF_PROMOTING": 1.2,
            "EFF_PROMOTING_SAME": 1.2,
            "EFF_PROMOTING_DIFF": 1.2,
            "EFF_EXHAUSTING": 0.8,
            "EFF_EXHAUSTING_SAME": 0.8,
            "EFF_EXHAUSTING_DIFF": 0.8,
            "EFF_RESTRAINING": 0.6,
            "EFF_RESTRAINING_SAME": 0.6,
            "EFF_RESTRAINING_DIFF": 0.6,
            "EFF_CONSUMING": 0.9,
            "EFF_CONSUMING_SAME": 0.9,
            "EFF_CONSUMING_DIFF": 0.9,
            "CF_FLOATING_DECAY": 0.2,
            "A_PROTRUSION": 1.0,
        },
        contribution_sources=contribution_sources,
        root_check=root_check,
    )
    assert by_pillar["year"]["element"] == "metal"
    assert sum(vector.values()) > 0
    assert round(sum(scores.values()), 2) == 100.0
    assert "比肩" in components
    assert "比肩" in axes
    assert "比肩" in trace
