from __future__ import annotations

from copy import deepcopy

import pytest

from core.contracts import BirthInputCanonical
from core.life_case import (
    FormalInsightLifecycleState,
    build_baseline_insight,
    commit_baseline_life_case,
)
from core.life_domains import LifeDomain, domain_access_allowed
from core.mingli_agent import MingliAgent, MingliContextCompiler, compile_chart_world
from product.agent_case_store import MemoryAgentCaseStore
from product.agent_command_service import BaselineCaseCommand, BaselineCaseCommandService
from product.formal_insight_state import cognition_background, lifecycle_from_background
from tests.test_v50_flow_slim_01 import (
    CountingCognitiveModel,
    StreamingFailureModel,
    _bootstrap,
    _wait_for_job,
    _workspace_client,
)
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload


class EmptyBaselineKnowledgeCompiler(MingliContextCompiler):
    KNOWLEDGE_LIMITS = {**MingliContextCompiler.KNOWLEDGE_LIMITS, "baseline": 0}


class ImmediateFailureModel(StreamingFailureModel):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error

    def generate(
        self,
        *,
        prompt,
        schema,
        temperature=0.2,
        thinking=True,
        max_tokens=3200,
        on_text_chunk=None,
    ):
        del prompt, schema, temperature, thinking, max_tokens, on_text_chunk
        self.calls += 1
        raise self.error


def _direct_command(*, case_id: str, model=None, compiler=None):
    birth = BirthInputCanonical.model_validate(_birth_payload())
    world = compile_chart_world(reading_id=f"local-gate-03:{case_id}", birth_input=birth)
    store = MemoryAgentCaseStore()
    service = BaselineCaseCommandService(
        agent=MingliAgent(
            model or CountingCognitiveModel(),
            context_compiler=compiler,
        ),
        case_store=store,
    )
    command = BaselineCaseCommand(
        case_id=case_id,
        reading_id=world.reading_id,
        birth_input=birth,
        profile_id=f"profile:{case_id}",
        user_id="local-gate-03",
        active_mode="research",
        world=world,
    )
    return service, command, store, world


@pytest.mark.parametrize("status", ["draft", "partial", "reviewed", "failed"])
def test_only_active_committed_insight_is_formally_reusable(status: str) -> None:
    state = FormalInsightLifecycleState(status=status)

    assert state.formal_projection_eligible is False
    assert state.role_projection_eligible is False
    assert state.path_assertion_eligible is False
    assert state.reminder_eligible is False
    assert state.hidden_attribute_evidence_eligible is False


def test_active_committed_insight_is_the_only_fully_eligible_state() -> None:
    committed = FormalInsightLifecycleState(
        status="committed",
        active=True,
        persistence_status="persisted",
        professional_release_status="passed",
    )
    inactive = FormalInsightLifecycleState(
        status="committed",
        active=False,
        persistence_status="persisted",
        professional_release_status="passed",
    )
    legacy_unreviewed = FormalInsightLifecycleState(
        status="committed",
        active=True,
        persistence_status="persisted",
    )

    assert committed.complete is True
    assert all((
        committed.formal_projection_eligible,
        committed.role_projection_eligible,
        committed.path_assertion_eligible,
        committed.reminder_eligible,
        committed.hidden_attribute_evidence_eligible,
    ))
    assert inactive.formal_projection_eligible is False
    assert legacy_unreviewed.formal_projection_eligible is False
    assert inactive.path_assertion_eligible is False


@pytest.mark.parametrize("status", ["partial", "failed"])
def test_partial_or_failed_insight_cannot_be_committed_or_create_paths(status: str) -> None:
    service, command, _, world = _direct_command(case_id=f"unsafe-{status}")
    record = service._agent.first_baseline_reading(  # noqa: SLF001 - contract-level test.
        case_id=command.case_id,
        world=world,
    )
    unsafe = build_baseline_insight(record=record, world=world).model_copy(
        update={"status": status}
    )

    with pytest.raises(ValueError, match=f"formal_insight_status_not_committable:{status}"):
        commit_baseline_life_case(insight=unsafe, world=world, profile_id=None)


def test_background_state_has_one_derived_safety_contract() -> None:
    partial = cognition_background(
        operational_status="failed",
        insight_status="partial",
        partial_result={"first_look": "保留这一段"},
    )

    assert partial["insight_status"] == "partial"
    assert partial["insight_safety"]["formal_projection_eligible"] is False
    assert lifecycle_from_background(partial).status == "partial"
    assert lifecycle_from_background(
        {"status": "completed", "insight_status": "committed"},
        committed=True,
    ).formal_projection_eligible is False
    released = cognition_background(
        operational_status="completed",
        insight_status="committed",
        persistence_status="persisted",
        professional_release_status="passed",
    )
    assert lifecycle_from_background(released, committed=True).formal_projection_eligible is True


