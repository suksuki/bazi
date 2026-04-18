from __future__ import annotations

import asyncio

from v17_rebirth.backend.logic.L1_atomic_ops import physics_kernel
from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel


class _FakeBackend:
    def __init__(self) -> None:
        self.physics = {
            "sid": {
                "day_master_stem": "壬",
                "ten_gods_base_l0": {"七杀": 200.0, "正官": 40.0},
                "ten_gods_runtime": {"七杀": 200.0, "正官": 40.0},
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


def test_physics_kernel_keeps_base_and_updates_runtime(monkeypatch) -> None:
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
                "reason": "测试运行态扰动",
                "physical_impact": {
                    "target_god": "七杀",
                    "impact_ratio": 0.1,
                    "significance_weight": 1.0,
                },
            },
        )
    )

    assert ok is True
    tensor = backend.physics["sid"]
    assert tensor["ten_gods_base_l0"]["七杀"] == 200.0
    assert tensor["ten_gods_runtime"]["七杀"] == 220.0
    assert tensor["ten_gods_absolute"]["七杀"] == 220.0


def test_physics_kernel_clamps_runtime_before_writeback(monkeypatch) -> None:
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
                "reason": "测试钳制",
                "physical_impact": {
                    "target_god": "七杀",
                    "impact_ratio": 99.0,
                    "significance_weight": 1.0,
                },
            },
        )
    )

    assert ok is False
    assert backend.physics["sid"]["ten_gods_runtime"]["七杀"] == 200.0
    assert backend.published[-1]["signal"] == "PHYSICS_ANOMALY"


def test_physics_kernel_rejects_runtime_base_ratio_over_three(monkeypatch) -> None:
    backend = _FakeBackend()

    monkeypatch.setattr(physics_kernel, "get_state_backend", lambda: backend)

    class _ExplodeFlowEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {"七杀": 5000.0, "正官": 0.0}, "topology": []}

    monkeypatch.setattr(physics_kernel, "FlowPhysicsEngine", _ExplodeFlowEngine)
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration._get_god_to_element_map",
        lambda *_args, **_kwargs: {"七杀": "土", "正官": "土"},
    )

    ok = asyncio.run(
        PhysicsKernel.dispatch_perturbation(
            session_id="sid",
            source="SRC_MANUAL",
            payload={"reason": "测试熔断"},
        )
    )

    assert ok is False
    assert backend.physics["sid"]["ten_gods_runtime"]["七杀"] == 200.0
    assert backend.published[-1]["payload"]["type"] == "AnomalyFrame"
