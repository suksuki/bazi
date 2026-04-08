from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.api.contracts import AuditPhysicsWithLlmRequest
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState, FourPillars, StemBranchPair
from app.services import audit_service


def _metadata() -> BaziMetadata:
    return BaziMetadata(
        pillars=FourPillars(
            year=StemBranchPair(stem="甲", branch="子"),
            month=StemBranchPair(stem="丙", branch="寅"),
            day=StemBranchPair(stem="戊", branch="午"),
            hour=StemBranchPair(stem="庚", branch="申"),
        ),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        notes="test",
    )


class _FakePhysicsSkill:
    def consume(self, payload):
        return payload

    def produce(self, _consumed):
        return {
            "deity_scores": {"比肩": 0.8},
            "audit_log": {"trace": {"root_check": {"no_root": True}}},
            "meta": {"solar_term": "立春", "params": {"CF_FLOATING_DECAY": 0.2}},
        }


class _StrictJsonClient:
    async def chat(self, messages, temperature, max_tokens, stop):
        return (
            '{"diagnosis":"正常","alignment_score":88,"top_anomaly":"比肩偏高","causal_reasoning":"无根导致虚浮",'
            '"tuning_suggestions":["UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key=\'CF_FLOATING_DECAY\';"],'
            '"sql_patch":"UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key=\'CF_FLOATING_DECAY\';",'
            '"refresh_hint":"POST /api/admin/refresh-physics",'
            '"logic_proposal":{"param_key":"CF_FLOATING_DECAY","suggested_value":0.2,"sql_patch":"UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key=\'CF_FLOATING_DECAY\';"}}'
        )


class _RetryClient:
    def __init__(self):
        self.calls = 0

    async def chat(self, messages, temperature, max_tokens, stop):
        self.calls += 1
        if self.calls == 1:
            return "not-json"
        return (
            '{"diagnosis":"重试成功","alignment_score":66,"top_anomaly":"虚浮","causal_reasoning":"需要回退",'
            '"tuning_suggestions":[],"sql_patch":"UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key=\'CF_FLOATING_DECAY\';",'
            '"refresh_hint":"POST /api/admin/refresh-physics","logic_proposal":{"sql_patch":"UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key=\'CF_FLOATING_DECAY\';"}}'
        )


class _FallbackClient:
    async def chat(self, messages, temperature, max_tokens, stop):
        return "still-not-json"


def test_ensure_physics_tensor_uses_skill_when_missing():
    body = AuditPhysicsWithLlmRequest(metadata=_metadata(), physics_tensor=None, solar_term="立春")
    with patch.object(audit_service.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        tensor = audit_service.ensure_physics_tensor(body)
    assert tensor["meta"]["solar_term"] == "立春"


def test_audit_flow_parses_strict_json():
    body = AuditPhysicsWithLlmRequest(metadata=_metadata(), physics_tensor=_FakePhysicsSkill().produce({}), solar_term="立春")
    with patch.object(audit_service, "QwenClient", return_value=_StrictJsonClient()):
        payload = asyncio.run(audit_service.audit_physics_with_llm_flow(body))
    assert payload["structured_hit"] is True
    assert payload["repair_mode"] == "strict_json"
    assert payload["diagnosis"] == "正常"
    assert payload["sql_patch"].startswith("UPDATE physics_interaction_params")


def test_audit_flow_uses_retry_json():
    body = AuditPhysicsWithLlmRequest(metadata=_metadata(), physics_tensor=_FakePhysicsSkill().produce({}), solar_term="立春")
    with patch.object(audit_service, "QwenClient", return_value=_RetryClient()):
        payload = asyncio.run(audit_service.audit_physics_with_llm_flow(body))
    assert payload["structured_hit"] is True
    assert payload["repair_mode"] == "retry_json"
    assert payload["diagnosis"] == "重试成功"


def test_audit_flow_falls_back_and_normalizes_defaults():
    body = AuditPhysicsWithLlmRequest(metadata=_metadata(), physics_tensor=_FakePhysicsSkill().produce({}), solar_term="立春")
    with patch.object(audit_service, "QwenClient", return_value=_FallbackClient()):
        payload = asyncio.run(audit_service.audit_physics_with_llm_flow(body))
    assert payload["ok"] is True
    assert payload["sql_patch"].startswith("UPDATE physics_interaction_params")
    assert payload["logic_proposal"]["source_role"] == "LLM"
