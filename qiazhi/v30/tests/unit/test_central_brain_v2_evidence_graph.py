from __future__ import annotations

from v30.brain.reading_engine import build_central_reading_state
from v30.runtime import create_smoke_runtime


def test_cbi_v2_runtime_exposes_full_diagnosis_graph_to_central_reading() -> None:
    runtime = create_smoke_runtime("pytest-cbi-v2-graph-runtime")
    effect = runtime.question_plan.policy_effect
    diagnosis = effect["real_bazi_diagnosis"]
    central = effect["central_reading_state"]

    assert isinstance(diagnosis["graph"], dict)
    assert len(diagnosis["graph"]["nodes"]) > 0
    assert len(diagnosis["graph"]["edges"]) > 0
    assert central["evidence_graph_snapshot"]["graph_missing"] is False
    assert central["evidence_graph_snapshot"]["node_count"] == len(diagnosis["graph"]["nodes"])
    assert central["evidence_graph_snapshot"]["edge_count"] == len(diagnosis["graph"]["edges"])
    assert central["graph_detail_status"] == "ready"
    assert central["graph_claim_metric_count"] > 0
    assert "diagnosis_graph" in central["candidate_sources"]
    assert "graph_claim_score_weight" in central["training_signal"]["targets"]


def test_cbi_v2_claim_score_uses_graph_support_and_counterevidence() -> None:
    diagnosis = {
        "status": "ready",
        "claims": [
            {
                "claim_id": "claim:career",
                "claim_level": "domain",
                "domain": "career",
                "claim_text": "事业压力需要转为资质和平台能力。",
                "confidence_band": "medium",
                "evidence_ids": ["ev:career"],
                "path_ids": ["path:career"],
                "needs_user_calibration": True,
                "blocked_overclaim": ["fixed_event_prediction"],
            }
        ],
        "paths": [
            {
                "path_id": "path:career",
                "score": 0.7,
                "timing_trigger": {},
            }
        ],
        "portraits": [],
        "graph": {
            "graph_id": "graph:test",
            "reading_id": "pytest-cbi-v2-graph-score",
            "nodes": [
                {
                    "node_id": "node:feature:career",
                    "node_kind": "feature",
                    "ref_id": "feature:career",
                    "domain": "career",
                    "weight": 0.82,
                    "metadata": {},
                },
                {
                    "node_id": "node:path:career",
                    "node_kind": "path",
                    "ref_id": "path:career",
                    "domain": "career",
                    "weight": 0.7,
                    "metadata": {},
                },
                {
                    "node_id": "node:claim:career",
                    "node_kind": "claim",
                    "ref_id": "claim:career",
                    "domain": "career",
                    "weight": 0.68,
                    "metadata": {},
                },
            ],
            "edges": [
                {
                    "edge_id": "edge:supports:feature->claim",
                    "source_node_id": "node:feature:career",
                    "target_node_id": "node:claim:career",
                    "edge_kind": "supports",
                    "weight": 0.82,
                    "evidence_ids": ["ev:career"],
                },
                {
                    "edge_id": "edge:explains:path->claim",
                    "source_node_id": "node:path:career",
                    "target_node_id": "node:claim:career",
                    "edge_kind": "explains",
                    "weight": 0.7,
                    "evidence_ids": ["ev:career"],
                },
                {
                    "edge_id": "edge:asks:claim->claim",
                    "source_node_id": "node:claim:career",
                    "target_node_id": "node:claim:career",
                    "edge_kind": "asks_followup",
                    "weight": 0.72,
                    "evidence_ids": ["ev:career"],
                },
            ],
            "top_claim_ids": ["claim:career"],
            "top_path_ids": ["path:career"],
        },
        "summaries": {},
        "public_projection": {},
    }

    state = build_central_reading_state(
        reading_id="pytest-cbi-v2-graph-score",
        role_key="user",
        diagnosis=diagnosis,
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
    )
    score = state["claim_scores"][0]

    assert state["evidence_graph_snapshot"]["graph_missing"] is False
    assert state["graph_detail_status"] == "ready"
    assert score["graph_metrics"]["support_edge_count"] == 2
    assert score["graph_metrics"]["requires_edge_count"] == 1
    assert score["components"]["graph_support"] > 0.0
    assert score["components"]["graph_prior"] == 1.0
    assert score["components"]["graph_path_coherence"] > 0.0
    assert score["boundary"] == "central_claim_score_ranks_existing_claim_without_generating_new_fact"
