from __future__ import annotations

from contextlib import contextmanager

from app.db.models import Consultation
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState, FourPillars, StemBranchPair
from app.services.orchestrator_service import OrchestratorService


class _FakeDbSession:
    def __init__(self, consultation: Consultation):
        self.consultation = consultation
        self.added = []

    def get(self, model, obj_id):
        if model is Consultation and int(obj_id) == int(self.consultation.id or 0):
            return self.consultation
        return None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        return None


def _pillars() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="午"),
        hour=StemBranchPair(stem="庚", branch="申"),
    )


def test_resume_calculation_updates_interrupt_and_feedback_history(monkeypatch):
    consultation = Consultation(
        id=101,
        subject_ref="resume-ut",
        input_meta={
            "persistence_layer": {
                "interrupt_request": {"state": "pending", "reason_code": "L1_LOGIC_CONFLICT"},
                "brain_hub": {},
            }
        },
    )
    fake_db = _FakeDbSession(consultation)

    @contextmanager
    def _fake_scope():
        yield fake_db

    monkeypatch.setattr("app.db.session.session_scope", _fake_scope)

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.PROBE_WAITING,
    )

    def _fake_loop(**kwargs):
        return {
            "metadata": kwargs["metadata_obj"],
            "physics_tensor": {"meta": {}},
            "plugin_outputs": {},
            "semantic_label_bundle_v1": {},
            "verified_fact_lines": [],
            "verdict_skeleton": "",
            "requires_narrative_refresh": False,
            "pre_injection_deity_display": {},
            "active_probing": {},
            "interrupt_request": {"state": "resumed"},
        }

    monkeypatch.setattr(OrchestratorService, "run_internal_loop", staticmethod(_fake_loop))

    out = OrchestratorService.resume_calculation(
        session_id=101,
        user_feedback={"answer": "确认冲突", "user_intention_id": "INTENT_FIX"},
        metadata=md.model_dump(mode="python"),
        enabled_plugins=[],
        blind_school_features={},
        physics_config={},
    )

    assert str(out.get("resume_ack_token") or "").startswith("resume:")
    assert out.get("is_idempotent_success") is not True
    persisted = consultation.input_meta.get("persistence_layer") or {}
    assert not persisted.get("interrupt_request") or persisted.get("interrupt_request") == {}
    history = persisted.get("resume_feedback_history") or []
    assert isinstance(history, list) and len(history) >= 1


def test_resume_calculation_idempotent_when_interrupt_already_resumed(monkeypatch):
    """重复 Resume：interrupt 已为终态时不应再写 ResumePulseHistory，且返回 idempotent。"""
    consultation = Consultation(
        id=202,
        subject_ref="resume-idem-ut",
        input_meta={
            "persistence_layer": {
                "interrupt_request": {
                    "state": "resumed",
                    "reason_code": "L1_LOGIC_CONFLICT",
                    "resume_ack_token": "resume:existing-token",
                },
                "brain_hub": {},
            }
        },
    )
    fake_db = _FakeDbSession(consultation)

    @contextmanager
    def _fake_scope():
        yield fake_db

    monkeypatch.setattr("app.db.session.session_scope", _fake_scope)

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.PROBE_WAITING,
    )

    def _fake_loop(**kwargs):
        return {
            "metadata": kwargs["metadata_obj"],
            "physics_tensor": {"meta": {}},
            "plugin_outputs": {},
            "semantic_label_bundle_v1": {},
            "verified_fact_lines": [],
            "verdict_skeleton": "",
            "requires_narrative_refresh": False,
            "pre_injection_deity_display": {},
            "active_probing": {},
            "interrupt_request": {"state": "resumed"},
        }

    monkeypatch.setattr(OrchestratorService, "run_internal_loop", staticmethod(_fake_loop))

    out = OrchestratorService.resume_calculation(
        session_id=202,
        user_feedback={"answer": "再次确认"},
        metadata=md.model_dump(mode="python"),
        enabled_plugins=[],
        blind_school_features={},
        physics_config={},
    )

    assert out.get("idempotent") is True
    assert out.get("is_idempotent_success") is True
    assert out.get("resume_ack_token") == "resume:existing-token"
    assert not any(type(x).__name__ == "ResumePulseHistory" for x in fake_db.added)


def test_resume_calculation_idempotent_empty_interrupt_probe_waiting_stale(monkeypatch):
    """元数据仍为 probe_waiting 但 persistence 已无中断：应幂等 Resume 并归一化 flow_state，避免 409。"""
    consultation = Consultation(
        id=404,
        subject_ref="resume-probe-stale-ut",
        input_meta={
            "flow_state": "probe_waiting",
            "persistence_layer": {"interrupt_request": {}, "brain_hub": {}},
        },
    )
    fake_db = _FakeDbSession(consultation)

    @contextmanager
    def _fake_scope():
        yield fake_db

    monkeypatch.setattr("app.db.session.session_scope", _fake_scope)

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.PROBE_WAITING,
    )

    def _fake_loop(**kwargs):
        meta = kwargs["metadata_obj"]
        assert meta.flow_state == FlowState.UNKNOWN
        return {
            "metadata": meta,
            "physics_tensor": {"meta": {}},
            "plugin_outputs": {},
            "semantic_label_bundle_v1": {},
            "verified_fact_lines": [],
            "verdict_skeleton": "",
            "requires_narrative_refresh": False,
            "pre_injection_deity_display": {},
            "active_probing": {},
            "interrupt_request": {},
        }

    monkeypatch.setattr(OrchestratorService, "run_internal_loop", staticmethod(_fake_loop))

    out = OrchestratorService.resume_calculation(
        session_id=404,
        user_feedback={"answer": "确认冲突"},
        metadata=md.model_dump(mode="python"),
        enabled_plugins=[],
        blind_school_features={},
        physics_config={},
    )

    assert out.get("idempotent") is True
    assert str(out.get("resume_ack_token") or "").startswith("resume:idempotent-probe-stale-")


def test_resume_calculation_idempotent_when_interrupt_expired(monkeypatch):
    consultation = Consultation(
        id=303,
        subject_ref="resume-expired-ut",
        input_meta={
            "persistence_layer": {
                "interrupt_request": {
                    "state": "expired",
                    "reason_code": "M3_L1_LOGIC_CONFLICT_PENDING",
                    "resume_ack_token": "resume:expired-token",
                },
                "brain_hub": {},
            }
        },
    )
    fake_db = _FakeDbSession(consultation)

    @contextmanager
    def _fake_scope():
        yield fake_db

    monkeypatch.setattr("app.db.session.session_scope", _fake_scope)

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.PROBE_WAITING,
    )

    def _fake_loop(**kwargs):
        return {
            "metadata": kwargs["metadata_obj"],
            "physics_tensor": {"meta": {}},
            "plugin_outputs": {},
            "semantic_label_bundle_v1": {},
            "verified_fact_lines": [],
            "verdict_skeleton": "",
            "requires_narrative_refresh": False,
            "pre_injection_deity_display": {},
            "active_probing": {},
            "interrupt_request": {},
        }

    monkeypatch.setattr(OrchestratorService, "run_internal_loop", staticmethod(_fake_loop))

    out = OrchestratorService.resume_calculation(
        session_id=303,
        user_feedback={"answer": "继续"},
        metadata=md.model_dump(mode="python"),
        enabled_plugins=[],
        blind_school_features={},
        physics_config={},
    )

    assert out.get("idempotent") is True
    assert out.get("is_idempotent_success") is True
    assert out.get("resume_ack_token") == "resume:expired-token"
