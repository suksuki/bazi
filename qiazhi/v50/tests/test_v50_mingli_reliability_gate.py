from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from core.contracts import BirthInputCanonical
from core.life_case import (
    build_baseline_insight,
    build_domain_insight,
    commit_baseline_life_case,
    commit_domain_insight,
    validate_formal_insight,
)
from core.life_domains import LifeDomain
from core.mingli_agent import MingliAgent, compile_chart_world
from core.mingli_agent.contracts import DomainCausalReading, WholeChartCognitionDraft
from core.mingli_agent.reasoner import review_cognition, review_domain_reading
from core.mingli_agent.reliability import cognition_semantic_signature
from product.agent_case_store import MemoryAgentCaseStore
from product.agent_job_store import MemoryAgentJobStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from tests.test_v50_mingli_agent_refoundation import (
    FakeCognitiveModel,
    _birth_payload,
)


def _world(reading_id: str = "reading.reliability-gate"):
    return compile_chart_world(
        reading_id=reading_id,
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )


class OneRepairModel(FakeCognitiveModel):
    def __init__(self) -> None:
        self.baseline_calls = 0

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is WholeChartCognitionDraft:
            self.baseline_calls += 1
            if self.baseline_calls == 1:
                broken = result.useful_god_reasoning[0].model_copy(
                    update={"applicable_conditions": [], "invalidating_conditions": []}
                )
                return result.model_copy(update={"useful_god_reasoning": [broken]})
        return result


class CountingDomainModel(FakeCognitiveModel):
    def __init__(self) -> None:
        self.domain_calls = 0

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is DomainCausalReading:
            self.domain_calls += 1
        return result


class BaselineOverrideDomainModel(FakeCognitiveModel):
    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is DomainCausalReading:
            return result.model_copy(
                update={"stable_tendencies": ["事业专题要求推翻原有基线主假设。"]}
            )
        return result


class HardFactBaselineModel(FakeCognitiveModel):
    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is WholeChartCognitionDraft:
            hypotheses = list(result.hypotheses)
            hypotheses[0] = hypotheses[0].model_copy(
                update={"thesis": "火生金是这张盘已经成立的原局主路径。"}
            )
            return result.model_copy(update={"hypotheses": hypotheses})
        return result


class UncomparedBaselineModel(FakeCognitiveModel):
    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is WholeChartCognitionDraft:
            hypotheses = list(result.hypotheses)
            hypotheses[1] = hypotheses[1].model_copy(update={"rejection_reason": ""})
            return result.model_copy(update={"hypotheses": hypotheses})
        return result


def test_hard_chart_fact_conflict_blocks_formal_commit() -> None:
    world = _world("reading.fact-conflict")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="case.fact-conflict",
        world=world,
    )
    conflicted = record.cognition.model_copy(
        update={"whole_chart_thesis": "子午冲是这张盘的原局主轴。"}
    )
    review = review_cognition(draft=conflicted, world=world, model="test")
    blocked_record = record.model_copy(
        update={
            "cognition": conflicted,
            "review": review,
            "reliability_disposition": review.disposition,
            "reliability_signature": cognition_semantic_signature(conflicted),
        }
    )
    insight = build_baseline_insight(record=blocked_record, world=world)
    validation = validate_formal_insight(insight=insight, world=world)

    assert review.disposition == "blocked"
    assert review.commit_eligible is False
    assert any(code.startswith("professional_fact:") for code in review.hard_failure_codes)
    assert validation.passed is False
    assert "epistemic_state_not_committable:blocked" in validation.errors
    with pytest.raises(ValueError, match="formal_insight_validation_failed"):
        commit_baseline_life_case(insight=insight, world=world, profile_id=None)


def test_production_baseline_isolates_one_hard_fact_without_rejecting_the_case() -> None:
    record = MingliAgent(HardFactBaselineModel()).first_baseline_reading(
        case_id="case.raw-hard-fact",
        world=_world("reading.raw-hard-fact"),
    )

    assert record.review.disposition == "competing"
    assert record.review.commit_eligible is True
    assert all("火生金" not in item.thesis for item in record.cognition.hypotheses)
    isolated = next(
        item for item in record.assertion_gate.decisions if item.assertion_ref == "h1"
    )
    assert isolated.disposition == "suppressed"
    assert any(code.startswith("semantic:") for code in isolated.reason_codes)
    assert record.assertion_gate.automatic_full_rerun_allowed is False


def test_api_commits_safe_assertions_and_excludes_the_bad_assertion() -> None:
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(HardFactBaselineModel()),
        agent_case_store=store,
    ))
    response = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()})
    payload = response.json()
    row = store.get(case_id=payload["case_id"])

    assert response.status_code == 200
    assert payload["status"] == "first_reading_ready"
    assert payload["reading"]["pillars"]
    assert row["life_case"] is not None
    assert "火生金" not in str(row["life_case"])
    assert row["record"]["assertion_gate"]["suppressed_count"] == 1


