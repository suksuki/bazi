from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = (
    ROOT
    / "apps"
    / "product"
    / "static"
    / "experience"
    / "active"
    / "onecanvas-r1"
)
FIXTURE_PATH = PROTOTYPE / "fixture.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_c2ar_fixture_is_anonymized_and_has_no_raw_birth_datetime() -> None:
    payload = _fixture()
    source = payload["source"]
    assert source["source_mode"] == "real_formal_life_case_anonymized"
    assert source["contains_personal_identity"] is False
    assert source["contains_raw_birth_datetime"] is False
    serialized = FIXTURE_PATH.read_text(encoding="utf-8")
    for forbidden in ("mingli-case-", "v50-user-"):
        assert forbidden not in serialized
    forbidden_keys = {"birth_date", "birth_time", "email", "display_name"}
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            assert not (set(item) & forbidden_keys)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def test_c2ar_unknown_gender_never_invents_luck_nodes() -> None:
    payload = _fixture()
    variants = [payload["formal"]]
    variants.extend(
        candidate
        for family in payload["candidate_families"].values()
        for candidate in family
    )
    expected = {
        f"node:{slot}_{kind}"
        for slot in ("year", "month", "day", "hour", "annual")
        for kind in ("stem", "branch")
    }
    for variant in variants:
        refs = {node["semantic_ref"] for node in variant["nodes"]}
        assert len(variant["nodes"]) == 10
        assert refs == expected
        assert variant["timing_recalculation"]["status"] == "recalculation_unavailable"
        assert variant["timing_recalculation"]["luck_sequence"] == []


def test_c2ar_candidate_families_are_precompiled_and_have_explicit_timing_status() -> None:
    payload = _fixture()
    assert {axis: len(items) for axis, items in payload["candidate_families"].items()} == {
        "year": 60,
        "day": 60,
    }
    allowed = {"recalculated_changed", "recalculated_unchanged", "recalculation_unavailable"}
    for family in payload["candidate_families"].values():
        for candidate in family:
            assert candidate["timing_recalculation"]["status"] in allowed
            assert candidate["structural_candidate_ref"].startswith("cycle-candidate:c2a:")

    assert len({candidate["pillars"][0] for candidate in payload["candidate_families"]["year"]}) == 60
    assert len({candidate["pillars"][2] for candidate in payload["candidate_families"]["day"]}) == 60


def test_c2ar_year_edit_precompiles_linked_month_and_preserves_day_hour() -> None:
    payload = _fixture()
    formal = payload["formal"]["pillars"]
    candidates = payload["candidate_families"]["year"]

    assert all(candidate["pillars"][1][1] == formal[1][1] for candidate in candidates)
    assert all(candidate["pillars"][2:] == formal[2:] for candidate in candidates)
    assert any(candidate["pillars"][1] != formal[1] for candidate in candidates)


def test_c2ar_day_edit_precompiles_linked_hour_change() -> None:
    payload = _fixture()
    formal = payload["formal"]["pillars"]
    linked_candidates = [
        candidate
        for candidate in payload["candidate_families"]["day"]
        if candidate["pillars"][2] != formal[2] and candidate["pillars"][3] != formal[3]
    ]
    assert linked_candidates
    for candidate in linked_candidates:
        changed_slots = {item["slot"] for item in candidate["diff"]["changed_pillars"]}
        assert {"day", "hour"}.issubset(changed_slots)
        assert candidate["pillars"][:2] == formal[:2]
        assert candidate["pillars"][3][1] == formal[3][1]


def test_c2ar_paths_only_reference_existing_primary_nodes() -> None:
    payload = _fixture()
    formal_keys = {node["node_key"] for node in payload["formal"]["nodes"]}
    assert {item["anchor"] for item in payload["formal"]["path"]["ordered_nodes"]} <= formal_keys
    for family in payload["candidate_families"].values():
        for candidate in family:
            candidate_path = candidate.get("graph_candidate")
            if candidate_path is None:
                continue
            node_keys = {node["node_key"] for node in candidate["nodes"]}
            assert set(candidate_path["node_keys"]) <= node_keys
            assert candidate_path["epistemic_status"] == "candidate"


def test_c2ar_renderer_is_one_canvas_without_permanent_console_panels() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    javascript = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    components = (PROTOTYPE / "onecanvas-components.js").read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")
    combined = "\n".join((html, javascript, components, stylesheet))
    assert 'class="canvas-field"' in components
    assert 'class="pillar-grid"' in javascript
    assert 'class="context-lens' in components
    assert "Path Studio" not in combined
    assert "permanent-inspector" not in combined
    assert "year-dial" not in combined


def test_c2ar_frontend_consumes_precompiled_semantics() -> None:
    runtime = (PROTOTYPE / "onecanvas-runtime.js").read_text(encoding="utf-8")
    prototype = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    components = (PROTOTYPE / "onecanvas-components.js").read_text(encoding="utf-8")
    frontend = prototype + components
    assert "fixture.candidate_families" in runtime
    assert "variantFor(snapshot).relations" in runtime
    assert "recomputeViewModel" in frontend
    for forbidden in ("resolve_ten_god", "STEM_ELEMENTS", "BRANCH_ELEMENTS", "calculateLuck", "inferRelation"):
        assert forbidden not in runtime
        assert forbidden not in frontend


def test_c2ar_contract_keeps_production_and_llm_boundaries_closed() -> None:
    payload = _fixture()
    boundaries = "\n".join(payload["boundaries"])
    assert "不修改正式命盘或 LifeCase" in boundaries
    assert "不自动升级为正式主路径" in boundaries
    assert "不调用 LLM、TTS" in boundaries
    contract = (
        ROOT / "docs" / "archive" / "proofs" / "V50_C2AR_MINGLI_ONECANVAS_PROTOTYPE.md"
    ).read_text(encoding="utf-8")
    assert "production_deployment: false" in contract
    assert "Do not deploy the prototype to server 13" in contract
