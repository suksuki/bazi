from __future__ import annotations

from datetime import datetime
import os

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.api.contracts import (
    ConfirmStructureRequest,
    ConsultationCreate,
    DecisionRollbackRequest,
    DecisionStepCreate,
)
from app.db.models import Consultation, DecisionStep, SessionConsensus
from app.services.consultation_service import (
    confirm_structure_for_consultation,
    create_consultation_record,
    create_decision_step_record,
    list_history_items,
    rollback_decision_step_record,
)


class _FakeQuery:
    def __init__(self, steps):
        self._steps = steps

    def order_by(self, _field):
        self._steps = sorted(self._steps, key=lambda item: item.id or 0, reverse=True)
        return self

    def limit(self, size):
        self._steps = self._steps[:size]
        return self

    def all(self):
        return list(self._steps)


class _FakeSession:
    def __init__(self):
        self.consultations = {}
        self.steps = {}
        self.consensus = {}
        self._next_consultation_id = 1
        self._next_step_id = 1
        self._next_consensus_id = 1

    def add(self, obj):
        if isinstance(obj, Consultation):
            if obj.id is None:
                obj.id = self._next_consultation_id
                self._next_consultation_id += 1
            self.consultations[obj.id] = obj
            return
        if isinstance(obj, DecisionStep):
            if obj.id is None:
                obj.id = self._next_step_id
                self._next_step_id += 1
            self.steps[obj.id] = obj
            return
        if isinstance(obj, SessionConsensus):
            if obj.id is None:
                obj.id = self._next_consensus_id
                self._next_consensus_id += 1
            self.consensus[obj.id] = obj
            return
        raise TypeError(f"unsupported object: {type(obj)!r}")

    def flush(self):
        return None

    def refresh(self, _obj):
        return None

    def get(self, model, obj_id):
        if model is Consultation:
            return self.consultations.get(obj_id)
        if model is DecisionStep:
            return self.steps.get(obj_id)
        return None

    def query(self, model):
        if model is not DecisionStep:
            raise TypeError(f"unsupported model: {model!r}")
        return _FakeQuery(self.steps.values())


def test_create_step_carries_confirmed_structure_and_persists_consensus():
    session = _FakeSession()
    consultation = create_consultation_record(
        session,
        ConsultationCreate(
            subject_ref="svc-1",
            input_meta={"confirmed_structure": {"name": "伤官配印", "confidence": 0.9}},
        ),
    )

    result = create_decision_step_record(
        session,
        DecisionStepCreate(
            consultation_id=consultation["id"],
            step_type="physics-adjustment",
            raw_data={"stage": "precheck"},
            human_choice={
                "action": "execute",
                "selected_proposals": [
                    {"param_key": "root_factor", "suggested_value": "1.25", "reason": "unit test"}
                ],
            },
        ),
    )

    saved_step = session.steps[result["id"]]
    assert saved_step.raw_data["confirmed_structure"]["name"] == "伤官配印"
    assert len(session.consensus) == 1
    consensus = next(iter(session.consensus.values()))
    assert consensus.decision_key == "root_factor"
    assert consensus.confirmed_value == 1.25


def test_confirm_and_rollback_raise_for_missing_targets():
    session = _FakeSession()

    try:
        confirm_structure_for_consultation(
            session,
            ConfirmStructureRequest(
                consultation_id=999,
                structure_name="从财格",
                confidence=0.5,
                evidence="missing",
            ),
        )
    except LookupError as exc:
        assert str(exc) == "consultation not found"
    else:
        raise AssertionError("expected LookupError")

    try:
        rollback_decision_step_record(session, DecisionRollbackRequest(target_step_id=999, reason="missing"))
    except LookupError as exc:
        assert str(exc) == "target decision step not found"
    else:
        raise AssertionError("expected LookupError")


def test_list_history_items_formats_latest_first():
    session = _FakeSession()
    create_consultation_record(session, ConsultationCreate(subject_ref="svc-history", input_meta={}))
    older = DecisionStep(
        id=1,
        consultation_id=1,
        step_type="older",
        raw_data={},
        human_choice={"action": "skip"},
        created_at=datetime(2024, 1, 1, 8, 0, 0),
    )
    newer = DecisionStep(
        id=2,
        consultation_id=1,
        step_type="newer",
        raw_data={},
        human_choice={"action": "execute"},
        created_at=datetime(2024, 1, 1, 9, 0, 0),
    )
    session.add(older)
    session.add(newer)

    payload = list_history_items(session, "fallback-time")

    assert [item["title"] for item in payload["items"]] == ["newer", "older"]
    assert payload["items"][0]["answer"] == "execute"
    assert payload["items"][0]["createdAt"] == "2024-01-01T09:00:00"
