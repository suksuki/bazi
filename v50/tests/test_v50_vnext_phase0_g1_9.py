from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.life_domains import DOMAIN_REGISTRY, LifeDomain, domain_access_allowed
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.fact_review import audit_professional_facts
from product.reading_projection import project_living_reading
from scripts.v50_audit_runtime_authority import audit_runtime_authority
from scripts.v50_prepare_vnext_phase0_g1_9 import prepare_g1_9
from scripts.v50_run_vnext_phase0_benchmark import DEVELOPMENT_FIXTURE_PACK_PATH


def _development_world():
    pack = json.loads(DEVELOPMENT_FIXTURE_PACK_PATH.read_text(encoding="utf-8"))
    birth = dict(pack["cases"][0]["birth_input"])
    birth["birth_time"] = "12:00"
    return compile_chart_world(
        reading_id="g1-9-unit",
        birth_input=BirthInputCanonical.model_validate(birth),
        include_research_fixture_prior=False,
    )


def test_professional_fact_integrity_catches_hard_errors_without_modality_false_positives() -> None:
    world = _development_world()

    assert audit_professional_facts(text="金克火", world=world)[0].severity == "hard"
    assert audit_professional_facts(text="火克金", world=world) == []
    assert audit_professional_facts(text="若流年子来，则可能形成子午冲", world=world) == []
    assert audit_professional_facts(text="是否可能出现午辰冲？", world=world) == []
    assert audit_professional_facts(text="假设存在某关系", world=world) == []
    assert audit_professional_facts(text="甲为阴木", world=world)[0].issue_type == "stem_polarity_or_element_conflict"
    assert audit_professional_facts(text="子藏甲", world=world)[0].issue_type == "hidden_stem_conflict"


def test_professional_fact_integrity_is_annotation_only() -> None:
    world = _development_world()
    raw = {"first_look": "金克火", "selected_hypothesis_id": "H1"}
    before = sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    issues = audit_professional_facts(text=raw["first_look"], world=world, claim_ref="raw:first_look")

    after = sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert issues[0].disposition == "suppress_from_projection"
    assert before == after


def test_first_look_is_production_only_and_challenge_tools_are_tagged() -> None:
    world = _development_world()
    compiler = MingliContextCompiler()

    pattern = compiler.compile(world=world, stage="pattern")
    assert pattern.reasoning_phase == "independent_observation"
    assert pattern.experimental_tool_refs == []
    assert {item["authority_status"] for item in pattern.payload["facts"]} <= {"production"}

    baseline = compiler.compile(world=world, stage="baseline")
    baseline_pool_refs = [
        *[item["fact_ref"] for item in baseline.payload["allowed_relation_pool"]],
        *[item["path_ref"] for item in baseline.payload["allowed_path_candidates"]],
    ]
    assert baseline.reasoning_phase == "tool_challenge"
    assert baseline.experimental_tool_refs == list(dict.fromkeys(baseline_pool_refs))
    assert {item["authority_status"] for item in baseline.payload["facts"]} <= {"production"}

    challenge = compiler.compile(world=world, stage="work_path")
    experimental = [item for item in challenge.payload["facts"] if item["authority_status"] == "experimental"]
    assert challenge.experimental_tool_refs
    assert experimental
    assert all(item["authority"] == "experimental_tool_observation" for item in experimental)


def test_guest_member_capabilities_and_projection_are_server_bounded() -> None:
    public = {item.domain for item in DOMAIN_REGISTRY if item.publicly_available}
    assert public == {
        LifeDomain.WHOLE_CHART,
        LifeDomain.CAREER,
        LifeDomain.WEALTH,
    }
    assert domain_access_allowed(LifeDomain.LIFE_TIMING, role_mode="member") is False
    assert domain_access_allowed(LifeDomain.LIFE_TIMING, role_mode="practitioner") is True
    assert domain_access_allowed(LifeDomain.RELATIONSHIP, role_mode="member") is False
    assert domain_access_allowed(LifeDomain.RELATIONSHIP, role_mode="practitioner") is True

    source = {
        "portrait": [],
        "prior_predictions": [],
        "dual_lens": None,
        "ziwei_profile": {},
        "workspace": {},
        "latest_revision": None,
        "domain_explorations": {
            "career": {
                "reading": {"claim": "保留", "mechanism_ast": ["不得公开"]},
                "review": {"issues": ["不得公开"]},
            }
        },
        "mechanism_ast": ["不得公开"],
        "theory_refs": ["不得公开"],
    }
    projected = project_living_reading(source, mode="member")
    serialized = json.dumps(projected, ensure_ascii=False)
    assert "保留" in serialized
    assert "mechanism_ast" not in serialized
    assert "theory_refs" not in serialized
    assert '"review"' not in serialized


def test_production_authority_manifest_is_valid_and_public_projection_has_no_research_base_fields() -> None:
    audit = audit_runtime_authority()

    assert audit["status"] == "passed"
    assert audit["observed_data"]["invalid_authority_statuses"] == []
    assert audit["observed_data"]["guest_member_forbidden_projection_fields"] == []


def test_g1_9_closes_machine_gates_but_preserves_external_blockers(tmp_path: Path) -> None:
    report = prepare_g1_9(run_id="g1-9-test", output_dir=tmp_path)

    assert all(report["machine_gates"].values())
    assert report["external_gates"] == {
        "human_expert_reference": False,
        "true_frontier_candidate": False,
        "clean_reproducible_snapshot": False,
    }
    assert report["status"] == "OPERATIONAL_EXTERNAL_GATES_BLOCKED"
    assert report["ready_for_p0_g2"] is False
    assert report["boundary_status"]["sealed_formal_set_access_count"] == 0
    assert report["boundary_status"]["raw_cognition_modified_by_review"] is False
    assert report["boundary_status"]["live_model_calls_performed"] is False
    assert (tmp_path / "P0_G1_9_MACHINE_LOCK_CANDIDATE.json").exists()
    lock = json.loads((tmp_path / "P0_G1_9_MACHINE_LOCK_CANDIDATE.json").read_text(encoding="utf-8"))
    assert lock["status"] == "CANDIDATE_NOT_FORMAL_LOCK"
    assert lock["sealed_assets_hashed_or_accessed"] is False
