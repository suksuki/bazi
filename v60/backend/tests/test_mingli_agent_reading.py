from __future__ import annotations

import json
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from abu_v60.api import mingli_stage
from abu_v60.db import engine
from abu_v60.mingli.agent_contracts import (
    MingliAgentModelOutput,
    MingliAgentReadingEnvelope,
    mingli_agent_generation_key,
)
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.agent_reasoning_modes import (
    BLIND_READING_CONTRACT,
    RECONCILIATION_CONTRACT,
)
from abu_v60.mingli.agent_runtime import (
    MingliAgentProviderError,
    MingliAgentProviderResult,
    MingliAgentRuntime,
    OllamaMingliAgentProvider,
    configured_mingli_agent_runtime,
    mingli_agent_runtime_manifest,
    mingli_agent_runtime_status,
)
from abu_v60.mingli.agent_service import MingliAgentService, MingliAgentServiceError
from abu_v60.mingli.agent_store import MingliAgentReadingStore
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_claim_graph import MingliReadingClaimGraphProjector
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.reading_summary import MingliReadingSummaryService
from abu_v60.mingli.service import MingliCaseService
from abu_v60.mingli.timing_store import MingliTimingVectorStore
from abu_v60.provenance import canonical_json, content_hash
from abu_v60.settings import settings
from fastapi import HTTPException, Response
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def _base_reading_fixture() -> dict[str, str]:
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT c.owner_account_ref, c.case_ref,
                           r.chart_version_ref, r.life_case_revision_ref,
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
    return {key: str(value) for key, value in row.items()}


def _unrelated_account_ref(account_ref: str) -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT account_ref FROM identity.accounts
                    WHERE account_ref <> :account_ref
                    ORDER BY created_at, account_ref
                    LIMIT 1
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
        )


