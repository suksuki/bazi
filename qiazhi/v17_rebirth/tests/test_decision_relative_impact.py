from __future__ import annotations

import asyncio

from v17_rebirth.backend.logic.L1_atomic_ops import physics_kernel
from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel


class _FakeBackend:
    def __init__(self) -> None:
        self.physics = {
            "sid": {
                "day_master_stem": "壬",
                "ten_gods_absolute": {"七杀": 200.0, "正官": 40.0},
                "ten_gods_ledger": {"七杀": [{"step": "L0_BASE", "val": 200.0, "reason": "基线"}]},
            }
        }
        self.published: list[dict] = []

    async def get_physics(self, session_id: str) -> dict:
        return dict(self.physics.get(session_id) or {})

    async def set_physics(self, session_id: str, tensor: dict) -> bool:
        self.physics[session_id] = dict(tensor)
        return True

    async def publish_action(self, _session_id: str, event: dict) -> None:
        self.published.append(event)


def test_relative_ratio_model_records_original_ratio_and_final(monkeypatch) -> None:
    backend = _FakeBackend()

    monkeypatch.setattr(physics_kernel, "get_state_backend", lambda: backend)

    class _NoFlowEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {"七杀": 0.0, "正官": 0.0}, "topology": []}

    monkeypatch.setattr(physics_kernel, "FlowPhysicsEngine", _NoFlowEngine)
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration._get_god_to_element_map",
        lambda *_args, **_kwargs: {"七杀": "土", "正官": "土"},
    )

    ok = asyncio.run(
        PhysicsKernel.dispatch_perturbation(
            session_id="sid",
            source="SRC_MANUAL",
            payload={
                "reason": "六冲触发",
                "physical_impact": {
                    "target_god": "七杀",
                    "impact_ratio": 0.12,
                    "significance_level": "L3",
                    "significance_weight": 1.0,
                },
            },
        )
    )

    assert ok is True
    tensor = backend.physics["sid"]
    assert tensor["ten_gods_absolute"]["七杀"] == 224.0
    ledger = tensor["ten_gods_ledger"]["七杀"][-1]
    assert ledger["original_value"] == 200.0
    assert ledger["ratio_applied"] == 0.12
    assert ledger["final_value"] == 224.0
    assert ledger["visible_ratio_change"] is True


def test_relative_ratio_model_hides_sub_half_percent_noise(monkeypatch) -> None:
    backend = _FakeBackend()

    monkeypatch.setattr(physics_kernel, "get_state_backend", lambda: backend)

    class _NoFlowEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {"七杀": 0.0, "正官": 0.0}, "topology": []}

    monkeypatch.setattr(physics_kernel, "FlowPhysicsEngine", _NoFlowEngine)
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration._get_god_to_element_map",
        lambda *_args, **_kwargs: {"七杀": "土", "正官": "土"},
    )

    asyncio.run(
        PhysicsKernel.dispatch_perturbation(
            session_id="sid",
            source="SRC_MANUAL",
            payload={
                "reason": "微弱波动",
                "physical_impact": {
                    "target_god": "七杀",
                    "impact_ratio": 0.004,
                    "significance_level": "L0",
                    "significance_weight": 1.0,
                },
            },
        )
    )

    ledger = backend.physics["sid"]["ten_gods_ledger"]["七杀"][-1]
    assert ledger["ratio_applied"] == 0.004
    assert ledger["visible_ratio_change"] is False
