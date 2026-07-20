from __future__ import annotations

import json
from pathlib import Path

from core.mingli_agent.benchmark import CognitiveBenchmarkReading
from scripts.v50_audit_runtime_authority import audit_runtime_authority
from scripts.v50_inventory_discovery_archaeology import inventory
from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world
from core.mingli_agent.phase0_governance import validate_phase0_assets
from scripts.v50_prepare_vnext_phase0_g1 import ASSET_PATHS, prepare
from scripts.v50_run_vnext_phase0_benchmark import (
    CRITICAL_PAIRWISE_LANE_PAIRS,
    LANES,
    _audit_reading,
    _failure_classification,
    _holistic_context_payload,
    _run_v30,
    _validate_formal_execution_request,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def test_phase0_pack_is_balanced_and_does_not_fabricate_gold() -> None:
    pack = json.loads(
        (ROOT / "data/validation/fixtures/vnext_cognitive_benchmark_pack_v1.json").read_text(encoding="utf-8")
    )
    categories = [row["category"] for row in pack["cases"]]

    assert len(pack["cases"]) == 10
    assert categories.count("anchor_candidate") == 3
    assert categories.count("contrastive_candidate") == 3
    assert categories.count("ambiguous_candidate") == 2
    assert categories.count("ordinary_control_candidate") == 1
    assert categories.count("negative_control_candidate") == 1
    assert all(row["expert_reference"]["status"] == "pending_human_freeze" for row in pack["cases"])
    assert all(row["controlled_feedback"] == [] for row in pack["cases"])
    assert pack["boundaries"]["expert_reference_fabrication_allowed"] is False


def test_phase0_plan_has_six_lanes_and_no_professional_winner(tmp_path: Path) -> None:
    assert list(LANES) == [
        "direct_same_model",
        "direct_frontier",
        "current_v50",
        "fact_only_deepbazi",
        "holistic_synthesis",
        "vnext",
    ]
    report = run_benchmark(
        run_id="unit-plan",
        live=False,
        dry_run=True,
        repeats=3,
        selected_lanes=list(LANES),
        base_url="http://127.0.0.1:9",
        same_model="same",
        frontier_base_url="http://127.0.0.1:9",
        frontier_model="frontier",
        frontier_kind="local_candidate",
        frontier_max_tokens=6400,
        selected_case_ids=[],
        retry_failures=False,
        output_dir=tmp_path,
    )

    assert report["status"] == "passed"
    assert report["phase0_decision"] == "planned"
    assert report["professional_winner"] is None
    assert report["observed_data"]["output_count"] == 12
    assert report["observed_data"]["planned_count"] == 12
    assert report["scope"]["true_frontier_comparison_complete"] is False
    assert report["boundary_status"]["training_performed"] is False
    assert report["boundary_status"]["professional_winner_claimed"] is False
    assert report["scope"]["resource_access"]["full_taxonomy_accessed"] is False
    assert report["scope"]["resource_access"]["formal_manifest_accessed"] is False
    assert report["scope"]["resource_access"]["expert_reference_accessed"] is False
    assert all(
        len(row["required_pairwise_comparisons"]) == len(CRITICAL_PAIRWISE_LANE_PAIRS)
        for row in report["pairwise_review_rows"]
    )


def test_model_timeout_is_a_policy_failure_not_a_harness_failure() -> None:
    assert _failure_classification(TimeoutError("timed out")) == "model_timeout"


def test_v30_lane_projects_real_runtime_without_llm_fill() -> None:
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json").read_text(encoding="utf-8")
    )
    fixture = next(row for row in taxonomy["cases"] if row["case_id"] == "c2.output_to_wealth.01")
    reading = _run_v30(fixture=fixture, reading_id="phase0-v30-unit")

    assert isinstance(reading, CognitiveBenchmarkReading)
    assert reading.independent_first_look
    assert reading.primary_hypothesis.name
    assert "mechanically projected" in reading.known_uncertainties[0]
    assert reading.cognitive_signature()

    birth = dict(fixture["birth_input"])
    birth["birth_time"] = "12:00"
    world = compile_chart_world(
        reading_id="phase0-v30-audit-unit",
        birth_input=BirthInputCanonical.model_validate(birth),
        include_research_fixture_prior=False,
    )
    audit = _audit_reading(reading=reading, world=world, lane="v30_runtime", model_name="v30_deterministic_runtime")
    assert audit["schema_passed"] is True


