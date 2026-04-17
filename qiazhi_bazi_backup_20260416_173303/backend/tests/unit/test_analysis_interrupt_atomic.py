from __future__ import annotations

from app.logic.brain.hub import BrainHub
from app.services.analysis_service import _merge_interrupt_request_atomic


def test_merge_interrupt_atomic_merges_hub_with_loop_m3() -> None:
    hub = BrainHub()
    orch = hub.orchestrate(
        conflict_points=[{"kind": "harm", "detail": "寅巳穿害"}],
        verified_facts=["VF_1"],
        user_confirmed=False,
    )
    loop = {
        "interrupt_id": "ap-m3-test",
        "reason_code": "M3_L1_LOGIC_CONFLICT_PENDING",
        "probe_query": "M3 追问：请确认冲突分支。",
        "state": "pending",
    }
    merged = _merge_interrupt_request_atomic(orchestration=orch, loop_interrupt=loop, session_hint=99)
    assert merged["reason_code"] == "M3_L1_LOGIC_CONFLICT_PENDING"
    assert "M3 追问" in str(merged.get("probe_query") or "")
    assert str(merged.get("interrupt_id") or "").startswith("ap-m3")


def test_merge_interrupt_atomic_fills_from_hub_when_loop_empty() -> None:
    hub = BrainHub()
    orch = hub.orchestrate(
        conflict_points=[],
        verified_facts=[],
        user_confirmed=False,
        self_abs=1.5,
        output_vector_present=False,
    )
    merged = _merge_interrupt_request_atomic(orchestration=orch, loop_interrupt={}, session_hint=100)
    assert "怀才不遇" in str(merged.get("probe_query") or "")
    assert str(merged.get("interrupt_id") or "")
