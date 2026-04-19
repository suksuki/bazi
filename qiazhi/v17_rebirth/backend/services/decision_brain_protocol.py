from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


PLAN_STATUSES = ("DRAFT", "AWAIT_REVIEW", "APPROVED", "REJECTED", "COMMITTED", "FAILED")
PLAN_CREATORS = ("system", "llm", "user")
PLAN_ROUTES = ("system", "llm", "user")
PLAN_SIGNALS = ("PLAN_SUBMIT", "PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _normalize_list(value: Any) -> List[str]:
    return [str(item).strip() for item in (value or []) if str(item).strip()]


def _unique(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


@dataclass
class DecisionRoutingClaim:
    claim_id: str
    severity: str
    confidence: float
    routing: str
    routing_reason: str
    rationale: str
    signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "severity": self.severity,
            "confidence": self.confidence,
            "routing": self.routing,
            "routing_reason": self.routing_reason,
            "rationale": self.rationale,
            "signals": dict(self.signals),
        }


@dataclass
class DecisionBatch:
    batch_id: str
    bucket: str
    target_god: str
    source_anchor: str
    source_families: List[str]
    decision_ids: List[str]
    decision_count: int
    net_impact_ratio: float
    max_priority: float
    prompt_line: str = ""
    labels: List[str] = field(default_factory=list)
    routing_hint: str | None = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DecisionBatch":
        return cls(
            batch_id=_normalize(payload.get("batch_id")),
            bucket=_normalize(payload.get("bucket")) or "manual",
            target_god=_normalize(payload.get("target_god")),
            source_anchor=_normalize(payload.get("source_anchor")),
            source_families=_unique(_normalize_list(payload.get("source_families"))),
            decision_ids=_unique(_normalize_list(payload.get("decision_ids"))),
            decision_count=int(payload.get("decision_count") or 0),
            net_impact_ratio=float(payload.get("net_impact_ratio") or 0.0),
            max_priority=float(payload.get("max_priority") or 0.0),
            prompt_line=_normalize(payload.get("prompt_line")),
            labels=_unique(_normalize_list(payload.get("labels"))),
            routing_hint=_normalize(payload.get("routing_hint")) or None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "bucket": self.bucket,
            "target_god": self.target_god,
            "source_anchor": self.source_anchor,
            "source_families": self.source_families,
            "decision_ids": self.decision_ids,
            "decision_count": self.decision_count,
            "net_impact_ratio": self.net_impact_ratio,
            "max_priority": self.max_priority,
            "prompt_line": self.prompt_line,
            "labels": self.labels,
            "routing_hint": self.routing_hint,
        }


@dataclass
class DecisionBrainPlan:
    plan_id: str
    session_id: str
    anchor: str
    batch_ids: List[str]
    routing: str
    status: str
    creator: str
    impact_summary: Dict[str, Any] = field(default_factory=dict)
    residual_estimate: float = 0.0
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    meta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], *, session_id: str = "") -> "DecisionBrainPlan":
        normalized_session = _normalize(session_id or payload.get("session_id"))
        route = _normalize(payload.get("routing")) or _normalize(payload.get("route")) or "system"
        if route not in PLAN_ROUTES:
            route = "system"
        status = _normalize(payload.get("status")) or "DRAFT"
        if status not in PLAN_STATUSES:
            status = "DRAFT"
        creator = _normalize(payload.get("creator")) or "system"
        if creator not in PLAN_CREATORS:
            creator = "system"
        batch_ids = _unique(_normalize_list(payload.get("batch_ids")))
        return cls(
            plan_id=_normalize(payload.get("plan_id")),
            session_id=normalized_session,
            anchor=_normalize(payload.get("anchor")),
            batch_ids=batch_ids,
            routing=route,
            status=status,
            creator=creator,
            impact_summary=dict(payload.get("impact_summary") or {}),
            residual_estimate=float(payload.get("residual_estimate") or 0.0),
            created_at=_normalize(payload.get("created_at")) or _now_iso(),
            updated_at=_normalize(payload.get("updated_at")) or _now_iso(),
            meta=dict(payload.get("meta") or {}),
        )

    def transition(self, status: str) -> "DecisionBrainPlan":
        next_status = _normalize(status) or "DRAFT"
        if next_status in PLAN_STATUSES:
            self.status = next_status
            self.updated_at = _now_iso()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "anchor": self.anchor,
            "batch_ids": self.batch_ids,
            "routing": self.routing,
            "status": self.status,
            "creator": self.creator,
            "impact_summary": self.impact_summary,
            "residual_estimate": self.residual_estimate,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "meta": self.meta,
        }


