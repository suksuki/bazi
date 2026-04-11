"""L1 核心冲突算子编排：在 status 之后、审计/熵合成之前依次应用。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping

from app.plugins.base_physics.core_operators.op_blade_clash import apply_op_blade_clash
from app.plugins.base_physics.core_operators.op_gov_kill_mix import apply_op_gov_kill_mix
from app.plugins.base_physics.core_operators.op_owl_food import apply_op_owl_food
from app.plugins.base_physics.core_operators.op_robber_wealth import apply_op_robber_wealth
from app.plugins.base_physics.core_operators.op_wealth_seal import apply_op_wealth_seal


def apply_l1_core_conflict_operators(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
    conflict_points: List[Any],
) -> List[Dict[str, Any]]:
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["l1_polarity_routing_seeds"] = []
    steps: List[Dict[str, Any]] = []
    steps.extend(apply_op_owl_food(physics_tensor=physics_tensor, settings=settings))
    steps.extend(apply_op_wealth_seal(physics_tensor=physics_tensor, metadata=metadata, settings=settings))
    steps.extend(apply_op_blade_clash(physics_tensor=physics_tensor, metadata=metadata, settings=settings, conflict_points=conflict_points))
    steps.extend(apply_op_robber_wealth(physics_tensor=physics_tensor, metadata=metadata, settings=settings))
    steps.extend(apply_op_gov_kill_mix(physics_tensor=physics_tensor, metadata=metadata, settings=settings))
    return steps
