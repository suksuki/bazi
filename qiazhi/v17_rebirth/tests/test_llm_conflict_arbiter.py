from __future__ import annotations

from v17_rebirth.backend.services.llm_conflict_arbiter import (
    apply_llm_conflict_result,
    build_conflict_bundle,
    build_llm_conflict_prompt,
    parse_llm_conflict_reply,
)


def _meta() -> dict:
    return {
        "plugin_claims": [
            {
                "claim_id": "c1",
                "plugin_id": "l1.physics.op_branch_liuhe",
                "target_god": "正财",
                "intent_vector": {"正财": 0.15},
            },
            {
                "claim_id": "c2",
                "plugin_id": "l2.risk.risk_matrix",
                "target_god": "正财",
                "intent_vector": {"正财": -0.12},
            },
        ],
        "plugin_conflicts": [
            {
                "conflict_id": "cx_1",
                "conflict_type": "same_target_opposite_sign",
                "claims": ["c1", "c2"],
                "recommended_arbiter": "llm",
            }
        ],
        "plugin_conflict_resolutions": [],
        "knowledge_snapshot": {
            "conflict_history": {"recommended_arbiters": {"llm": 2}},
        },
    }


def test_build_conflict_bundle_collects_conflict_claims_and_knowledge() -> None:
    bundle = build_conflict_bundle(meta=_meta(), conflict_id="cx_1")
    assert bundle["conflict"]["conflict_id"] == "cx_1"
    assert len(bundle["claims"]) == 2
    assert bundle["knowledge_snapshot"]["conflict_history"]["recommended_arbiters"]["llm"] == 2


def test_build_llm_conflict_prompt_embeds_bundle_sections() -> None:
    prompt = build_llm_conflict_prompt(bundle=build_conflict_bundle(meta=_meta(), conflict_id="cx_1"))
    assert "## Conflict" in prompt
    assert "## Claims" in prompt
    assert "## Knowledge Snapshot" in prompt
    assert "只输出 JSON" in prompt


def test_parse_llm_conflict_reply_prefers_json_contract() -> None:
    parsed = parse_llm_conflict_reply(
        reply='{"resolution_type":"merge","preferred_arbiter":"system","winner_claim_ids":["c1"],"dropped_claim_ids":["c2"],"reason":"L1优先","confidence":0.81}',
        bundle=build_conflict_bundle(meta=_meta(), conflict_id="cx_1"),
    )
    assert parsed["resolution_type"] == "merge"
    assert parsed["preferred_arbiter"] == "system"
    assert parsed["winner_claim_ids"] == ["c1"]
    assert parsed["dropped_claim_ids"] == ["c2"]


def test_apply_llm_conflict_result_persists_structured_reply() -> None:
    out = apply_llm_conflict_result(
        meta=_meta(),
        conflict_id="cx_1",
        bundle=build_conflict_bundle(meta=_meta(), conflict_id="cx_1"),
        reply='{"resolution_type":"merge"}',
        parsed={
            "resolution_type": "merge",
            "preferred_arbiter": "system",
            "winner_claim_ids": ["c1"],
            "dropped_claim_ids": ["c2"],
            "reason": "L1优先",
            "confidence": 0.81,
        },
    )
    assert out["plugin_conflicts"][0]["resolution_status"] == "resolved_llm"
    assert out["plugin_conflicts"][0]["llm_resolution_type"] == "merge"
    assert out["plugin_conflicts"][0]["next_queue"] == "system"
    assert out["plugin_conflict_resolutions"][0]["winner_claim_id"] == "c1"
    assert out["plugin_conflict_resolutions"][0]["llm_result"]["confidence"] == 0.81
    assert out["brain_action_queue"][0]["action_type"] == "system_merge_suggestion"
    assert out["brain_action_queue"][0]["queue"] == "system"
