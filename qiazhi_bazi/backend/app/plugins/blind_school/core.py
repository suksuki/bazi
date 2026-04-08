"""Blind school plugin container: decoupled post-physics audit."""
from __future__ import annotations

from typing import Any, Dict

from app.skills.blind_school_encyclopedia import audit_host_guest_vectors
from app.skills.blind_work_evaluator import evaluate_blind_work
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.skills.unlock_advice import build_unlock_advice


def _build_house_sovereignty_map(metadata: Dict[str, Any]) -> Dict[str, str]:
    pillars = ((metadata or {}).get("pillars") or {}) if isinstance(metadata, dict) else {}
    out: Dict[str, str] = {}
    if isinstance(pillars, dict):
        if "year" in pillars:
            out["year"] = "EXTERNAL"
        if "month" in pillars:
            out["month"] = "EXTERNAL"
        if "day" in pillars:
            out["day"] = "INTERNAL"
        if "hour" in pillars:
            out["hour"] = "INTERNAL"
    return out


def _bind_rule_source(work_vector: Dict[str, Any]) -> None:
    vectors = list((work_vector or {}).get("work_vectors") or [])
    for item in vectors:
        tag = str(item.get("spatial_tag") or item.get("guest_host_tag") or "")
        if tag in {"[GAIN_PATH]", "GAIN_VECTOR"}:
            item["rule_source"] = "BLIND_SCHOOL_SYSTEM.md#1.2"
        elif tag in {"[LOSS_PATH]", "LOSS_VECTOR"}:
            item["rule_source"] = "BLIND_SCHOOL_SYSTEM.md#4.2"
        else:
            item["rule_source"] = "BLIND_SCHOOL_SYSTEM.md#3"


class BlindSchoolPlugin:
    plugin_id = "blind_school_plugin"
    plugin_version = "1.0.0"

    def run(self, *, physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        work_vector = evaluate_blind_work(metadata, physics_tensor)
        work_vector["house_sovereignty_map"] = _build_house_sovereignty_map(metadata)
        work_vector["spatial_audit"] = audit_spatial_sovereignty(work_vector=work_vector)
        work_vector["encyclopedia_audit"] = audit_host_guest_vectors(work_vector=work_vector)
        work_vector["unlock_advice"] = build_unlock_advice(
            spatial_audit=work_vector.get("spatial_audit", {}) or {},
            work_vector=work_vector,
        )
        _bind_rule_source(work_vector)
        work_vector["plugin_trace"] = {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "rule_source": "BLIND_SCHOOL_SYSTEM.md",
        }
        return work_vector


def run_blind_school_plugin(*, physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    return BlindSchoolPlugin().run(physics_tensor=physics_tensor, metadata=metadata)

