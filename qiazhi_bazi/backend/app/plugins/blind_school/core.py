"""Blind school plugin container: decoupled post-physics audit."""
from __future__ import annotations

from typing import Any, Dict

from app.plugins.blind_school.mangpai_engine import (
    compute_causal_dividend_index,
    merge_mangpai_chip_logs,
)
from app.plugins.blind_school.rules.rule_pierce import (
    attach_pierce_semantic_intensity,
    collect_pierce_semantics,
)
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors
from app.plugins.blind_school.blind_work_evaluator import (
    build_mangpai_interaction_hub_overlay,
    evaluate_blind_work,
)
from app.plugins.blind_school.op_work_logic import apply_work_intensity_and_meta_audit
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.skills.unlock_advice import build_unlock_advice

_DEFAULT_BLIND_FLAGS: Dict[str, bool] = {
    "enable_pierce_harm": True,
    "enable_tomb_vault": True,
    "enable_host_guest_bonus": True,
    "enable_standard_overlap": True,
}


def _normalize_feature_flags(raw: Any) -> Dict[str, bool]:
    out = dict(_DEFAULT_BLIND_FLAGS)
    if isinstance(raw, dict):
        for k in out:
            if k in raw:
                out[k] = bool(raw[k])
    return out


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
    plugin_version = "1.1.0"

    def run(
        self,
        *,
        physics_tensor: Dict[str, Any],
        metadata: Dict[str, Any],
        feature_flags: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        meta = (physics_tensor or {}).get("meta") if isinstance(physics_tensor, dict) else None
        merged: Dict[str, Any] = {}
        if isinstance(meta, dict) and isinstance(meta.get("blind_school_features"), dict):
            merged.update(meta.get("blind_school_features") or {})
        if feature_flags:
            merged.update(feature_flags)
        flags = _normalize_feature_flags(merged)

        work_vector = evaluate_blind_work(metadata, physics_tensor)
        work_vector["house_sovereignty_map"] = _build_house_sovereignty_map(metadata)
        work_vector["spatial_audit"] = audit_spatial_sovereignty(work_vector=work_vector)
        work_vector["encyclopedia_audit"] = audit_host_guest_vectors(work_vector=work_vector)
        work_vector["unlock_advice"] = build_unlock_advice(
            spatial_audit=work_vector.get("spatial_audit", {}) or {},
            work_vector=work_vector,
        )
        _bind_rule_source(work_vector)

        wv_list = list(work_vector.get("work_vectors") or [])
        if flags.get("enable_pierce_harm", True):
            attach_pierce_semantic_intensity(wv_list)
        if flags.get("enable_host_guest_bonus", True):
            dividend, _ = compute_causal_dividend_index(physics_tensor)
            work_vector["causal_dividend_index"] = dividend
        else:
            work_vector["causal_dividend_index"] = 0.0

        hub_overlay = build_mangpai_interaction_hub_overlay(work_vector)
        if hub_overlay:
            work_vector["interaction_hub_overlay_mangpai"] = hub_overlay

        chip_logs = merge_mangpai_chip_logs(
            work_vectors=wv_list,
            feature_flags=flags,
            metadata=metadata,
            physics_tensor=physics_tensor,
        )
        work_vector["mangpai_chip_logs"] = chip_logs
        work_vector["mangpai_pierce_semantics"] = (
            collect_pierce_semantics(wv_list) if flags.get("enable_pierce_harm", True) else []
        )
        work_vector["blind_school_features"] = flags

        work_vector["plugin_trace"] = {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "rule_source": "BLIND_SCHOOL_SYSTEM.md",
        }
        if isinstance(physics_tensor, dict):
            apply_work_intensity_and_meta_audit(work_vector=work_vector, physics_tensor=physics_tensor)
        return work_vector


def run_blind_school_plugin(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
    feature_flags: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return BlindSchoolPlugin().run(
        physics_tensor=physics_tensor,
        metadata=metadata,
        feature_flags=feature_flags,
    )

