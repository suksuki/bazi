"""Spatial sovereignty audit for blind-school reasoning."""
from __future__ import annotations

from typing import Any, Dict, List

from app.skills.base import AuditLog, BaseSkill


def audit_spatial_sovereignty(*, work_vector: Dict[str, Any]) -> Dict[str, Any]:
    vectors: List[Dict[str, Any]] = list((work_vector or {}).get("work_vectors") or [])
    gain_paths = 0
    loss_paths = 0
    blocking_elements: List[str] = []
    for item in vectors:
        relation = str(item.get("type") or "")
        direction = str(item.get("direction") or "")
        source_space = "INTERNAL" if direction == "Host->Guest" else "EXTERNAL"
        target_space = "EXTERNAL" if source_space == "INTERNAL" else "INTERNAL"
        item["source_space"] = source_space
        item["target_space"] = target_space
        if source_space == "INTERNAL" and target_space == "EXTERNAL" and relation in {"合", "冲", "克", "刑"}:
            item["spatial_tag"] = "[GAIN_PATH]"
            gain_paths += 1
        elif source_space == "EXTERNAL" and target_space == "INTERNAL" and relation in {"穿", "害", "冲"}:
            item["spatial_tag"] = "[LOSS_PATH]"
            loss_paths += 1
            target = str(item.get("target_deity") or "")
            detail = str(item.get("detail") or "")
            if target:
                blocking_elements.append(target)
            if detail:
                blocking_elements.append(detail[:8])
        else:
            item["spatial_tag"] = "[NEUTRAL_PATH]"

    host_abs = float((work_vector or {}).get("host_abs", 0.0) or 0.0)
    work_net = float((work_vector or {}).get("work_expectation", 0.0) or 0.0)
    lock_warning = ""
    is_exit_locked = host_abs > 15 and work_net <= 0 and loss_paths > 0
    if is_exit_locked:
        lock_warning = "外部环境锁死，能量无法外溢做功。"

    return {
        "gain_path_count": gain_paths,
        "loss_path_count": loss_paths,
        "is_exit_locked": is_exit_locked,
        "blocking_elements": list(dict.fromkeys([x for x in blocking_elements if x])),
        "lock_warning": lock_warning,
        "internal_scope": ["日柱", "时柱"],
        "external_scope": ["年柱", "月柱"],
    }


class SpatialSovereigntySkill(BaseSkill):
    skill_id = "spatial_sovereignty_skill"
    skill_version = "1.0.0"
    rule_version = "spatial_sovereignty.v1"

    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"work_vector": context.get("work_vector") or {}}

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        return audit_spatial_sovereignty(work_vector=consumed.get("work_vector") or {})

    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        return AuditLog(
            skill_id=self.skill_id,
            skill_version=self.skill_version,
            rule_version=self.rule_version,
            param_version_id="runtime",
            formula_refs=["spatial_sovereignty.path_tagging"],
            trace={
                "gain_path_count": produced.get("gain_path_count", 0),
                "loss_path_count": produced.get("loss_path_count", 0),
                "has_lock_warning": bool(produced.get("lock_warning")),
            },
        )
