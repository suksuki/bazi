"""逻辑检察院 diagnose：L1 管道与 logical_evidence 脱水。"""
from __future__ import annotations

from app.api.contracts import AuditDiagnoseRequest
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from app.services.audit_chamber_service import run_audit_diagnose


def _demo_pillars() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="午"),
        hour=StemBranchPair(stem="庚", branch="申"),
    )


def test_audit_diagnose_returns_pipeline_and_evidence() -> None:
    body = AuditDiagnoseRequest(pillars=_demo_pillars(), enabled_plugins=["classical.blind_school.v1"])
    out = run_audit_diagnose(body)
    assert out.get("ok") is True
    assert isinstance(out.get("logical_evidence"), list)
    pipe = out.get("l1_atomic_pipeline") or {}
    assert isinstance(pipe.get("steps"), list)
    assert "composite_field_impact" in out
    assert "decision_inbox_gate" in out


def test_audit_diagnose_report_and_confront() -> None:
    body = AuditDiagnoseRequest(
        pillars=_demo_pillars(),
        final_verdict_markdown="随便写点无关内容，不含三合关键词。",
        user_question="三合局在哪里？",
        generate_report=True,
        enabled_plugins=[],
    )
    out = run_audit_diagnose(body)
    assert "audit_report_markdown" in out
    assert out["audit_report_markdown"]
    assert "confront_answer_markdown" in out
