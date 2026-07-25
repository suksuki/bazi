from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from product.app import create_product_app
from product.onecanvas_structural import (
    OneCanvasStructuralError,
    compile_target_draft,
    compile_structural_variant,
    resolve_pillar_target,
    selection_catalog_payload,
)
from product.product_store import MemoryProductStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "apps/product/static/experience/active/onecanvas-r1/fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_selection_catalog_has_two_independent_and_two_dependent_axes() -> None:
    catalog = selection_catalog_payload()

    assert len(catalog["year"]) == 60
    assert len(catalog["day"]) == 60
    assert len(catalog["stems"]) == 10
    assert len(catalog["branches"]) == 12
    assert {len(items) for items in catalog["branches_by_stem"].values()} == {6}
    assert {len(items) for items in catalog["stems_by_branch"].values()} == {5}
    assert {len(items) for items in catalog["month_by_year"].values()} == {12}
    assert {len(items) for items in catalog["hour_by_day"].values()} == {12}
    assert catalog["month_by_year"]["甲子"] == [
        "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未",
        "壬申", "癸酉", "甲戌", "乙亥", "丙子", "丁丑",
    ]
    assert catalog["hour_by_day"]["甲子"] == [
        "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳",
        "庚午", "辛未", "壬申", "癸酉", "甲戌", "乙亥",
    ]
    assert catalog["gender_options"] == [
        {"value": "male", "label": "乾造"},
        {"value": "female", "label": "坤造"},
    ]
    assert catalog["birth_year_range"] == [1900, 2100]
    assert catalog["cycle_year_anchor_by_year_pillar"]["丁巳"][:2] == [1917, 1977]
    assert 1977 in catalog["birth_year_by_year_pillar"]["丁巳"]
    assert 1977 in catalog["birth_year_by_year_pillar"]["丙辰"]
    assert catalog["annual_observations"][126] == {"year": 2026, "pillar": "丙午"}


def test_structural_compile_rejects_illegal_month_or_hour_combination() -> None:
    fixture = _fixture()
    kwargs = {
        "baseline_pillars": fixture["formal"]["pillars"],
        "baseline_relations": fixture["formal"]["relations"],
        "formal_path": fixture["formal"]["path"],
        "baseline_timing": fixture["formal"]["timing_recalculation"],
        "analysis_year": fixture["formal"]["analysis_year"],
        "gender": "male",
    }

    try:
        compile_structural_variant(selected_pillars=["甲子", "甲寅", "甲子", "甲子"], **kwargs)
    except OneCanvasStructuralError as exc:
        assert str(exc) == "onecanvas_month_pillar_not_legal_for_year"
    else:
        raise AssertionError("illegal month pillar was accepted")


def test_structural_compile_derives_sequence_but_not_fake_start_years() -> None:
    fixture = _fixture()
    variant = compile_structural_variant(
        selected_pillars=["甲子", "丙寅", "乙丑", "己卯"],
        baseline_pillars=fixture["formal"]["pillars"],
        baseline_relations=fixture["formal"]["relations"],
        formal_path=fixture["formal"]["path"],
        baseline_timing=fixture["formal"]["timing_recalculation"],
        analysis_year=fixture["formal"]["analysis_year"],
        gender="male",
    )

    timing = variant["timing_recalculation"]
    assert variant["pillars"] == ["甲子", "丙寅", "乙丑", "己卯"]
    assert timing["calculation_mode"] == "structural_sequence_only"
    assert timing["exact_timing_status"] == "unavailable"
    assert timing["direction"] == "forward"
    assert timing["luck_sequence"][0]["pillar"] == "丁卯"
    assert timing["luck_year_range"] == []
    assert timing["current_luck_status"] == "unresolved"
    assert timing["luck_pillar"] == ""
    assert all(item["start_year"] is None for item in timing["luck_sequence"])
    assert len(variant["relations"]) > 0


def test_structural_compile_keeps_unknown_gender_unresolved_and_reverses_sequence_for_kun_chart() -> None:
    fixture = _fixture()
    kwargs = {
        "selected_pillars": ["甲子", "丙寅", "乙丑", "己卯"],
        "baseline_pillars": fixture["formal"]["pillars"],
        "baseline_relations": fixture["formal"]["relations"],
        "formal_path": fixture["formal"]["path"],
        "baseline_timing": fixture["formal"]["timing_recalculation"],
        "analysis_year": fixture["formal"]["analysis_year"],
    }

    unknown = compile_structural_variant(gender="unknown", **kwargs)
    unknown_timing = unknown["timing_recalculation"]
    assert unknown_timing["direction"] == "unresolved"
    assert unknown_timing["luck_sequence"] == []
    assert unknown_timing["luck_pillar"] == ""

    female = compile_structural_variant(gender="female", **kwargs)
    timing = female["timing_recalculation"]
    assert timing["chart_type"] == "坤造"
    assert timing["direction"] == "reverse"
    assert timing["luck_sequence"][0]["pillar"] == "乙丑"


