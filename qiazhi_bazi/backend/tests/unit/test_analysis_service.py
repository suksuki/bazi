from __future__ import annotations

import asyncio
import json
import os
from contextlib import contextmanager
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.api.contracts import AnalyzeSeedRequest, FinalVerdictRequest, TranslateRequest
from app.db.models import SessionConsensus
from app.schemas.bazi_metadata import ConflictMatrix, ConflictPoint, FourPillars, StemBranchPair
from app.services import analysis_service


class _FakeClient:
    async def chat(self, messages, temperature, max_tokens, stop):
        if isinstance(messages, list) and messages and isinstance(messages[0], dict) and "translation engine" in messages[0]["content"]:
            return json.dumps({"items": ["hello", "world"]}, ensure_ascii=False)
        return "观察到寅申冲，建议继续分析。"


class _FakePhysicsSkill:
    def consume(self, payload):
        return payload

    def produce(self, consumed):
        return {
            "audit_log": {
                "param_version_id": "v-test",
                "trace": {
                    "hard_route_logs": ["route-a"],
                    "root_check": {"no_root": True},
                },
            },
            "summary": {"self_score": 0.7},
        }


class _FakeVerdictSkill:
    async def generate(self, **kwargs):
        return {
            "version_id": "ver-1",
            "verdict_body": "适合推进",
            "change_log": ["调整一"],
            "logical_evidence": ["证据一"],
            "work_vector": {"work_expectation": 1.23, "llm_hint": "取财有道"},
            "audit_log": {"skill_id": "final_verdict_skill", "param_version_id": "p-1"},
        }


class _FakeExecResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeSession:
    def exec(self, _statement):
        return _FakeExecResult(
            [
                SessionConsensus(session_id=1, decision_key="root_factor", confirmed_value=1.2, reasoning="manual"),
            ]
        )


def test_translate_text_items_keeps_same_order():
    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()):
        payload = asyncio.run(
            analysis_service.translate_text_items(
                TranslateRequest(texts=["你好", "世界"], target_lang="EN")
            )
        )
    assert payload["items"] == ["hello", "world"]


def test_analyze_seed_flow_builds_audit_summary():
    pillars = FourPillars(
        year=StemBranchPair(stem="甲", branch="申"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="午"),
        hour=StemBranchPair(stem="庚", branch="子"),
    )
    fake_matrix = ConflictMatrix(points=[ConflictPoint(kind="clash", positions=["month_branch", "year_branch"], detail="寅申冲")])
    body = AnalyzeSeedRequest(date="1977-05-08", time="18:00", calendar="solar")

    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()), patch.object(
        analysis_service.Scanner, "scan", return_value=fake_matrix
    ), patch.object(analysis_service.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        payload = asyncio.run(
            analysis_service.analyze_seed_flow(
                body,
                lambda *_args: pillars,
                lambda *_args: {"dayun": "甲子", "liunian": "乙丑"},
                "2026-04-08T00:00:00Z",
            )
        )

    assert payload["timeline"]["dayun"] == "甲子"
    assert payload["audit_summary"][1]["role"] == "Core"
    assert payload["audit_summary"][2]["payload"]["param_version_id"] == "v-test"
    assert "寅申冲" in payload["llm_prompt"]


def test_load_consensus_history_and_generate_final_verdict():
    history = analysis_service.load_consensus_history(_FakeSession(), 1)
    assert history[0]["decision_key"] == "root_factor"
    assert history[0]["confirmed_value"] == 1.2

    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=_FakeVerdictSkill()):
        payload = asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata={"foo": "bar"},
                    physics_tensor={"score": 1},
                    selected_cards=[],
                    consensus_history=[],
                    previous_verdict="",
                    previous_logical_evidence=[],
                    lang="ZH",
                ),
                history,
            )
        )

    assert payload["ok"] is True
    assert payload["version_id"] == "ver-1"
    assert payload["verdict_body"] == "适合推进"
    assert payload["work_vector"]["llm_hint"] == "取财有道"
    assert payload["audit_log"]["skill_id"] == "final_verdict_skill"


def test_resolve_consensus_history_prefers_explicit_history():
    explicit = [{"decision_key": "k", "confirmed_value": 1.1, "reasoning": "manual"}]

    @contextmanager
    def fake_scope():
        yield _FakeSession()

    resolved = analysis_service.resolve_consensus_history(
        explicit_history=explicit,
        consultation_id=1,
        session_scope=fake_scope,
    )
    assert resolved == explicit


def test_resolve_consensus_history_falls_back_to_db():
    @contextmanager
    def fake_scope():
        yield _FakeSession()

    resolved = analysis_service.resolve_consensus_history(
        explicit_history=[],
        consultation_id=1,
        session_scope=fake_scope,
    )
    assert resolved[0]["decision_key"] == "root_factor"
