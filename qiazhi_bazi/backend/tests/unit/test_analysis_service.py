from __future__ import annotations

import asyncio

import json
import os
from contextlib import contextmanager
from unittest.mock import patch
from unittest.mock import AsyncMock

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.api.contracts import AnalyzeClashRequest, AnalyzeSeedRequest, FinalVerdictRequest, RegenerationContext, TranslateRequest
from app.db.models import SessionConsensus
from app.schemas.bazi_metadata import ConflictMatrix, ConflictPoint, FourPillars, StemBranchPair
from app.skills import physics_engine as physics_engine_module
from app.services import analysis_service
from app.services.bazi_engine import get_bazi


class _FakeClient:
    async def chat(self, messages, temperature, max_tokens, stop):
        text, _ = await self.chat_with_telemetry(messages, temperature, max_tokens, stop)
        return text

    async def chat_with_telemetry(self, messages, temperature, max_tokens, stop):
        if isinstance(messages, list) and messages and isinstance(messages[0], dict) and "translation engine" in messages[0]["content"]:
            raw = json.dumps({"items": ["hello", "world"]}, ensure_ascii=False)
            return raw, {"elapsed_ms": 1.0, "approx_tokens": 1.0, "usage": {}}
        return "观察到寅申冲，建议继续分析。", {"elapsed_ms": 2.0, "approx_tokens": 3.0, "usage": {}}


class _FakePhysicsSkill:
    def consume(self, payload):
        return payload

    def get_interaction_params(self):
        from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

        return dict(DEFAULT_INTERACTION_PARAMS)

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
            "topology_graph_v1": {"edges": [{"final_work": 1.1}]},
            "hit_pattern_name": "测试格 (亲和度 88.0%)",
            "structure_candidates_v0": {"hud": {"stable_pct": 40.0, "follower_pct": 30.0, "leap_pct": 30.0}},
            "structure_final_decision_v0": {"primary_structure": "FOLLOW_WEALTH_POWER", "decision_confidence": 0.86},
            "audit_log": {"skill_id": "final_verdict_skill", "param_version_id": "p-1"},
            "llm_request_messages": [{"role": "user", "content": "终判探针"}],
            "llm_raw_response": '{"verdict_body":"适合推进"}',
            "llm_meta": {"model_name": "stub", "elapsed_ms": 1.0},
            "brain_hub": {"lineage": "HTN_DRIVEN", "seeds_matched": ["system_stress"], "htn_plan": {"plan": ["OBSERVE"]}},
            "assertion_tree": {
                "protocol": "assertion_tree.v1",
                "nodes": [{"node_id": "n1", "node_type": "FACT", "text": "stub", "evidence_refs": []}],
            },
        }


class _CaptureVerdictSkill:
    def __init__(self) -> None:
        self.kwargs = {}

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        return {
            "version_id": "ver-x",
            "verdict_body": "x",
            "change_log": [],
            "logical_evidence": [],
            "work_vector": {},
            "structure_candidates_v0": {},
            "audit_log": {},
            "brain_hub": {"lineage": "HTN_DRIVEN", "seeds_matched": ["system_stress"], "htn_plan": {"plan": ["OBSERVE"]}},
            "assertion_tree": {
                "protocol": "assertion_tree.v1",
                "nodes": [{"node_id": "n1", "node_type": "FACT", "text": "stub", "evidence_refs": []}],
            },
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


def test_analyze_clash_1990_06_14_officer_pattern_rows_with_blind_only_enabled_plugins_v82():
    """V8.2：格局白名单常驻；enabled 仅盲派时 1990-06-14 样本仍须产出正官格 strict 行（与机房一致）。"""
    pillars = get_bazi("1990-06-14", "12:00", "solar")
    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()):
        payload = asyncio.run(
            analysis_service.analyze_clash_flow(
                AnalyzeClashRequest(
                    pillars=pillars,
                    enabled_plugins=["classical.blind_school.v1"],
                )
            )
        )
    meta = (payload.get("physics_tensor") or {}).get("meta") or {}
    assert meta.get("pattern_thresholds_status") == "OK"
    rows = meta.get("pattern_thresholds") or []
    assert isinstance(rows, list) and rows
    ids = [str(r.get("pattern_id") or "") for r in rows if isinstance(r, dict)]
    assert "GOV_PATTERN" in ids
    gov = next(r for r in rows if isinstance(r, dict) and r.get("pattern_id") == "GOV_PATTERN")
    assert str(gov.get("engine_v") or "") == "MANIFEST_V5.8_STRICT"
    assert "正官" in str(gov.get("name") or "")
    l2 = str(meta.get("l2_pattern_result_summary_v1") or "")
    assert l2 == "正官格 (亲和度 100.0%)"
    assert str(meta.get("hit_pattern_name") or "") == l2


def test_arch_sentry_round_messages_under_300_chars():
    pillars = get_bazi("1990-06-14", "12:00", "solar")
    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()):
        payload = asyncio.run(
            analysis_service.analyze_clash_flow(
                AnalyzeClashRequest(
                    pillars=pillars,
                    enabled_plugins=["classical.blind_school.v1"],
                )
            )
        )
    msgs = (((payload.get("first_observation_llm") or {}).get("messages")) or [])
    assert isinstance(msgs, list) and msgs
    assert all(len(str((m or {}).get("content") or "")) <= 300 for m in msgs)