def _valid_output(*, suffix: str = "", packet: Any | None = None) -> MingliAgentModelOutput:
    if packet is None:
        roots: tuple[str, ...] = ()
        peers: tuple[str, ...] = ()
        resources: tuple[str, ...] = ()
        base_evidence = ("E001", "E002")
        mechanism_ids: tuple[str, ...] = ()
        dayun_coordinate = "E003"
        annual_coordinate = "E004"
        dayun_relations: tuple[str, ...] = ()
        annual_relations: tuple[str, ...] = ()
    else:
        roots = packet.day_master_support.same_element_hidden_support
        peers = packet.day_master_support.visible_peer_support
        resources = packet.day_master_support.resource_support
        base_evidence = (
            packet.pillars[1].evidence_id,
            packet.day_master_support.evidence_id,
        )
        mechanism_ids = tuple(
            item.evidence_id for item in packet.mechanism_observations
        )
        coordinates = {item.layer: item.evidence_id for item in packet.timing_coordinates}
        dayun_coordinate = coordinates["DAYUN"]
        annual_coordinate = coordinates["ANNUAL"]
        dayun_relations = tuple(
            item.evidence_id
            for item in packet.timing_relations
            if item.left_layer == "DAYUN"
        )
        annual_relations = tuple(
            item.evidence_id
            for item in packet.timing_relations
            if item.left_layer == "ANNUAL"
        )
    domains = {}
    for domain, title in (
        ("personality", "性情里的主轴"),
        ("career", "事业里的发力方式"),
        ("wealth", "财富里的交换路径"),
        ("relationship", "关系里的靠近方式"),
        ("family", "家庭里的责任位置"),
    ):
        domains[domain] = {
                "headline": f"{title}{suffix}",
                "conclusion": (
                    "命局的主结构使这个领域先经过辨别与组织，再形成稳定行动，"
                    "环境配合时表现得更集中。"
                ),
                "causal_chain": ["结构形成注意方向并进入现实选择"],
                "condition": "职责清楚并允许持续积累",
                "evidence_ids": base_evidence,
                "confidence": "MEDIUM",
            }
    return MingliAgentModelOutput.model_validate(
        {
            "first_look": f"这是一张力量集中而转化路径鲜明的命局{suffix}",
            "whole_chart_thesis": (
                "全盘的关键不在单个五行多少，而在月令、透藏与各柱之间能否"
                "把分散力量导向同一条可持续的转化路径。"
            ),
            "day_master_state": "BALANCED",
            "support_selection": {
                "root_status": "PRESENT" if roots else "NONE",
                "root_coordinates": roots,
                "peer_coordinates": peers,
                "resource_coordinates": resources,
            },
            "day_master_rationale": (
                "日主得到明干同类和印星回应，也受到泄耗与约束，不能用简单"
                "计数判定，整体更接近有条件的相对均衡。"
            ),
            "day_master_evidence_ids": base_evidence,
            "hypotheses": [
                {
                    "hypothesis_id": "H1",
                    "role": "PRIMARY",
                    "name": "主结构承接",
                    "judgment": "WORKS_IF",
                    "mechanism_evidence_ids": mechanism_ids[:1],
                    "thesis": "以月令为起点，各位置彼此承接，构成全盘最连贯的主解释。",
                    "failure_condition": "关键转化被持续截断时不成立",
                    "evidence_ids": (*base_evidence, *mechanism_ids[:1]),
                    "confidence": "MEDIUM",
                },
                {
                    "hypothesis_id": "H2",
                    "role": "ALTERNATIVE",
                    "name": "局部力量主导",
                    "judgment": "PARTIAL",
                    "mechanism_evidence_ids": mechanism_ids[1:2],
                    "thesis": "另一种解释是局部力量暂时占先，但对全盘位置关系的解释较弱。",
                    "failure_condition": "岁运转向后迅速失去主导",
                    "evidence_ids": (*base_evidence, *mechanism_ids[1:2]),
                    "confidence": "LOW",
                },
            ],
            "work_path": {
                "path_statement": "力量从月令起步，经由透干组织和现实任务转化，最后落到可重复的成果。",
                "transformation_codes": ["CHANNELS", "GENERATES"],
                "closure": "CONDITIONAL",
                "condition": "任务边界清楚且转化方向一致",
                "evidence_ids": base_evidence,
            },
            "life_image": {
                "title": f"有渠可行的水{suffix}",
                "image": "水势并不只求浩大，而要找到能够持续转弯并抵达田地的河道。",
                "explanation": (
                    "这幅意象来自月令、透干与转化路径之间的承接：力量被组织时能润物，"
                    "失去河道时则容易在局部回旋。"
                ),
                "evidence_ids": base_evidence,
            },
            "domains": domains,
            "timing": {
                "natal_baseline": "原局先确定力量如何承接，岁运只改变哪一段被放大。",
                "natal_evidence_ids": base_evidence,
                "dayun": {
                    "coordinate_evidence_id": dayun_coordinate,
                    "relation_evidence_ids": dayun_relations,
                    "conclusion": "若关系成员获得原局承接，当前大运会把外部任务推到前台，也更考验收束目标。",
                    "activation_chain": ["若原局路径具备承载条件，大运进入后才会放大对应位置"],
                    "evidence_ids": (*base_evidence, dayun_coordinate, *dayun_relations),
                    "confidence": "MEDIUM",
                },
                "annual": {
                    "coordinate_evidence_id": annual_coordinate,
                    "relation_evidence_ids": annual_relations,
                    "conclusion": "当前流年进一步触发行动与交换，不宜把短期活跃直接等同长期定局。",
                    "activation_chain": ["流年进入后检验成果能否落地"],
                    "evidence_ids": (*base_evidence, dayun_coordinate, annual_coordinate, *annual_relations),
                    "confidence": "MEDIUM",
                },
                "verification_signals": ["职责是否更集中", "成果是否更容易被确认"],
            },
            "discriminating_question": "现实中的任务增加后，成果更集中还是方向更分散？",
        }
    )


def _packet():
    fixture = _base_reading_fixture()
    workspace = MingliCaseService(engine).workspace(
        account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
    )
    reading = MingliReadingStore(engine).get(reading_ref=fixture["reading_ref"])
    return fixture, MingliAgentCasePacketCompiler().compile(
        workspace=workspace,
        reading=reading,
        quant_vector=MingliQuantVectorStore(engine).get(
            vector_ref=str(reading.quant_vector_ref)
        ),
        mechanism_vector=MingliMechanismVectorStore(engine).get(
            vector_ref=str(reading.mechanism_vector_ref)
        ),
        timing_vector=MingliTimingVectorStore(engine).get(
            vector_ref=str(reading.timing_vector_ref)
        ),
    )


class _FakeProvider:
    provider_id = "test-provider"
    model_ref = "test-mingli-model"
    model_digest = "a" * 64
    provider_profile_ref = "v60.test-mingli-agent-profile.001"
    provider_profile_hash = content_hash({"profile": provider_profile_ref})

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *, packet: Any) -> MingliAgentProviderResult:
        self.calls += 1
        return MingliAgentProviderResult(
            provider_response_ref=f"test-response-{packet.packet_hash[:24]}",
            output=_valid_output(packet=packet),
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            duration_ms=50,
        )


