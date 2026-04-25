from __future__ import annotations

from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.evidence_bundle import (
    EVIDENCE_BUNDLE_CONTRACT,
    build_evidence_bundle,
    compact_fact_meta,
)


def test_evidence_bundle_preserves_pattern_detail_and_claim_link() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.pattern.yangren_jiasha.v1",
            text="阳刃驾杀候选：刃杀同见，但需校验位置。",
            priority=0.83,
            salience_weight=0.96,
            meta={
                "pattern_candidate": "阳刃驾杀",
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "target_god": "七杀",
                "match_ratio": 0.78,
                "pattern_confidence": 0.74,
                "blade_branch": "寅",
                "blade_scopes": ["month", "hour"],
                "runtime_blade_scopes": [],
                "pattern_scope": "natal",
                "pattern_scope_label": "原局",
            },
        )
    ]
    tensor = {
        "meta": {
            "plugin_claims": [
                {
                    "claim_id": "classical.pattern.yangren_jiasha.v1_claim_0",
                    "plugin_id": "classical.pattern.yangren_jiasha.v1",
                    "claim_text": facts[0].text,
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "target_god": "七杀",
                    "confidence": 0.71,
                    "match_ratio": 0.78,
                }
            ]
        }
    }

    bundle = build_evidence_bundle(facts, physics_tensor=tensor)

    assert bundle["contract"] == EVIDENCE_BUNDLE_CONTRACT
    assert bundle["summary"]["candidate_count"] == 1
    item = bundle["items"][0]
    assert item["claim_id"] == "classical.pattern.yangren_jiasha.v1_claim_0"
    assert item["title"] == "阳刃驾杀"
    assert item["evidence_type"] == "pattern"
    assert item["details"]["blade_branch"] == "寅"
    assert item["details"]["blade_scopes"] == ["month", "hour"]
    assert item["details"]["pattern_scope_label"] == "原局"


def test_evidence_bundle_marks_risk_and_compacts_work_evidence() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.risk_matrix.v1",
            text="伤官见官风险观察：伤官对官星形成压力。",
            priority=0.75,
            salience_weight=0.9,
            meta={
                "risk_driver": "officer_crush",
                "claim_type": "risk_observation",
                "observe_only": True,
                "target_god": "正官",
                "work_evidence": {
                    "relation_family": "risk_officer_crush",
                    "actor_gods": ["伤官"],
                    "receiver_gods": ["正官"],
                    "effect_type": "harm",
                    "match_ratio": 0.82,
                },
            },
        )
    ]

    bundle = build_evidence_bundle(facts)

    assert bundle["summary"]["risk_count"] == 1
    assert bundle["summary"]["observe_only_count"] == 1
    item = bundle["items"][0]
    assert item["evidence_type"] == "risk"
    assert item["observe_only"] is True
    assert item["details"]["work_evidence"]["relation_family"] == "risk_officer_crush"


def test_compact_fact_meta_projects_only_safe_ui_fields() -> None:
    meta = compact_fact_meta(
        {
            "pattern_candidate": "正官格",
            "match_ratio": 0.61818,
            "work_evidence": {"large": "kept out of row"},
            "god_ring_bias": {"huge": True},
        }
    )

    assert meta["pattern_candidate"] == "正官格"
    assert meta["match_ratio"] == 0.6182
    assert "work_evidence" not in meta
    assert "god_ring_bias" not in meta