def test_analyze_seed_flow_builds_audit_summary():
    pillars = FourPillars(
        year=StemBranchPair(stem="甲", branch="申"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="午"),
        hour=StemBranchPair(stem="庚", branch="子"),
    )
    fake_matrix = ConflictMatrix(points=[ConflictPoint(kind="clash", positions=["month_branch", "year_branch"], detail="寅申冲")])
    body = AnalyzeSeedRequest(date="1977-05-08", time="18:00", calendar="solar", gender="male")

    with patch.object(analysis_service, "QwenClient", return_value=_FakeClient()), patch.object(
        analysis_service.Scanner, "scan", return_value=fake_matrix
    ), patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
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
    fo = payload.get("first_observation_llm") or {}
    assert isinstance(fo.get("messages"), list) and len(fo["messages"]) >= 1
    assert fo.get("response_text") == payload["llm_prompt"]


def test_load_consensus_history_and_generate_final_verdict():
    history = analysis_service.load_consensus_history(_FakeSession(), 1)
    assert history[0]["decision_key"] == "root_factor"
    assert history[0]["confirmed_value"] == 1.2

    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=_FakeVerdictSkill()):
        payload = asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata={"foo": "bar"},
                    physics_tensor={"score": 1, "meta": {}, "abs_nodes": {"比肩": 1.0}},
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
    assert payload["topology_graph_v1"]["edges"][0]["final_work"] == 1.1
    assert payload["hit_pattern_name"] == "测试格 (亲和度 88.0%)"
    assert payload["structure_candidates_v0"]["hud"]["leap_pct"] == 30.0
    assert payload["structure_final_decision_v0"]["primary_structure"] == "FOLLOW_WEALTH_POWER"
    assert payload["audit_log"]["skill_id"] == "final_verdict_skill"
    assert payload["llm_request_messages"][0]["role"] == "user"
    assert "适合推进" in payload["llm_raw_response"]
    assert payload["llm_meta"]["model_name"] == "stub"


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


def test_final_verdict_mandatory_final_synthesis_passes_to_skill() -> None:
    skill = _CaptureVerdictSkill()
    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=skill):
        asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata={"pillars": {"year": {"stem": "甲", "branch": "子"}}},
                    physics_tensor={"meta": {}, "abs_nodes": {"比肩": 1.0}},
                    mandatory_final_synthesis=True,
                ),
                [],
            )
        )
    assert skill.kwargs.get("mandatory_final_synthesis") is True


def test_final_verdict_request_regeneration_context_serializes_to_skill() -> None:
    skill = _CaptureVerdictSkill()
    reg = RegenerationContext(
        reason="η 微调",
        trigger="physics_recalc",
        previous_version_id="ver-prev",
    )
    assert reg.model_dump() == {
        "reason": "η 微调",
        "trigger": "physics_recalc",
        "previous_version_id": "ver-prev",
    }
    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=skill):
        asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata={},
                    physics_tensor={"meta": {}, "abs_nodes": {"比肩": 1.0}},
                    selected_cards=[],
                    consensus_history=[],
                    previous_verdict="",
                    regeneration_context=reg,
                    lang="ZH",
                ),
                [],
            )
        )
    assert skill.kwargs.get("regeneration_context") == reg.model_dump()


def test_generate_final_verdict_clear_previous_forces_rewrite():
    skill = _CaptureVerdictSkill()
    with patch.object(analysis_service.FinalVerdictSkill, "instance", return_value=skill):
        payload = asyncio.run(
            analysis_service.generate_final_verdict(
                FinalVerdictRequest(
                    metadata={},
                    physics_tensor={"meta": {}, "abs_nodes": {"比肩": 1.0}},
                    selected_cards=[],
                    consensus_history=[],
                    previous_verdict="old",
                    previous_logical_evidence=["old-evidence"],
                    clear_previous_verdict=True,
                    lang="ZH",
                ),
                [],
            )
        )
    assert payload["ok"] is True
    assert skill.kwargs.get("previous_verdict") == ""
    assert skill.kwargs.get("previous_logical_evidence") == []


def test_run_stress_test_returns_rollback_signal():
    fake_payload = {
        "physics_tensor": {
            "deity_energy_axes": {
                "比肩": {"absolute_energy": 0.2},
                "正财": {"absolute_energy": 6.0},
            },
            "meta": {"runtime_physics_config": {}},
        }
    }

    with patch.object(analysis_service, "analyze_clash_flow", new=AsyncMock(side_effect=[fake_payload, fake_payload])):
        payload = asyncio.run(
            analysis_service.run_stress_test(
                type(
                    "Req",
                    (),
                    {
                        "metadata": {
                            "pillars": {
                                "year": {"stem": "甲", "branch": "子", "energy_value": 100},
                                "month": {"stem": "丙", "branch": "寅", "energy_value": 100},
                                "day": {"stem": "戊", "branch": "午", "energy_value": 100},
                                "hour": {"stem": "庚", "branch": "申", "energy_value": 100},
                            },
                            "conflict_matrix": {"points": [{"detail": "寅午冲"}]},
                        },
                        "physics_config": None,
                        "gender": "male",
                        "baseline_structure_final_decision": {"rollback_triggers": ["if Self_Abs > 1.2 -> CollapseFollowerStructure"]},
                        "luck_pillar": "壬辰",
                        "year_pillar": "庚子",
                        "lang": "ZH",
                        "enabled_plugins": [],
                    },
                )()
            )
        )
    assert payload["ok"] is True
    assert "rollback_triggered" in payload
