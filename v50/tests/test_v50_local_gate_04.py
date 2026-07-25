from __future__ import annotations

import re

from core.contracts import BirthInputCanonical
from core.engines import resolve_birth_input_pillars
from core.life_case import build_baseline_insight, commit_baseline_life_case
from core.mingli_agent import MingliAgent, compile_chart_world
from core.mingli_agent.contracts import (
    BaselineCoreCognitionDraft,
    CognitiveHypothesis,
    SalientPhenomenon,
)
from core.mingli_agent.professional_review import review_professional_record
from product.agent_case_store import MemoryAgentCaseStore
from product.canvas_projection import ReadOnlySixPillarCanvasService
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel


REAL_CALENDAR_CASES = (
    ("lg04-fire-metal", "1987-05-12", "18:00", "male"),
    ("lg04-earth-metal", "1990-01-15", "10:00", "female"),
    ("lg04-wood-pressure", "1995-09-20", "14:00", "male"),
    ("lg04-metal-support", "2001-03-08", "06:00", "female"),
    ("lg04-earth-water", "1976-11-22", "20:00", "male"),
)


class PathSelectingBaselineModel(FakeCognitiveModel):
    """Mechanical gate model: chooses one provided candidate; it is not professional gold."""

    model = "local-gate-04-path-selecting-fixture"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *, prompt, schema, **kwargs):
        self.calls += 1
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=kwargs.get("temperature", 0.2),
            thinking=kwargs.get("thinking", True),
            max_tokens=kwargs.get("max_tokens", 3200),
        )
        if schema is not BaselineCoreCognitionDraft:
            return result
        match = re.search(r'"path_ref":"([^"]+)"', prompt)
        assert match is not None
        candidate_ref = match.group(1)
        hypothesis = CognitiveHypothesis(
            hypothesis_id="h1",
            name="结构路径候选",
            thesis="当前只把系统枚举路径作为待验证的结构解释。",
            rank=1,
            status="primary",
            supporting_evidence_refs=["F001"],
            success_conditions=["每一段引用通过验证"],
            failure_conditions=["任一必要关系不成立"],
            confidence="medium",
        )
        return result.model_copy(update={
            "first_look": "先看当前命盘中同时显现的结构关系。",
            "whole_chart_thesis": "当前只提交系统逐段验证后的结构路径，其他解释保持未决。",
            "salient_phenomena": [SalientPhenomenon(
                phenomenon_id="s1",
                observation="命盘四柱同时显现",
                why_it_matters="为结构关系提供明确节点",
                evidence_refs=["F001"],
            )],
            "hypotheses": [hypothesis],
            "selected_hypothesis_id": "h1",
            "work_path": result.work_path.model_copy(update={
                "candidate_path_refs": [candidate_ref],
                "evidence_refs": ["F001"],
            }),
            "useful_god_reasoning": [],
            "unresolved_questions": ["现实作用仍需专业审阅"],
            "evidence_refs": ["F001"],
        })


def _calendar_birth(case_id: str, date: str, time: str, gender: str) -> BirthInputCanonical:
    return resolve_birth_input_pillars(BirthInputCanonical(
        birth_input_id=f"birth:{case_id}",
        name=case_id,
        gender=gender,
        calendar_type="solar",
        birth_date=date,
        birth_time=time,
        birth_location="Shanghai",
        timezone="Asia/Shanghai",
    ))


def test_local_gate_04_five_calendar_cases_commit_and_project_real_paths() -> None:
    store = MemoryAgentCaseStore()
    participant_id = "local-gate-04"
    cases = []

    for case_id, date, time, gender in REAL_CALENDAR_CASES:
        birth = _calendar_birth(case_id, date, time, gender)
        assert birth.pillar_fact_source == "calendar_derived_formal"
        world = compile_chart_world(reading_id=case_id, birth_input=birth)
        assert [
            birth.year_pillar,
            birth.month_pillar,
            birth.day_pillar,
            birth.hour_pillar,
        ] == world.pillars
        model = PathSelectingBaselineModel()
        record = MingliAgent(model).first_baseline_reading(case_id=case_id, world=world)
        assert model.calls == 1
        assert record.cognition.work_path.structured_candidate is not None
        assert record.cognition.work_path.structured_candidate.validation_status == "validated"
        professional = review_professional_record(
            record=record,
            world=world,
            persistence_status="persisted",
        )
        assert professional.overlay.professional_release_status == "passed"
        insight = build_baseline_insight(
            record=record,
            world=world,
            professional_review=professional,
        )
        life_case, validation = commit_baseline_life_case(
            insight=insight,
            world=world,
            profile_id=f"profile:{case_id}",
        )
        assert validation.passed is True
        assert life_case.path_assertions
        assert life_case.relation_assertions
        assert all(item.position_context is not None for item in life_case.relation_assertions)
        store.save(
            case_id=case_id,
            user_id=participant_id,
            profile_id=f"profile:{case_id}",
            payload={
                "case_id": case_id,
                "birth_input": birth.model_dump(mode="json"),
                "world": world.model_dump(mode="json"),
                "record": record.model_dump(mode="json"),
                "life_case": life_case.model_dump(mode="json"),
            },
        )
        cases.append((case_id, life_case))

    service = ReadOnlySixPillarCanvasService(case_store=store)
    for case_id, life_case in cases:
        member = service.issue(
            case_id=case_id,
            participant_id=participant_id,
            account_role="member",
        )
        research = service.issue(
            case_id=case_id,
            participant_id=participant_id,
            account_role="research",
        )
        assert member["path_availability"]["status"] == "available"
        assert member["llm_used"] is False
        assert [
            len(member["stages"][stage]["spec"]["semantic_slots"])
            for stage in ("natal", "luck", "year")
        ] == [4, 5, 6]
        natal_paths = member["stages"]["natal"]["spec"]["paths"]
        assert natal_paths
        assert {item["label"] for item in natal_paths} == {
            item.statement for item in life_case.path_assertions
        }
        natal_node_refs = {
            item["node_ref"]
            for item in member["stages"]["natal"]["spec"]["nodes"]
        }
        assert natal_node_refs.issubset({
            item["node_ref"]
            for item in member["stages"]["luck"]["spec"]["nodes"]
        })
        assert natal_node_refs.issubset({
            item["node_ref"]
            for item in member["stages"]["year"]["spec"]["nodes"]
        })
        assert not [
            item
            for item in member["stages"]["natal"]["spec"]["relations"]
            if item["relation_state"] in {"potential", "structural"}
        ]
        assert research["renderer_policy"]["available_visibility_layers"][-1] == "lab_audit"
        assert [
            item
            for item in research["stages"]["natal"]["spec"]["relations"]
            if item["relation_state"] in {"potential", "structural"}
        ]
