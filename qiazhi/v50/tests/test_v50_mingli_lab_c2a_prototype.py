from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "archive/proofs/prototypes/mingli-lab-c2a"
FIXTURE = PROTOTYPE / "fixture.json"


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_c2a_fixture_is_anonymized_and_keeps_formal_authority_separate() -> None:
    payload = _fixture()
    serialized = json.dumps(payload, ensure_ascii=False)
    source = payload["source"]
    formal = payload["formal"]
    assert isinstance(source, dict)
    assert isinstance(formal, dict)

    assert source["source_mode"] == "real_formal_life_case_anonymized"
    assert source["contains_personal_identity"] is False
    assert str(source["chart_version_id"]).startswith("chart:c2a:")
    assert formal["path"]["authority"] == "committed_life_case"
    assert formal["path"]["epistemic_status"] == "committed"
    assert all(
        str(value).split(":", 1)[0] in {"chart", "path", "relation", "source", "commitment"}
        for value in _all_public_refs(payload)
    )

    for forbidden_key in (
        '"case_id"', '"user_id"', '"profile_id"', '"display_name"',
        '"email"', '"birth_date"', '"birth_time"', '"birth_location"',
    ):
        assert forbidden_key not in serialized


def test_c2a_has_twelve_calendar_compatible_hours_and_three_path_outcomes() -> None:
    payload = _fixture()
    variants = payload["variants"]
    baseline_index = payload["baseline_variant_index"]
    assert isinstance(variants, list)
    assert len(variants) == 12
    assert 0 <= baseline_index < len(variants)

    baseline = variants[baseline_index]
    baseline_locked = baseline["pillars"][:3]
    assert baseline["source_mode"] == "canonical"
    assert all(item["calendar_compatible_with_locked_ymd"] for item in variants)
    assert all(item["pillars"][:3] == baseline_locked for item in variants)

    outcomes = {
        item["formal_path_reference"]["continuity_status"]
        for item in variants
    }
    assert outcomes == {"preserved", "partial", "broken"}
    assert all(item["graph_candidate"]["epistemic_status"] == "candidate" for item in variants)
    assert all(item["formal_path_reference"]["authority"] == "deterministic_structural_comparison" for item in variants)


def test_c2a_year_dial_never_fabricates_formal_temporal_effects() -> None:
    payload = _fixture()
    years = payload["year_dial"]
    assert len(years) == 5
    assert sum(item["source_mode"] == "official" for item in years) == 1
    assert all(item["formal_temporal_effect_available"] is False for item in years)
    assert "不修改正式命盘或 LifeCase" in " ".join(payload["boundaries"])


def test_c2a_frontend_keeps_llm_and_formal_writes_out_of_the_prototype() -> None:
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    contract = (
        ROOT / "docs/archive/proofs/V50_C2A_MINGLI_LAB_DIRECT_MANIPULATION_PROTOTYPE.md"
    ).read_text(encoding="utf-8")

    assert "fetch(\"./fixture.json\"" in script
    assert "/api/" not in script
    assert "WebSocket" not in script
    assert "EventSource" not in script
    assert "no LLM" in contract
    assert "no write to ChartVersion, LifeCase or case memory" in contract


def _all_public_refs(payload: dict[str, object]) -> list[str]:
    refs: list[str] = [str(payload["source"]["chart_version_id"])]
    formal_path = payload["formal"]["path"]
    refs.extend(str(item) for item in formal_path["source_refs"])
    refs.extend(str(item) for item in formal_path["commitment_refs"])
    refs.append(str(formal_path["path_ref"]))
    refs.extend(str(item["relation_ref"]) for item in formal_path["segments"])
    for variant in payload["variants"]:
        refs.append(str(variant["graph_candidate"]["path_ref"]))
        refs.extend(str(item) for item in variant["graph_candidate"]["source_refs"])
        for node in variant["nodes"]:
            refs.extend(str(item) for item in node["source_refs"])
        for relation in variant["relations"]:
            refs.append(str(relation["relation_id"]))
            refs.extend(str(item) for item in relation["source_refs"])
    return refs
