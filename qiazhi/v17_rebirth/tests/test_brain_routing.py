from __future__ import annotations

from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot


def test_build_knowledge_snapshot_summarizes_claims_conflicts_and_resolutions() -> None:
    snapshot = build_knowledge_snapshot(
        claims=[
            {"claim_type": "weaken", "target_god": "食神"},
            {"claim_type": "weaken", "target_god": "食神"},
            {"claim_type": "enhance", "target_god": "正财"},
        ],
        conflicts=[
            {"conflict_type": "same_event_duplicate", "recommended_arbiter": "system"},
            {"conflict_type": "same_target_opposite_sign", "recommended_arbiter": "llm"},
        ],
        conflict_resolutions=[
            {"resolved_by": "system"},
        ],
        current_authority={
            "effect_scores": {
                "食神": {"flux_tension_load": 0.18, "resolved_utility_flux": 0.66},
            },
            "judgement_bias_protocol": {
                "summary": {
                    "by_target": {
                        "食神": {"use_bias": 0.12, "taboo_bias": 0.03, "entry_count": 2},
                    }
                }
            },
            "stage_bias_protocol": {
                "summary": {
                    "by_target": {
                        "食神": {"use_boost": 0.2, "taboo_boost": 0.0, "stability_boost": 0.08, "volatility_boost": 0.02},
                    }
                }
            },
        },
    )

    assert snapshot["claim_history"]["total_claims"] == 3
    assert snapshot["claim_history"]["by_type"]["weaken"] == 2
    assert snapshot["conflict_history"]["by_type"]["same_event_duplicate"] == 1
    assert snapshot["resolution_preview"]["resolved_by"]["system"] == 1
    assert snapshot["claim_history"]["current_targets"]["食神"]["flux_tension_load"] == 0.18
    assert snapshot["claim_history"]["current_targets"]["食神"]["judgement_use_bias"] == 0.12
    assert snapshot["claim_history"]["current_targets"]["食神"]["stage_stability_boost"] == 0.08


def test_route_conflicts_prefers_severity_policy_with_session_knowledge() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P3", "recommended_arbiter": "system"},
        {"conflict_id": "c2", "severity": "P2", "recommended_arbiter": "llm"},
        {"conflict_id": "c3", "severity": "P1", "recommended_arbiter": "llm"},
    ]
    knowledge_snapshot = {
        "conflict_history": {
            "recommended_arbiters": {
                "system": 4,
                "llm": 2,
                "user": 1,
            }
        }
    }

    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "system"
    assert routed[1]["recommended_arbiter"] == "llm"
    assert routed[2]["recommended_arbiter"] == "user"
    assert routed[0]["routing_policy"] == "severity_plus_session_preference"


def test_route_conflicts_keeps_valid_explicit_recommendation() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P2", "recommended_arbiter": "user"},
    ]
    routed = route_conflicts(
        conflicts=conflicts,
        knowledge_snapshot={"conflict_history": {"recommended_arbiters": {"user": 9}}},
    )
    assert routed[0]["recommended_arbiter"] == "user"


def test_route_conflicts_falls_back_when_explicit_arbiter_is_invalid() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P2", "recommended_arbiter": "auto"},
        {"conflict_id": "c2", "severity": "P3", "recommended_arbiter": ""},
        {"conflict_id": "c3", "severity": "", "recommended_arbiter": "invalid"},
    ]
    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot={"conflict_history": {"recommended_arbiters": {"system": 0, "llm": 0}}})
    assert routed[0]["recommended_arbiter"] == "llm"
    assert routed[1]["recommended_arbiter"] == "system"
    assert routed[2]["recommended_arbiter"] == "system"


def test_build_knowledge_snapshot_merges_feedback_arbiters() -> None:
    snapshot = build_knowledge_snapshot(
        claims=[],
        conflicts=[],
        conflict_resolutions=[],
        feedback_rows=[
            {"status": "llm"},
            {"status": "user"},
            {"status": "queued_llm", "meta": {"arbiter": "llm"}},
        ],
    )

    assert snapshot["conflict_history"]["feedback_arbiters"]["llm"] == 2
    assert snapshot["conflict_history"]["feedback_arbiters"]["user"] == 1
    assert "feedback_arbiter_scores" in snapshot["conflict_history"]