def build_plan_claim(*, routing: str, routing_reason: str, routing_features: Dict[str, Any]) -> Dict[str, Any]:
    """Build a compact claim object to drive arbitration explainability."""
    conflict_pairs = int(routing_features.get("conflict_pairs") or 0)
    duplicate_events = int(routing_features.get("duplicate_events") or 0)
    decision_count = int(routing_features.get("decision_count") or 0)
    total_abs_ratio = float(routing_features.get("total_abs_ratio") or 0.0)
    max_abs_ratio = float(routing_features.get("max_abs_ratio") or 0.0)

    risk = abs(max_abs_ratio) + max(0.0, total_abs_ratio)
    risk += min(conflict_pairs, 3) * 0.28
    risk += min(duplicate_events, 3) * 0.18
    if risk > 1.0:
        risk = 1.0

    if routing == "user":
        severity = "P1"
        confidence = round(0.86 + max(0.0, min(0.13, risk * 0.2)), 3)
    elif routing == "llm":
        severity = "P2"
        confidence = round(0.68 + max(0.0, min(0.26, (1.0 - risk) * 0.35)), 3)
    else:
        severity = "P3" if routing == "system" and (risk < 0.45 or decision_count <= 8) else "P2"
        confidence = round(0.74 + max(0.0, min(0.22, (1.0 - risk) * 0.28)), 3)

    return DecisionRoutingClaim(
        claim_id=f"{routing}:{decision_count}:{decision_count and int(risk * 100)}",
        severity=severity,
        confidence=confidence,
        routing=routing,
        routing_reason=routing_reason,
        rationale=f"按 routing={routing} 分流，综合 risk={risk:.3f}。",
        signals={
            "conflict_pairs": conflict_pairs,
            "duplicate_events": duplicate_events,
            "decision_count": decision_count,
            "max_abs_ratio": round(max_abs_ratio, 4),
            "total_abs_ratio": round(total_abs_ratio, 4),
        },
    ).to_dict()


def normalize_plan_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    signal = _normalize(payload.get("signal")).upper()
    if signal not in PLAN_SIGNALS:
        signal = "PLAN_SUBMIT"

    action = _normalize(payload.get("action")).strip()
    decision_ids = _normalize_list(payload.get("decision_ids"))
    batch_ids = _normalize_list(payload.get("batch_ids"))
    if not batch_ids and decision_ids:
        batch_ids = decision_ids

    return {
        "signal": signal,
        "action": action,
        "plan_id": _normalize(payload.get("plan_id")) or f"plan_{int(datetime.now(timezone.utc).timestamp()*1000)}",
        "anchor": _normalize(payload.get("anchor")),
        "batch_ids": _unique(batch_ids),
        "routing": _normalize(payload.get("routing")) or "system",
        "creator": (_normalize(payload.get("creator")).lower() or "user") if signal != "PLAN_APPROVE" else "user",
        "status": "APPROVED" if signal == "PLAN_APPROVE" else "DRAFT",
        "source_event_signal": signal,
        "residual_estimate": float(payload.get("residual_estimate") or 0.0),
        "meta": dict(payload.get("meta") or {}),
    }
