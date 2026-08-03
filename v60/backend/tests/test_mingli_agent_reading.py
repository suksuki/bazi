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
    mingli_agent_generation_output_schema,
)
from abu_v60.mingli.agent_method_cards import (
    FALLBACK_METHOD_CARD_REF,
    fallback_hypothesis_method_card,
    mechanism_method_card,
    method_card_catalog,
)
from abu_v60.mingli.agent_method_distillation import exact_role_paths
from abu_v60.mingli.agent_normalization_receipt import (
    MingliAgentNormalizationReceipt,
)
from abu_v60.mingli.agent_output_copy import repair_output_form
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.agent_profile import (
    MINGLI_AGENT_PROFILE_HASH,
    MINGLI_AGENT_PROFILE_REF,
    MINGLI_AGENT_PROMPT_HASH,
    MINGLI_AGENT_PROMPT_REF,
)
from abu_v60.mingli.agent_reasoning_modes import (
    BLIND_READING_CONTRACT,
    RECONCILIATION_CONTRACT,
)
from abu_v60.mingli.agent_runtime import (
    MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS,
    MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS,
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
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.settings import settings
from fastapi import HTTPException, Response
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def test_copy_repair_preserves_excluded_candidate_status_enum() -> None:
    repaired = repair_output_form(
        {
            "excluded_candidates": [
                {
                    "status": "UNRESOLVED",
                    "rationale": "UNRESOLVED：这条候选还需要整盘比较。",
                }
            ]
        }
    )

    assert repaired["excluded_candidates"][0]["status"] == "UNRESOLVED"
    assert repaired["excluded_candidates"][0]["rationale"] == (
        "这条候选还需要整盘比较。"
    )


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
        cards = {
            FALLBACK_METHOD_CARD_REF: fallback_hypothesis_method_card(),
        }
    else:
        roots = packet.day_master_support.same_element_hidden_support
        peers = packet.day_master_support.visible_peer_support
        resources = packet.day_master_support.resource_support
        base_evidence = (
            packet.pillars[1].evidence_id,
            packet.day_master_support.evidence_id,
        )
        mechanism_ids = tuple(item.evidence_id for item in packet.mechanism_observations)
        coordinates = {item.layer: item.evidence_id for item in packet.timing_coordinates}
        dayun_coordinate = coordinates["DAYUN"]
        annual_coordinate = coordinates["ANNUAL"]
        dayun_relations = tuple(
            item.evidence_id for item in packet.timing_relations if item.left_layer == "DAYUN"
        )
        annual_relations = tuple(
            item.evidence_id for item in packet.timing_relations if item.left_layer == "ANNUAL"
        )
        cards = method_card_catalog(packet.mechanism_observations)
    card_refs = (
        mechanism_ids[0] if mechanism_ids else FALLBACK_METHOD_CARD_REF,
        mechanism_ids[1] if len(mechanism_ids) > 1 else FALLBACK_METHOD_CARD_REF,
    )

    def exact_path_copy(card_ref: str, *, fallback_name: str) -> tuple[str, str]:
        if packet is None or card_ref == FALLBACK_METHOD_CARD_REF:
            return fallback_name, (
                f"{fallback_name}需要比较月令、透藏和整盘承接后才可作为工作解释。"
            )
        observation = next(
            item for item in packet.mechanism_observations if item.evidence_id == card_ref
        )
        occurrences: dict[str, list[str]] = {}
        for pillar in packet.pillars:
            occurrences.setdefault(pillar.visible_ten_god, []).append(
                f"{pillar.slot}干{pillar.stem}"
            )
            for hidden_stem, ten_god in zip(
                pillar.hidden_stems,
                pillar.hidden_ten_gods,
                strict=True,
            ):
                occurrences.setdefault(ten_god, []).append(
                    f"{pillar.slot}支藏{hidden_stem}"
                )
        paths = exact_role_paths(observation.pattern_ref, occurrences)
        if not paths:
            name = observation.label.removesuffix("候选")[:48]
            return name, f"{name}需要比较月令、透藏和整盘承接后才可作为工作解释。"
        path = paths[0]
        source = str(path["source"]["ten_god"])
        target = str(path["target"]["ten_god"])
        name = f"{source}到{target}路径"
        return name, f"暂以{source}能否作用于{target}作为本候选的具体工作解释。"

    h1_name, h1_thesis = exact_path_copy(card_refs[0], fallback_name="主结构承接")
    h2_name, h2_thesis = exact_path_copy(card_refs[1], fallback_name="局部力量主导")

    def method_rulings(card_ref: str) -> list[dict[str, object]]:
        evidence_id = base_evidence[0] if card_ref == FALLBACK_METHOD_CARD_REF else card_ref
        return [
            {
                "method_card_ref": card_ref,
                "check_code": check_code,
                "ruling": "CONDITIONAL",
                "rationale": "当前命盘位置支持这条路径，但仍要结合整盘承载判断。",
                "condition_or_falsifier": "若该位置长期不能形成对应结果，这一项需要重判。",
                "evidence_ids": [evidence_id],
            }
            for check_code in cards[card_ref]["required_checks"]
        ]

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
                "命局的主结构使这个领域先经过辨别与组织，再形成稳定行动，环境配合时表现得更集中。"
            ),
            "causal_chain": ["结构形成注意方向并进入现实选择"],
            "condition": "职责清楚并允许持续积累",
            "evidence_ids": (*base_evidence, *mechanism_ids[:1]),
            "confidence": "MEDIUM",
        }
    return MingliAgentModelOutput.model_validate(
        {
            "first_look": f"这是一张力量集中而转化路径鲜明的命局{suffix}",
            "whole_chart_thesis": (
                "全盘的关键不在单个五行多少，而在月令、透藏与各柱之间能否"
                "把分散力量导向同一条可持续的转化路径。"
            ),
            "regime_decision": {
                "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
                "classification": "NON_WEAK_OUTSIDE_SCOPE",
                "effective_root_status": "UNRESOLVED" if roots else "ABSENT",
                "effective_root_coordinates": [],
                "rooted_visible_support_status": "ABSENT",
                "dominant_chain_status": "UNRESOLVED",
                "competition_kinds": [
                    *(["VISIBLE_PEER"] if peers else []),
                    *(["HIDDEN_RESOURCE"] if resources else []),
                ],
                "evidence_ids": [base_evidence[-1]],
            },
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
                    "name": h1_name,
                    "judgment": "WORKS_IF",
                    "mechanism_evidence_ids": mechanism_ids[:1],
                    "method_card_ref": card_refs[0],
                    "method_rulings": method_rulings(card_refs[0]),
                    "adjudication": "CONDITIONAL",
                    "thesis": h1_thesis,
                    "failure_condition": "关键转化被持续截断时不成立",
                    "evidence_ids": (*base_evidence, *mechanism_ids[:1]),
                    "confidence": "MEDIUM",
                },
                {
                    "hypothesis_id": "H2",
                    "role": "ALTERNATIVE",
                    "name": h2_name,
                    "judgment": "PARTIAL",
                    "mechanism_evidence_ids": mechanism_ids[1:2],
                    "method_card_ref": card_refs[1],
                    "method_rulings": method_rulings(card_refs[1]),
                    "adjudication": "CONDITIONAL",
                    "thesis": h2_thesis,
                    "failure_condition": "岁运转向后迅速失去主导",
                    "evidence_ids": (*base_evidence, *mechanism_ids[1:2]),
                    "confidence": "LOW",
                },
            ],
            "excluded_candidates": [
                {
                    "method_card_ref": card_ref,
                    "name": next(
                        item.label
                        for item in packet.mechanism_observations
                        if item.evidence_id == card_ref
                    ),
                    "status": "UNRESOLVED",
                    "decisive_check": cards[card_ref]["required_checks"][0],
                    "rationale": "这条候选尚未进入前两位解释，保留等待进一步比较。",
                    "evidence_ids": [card_ref],
                }
                for card_ref in mechanism_ids[2:]
            ]
            if packet is not None
            else [],
            "hypothesis_decision": {
                "winner_id": "H1",
                "loser_id": "H2",
                "winner": {
                    "rationale": "主解释对月令、透藏和整盘承接的覆盖更完整，因此暂居第一。",
                    "decisive_checks": [cards[card_refs[0]]["required_checks"][0]],
                },
                "loser": {
                    "rationale": "替代解释能说明局部力量，却不能同样完整解释整盘重心。",
                    "decisive_checks": [cards[card_refs[1]]["required_checks"][0]],
                },
                "reversal": {
                    "question": "现实中的任务增加后，成果更集中还是方向更分散？",
                    "winner_signal": "任务越复杂，反而越能收束为一条稳定成果路径。",
                    "loser_signal": "任务越复杂，越容易由局部力量带着方向持续分散。",
                },
            },
            "work_path": {
                "selected_hypothesis_id": "H1",
                "method_card_ref": card_refs[0],
                "path_statement": "力量从月令起步，经由透干组织和现实任务转化，最后落到可重复的成果。",
                "transformation_codes": ["CHANNELS", "GENERATES"],
                "closure": "CONDITIONAL",
                "condition": "任务边界清楚且转化方向一致",
                "evidence_ids": (*base_evidence, *mechanism_ids[:1]),
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
                    "evidence_ids": (
                        *base_evidence,
                        dayun_coordinate,
                        annual_coordinate,
                        *annual_relations,
                    ),
                    "confidence": "MEDIUM",
                },
                "verification_signals": ["职责是否更集中", "成果是否更容易被确认"],
            },
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
        quant_vector=MingliQuantVectorStore(engine).get(vector_ref=str(reading.quant_vector_ref)),
        mechanism_vector=MingliMechanismVectorStore(engine).get(
            vector_ref=str(reading.mechanism_vector_ref)
        ),
        timing_vector=MingliTimingVectorStore(engine).get(
            vector_ref=str(reading.timing_vector_ref)
        ),
    )


