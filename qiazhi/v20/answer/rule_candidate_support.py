from __future__ import annotations

from v20.answer.measurement_policy import feature_domains_for_applied_domain
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.rule_proposal import build_knowledge_rule_proposals


RULE_LABELS_ZH = {
    "strength": "日主强弱规则候选",
    "ten_god": "十神来源层规则候选",
    "useful_god": "用神候选规则候选",
    "element": "五行分布规则候选",
    "branch": "地支关系规则候选",
    "wealth": "财星材料规则候选",
    "pattern": "格局审查规则候选",
    "time": "时间层触发规则候选",
    "career": "事业投影规则候选",
    "relationship": "关系投影规则候选",
    "health": "健康边界规则候选",
}

CONDITION_LABELS_ZH = {
    "feature_hook_prefix_match": "匹配已编译命理特征前缀",
}


def build_rule_candidate_support(question: QuestionCandidate, *, limit: int = 4) -> dict[str, object]:
    domains = _candidate_domains(question.domain)
    candidates: list[dict[str, object]] = []
    for domain in domains:
        report = build_knowledge_rule_proposals(domain, limit=1)
        for proposal in report.get("proposals", ()):
            if not isinstance(proposal, dict):
                continue
            candidates.append(_safe_candidate(proposal))
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return {
        "version": "v20.answer_rule_candidate_support.v1",
        "status": "ready" if candidates else "empty",
        "selected_question_key": question.question_key,
        "selected_domain": question.domain,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "runtime_mutation": False,
        "guardrails": [
            "RULE_CANDIDATES_ARE_SHADOW_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_USER_VISIBLE_VERDICT_FROM_RULE_CANDIDATE",
        ],
    }


def rule_candidate_section_body(report: dict[str, object]) -> str:
    candidates = [row for row in report.get("candidates", ()) if isinstance(row, dict)]
    if not candidates:
        return "当前没有可展示的规则候选，回答只保留特征、知识依据和测算边界。"
    rows = []
    for row in candidates[:4]:
        rows.append(
            f"{row.get('label', '规则候选')}：{row.get('condition_summary', '')}，"
            f"{row.get('validation_summary', '')}"
        )
    return "；".join(rows) + "。这些规则候选只进入影子复核，不激活为用户可见断语。"


def _candidate_domains(domain: str) -> tuple[str, ...]:
    domains = [domain]
    domains.extend(feature_domains_for_applied_domain(domain))
    return tuple(dict.fromkeys(domains))


def _safe_candidate(proposal: dict[str, object]) -> dict[str, object]:
    domain = str(proposal.get("domain", ""))
    condition_model = proposal.get("condition_model", {})
    condition_type = ""
    condition_count = 0
    if isinstance(condition_model, dict):
        condition_type = str(condition_model.get("type", ""))
        all_of = condition_model.get("all_of", ())
        condition_count = len(all_of) if isinstance(all_of, list | tuple) else 0
    return {
        "rule_id": proposal.get("proposal_id", ""),
        "label": RULE_LABELS_ZH.get(domain, f"{domain}规则候选"),
        "domain": domain,
        "source_knowledge_id": proposal.get("source_knowledge_id", ""),
        "condition_summary": _condition_summary(condition_type, condition_count),
        "validation_summary": _validation_summary(proposal),
        "activation_scope": proposal.get("activation_scope", "shadow_training_and_candidate_rule_graph"),
        "status": proposal.get("status", "released_to_shadow_training"),
        "runtime_allowed": False,
        "guardrails": [
            "SAFE_RULE_CANDIDATE_SUMMARY",
            "INTERNAL_CONDITION_IDS_NOT_USER_VERDICTS",
            "PROMOTION_REQUIRED_BEFORE_RUNTIME_ACTIVATION",
        ],
    }


def _condition_summary(condition_type: str, condition_count: int) -> str:
    label = CONDITION_LABELS_ZH.get(condition_type, "匹配已编译命理结构条件")
    if condition_count:
        return f"碰撞条件为{label}，共 {condition_count} 组前置条件"
    return f"碰撞条件为{label}"


def _validation_summary(proposal: dict[str, object]) -> str:
    requirements = proposal.get("validation_requirements", ())
    count = len(requirements) if isinstance(requirements, tuple | list) else 0
    if count:
        return f"需通过 {count} 项验证后才可晋升"
    return "需通过合成验证和决策记录后才可晋升"
