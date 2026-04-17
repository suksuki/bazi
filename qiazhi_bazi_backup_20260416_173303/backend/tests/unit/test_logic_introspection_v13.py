from __future__ import annotations

import asyncio
from unittest.mock import patch

from app.api.contracts import AnalyzeClashRequest, FinalVerdictRequest
from app.services import analysis_service
from app.services.bazi_engine import get_bazi


class _FakeClient:
    async def chat_with_telemetry(self, messages, temperature, max_tokens, stop):
        return "首观：冲突点已识别，待仲裁。", {"elapsed_ms": 1.0, "approx_tokens": 8.0, "usage": {}}

    async def chat(self, messages, temperature, max_tokens, stop):
        raw, _ = await self.chat_with_telemetry(messages, temperature, max_tokens, stop)
        return raw


class _FakeFinalVerdictSkill:
    async def generate(self, **kwargs):
        md = kwargs.get("metadata") if isinstance(kwargs.get("metadata"), dict) else {}
        pl = md.get("persistence_layer") if isinstance(md.get("persistence_layer"), dict) else {}
        rh = pl.get("resume_feedback_history") if isinstance(pl.get("resume_feedback_history"), list) else []
        first_feedback = ""
        if rh and isinstance(rh[0], dict):
            uf = rh[0].get("user_feedback_payload")
            if isinstance(uf, dict):
                first_feedback = str(uf.get("answer") or uf.get("feedback") or "").strip()
        user_ctx = first_feedback or "NO_RESUME_FEEDBACK"
        return {
            "version_id": "v13-trace-ut",
            "verdict_body": "终判：可执行，建议以稳态优先。",
            "change_log": [],
            "logical_evidence": ["conflict_matrix.points[0]", "fact-0"],
            "work_vector": {},
            "topology_graph_v1": {},
            "hit_pattern_name": "测试格局",
            "structure_candidates_v0": {},
            "structure_final_decision_v0": {},
            "plugin_outputs_verdict_ready": {},
            "plugin_conflict_report": {},
            "audit_log": {},
            "confirmed_decisions": [],
            "llm_request_messages": [
                {"role": "system", "content": "FINAL_VERDICT_SYSTEM: enforce assertion_tree and will alignment."},
                {"role": "user", "content": f"user_context / will_proxy: {user_ctx}"},
            ],
            "llm_raw_response": '{"final_verdict":"ok"}',
            "llm_meta": {"model_name": "ut-stub", "elapsed_ms": 2.0},
            "narrative_chunks": [],
            "metadata_memory_patch": {},
            "l1_junction_flags": {},
            "brain_hub": {"lineage": "HTN_DRIVEN", "seeds_matched": ["system_stress"], "htn_plan": {"plan": ["OBSERVE"]}},
            "narrative_strategy": "assertion_tree",
            "assertion_tree": {
                "protocol": "assertion_tree.v1",
                "nodes": [{"node_id": "fact-0", "node_type": "FACT", "text": "冲突点", "evidence_refs": ["conflict_matrix.points[0]"]}],
            },
        }


async def _inject_fake_arbiter(out, session_id, lang, client):
    pt = out.get("physics_tensor") if isinstance(out.get("physics_tensor"), dict) else {}
    meta = pt.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["arbitration_audit_feed_v1"] = [
            {
                "audit_id": "arb-1",
                "timestamp": "2026-04-15T00:00:00Z",
                "llm_prompt": [
                    {"role": "system", "content": "ARBITRATION_SYSTEM: resolve conflict by ledger and entropy."},
                    {"role": "user", "content": "conflict=寅申冲"},
                ],
                "llm_raw_response": "裁决：保留主冲，次冲递延。",
                "conflict": {"kind": "clash", "detail": "寅申冲"},
            },
            {
                "audit_id": "arb-2",
                "timestamp": "2026-04-15T00:00:01Z",
                "llm_prompt": [
                    {"role": "system", "content": "ARBITRATION_SYSTEM: second pass consistency check."},
                    {"role": "user", "content": "conflict=寅巳穿"},
                ],
                "llm_raw_response": "裁决：纳入次要冲突。",
                "conflict": {"kind": "harm", "detail": "寅巳穿"},
            },
        ]
    out["physics_tensor"] = pt
    return out


def test_logic_introspection_full_trace_v13_contains_three_stages_and_messages() -> None:
    pillars = get_bazi("1990-06-14", "12:00", "solar")
    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()), patch(
        "app.services.helpers.v1294_silent_arbiter.maybe_apply_v1294_silent_arbiter_to_analyze_clash",
        new=_inject_fake_arbiter,
    ):
        clash_out = asyncio.run(
            analysis_service.analyze_clash_flow(
                AnalyzeClashRequest(
                    pillars=pillars,
                    enabled_plugins=["classical.blind_school.v1"],
                )
            )
        )

    md = clash_out.get("metadata") if isinstance(clash_out.get("metadata"), dict) else {}
    pl = md.setdefault("persistence_layer", {}) if isinstance(md, dict) else {}
    if isinstance(pl, dict):
        pl["resume_feedback_history"] = [
            {"user_feedback_payload": {"answer": "我确认冲突，以稳态与长期收益为先。"}}
        ]

    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=_FakeFinalVerdictSkill()):
        fv_out = asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata=md,
                    physics_tensor=clash_out.get("physics_tensor") or {"meta": {}, "abs_nodes": {"比肩": 1.0}},
                    selected_cards=[],
                    consensus_history=[],
                    previous_verdict="",
                    previous_logical_evidence=[],
                    lang="ZH",
                ),
                [],
            )
        )

    patch_md = fv_out.get("metadata_memory_patch") if isinstance(fv_out.get("metadata_memory_patch"), dict) else {}
    li = patch_md.get("logic_introspection") if isinstance(patch_md.get("logic_introspection"), dict) else {}
    full_trace = li.get("full_trace") if isinstance(li.get("full_trace"), list) else []

    assert len(full_trace) > 3
    stages = {str((row or {}).get("stage") or "") for row in full_trace if isinstance(row, dict)}
    assert {"FIRST_OBSERVATION", "ARBITRATION", "FINAL_VERDICT"}.issubset(stages)

    for row in full_trace:
        assert isinstance(row, dict)
        msgs = row.get("messages")
        assert isinstance(msgs, list) and len(msgs) > 0
        has_system = any(
            isinstance(m, dict) and str(m.get("role") or "").strip().lower() == "system"
            for m in msgs
        )
        assert has_system

    final_rows = [row for row in full_trace if isinstance(row, dict) and str(row.get("stage") or "") == "FINAL_VERDICT"]
    assert final_rows
    final_msg_text = "\n".join(
        str(m.get("content") or "")
        for m in (final_rows[-1].get("messages") or [])
        if isinstance(m, dict)
    )
    assert "我确认冲突，以稳态与长期收益为先" in final_msg_text