def test_route_conflicts_consume_feedback_arbiters() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P2", "recommended_arbiter": "system"},
    ]
    knowledge_snapshot = {
        "conflict_history": {
            "recommended_arbiters": {"system": 0, "llm": 1, "user": 0},
            "feedback_arbiters": {"llm": 3, "system": 0, "user": 0},
        }
    }
    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "llm"


def test_route_conflicts_consume_feedback_scores() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P2", "recommended_arbiter": "system"},
    ]
    knowledge_snapshot = {
        "conflict_history": {
            "recommended_arbiters": {"system": 0, "llm": 0, "user": 0},
            "feedback_arbiters": {"llm": 1, "system": 0, "user": 0},
            "feedback_arbiter_scores": {"llm": 0.92, "system": 0.00, "user": 0.00},
        }
    }
    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "llm"


def test_feedback_residual_scales_arbiter_scores() -> None:
    snapshot = build_knowledge_snapshot(
        claims=[],
        conflicts=[],
        conflict_resolutions=[],
        feedback_rows=[
            {"status": "system", "residual_correction": 1.0},
            {"status": "llm", "residual_correction": -1.0},
        ],
    )

    assert snapshot["conflict_history"]["feedback_arbiter_scores"]["system"] > 1.0
    assert snapshot["conflict_history"]["feedback_arbiter_scores"]["llm"] < 1.0
    assert round(snapshot["conflict_history"]["feedback_arbiter_scores"]["system"], 3) == 1.6
    assert round(snapshot["conflict_history"]["feedback_arbiter_scores"]["llm"], 3) == 0.378


def test_route_conflicts_uses_feedback_quality() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P3", "recommended_arbiter": ""},
    ]
    knowledge_snapshot = {
        "conflict_history": {
            "feedback_arbiters": {"system": 1, "llm": 1, "user": 0},
            "feedback_arbiter_scores": {"system": 1.6, "llm": 0.4, "user": 0.0},
        }
    }

    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "system"


def test_route_conflicts_uses_live_target_tension_for_same_target_opposite_sign() -> None:
    conflicts = [
        {
            "conflict_id": "c1",
            "severity": "P2",
            "conflict_type": "same_target_opposite_sign",
            "target_god": "正官",
            "recommended_arbiter": "system",
            "conflict_score": 0.52,
        },
    ]
    knowledge_snapshot = {
        "claim_history": {
            "current_targets": {
                "正官": {
                    "flux_tension_load": 0.56,
                    "flux_reinforce_load": 0.02,
                    "contest_pressure": 0.31,
                }
            }
        },
        "conflict_history": {
            "recommended_arbiters": {"system": 1, "llm": 0, "user": 0},
        },
    }

    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "llm"
    assert routed[0]["live_target_tension"] == 0.56


def test_route_conflicts_reads_judgement_and_stage_signals_from_authority_snapshot() -> None:
    conflicts = [
        {
            "conflict_id": "c2",
            "severity": "P2",
            "conflict_type": "same_target_opposite_sign",
            "target_god": "正官",
            "recommended_arbiter": "system",
            "conflict_score": 0.48,
        },
    ]
    knowledge_snapshot = {
        "claim_history": {
            "current_targets": {
                "正官": {
                    "flux_tension_load": 0.24,
                    "flux_reinforce_load": 0.02,
                    "contest_pressure": 0.18,
                    "judgement_use_bias": 0.26,
                    "judgement_taboo_bias": 0.22,
                    "judgement_entry_count": 3,
                    "stage_use_boost": 0.14,
                    "stage_taboo_boost": 0.03,
                    "stage_stability_boost": 0.02,
                    "stage_volatility_boost": 0.11,
                    "authority_profile": "高能躁动",
                }
            }
        },
        "conflict_history": {
            "recommended_arbiters": {"system": 1, "llm": 0, "user": 0},
        },
    }

    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "llm"
    assert routed[0]["live_target_judgement_entries"] == 3.0
    assert routed[0]["live_target_stage_volatility"] == 0.11