def test_competing_api_preserves_both_explanations_in_formal_case() -> None:
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(UncomparedBaselineModel()),
        agent_case_store=store,
    ))
    response = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()})
    payload = response.json()
    row = store.get(case_id=payload["case_id"])

    assert response.status_code == 200
    assert payload["status"] == "first_reading_ready"
    assert payload["reading"]["reliability"]["state"] == "competing"
    assert row["life_case"] is not None
    uncertainty = row["life_case"]["baseline_insight"]["uncertainty"]
    assert uncertainty["competing_hypotheses"]


def test_incomplete_reasoning_is_locally_isolated_without_a_second_model_call() -> None:
    model = OneRepairModel()
    record = MingliAgent(model).first_baseline_reading(
        case_id="case.one-repair",
        world=_world("reading.one-repair"),
    )

    assert model.baseline_calls == 1
    assert [item["stage"] for item in record.stage_receipts] == ["baseline_cognition"]
    assert record.assertion_gate.candidate_count == 1
    assert record.cognition.useful_god_reasoning == []
    assert record.assertion_gate.automatic_full_rerun_allowed is False
    assert record.review.disposition == "reliable"


def test_competing_hypotheses_remain_visible_and_committable_as_competing() -> None:
    world = _world("reading.competing")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="case.competing",
        world=world,
    )
    hypotheses = list(record.cognition.hypotheses)
    hypotheses[0] = hypotheses[0].model_copy(update={"confidence": "low"})
    competing = record.cognition.model_copy(update={"hypotheses": hypotheses})
    review = review_cognition(draft=competing, world=world, model="test")
    competing_record = record.model_copy(
        update={
            "cognition": competing,
            "review": review,
            "reliability_disposition": review.disposition,
        }
    )
    validation = validate_formal_insight(
        insight=build_baseline_insight(record=competing_record, world=world),
        world=world,
    )

    assert review.passed is True
    assert review.disposition == "competing"
    assert review.commit_eligible is True
    assert validation.passed is True


def test_strategy_dimensions_are_explicit_and_mixed_is_blocked() -> None:
    world = _world("reading.strategy-dimensions")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="case.strategy-dimensions",
        world=world,
    )
    strategy = record.cognition.useful_god_reasoning[0]

    assert strategy.lens == "work_path"
    assert strategy.scope == "natal"
    assert strategy.question_answered

    mixed = strategy.model_copy(update={"lens": "mixed"})
    cognition = record.cognition.model_copy(update={"useful_god_reasoning": [mixed]})
    review = review_cognition(draft=cognition, world=world, model="test")
    assert review.disposition == "blocked"
    assert "ambiguous_strategy_dimension" in review.hard_failure_codes


def test_uncompared_alternative_is_competing_even_when_ranked_lower() -> None:
    world = _world("reading.uncompared-alternative")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="case.uncompared-alternative",
        world=world,
    )
    hypotheses = list(record.cognition.hypotheses)
    hypotheses[1] = hypotheses[1].model_copy(update={"rejection_reason": ""})
    cognition = record.cognition.model_copy(update={"hypotheses": hypotheses})
    review = review_cognition(draft=cognition, world=world, model="test")

    assert review.disposition == "competing"
    assert review.commit_eligible is True


def test_domain_cache_requires_same_question_and_exact_baseline() -> None:
    world = _world("reading.domain-cache")
    model = CountingDomainModel()
    agent = MingliAgent(model)
    record = agent.first_baseline_reading(case_id="case.domain-cache", world=world)
    baseline = build_baseline_insight(record=record, world=world)
    life_case, _ = commit_baseline_life_case(insight=baseline, world=world, profile_id=None)
    question = "我的职业价值如何形成？"
    first_events: list[str] = []
    first = agent.explore_domain(
        world=world,
        record=record,
        domain=LifeDomain.CAREER,
        user_question=question,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        baseline_case_version=life_case.case_version,
        on_stage=lambda event_type, _payload: first_events.append(event_type),
    )
    record = record.model_copy(
        update={"domain_explorations": {LifeDomain.CAREER: first}}
    )
    cached = agent.explore_domain(
        world=world,
        record=record,
        domain=LifeDomain.CAREER,
        user_question=question,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        baseline_case_version=life_case.case_version,
        on_stage=lambda event_type, _payload: first_events.append(event_type),
    )
    changed = agent.explore_domain(
        world=world,
        record=record,
        domain=LifeDomain.CAREER,
        user_question="我是否适合转向研究工作？",
        baseline_insight_id=life_case.baseline_insight.insight_id,
        baseline_case_version=life_case.case_version,
    )

    assert model.domain_calls == 2
    assert first_events == ["domain_baseline_reused", "domain_cache_reused"]
    assert cached.request_fingerprint == first.request_fingerprint
    assert changed.request_fingerprint != first.request_fingerprint


