from __future__ import annotations

from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import (
    branches_and_stems_from_runtime_pillars,
    detect_stem_fusion_cases,
    eval_banhe_hits,
    eval_gonghe_hits,
    eval_liu_chong_hits,
    eval_sanhe_hits,
)


def test_structured_geometry_modules_report_sanhe_banhe_and_gonghe() -> None:
    sanhe_branches = {
        "year": "寅",
        "month": "午",
        "hour": "戌",
    }
    banhe_branches = {
        "year": "酉",
        "month": "丑",
        "day": "寅",
        "hour": "辰",
    }
    gonghe_branches = {
        "year": "申",
        "month": "辰",
        "day": "寅",
        "hour": "午",
    }

    sanhe = eval_sanhe_hits(sanhe_branches)
    banhe = eval_banhe_hits(banhe_branches)
    gonghe = eval_gonghe_hits(gonghe_branches)

    assert any(hit["element"] == "fire" for hit in sanhe)
    assert any(hit["pair_kind"] == "muwang" and hit["element"] == "metal" for hit in banhe)
    assert any(hit["pair_kind"] == "gonghe" and hit["element"] == "water" for hit in gonghe)


def test_pair_geometry_modules_report_clash() -> None:
    branches = {"day": "子", "flow": "午"}
    hits = eval_liu_chong_hits(branches)
    assert len(hits) == 1
    assert set(hits[0]["pair"]) == {"子", "午"}
    assert hits[0]["pillars"] == ["day", "flow"]


def test_stem_fusion_geometry_and_runtime_parsing_work_via_facade() -> None:
    branches, stems = branches_and_stems_from_runtime_pillars(
        {"year": "甲子", "month": "己丑", "day": "丙寅", "hour": "丁卯"},
        luck_pillar="庚辰",
        flow_pillar="辛巳",
    )

    assert branches["luck"] == "辰"
    assert stems["flow"] == "辛"

    cases = detect_stem_fusion_cases(
        stems={"year": "甲", "month": "己"},
        branches={"year": "子", "month": "丑"},
    )
    assert cases
    assert cases[0]["stems"] == ["甲", "己"]