def test_ding_si_qian_chart_derives_reverse_sequence_but_does_not_call_jia_chen_current_luck() -> None:
    fixture = _fixture()
    variant = compile_structural_variant(
        selected_pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        baseline_pillars=fixture["formal"]["pillars"],
        baseline_relations=fixture["formal"]["relations"],
        formal_path=fixture["formal"]["path"],
        baseline_timing=fixture["formal"]["timing_recalculation"],
        analysis_year=2026,
        gender="male",
    )

    timing = variant["timing_recalculation"]
    assert timing["direction"] == "reverse"
    assert [item["pillar"] for item in timing["luck_sequence"][:5]] == [
        "甲辰", "癸卯", "壬寅", "辛丑", "庚子",
    ]
    assert timing["current_luck_status"] == "unresolved"
    assert timing["luck_pillar"] == ""
    assert timing["luck_year_range"] == []


def test_ding_si_qian_chart_uses_1977_anchor_to_resolve_geng_zi_in_2026() -> None:
    fixture = _fixture()
    variant = compile_structural_variant(
        selected_pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        baseline_pillars=fixture["formal"]["pillars"],
        baseline_relations=fixture["formal"]["relations"],
        formal_path=fixture["formal"]["path"],
        baseline_timing=fixture["formal"]["timing_recalculation"],
        analysis_year=2026,
        gender="male",
        birth_year_hint=1977,
    )

    timing = variant["timing_recalculation"]
    assert timing["current_luck_status"] == "resolved_from_birth_year"
    assert timing["luck_pillar"] == "庚子"
    assert timing["luck_year_range"] == [2018, 2027]
    assert timing["calculation_mode"] == "birth_year_anchored_reverse_lookup"
    assert timing["calendar_resolution"]["status"] == "resolved"
    assert variant["selection_context"]["birth_year_hint"] == 1977
    assert variant["selection_context"]["maps_to_real_birth_datetime"] is True


