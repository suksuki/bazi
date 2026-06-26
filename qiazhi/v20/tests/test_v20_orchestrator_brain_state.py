from __future__ import annotations

from v20.access.projection import project_runtime_for_role
from v20.api.runtime import run_runtime_from_pillars


def test_v20_orchestrator_brain_state_summarizes_current_runtime_spine() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain_state",
        user_text="我想看事业和财运",
    )

    state = result["brain_state"]
    public = state["public_summary"]
    review = state["review_summary"]

    assert state["version"] == "v20.orchestrator_brain_state.v1"
    assert state["runtime_mutation"] is False
    assert public["primary_title"] == public["dynamic_work_path"]["label"]
    assert public["primary_title"] in public["headline"]
    assert public["primary_nodes"] == ["食伤", "官杀", "印星"]
    assert public["selection_reasons"]
    assert any("当前问题落在" in row for row in public["selection_reasons"])
    assert public["selected_question_key"] == result["selected_question"]["question_key"]
    assert public["question_focus_status"] == result["question_mainline_focus"]["status"]
    assert public["coordination_status"] in {"已对齐", "需复核", "未就绪"}
    assert public["coordination_note"]
    assert public["runtime_policy_coordination"]["version"] == "v20.brain_runtime_policy_coordination.v1"
    assert public["runtime_policy_coordination"]["status"] in {"applied", "baseline", "active_no_match", "not_applied"}
    assert isinstance(public["dynamic_chain"], str)
    assert "authority" not in public["dynamic_chain"]
    assert "resource" not in public["dynamic_chain"]
    assert isinstance(public["dynamic_work_path"], dict)
    assert public["dynamic_work_path"]["label"]
    assert public["dynamic_work_path"]["path"]
    assert "dynamic_path" not in str(public["dynamic_work_path"])
    assert isinstance(public["supporting_evidence"], list)
    assert public["supporting_evidence"]
    assert isinstance(public["knowledge_basis"], list)
    assert public["knowledge_basis"]
    assert isinstance(public["answer_guidance"], list)
    assert public["answer_guidance"]
    assert all("source_key" not in row for row in public["knowledge_basis"])
    assert all("evidence_id" not in row for row in public["knowledge_basis"])
    assert all("source_key" not in row for row in public["supporting_evidence"])
    assert all("evidence_id" not in row for row in public["supporting_evidence"])
    assert all("evidence." not in str(row) for row in public["supporting_evidence"])
    assert all("规则" not in str(row) for row in public["supporting_evidence"])
    assert review["evidence_count"] == result["orchestrator_evidence"]["evidence_count"]
    assert review["knowledge_evidence_count"] >= 1
    assert any(row["source_type"] == "knowledge_basis" for row in result["orchestrator_evidence"]["items"])
    assert any(row["source_type"] == "structure_dynamics_v2" for row in result["orchestrator_evidence"]["items"])
    assert "coordination_flags" in review
    assert "BRAIN_STATE_DOES_NOT_CREATE_FACTS" in state["guardrails"]
    assert result["reasoning_orchestrator"]["primary_outputs"]["brain_state"] == "brain_state.public_summary"
    assert any(row["step_key"] == "brain_state" for row in result["reasoning_orchestrator"]["steps"])


def test_v20_orchestrator_brain_state_is_role_projected_for_user() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain_state.role",
        user_text="我想看事业和财运",
    )

    user = project_runtime_for_role(result, "user")
    analyst = project_runtime_for_role(result, "analyst")

    assert "brain_state" in user
    assert "brain_state" in analyst
    assert "public_summary" in user["brain_state"]
    assert "review_summary" not in user["brain_state"]
    assert "review_summary" in analyst["brain_state"]
    assert "orchestrator_evidence" not in user


def test_v20_answer_consumes_public_brain_state_without_internal_markers() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain_state.answer",
        user_text="我想看事业和财运",
    )

    answer = result["answer_text"]

    assert "中枢判断：本轮先以" in answer
    assert "知识边界：" in answer
    assert result["brain_state"]["public_summary"]["selected_question_title"] in answer
    assert "RuleSpec" not in answer
    assert "evidence." not in answer
    assert "规则候选" not in answer
    assert "质量门" not in answer
    assert "综合权重" not in answer
    assert "复核标记：" not in answer
    assert "日主承载规则" not in answer


def test_v20_llm_context_pack_carries_public_brain_state() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain_state.llm",
        user_text="我想看事业和财运",
    )

    context_pack = result["llm_assist"]["context_pack"]
    rewrite_prompt = context_pack["task_contexts"]["answer_plan_rewrite"]["prompt"]
    rewrite_context = rewrite_prompt["context"]
    practitioner_context = context_pack["task_contexts"]["practitioner_answer"]["prompt"]

    assert rewrite_context["version"] == "v20.answer_rewrite_context.v2"
    assert rewrite_context["verified_answer_text"]
    assert rewrite_prompt["answer_contract"]["version"] == "v20.llm_answer_contract.v1"
    assert rewrite_context["brain_state"]["primary_title"] == result["brain_state"]["public_summary"]["primary_title"]
    assert rewrite_context["brain_state"]["selection_reasons"]
    assert rewrite_context["brain_state"]["answer_guidance"]
    assert rewrite_context["brain_state"]["coordination_status"] == result["brain_state"]["public_summary"]["coordination_status"]
    assert rewrite_context["brain_state"]["runtime_policy_coordination"]["status"] == result["brain_state"]["public_summary"]["runtime_policy_coordination"]["status"]
    assert practitioner_context["context_version"] == "v20.practitioner_answer_card.v2"
    assert practitioner_context["context"]["brain_state"]["primary_title"] == result["brain_state"]["public_summary"]["primary_title"]
    assert practitioner_context["context"]["brain_state"]["selection_reasons"]
    assert practitioner_context["context"]["brain_state"]["coordination_note"]
    assert practitioner_context["context"]["brain_state"]["selected_question_title"] == result["selected_question"]["title"]
    assert "source_key" not in str(practitioner_context["context"]["brain_state"])
    assert "evidence_id" not in str(practitioner_context["context"]["brain_state"])
    assert "规则" not in str(practitioner_context["context"]["brain_state"])
    assert "answer_plan" not in practitioner_context["context"]


def test_v20_brain_state_public_contract_stays_stable() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain_state.contract",
        user_text="我想看事业和财运",
    )

    public = result["brain_state"]["public_summary"]

    assert set(public) == {
        "headline",
        "primary_domain",
        "primary_title",
        "primary_nodes",
        "selection_reasons",
        "selected_question_key",
        "selected_question_title",
        "selected_question_domain",
        "question_focus_status",
        "coordination_status",
        "coordination_note",
        "dynamic_chain",
        "dynamic_work_path",
        "chain_state",
        "energy_state",
        "stability_state",
        "time_layer_status",
        "runtime_policy_coordination",
        "knowledge_basis",
        "answer_guidance",
        "supporting_evidence",
        "next_action",
    }
    assert all(isinstance(public[key], str) for key in (
        "headline",
        "primary_domain",
        "primary_title",
        "selected_question_key",
        "selected_question_title",
        "selected_question_domain",
        "question_focus_status",
        "coordination_status",
        "coordination_note",
        "dynamic_chain",
        "chain_state",
        "energy_state",
        "stability_state",
        "time_layer_status",
        "next_action",
    ))
    assert all("规则" not in str(value) for value in public.values())
    assert all("question_domain_focus" not in str(value) for value in public.values())
    assert public["supporting_evidence"][0]["label"] == "主线条件"
