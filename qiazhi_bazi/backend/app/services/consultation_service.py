"""Consultation service layer for persistence-heavy decision workflows."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.api.contracts import (
    ConfirmStructureRequest,
    ConsultationCreate,
    DecisionRollbackRequest,
    DecisionStepCreate,
)
from app.db.models import Consultation, DecisionStep, SessionConsensus


def create_consultation_record(session: Any, body: ConsultationCreate) -> Dict[str, int]:
    consultation = Consultation(subject_ref=body.subject_ref, input_meta=body.input_meta)
    session.add(consultation)
    session.flush()
    session.refresh(consultation)
    return {"id": consultation.id}


def confirm_structure_for_consultation(session: Any, body: ConfirmStructureRequest) -> Dict[str, Any]:
    consultation = session.get(Consultation, body.consultation_id)
    if not consultation:
        raise LookupError("consultation not found")

    meta = dict(consultation.input_meta or {})
    meta["confirmed_structure"] = {
        "name": body.structure_name,
        "confidence": body.confidence,
        "evidence": body.evidence,
        "confirmed_at": datetime.utcnow().isoformat(),
    }
    consultation.input_meta = meta
    session.add(consultation)
    return {"ok": True, "confirmed_structure": meta["confirmed_structure"]}


def create_decision_step_record(session: Any, body: DecisionStepCreate) -> Dict[str, int]:
    consultation = session.get(Consultation, body.consultation_id)
    confirmed_structure = None
    if consultation:
        meta = consultation.input_meta or {}
        confirmed_structure = meta.get("confirmed_structure")

    step = DecisionStep(
        consultation_id=body.consultation_id,
        step_type=body.step_type,
        raw_data={
            **(body.raw_data or {}),
            **({} if confirmed_structure is None else {"confirmed_structure": confirmed_structure}),
        },
        human_choice=body.human_choice,
    )
    session.add(step)
    session.flush()
    session.refresh(step)
    _persist_session_consensus(session, body)
    return {"id": step.id}


def rollback_decision_step_record(session: Any, body: DecisionRollbackRequest) -> Dict[str, int]:
    target = session.get(DecisionStep, body.target_step_id)
    if not target:
        raise LookupError("target decision step not found")

    event = DecisionStep(
        consultation_id=target.consultation_id,
        step_type="rollback_event",
        raw_data={
            "target_step_id": target.id,
            "target_step_type": target.step_type,
        },
        human_choice={
            "action": "rollback",
            "reason": body.reason or "manual rollback",
        },
    )
    session.add(event)
    session.flush()
    session.refresh(event)
    return {
        "id": event.id,
        "target_step_id": target.id,
        "consultation_id": target.consultation_id,
    }


def list_history_items(session: Any, now_iso_value: str) -> Dict[str, List[Dict[str, Any]]]:
    rows = session.query(DecisionStep).order_by(DecisionStep.id.desc()).limit(50).all()
    items = [
        {
            "id": f"db-{row.id}",
            "title": row.step_type,
            "answer": (row.human_choice or {}).get("action") if isinstance(row.human_choice, dict) else None,
            "createdAt": row.created_at.isoformat() if getattr(row, "created_at", None) else now_iso_value,
        }
        for row in rows
    ]
    return {"items": items}


def _persist_session_consensus(session: Any, body: DecisionStepCreate) -> None:
    choice = body.human_choice or {}
    action = str(choice.get("action") or "")
    selected_proposals = choice.get("selected_proposals") or []
    if action != "execute" or not isinstance(selected_proposals, list):
        return

    for proposal in selected_proposals:
        if not isinstance(proposal, dict):
            continue
        key = str(proposal.get("param_key") or "").strip()
        if not key:
            continue
        value_raw = proposal.get("suggested_value")
        try:
            value = float(value_raw) if value_raw is not None else None
        except Exception:
            value = None
        reasoning = str(proposal.get("reason") or proposal.get("expected_impact") or "")
        session.add(
            SessionConsensus(
                session_id=body.consultation_id,
                decision_key=key,
                confirmed_value=value,
                reasoning=reasoning,
            )
        )
