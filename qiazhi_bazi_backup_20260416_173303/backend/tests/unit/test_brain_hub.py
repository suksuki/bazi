from __future__ import annotations

import json

from app.logic.brain.hub import BrainHub
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def test_brain_hub_build_context_with_sample_19900614() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    hub = BrainHub()
    ctx = hub.build_context(
        metadata=sample["metadata"],
        physics_tensor=sample["physics_tensor"],
        user_intention=sample.get("user_intention", ""),
    )
    assert ctx.tri.static_fact.physics_param_version_id == "pv-mock-19900614"
    assert ctx.psv_list
    assert any(s.axis == "WEALTH" for s in ctx.psv_list)


def test_brain_hub_audit_and_retry_prompt_with_sample_19900614() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    hub = BrainHub()
    ctx = hub.build_context(
        metadata=sample["metadata"],
        physics_tensor=sample["physics_tensor"],
        user_intention=sample.get("user_intention", ""),
    )
    ret = hub.audit("财星高照，近期大发横财。", ctx.psv_list)
    assert ret.audit_state == "REJECT"
    auto_prompt = hub.build_auto_retry_prompt("财星高照，近期大发横财。", ctx.psv_list, ret)
    assert "Evidence Refs" in auto_prompt


def test_brain_hub_orchestrate_emits_probe_waiting_introspection() -> None:
    hub = BrainHub()
    out = hub.orchestrate(
        conflict_points=[{"kind": "harm", "detail": "寅巳穿害"}],
        verified_facts=["VF_1", "VF_2", "VF_3", "VF_4"],
        user_confirmed=False,
    )
    assert out.flow_state == "PROBE_WAITING"
    assert out.seed_key == "harm:寅巳"
    assert out.seed_short == "marriage_clash"
    assert out.target_node_id == "fact-0"
    assert len(out.vf_tags) == 3
    assert len(out.llm_user_message) <= 300
    assert out.introspection_path and "检索种子库" in out.introspection_path
    assert isinstance(out.interrupt_request, dict)
    assert str(out.interrupt_request.get("probe_query") or "").strip()
    assert out.interrupt_request.get("interrupt_id")
    assert out.interrupt_request.get("state") == "pending"


def test_brain_hub_orchestrate_high_lock_probe_query_atomic() -> None:
    hub = BrainHub()
    out = hub.orchestrate(
        conflict_points=[],
        verified_facts=[],
        user_confirmed=False,
        self_abs=1.5,
        output_vector_present=False,
    )
    assert out.flow_state == "PROBE_WAITING"
    assert out.seed_key == "stagnation:high_lock_no_output"
    pq = str(out.interrupt_request.get("probe_query") or "")
    assert "怀才不遇" in pq
    assert out.interrupt_request.get("reason_code") == "high_lock"


def test_brain_hub_master_protocol_gate_and_evidence_chain() -> None:
    hub = BrainHub()
    assert hub.llm_decision_allowed("AMBIGUOUS") is True
    assert hub.llm_decision_allowed("CONFLICT_UNRESOLVED") is True
    assert hub.llm_decision_allowed("READY") is False
    bb = {"VF01", "rule:psv.robber_wealth_pierce_ratio"}
    ok, miss = hub.verify_evidence_chain(
        candidate_refs=["VF01", "rule:psv.robber_wealth_pierce_ratio"],
        blackboard_refs=bb,
    )
    assert ok is True
    assert miss == []
    ok2, miss2 = hub.verify_evidence_chain(candidate_refs=["FAKE_REF"], blackboard_refs=bb)
    assert ok2 is False
    assert miss2 == ["FAKE_REF"]


def test_arch_sentry_payload_limit_under_300_chars() -> None:
    hub = BrainHub()
    messages = hub.enforce_prompt_boundary(
        local_fact_block="FACT_NODE:寅巳穿害导致关系张力上升",
        target_node_id="fact-0",
        vf_tags=["VF01", "VF02", "VF03", "VF04"],
    )
    assert messages
    assert all(len(str((m or {}).get("content") or "")) <= 300 for m in messages)
    assert len(json.dumps(messages, ensure_ascii=False)) <= 300


def test_feedback_assimilation_confirmed_fact() -> None:
    out = BrainHub.assimilate_feedback({"text": "是的，很准"})
    assert out["confirmed"] is True
    assert str((out["fact"] or {}).get("kind") or "") == "CONFIRMED_FACT"
    assert float((out["fact"] or {}).get("weight") or 0.0) == 1.0


def test_export_lineage_injects_htn_defaults() -> None:
    out = BrainHub.export_lineage(seed_short="high_lock", htn_plan={})
    assert out["lineage"] == "HTN_DRIVEN"
    assert out["seeds_matched"] == ["high_lock"]
    assert isinstance((out.get("htn_plan") or {}).get("plan"), list)
    assert len((out.get("htn_plan") or {}).get("plan") or []) > 0
