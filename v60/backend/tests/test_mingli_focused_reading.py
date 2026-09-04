from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from abu_v60.api import mingli_stage
from abu_v60.db import engine
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.focused_pass_service import MingliFocusedPassService
from abu_v60.mingli.focused_reading_contracts import (
    MINGLI_FOCUS_ORDER,
    MingliFocusedPassRecord,
    MingliFocusedReadingEnvelope,
)
from abu_v60.mingli.focused_reading_runtime import (
    MINGLI_FOCUSED_NUM_CTX,
    MINGLI_FOCUSED_NUM_PREDICT,
    MINGLI_FOCUSED_PROMPT_HASH,
    MINGLI_FOCUSED_SEED,
    QWEN38_INSTRUCT_MIN_P,
    QWEN38_INSTRUCT_PRESENCE_PENALTY,
    QWEN38_INSTRUCT_REPEAT_PENALTY,
    QWEN38_INSTRUCT_TEMPERATURE,
    QWEN38_INSTRUCT_TOP_K,
    QWEN38_INSTRUCT_TOP_P,
    MingliFocusedRuntime,
    OllamaFocusedReadingProvider,
    focused_context,
    mingli_focused_runtime_manifest,
    normalize_focused_text,
)
from abu_v60.mingli.focused_reading_service import MingliFocusedReadingService
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.service import MingliCaseService
from abu_v60.mingli.timing_store import MingliTimingVectorStore
from abu_v60.settings import settings
from fastapi import Response
from sqlalchemy import text


def _packet() -> tuple[dict[str, str], Any]:
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT c.owner_account_ref, c.case_ref,
                           r.reading_ref, r.reading_hash
                    FROM mingli.cases AS c
                    JOIN mingli.readings AS r ON r.case_ref = c.case_ref
                    WHERE c.subject_kind IN ('HUMAN_OWNER', 'HUMAN_REFERENCE')
                      AND c.status = 'ACTIVE'
                    ORDER BY (c.subject_kind = 'HUMAN_OWNER') DESC,
                             c.created_at, r.created_at DESC
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .one()
        )
    fixture = {key: str(value) for key, value in row.items()}
    workspace = MingliCaseService(engine).workspace(
        account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
    )
    reading = MingliReadingStore(engine).get(reading_ref=fixture["reading_ref"])
    packet = MingliAgentCasePacketCompiler().compile(
        workspace=workspace,
        reading=reading,
        quant_vector=MingliQuantVectorStore(engine).get(vector_ref=str(reading.quant_vector_ref)),
        mechanism_vector=MingliMechanismVectorStore(engine).get(
            vector_ref=str(reading.mechanism_vector_ref)
        ),
        timing_vector=MingliTimingVectorStore(engine).get(
            vector_ref=str(reading.timing_vector_ref)
        ),
    )
    return fixture, packet


