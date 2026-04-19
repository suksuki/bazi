from __future__ import annotations

from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.claim_protocol import compile_claims
from v17_rebirth.backend.services.decision_compiler import compile_pending_decisions
from v17_rebirth.backend.services.pattern_confidence import derive_pattern_confidence


def test_derive_pattern_confidence_for_candidate() -> None:
    meta = derive_pattern_confidence(
        plugin_id="classical.pattern.axis.v1",
        meta={
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "match_ratio": 0.72,
            "origin_multiplier": 1.0,
            "manifestation_state": "supported",
            "projection_share": 0.66,
            "dominant_ratio": 1.8,
        },
        priority=0.77,
        salience_weight=0.95,
    )
    assert float(meta["pattern_confidence"]) > 0.6
    assert meta["pattern_confidence_label"] in {"中高置信", "高置信"}


def test_compile_pending_decisions_promotes_pattern_confidence_for_display() -> None:
    rows = compile_pending_decisions(
        facts=[
            V17Fact(
                plugin_id="classical.pattern.axis.v1",
                text="格局轴线候选：伤官 当前为最强主轴，可作为格局专题的第一观察面。",
                decision_hint="格局轴线",
                causal_tier=3,
                priority=0.77,
                salience_weight=0.95,
                meta={
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "match_ratio": 0.72,
                    "target_god": "伤官",
                    "pattern_candidate": "主轴格",
                    "manifestation_state": "supported",
                    "projection_share": 0.66,
                    "dominant_ratio": 1.8,
                },
            )
        ],
        spec_decisions=[],
        existing_rows=[],
    )
    assert rows
    assert float(rows[0]["pattern_confidence"]) > 0.0
    assert str(rows[0]["pattern_confidence_label"]).strip() != ""


def test_compile_claims_uses_pattern_confidence_as_claim_confidence() -> None:
    claims = compile_claims(
        facts=[
            V17Fact(
                plugin_id="classical.pattern.axis.v1",
                text="格局轴线候选：正官 当前为最强主轴。",
                causal_tier=3,
                priority=0.77,
                salience_weight=0.95,
                meta={
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "match_ratio": 0.72,
                    "target_god": "正官",
                    "manifestation_state": "manifested",
                    "projection_share": 0.74,
                    "dominant_ratio": 2.1,
                },
            )
        ]
    )
    assert claims
    assert float(claims[0]["confidence"]) > 0.6
    assert float(claims[0]["match_ratio"]) == 0.72