def test_authenticated_compile_endpoint_is_read_only_and_uses_server_compiler() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "OneCanvas",
            "email": "onecanvas-v2@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    fixture = _fixture()
    response = client.post(
        "/api/v50/experience/onecanvas/structural-compile",
        json={
            "selected_pillars": ["甲子", "丙寅", "乙丑", "己卯"],
            "baseline_pillars": fixture["formal"]["pillars"],
            "baseline_relations": fixture["formal"]["relations"],
            "formal_path": fixture["formal"]["path"],
            "baseline_timing": fixture["formal"]["timing_recalculation"],
            "analysis_year": fixture["formal"]["analysis_year"],
            "gender": "male",
            "birth_year_hint": 1977,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["variant"]["pillars"] == ["甲子", "丙寅", "乙丑", "己卯"]
    assert body["llm_used"] is False
    assert body["formal_state_writes"] is False
    assert body["life_case_writes"] is False
    assert body["variant"]["selection_context"]["birth_year_hint"] == 1977


def test_compile_endpoint_accepts_unknown_gender_without_calculating_luck() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "OneCanvas Gender",
            "email": "onecanvas-gender@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    fixture = _fixture()
    response = client.post(
        "/api/v50/experience/onecanvas/structural-compile",
        json={
            "selected_pillars": ["甲子", "丙寅", "乙丑", "己卯"],
            "baseline_pillars": fixture["formal"]["pillars"],
            "baseline_relations": fixture["formal"]["relations"],
            "formal_path": fixture["formal"]["path"],
            "baseline_timing": fixture["formal"]["timing_recalculation"],
            "analysis_year": fixture["formal"]["analysis_year"],
            "gender": "unknown",
        },
    )

    assert response.status_code == 200
    timing = response.json()["variant"]["timing_recalculation"]
    assert timing["direction"] == "unresolved"
    assert timing["luck_sequence"] == []


def test_target_solver_normalizes_dependent_stems_and_invalidates_stale_anchor() -> None:
    resolution = resolve_pillar_target(
        desired={
            "year": "乙丑",
            "month": "丙寅",
            "day": "丙子",
            "hour": "壬午",
        },
        baseline_pillars=["甲子", "丙寅", "乙丑", "己卯"],
        cycle_year_anchor=1977,
        target_draft_id="target-order-proof",
    )

    assert resolution["status"] == "single_solution"
    assert resolution["selected_pillars"] == ["乙丑", "戊寅", "丙子", "甲午"]
    assert resolution["normalized_slots"] == ["month", "hour"]
    assert resolution["cycle_year_anchor"] is None
    assert resolution["invalidated_anchor_reasons"][0]["field"] == "sexagenary_year_anchor"


def test_target_solver_reaches_same_chart_regardless_of_parent_edit_order() -> None:
    baseline = ["庚寅", "丁亥", "庚戌", "壬午"]
    month_first = resolve_pillar_target(
        desired={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        baseline_pillars=baseline,
    )
    year_first = resolve_pillar_target(
        desired={"year": "丁巳", "month": "辛巳", "day": "乙丑", "hour": "乙酉"},
        baseline_pillars=baseline,
    )

    assert month_first["selected_pillars"] == year_first["selected_pillars"]
    assert month_first["selected_pillars"] == ["丁巳", "乙巳", "乙丑", "乙酉"]


def test_target_compile_endpoint_is_wysiwyg_and_read_only() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "OneCanvas Target",
            "email": "onecanvas-target@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    fixture = _fixture()
    response = client.post(
        "/api/v50/experience/onecanvas/target-compile",
        json={
            "target_draft_id": "target-api-v1",
            "desired": {
                "year": "丁巳",
                "month": "乙巳",
                "day": "乙丑",
                "hour": "乙酉",
            },
            "baseline_pillars": fixture["formal"]["pillars"],
            "baseline_relations": fixture["formal"]["relations"],
            "formal_path": fixture["formal"]["path"],
            "baseline_timing": fixture["formal"]["timing_recalculation"],
            "analysis_year": 2026,
            "gender": "male",
            "cycle_year_anchor": 1977,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["resolution"]["selected_pillars"] == ["丁巳", "乙巳", "乙丑", "乙酉"]
    assert body["variant"]["timing_recalculation"]["luck_pillar"] == "庚子"
    assert body["llm_used"] is False
    assert body["formal_state_writes"] is False
    assert body["life_case_writes"] is False


def test_target_compile_endpoint_exposes_multiple_solutions_until_explicit_choice() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "OneCanvas Multiple",
            "email": "onecanvas-multiple@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    fixture = _fixture()
    payload = {
        "target_draft_id": "target-api-many-v1",
        "target_draft": {
            "year": {"pillar": "丁巳"},
            "month": {"branch": "巳"},
            "day": {"stem": "乙"},
            "hour": {"branch": "酉"},
        },
        "baseline_pillars": fixture["formal"]["pillars"],
        "baseline_relations": fixture["formal"]["relations"],
        "formal_path": fixture["formal"]["path"],
        "baseline_timing": fixture["formal"]["timing_recalculation"],
        "analysis_year": 2026,
        "gender": "male",
    }

    unresolved = client.post(
        "/api/v50/experience/onecanvas/target-compile",
        json=payload,
    )
    assert unresolved.status_code == 200, unresolved.text
    body = unresolved.json()
    resolution = body["resolution"]
    assert resolution["status"] == "multiple_solutions"
    assert resolution["candidate_count"] == 6
    assert resolution["selection_required"] is True
    assert resolution["selected_pillars"] == []
    assert body["variant"] is None

    selected_ref = resolution["legal_variants"][2]["variant_ref"]
    selected = client.post(
        "/api/v50/experience/onecanvas/target-compile",
        json={**payload, "selected_variant_id": selected_ref},
    )
    assert selected.status_code == 200, selected.text
    selected_body = selected.json()
    assert selected_body["resolution"]["status"] == "multiple_solutions"
    assert selected_body["resolution"]["selection_required"] is False
    assert selected_body["resolution"]["user_selected_variant_ref"] == selected_ref
    assert selected_body["variant"]["pillars"] == selected_body["resolution"]["selected_pillars"]
    assert selected_body["formal_state_writes"] is False
    assert selected_body["life_case_writes"] is False


def test_target_compile_endpoint_exposes_no_solution_and_releasable_constraints() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "OneCanvas Conflict",
            "email": "onecanvas-conflict@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    fixture = _fixture()
    response = client.post(
        "/api/v50/experience/onecanvas/target-compile",
        json={
            "target_draft_id": "target-api-none-v1",
            "target_draft": {
                "year": {"pillar": "丁巳"},
                "month": {"pillar": "丙寅"},
                "day": {"pillar": "乙丑"},
                "hour": {"branch": "酉"},
            },
            "baseline_pillars": fixture["formal"]["pillars"],
            "baseline_relations": fixture["formal"]["relations"],
            "formal_path": fixture["formal"]["path"],
            "baseline_timing": fixture["formal"]["timing_recalculation"],
            "analysis_year": 2026,
            "gender": "male",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    resolution = body["resolution"]
    assert resolution["status"] == "no_solution"
    assert resolution["candidate_count"] == 0
    assert resolution["conflict_reasons"][0]["reason"] == "month_pillar_not_legal_for_year"
    assert resolution["releasable_constraints"] == ["month.pillar", "year.pillar"]
    assert resolution["selected_pillars"] == []
    assert body["variant"] is None
    assert body["formal_state_writes"] is False
    assert body["life_case_writes"] is False
