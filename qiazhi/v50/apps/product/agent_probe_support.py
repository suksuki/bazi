from __future__ import annotations

from typing import Any

from core.mingli_agent import CaseBeliefState, ProbePlan
from core.mingli_agent.contracts import CaseTurnDraft


def probe_revision_request(
    *,
    plan: ProbePlan,
    option_label: str,
    evidence: dict[str, Any],
    workspace: CaseBeliefState,
) -> str:
    return f"""
[结构化案例证据复审]
这不是让你重新排盘，也不是让你迎合用户。请比较封存的先验命局认知与下面的新证据，只修正受影响的案例判断。

Probe 目标：{plan.purpose}
用户选择：{option_label}
证据：{evidence}
案例 Belief：{workspace.model_dump(mode='json')}

要求：
- interaction_type 必须是 feedback_revision；
- abu_message 简洁说明现在更倾向哪种理解；
- interpretation 明确什么改变、什么没有改变；
- changed_assertions 只包含真正受影响的案例断言；
- 不修改四柱、十神、时序计算或全局理论；
- 不重复用户原问题和完整回答；
- 若证据不足，明确保留两种解释，不假装已经确定；
- next_probe 只有在能显著区分剩余假设时才提供一个。
""".strip()


def fallback_probe_revision(*, plan: ProbePlan, option_label: str) -> CaseTurnDraft:
    selected = next((item for item in plan.options if item.label == option_label), None)
    return CaseTurnDraft(
        interaction_type="feedback_revision",
        abu_message="这条现实线索已进入当前命盘的案例理解，但还不足以单独推翻整盘判断。",
        canvas_focus="overview",
        interpretation=f"当前只修正 {plan.domain.value} 范围内的表现方式；四柱、原局结构和全局理论保持不变。",
        hypothesis_updates=selected.hypothesis_updates if selected else {},
        changed_assertions=[],
        retained_assertion_ids=plan.target_assertion_ids,
        next_probe=None,
        suggested_actions=[],
        evidence_refs=[],
    )


def public_revision(revision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not revision:
        return None
    turn = revision.get("turn") or {}
    return {
        "revision_id": revision.get("evidence_id"),
        "summary": turn.get("abu_message") or "当前案例理解已修正。",
        "interpretation": turn.get("interpretation") or "原局事实保持不变。",
        "changed_assertions": [
            {
                "assertion_id": item.get("assertion_id"),
                "domain": item.get("domain"),
                "claim": item.get("claim"),
                "epistemic_status": item.get("epistemic_status"),
            }
            for item in turn.get("changed_assertions", [])
        ],
        "affected_hidden_attributes": revision.get("affected_hidden_attributes", []),
        "chart_facts_modified": False,
    }
