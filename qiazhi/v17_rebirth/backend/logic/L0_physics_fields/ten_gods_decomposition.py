from __future__ import annotations

from typing import Dict


def ensure_decomposition_bucket(
    decomposition: Dict[str, Dict[str, float]],
    god: str,
) -> Dict[str, float]:
    row = decomposition.get(god)
    if isinstance(row, dict):
        return row
    row = {
        "manifest": 0.0,
        "root": 0.0,
        "momentum": 0.0,
        "momentum_month_order": 0.0,
        "momentum_stage": 0.0,
        "momentum_stage_lu": 0.0,
        "momentum_stage_blade": 0.0,
        "momentum_stage_general": 0.0,
        "momentum_structure": 0.0,
        "momentum_auxiliary": 0.0,
        "hidden": 0.0,
        "total": 0.0,
    }
    decomposition[god] = row
    return row


def add_decomposition(
    decomposition: Dict[str, Dict[str, float]],
    god: str,
    *,
    manifest: float = 0.0,
    root: float = 0.0,
    momentum: float = 0.0,
    momentum_month_order: float = 0.0,
    momentum_stage: float = 0.0,
    momentum_stage_lu: float = 0.0,
    momentum_stage_blade: float = 0.0,
    momentum_stage_general: float = 0.0,
    momentum_structure: float = 0.0,
    momentum_auxiliary: float = 0.0,
    hidden: float = 0.0,
) -> None:
    row = ensure_decomposition_bucket(decomposition, god)
    month_order = max(0.0, float(momentum_month_order or 0.0))
    stage_lu = max(0.0, float(momentum_stage_lu or 0.0))
    stage_blade = max(0.0, float(momentum_stage_blade or 0.0))
    stage_general = max(0.0, float(momentum_stage_general or 0.0))
    stage = max(0.0, float(momentum_stage or 0.0)) + stage_lu + stage_blade + stage_general
    structure = max(0.0, float(momentum_structure or 0.0))
    auxiliary = max(0.0, float(momentum_auxiliary or 0.0))
    total_momentum = max(0.0, float(momentum or 0.0)) + month_order + stage + structure + auxiliary
    row["manifest"] += max(0.0, float(manifest or 0.0))
    row["root"] += max(0.0, float(root or 0.0))
    row["momentum"] += total_momentum
    row["momentum_month_order"] += month_order
    row["momentum_stage"] += stage
    row["momentum_stage_lu"] += stage_lu
    row["momentum_stage_blade"] += stage_blade
    row["momentum_stage_general"] += stage_general
    row["momentum_structure"] += structure
    row["momentum_auxiliary"] += auxiliary
    row["hidden"] += max(0.0, float(hidden or 0.0))
    row["total"] = row["manifest"] + row["root"] + row["momentum"] + row["hidden"]


def finalize_decomposition(
    decomposition: Dict[str, Dict[str, float]],
    *,
    damping: float,
    energy_min: float,
    energy_max: float,
) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for god, raw in decomposition.items():
        if not isinstance(raw, dict):
            continue
        manifest = max(0.0, float(raw.get("manifest") or 0.0)) * damping
        root = max(0.0, float(raw.get("root") or 0.0)) * damping
        momentum_month_order = max(0.0, float(raw.get("momentum_month_order") or 0.0)) * damping
        momentum_stage_lu = max(0.0, float(raw.get("momentum_stage_lu") or 0.0)) * damping
        momentum_stage_blade = max(0.0, float(raw.get("momentum_stage_blade") or 0.0)) * damping
        momentum_stage_general = max(0.0, float(raw.get("momentum_stage_general") or 0.0)) * damping
        momentum_stage = (
            max(0.0, float(raw.get("momentum_stage") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_lu") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_blade") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_general") or 0.0))
        )
        momentum_stage = max(0.0, momentum_stage) * damping + momentum_stage_lu + momentum_stage_blade + momentum_stage_general
        momentum_structure = max(0.0, float(raw.get("momentum_structure") or 0.0)) * damping
        momentum_auxiliary = max(0.0, float(raw.get("momentum_auxiliary") or 0.0)) * damping
        momentum_base = max(0.0, float(raw.get("momentum") or 0.0)) - (
            max(0.0, float(raw.get("momentum_month_order") or 0.0))
            + max(0.0, float(raw.get("momentum_stage") or 0.0))
            + max(0.0, float(raw.get("momentum_structure") or 0.0))
            + max(0.0, float(raw.get("momentum_auxiliary") or 0.0))
        )
        momentum_other = max(0.0, momentum_base) * damping
        momentum = momentum_month_order + momentum_stage + momentum_structure + momentum_auxiliary + momentum_other
        hidden = max(0.0, float(raw.get("hidden") or 0.0)) * damping
        total_raw = manifest + root + momentum + hidden
        total = max(energy_min, min(energy_max, total_raw))
        if total_raw > 0.0 and total != total_raw:
            scale = total / total_raw
            manifest *= scale
            root *= scale
            momentum_month_order *= scale
            momentum_stage *= scale
            momentum_stage_lu *= scale
            momentum_stage_blade *= scale
            momentum_stage_general *= scale
            momentum_structure *= scale
            momentum_auxiliary *= scale
            momentum_other *= scale
            momentum *= scale
            hidden *= scale
        manifest_r = round(manifest, 2)
        root_r = round(root, 2)
        momentum_r = round(momentum, 2)
        hidden_r = round(hidden, 2)
        out[god] = {
            "manifest": manifest_r,
            "root": root_r,
            "momentum": momentum_r,
            "momentum_month_order": round(momentum_month_order, 2),
            "momentum_stage": round(momentum_stage, 2),
            "momentum_stage_lu": round(momentum_stage_lu, 2),
            "momentum_stage_blade": round(momentum_stage_blade, 2),
            "momentum_stage_general": round(momentum_stage_general, 2),
            "momentum_structure": round(momentum_structure, 2),
            "momentum_auxiliary": round(momentum_auxiliary, 2),
            "momentum_other": round(momentum_other, 2),
            "hidden": hidden_r,
            "total": round(manifest_r + root_r + momentum_r + hidden_r, 2),
        }
    return out