def test_repeated_command_reuses_committed_case_without_model_or_write() -> None:
    model = CountingCognitiveModel()
    service, command, store, _ = _direct_command(case_id="resume-existing", model=model)
    first = service.execute(command)
    before = deepcopy(store.get(case_id=command.case_id, user_id=command.user_id))

    second = service.execute(command)
    after = store.get(case_id=command.case_id, user_id=command.user_id)

    assert first.committed is True
    assert second.committed is True
    assert second.metrics["cache_hit"] is True
    assert second.metrics["model_calls"] == 0
    assert second.metrics["case_store_operations"] == {"reads": 1, "writes": 0}
    assert model.baseline_calls == 1
    assert after == before


def test_logout_and_login_resume_committed_case_without_recompute() -> None:
    client, _, _, model, profile_id = _workspace_client()
    case_id = _bootstrap(client, profile_id)["selected_case_id"]
    started = client.post(f"/api/v50/experience/workspace/cases/{case_id}/baseline")
    assert _wait_for_job(client, started.json()["job_id"])["status"] == "completed"
    assert model.baseline_calls == 1

    logged_out = client.post("/api/v50/product/auth/logout")
    assert logged_out.status_code == 200
    assert client.post(
        "/api/v50/experience/workspace/bootstrap",
        json={"profile_id": profile_id, "case_id": ""},
    ).status_code == 401
    logged_in = client.post(
        "/api/v50/product/auth/login",
        json={"email": "flow-slim@example.com", "password": "secure-pass-123"},
    )
    assert logged_in.status_code == 200

    resumed = _bootstrap(client, profile_id)

    assert resumed["selected_case_id"] == case_id
    assert resumed["cognition"]["status"] == "ready"
    assert resumed["cognition"]["cache_hit"] is True
    assert resumed["cognition"]["insight"]["status"] == "committed"
    assert model.baseline_calls == 1


def test_empty_knowledge_retrieval_can_still_form_a_traceable_baseline() -> None:
    service, command, _, _ = _direct_command(
        case_id="empty-knowledge",
        compiler=EmptyBaselineKnowledgeCompiler(),
    )

    result = service.execute(command)

    assert result.committed is True
    assert result.metrics["knowledge_retrieval_count"] == 0
    assert result.record.context_manifest[0]["knowledge_count"] == 0
    assert result.validation.passed is True


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (TimeoutError("synthetic_timeout"), "failed"),
        (ValueError("synthetic_parse_failure"), "failed"),
    ],
)
def test_timeout_and_parse_failure_never_create_formal_insight(error: Exception, expected_status: str) -> None:
    model = ImmediateFailureModel(error)
    client, case_store, _, _, profile_id = _workspace_client(model)
    case_id = _bootstrap(client, profile_id)["selected_case_id"]

    started = client.post(f"/api/v50/experience/workspace/cases/{case_id}/baseline")
    job = _wait_for_job(client, started.json()["job_id"])
    stored = case_store.get(case_id=case_id)

    assert job["status"] == "failed"
    assert stored is not None
    assert stored["life_case"] is None
    assert stored["background_cognition"]["insight_status"] == expected_status
    assert stored["background_cognition"]["insight_safety"]["formal_projection_eligible"] is False
    assert stored["background_cognition"]["automatic_full_reruns"] == 0
    assert model.calls == 1


def test_public_domain_boundary_is_whole_chart_career_and_wealth_only() -> None:
    assert all(
        domain_access_allowed(domain, role_mode="member")
        for domain in (LifeDomain.WHOLE_CHART, LifeDomain.CAREER, LifeDomain.WEALTH)
    )
    assert all(
        not domain_access_allowed(domain, role_mode="member")
        for domain in set(LifeDomain)
        - {LifeDomain.WHOLE_CHART, LifeDomain.CAREER, LifeDomain.WEALTH}
    )

    client, _, _, model, profile_id = _workspace_client()
    case_id = _bootstrap(client, profile_id)["selected_case_id"]
    started = client.post(f"/api/v50/experience/workspace/cases/{case_id}/baseline")
    assert _wait_for_job(client, started.json()["job_id"])["status"] == "completed"
    before = model.domain_calls

    timing = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/life_timing",
        json={"user_question": "我现在处于什么阶段？", "progressive": False},
    )
    abu = client.post(
        "/api/v50/agent/abu/resolve",
        json={
            "message": "我现在处于什么人生阶段",
            "has_case": True,
            "active_mode": "member",
            "active_domain": "whole_chart",
        },
    )

    assert timing.status_code == 403
    assert abu.status_code == 200
    assert abu.json()["plan"]["missing_requirements"] == ["capability_boundary"]
    assert model.domain_calls == before
