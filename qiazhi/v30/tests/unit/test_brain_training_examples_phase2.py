from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from v30.api.app import create_app
from v30.brain import (
    BrainBeliefState,
    BrainClaimBelief,
    BrainDecisionTrace,
    BrainEvidenceGraphSnapshot,
    BrainQuestionCandidate,
)
from v30.brain.contracts import BrainTrainingSafety
from v30.training import BrainTrainingExampleStore, build_brain_training_example


def test_phase2_builds_brain_training_example_from_decision_trace() -> None:
    decision = _decision_trace()

    example = build_brain_training_example(
        reading_id="phase2-reading",
        source="runtime_feedback",
        decision=decision,
        question_outcome={
            "selected_option": "证书平台",
            "answer_type": "choice",
            "claim_delta": {"career.pressure_to_credentials": 0.12},
            "followup_useful": True,
            "confirmed": True,
        },
        labels={
            "question_information_gain": 0.78,
            "advice_actionability": 0.84,
            "template_risk": 0.08,
            "overclaim_risk": 0.12,
            "user_cost": 0.18,
        },
        trainable_targets=["claim_score_weights", "question_selection_policy", "chart_facts"],
        example_id="phase2-example-1",
    )

    assert example.version == "v30.brain_training_example.v1"
    assert example.source == "runtime_feedback"
    assert example.input is not None
    assert example.input.user_goal == "career"
    assert example.outcome.status == "confirmed"
    assert example.outcome.answer_type == "choice"
    assert example.structured_labels.advice_actionability == 0.84
    assert example.safety.chart_fact_mutation_allowed is False
    assert "chart_facts" not in example.trainable_targets
    assert "chart_facts" in example.blocked_targets


def test_phase2_training_safety_rejects_fact_injection() -> None:
    with pytest.raises(ValidationError, match="cannot accept LLM fact injection"):
        BrainTrainingSafety(llm_fact_injection_detected=True)

    with pytest.raises(ValidationError, match="cannot allow chart fact mutation"):
        BrainTrainingSafety(chart_fact_mutation_allowed=True)


def test_phase2_brain_training_example_store_round_trips_jsonl(tmp_path: Path) -> None:
    store = BrainTrainingExampleStore(tmp_path / ".runtime")
    example = build_brain_training_example(
        reading_id="phase2-reading",
        source="synthetic_replay",
        decision=_decision_trace(),
        question_outcome={"skipped": True},
        example_id="phase2-example-store",
    )

    path = store.append(example)
    loaded = store.read()
    summary = store.summary()

    assert path.name == "raw.jsonl"
    assert len(loaded) == 1
    assert loaded[0].example_id == "phase2-example-store"
    assert summary["example_count"] == 1
    assert summary["source_counts"]["synthetic_replay"] == 1
    assert summary["chart_fact_mutation_allowed"] is False


def test_phase2_brain_training_example_store_builds_deterministic_splits(tmp_path: Path) -> None:
    store = BrainTrainingExampleStore(tmp_path / ".runtime")
    for index in range(10):
        store.append(
            build_brain_training_example(
                reading_id="phase2-reading",
                source="runtime_feedback" if index % 2 else "synthetic_replay",
                decision=_decision_trace(),
                question_outcome={"confirmed": True, "selected_option": f"choice-{index}"},
                example_id=f"phase2-example-{index}",
            )
        )

    manifest = store.build_splits(seed=20260628, train_ratio=0.6, validation_ratio=0.2)
    replay_ids = [row.example_id for row in store.read(split="replay", limit=20)]
    repeat = store.build_splits(seed=20260628, train_ratio=0.6, validation_ratio=0.2)
    repeat_replay_ids = [row.example_id for row in store.read(split="replay", limit=20)]
    runtime_feedback = store.read(split="raw", source="runtime_feedback", limit=20)
    summary = store.summary()

    assert manifest["splits"] == {"train": 6, "validation": 2, "replay": 2}
    assert repeat["splits"] == manifest["splits"]
    assert repeat_replay_ids == replay_ids
    assert len(runtime_feedback) == 5
    assert summary["split_manifest"]["seed"] == 20260628


def test_phase2_admin_api_exposes_brain_training_example_summary_and_split(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    store = BrainTrainingExampleStore(runtime_dir)
    for index in range(5):
        store.append(
            build_brain_training_example(
                reading_id="phase2-reading",
                source="runtime_feedback",
                decision=_decision_trace(),
                question_outcome={"confirmed": True, "selected_option": f"choice-{index}"},
                example_id=f"phase2-api-example-{index}",
            )
        )
    app = create_app()
    client = TestClient(app)

    summary = client.get("/api/v30/admin/training/brain-examples/summary").json()
    split = client.post(
        "/api/v30/admin/training/brain-examples/split",
        json={"seed": 9, "train_ratio": 0.6, "validation_ratio": 0.2},
    ).json()
    optimize = client.post(
        "/api/v30/admin/training/brain-examples/optimize",
        json={"split": "train", "min_examples": 3, "max_delta": 0.06},
    ).json()

    assert summary["version"] == "v30.admin.brain_training_example_summary.v1"
    assert summary["store"]["example_count"] == 5
    assert split["version"] == "v30.admin.brain_training_example_split.v1"
    assert split["manifest"]["splits"] == {"train": 3, "validation": 1, "replay": 1}
    assert split["chart_fact_mutation_allowed"] is False
    assert optimize["version"] == "v30.admin.brain_training_example_optimize.v1"
    assert optimize["candidate"]["promotion_signal"] == "eligible"
    assert optimize["candidate"]["chart_fact_mutation_allowed"] is False


def _decision_trace() -> BrainDecisionTrace:
    graph = BrainEvidenceGraphSnapshot(
        graph_id="phase2-reading:graph",
        reading_id="phase2-reading",
        node_count=3,
        edge_count=2,
        node_kinds=["chart_fact", "path", "claim"],
        edge_kinds=["supports"],
        top_claim_ids=["career.pressure_to_credentials"],
        top_path_ids=["path.guan_to_yin"],
    )
    claim = BrainClaimBelief(
        claim_id="career.pressure_to_credentials",
        domain="career",
        status="selected",
        confidence=0.74,
        actionability=0.82,
        uncertainty=0.26,
        supporting_node_ids=["node.path.guan_to_yin"],
        missing_context=["career_pressure_boundary"],
        requires_question=True,
    )
    belief = BrainBeliefState(
        reading_id="phase2-reading",
        active_stage_id="path_reasoning",
        user_goal="career",
        evidence_graph=graph,
        top_claims=[claim],
        missing_context=["career_pressure_boundary"],
        final_decision_readiness=0.68,
    )
    question = BrainQuestionCandidate(
        question_id="q.career.pressure_boundary",
        prompt="事业压力更像岗位责任，还是转化成证书和平台？",
        domain="career",
        answer_shape="choice",
        target_claim_ids=["career.pressure_to_credentials"],
        option_labels=["岗位责任", "证书平台"],
        information_gain=0.78,
        user_cost=0.18,
    )
    return BrainDecisionTrace(
        decision_id="decision.phase2.1",
        reading_id="phase2-reading",
        stage_id="path_reasoning",
        selected_action="ask_stage_question",
        selected_claim_ids=["career.pressure_to_credentials"],
        selected_question_id="q.career.pressure_boundary",
        reason_codes=["high_information_gain", "claim_confidence_near_threshold"],
        feature_vector={"information_gain": 0.78, "user_cost": 0.18, "overask_penalty": 0.12},
        belief_state=belief,
        question_candidates=[question],
        training_targets=["claim_score_weights", "question_selection_policy"],
    )
