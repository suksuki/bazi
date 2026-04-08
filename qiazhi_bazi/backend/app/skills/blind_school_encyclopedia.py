"""Blind school encyclopedia skill: host/guest and anti-subjugation audits."""
from __future__ import annotations

from typing import Any, Dict, List

from app.skills.base import AuditLog, BaseSkill


def build_blind_school_digest() -> List[str]:
    return [
        "空间主权=Year/Month->GUEST, Day/Hour->HOST",
        "体用主线=BODY(日主印比禄) 作用 USE(财官) 为得功",
        "做功公式=Net_Effect=(Abs*eta*Climate)-Backfire_Risk",
        "高能闭锁=Self_Abs高但Work_Vectors空 -> 身强无依/闭门造车",
    ]


def audit_host_guest_vectors(*, work_vector: Dict[str, Any]) -> Dict[str, Any]:
    vectors = list((work_vector or {}).get("work_vectors") or [])
    gain_vector_count = 0
    anti_subjugation = False

    for item in vectors:
        direction = str(item.get("direction") or "")
        relation = str(item.get("type") or "")
        host_abs = float(item.get("host_abs", 0.0) or 0.0)
        guest_abs = float(item.get("guest_abs", 0.0) or 0.0)

        # Current direction semantics in this repo:
        # Host->Guest means BODY side initiates to USE side.
        if direction == "Host->Guest" and relation in {"合", "冲", "克"}:
            gain_vector_count += 1
            item["guest_host_tag"] = "GAIN_VECTOR"
        elif direction == "Guest->Host" and relation in {"穿", "害", "冲"}:
            item["guest_host_tag"] = "LOSS_VECTOR"
        else:
            item["guest_host_tag"] = "NEUTRAL_VECTOR"

        if host_abs > 0 and guest_abs > host_abs * 3.0:
            anti_subjugation = True
            item["anti_subjugation"] = True
        else:
            item["anti_subjugation"] = False

    return {
        "gain_vector_count": gain_vector_count,
        "anti_subjugation": anti_subjugation,
        "host_scope": ["日柱", "时柱"],
        "guest_scope": ["年柱", "月柱"],
    }


class BlindSchoolEncyclopediaSkill(BaseSkill):
    skill_id = "blind_school_encyclopedia_skill"
    skill_version = "1.0.0"
    rule_version = "blind_school_encyclopedia.v1"

    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"work_vector": context.get("work_vector") or {}}

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "digest": build_blind_school_digest(),
            "audit": audit_host_guest_vectors(work_vector=consumed.get("work_vector") or {}),
        }

    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        a = (produced or {}).get("audit") or {}
        return AuditLog(
            skill_id=self.skill_id,
            skill_version=self.skill_version,
            rule_version=self.rule_version,
            param_version_id="runtime",
            formula_refs=["blind_school_encyclopedia.host_guest_audit"],
            trace={
                "gain_vector_count": int(a.get("gain_vector_count", 0) or 0),
                "anti_subjugation": bool(a.get("anti_subjugation", False)),
            },
        )