def test_progressive_domain_reuses_baseline_and_exact_cache() -> None:
    case_store = MemoryAgentCaseStore()
    job_store = MemoryAgentJobStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=case_store,
        agent_job_store=job_store,
    ))
    created = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()
    case_id = created["case_id"]

    def run() -> dict:
        started = client.post(
            f"/api/v50/agent/cases/{case_id}/domains/career",
            json={"progressive": True, "user_question": "职业价值如何形成？"},
        ).json()
        assert started["status"] == "domain_job_started"
        for _ in range(60):
            job = client.get(f"/api/v50/agent/jobs/{started['job_id']}").json()
            if job["status"] in {"completed", "failed"}:
                return job
            time.sleep(0.005)
        raise AssertionError("progressive domain did not finish")

    first = run()
    second = run()
    first_types = [item["event_type"] for item in first["events"]]
    second_types = [item["event_type"] for item in second["events"]]

    assert first["status"] == "completed"
    assert first_types == ["domain_baseline_reused", "domain_committed"]
    assert second_types == ["domain_cache_reused", "domain_committed"]
    assert second["events"][-1]["payload"]["cache_hit"] is True


def test_domain_commit_requires_exact_committed_baseline_references() -> None:
    world = _world("reading.domain-baseline")
    agent = MingliAgent(FakeCognitiveModel())
    record = agent.first_baseline_reading(case_id="case.domain-baseline", world=world)
    baseline = build_baseline_insight(record=record, world=world)
    life_case, _ = commit_baseline_life_case(insight=baseline, world=world, profile_id=None)
    exploration = agent.explore_domain(
        world=world,
        record=record,
        domain=LifeDomain.WEALTH,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        baseline_case_version=life_case.case_version,
    )
    insight = build_domain_insight(
        record=record,
        exploration=exploration,
        world=world,
        case_version=life_case.case_version,
    )
    updated, receipt = commit_domain_insight(
        life_case=life_case,
        insight=insight,
        world=world,
    )

    assert receipt.passed is True
    assert updated.domain_insights["wealth"][0].baseline_insight_id == baseline.insight_id
    mismatched = insight.model_copy(update={"baseline_semantic_signature": "wrong-signature"})
    with pytest.raises(ValueError, match="domain_baseline_reference_mismatch"):
        commit_domain_insight(life_case=life_case, insight=mismatched, world=world)


def test_domain_may_cite_current_baseline_cognition_but_not_invented_ids() -> None:
    world = _world("reading.domain-cognitive-refs")
    agent = MingliAgent(FakeCognitiveModel())
    record = agent.first_baseline_reading(case_id="case.domain-cognitive-refs", world=world)
    exploration = agent.explore_domain(world=world, record=record, domain=LifeDomain.CAREER)
    assertion = exploration.reading.assertions[0]
    cited = exploration.reading.model_copy(update={
        "assertions": [assertion.model_copy(update={"evidence_refs": ["h1"]})],
        "next_probe": exploration.reading.next_probe.model_copy(
            update={"distinguishes_hypothesis_refs": ["h1", "h2"]}
        ) if exploration.reading.next_probe else None,
    })
    accepted = review_domain_reading(
        reading=cited,
        world=world,
        model="test",
        baseline_record=record,
        expected_domain=LifeDomain.CAREER,
    )
    invented = cited.model_copy(update={
        "assertions": [assertion.model_copy(update={"evidence_refs": ["H_DOES_NOT_EXIST"]})],
    })
    rejected = review_domain_reading(
        reading=invented,
        world=world,
        model="test",
        baseline_record=record,
        expected_domain=LifeDomain.CAREER,
    )

    assert accepted.commit_eligible is True
    assert rejected.commit_eligible is False
    assert "unknown_evidence_refs" in rejected.hard_failure_codes


def test_domain_baseline_override_becomes_revision_candidate_not_insight() -> None:
    world = _world("reading.domain-revision")
    agent = MingliAgent(BaselineOverrideDomainModel())
    record = agent.first_baseline_reading(case_id="case.domain-revision", world=world)
    baseline = build_baseline_insight(record=record, world=world)
    life_case, _ = commit_baseline_life_case(insight=baseline, world=world, profile_id=None)
    exploration = agent.explore_domain(
        world=world,
        record=record,
        domain=LifeDomain.CAREER,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        baseline_case_version=life_case.case_version,
    )

    assert exploration.review.disposition == "blocked"
    assert "baseline_override_attempt" in exploration.review.hard_failure_codes
    assert exploration.case_revision_candidate is not None
    assert exploration.case_revision_candidate["baseline_record_id"] == record.record_id
