"""V13.02：resume 轮次超限时的 Finality Hammer。"""

from __future__ import annotations

from app.logic.brain.hub import BrainHub


def test_finality_hammer_after_three_resume_rounds() -> None:
    hub = BrainHub()
    phys: dict = {"meta": {"global_conflict_tension": 0.88}}
    hist = [{"at": "a"}, {"at": "b"}, {"at": "c"}, {"at": "d"}]
    out = hub.orchestrate(
        conflict_points=[{"kind": "harm", "detail": "寅巳穿害"}],
        verified_facts=["VF_1"],
        user_confirmed=False,
        resume_feedback_history=hist,
        physics_tensor=phys,
    )
    assert out.finality_hammer_applied is True
    assert out.flow_state == "READY"
    assert out.interrupt_request == {}
    assert float(phys["meta"]["global_conflict_tension"]) == 0.05
    assert phys["meta"].get("v1302_finality_hammer") is True
    assert str(out.htn_plan.get("active_task") or "") == "SYNTHESIS"


def test_no_finality_hammer_when_history_short() -> None:
    hub = BrainHub()
    phys: dict = {"meta": {"global_conflict_tension": 0.5}}
    hist = [{"at": "1"}, {"at": "2"}, {"at": "3"}]
    out = hub.orchestrate(
        conflict_points=[{"kind": "harm", "detail": "寅巳穿害"}],
        verified_facts=["VF_1"],
        user_confirmed=False,
        resume_feedback_history=hist,
        physics_tensor=phys,
    )
    assert out.finality_hammer_applied is False
    assert out.flow_state == "PROBE_WAITING"
    assert float(phys["meta"]["global_conflict_tension"]) == 0.5
