from __future__ import annotations

from copy import deepcopy

from core.graph import AssertionLifecycle, MingliRelationState
from core.life_case.contracts import FormalInsight, LifeCase
from core.life_case.relation_path import build_committed_relation_path_assertions
from core.mingli_agent import compile_chart_world
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord, WorkPathReasoning
from core.mingli_agent.path_bridge import bind_structured_path_candidate
from tests.test_v50_mingli_structural_experiment import _birth, _case_payload


def _work_path(*, candidate_ref: str = "") -> WorkPathReasoning:
    return WorkPathReasoning(
        path_statement="模型自然语言不能直接成为正式路径。",
        source=["模型起点"],
        transformations=["模型转换"],
        target=["模型终点"],
        body_function_relation="等待系统逐段绑定。",
        closure="uncertain",
        success_conditions=["引用通过验证"],
        failure_conditions=["引用无效"],
        evidence_refs=[],
        candidate_path_refs=[candidate_ref] if candidate_ref else [],
    )


def _candidate(world: ChartWorldInstance, *, edge_count: int):
    return next(
        fact
        for fact in world.facts
        if fact.category == "candidate_path"
        and len(fact.payload.get("relation_descriptors") or []) == edge_count
    )


def test_path_bridge_binds_only_system_enumerated_candidate_and_rewrites_narration() -> None:
    world = compile_chart_world(reading_id="path-bridge-bind", birth_input=_birth())
    fact = _candidate(world, edge_count=2)

    bound, receipt = bind_structured_path_candidate(
        work_path=_work_path(candidate_ref=fact.fact_id),
        world=world,
    )

    assert receipt.selected_path_ref == fact.fact_id
    assert receipt.accepted_segment_count == 2
    assert receipt.rejected_segment_count == 0
    assert bound.origin == "system_enumerated"
    assert bound.structured_candidate is not None
    assert bound.structured_candidate.validation_status == "validated"
    assert bound.path_statement.startswith("已验证路径：")
    assert "模型自然语言" not in bound.path_statement
    assert all(item.relation_ref in world.allowed_evidence_refs for item in bound.structured_candidate.segments)
    assert all(item.mechanism_ref != "" for item in bound.structured_candidate.segments)


def test_path_bridge_leaves_prose_uncommitted_when_no_exact_candidate_was_selected() -> None:
    world = compile_chart_world(reading_id="path-bridge-prose", birth_input=_birth())

    bound, receipt = bind_structured_path_candidate(
        work_path=_work_path(),
        world=world,
    )

    assert receipt.selected_path_ref == ""
    assert bound.structured_candidate is None
    assert bound.candidate_path_refs == []
    assert bound.path_statement == "模型自然语言不能直接成为正式路径。"


def test_path_bridge_isolates_invalid_middle_segment_without_jumping_the_gap() -> None:
    payload = _case_payload("path-bridge-partial")
    world_payload = deepcopy(payload["world"])
    candidate_payload = next(
        item
        for item in world_payload["facts"]
        if item["category"] == "candidate_path"
        and len(item["payload"].get("relation_descriptors") or []) == 3
    )
    candidate_payload["payload"]["relation_descriptors"][1]["candidate_relation_key"] = (
        "candidate-relation-invalid-middle"
    )
    world = ChartWorldInstance.model_validate(world_payload)
    selected_ref = candidate_payload["fact_id"]
    bound, receipt = bind_structured_path_candidate(
        work_path=_work_path(candidate_ref=selected_ref),
        world=world,
    )

    assert receipt.accepted_segment_count == 2
    assert receipt.rejected_segment_count == 1
    assert bound.structured_candidate is not None
    assert bound.structured_candidate.validation_status == "partial"
    assert [item.validation_status for item in bound.structured_candidate.segments] == [
        "validated",
        "rejected",
        "validated",
    ]

    record = MingliCognitiveRecord.model_validate(payload["record"])
    record = record.model_copy(update={
        "world_id": world.world_id,
        "cognition": record.cognition.model_copy(update={"work_path": bound}),
    })
    legacy_case = LifeCase.model_validate(payload["life_case"])
    insight = FormalInsight.model_validate(
        legacy_case.baseline_insight.model_copy(update={
            "projection_payload": {
                **legacy_case.baseline_insight.projection_payload,
                "record_projection": record.model_dump(mode="json"),
            },
        })
    )
    relations, paths = build_committed_relation_path_assertions(
        insight=insight,
        world=world,
        life_case_id=legacy_case.life_case_id,
        chart_version=legacy_case.chart_version,
        case_version=legacy_case.case_version,
    )

    assert len(relations) == 2
    assert len(paths) == 2
    assert all(item.status == AssertionLifecycle.COMMITTED for item in paths)
    assert all(len(item.path_key.relation_keys) == 1 for item in paths if item.path_key)
    assert all(item.rejected_segment_refs for item in paths)
    assert all(item.relation_state == MingliRelationState.EFFECTIVE for item in relations)
    assert all(item.position_context is not None for item in relations)


def test_commit_rejects_tampered_structured_candidate_even_when_fact_ref_exists() -> None:
    payload = _case_payload("path-bridge-integrity")
    world = ChartWorldInstance.model_validate(payload["world"])
    record = MingliCognitiveRecord.model_validate(payload["record"])
    structured = record.cognition.work_path.structured_candidate
    assert structured is not None
    tampered = structured.model_copy(update={"candidate_path_key": "candidate-path-tampered"})
    record = record.model_copy(update={
        "cognition": record.cognition.model_copy(update={
            "work_path": record.cognition.work_path.model_copy(update={
                "structured_candidate": tampered,
            }),
        }),
    })
    legacy_case = LifeCase.model_validate(payload["life_case"])
    insight = legacy_case.baseline_insight.model_copy(update={
        "projection_payload": {
            **legacy_case.baseline_insight.projection_payload,
            "record_projection": record.model_dump(mode="json"),
        },
    })

    relations, paths = build_committed_relation_path_assertions(
        insight=insight,
        world=world,
        life_case_id=legacy_case.life_case_id,
        chart_version=legacy_case.chart_version,
        case_version=legacy_case.case_version,
    )

    assert relations == []
    assert len(paths) == 1
    assert paths[0].status == AssertionLifecycle.LEGACY_UNRESOLVED
    assert paths[0].unresolved_reason == "structured_path_candidate_integrity_mismatch"
