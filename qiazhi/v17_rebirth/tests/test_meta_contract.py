from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.services.meta_contract import build_meta_contract


def test_meta_contract_splits_public_and_solver_trace_keys() -> None:
    contract = build_meta_contract(
        {
            "god_ring_authority": {"use_gods": ["食神"]},
            "relation_formation_summary": [{"family_key": "sanhe"}],
            "plugin_claims": [{"claim_id": "c1"}],
            "knowledge_snapshot": {"claim_history": {}},
            "master_reasoning": {"summary": "ok"},
        }
    )

    assert contract["protocol"] == "v17.meta_contract.v1"
    assert "god_ring_authority" in contract["public_meta_keys"]
    assert "relation_formation_summary" in contract["public_meta_keys"]
    assert "plugin_claims" in contract["solver_trace_keys"]
    assert "knowledge_snapshot" in contract["learning_signal_keys"]
    assert contract["boundary"]["solver_trace_meta"]


def test_hydration_emits_meta_contract_without_changing_runtime_scores() -> None:
    four_pillars = {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"}
    scores, _top, _total, meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar="庚子",
        flow_pillar="丙午",
        gender="male",
    )
    pt = {
        "four_pillars": four_pillars,
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "gender": "male",
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "meta": dict(meta or {}),
    }

    hydrate_v17_physics_tensor(pt)

    contract = pt["meta"].get("meta_contract")
    assert isinstance(contract, dict)
    assert contract["protocol"] == "v17.meta_contract.v1"
    assert "plugin_execution_status" in contract["public_meta_keys"]
    assert "plugin_claims" in contract["solver_trace_keys"]
    assert isinstance(pt.get("ten_gods_runtime"), dict)