def test_historical_v30_is_optional_and_not_a_formal_lane() -> None:
    lanes = json.loads(ASSET_PATHS["lane_policy"].read_text(encoding="utf-8"))
    historical = next(row for row in lanes["optional_nonformal_lanes"] if row["lane_id"] == "historical_v30")

    assert "v30_runtime" not in LANES
    assert historical["required_for_formal_run"] is False
    assert historical["status"] == "unavailable"
    assert historical["use"] == "excluded"


def test_holistic_synthesis_policy_is_frozen_without_vnext_or_legacy_tool_inputs() -> None:
    context = _holistic_context_payload()["holistic_synthesis_protocol"]
    serialized = json.dumps(context, ensure_ascii=False)

    assert context["version"] == "deepbazi.vnext_phase0.holistic_synthesis_policy.v1"
    assert len(context["observation_protocol"]) >= 8
    assert "graph_v1 ranking" in context["forbidden_inputs"]
    assert "VNext challenge pack" in context["forbidden_inputs"]
    assert "VNext epistemic review" in context["forbidden_inputs"]
    assert context["boundaries"]["historical_v30_claim_allowed"] is False
    assert "specific exemplar" not in serialized.lower()


def test_authority_manifest_downgrades_experimental_tools() -> None:
    report = audit_runtime_authority()
    tools = report["observed_data"]["experimental_advisory_tools"]

    assert report["status"] == "passed"
    assert "structural_tools" not in report["observed_data"]["production_authoritative"]
    assert tools["graph_v1"]["authority"] == "experimental_tool_observation"
    assert tools["path_v1"]["authority"] == "experimental_candidate_generator"
    assert report["observed_data"]["research_projection_authority"]["decision_confidence"] == "uncalibrated_research_indicator"


def test_discovery_archaeology_is_read_only_and_finds_legacy_assets() -> None:
    report = inventory()

    assert report["status"] == "completed"
    assert report["observed_data"]["artifact_count"] > 0
    assert report["boundary_status"]["read_only"] is True
    assert report["boundary_status"]["files_deleted"] is False
    assert report["boundary_status"]["research_asset_promoted"] is False


def test_phase0_g1_sets_are_disjoint_and_dry_cases_are_not_formal() -> None:
    validation = validate_phase0_assets(
        taxonomy_path=ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json",
        development_path=ASSET_PATHS["development_set"],
        model_selection_path=ASSET_PATHS["model_selection_set"],
        formal_manifest_path=ASSET_PATHS["formal_manifest"],
        expert_reference_path=ASSET_PATHS["expert_reference"],
        reality_evidence_path=ASSET_PATHS["reality_evidence"],
    )

    assert validation["valid"] is True
    assert len(validation["development_ids"]) == 2
    assert len(validation["model_selection_ids"]) == 5
    assert len(validation["formal_ids"]) == 10
    assert not (set(validation["development_ids"]) & set(validation["formal_ids"]))
    assert "c2.output_to_wealth.01" not in validation["formal_ids"]
    assert "c2.mixed_no_obvious_main_path.01" not in validation["formal_ids"]


def test_round1_expert_reference_cannot_contain_reality_evidence() -> None:
    expert = json.loads(ASSET_PATHS["expert_reference"].read_text(encoding="utf-8"))
    forbidden = {"known_reality_evidence", "reality_observations", "historical_years", "probe_answers"}

    assert expert["status"] == "pending_human_freeze"
    assert all(not (forbidden & set(row)) for row in expert["references"])
    assert expert["boundaries"]["llm_authorship_allowed"] is False