def _packet_with_candidate_count(count: int):
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                SELECT c.owner_account_ref, c.case_ref, r.reading_ref, r.reading_hash
                FROM mingli.cases AS c
                JOIN mingli.readings AS r ON r.case_ref = c.case_ref
                JOIN mingli.mechanism_evidence_vectors AS m
                  ON m.vector_ref = r.mechanism_vector_ref
                WHERE jsonb_array_length(m.vector_json -> 'candidates') = :count
                  AND c.status = 'ACTIVE'
                  AND c.subject_kind IN ('HUMAN_OWNER', 'HUMAN_REFERENCE')
                ORDER BY r.created_at DESC
                LIMIT 1
                """
                ),
                {"count": count},
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
    return fixture, MingliAgentCasePacketCompiler().compile(
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
        output = _valid_output(packet=packet)
        provider_response_ref = f"test-response-{packet.packet_hash[:24]}"
        return MingliAgentProviderResult(
            provider_response_ref=provider_response_ref,
            output=output,
            normalization_receipt=_test_normalization_receipt(
                provider=self,
                packet=packet,
                output=output,
                provider_response_ref=provider_response_ref,
            ),
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
        provider_response_ref = f"test-response-{packet.packet_hash[:24]}"
        return MingliAgentProviderResult(
            provider_response_ref=provider_response_ref,
            output=self._output,
            normalization_receipt=_test_normalization_receipt(
                provider=self,
                packet=packet,
                output=self._output,
                provider_response_ref=provider_response_ref,
            ),
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            duration_ms=50,
        )


def _test_normalization_receipt(
    *,
    provider: _FakeProvider,
    packet: Any,
    output: MingliAgentModelOutput,
    provider_response_ref: str,
) -> MingliAgentNormalizationReceipt:
    structured = output.model_dump(mode="json")
    return MingliAgentNormalizationReceipt.issue(
        provider_response_ref=provider_response_ref,
        packet_ref=packet.packet_ref,
        packet_hash=packet.packet_hash,
        agent_profile_ref=MINGLI_AGENT_PROFILE_REF,
        agent_profile_hash=MINGLI_AGENT_PROFILE_HASH,
        provider_id=provider.provider_id,
        model_ref=provider.model_ref,
        model_digest=provider.model_digest,
        provider_profile_ref=provider.provider_profile_ref,
        provider_profile_hash=provider.provider_profile_hash,
        prompt_ref=MINGLI_AGENT_PROMPT_REF,
        prompt_hash=MINGLI_AGENT_PROMPT_HASH,
        raw_output=structured,
        normalized_output=structured,
        changes=(),
        server_issue_keys=output.server_issue_keys,
    )


def _normalize_raw(*, packet: Any, raw: dict[str, Any]) -> MingliAgentModelOutput:
    provider = OllamaMingliAgentProvider(
        model_ref="gemma4:test",
        model_digest="b" * 64,
        provider_profile_ref="v60.test-provider.semantic-normalization",
        base_url="http://private-model.invalid",
        timeout_seconds=3,
        think=False,
        temperature=0,
        top_p=0.95,
        top_k=64,
        num_ctx=32768,
        num_predict=4096,
        keep_alive="30m",
        transport=lambda **_: {
            "response": json.dumps(raw, ensure_ascii=False),
            "prompt_eval_count": 10,
            "eval_count": 20,
        },
    )
    return provider.generate(packet=packet).output


class _MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, MingliAgentReadingEnvelope] = {}

    def find_generation(self, *, requester_account_ref: str, generation_key: str):
        value = self.values.get(generation_key)
        return (
            value
            if value is not None and value.requester_account_ref == requester_account_ref
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


def test_agent_contract_rejects_unknown_evidence_and_localizes_engineering_copy() -> None:
    output = _valid_output()
    output.validate_evidence(frozenset({"E001", "E002", "E003", "E004"}))
    with pytest.raises(ValueError, match="unknown_evidence"):
        output.validate_evidence(frozenset({"E999"}))
    fixture, packet = _packet()
    localized = _valid_output(packet=packet).model_dump(mode="json")
    localized["hypotheses"][0]["method_rulings"][0]["rationale"] = (
        "这份命局尚未接线，稍后再看具体结果。"
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(localized)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)
    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    whole = next(item for item in graph.claims if item.semantic_key == "WHOLE_CHART")
    assert whole.status == "WITHHELD"
    assert "NON_READING_LANGUAGE" in whole.assessment_codes
    assert any(item.status != "WITHHELD" for item in graph.claims)


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
    assert prompt_view["professional_adjudication"]["domain_method_assets"][
        "relationship"
    ]["gender_fact"] == packet.gender
    assert packet.birth_timezone not in serialized
    assert packet.subject_kind not in serialized


def test_generation_schema_requires_non_null_regime_without_breaking_legacy_model() -> None:
    schema = mingli_agent_generation_output_schema()
    regime = schema["properties"]["regime_decision"]
    work_path = schema["$defs"]["AgentWorkPath"]

    assert "regime_decision" in schema["required"]
    assert regime.get("$ref", "").endswith("/$defs/AgentRegimeDecision")
    assert "anyOf" not in regime
    assert {"selected_hypothesis_id", "method_card_ref"}.issubset(
        work_path["required"]
    )
    assert work_path["properties"]["transformation_codes"]["uniqueItems"] is True
    assert MingliAgentModelOutput.model_json_schema()["properties"]["regime_decision"][
        "default"
    ] is None


def test_prompt_view_separates_candidate_acknowledgement_regime_and_timing_scope() -> None:
    _, packet = _packet()
    contract = packet.model_prompt_view()["professional_adjudication"][
        "output_field_contract"
    ]

    assert contract["regime_decision"]["required_non_null"] is True
    assert "NOT_EFFECTIVE_ROOT_RULING" in contract["support_selection"]["meaning"]
    assert contract["work_path"]["evidence_ids_forbidden"]
    assert set(contract["work_path"]["evidence_ids_forbidden"]).isdisjoint(
        contract["work_path"]["evidence_ids_allowed"]
    )


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
    assert (
        len(canonical_json(calls[0]["payload"]["format"]))
        <= MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS
    )
    assert result.total_tokens == 360
    assert result.output.day_master_evidence_ids[0] == "E001"
    assert "E001" not in result.output.domains.career.conclusion
    assert result.output.support_selection.peer_coordinates == (
        packet.day_master_support.visible_peer_support
    )
    assert set(result.output.hypotheses[0].mechanism_evidence_ids).issubset(
        {item.evidence_id for item in packet.mechanism_observations}
    )
    assert result.output.day_master_evidence_ids == (
        *(item.evidence_id for item in packet.pillars),
        packet.day_master_support.evidence_id,
    )
    assert result.output.hypotheses[0].role == "PRIMARY"
    assert result.output.regime_decision is not None
    assert result.output.regime_decision.classification == "NON_WEAK_OUTSIDE_SCOPE"
    receipt = result.normalization_receipt
    assert receipt.raw_output["support_selection"]["peer_coordinates"] == [
        "错误坐标"
    ]
    assert receipt.raw_output_hash == content_hash(receipt.raw_output)
    assert receipt.normalized_output_hash == content_hash(
        result.output.model_dump(mode="json")
    )
    assert receipt.hidden_reasoning_stored is False
    assert receipt.stored_scope == "STRUCTURED_PROVIDER_OUTPUT_ONLY"
    assert {
        (item.stage, item.path)
        for item in receipt.changes
    }.issuperset(
        {
            ("EVIDENCE_ID_NORMALIZATION", "/day_master_evidence_ids"),
            ("PACKET_FACT_BINDING", "/support_selection/peer_coordinates"),
        }
    )


def test_ollama_adapter_maps_non_object_json_to_provider_error() -> None:
    _, packet = _packet()
    provider = OllamaMingliAgentProvider(
        model_ref="gemma4:test",
        model_digest="b" * 64,
        provider_profile_ref="v60.test-provider.non-object",
        base_url="http://private-model.invalid",
        timeout_seconds=3,
        think=False,
        temperature=0,
        top_p=0.95,
        top_k=64,
        num_ctx=32768,
        num_predict=4096,
        keep_alive="30m",
        transport=lambda **_: {
            "response": "[]",
            "prompt_eval_count": 1,
            "eval_count": 1,
        },
    )

    with pytest.raises(MingliAgentProviderError, match="output_not_object"):
        provider.generate(packet=packet)


def test_ollama_adapter_repairs_partial_rulings_and_timing_scope() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    first = raw["hypotheses"][0]["method_rulings"][0]
    first.update(
        {
            "ruling": "SUPPORTS",
            "rationale": "财星戊土己土都在原局透出，所以来源一定可用。",
            "condition_or_falsifier": "BAD",
            "evidence_ids": [packet.timing_coordinates[1].evidence_id],
        }
    )
    raw["hypotheses"][0]["method_rulings"] = [
        first,
        {
            **first,
            "check_code": "UNKNOWN_EXTRA_CHECK",
        },
    ]
    raw["hypothesis_decision"]["winner"]["decisive_checks"] = ["H1"]
    raw["work_path"]["closure"] = "CLOSED"
    raw["domains"]["wealth"]["evidence_ids"] = ["E020"]
    raw["life_image"].update(
        {
            "title": "知识工作者模型",
            "image": "一位知识分子在专业工坊里持续输出技能。",
            "explanation": "这是把职业框架误当成生命意象的无效示例，需要服务端修复。",
        }
    )
    dayun_relation = next(
        item.evidence_id for item in packet.timing_relations if item.left_layer == "DAYUN"
    )
    raw["timing"]["dayun"]["coordinate_evidence_id"] = "E999"
    raw["timing"]["dayun"]["relation_evidence_ids"] = [dayun_relation]
    raw["timing"]["dayun"]["evidence_ids"] = [packet.timing_coordinates[1].evidence_id]

    def transport(**_: Any) -> dict[str, Any]:
        return {
            "response": json.dumps(raw, ensure_ascii=False),
            "prompt_eval_count": 10,
            "eval_count": 20,
        }

    provider = OllamaMingliAgentProvider(
        model_ref="gemma4:test",
        model_digest="b" * 64,
        provider_profile_ref="v60.test-provider.002",
        base_url="http://private-model.invalid",
        timeout_seconds=3,
        think=False,
        temperature=0,
        top_p=0.95,
        top_k=64,
        num_ctx=32768,
        num_predict=4096,
        keep_alive="30m",
        transport=transport,
    )
    result = provider.generate(packet=packet)
    primary = next(item for item in result.output.hypotheses if item.role == "PRIMARY")
    repaired = next(item for item in result.output.hypotheses if item.hypothesis_id == "H1")
    expected_checks = method_card_catalog(packet.mechanism_observations)[repaired.method_card_ref][
        "required_checks"
    ]

    assert primary.hypothesis_id == "H1"
    assert primary.confidence == "LOW"
    assert tuple(item.check_code for item in repaired.method_rulings) == expected_checks
    assert repaired.method_rulings[0].ruling == "UNRESOLVED"
    assert repaired.method_rulings[0].evidence_ids == ()
    assert result.output.work_path.selected_hypothesis_id == "H1"
    assert result.output.work_path.method_card_ref == repaired.method_card_ref
    assert result.output.work_path.closure == "UNCERTAIN"
    assert {"HYPOTHESIS_H1", "HYPOTHESIS_DECISION"}.issubset(
        result.output.server_issue_keys
    )
    assert result.output.timing.dayun.coordinate_evidence_id == (
        packet.timing_coordinates[0].evidence_id
    )
    assert result.output.timing.dayun.relation_evidence_ids == (dayun_relation,)
    assert packet.timing_coordinates[1].evidence_id not in (result.output.timing.dayun.evidence_ids)
    assert result.output.domains.wealth.evidence_ids == ()
    assert "DOMAIN_WEALTH" in result.output.server_issue_keys
    assert result.output.life_image.title == "盛夏旷野里的柔韧藤木"
    assert "地支同类根0处" in result.output.life_image.explanation


def test_ollama_adapter_preserves_reversed_valid_candidate_identity() -> None:
    fixture, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    pressure_ref, wealth_ref = (
        item.evidence_id for item in packet.mechanism_observations[:2]
    )
    pressure, wealth = raw["hypotheses"]
    raw["hypotheses"] = [wealth, pressure]
    wealth.update(
        {
            "hypothesis_id": "H1",
            "role": "PRIMARY",
            "name": "食伤生财条件主线",
            "judgment": "WORKS_IF",
            "confidence": "MEDIUM",
        }
    )
    pressure.update(
        {
            "hypothesis_id": "H2",
            "role": "ALTERNATIVE",
            "name": "食伤制杀受阻线",
            "judgment": "BLOCKED",
            "adjudication": "BROKEN",
            "confidence": "LOW",
        }
    )
    reachability = next(
        item
        for item in pressure["method_rulings"]
        if item["check_code"] == "VISIBLE_HIDDEN_REACHABILITY"
    )
    reachability.update(
        {
            "ruling": "OPPOSES",
            "rationale": "官杀全部藏而未透，不能证明食伤已经直接制到压力目标。",
        }
    )
    raw["hypothesis_decision"].update(
        {
            "winner_id": "H1",
            "loser_id": "H2",
            "reversal": {
                "question": "成果更常形成明确价值，还是更常用于处理规则压力？",
                "winner_signal": "成果稳定进入定价和回报环节，维持食伤生财主线。",
                "loser_signal": "输出长期直接降低规则压力，食伤制杀才可能翻盘。",
            },
        }
    )
    raw["work_path"]["evidence_ids"] = [
        wealth_ref if item == pressure_ref else item
        for item in raw["work_path"]["evidence_ids"]
    ]
    for domain in raw["domains"].values():
        domain["evidence_ids"] = [
            wealth_ref if item == pressure_ref else item for item in domain["evidence_ids"]
        ]

    output = _normalize_raw(packet=packet, raw=raw)
    first, second = output.hypotheses

    assert first.method_card_ref == wealth_ref
    assert first.name == "食伤生财条件主线"
    assert first.role == "PRIMARY"
    assert tuple(item.check_code for item in first.method_rulings) == tuple(
        method_card_catalog(packet.mechanism_observations)[wealth_ref]["required_checks"]
    )
    assert all(item.method_card_ref == wealth_ref for item in first.method_rulings)
    assert second.method_card_ref == pressure_ref
    assert second.name == "食伤制杀受阻线"
    assert second.role == "ALTERNATIVE"
    assert second.adjudication == "BROKEN"
    assert output.hypothesis_decision.winner_id == "H1"
    assert "食伤生财" in output.hypothesis_decision.reversal.winner_signal
    assert "食伤制杀" in output.hypothesis_decision.reversal.loser_signal
    assert "HYPOTHESIS_H1" not in output.server_issue_keys
    assert "HYPOTHESIS_H2" not in output.server_issue_keys

    reading = MingliAgentRuntime(
        provider=_OutputProvider(output),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)
    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}
    assert by_key["WHOLE_CHART"].headline == "食伤生财条件主线"
    assert by_key["HYPOTHESIS_H1"].mechanism_evidence_ids == (wealth_ref,)
    assert by_key["HYPOTHESIS_H2"].mechanism_evidence_ids == (pressure_ref,)
    for semantic_key in (
        "DOMAIN_PERSONALITY",
        "DOMAIN_CAREER",
        "DOMAIN_WEALTH",
        "DOMAIN_RELATIONSHIP",
        "DOMAIN_FAMILY",
    ):
        assert "DOMAIN_PRIMARY_PATH_MISSING" not in by_key[semantic_key].assessment_codes


def test_no_root_weak_regime_caps_mechanism_capacity_at_conditional() -> None:
    _, packet = _packet()
    assert packet.day_master_support.same_element_hidden_support == ()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "WEAK"
    for hypothesis in raw["hypotheses"]:
        capacity = next(
            item
            for item in hypothesis["method_rulings"]
            if item["check_code"] == "DAY_MASTER_CAPACITY"
        )
        capacity.update(
            {
                "ruling": "SUPPORTS",
                "rationale": "两处浮透比肩能够持续帮身，所以日主足以承担全部泄耗。",
            }
        )

    output = _normalize_raw(packet=packet, raw=raw)

    for hypothesis in output.hypotheses:
        capacity = next(
            item
            for item in hypothesis.method_rulings
            if item.check_code == "DAY_MASTER_CAPACITY"
        )
        assert capacity.ruling == "CONDITIONAL"
        assert "日主无根" in capacity.rationale
    assert {"DAY_MASTER_CAPACITY_H1", "DAY_MASTER_CAPACITY_H2"}.issubset(
        output.server_issue_keys
    )


def test_server_preserves_valid_model_primary_instead_of_counting_card_checks() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    pressure, wealth = raw["hypotheses"]
    pressure_values = {
        "OUTPUT_SOURCE_AVAILABILITY": "SUPPORTS",
        "OFFICIAL_KILLING_ROLE_POSITIONED": "SUPPORTS",
        "DAY_MASTER_CAPACITY": "CONDITIONAL",
        "VISIBLE_HIDDEN_REACHABILITY": "CONDITIONAL",
        "RESOURCE_OR_OTHER_BLOCKER_RESOLUTION": "SUPPORTS",
        "SOURCE_AND_TARGET_SAME_LAYER": "UNRESOLVED",
    }
    wealth_values = {
        "OUTPUT_SOURCE_AVAILABILITY": "SUPPORTS",
        "WEALTH_TARGET_REACHABILITY": "CONDITIONAL",
        "DAY_MASTER_CAPACITY": "CONDITIONAL",
        "RESOURCE_SUPPRESSION_RESOLUTION": "SUPPORTS",
        "PEER_COMPETITION_RESOLUTION": "CONDITIONAL",
    }
    for ruling in pressure["method_rulings"]:
        ruling["ruling"] = pressure_values[ruling["check_code"]]
    for ruling in wealth["method_rulings"]:
        ruling["ruling"] = wealth_values[ruling["check_code"]]

    output = _normalize_raw(packet=packet, raw=raw)
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")

    assert primary.method_card_ref == pressure["method_card_ref"]
    assert "食神到七杀" in primary.name
    assert output.work_path.method_card_ref == primary.method_card_ref


def test_following_tendency_retreats_when_peer_or_resource_competition_exists() -> None:
    _, packet = _packet()
    assert (
        packet.day_master_support.visible_peer_support
        or packet.day_master_support.resource_support
    )
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "FOLLOWING_TENDENCY"
    raw["day_master_rationale"] = "日主无根，所以已经可以直接顺从异类力量形成从势。"
    raw["regime_decision"]["dominant_chain_status"] = "CLOSED"
    raw["regime_decision"]["classification"] = "FALSE_FOLLOW_COMPETITION"

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.day_master_state == "UNCERTAIN"
    assert output.regime_decision is not None
    assert output.regime_decision.classification == "FALSE_FOLLOW_COMPETITION"
    assert "浮比、藏印或未决组合" in output.day_master_rationale
    assert "DAY_MASTER_REGIME" in output.server_issue_keys


def test_regime_rejects_invented_effective_root_coordinate() -> None:
    _, packet = _packet_with_candidate_count(1)
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "WEAK"
    raw["regime_decision"].update(
        {
            "classification": "ORDINARY_WEAK",
            "effective_root_status": "PRESENT",
            "effective_root_coordinates": ["hour支藏甲-虚构"],
            "dominant_chain_status": "CLOSED",
        }
    )

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.regime_decision is not None
    assert output.regime_decision.effective_root_status == "UNRESOLVED"
    assert output.regime_decision.effective_root_coordinates == ()
    assert output.regime_decision.classification == "UNRESOLVED"
    assert "DAY_MASTER_REGIME" in output.server_issue_keys


def test_candidate_root_without_invalidation_stays_unresolved_and_caps_capacity() -> None:
    _, packet = _packet_with_candidate_count(1)
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "WEAK"
    raw["regime_decision"].update(
        {
            "classification": "FALSE_FOLLOW_COMPETITION",
            "effective_root_status": "ABSENT",
            "effective_root_coordinates": [],
            "dominant_chain_status": "CLOSED",
        }
    )
    for hypothesis in raw["hypotheses"]:
        for capacity in (
            item
            for item in hypothesis["method_rulings"]
            if item["check_code"] == "DAY_MASTER_CAPACITY"
        ):
            capacity["ruling"] = "SUPPORTS"

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.regime_decision is not None
    assert output.regime_decision.effective_root_status == "UNRESOLVED"
    assert output.regime_decision.classification == "UNRESOLVED"
    capacities = tuple(
        item
        for hypothesis in output.hypotheses
        for item in hypothesis.method_rulings
        if item.check_code == "DAY_MASTER_CAPACITY"
    )
    assert capacities
    for capacity in capacities:
        assert capacity.ruling == "CONDITIONAL"


def test_open_dominant_chain_cannot_be_normalized_to_follow_trend() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "FOLLOWING_TENDENCY"
    raw["regime_decision"].update(
        {
            "classification": "FOLLOW_TREND",
            "dominant_chain_status": "OPEN",
        }
    )

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.regime_decision is not None
    assert output.regime_decision.classification == "UNRESOLVED"
    assert output.day_master_state == "UNCERTAIN"


def test_candidate_allocator_reserves_later_valid_ref_before_repairing_invalid_first() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    pressure_ref, wealth_ref = (
        item.evidence_id for item in packet.mechanism_observations[:2]
    )
    pressure, wealth = raw["hypotheses"]
    raw["hypotheses"] = [wealth, pressure]
    raw["hypotheses"][0].update(
        {
            "hypothesis_id": "H1",
            "method_card_ref": "INVALID_METHOD_CARD",
            "mechanism_evidence_ids": [],
        }
    )
    raw["hypotheses"][1].update(
        {
            "hypothesis_id": "H2",
            "method_card_ref": pressure_ref,
            "mechanism_evidence_ids": [pressure_ref],
        }
    )

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.hypotheses[0].method_card_ref == wealth_ref
    assert output.hypotheses[1].method_card_ref == pressure_ref
    assert output.hypotheses[1].name == _valid_output(packet=packet).hypotheses[0].name
    assert "HYPOTHESIS_H1" in output.server_issue_keys
    assert "HYPOTHESIS_H2" not in output.server_issue_keys


def test_adapter_preserves_reversed_single_candidate_and_fallback() -> None:
    _, packet = _packet_with_candidate_count(1)
    raw = _valid_output(packet=packet).model_dump(mode="json")
    candidate_ref = packet.mechanism_observations[0].evidence_id
    candidate, fallback = raw["hypotheses"]
    raw["hypotheses"] = [fallback, candidate]
    raw["hypotheses"][0].update(
        {
            "hypothesis_id": "H1",
            "name": "月令整盘替代解释",
        }
    )
    raw["hypotheses"][1].update(
        {
            "hypothesis_id": "H2",
            "name": "唯一机制条件解释",
        }
    )

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.hypotheses[0].method_card_ref == FALLBACK_METHOD_CARD_REF
    assert output.hypotheses[0].name == "月令整盘替代解释"
    assert output.hypotheses[1].method_card_ref == candidate_ref
    assert output.hypotheses[1].name == "唯一机制条件解释"
    assert output.server_issue_keys == ("HYPOTHESIS_DECISION", "WORK_PATH")


def test_work_path_mixed_timing_evidence_is_not_silently_washed_clean() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    natal_id = packet.pillars[0].evidence_id
    timing_id = packet.timing_coordinates[0].evidence_id
    raw["work_path"]["evidence_ids"] = [natal_id, timing_id]

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.work_path.evidence_ids == (natal_id,)
    assert "WORK_PATH" in output.server_issue_keys


def test_work_path_timing_prose_is_withheld_even_with_natal_evidence() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["work_path"]["path_statement"] = (
        "原局主线先承接月令压力，再由岁运推动表达并抵达目标。"
    )

    output = _normalize_raw(packet=packet, raw=raw)

    assert "WORK_PATH" in output.server_issue_keys
    assert output.work_path.closure == "UNCERTAIN"
    assert not any(
        term in f"{output.work_path.path_statement}\n{output.work_path.condition}"
        for term in ("大运", "流年", "岁运")
    )


@pytest.mark.parametrize(
    "codes",
    ([], ["NOT_A_CODE"], ["CHANNELS", "CHANNELS"]),
)
def test_work_path_transformation_form_repairs_are_receipted(codes: list[str]) -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["work_path"]["transformation_codes"] = codes

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.work_path.transformation_codes == ("CHANNELS",)
    assert "WORK_PATH_FORM" in output.server_issue_keys


def test_all_broken_candidates_emit_primary_selection_when_fallback_is_installed() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    for hypothesis in raw["hypotheses"]:
        for ruling in hypothesis["method_rulings"]:
            ruling["ruling"] = "OPPOSES"

    output = _normalize_raw(packet=packet, raw=raw)
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")

    assert primary.method_card_ref == FALLBACK_METHOD_CARD_REF
    assert {"PRIMARY_SELECTION", "HYPOTHESIS_DECISION", "WORK_PATH"}.issubset(
        output.server_issue_keys
    )


def test_all_broken_fallback_slots_emit_semantic_repair_receipts() -> None:
    _, packet = _packet()
    packet_values = packet.model_dump(
        mode="python",
        exclude={"packet_version", "packet_ref", "packet_hash", "read_only"},
    )
    packet_values["mechanism_observations"] = ()
    zero_packet = type(packet).issue(**packet_values)
    raw = _valid_output(packet=zero_packet).model_dump(mode="json")
    for hypothesis in raw["hypotheses"]:
        for ruling in hypothesis["method_rulings"]:
            ruling["ruling"] = "OPPOSES"

    output = _normalize_raw(packet=zero_packet, raw=raw)

    assert output.hypotheses[0].adjudication == "UNRESOLVED"
    assert {"HYPOTHESIS_H1", "PRIMARY_SELECTION", "WORK_PATH"}.issubset(
        output.server_issue_keys
    )


def test_localized_day_master_state_is_normalized_before_regime_projection() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    raw["day_master_state"] = "身强"

    output = _normalize_raw(packet=packet, raw=raw)

    assert output.day_master_state == "STRONG"
    assert output.regime_decision is not None
    assert output.regime_decision.classification == "NON_WEAK_OUTSIDE_SCOPE"
    assert "DAY_MASTER" in output.server_issue_keys


def test_duplicate_candidate_refs_are_neutralized_instead_of_silently_rebound() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    pressure_ref, wealth_ref = (
        item.evidence_id for item in packet.mechanism_observations[:2]
    )
    raw["hypotheses"][1]["method_card_ref"] = pressure_ref
    raw["hypotheses"][1]["mechanism_evidence_ids"] = [pressure_ref]

    output = _normalize_raw(packet=packet, raw=raw)

    assert tuple(item.method_card_ref for item in output.hypotheses) == (
        pressure_ref,
        wealth_ref,
    )
    assert set(output.server_issue_keys) == {
        "HYPOTHESIS_H1",
        "HYPOTHESIS_H2",
        "HYPOTHESIS_DECISION",
        "PRIMARY_SELECTION",
        "WORK_PATH",
    }
    assert all(item.adjudication == "UNRESOLVED" for item in output.hypotheses)
    assert all(
        ruling.ruling == "UNRESOLVED"
        for item in output.hypotheses
        for ruling in item.method_rulings
    )


def test_adapter_allows_two_fallback_hypotheses_when_packet_has_no_candidates() -> None:
    _, packet = _packet()
    packet_values = packet.model_dump(
        mode="python",
        exclude={"packet_version", "packet_ref", "packet_hash", "read_only"},
    )
    packet_values["mechanism_observations"] = ()
    zero_packet = type(packet).issue(**packet_values)
    raw = _valid_output(packet=zero_packet).model_dump(mode="json")

    output = _normalize_raw(packet=zero_packet, raw=raw)

    assert tuple(item.method_card_ref for item in output.hypotheses) == (
        FALLBACK_METHOD_CARD_REF,
        FALLBACK_METHOD_CARD_REF,
    )
    assert output.server_issue_keys == ()


def test_two_fallback_hypotheses_preserve_primary_by_slot_not_method_ref() -> None:
    _, packet = _packet()
    packet_values = packet.model_dump(
        mode="python",
        exclude={"packet_version", "packet_ref", "packet_hash", "read_only"},
    )
    packet_values["mechanism_observations"] = ()
    zero_packet = type(packet).issue(**packet_values)
    raw = _valid_output(packet=zero_packet).model_dump(mode="json")
    raw["hypotheses"][0]["role"] = "ALTERNATIVE"
    raw["hypotheses"][1]["role"] = "PRIMARY"
    raw["hypothesis_decision"]["winner_id"] = "H2"
    raw["hypothesis_decision"]["loser_id"] = "H1"
    raw["work_path"]["selected_hypothesis_id"] = "H2"

    output = _normalize_raw(packet=zero_packet, raw=raw)
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")

    assert primary.hypothesis_id == "H2"
    assert output.work_path.selected_hypothesis_id == "H2"
    assert "PRIMARY_SELECTION" not in output.server_issue_keys


def test_one_malformed_projection_never_erases_the_whole_reading() -> None:
    fixture, packet = _packet()
    base = _valid_output(packet=packet).model_dump(mode="json")

    def copy() -> dict[str, Any]:
        return json.loads(json.dumps(base, ensure_ascii=False))

    cases: list[tuple[dict[str, Any], str, str | None]] = []

    relationship_risk = copy()
    relationship_risk["domains"]["relationship"]["conclusion"] = (
        "关系压力必然导致离婚，并且无法通过沟通改变。"
    )
    cases.append((relationship_risk, "DOMAIN_RELATIONSHIP", "HIGH_RISK_EVENT_ASSERTION"))

    duplicate_hypothesis = copy()
    duplicate_hypothesis["hypotheses"][1]["thesis"] = duplicate_hypothesis["hypotheses"][0][
        "thesis"
    ]
    cases.append((duplicate_hypothesis, "HYPOTHESIS_H2", "MODEL_FIELD_INVALID"))

    evidence_only_chain = copy()
    evidence_only_chain["domains"]["career"]["causal_chain"] = ["E001"]
    cases.append((evidence_only_chain, "DOMAIN_CAREER", "MODEL_FIELD_INVALID"))

    short_domain = copy()
    short_domain["domains"]["career"]["conclusion"] = "太短"
    cases.append((short_domain, "DOMAIN_CAREER", "MODEL_FIELD_INVALID"))

    missing_domain = copy()
    del missing_domain["domains"]["career"]
    cases.append((missing_domain, "DOMAIN_CAREER", "MODEL_FIELD_INVALID"))

    high_confidence = copy()
    high_confidence["domains"]["career"]["confidence"] = "HIGH"
    cases.append((high_confidence, "DOMAIN_CAREER", "MODEL_FIELD_INVALID"))

    for raw, semantic_key, expected_code in cases:
        provider = OllamaMingliAgentProvider(
            model_ref="gemma4:test",
            model_digest="b" * 64,
            provider_profile_ref="v60.test-provider.local-repair",
            base_url="http://private-model.invalid",
            timeout_seconds=3,
            think=False,
            temperature=0,
            top_p=0.95,
            top_k=64,
            num_ctx=32768,
            num_predict=4096,
            keep_alive="30m",
            transport=lambda raw=raw, **_: {
                "response": json.dumps(raw, ensure_ascii=False),
                "prompt_eval_count": 10,
                "eval_count": 20,
            },
        )
        result = provider.generate(packet=packet)
        reading = MingliAgentRuntime(
            provider=_OutputProvider(result.output),
            enabled=True,
        ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)
        graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
        claim = next(item for item in graph.claims if item.semantic_key == semantic_key)
        assert claim.status == "WITHHELD"
        assert expected_code in claim.assessment_codes
        assert any(
            item.semantic_key == "DAY_MASTER" and item.status != "WITHHELD" for item in graph.claims
        )

    invalid_image = copy()
    invalid_image["life_image"]["title"] = "身弱用神之格"
    del invalid_image["life_image"]["image"]
    mapped_state = copy()
    mapped_state["day_master_state"] = "身弱"
    extra_field = copy()
    extra_field["domains"]["career"]["note"] = "模型多给出的字段"
    for raw in (invalid_image, mapped_state, extra_field):
        provider = OllamaMingliAgentProvider(
            model_ref="gemma4:test",
            model_digest="b" * 64,
            provider_profile_ref="v60.test-provider.local-form-repair",
            base_url="http://private-model.invalid",
            timeout_seconds=3,
            think=False,
            temperature=0,
            top_p=0.95,
            top_k=64,
            num_ctx=32768,
            num_predict=4096,
            keep_alive="30m",
            transport=lambda raw=raw, **_: {
                "response": json.dumps(raw, ensure_ascii=False),
                "prompt_eval_count": 10,
                "eval_count": 20,
            },
        )
        result = provider.generate(packet=packet)
        assert result.output.life_image.title != "身弱用神之格"
        if raw is mapped_state:
            assert result.output.day_master_state == "WEAK"


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
    assert len(canonical_json(packet.model_prompt_view())) <= (MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS)
    assert any(
        relation.relation_type == "same_branch_membership"
        and {relation.left_slot, relation.right_slot} == {"year", "month"}
        for relation in packet.natal_relations
    )


def test_owner_method_cards_are_pattern_bound_and_fully_adjudicated() -> None:
    fixture, packet = _packet()
    cards = [mechanism_method_card(item) for item in packet.mechanism_observations]
    assert tuple(len(card["required_checks"]) for card in cards) == (6, 5)
    relabeled = packet.mechanism_observations[0].model_copy(update={"label": "显示文案可以变化"})
    assert mechanism_method_card(relabeled)["required_checks"] == cards[0]["required_checks"]

    output = _valid_output(packet=packet)
    reading = MingliAgentRuntime(
        provider=_OutputProvider(output),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)
    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    primary = next(item for item in graph.claims if item.role == "PRIMARY")
    assert primary.status == "PROVISIONAL"
    assert "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION" not in (primary.assessment_codes)


def test_candidate_coverage_handles_zero_one_and_four_candidates() -> None:
    fixture, owner_packet = _packet()
    packet_values = owner_packet.model_dump(
        mode="python",
        exclude={"packet_version", "packet_ref", "packet_hash", "read_only"},
    )
    packet_values["mechanism_observations"] = ()
    zero_packet = type(owner_packet).issue(**packet_values)
    zero_output = _valid_output(packet=zero_packet)
    assert {item.method_card_ref for item in zero_output.hypotheses} == {FALLBACK_METHOD_CARD_REF}
    MingliAgentRuntime(
        provider=_OutputProvider(zero_output),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=zero_packet,
    )

    one_fixture, one_packet = _packet_with_candidate_count(1)
    one_output = _valid_output(packet=one_packet)
    assert {item.method_card_ref for item in one_output.hypotheses} == {
        one_packet.mechanism_observations[0].evidence_id,
        FALLBACK_METHOD_CARD_REF,
    }
    MingliAgentRuntime(
        provider=_OutputProvider(one_output),
        enabled=True,
    ).run(requester_account_ref=one_fixture["owner_account_ref"], packet=one_packet)

    four_fixture, four_packet = _packet_with_candidate_count(4)
    four_output = _valid_output(packet=four_packet)
    considered = {
        *(
            item.method_card_ref
            for item in four_output.hypotheses
            if item.method_card_ref != FALLBACK_METHOD_CARD_REF
        ),
        *(item.method_card_ref for item in four_output.excluded_candidates),
    }
    assert considered == {item.evidence_id for item in four_packet.mechanism_observations}
    MingliAgentRuntime(
        provider=_OutputProvider(four_output),
        enabled=True,
    ).run(
        requester_account_ref=four_fixture["owner_account_ref"],
        packet=four_packet,
    )


def test_method_ruling_cannot_use_timing_evidence() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["hypotheses"][0]["method_rulings"][0]["evidence_ids"] = [
        packet.timing_coordinates[0].evidence_id
    ]
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    )
    with pytest.raises(MingliAgentProviderError, match="non_natal_evidence"):
        runtime.run(
            requester_account_ref=fixture["owner_account_ref"],
            packet=packet,
        )


def test_unresolved_method_still_produces_low_confidence_working_primary() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    primary, alternative = output["hypotheses"]
    primary["method_rulings"][0]["ruling"] = "UNRESOLVED"
    primary.update(
        {
            "adjudication": "UNRESOLVED",
            "judgment": "COMPETING",
            "confidence": "LOW",
        }
    )
    alternative["method_rulings"][0]["ruling"] = "OPPOSES"
    alternative.update(
        {
            "adjudication": "BROKEN",
            "judgment": "BLOCKED",
            "confidence": "LOW",
        }
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)
    assert reading.output.hypotheses[0].role == "PRIMARY"
    assert reading.output.hypotheses[0].adjudication == "UNRESOLVED"


def test_valid_model_primary_and_reversal_copy_survive_server_repairs() -> None:
    _, packet = _packet()
    raw = _valid_output(packet=packet).model_dump(mode="json")
    for ruling in raw["hypotheses"][0]["method_rulings"][:3]:
        ruling["ruling"] = "UNRESOLVED"
    next(
        item
        for item in raw["hypotheses"][0]["method_rulings"]
        if item["check_code"] == "SOURCE_AND_TARGET_SAME_LAYER"
    )["ruling"] = "UNRESOLVED"
    raw["hypotheses"][1]["method_rulings"][0]["ruling"] = "UNRESOLVED"
    raw["hypothesis_decision"]["reversal"].update(
        {
            "winner_signal": "原来属于H1的收束路径信号仍然成立。",
            "loser_signal": "原来属于H2的分散路径信号足以翻盘。",
        }
    )
    peer_resolution = next(
        item
        for item in raw["hypotheses"][1]["method_rulings"]
        if item["check_code"] == "PEER_COMPETITION_RESOLUTION"
    )
    peer_resolution.update(
        {
            "ruling": "SUPPORTS",
            "rationale": "双比肩意味着同辈竞争，会争夺财星的承接空间。",
        }
    )
    provider = OllamaMingliAgentProvider(
        model_ref="gemma4:test",
        model_digest="b" * 64,
        provider_profile_ref="v60.test-provider.comparative-selection",
        base_url="http://private-model.invalid",
        timeout_seconds=3,
        think=False,
        temperature=0,
        top_p=0.95,
        top_k=64,
        num_ctx=32768,
        num_predict=4096,
        keep_alive="30m",
        transport=lambda **_: {
            "response": json.dumps(raw, ensure_ascii=False),
            "prompt_eval_count": 10,
            "eval_count": 20,
        },
    )
    output = provider.generate(packet=packet).output
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")
    alternative = next(item for item in output.hypotheses if item.role == "ALTERNATIVE")
    repaired_peer = next(
        item
        for item in alternative.method_rulings
        if item.check_code == "PEER_COMPETITION_RESOLUTION"
    )
    assert primary.hypothesis_id == "H1"
    assert repaired_peer.ruling == "UNRESOLVED"
    assert output.hypothesis_decision.winner_id == "H1"
    assert "主解释对月令、透藏和整盘承接的覆盖更完整" in (
        output.hypothesis_decision.winner.rationale
    )
    assert "原来属于食神到七杀路径的收束路径信号" in (
        output.hypothesis_decision.reversal.winner_signal
    )
    assert "原来属于食神到正财路径的分散路径信号" in (
        output.hypothesis_decision.reversal.loser_signal
    )
    assert output.server_issue_keys == ("HYPOTHESIS_H2",)


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
        item.evidence_id for item in packet.timing_relations if item.left_layer == "DAYUN"
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


def test_method_ruling_evidence_supplies_primary_chart_basis() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    primary = next(item for item in output["hypotheses"] if item["role"] == "PRIMARY")
    primary["evidence_ids"] = [item.evidence_id for item in packet.mechanism_observations[:2]]
    primary["method_rulings"][0]["evidence_ids"] = [packet.pillars[0].evidence_id]
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["WHOLE_CHART"].status == "PROVISIONAL"
    assert by_key["HYPOTHESIS_H1"].status == "PROVISIONAL"
    assert by_key["HYPOTHESIS_H1"].assessment_codes == ()
    assert set(by_key["HYPOTHESIS_H1"].evidence_ids) - {
        item.evidence_id for item in packet.mechanism_observations
    }
    assert by_key["DAY_MASTER"].status == "PROVISIONAL"


def test_claim_graph_isolates_invented_root_without_refusing_reading() -> None:
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
    invented_root["hypotheses"][0]["method_rulings"][0]["rationale"] = (
        "日主在地支仍有微弱根气，因此可以直接承接月令与岁运带来的所有压力。"
    )
    runtime = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(invented_root)),
        enabled=True,
    )
    reading = runtime.run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )
    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    whole_chart = next(item for item in graph.claims if item.semantic_key == "WHOLE_CHART")
    assert whole_chart.status == "WITHHELD"
    assert "ROOT_ASSERTION_CONFLICTS_WITH_PACKET" in whole_chart.assessment_codes
    assert any(item.status != "WITHHELD" for item in graph.claims)


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


def test_claim_graph_replaces_timing_relation_effect_without_rejecting_reading() -> None:
    fixture, packet = _packet()
    assert any(item.left_layer == "DAYUN" for item in packet.timing_relations)
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["timing"]["dayun"]["conclusion"] = (
        "子丑六合已经合动偏印、化解七杀并提升承载，所以这一运的结构自然完成。"
    )
    output["timing"]["dayun"]["activation_chain"] = ["六合成员直接兑现为确定作用"]
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
    dayun_claim = next(item for item in graph.claims if item.semantic_key == "TIMING_DAYUN")
    assert len(memory.values) == 1
    assert reading.output.timing.dayun.conclusion.startswith("子丑六合已经合动")
    assert dayun_claim.status == "PROVISIONAL"
    assert dayun_claim.assessment_codes == ()
    assert "六合" not in dayun_claim.statement
    assert "确定作用" not in "".join(dayun_claim.causal_chain)
    assert (
        next(item for item in graph.claims if item.semantic_key == "WHOLE_CHART").status
        == "PROVISIONAL"
    )

    relation_evidence_id = next(
        item.evidence_id for item in packet.timing_relations if item.left_layer == "DAYUN"
    )
    domain_bypass = _valid_output(packet=packet).model_dump(mode="json")
    domain_bypass["domains"]["career"]["conclusion"] = (
        "六合已经合动偏印并化解七杀，因此事业承载会直接提升到稳定状态。"
    )
    domain_bypass["domains"]["career"]["evidence_ids"].append(relation_evidence_id)
    domain_memory = _MemoryStore()
    domain_service = MingliAgentService(
        engine,
        runtime=MingliAgentRuntime(
            provider=_OutputProvider(MingliAgentModelOutput.model_validate(domain_bypass)),
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
            provider=_OutputProvider(MingliAgentModelOutput.model_validate(field_bypass)),
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
    assert mingli_agent_runtime_status(enabled_settings).value == "READY_FOR_OWNER_REVIEW"
    assert configured_mingli_agent_runtime(enabled_settings).ready is True
    manifest = mingli_agent_runtime_manifest(enabled_settings)
    assert manifest["model_qualification_status"] == (
        "GEMMA4_PRODUCT_CANDIDATE_REQUIRES_OWNER_REVIEW"
    )
    assert manifest["reasoning_mode"] == "BLIND_READING"
    assert manifest["owner_review_allowed"] is True
    assert manifest["publication_allowed"] is False
    assert manifest["network_calls_enabled"] is True

    thinking_settings = replace(enabled_settings, mingli_agent_think=True)
    assert mingli_agent_runtime_status(thinking_settings).value == "MISCONFIGURED"
    assert configured_mingli_agent_runtime(thinking_settings).ready is False

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
            requester_account_ref=_unrelated_account_ref(fixture["owner_account_ref"]),
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
    output = _valid_output(suffix=suffix, packet=packet)
    provider_response_ref = f"test-provider-response{suffix}"
    normalization_receipt = MingliAgentNormalizationReceipt.issue(
        provider_response_ref=provider_response_ref,
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
        raw_output=output.model_dump(mode="json"),
        normalized_output=output.model_dump(mode="json"),
        changes=(),
        server_issue_keys=output.server_issue_keys,
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
        provider_response_ref=provider_response_ref,
        normalization_receipt=normalization_receipt,
        output=output,
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        duration_ms=40,
    )


def test_legacy_reading_003_replays_without_injecting_null_regime() -> None:
    fixture = _base_reading_fixture()
    current = _envelope(fixture)
    payload = current.model_dump(mode="json")
    payload["agent_reading_version"] = "v60.mingli-agent-reading.003"
    payload["generation_key"] = mingli_agent_generation_key(
        requester_account_ref=payload["requester_account_ref"],
        reading_ref=payload["reading_ref"],
        reading_hash=payload["reading_hash"],
        packet_ref=payload["packet_ref"],
        packet_hash=payload["packet_hash"],
        agent_profile_ref=payload["agent_profile_ref"],
        agent_profile_hash=payload["agent_profile_hash"],
        provider_profile_ref=payload["provider_profile_ref"],
        provider_profile_hash=payload["provider_profile_hash"],
        prompt_ref=payload["prompt_ref"],
        prompt_hash=payload["prompt_hash"],
        agent_reading_version="v60.mingli-agent-reading.003",
    )
    payload.pop("normalization_receipt")
    payload["output"].pop("regime_decision")
    payload["output"]["work_path"].pop("selected_hypothesis_id")
    payload["output"]["work_path"].pop("method_card_ref")
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"agent_reading_ref", "agent_reading_hash"}
    }
    payload["agent_reading_ref"] = stable_ref("v60-mingli-agent-reading", identity)
    payload["agent_reading_hash"] = content_hash(identity)

    restored = MingliAgentReadingEnvelope.model_validate(payload)

    assert restored.agent_reading_version == "v60.mingli-agent-reading.003"
    assert restored.output.regime_decision is None
    assert "regime_decision" not in restored.output.model_dump(mode="json")
    assert "selected_hypothesis_id" not in restored.output.work_path.model_dump(mode="json")
    assert "method_card_ref" not in restored.output.work_path.model_dump(mode="json")


def test_reading_004_keeps_typed_regime_and_historical_generation_key() -> None:
    fixture = _base_reading_fixture()
    payload = _envelope(fixture).model_dump(mode="json")
    payload["agent_reading_version"] = "v60.mingli-agent-reading.004"
    payload.pop("normalization_receipt")
    payload["output"]["work_path"].pop("selected_hypothesis_id")
    payload["output"]["work_path"].pop("method_card_ref")
    payload["generation_key"] = mingli_agent_generation_key(
        requester_account_ref=payload["requester_account_ref"],
        reading_ref=payload["reading_ref"],
        reading_hash=payload["reading_hash"],
        packet_ref=payload["packet_ref"],
        packet_hash=payload["packet_hash"],
        agent_profile_ref=payload["agent_profile_ref"],
        agent_profile_hash=payload["agent_profile_hash"],
        provider_profile_ref=payload["provider_profile_ref"],
        provider_profile_hash=payload["provider_profile_hash"],
        prompt_ref=payload["prompt_ref"],
        prompt_hash=payload["prompt_hash"],
        agent_reading_version="v60.mingli-agent-reading.004",
    )
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"agent_reading_ref", "agent_reading_hash"}
    }
    payload["agent_reading_ref"] = stable_ref("v60-mingli-agent-reading", identity)
    payload["agent_reading_hash"] = content_hash(identity)

    restored = MingliAgentReadingEnvelope.model_validate(payload)

    assert restored.output.regime_decision is not None
    assert "selected_hypothesis_id" not in restored.output.work_path.model_dump(mode="json")
    assert "method_card_ref" not in restored.output.work_path.model_dump(mode="json")
    assert restored.generation_key == mingli_agent_generation_key(
        requester_account_ref=payload["requester_account_ref"],
        reading_ref=payload["reading_ref"],
        reading_hash=payload["reading_hash"],
        packet_ref=payload["packet_ref"],
        packet_hash=payload["packet_hash"],
        agent_profile_ref=payload["agent_profile_ref"],
        agent_profile_hash=payload["agent_profile_hash"],
        provider_profile_ref=payload["provider_profile_ref"],
        provider_profile_hash=payload["provider_profile_hash"],
        prompt_ref=payload["prompt_ref"],
        prompt_hash=payload["prompt_hash"],
        agent_reading_version="v60.mingli-agent-reading.003",
    )
    payload["output"].pop("regime_decision")
    with pytest.raises(ValueError, match="regime_decision_required"):
        MingliAgentReadingEnvelope.model_validate(payload)


def test_reading_005_requires_typed_regime_decision() -> None:
    fixture = _base_reading_fixture()
    payload = _envelope(fixture).model_dump(mode="json")
    payload["output"].pop("regime_decision")

    with pytest.raises(ValueError, match="regime_decision_required"):
        MingliAgentReadingEnvelope.model_validate(payload)


def test_legacy_reading_005_replays_without_injecting_work_path_binding() -> None:
    fixture = _base_reading_fixture()
    payload = _envelope(fixture).model_dump(mode="json")
    payload["agent_reading_version"] = "v60.mingli-agent-reading.005"
    payload["output"]["work_path"].pop("selected_hypothesis_id")
    payload["output"]["work_path"].pop("method_card_ref")
    payload["generation_key"] = mingli_agent_generation_key(
        requester_account_ref=payload["requester_account_ref"],
        reading_ref=payload["reading_ref"],
        reading_hash=payload["reading_hash"],
        packet_ref=payload["packet_ref"],
        packet_hash=payload["packet_hash"],
        agent_profile_ref=payload["agent_profile_ref"],
        agent_profile_hash=payload["agent_profile_hash"],
        provider_profile_ref=payload["provider_profile_ref"],
        provider_profile_hash=payload["provider_profile_hash"],
        prompt_ref=payload["prompt_ref"],
        prompt_hash=payload["prompt_hash"],
        agent_reading_version="v60.mingli-agent-reading.005",
    )
    prior_receipt = MingliAgentNormalizationReceipt.model_validate(
        payload["normalization_receipt"]
    )
    legacy_output = payload["output"]
    legacy_receipt = MingliAgentNormalizationReceipt.issue(
        provider_response_ref=prior_receipt.provider_response_ref,
        packet_ref=prior_receipt.packet_ref,
        packet_hash=prior_receipt.packet_hash,
        agent_profile_ref=prior_receipt.agent_profile_ref,
        agent_profile_hash=prior_receipt.agent_profile_hash,
        provider_id=prior_receipt.provider_id,
        model_ref=prior_receipt.model_ref,
        model_digest=prior_receipt.model_digest,
        provider_profile_ref=prior_receipt.provider_profile_ref,
        provider_profile_hash=prior_receipt.provider_profile_hash,
        prompt_ref=prior_receipt.prompt_ref,
        prompt_hash=prior_receipt.prompt_hash,
        raw_output=legacy_output,
        normalized_output=legacy_output,
        changes=(),
        server_issue_keys=tuple(legacy_output["server_issue_keys"]),
    )
    payload["normalization_receipt"] = legacy_receipt.model_dump(mode="json")
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"agent_reading_ref", "agent_reading_hash"}
    }
    payload["agent_reading_ref"] = stable_ref("v60-mingli-agent-reading", identity)
    payload["agent_reading_hash"] = content_hash(identity)

    restored = MingliAgentReadingEnvelope.model_validate(payload)

    dumped = restored.output.work_path.model_dump(mode="json")
    assert restored.agent_reading_version == "v60.mingli-agent-reading.005"
    assert "selected_hypothesis_id" not in dumped
    assert "method_card_ref" not in dumped


def test_normalization_receipt_rejects_unproved_raw_to_normalized_change() -> None:
    fixture = _base_reading_fixture()
    envelope = _envelope(fixture)
    receipt = envelope.normalization_receipt
    assert receipt is not None

    with pytest.raises(ValueError, match="delta_chain_mismatch"):
        MingliAgentNormalizationReceipt.issue(
            provider_response_ref=receipt.provider_response_ref,
            packet_ref=receipt.packet_ref,
            packet_hash=receipt.packet_hash,
            agent_profile_ref=receipt.agent_profile_ref,
            agent_profile_hash=receipt.agent_profile_hash,
            provider_id=receipt.provider_id,
            model_ref=receipt.model_ref,
            model_digest=receipt.model_digest,
            provider_profile_ref=receipt.provider_profile_ref,
            provider_profile_hash=receipt.provider_profile_hash,
            prompt_ref=receipt.prompt_ref,
            prompt_hash=receipt.prompt_hash,
            raw_output={"verdict": "RAW"},
            normalized_output={"verdict": "REPAIRED"},
            changes=(),
            server_issue_keys=(),
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
    primary = next(item for item in reading.output.hypotheses if item.role == "PRIMARY")
    assert by_key["WHOLE_CHART"].headline == primary.name
    assert by_key["WHOLE_CHART"].statement.startswith(
        f"暂以{primary.name}作为整盘工作主线"
    )
    assert primary.method_rulings[0].rationale.rstrip("。").replace("此项通过", "") in (
        by_key["WHOLE_CHART"].statement
    )
    assert by_key["LIFE_IMAGE"].statement == reading.output.life_image.explanation
    assert by_key["DOMAIN_CAREER"].statement == reading.output.domains.career.conclusion
    assert by_key["TIMING_DAYUN"].statement.startswith(
        next(item.pillar for item in packet.timing_coordinates if item.layer == "DAYUN")
    )
    assert by_key["TIMING_ANNUAL"].statement.startswith(
        next(item.pillar for item in packet.timing_coordinates if item.layer == "ANNUAL")
    )
    assert "这不等于结果已经发生" in by_key["TIMING_ANNUAL"].statement
    assert (
        by_key["DISCRIMINATING_QUESTION"].statement
        == reading.output.hypothesis_decision.reversal.question
    )
    assert by_key["HYPOTHESIS_H1"].status == "PROVISIONAL"
    assert by_key["HYPOTHESIS_H2"].status == "NEEDS_RECONCILIATION"
    assert by_key["HYPOTHESIS_H2"].assessment_codes == ()
    assert "CONDITIONAL" in by_key["HYPOTHESIS_H1"].codes
    assert by_key["HYPOTHESIS_H1"].mechanism_evidence_ids
    assert by_key["TIMING_DAYUN"].coordinate_evidence_id in by_key["TIMING_DAYUN"].evidence_ids
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
    output["domains"]["career"]["conclusion"] = "六合已经合动全盘，并决定事业路径稳定兑现。"
    output["domains"]["career"]["condition"] = "若外部职责变化，再观察收入节奏。"
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    career = next(item for item in graph.claims if item.semantic_key == "DOMAIN_CAREER")

    assert career.status == "WITHHELD"
    assert "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT" in career.assessment_codes


def test_relationship_and_family_single_ten_god_stories_are_withheld() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["relationship"].update(
        {
            "headline": "寻找精神共鸣的关系",
            "conclusion": "日支所藏偏印代表精神依恋，因此关系更需要理解和陪伴。",
            "causal_chain": ["偏印进入夫妻宫并形成情感安全需求"],
        }
    )
    output["domains"]["family"].update(
        {
            "headline": "重视精神滋养的家庭",
            "conclusion": "日支所藏偏印使家庭天然围绕精神交流和情感安全展开。",
            "causal_chain": ["偏印直接形成家庭里的精神滋养"],
        }
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    for semantic_key in ("DOMAIN_RELATIONSHIP", "DOMAIN_FAMILY"):
        claim = by_key[semantic_key]
        assert claim.status == "WITHHELD"
        assert "TEN_GOD_TO_LIFE_STORY_SHORTCUT" in claim.assessment_codes
        assert "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED" in claim.assessment_codes


def test_relationship_and_family_keywords_cannot_bypass_missing_positive_method() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["relationship"].update(
        {
            "headline": "承诺与资源分配要同时校准",
            "conclusion": (
                "男命财星落入日支夫妻宫提供现实承诺的一轴，但关系质量仍取决于"
                "整盘财路能否被日主持久承接。"
            ),
            "causal_chain": ["偏财位于日支夫妻宫，再与整盘主路径共同决定责任分配"],
        }
    )
    output["domains"]["family"].update(
        {
            "headline": "当前家庭先校准责任边界",
            "conclusion": (
                "当前家庭先看日支所承载的现实责任，再结合整盘主路径判断资源与"
                "照料如何分配。"
            ),
            "causal_chain": ["当前家庭范围结合日支宫位与整盘主路径形成责任分配"],
        }
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    for semantic_key in ("DOMAIN_RELATIONSHIP", "DOMAIN_FAMILY"):
        claim = by_key[semantic_key]
        assert "TEN_GOD_TO_LIFE_STORY_SHORTCUT" not in claim.assessment_codes
        assert "DOMAIN_METHOD_AXES_INCOMPLETE" not in claim.assessment_codes
        assert "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED" in claim.assessment_codes
        assert claim.status == "WITHHELD"


@pytest.mark.parametrize(
    "conclusion",
    (
        "当前家庭里，偏财天然代表重物质，因此责任一定围绕收入展开。",
        "男命财星与日支夫妻宫同时出现，因此伴侣天然务实。",
        "财星不在日支，夫妻宫并无财星，所以伴侣天然疏离。",
    ),
)
def test_domain_method_keywords_cannot_launder_unadmitted_life_story(
    conclusion: str,
) -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["relationship"]["conclusion"] = conclusion
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    relationship = next(
        item for item in graph.claims if item.semantic_key == "DOMAIN_RELATIONSHIP"
    )

    assert relationship.status == "WITHHELD"
    assert "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED" in relationship.assessment_codes


def test_spouse_palace_axis_rejects_ten_god_from_another_branch() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["relationship"].update(
        {
            "headline": "现实承诺需要共同校准",
            "conclusion": "财星与日支夫妻宫共同构成关系判断的两条命盘轴。",
            "causal_chain": [
                "日支为丑土，藏干中正财（戊）和偏财（己）均显现，因此更看重现实承诺。"
            ],
        }
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    relationship = next(
        item for item in graph.claims if item.semantic_key == "DOMAIN_RELATIONSHIP"
    )

    assert relationship.status == "WITHHELD"
    assert "NAMED_COORDINATE_CONFLICTS_WITH_PACKET" in relationship.assessment_codes


def test_named_coordinate_check_stops_before_the_next_clause() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["relationship"].update(
        {
            "headline": "先核对夫妻宫里的真实成员",
            "conclusion": "财星与日支夫妻宫必须分别核对，不能把其他柱的十神移入日支。",
            "causal_chain": [
                "日支丑土藏干中偏财（己）与偏印（癸）同在，年干食神（丁）明透。"
            ],
        }
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    relationship = next(
        item for item in graph.claims if item.semantic_key == "DOMAIN_RELATIONSHIP"
    )

    assert "NAMED_COORDINATE_CONFLICTS_WITH_PACKET" not in relationship.assessment_codes
    assert "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED" in relationship.assessment_codes


def test_generic_mechanism_group_name_cannot_replace_exact_ten_god_path() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    primary = next(item for item in output["hypotheses"] if item["role"] == "PRIMARY")
    primary.update(
        {
            "name": "食伤生财结构",
            "thesis": "食伤可以生财，因此这条结构暂时作为整盘主解释。",
        }
    )
    for ruling in primary["method_rulings"]:
        ruling["rationale"] = "食伤与财星成员同时存在，因此先保留这条宽泛机制。"
        ruling["condition_or_falsifier"] = "若食伤不能生财，再翻转当前解释。"
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    hypothesis = next(
        item for item in graph.claims if item.semantic_key == f"HYPOTHESIS_{primary['hypothesis_id']}"
    )

    assert hypothesis.status == "WITHHELD"
    assert "EXACT_ROLE_PATH_MISSING" in hypothesis.assessment_codes


def test_withheld_h1_alternative_does_not_quarantine_valid_h2_primary() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    first, second = output["hypotheses"]
    first["role"] = "ALTERNATIVE"
    second["role"] = "PRIMARY"
    output["hypothesis_decision"]["winner_id"] = "H2"
    output["hypothesis_decision"]["loser_id"] = "H1"
    output["work_path"]["selected_hypothesis_id"] = "H2"
    output["work_path"]["method_card_ref"] = second["method_card_ref"]
    first.update(
        {
            "name": "食伤制官杀宽泛候选",
            "thesis": "食伤与官杀同时存在，所以先保留为一条宽泛替代解释。",
        }
    )
    for ruling in first["method_rulings"]:
        ruling["rationale"] = "食伤与官杀成员同时存在，尚未锁定具体十神路径。"
        ruling["condition_or_falsifier"] = "若宽泛结构不能解释现实，就撤下本候选。"
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["HYPOTHESIS_H1"].status == "WITHHELD"
    assert by_key["HYPOTHESIS_H2"].status == "PROVISIONAL"
    assert by_key["WHOLE_CHART"].status == "PROVISIONAL"


def test_peer_presence_cannot_be_rewritten_as_human_cooperation() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["wealth"]["conclusion"] = (
        "财富积累依赖持续专业输出，也依赖人际合作带来的资源承接。"
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(requester_account_ref=fixture["owner_account_ref"], packet=packet)

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    wealth = next(item for item in graph.claims if item.semantic_key == "DOMAIN_WEALTH")

    assert wealth.status == "WITHHELD"
    assert "UNSUPPORTED_SOCIAL_RESOURCE_INFERENCE" in wealth.assessment_codes


def test_ordinary_conflict_resolution_is_not_misread_as_relation_effect() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["work_path"]["path_statement"] = (
        "食伤向官杀施加影响，但路径能否持续依赖于印星化解冲突的能力。"
    )
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    work_path = next(item for item in graph.claims if item.semantic_key == "WORK_PATH")

    assert work_path.status == "PROVISIONAL"
    assert "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT" not in work_path.assessment_codes


def test_selected_timing_stem_can_be_described_as_visible_in_its_own_layer() -> None:
    fixture, packet = _packet()
    annual = next(item for item in packet.timing_coordinates if item.layer == "ANNUAL")
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["timing"]["annual"]["conclusion"] = (
        f"{annual.pillar}流年{annual.ten_god_label}透出，极大增强冲突并使张力达到顶峰。"
    )
    output["timing"]["annual"]["activation_chain"] = [
        f"{annual.pillar}进入流年层，令所有冲突达到高峰。"
    ]
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    annual_claim = next(item for item in graph.claims if item.semantic_key == "TIMING_ANNUAL")

    assert annual_claim.status == "PROVISIONAL"
    assert "极大" not in annual_claim.statement
    assert "顶峰" not in annual_claim.statement
    assert "这不等于结果已经发生" in annual_claim.statement
    assert "TEN_GOD_MANIFESTATION_CONFLICTS_WITH_PACKET" not in (
        annual_claim.assessment_codes
    )


def test_timing_natal_uses_selected_primary_instead_of_model_timing_rewrite() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["timing"]["natal_baseline"] = "当前大运进入以后直接改变原局结构，所以日主已经明确偏强。"
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    natal = next(item for item in graph.claims if item.semantic_key == "TIMING_NATAL")

    assert natal.status == "PROVISIONAL"
    assert natal.statement.startswith("暂以")
    assert "当前大运进入以后" not in natal.statement
    assert natal.assessment_codes == ()


def test_owner_gemma4_reading_has_exact_evidence_and_dependency_admission() -> None:
    fixture, packet = _packet()
    frozen_output = json.loads(
        (Path(__file__).parent / "fixtures" / "owner_gemma4_agent_reading_010.json").read_text(
            encoding="utf-8"
        )
    )
    upgraded_output = _valid_output(packet=packet).model_dump(mode="json")
    for key, value in frozen_output.items():
        if key not in {"hypotheses", "discriminating_question", "day_master_state"}:
            upgraded_output[key] = value
    for upgraded, frozen in zip(
        upgraded_output["hypotheses"], frozen_output["hypotheses"], strict=True
    ):
        upgraded.update(frozen)
        if upgraded["confidence"] == "HIGH":
            upgraded["confidence"] = "MEDIUM"
    upgraded_output["hypothesis_decision"]["reversal"]["question"] = frozen_output[
        "discriminating_question"
    ]
    selected = next(
        item for item in upgraded_output["hypotheses"] if item["role"] == "PRIMARY"
    )
    upgraded_output["work_path"]["selected_hypothesis_id"] = selected["hypothesis_id"]
    upgraded_output["work_path"]["method_card_ref"] = selected["method_card_ref"]
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(upgraded_output)),
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
        "HYPOTHESIS_H1": "WITHHELD",
        "HYPOTHESIS_H2": "WITHHELD",
        "WORK_PATH": "WITHHELD",
        "LIFE_IMAGE": "PROVISIONAL",
        "DOMAIN_PERSONALITY": "WITHHELD",
        "DOMAIN_CAREER": "WITHHELD",
        "DOMAIN_WEALTH": "NEEDS_RECONCILIATION",
        "DOMAIN_RELATIONSHIP": "WITHHELD",
        "DOMAIN_FAMILY": "WITHHELD",
        "TIMING_NATAL": "PROVISIONAL",
        "TIMING_DAYUN": "PROVISIONAL",
        "TIMING_ANNUAL": "PROVISIONAL",
        "DISCRIMINATING_QUESTION": "OPEN_QUESTION",
    }
    assert by_key["HYPOTHESIS_H1"].mechanism_evidence_ids == ("E009",)
    assert by_key["HYPOTHESIS_H1"].confidence == "MEDIUM"
    assert by_key["TIMING_DAYUN"].coordinate_evidence_id == "E011"
    assert by_key["TIMING_ANNUAL"].coordinate_evidence_id == "E012"
    assert "E012" in by_key["TIMING_ANNUAL"].evidence_ids
    assert by_key["DISCRIMINATING_QUESTION"].statement == (frozen_output["discriminating_question"])
    assert "DEPENDENCY_WITHHELD" in by_key["WHOLE_CHART"].assessment_codes
    withheld_refs = {item.claim_ref for item in graph.claims if item.status == "WITHHELD"}
    assert all(
        edge.source_claim_ref not in withheld_refs and edge.target_claim_ref not in withheld_refs
        for edge in graph.edges
    )


def test_local_fact_overreach_quarantines_claim_not_whole_reading() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    output["domains"]["career"]["causal_chain"] = ["日主坐支根气受制，且酉、藏庚形成持续压力。"]
    output["domains"]["family"]["conclusion"] = "丑土作为财库，使家庭责任天然围绕物质积累展开。"
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

    assert by_key["WHOLE_CHART"].status == "PROVISIONAL"
    assert by_key["DOMAIN_CAREER"].status == "WITHHELD"
    assert set(by_key["DOMAIN_CAREER"].assessment_codes) == {
        "ROOT_ASSERTION_CONFLICTS_WITH_PACKET",
        "NAMED_COORDINATE_CONFLICTS_WITH_PACKET",
    }
    assert by_key["DOMAIN_FAMILY"].assessment_codes == (
        "UNADMITTED_CLASSICAL_ASSERTION",
        "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED",
    )
    assert by_key["DOMAIN_RELATIONSHIP"].assessment_codes == (
        "UNLISTED_RELATION_COORDINATE_ASSERTION",
        "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED",
    )


def test_many_local_overreaches_cannot_break_the_claim_graph() -> None:
    fixture, packet = _packet()
    output = _valid_output(packet=packet).model_dump(mode="json")
    relation_evidence_id = next(
        item.evidence_id for item in packet.timing_relations if item.left_layer == "DAYUN"
    )
    output["domains"]["career"]["conclusion"] = (
        "大运庚子使根气受制，酉、藏庚与丑土财库、巳火相连，六合已经合动并导致车祸。"
    )
    output["domains"]["career"]["evidence_ids"].append(relation_evidence_id)
    reading = MingliAgentRuntime(
        provider=_OutputProvider(MingliAgentModelOutput.model_validate(output)),
        enabled=True,
    ).run(
        requester_account_ref=fixture["owner_account_ref"],
        packet=packet,
    )

    graph = MingliReadingClaimGraphProjector().project(reading, packet=packet)
    by_key = {item.semantic_key: item for item in graph.claims}

    assert by_key["WHOLE_CHART"].status == "PROVISIONAL"
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
        assert (
            store.find_generation(
                requester_account_ref=fixture["owner_account_ref"],
                generation_key=first.generation_key,
            )
            == first
        )
        assert (
            store.find_generation(
                requester_account_ref=_unrelated_account_ref(fixture["owner_account_ref"]),
                generation_key=first.generation_key,
            )
            is None
        )
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
    session = SimpleNamespace(account=SimpleNamespace(account_ref=fixture["owner_account_ref"]))

    payload = mingli_stage.generate_agent_reading(  # type: ignore[arg-type]
        request,
        response,
        session,
    )

    assert payload["agent_reading_ref"] == envelope.agent_reading_ref
    assert "normalization_receipt" not in payload
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


def test_reading_summary_api_redacts_private_normalization_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SummaryService:
        def project(self, **_: str):
            return SimpleNamespace(
                model_dump=lambda **__: {
                    "agent_reading": {
                        "agent_reading_ref": "reading:owner",
                        "normalization_receipt": {"raw_output": {"private": True}},
                    }
                }
            )

    monkeypatch.setattr(mingli_stage, "reading_summaries", SummaryService())
    response = Response()
    session = SimpleNamespace(account=SimpleNamespace(account_ref="owner"))

    payload = mingli_stage.stage_reading_summary(
        response,
        session,  # type: ignore[arg-type]
        case_ref="case:owner",
    )

    assert "normalization_receipt" not in payload["agent_reading"]