def _provider(packet: Any) -> tuple[OllamaFocusedReadingProvider, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    timing_pillars = "、".join(item.pillar for item in packet.timing_coordinates)
    responses = (
        "### 原局总纲\n月令先定气候，根与印比决定承载；主路径成立仍要看泄耗。E001",
        "水势有源而不宜写成无边洪流，性情表现为先观察后推进，边界在承载是否稳定。",
        "事业先看结构如何把资源转成成果，财富则看交换能否持续；两者都不能脱离承载条件。",
        "关系要同时看星轴和夫妻宫，家庭责任则看全局如何分配；不能据此编造既成事件。",
        f"原局基线不变，当前{timing_pillars}只是在既有路径上增加推动或阻断。",
    )

    def transport(**values: Any) -> dict[str, Any]:
        index = len(calls)
        calls.append(values)
        return {
            "response": responses[index],
            "prompt_eval_count": 80 + index,
            "eval_count": 40 + index,
            "created_at": f"2026-08-15T00:00:0{index}Z",
        }

    return (
        OllamaFocusedReadingProvider(
            model_ref="qwen3.8:27b",
            model_digest="b" * 64,
            base_url="http://private-model.invalid",
            timeout_seconds=12,
            temperature=0,
            top_p=0.95,
            top_k=64,
            keep_alive="30m",
            transport=transport,
        ),
        calls,
    )


def _envelope(fixture: dict[str, str], packet: Any, passes: tuple[Any, ...]):
    provider, _ = _provider(packet)
    return MingliFocusedReadingEnvelope.issue(
        generation_key="c" * 64,
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=packet.case_ref,
        chart_version_ref=packet.chart_version_ref,
        life_case_revision_ref=packet.life_case_revision_ref,
        reading_ref=packet.reading_ref,
        reading_hash=packet.reading_hash,
        packet_ref=packet.packet_ref,
        packet_hash=packet.packet_hash,
        provider_id=provider.provider_id,
        model_ref=provider.model_ref,
        model_digest=provider.model_digest,
        provider_profile_ref=provider.provider_profile_ref,
        provider_profile_hash=provider.provider_profile_hash,
        prompt_hash=MINGLI_FOCUSED_PROMPT_HASH,
        passes=passes,
    )


def test_focused_provider_asks_five_small_natural_text_questions() -> None:
    _, packet = _packet()
    provider, calls = _provider(packet)

    passes = provider.generate(packet=packet)

    assert tuple(item.focus for item in passes) == MINGLI_FOCUS_ORDER
    assert len(calls) == 5
    assert all("format" not in call["payload"] for call in calls)
    assert all("system" not in call["payload"] for call in calls)
    assert all(call["payload"]["raw"] is True for call in calls)
    assert all(call["payload"]["think"] is False for call in calls)
    assert all(call["payload"]["stream"] is False for call in calls)
    assert all(
        call["payload"]["prompt"].startswith("<|im_start|>system\n")
        and "<|im_start|>user\n" in call["payload"]["prompt"]
        and call["payload"]["prompt"].endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")
        for call in calls
    )
    assert all(
        call["payload"]["options"]["temperature"] == QWEN38_INSTRUCT_TEMPERATURE
        and call["payload"]["options"]["top_p"] == QWEN38_INSTRUCT_TOP_P
        and call["payload"]["options"]["top_k"] == QWEN38_INSTRUCT_TOP_K
        and call["payload"]["options"]["min_p"] == QWEN38_INSTRUCT_MIN_P
        and call["payload"]["options"]["presence_penalty"] == QWEN38_INSTRUCT_PRESENCE_PENALTY
        and call["payload"]["options"]["repeat_penalty"] == QWEN38_INSTRUCT_REPEAT_PENALTY
        and call["payload"]["options"]["seed"] == MINGLI_FOCUSED_SEED
        for call in calls
    )
    assert all(call["payload"]["options"]["num_ctx"] == MINGLI_FOCUSED_NUM_CTX for call in calls)
    assert all(
        call["payload"]["options"]["num_predict"] == MINGLI_FOCUSED_NUM_PREDICT for call in calls
    )
    assert "分析日期" not in calls[0]["payload"]["prompt"]
    assert "前序原局总纲" in calls[1]["payload"]["prompt"]
    assert "大运与流年" in calls[4]["payload"]["prompt"]
    assert "E001" not in passes[0].normalized_text
    assert set(passes[0].normalization_codes) == {
        "EVIDENCE_TOKEN_REMOVED",
        "MARKDOWN_PRESENTATION_REMOVED",
    }
    assert sum(item.total_tokens for item in passes) == sum(120 + index * 2 for index in range(5))


def test_focused_context_and_normalizer_do_not_invent_semantics() -> None:
    _, packet = _packet()
    structure = focused_context(packet, focus="STRUCTURE", structure_text=None)
    timing = focused_context(packet, focus="TIMING", structure_text="原局总纲")

    assert "分析日期" not in structure
    assert "大运与流年" not in structure
    assert timing["流月资料"] == "未提供"
    raw = "**判断**：一定会在流年发财，且有六合。E003"
    normalized, codes = normalize_focused_text(
        raw,
        focus="CAREER_WEALTH",
        packet=packet,
    )
    assert normalized == "判断：一定会在流年发财，且有六合。"
    assert "ABSOLUTE_CLAIM_REQUIRES_REVIEW" in codes
    assert "TIMING_SCOPE_LEAK_REQUIRES_REVIEW" in codes
    assert "EVIDENCE_TOKEN_REMOVED" in codes
    assert "发财" in normalized

    semantic_raw = (
        "辰、亥中藏戊己壬水得印比，己土能化泄卯木，"
        "又与双午形成强烈火局，属于财印相生，易生灾祸与焦虑。"
    )
    semantic_text, semantic_codes = normalize_focused_text(
        semantic_raw,
        focus="TIMING",
        packet=packet,
    )
    assert semantic_text == semantic_raw
    assert "FIVE_ELEMENT_CAUSAL_CONFLICT_REQUIRES_REVIEW" in semantic_codes
    assert "HIDDEN_STEM_COORDINATE_CONFLICT_REQUIRES_REVIEW" in semantic_codes
    assert "HEALTH_DISASTER_CLAIM_REQUIRES_REVIEW" in semantic_codes
    assert "PSYCHOLOGICAL_CLAIM_REQUIRES_REVIEW" in semantic_codes
    assert "UNADMITTED_RELATION_EFFECT_REQUIRES_REVIEW" in semantic_codes

    branch = packet.pillars[0].branch
    actual_count = sum(item.branch == branch for item in packet.pillars)
    wrong_count = "一" if actual_count != 1 else "两"
    month_hidden = set(packet.pillars[1].hidden_stems)
    wrong_month_stem = next(stem for stem in "甲乙丙丁戊己庚辛壬癸" if stem not in month_hidden)
    coordinate_text, coordinate_codes = normalize_focused_text(
        f"地支{wrong_count}{branch}，月令七杀{wrong_month_stem}木。",
        focus="STRUCTURE",
        packet=packet,
    )
    assert coordinate_text
    assert "BRANCH_COUNT_CONFLICT_REQUIRES_REVIEW" in coordinate_codes
    assert "MONTH_COMMAND_COORDINATE_CONFLICT_REQUIRES_REVIEW" in coordinate_codes

    inference_text, inference_codes = normalize_focused_text(
        "原生家庭已经缺少支持，属于从财格；唯有顺势方能稳定。丙辛合化，午子六冲引发财星动荡。",
        focus="TIMING",
        packet=packet,
    )
    assert inference_text
    assert "ABSOLUTE_CLAIM_REQUIRES_REVIEW" in inference_codes
    assert "REGIME_ASSERTION_REQUIRES_REVIEW" in inference_codes
    assert "UNSUPPORTED_BIOGRAPHICAL_CLAIM_REQUIRES_REVIEW" in inference_codes
    assert "UNADMITTED_RELATION_TERM_REQUIRES_REVIEW" in inference_codes
    assert "UNADMITTED_RELATION_EFFECT_REQUIRES_REVIEW" in inference_codes


def test_focused_normalizer_repairs_visible_ten_god_position_counts() -> None:
    _, packet = _packet()
    target = next(
        item.visible_ten_god
        for item in packet.pillars
        if item.visible_ten_god != "日主"
    )

    normalized, codes = normalize_focused_text(
        f"虽年、月、日、时四透{target}帮身，仍需看承载。",
        focus="STRUCTURE",
        packet=packet,
    )

    expected_positions = [
        item.slot
        for item in packet.pillars
        if item.visible_ten_god == target
    ]
    assert "VISIBLE_TEN_GOD_COORDINATE_REPAIRED" in codes
    assert f"年、月、日、时四透{target}" not in normalized
    assert all(
        {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}[slot]
        in normalized
        for slot in expected_positions
    )

    scoped, scoped_codes = normalize_focused_text(
        "主路径的失效条件是：若岁运再行火地，火势过旺则焚木，导致日主彻底枯竭。",
        focus="STRUCTURE",
        packet=packet,
    )
    assert scoped == "主路径的失效条件是：若火势继续过旺，日主承载会进一步减弱。"
    assert "TIMING_SCOPE_PHRASE_REMOVED" in scoped_codes
    assert "ABSOLUTE_TONE_SOFTENED" in scoped_codes
    assert "TIMING_SCOPE_LEAK_REQUIRES_REVIEW" not in scoped_codes


def test_focused_envelope_binds_pass_order_tokens_and_lineage() -> None:
    fixture, packet = _packet()
    provider, _ = _provider(packet)
    passes = provider.generate(packet=packet)

    reading = _envelope(fixture, packet, passes)

    assert reading.pass_for("STRUCTURE") == passes[0]
    assert reading.total_tokens == sum(item.total_tokens for item in passes)
    assert reading.duration_ms == sum(item.duration_ms for item in passes)
    assert reading.publication_allowed is False
    assert reading.canonical_fact_write_allowed is False
    assert reading.owner_review_status == "NOT_REVIEWED"


def test_focused_service_replays_by_generation_key_without_second_model_run() -> None:
    fixture, packet = _packet()
    provider, calls = _provider(packet)

    class PacketService:
        def compile_packet(self, **_: str):
            return packet

    class MemoryStore:
        def __init__(self) -> None:
            self.values: dict[tuple[str, str], MingliFocusedReadingEnvelope] = {}

        def find_generation(self, *, requester_account_ref: str, generation_key: str):
            return self.values.get((requester_account_ref, generation_key))

        def ensure(self, reading: MingliFocusedReadingEnvelope):
            key = (reading.requester_account_ref, reading.generation_key)
            self.values.setdefault(key, reading)
            return self.values[key]

    memory = MemoryStore()
    service = MingliFocusedReadingService(
        engine,
        runtime=MingliFocusedRuntime(provider=provider, enabled=True),
        store=memory,  # type: ignore[arg-type]
        packet_service=PacketService(),  # type: ignore[arg-type]
    )
    request = {
        "requester_account_ref": fixture["owner_account_ref"],
        "case_ref": fixture["case_ref"],
        "expected_reading_ref": fixture["reading_ref"],
        "expected_reading_hash": fixture["reading_hash"],
    }

    first = service.generate(**request)
    replay = service.generate(**request)

    assert replay == first
    assert len(calls) == 5
    assert len(memory.values) == 1


def test_progressive_pass_service_requires_structure_and_replays_each_focus() -> None:
    fixture, packet = _packet()
    provider, calls = _provider(packet)

    class PacketService:
        def compile_packet(self, **_: str):
            return packet

    class MemoryStore:
        def __init__(self) -> None:
            self.values: dict[tuple[str, str], MingliFocusedPassRecord] = {}

        def find_generation(self, *, requester_account_ref: str, generation_key: str):
            return self.values.get((requester_account_ref, generation_key))

        def latest(self, **values: str):
            matches = [
                item
                for item in self.values.values()
                if item.requester_account_ref == values["requester_account_ref"]
                and item.case_ref == values["case_ref"]
                and item.reading_ref == values["reading_ref"]
                and item.reading_hash == values["reading_hash"]
                and item.provider_profile_hash == values["provider_profile_hash"]
                and item.prompt_hash == values["prompt_hash"]
                and item.focus == values["focus"]
            ]
            return matches[-1] if matches else None

        def ensure(self, record: MingliFocusedPassRecord):
            key = (record.requester_account_ref, record.generation_key)
            self.values.setdefault(key, record)
            return self.values[key]

    memory = MemoryStore()
    service = MingliFocusedPassService(
        engine,
        runtime=MingliFocusedRuntime(provider=provider, enabled=True),
        store=memory,  # type: ignore[arg-type]
        packet_service=PacketService(),  # type: ignore[arg-type]
    )
    request = {
        "requester_account_ref": fixture["owner_account_ref"],
        "case_ref": fixture["case_ref"],
        "expected_reading_ref": fixture["reading_ref"],
        "expected_reading_hash": fixture["reading_hash"],
    }

    with pytest.raises(ValueError, match="mingli_focused_structure_required"):
        service.generate(**request, focus="CAREER_WEALTH")

    structure = service.generate(**request, focus="STRUCTURE")
    replay = service.generate(**request, focus="STRUCTURE")
    career = service.generate(**request, focus="CAREER_WEALTH")

    assert replay == structure
    assert career.structure_pass_hash == structure.pass_result.pass_hash
    assert career.pass_result.focus == "CAREER_WEALTH"
    assert len(calls) == 2
    assert len(memory.values) == 2


def test_progressive_pass_api_redacts_raw_teacher_material(monkeypatch: Any) -> None:
    fixture, packet = _packet()
    provider, _ = _provider(packet)
    result = provider.generate_focus(
        packet=packet,
        focus="STRUCTURE",
        structure_text=None,
    )
    record = MingliFocusedPassRecord.issue(
        generation_key="d" * 64,
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=packet.case_ref,
        chart_version_ref=packet.chart_version_ref,
        life_case_revision_ref=packet.life_case_revision_ref,
        reading_ref=packet.reading_ref,
        reading_hash=packet.reading_hash,
        packet_ref=packet.packet_ref,
        packet_hash=packet.packet_hash,
        provider_id=provider.provider_id,
        model_ref=provider.model_ref,
        model_digest=provider.model_digest,
        provider_profile_ref=provider.provider_profile_ref,
        provider_profile_hash=provider.provider_profile_hash,
        prompt_hash=MINGLI_FOCUSED_PROMPT_HASH,
        focus="STRUCTURE",
        structure_pass_hash=None,
        pass_result=result,
    )

    class Service:
        def generate(self, **_: Any):
            return record

    monkeypatch.setattr(mingli_stage, "focused_passes", Service())
    request = mingli_stage.MingliFocusedPassRequest(
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
        focus="STRUCTURE",
    )
    response = Response()
    session = SimpleNamespace(account=SimpleNamespace(account_ref=fixture["owner_account_ref"]))

    payload = mingli_stage.generate_focused_pass(
        request,
        response,
        session,  # type: ignore[arg-type]
    )

    assert "raw_text" not in payload["pass_result"]
    assert payload["pass_result"]["normalized_text"]
    assert response.headers["Cache-Control"] == "private, no-store"


def test_focused_api_uses_session_and_redacts_raw_teacher_material(
    monkeypatch: Any,
) -> None:
    fixture, packet = _packet()
    provider, _ = _provider(packet)
    envelope = _envelope(fixture, packet, provider.generate(packet=packet))
    calls: list[dict[str, str]] = []

    class Service:
        def generate(self, **values: str):
            calls.append(values)
            return envelope

    monkeypatch.setattr(mingli_stage, "focused_readings", Service())
    request = mingli_stage.MingliFocusedReadingRequest(
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    response = Response()
    session = SimpleNamespace(account=SimpleNamespace(account_ref=fixture["owner_account_ref"]))

    payload = mingli_stage.generate_focused_reading(
        request,
        response,
        session,  # type: ignore[arg-type]
    )

    assert all("raw_text" not in item for item in payload["passes"])
    assert all(item["normalized_text"] for item in payload["passes"])
    assert calls[0]["requester_account_ref"] == fixture["owner_account_ref"]
    assert response.headers["Cache-Control"] == "private, no-store"


def test_focused_runtime_manifest_is_local_natural_text_only() -> None:
    manifest = mingli_focused_runtime_manifest(
        replace(settings, mingli_agent_enabled=True, mingli_agent_think=False)
    )

    assert manifest["status"] == "READY_FOR_OWNER_REVIEW"
    assert manifest["generation_mode"] == "PROGRESSIVE_ONE_FOCUS_PER_REQUEST"
    assert manifest["product_call_count_per_request"] == 1
    assert manifest["dev_batch_call_count"] == 5
    assert manifest["provider_profile"]["structured_output_mode"] == "natural_text"
    assert manifest["provider_profile"]["normalizer_version"] == (
        "v60.mingli-focused-normalizer.006"
    )
    assert manifest["provider_profile"]["call_count"] == 5
    assert manifest["provider_profile"]["think"] is False
    assert manifest["provider_profile"]["temperature"] == 0.7
    assert manifest["provider_profile"]["top_p"] == 0.8
    assert manifest["provider_profile"]["top_k"] == 20
    assert manifest["provider_profile"]["min_p"] == 0.0
    assert manifest["provider_profile"]["presence_penalty"] == 1.5
    assert manifest["provider_profile"]["repeat_penalty"] == 1.0
    assert manifest["provider_profile"]["num_ctx"] == 4096
    assert manifest["provider_profile"]["num_predict_per_call"] == 320
    assert manifest["publication_allowed"] is False
    assert manifest["canonical_fact_write_allowed"] is False