class _OutputProvider(_FakeProvider):
    def __init__(self, output: MingliAgentModelOutput) -> None:
        super().__init__()
        self._output = output

    def generate(self, *, packet: Any) -> MingliAgentProviderResult:
        self.calls += 1
        return MingliAgentProviderResult(
            provider_response_ref=f"test-response-{packet.packet_hash[:24]}",
            output=self._output,
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            duration_ms=50,
        )


class _MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, MingliAgentReadingEnvelope] = {}

    def find_generation(self, *, requester_account_ref: str, generation_key: str):
        value = self.values.get(generation_key)
        return (
            value
            if value is not None
            and value.requester_account_ref == requester_account_ref
            else None
        )

    def ensure(self, reading: MingliAgentReadingEnvelope):
        return self.values.setdefault(reading.generation_key, reading)

    def latest(self, **_: object):
        return None


class _TransactionalEngine:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def begin(self):
        return nullcontext(self._connection)

    def connect(self):
        return nullcontext(self._connection)


def test_agent_contract_rejects_unknown_evidence_and_engineering_copy() -> None:
    output = _valid_output()
    output.validate_evidence(frozenset({"E001", "E002", "E003", "E004"}))
    with pytest.raises(ValueError, match="unknown_evidence"):
        output.validate_evidence(frozenset({"E999"}))
    with pytest.raises(ValueError, match="non_reading_language"):
        MingliAgentModelOutput.model_validate(
            {**output.model_dump(mode="json"), "first_look": "这份命局尚未接线，稍后再看具体结果"}
        )


def test_blind_and_reconciliation_modes_are_physically_distinct() -> None:
    _, packet = _packet()
    prompt_view = packet.model_prompt_view()

    assert BLIND_READING_CONTRACT.admission_status == "ACTIVE"
    assert BLIND_READING_CONTRACT.generation_allowed is True
    assert BLIND_READING_CONTRACT.observation_ledger_required is False
    assert RECONCILIATION_CONTRACT.admission_status == "CONTRACT_RESERVED"
    assert RECONCILIATION_CONTRACT.generation_allowed is False
    assert RECONCILIATION_CONTRACT.observation_ledger_required is True
    assert prompt_view["reasoning_contract"]["mode"] == "BLIND_READING"
    assert prompt_view["reasoning_contract"]["profile_context_allowed"] is False
    assert prompt_view["reasoning_contract"]["life_case_observations_allowed"] is False
    serialized = canonical_json(prompt_view)
    assert packet.gender not in serialized
    assert packet.birth_timezone not in serialized
    assert packet.subject_kind not in serialized


def test_ollama_adapter_sends_one_locked_packet_and_validates_output() -> None:
    _, packet = _packet()
    calls: list[dict[str, Any]] = []

    def transport(**values: Any) -> dict[str, Any]:
        calls.append(values)
        output = _valid_output(packet=packet).model_dump(mode="json")
        output["day_master_evidence_ids"][0] = "E1"
        output["domains"]["career"]["conclusion"] += "（E001）"
        output["support_selection"]["peer_coordinates"] = ["错误坐标"]
        output["hypotheses"][0]["mechanism_evidence_ids"] = ["E001"]
        return {
            "response": json.dumps(output, ensure_ascii=False),
            "prompt_eval_count": 120,
            "eval_count": 240,
            "created_at": "2026-08-01T00:00:00Z",
        }

    provider = OllamaMingliAgentProvider(
        model_ref="qwen3.5:35b",
        model_digest="b" * 64,
        provider_profile_ref="v60.test-provider.001",
        base_url="http://private-model.invalid",
        timeout_seconds=3,
        think=False,
        temperature=0.1,
        top_p=0.9,
        top_k=40,
        num_ctx=32768,
        num_predict=3600,
        keep_alive="30m",
        transport=transport,
    )
    result = provider.generate(packet=packet)

    assert len(calls) == 1
    assert calls[0]["url"] == "http://private-model.invalid/api/generate"
    assert calls[0]["payload"]["prompt"] == canonical_json(packet.model_prompt_view())
    assert calls[0]["payload"]["stream"] is False
    assert calls[0]["payload"]["think"] is False
    assert result.total_tokens == 360
    assert result.output.day_master_evidence_ids[0] == "E001"
    assert "E001" not in result.output.domains.career.conclusion
    assert result.output.support_selection.peer_coordinates == (
        packet.day_master_support.visible_peer_support
    )
    assert set(result.output.hypotheses[0].mechanism_evidence_ids).issubset(
        {item.evidence_id for item in packet.mechanism_observations}
    )
    assert len(result.output.day_master_evidence_ids) == 2
    assert result.output.hypotheses[0].role == "PRIMARY"