def test_qwen36_is_local_stress_baseline_not_direct_frontier() -> None:
    frontier = json.loads(ASSET_PATHS["frontier_policy"].read_text(encoding="utf-8"))
    lanes = json.loads(ASSET_PATHS["lane_policy"].read_text(encoding="utf-8"))

    assert frontier["selected_policy"] is None
    assert frontier["local_observation"]["model"] == "qwen3.6:27b"
    assert frontier["local_observation"]["direct_frontier_eligible"] is False
    assert len(lanes["formal_lanes"]) == 6
    assert any(row["lane_id"] == "local_open_stress" for row in lanes["optional_nonformal_lanes"])
    assert lanes["status"] == "frozen_for_formal_run"


def test_g1_preparation_blocks_formal_run_without_human_and_external_freeze(tmp_path: Path) -> None:
    report = prepare(run_id="unit-g1", output_dir=tmp_path)
    lock = json.loads((tmp_path / "FORMAL_RUN_LOCK_CANDIDATE.json").read_text(encoding="utf-8"))

    assert report["status"] == "passed_machine_preparation"
    assert report["ready_for_formal_run"] is False
    assert lock["status"] == "candidate_blocked"
    assert "round1_expert_reference_not_human_frozen" in lock["blockers"]
    assert "true_frontier_policy_not_frozen" in lock["blockers"]
    assert "representative_v30_baseline_not_frozen" not in lock["blockers"]
    assert "lane_policy_not_frozen_for_formal_run" not in lock["blockers"]
    assert "v50_code_snapshot_not_committed" in lock["blockers"]
    assert lock["dependency_lock_hash"]
    assert lock["fact_engine_version"].startswith("chart_world_sha256:")
    assert lock["boundaries"]["formal_execution_allowed"] is False


def test_formal_live_run_requires_frozen_lock_before_any_model_call(tmp_path: Path) -> None:
    try:
        run_benchmark(
            run_id="unit-formal-block",
            live=True,
            dry_run=False,
            repeats=3,
            selected_lanes=list(LANES),
            base_url="http://127.0.0.1:9",
            same_model="same",
            frontier_base_url="http://127.0.0.1:9",
            frontier_model="frontier",
            frontier_kind="true_frontier",
            frontier_max_tokens=6400,
            selected_case_ids=[],
            retry_failures=False,
            output_dir=tmp_path,
        )
    except ValueError as exc:
        assert str(exc) == "formal_live_run_requires_frozen_formal_lock"
    else:  # pragma: no cover - the gate must fail closed.
        raise AssertionError("formal run started without a frozen lock")


def test_formal_request_cannot_override_frozen_models_lanes_or_manifests(tmp_path: Path) -> None:
    lock = {
        "execution_policy": {"repeats": 3},
        "model_policy": {
            "same_model": {"model": "qwen3.5:35b"},
            "frontier": {"model": "frontier-v1", "token_budget": 6400},
        },
    }
    errors = _validate_formal_execution_request(
        lock=lock,
        active_manifest_path=tmp_path / "operator-selected.json",
        expert_reference_path=tmp_path / "operator-reference.json",
        selected_lanes=["vnext"],
        repeats=1,
        same_model="different-model",
        frontier_model="different-frontier",
        frontier_kind="local_candidate",
        frontier_max_tokens=3200,
    )

    assert set(errors) == {
        "formal_manifest_override_not_allowed",
        "expert_reference_override_not_allowed",
        "formal_lanes_do_not_match_lock",
        "repeat_count_does_not_match_lock",
        "same_model_does_not_match_lock",
        "frontier_kind_does_not_match_lock",
        "frontier_model_does_not_match_lock",
        "frontier_token_budget_does_not_match_lock",
    }
