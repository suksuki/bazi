"""逻辑检察院 API。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.contracts import AuditDiagnoseRequest
from app.services.audit_chamber_service import run_audit_diagnose

router = APIRouter(prefix="/v1/audit", tags=["audit-chamber"])


@router.post("/diagnose", response_model=dict)
def audit_diagnose(body: AuditDiagnoseRequest) -> dict:
    """
    接收四柱 → PhysicsInferenceSkill + evaluate_interactions（L1 原子流）→
    返回 `l1_atomic_pipeline`、`composite_field_impact`（含 sanhe_clusters）、
    `logical_evidence`、Inbox 门控块、与终判文本的启发式差异。
    """
    return run_audit_diagnose(body)