def test_packet_separates_roots_visible_peers_resources_and_repeated_branch() -> None:
    _, packet = _packet()

    assert packet.day_master_support.same_identity_hidden_support == ()
    assert packet.day_master_support.same_element_hidden_support == ()
    assert packet.day_master_support.visible_peer_support == (
        "month干乙(比肩)",
        "hour干乙(比肩)",
    )
    assert packet.day_master_support.resource_support == ("day支藏癸(偏印)",)
    assert tuple(item.layer for item in packet.timing_coordinates) == (
        "DAYUN",
        "ANNUAL",
    )
    assert all(item.left_layer != "MONTHLY" for item in packet.timing_relations)
    assert len(canonical_json(packet.model_prompt_view())) <= 6500
    assert any(
        relation.relation_type == "same_branch_membership"
        and {relation.left_slot, relation.right_slot} == {"year", "month"}
        for relation in packet.natal_relations
    )


def test_common_runtime_rejects_support_and_timing_scope_drift() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet)
    root_drift = output.model_dump(mode="json")
    root_drift["support_selection"].update(
        {
            "root_status": "PRESENT",
            "root_coordinates": list(packet.day_master_support.resource_support),
        }
    )
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(root_drift)),
        enabled=True,
    )
    with pytest.raises(MingliAgentProviderError, match="root_status_conflicts"):
        runtime.run(
            requester_account_ref=fixture["owner_account_ref"],
            packet=packet,
        )

    dayun_relation = next(
        item.evidence_id
        for item in packet.timing_relations
        if item.left_layer == "DAYUN"
    )
    timing_drift = output.model_dump(mode="json")
    timing_drift["timing"]["annual"]["relation_evidence_ids"] = [dayun_relation]
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(timing_drift)),
        enabled=True,
    )
    with pytest.raises(MingliAgentProviderError, match="relation_scope_conflict"):
        runtime.run(
            requester_account_ref=fixture["owner_account_ref"],
            packet=packet,
        )


def test_missing_primary_chart_basis_keeps_whole_reading_for_claim_review() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    primary = next(
        item for item in output["hypotheses"] if item["role"] == "PRIMARY"
    )
    primary["evidence_ids"] = [
        item.evidence_id for item in packet.mechanism_observations[:2]
    ]
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["WHOLE_CHART"].status == "NEEDS_RECONCILIATION"
    assert by_key["HYPOTHESIS_H1"].status == "NEEDS_RECONCILIATION"
    assert set(by_key["HYPOTHESIS_H1"].assessment_codes) == {
        "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
        "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
    }
    assert by_key["DAY_MASTER"].status == "PROVISIONAL"


def test_common_runtime_distinguishes_no_root_from_invented_root_claim() -> None:
    fixture, packet = _packet()
    assert packet.day_master_support.same_element_hidden_support == ()
    output = _valid_output(packet=packet)

    no_root = output.model_dump(mode="json")
    no_root["whole_chart_thesis"] = (
        "日主在地支无同类根气，判断必须转向月令、明干同类与印星位置如何共同承接。"
    )
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(no_root)),
        enabled=True,
    )
    reading = runtime.run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )
    assert "无同类根气" in reading.output.whole_chart_thesis

    invented_root = output.model_dump(mode="json")
    invented_root["whole_chart_thesis"] = (
        "日主在地支仍有微弱根气，因此可以直接承接月令与岁运带来的所有压力。"
    )
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(
            MingliAgentModelOutput.model_validate(invented_root)
        ),
        enabled=True,
    )
    with pytest.raises(MingliAgentProviderError, match="root_claim_conflicts"):
        runtime.run(
            requester_account_ref=fixture["owner_account_ref"],
            packet=packet,
        )


def test_common_runtime_rejects_evidence_ids_in_user_facing_prose() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["career"]["conclusion"] = (
        "事业判断由 E001 与月令位置共同支持，但证据编号不应出现在用户正文里。"
    )
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    )
    with pytest.raises(MingliAgentProviderError, match="evidence_id_leaked_into_prose"):
        runtime.run(
            requester_account_ref=fixture["owner_account_ref"],
            packet=packet,
        )


def test_claim_graph_quarantines_relation_effect_without_rejecting_reading() -> None:
    fixture, packet = _packet()
    assert any(
        item.left_layer == "DAYUN" for item in packet.timing_relations
    )
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["timing"]["dayun"]["conclusion"] = (
        "子丑六合已经合动偏印、化解七杀并提升承载，所以这一运的结构自然完成。"
    )
    output["timing"]["dayun"]["activation_chain"] = [
        "六合成员直接兑现为确定作用"
    ]
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    )
    memory = _MemoryStore()
    service = MingliAgentService(
        engine,
        runtime=runtime,
        store=memory,  # type: ignore[arg-type]
    )
    reading = service.generate(
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    dayun_claim = next(
        item for item in graph.claims if item.semantic_key == "TIMING_DAYUN"
    )
    assert len(memory.values) == 1
    assert dayun_claim.status == "WITHHELD"
    assert dayun_claim.assessment_codes == (
        "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT",
    )
    assert next(
        item for item in graph.claims if item.semantic_key == "WHOLE_CHART"
    ).status == "NEEDS_RECONCILIATION"

    relation_evidence_id = next(
        item.evidence_id
        for item in packet.timing_relations
        if item.left_layer == "DAYUN"
    )
    domain_bypass = _valid_output(packet=packet).model_dump(mode="json")
    domain_bypass["domains"]["career"]["conclusion"] = (
        "六合已经合动偏印并化解七杀，因此事业承载会直接提升到稳定状态。"
    )
    domain_bypass["domains"]["career"]["evidence_ids"].append(
        relation_evidence_id
    )
    domain_memory = _MemoryStore()
    domain_service = MingliAgentService(
        engine,
        runtime=MingliAgentRuntime(
            provider=_OutputProvider(
                MingliAgentModelOutput.model_validate(domain_bypass)
            ),
            enabled=True,
        ),
        store=domain_memory,  # type: ignore[arg-type]
    )
    domain_reading = domain_service.generate(
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    domain_graph = MingliReadingClaimGraphProjector().project(
        domain_reading,
        packet=packet,
    )
    career_claim = next(
        item for item in domain_graph.claims if item.semantic_key == "DOMAIN_CAREER"
    )
    assert len(domain_memory.values) == 1
    assert career_claim.status == "WITHHELD"
    assert set(career_claim.assessment_codes) == {
        "NATAL_CLAIM_CITES_TIMING_EVIDENCE",
        "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT",
    }

    field_bypass = _valid_output(packet=packet).model_dump(mode="json")
    field_bypass["timing"]["dayun"]["relation_evidence_ids"] = []
    field_memory = _MemoryStore()
    field_service = MingliAgentService(
        engine,
        runtime=MingliAgentRuntime(
            provider=_OutputProvider(
                MingliAgentModelOutput.model_validate(field_bypass)
            ),
            enabled=True,
        ),
        store=field_memory,  # type: ignore[arg-type]
    )
    with pytest.raises(
        MingliAgentServiceError,
        match="relation_evidence_field_mismatch",
    ):
        field_service.generate(
            requester_account_ref=fixture["owner_account_ref"],
            case_ref=fixture["case_ref"],
            expected_reading_ref=fixture["reading_ref"],
            expected_reading_hash=fixture["reading_hash"],
        )
    assert field_memory.values == {}


def test_unqualified_candidate_can_generate_private_review_without_publication() -> None:
    enabled_settings = replace(settings, mingli_agent_enabled=True)
    assert (
        mingli_agent_runtime_status(enabled_settings).value
        == "READY_FOR_OWNER_REVIEW"
    )
    assert configured_mingli_agent_runtime(enabled_settings).ready is True
    manifest = mingli_agent_runtime_manifest(enabled_settings)
    assert manifest["model_qualification_status"] == (
        "GEMMA4_PRODUCT_CANDIDATE_REQUIRES_OWNER_REVIEW"
    )
    assert manifest["reasoning_mode"] == "BLIND_READING"
    assert manifest["owner_review_allowed"] is True
    assert manifest["publication_allowed"] is False
    assert manifest["network_calls_enabled"] is True

    fixture = _base_reading_fixture()
    summary_service = MingliReadingSummaryService(engine)

    class ReviewAgentStore:
        def latest(self, **_: object):
            return _envelope(fixture)

    summary_service._agent_readings = ReviewAgentStore()  # type: ignore[assignment]
    summary = summary_service.project(
        account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
    )
    assert summary.agent_status == "READY"
    assert summary.agent_projection_scope == "OWNER_REVIEW"
    assert summary.agent_reading is not None
    assert summary.claim_graph is not None
    assert summary.claim_graph.public_projection_allowed is False
    assert summary.professional_verdict_allowed is False

    summary_service._agent_runtime_manifest = {
        **summary_service._agent_runtime_manifest,
        "status": "READY",
        "publication_allowed": True,
        "owner_review_allowed": False,
    }
    with pytest.raises(
        ValueError,
        match="unqualified_graph_cannot_be_public",
    ):
        summary_service.project(
            account_ref=fixture["owner_account_ref"],
            case_ref=fixture["case_ref"],
        )


def test_service_calls_one_agent_once_and_replays_by_generation_key() -> None:
    fixture = _base_reading_fixture()
    provider = _FakeProvider()
    memory = _MemoryStore()
    service = MingliAgentService(
        engine,
        runtime=MingliAgentRuntime(provider=provider, enabled=True),
        store=memory,  # type: ignore[arg-type]
    )

    first = service.generate(
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    replay = service.generate(
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )

    assert replay == first
    assert provider.calls == 1
    assert len(memory.values) == 1
    assert first.reading_ref == fixture["reading_ref"]
    assert first.canonical_fact_write_allowed is False


def test_service_rejects_unrelated_account_before_agent_call() -> None:
    fixture = _base_reading_fixture()
    provider = _FakeProvider()
    service = MingliAgentService(
        engine,
        runtime=MingliAgentRuntime(provider=provider, enabled=True),
        store=_MemoryStore(),  # type: ignore[arg-type]
    )
    with pytest.raises(MingliAgentServiceError, match="case_not_found"):
        service.generate(
            requester_account_ref=_unrelated_account_ref(
                fixture["owner_account_ref"]
            ),
            case_ref=fixture["case_ref"],
            expected_reading_ref=fixture["reading_ref"],
            expected_reading_hash=fixture["reading_hash"],
        )
    assert provider.calls == 0


def _envelope(fixture: dict[str, str], *, suffix: str = "", packet: Any | None = None):
    if packet is None:
        _, packet = _packet()
    packet_ref = packet.packet_ref
    packet_hash = packet.packet_hash
    agent_profile_ref = "v60-test-agent-profile-001"
    agent_profile_hash = "d" * 64
    provider_profile_ref = "v60-test-provider-profile-001"
    provider_profile_hash = "e" * 64
    prompt_ref = "v60-test-agent-prompt-001"
    prompt_hash = "f" * 64
    generation_key = mingli_agent_generation_key(
        requester_account_ref=fixture["owner_account_ref"],
        reading_ref=fixture["reading_ref"],
        reading_hash=fixture["reading_hash"],
        packet_ref=packet_ref,
        packet_hash=packet_hash,
        agent_profile_ref=agent_profile_ref,
        agent_profile_hash=agent_profile_hash,
        provider_profile_ref=provider_profile_ref,
        provider_profile_hash=provider_profile_hash,
        prompt_ref=prompt_ref,
        prompt_hash=prompt_hash,
    )
    return MingliAgentReadingEnvelope.issue(
        generation_key=generation_key,
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        chart_version_ref=fixture["chart_version_ref"],
        life_case_revision_ref=fixture["life_case_revision_ref"],
        reading_ref=fixture["reading_ref"],
        reading_hash=fixture["reading_hash"],
        packet_ref=packet_ref,
        packet_hash=packet_hash,
        agent_profile_ref=agent_profile_ref,
        agent_profile_hash=agent_profile_hash,
        provider_id="test-provider",
        model_ref="test-model",
        model_digest="1" * 64,
        provider_profile_ref=provider_profile_ref,
        provider_profile_hash=provider_profile_hash,
        prompt_ref=prompt_ref,
        prompt_hash=prompt_hash,
        provider_response_ref=f"test-provider-response{suffix}",
        output=_valid_output(suffix=suffix, packet=packet),
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        duration_ms=40,
    )


def test_agent_reading_projects_one_deterministic_shared_claim_graph() -> None:
    fixture = _base_reading_fixture()
    _, packet = _packet()
    reading = _envelope(fixture, packet=packet)
    projector = MingliReadingClaimGraphProjector()

    first = projector.project(reading, packet=packet)
    replay = projector.project(reading, packet=packet)

    assert replay == first
    assert first.reasoning_mode == "BLIND_READING"
    assert first.reconciliation_status == "NOT_ADMITTED"
    assert first.qualification_status == "OWNER_REVIEW_REQUIRED"
    assert first.owner_review_projection_allowed is True
    assert first.public_projection_allowed is False
    assert first.canonical_fact_write_allowed is False
    assert len(first.claims) == 15
    assert tuple(item.semantic_key for item in first.claims) == (
        "WHOLE_CHART",
        "DAY_MASTER",
        "HYPOTHESIS_H1",
        "HYPOTHESIS_H2",
        "WORK_PATH",
        "LIFE_IMAGE",
        "DOMAIN_PERSONALITY",
        "DOMAIN_CAREER",
        "DOMAIN_WEALTH",
        "DOMAIN_RELATIONSHIP",
        "DOMAIN_FAMILY",
        "TIMING_NATAL",
        "TIMING_DAYUN",
        "TIMING_ANNUAL",
        "DISCRIMINATING_QUESTION",
    )
    by_key = {item.semantic_key: item for item in first.claims}
    assert by_key["WHOLE_CHART"].headline == reading.output.first_look
    assert by_key["WHOLE_CHART"].statement == reading.output.whole_chart_thesis
    assert by_key["LIFE_IMAGE"].statement == reading.output.life_image.explanation
    assert by_key["DOMAIN_CAREER"].statement == reading.output.domains.career.conclusion
    assert by_key["TIMING_DAYUN"].statement == reading.output.timing.dayun.conclusion
    assert by_key["TIMING_ANNUAL"].statement == reading.output.timing.annual.conclusion
    assert (
        by_key["DISCRIMINATING_QUESTION"].statement
        == reading.output.discriminating_question
    )
    assert by_key["HYPOTHESIS_H1"].status == "NEEDS_RECONCILIATION"
    assert by_key["HYPOTHESIS_H2"].status == "NEEDS_RECONCILIATION"
    assert by_key["HYPOTHESIS_H2"].assessment_codes == (
        "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
    )
    assert by_key["HYPOTHESIS_H1"].mechanism_evidence_ids
    assert (
        by_key["TIMING_DAYUN"].coordinate_evidence_id
        in by_key["TIMING_DAYUN"].evidence_ids
    )
    assert {item.relation for item in first.edges} == {
        "SUPPORTS",
        "COMPETES_WITH",
        "PROJECTS_TO",
        "TEMPORALLY_EXTENDS",
        "DISCRIMINATES",
    }


def test_condition_field_cannot_launder_unconditional_relation_effect() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["career"]["conclusion"] = (
        "六合已经合动全盘，并决定事业路径稳定兑现。"
    )
    output["domains"]["career"]["condition"] = (
        "若外部职责变化，再观察收入节奏。"
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    career = next(
        item for item in graph.claims if item.semantic_key == "DOMAIN_CAREER"
    )

    assert career.status == "WITHHELD"
    assert "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT" in career.assessment_codes


def test_timing_natal_cannot_use_current_dayun_to_rewrite_natal_chart() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["timing"]["natal_baseline"] = (
        "当前大运进入以后直接改变原局结构，所以日主已经明确偏强。"
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    natal = next(
        item for item in graph.claims if item.semantic_key == "TIMING_NATAL"
    )

    assert natal.status == "WITHHELD"
    assert natal.assessment_codes == ("NATAL_CLAIM_USES_SELECTED_TIMING",)


def test_owner_gemma4_reading_has_exact_evidence_and_dependency_admission() -> None:
    fixture, packet = _packet()
    frozen_output = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / "owner_gemma4_agent_reading_010.json"
        ).read_text(encoding="utf-8")
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(
            MingliAgentModelOutput.model_validate(frozen_output)
        ),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}
    statuses = {key: item.status for key, item in by_key.items()}

    assert statuses == {
        "WHOLE_CHART": "NEEDS_RECONCILIATION",
        "DAY_MASTER": "PROVISIONAL",
        "HYPOTHESIS_H1": "NEEDS_RECONCILIATION",
        "HYPOTHESIS_H2": "NEEDS_RECONCILIATION",
        "WORK_PATH": "WITHHELD",
        "LIFE_IMAGE": "PROVISIONAL",
        "DOMAIN_PERSONALITY": "NEEDS_RECONCILIATION",
        "DOMAIN_CAREER": "WITHHELD",
        "DOMAIN_WEALTH": "NEEDS_RECONCILIATION",
        "DOMAIN_RELATIONSHIP": "WITHHELD",
        "DOMAIN_FAMILY": "WITHHELD",
        "TIMING_NATAL": "NEEDS_RECONCILIATION",
        "TIMING_DAYUN": "WITHHELD",
        "TIMING_ANNUAL": "NEEDS_RECONCILIATION",
        "DISCRIMINATING_QUESTION": "OPEN_QUESTION",
    }
    assert by_key["HYPOTHESIS_H1"].mechanism_evidence_ids == ("E009",)
    assert by_key["HYPOTHESIS_H1"].confidence == "MEDIUM"
    assert by_key["TIMING_DAYUN"].coordinate_evidence_id == "E011"
    assert by_key["TIMING_ANNUAL"].coordinate_evidence_id == "E012"
    assert "E012" in by_key["TIMING_ANNUAL"].evidence_ids
    assert by_key["DISCRIMINATING_QUESTION"].statement == (
        frozen_output["discriminating_question"]
    )
    assert "DEPENDENCY_WITHHELD" in by_key["WHOLE_CHART"].assessment_codes
    withheld_refs = {
        item.claim_ref for item in graph.claims if item.status == "WITHHELD"
    }
    assert all(
        edge.source_claim_ref not in withheld_refs
        and edge.target_claim_ref not in withheld_refs
        for edge in graph.edges
    )


def test_local_fact_overreach_quarantines_claim_not_whole_reading() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["career"]["causal_chain"] = [
        "日主坐支根气受制，且酉、藏庚形成持续压力。"
    ]
    output["domains"]["family"]["conclusion"] = (
        "丑土作为财库，使家庭责任天然围绕物质积累展开。"
    )
    output["domains"]["relationship"]["causal_chain"] = [
        "日支丑土与月令巳火相连，因此关系更重实际行动。"
    ]
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["WHOLE_CHART"].status == "NEEDS_RECONCILIATION"
    assert by_key["DOMAIN_CAREER"].status == "WITHHELD"
    assert set(by_key["DOMAIN_CAREER"].assessment_codes) == {
        "ROOT_ASSERTION_CONFLICTS_WITH_PACKET",
        "NAMED_COORDINATE_CONFLICTS_WITH_PACKET",
    }
    assert by_key["DOMAIN_FAMILY"].assessment_codes == (
        "UNADMITTED_CLASSICAL_ASSERTION",
    )
    assert by_key["DOMAIN_RELATIONSHIP"].assessment_codes == (
        "UNLISTED_RELATION_COORDINATE_ASSERTION",
    )


def test_many_local_overreaches_cannot_break_the_claim_graph() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    relation_evidence_id = next(
        item.evidence_id
        for item in packet.timing_relations
        if item.left_layer == "DAYUN"
    )
    output["domains"]["career"]["conclusion"] = (
        "大运庚子使根气受制，酉、藏庚与丑土财库、巳火相连，"
        "六合已经合动并导致车祸。"
    )
    output["domains"]["career"]["evidence_ids"].append(
        relation_evidence_id
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["WHOLE_CHART"].status == "NEEDS_RECONCILIATION"
    assert by_key["DOMAIN_CAREER"].status == "WITHHELD"
    assert len(by_key["DOMAIN_CAREER"].assessment_codes) >= 7
def test_store_is_append_only_private_and_first_generation_wins() -> None:
    fixture = _base_reading_fixture()
    first = _envelope(fixture)
    competing_retry = _envelope(fixture, suffix="重试")
    connection = engine.connect()
    transaction = connection.begin()
    try:
        store = MingliAgentReadingStore(  # type: ignore[arg-type]
            _TransactionalEngine(connection)
        )
        stored = store.ensure(first)
        replay = store.ensure(competing_retry)

        assert stored == replay
        assert store.find_generation(
            requester_account_ref=fixture["owner_account_ref"],
            generation_key=first.generation_key,
        ) == first
        assert store.find_generation(
            requester_account_ref=_unrelated_account_ref(
                fixture["owner_account_ref"]
            ),
            generation_key=first.generation_key,
        ) is None
        with pytest.raises(DBAPIError, match="append_only"):
            connection.execute(
                text(
                    """
                    UPDATE mingli.agent_readings SET duration_ms = duration_ms + 1
                    WHERE agent_reading_ref = :agent_reading_ref
                    """
                ),
                {"agent_reading_ref": first.agent_reading_ref},
            )
    finally:
        transaction.rollback()
        connection.close()


def test_api_uses_session_identity_and_maps_runtime_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _base_reading_fixture()
    envelope = _envelope(fixture)
    calls: list[dict[str, str]] = []

    class Service:
        def generate(self, **values: str):
            calls.append(values)
            return envelope

    monkeypatch.setattr(mingli_stage, "agent_readings", Service())
    response = Response()
    request = mingli_stage.MingliAgentReadingRequest(
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    session = SimpleNamespace(
        account=SimpleNamespace(account_ref=fixture["owner_account_ref"])
    )

    payload = mingli_stage.generate_agent_reading(  # type: ignore[arg-type]
        request,
        response,
        session,
    )

    assert payload["agent_reading_ref"] == envelope.agent_reading_ref
    assert calls[0]["requester_account_ref"] == fixture["owner_account_ref"]
    assert response.headers["Cache-Control"] == "private, no-store"

    class Unavailable:
        def generate(self, **_: str):
            raise MingliAgentServiceError("mingli_agent_runtime_not_ready")

    monkeypatch.setattr(mingli_stage, "agent_readings", Unavailable())
    with pytest.raises(HTTPException) as caught:
        mingli_stage.generate_agent_reading(  # type: ignore[arg-type]
            request,
            Response(),
            session,
        )
    assert caught.value.status_code == 503
