from __future__ import annotations

from v30.brain.judge import BRAIN_JUDGE_VERSION, judge_final_synthesis_quality


FINAL_SYNTHESIS_ENGINE_VERSION = "v30.final_synthesis_engine.v1"
FINAL_SYNTHESIS_VERSION = "v30.final_synthesis.v1"


def build_final_synthesis(
    *,
    diagnosis: dict[str, object],
    claim_scores: list[dict[str, object]],
    practical_reading_context: dict[str, object],
    feedback_weight_update: dict[str, object],
    central_feedback_overlay: dict[str, object] | None = None,
    synthesis_policy: dict[str, object] | None = None,
    decision_result: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = synthesis_policy if isinstance(synthesis_policy, dict) else {}
    claims = _claims_by_id(diagnosis)
    paths = _paths_by_id(diagnosis)
    portraits = _portraits_by_id(diagnosis)
    decision_verdicts = _decision_verdicts(decision_result or {})
    ranked_scores = _policy_ranked_claim_scores(claim_scores, policy)
    top_claims = _verdict_rows(decision_verdicts) if decision_verdicts else [
        _claim_row(score, claims.get(str(score.get("claim_id") or ""), {}), paths=paths, portraits=portraits)
        for score in ranked_scores[:6]
        if isinstance(score, dict)
    ]
    top_claims = [row for row in top_claims if row.get("claim_text")]
    primary = top_claims[0] if top_claims else {}
    focus_domains = _focus_domains(top_claims, practical_reading_context)
    evidence_chain = _evidence_chain(top_claims)
    feedback_summary = _feedback_summary(feedback_weight_update)
    feedback_overlay_summary = _feedback_overlay_summary(central_feedback_overlay or {})
    synthesis_blueprint = _synthesis_blueprint(
        primary=primary,
        top_claims=top_claims,
        focus_domains=focus_domains,
        practical=practical_reading_context,
        evidence_chain=evidence_chain,
        feedback_summary=feedback_summary,
        feedback_overlay_summary=feedback_overlay_summary,
    )
    conclusion = _conclusion(synthesis_blueprint)
    advice = _advice(synthesis_blueprint)
    visual_hint = _visual_hint(
        primary=primary,
        focus_domains=focus_domains,
        evidence_chain=evidence_chain,
        feedback_summary=feedback_summary,
    )
    brain_judge = judge_final_synthesis_quality(
        conclusion=conclusion,
        advice=advice,
        evidence_chain=evidence_chain,
        top_claims=top_claims,
        feedback_summary=feedback_summary,
    )
    min_quality_score = _policy_float(policy, "min_quality_score", 0.58)
    return {
        "version": FINAL_SYNTHESIS_VERSION,
        "engine_version": FINAL_SYNTHESIS_ENGINE_VERSION,
        "brain_judge_version": BRAIN_JUDGE_VERSION,
        "status": "ready" if top_claims else "insufficient_claims",
        "primary_domain": str(primary.get("domain") or (focus_domains[0] if focus_domains else "overview")),
        "focus_domains": focus_domains,
        "conclusion": conclusion,
        "advice": advice,
        "evidence_chain": evidence_chain,
        "top_claims": top_claims,
        "feedback_summary": feedback_summary,
        "feedback_overlay_summary": feedback_overlay_summary,
        "decision_engine": _decision_engine_summary(decision_result or {}, decision_verdicts),
        "decision_verdicts": decision_verdicts[:6],
        "synthesis_blueprint": synthesis_blueprint,
        "visual_hint": visual_hint,
        "brain_judge": brain_judge,
        "synthesis_policy_effect": _public_synthesis_policy_effect(policy, brain_judge),
        "customer_summary": _customer_summary(conclusion, advice),
        "quality_contract": {
            "version": "v30.final_synthesis_quality_contract.v1",
            "conclusion_first": str(conclusion).startswith("结论："),
            "advice_actionable": bool(brain_judge.get("accepted")) and float(brain_judge.get("quality_score") or 0.0) >= min_quality_score,
            "uses_traceable_claims": bool(top_claims),
            "uses_decision_verdicts": bool(decision_verdicts),
            "brain_judge_accepted": bool(brain_judge.get("accepted")),
            "brain_judge_quality_score": float(brain_judge.get("quality_score") or 0.0),
            "min_quality_score": min_quality_score,
            "synthesis_policy_applied": bool(policy.get("version")),
            "llm_can_rewrite_expression_only": True,
            "chart_fact_mutation_allowed": False,
            "boundary": "final_synthesis_quality_contract_blocks_untraceable_or_template_verdicts",
        },
        "training_signal": {
            "version": "v30.training_signal.final_synthesis.v1",
            "trainable": True,
            "targets": [
                "claim_selection_for_final_synthesis",
                "domain_priority_weight",
                "advice_actionability_weight",
                "feedback_to_synthesis_weight",
                "central_feedback_overlay_to_synthesis_weight",
                "evidence_chain_ordering",
                "synthesis_blueprint_quality",
                "central_brain_judge_quality",
                "final_synthesis_template_risk",
                "decision_verdict_expression_quality",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "base_diagnosis_claim_text",
                "untraceable_fortune_verdict",
            ],
        },
        "boundary": "final_synthesis_uses_ranked_claims_feedback_and_practical_context_without_mutating_chart_facts",
    }


def _policy_ranked_claim_scores(
    claim_scores: list[dict[str, object]],
    synthesis_policy: dict[str, object],
) -> list[dict[str, object]]:
    if not synthesis_policy.get("version"):
        return claim_scores
    weights = synthesis_policy.get("weights")
    weights = weights if isinstance(weights, dict) else {}
    evidence_weight = _policy_float(weights, "evidence_binding", 1.0)
    advice_weight = _policy_float(weights, "advice_actionability", 1.0)
    overclaim_penalty = _policy_float(weights, "overclaim_risk_penalty", 1.0)

    def adjusted_score(row: dict[str, object]) -> float:
        components = row.get("components")
        components = components if isinstance(components, dict) else {}
        base = _float(row.get("score"), 0.0)
        evidence = _float(components.get("evidence_diversity"), 0.0)
        actionability = _float(components.get("actionability"), 0.0)
        overclaim = _float(components.get("overclaim_risk"), 0.0)
        return round(
            base
            + min(0.025, max(0.0, evidence_weight - 1.0) * evidence)
            + min(0.025, max(0.0, advice_weight - 1.0) * actionability)
            - min(0.035, max(0.0, overclaim_penalty - 1.0) * overclaim),
            6,
        )

    return sorted(claim_scores, key=lambda row: (-adjusted_score(row), str(row.get("claim_id") or "")))


def _decision_verdicts(decision_result: dict[str, object]) -> list[dict[str, object]]:
    verdicts = decision_result.get("verdicts") if isinstance(decision_result, dict) else []
    rows = [row for row in _list(verdicts) if isinstance(row, dict)]
    return sorted(rows, key=lambda row: (-_assertion_rank(str(row.get("assertion_level") or "")), -_float(row.get("confidence"), 0.0), str(row.get("domain") or "")))


def _verdict_rows(verdicts: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for verdict in verdicts[:6]:
        allowed = [str(row) for row in _list(verdict.get("allowed_assertions")) if str(row)]
        advice_points = [str(row) for row in _list(verdict.get("advice_points")) if str(row)]
        evidence_refs = [str(row) for row in _list(verdict.get("evidence_refs")) if str(row)]
        rows.append(
            {
                "claim_id": str(verdict.get("primary_branch_id") or verdict.get("verdict_id") or ""),
                "verdict_id": str(verdict.get("verdict_id") or ""),
                "domain": str(verdict.get("domain") or "overview"),
                "claim_level": str(verdict.get("assertion_level") or ""),
                "claim_text": _clean_claim_text(str(verdict.get("headline") or "")),
                "raw_claim_text_available": bool(str(verdict.get("headline") or "")),
                "score": _float(verdict.get("confidence"), 0.0),
                "confidence_band": str(verdict.get("assertion_level") or ""),
                "assertion_level": str(verdict.get("assertion_level") or ""),
                "requires_question": bool(_list(verdict.get("next_question_slots"))),
                "feedback_alignment": _float(_nested(_dict(verdict.get("trace")), "score_components", "feedback_alignment"), 0.0),
                "feedback_contradiction": _float(_nested(_dict(verdict.get("trace")), "score_components", "feedback_contradiction"), 0.0),
                "path_labels": evidence_refs[:3],
                "portrait_statements": [],
                "allowed_assertions": allowed,
                "forbidden_assertions": [str(row) for row in _list(verdict.get("forbidden_assertions")) if str(row)],
                "advice_points": advice_points,
                "alternative_branch_ids": [str(row) for row in _list(verdict.get("alternative_branch_ids")) if str(row)],
                "boundary": "final_synthesis_verdict_row_consumes_decision_verdict_not_llm_text",
            }
        )
    return rows


def _decision_engine_summary(decision_result: dict[str, object], verdicts: list[dict[str, object]]) -> dict[str, object]:
    if not decision_result:
        return {
            "version": "v30.final_synthesis_decision_engine_summary.v1",
            "status": "missing",
            "uses_decision_verdicts": False,
            "boundary": "legacy_final_synthesis_without_decision_engine_result",
        }
    return {
        "version": "v30.final_synthesis_decision_engine_summary.v1",
        "status": "ready" if verdicts else "no_verdicts",
        "engine_version": str(decision_result.get("engine_version") or ""),
        "uses_decision_verdicts": bool(verdicts),
        "verdict_count": len(verdicts),
        "blocked_verdict_count": int(_float(decision_result.get("blocked_verdict_count"), 0.0)),
        "llm_expression_only": bool(_dict(decision_result.get("llm_expression_contract")).get("llm_can_rewrite_expression_only")),
        "chart_fact_mutation_allowed": bool(decision_result.get("chart_fact_mutation_allowed")),
        "boundary": "final_synthesis_consumes_decision_verdicts_before_llm_expression",
    }


def _assertion_rank(level: str) -> int:
    return {
        "confirmed": 5,
        "supported": 4,
        "mixed": 3,
        "weak_candidate": 2,
        "blocked": 1,
    }.get(level, 0)


def _assertion_level_label(level: str) -> str:
    return {
        "confirmed": "可明确断",
        "supported": "证据支持",
        "mixed": "分支并存",
        "weak_candidate": "候选待复核",
        "blocked": "暂不下断",
    }.get(level, level or "候选")


def _public_synthesis_policy_effect(policy: dict[str, object], brain_judge: dict[str, object]) -> dict[str, object]:
    if not policy.get("version"):
        return {
            "version": "v30.central_brain_synthesis_policy_effect.v1",
            "status": "baseline",
            "applied": False,
            "boundary": "synthesis_policy_effect_reports_quality_policy_without_chart_fact_mutation",
        }
    weights = policy.get("weights")
    weights = weights if isinstance(weights, dict) else {}
    return {
        "version": "v30.central_brain_synthesis_policy_effect.v1",
        "status": "applied",
        "applied": True,
        "source_policy_version": str(policy.get("version") or ""),
        "source_signal_id": str(policy.get("source_signal_id") or ""),
        "quality_observation_count": int(_policy_float(policy, "quality_observation_count", 0.0)),
        "accepted_rate": round(_policy_float(policy, "accepted_rate", 0.0), 3),
        "min_quality_score": _policy_float(policy, "min_quality_score", 0.58),
        "judge_quality_score": round(_float(brain_judge.get("quality_score"), 0.0), 3),
        "weights": {
            key: round(_policy_float(weights, key, 1.0), 3)
            for key in [
                "final_synthesis_quality",
                "evidence_binding",
                "conclusion_strength",
                "advice_actionability",
                "template_risk_penalty",
                "overclaim_risk_penalty",
            ]
        },
        "can_tune_chart_facts": False,
        "boundary": "synthesis_policy_effect_reports_quality_policy_without_chart_fact_mutation",
    }


def _claims_by_id(diagnosis: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("claim_id") or ""): row
        for row in _list(diagnosis.get("claims"))
        if isinstance(row, dict)
    }


def _paths_by_id(diagnosis: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("path_id") or ""): row
        for row in _list(diagnosis.get("paths"))
        if isinstance(row, dict)
    }


def _portraits_by_id(diagnosis: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("portrait_id") or ""): row
        for row in _list(diagnosis.get("portraits"))
        if isinstance(row, dict)
    }


def _claim_row(
    score: dict[str, object],
    claim: dict[str, object],
    *,
    paths: dict[str, dict[str, object]],
    portraits: dict[str, dict[str, object]],
) -> dict[str, object]:
    path_ids = [str(row) for row in _list(claim.get("path_ids"))]
    portrait_ids = [str(row) for row in _list(claim.get("portrait_ids"))]
    return {
        "claim_id": str(score.get("claim_id") or claim.get("claim_id") or ""),
        "domain": str(score.get("domain") or claim.get("domain") or "overview"),
        "claim_level": str(score.get("claim_level") or claim.get("claim_level") or ""),
        "claim_text": _clean_claim_text(str(claim.get("claim_text") or "")),
        "raw_claim_text_available": bool(str(claim.get("claim_text") or "")),
        "score": _float(score.get("score"), 0.0),
        "confidence_band": str(score.get("confidence_band") or claim.get("confidence_band") or ""),
        "requires_question": bool(score.get("requires_question")),
        "feedback_alignment": _float(_nested(score, "components", "feedback_alignment"), 0.0),
        "feedback_contradiction": _float(_nested(score, "components", "feedback_contradiction"), 0.0),
        "path_labels": [_path_label(paths.get(path_id, {})) for path_id in path_ids[:3]],
        "portrait_statements": [
            str(portraits.get(portrait_id, {}).get("statement") or "")
            for portrait_id in portrait_ids[:3]
            if str(portraits.get(portrait_id, {}).get("statement") or "")
        ],
        "boundary": "final_synthesis_claim_row_is_traceable_ranked_input_not_new_fact",
    }


def _focus_domains(top_claims: list[dict[str, object]], practical: dict[str, object]) -> list[str]:
    domains: list[str] = []
    for row in top_claims:
        domain = str(row.get("domain") or "")
        if domain and domain not in {"overview", "structure"} and domain not in domains:
            domains.append(domain)
    domain_readings = practical.get("domain_readings") if isinstance(practical, dict) else {}
    if isinstance(domain_readings, dict):
        ranked = sorted(
            [
                (str(domain), _float(payload.get("priority_score"), 0.0))
                for domain, payload in domain_readings.items()
                if isinstance(payload, dict)
            ],
            key=lambda row: (-row[1], row[0]),
        )
        for domain, _score in ranked:
            if domain and domain not in domains:
                domains.append(domain)
    return domains[:3] or ["overview"]


def _synthesis_blueprint(
    *,
    primary: dict[str, object],
    top_claims: list[dict[str, object]],
    focus_domains: list[str],
    practical: dict[str, object],
    evidence_chain: list[dict[str, object]],
    feedback_summary: dict[str, object],
    feedback_overlay_summary: dict[str, object],
) -> dict[str, object]:
    primary_domain = str(primary.get("domain") or (focus_domains[0] if focus_domains else "overview"))
    core_claim = _clean_claim_text(str(primary.get("claim_text") or "")) or f"{_domain_label(primary_domain)}需要先收束主线"
    evidence_handles = _evidence_handles(primary, evidence_chain)
    domain_payload = _domain_payload(practical, primary_domain)
    action_steps = _action_steps(primary_domain, domain_payload)
    verdict_advice = [_normalize_action_step(str(row)) for row in _list(primary.get("advice_points")) if str(row)]
    if verdict_advice:
        action_steps = verdict_advice[:3]
    risk_boundary = _risk_boundary(primary, top_claims, feedback_summary)
    forbidden_assertions = [str(row).strip(" 。") for row in _list(primary.get("forbidden_assertions")) if str(row)]
    if forbidden_assertions:
        risk_boundary = forbidden_assertions[0]
    feedback_focus = str(feedback_overlay_summary.get("focus_text") or "")
    if feedback_focus and risk_boundary:
        risk_boundary = f"{risk_boundary}；并复核{feedback_focus}"
    elif feedback_focus:
        risk_boundary = f"忽略{feedback_focus}"
    decision_focus = _decision_focus(primary_domain, core_claim, evidence_handles)
    return {
        "version": "v30.final_synthesis_blueprint.v1",
        "primary_domain": primary_domain,
        "domain_label": _domain_label(primary_domain),
        "core_claim": core_claim,
        "decision_focus": decision_focus,
        "evidence_handles": evidence_handles,
        "action_steps": action_steps,
        "risk_boundary": risk_boundary,
        "confidence_band": str(primary.get("confidence_band") or ""),
        "assertion_level": str(primary.get("assertion_level") or ""),
        "allowed_assertions": [str(row) for row in _list(primary.get("allowed_assertions")) if str(row)],
        "forbidden_assertions": forbidden_assertions,
        "requires_question": bool(primary.get("requires_question")),
        "claim_count": len(top_claims),
        "feedback_signal_count": int(feedback_summary.get("active_signal_count") or 0),
        "feedback_overlay_focus": feedback_focus,
        "boundary": "final_synthesis_blueprint_structures_existing_claims_evidence_and_actions_not_new_facts",
    }


def _feedback_overlay_summary(overlay: dict[str, object]) -> dict[str, object]:
    if not overlay:
        return {
            "version": "v30.final_synthesis_feedback_overlay_summary.v1",
            "effect_count": 0,
            "focus_text": "",
            "boundary": "no_feedback_overlay_available",
        }
    domain_deltas = overlay.get("domain_deltas") if isinstance(overlay.get("domain_deltas"), dict) else {}
    ranked = sorted(
        [(str(domain), _float(delta, 0.0)) for domain, delta in domain_deltas.items()],
        key=lambda row: (-abs(row[1]), row[0]),
    )
    focus = ""
    if ranked:
        domain, delta = ranked[0]
        focus = f"{_domain_label(domain)}反馈权重{'升高' if delta > 0 else '降低'}"
    return {
        "version": "v30.final_synthesis_feedback_overlay_summary.v1",
        "effect_count": int(_float(overlay.get("effect_count"), 0.0)),
        "question_outcome_count": int(_float(overlay.get("question_outcome_count"), 0.0)),
        "practitioner_selection_count": int(_float(overlay.get("practitioner_selection_count"), 0.0)),
        "domain_deltas": domain_deltas,
        "focus_text": focus,
        "chart_fact_mutation_allowed": False,
        "boundary": "feedback_overlay_summary_guides_final_expression_without_new_facts",
    }


def _conclusion(blueprint: dict[str, object]) -> str:
    domain_label = str(blueprint.get("domain_label") or "整体")
    core_claim = str(blueprint.get("core_claim") or "")
    decision_focus = str(blueprint.get("decision_focus") or "")
    assertion_level = str(blueprint.get("assertion_level") or "")
    evidence = [str(row) for row in _list(blueprint.get("evidence_handles")) if row]
    evidence_text = "、".join(evidence[:2]) if evidence else "可追溯证据链"
    if assertion_level:
        level_text = _assertion_level_label(assertion_level)
        if core_claim:
            return f"结论：{domain_label}主线为“{core_claim}”；断语等级是{level_text}，依据是{evidence_text}，判断重点是{decision_focus}。"
        return f"结论：{domain_label}暂按{level_text}处理；依据是{evidence_text}，判断重点是{decision_focus}。"
    if core_claim:
        return f"结论：{domain_label}主线落在“{core_claim}”；核心依据是{evidence_text}，判断重点收束为{decision_focus}。"
    return f"结论：{domain_label}主线需要围绕{decision_focus}收束；核心依据是{evidence_text}。"


def _advice(blueprint: dict[str, object]) -> str:
    domain_label = str(blueprint.get("domain_label") or "整体")
    action_steps = [str(row) for row in _list(blueprint.get("action_steps")) if row]
    risk_boundary = str(blueprint.get("risk_boundary") or "")
    first = action_steps[0] if action_steps else f"把{domain_label}选择拆成一个可执行动作"
    second = action_steps[1] if len(action_steps) > 1 else "保留一个可校准的反馈点"
    if risk_boundary:
        return f"建议：先{first}，再{second}；避免{risk_boundary}。"
    return f"建议：先{first}，再{second}。"


def _evidence_handles(primary: dict[str, object], evidence_chain: list[dict[str, object]]) -> list[str]:
    handles: list[str] = []
    for row in evidence_chain[:2]:
        for item in _list(row.get("evidence")) if isinstance(row, dict) else []:
            text = str(item).strip()
            if text and text not in handles:
                handles.append(text)
    if not handles:
        for item in _list(primary.get("path_labels")) + _list(primary.get("portrait_statements")):
            text = str(item).strip()
            if text and text not in handles:
                handles.append(text)
    return handles[:3]


def _domain_payload(practical: dict[str, object], domain: str) -> dict[str, object]:
    domain_readings = practical.get("domain_readings") if isinstance(practical, dict) else {}
    if not isinstance(domain_readings, dict):
        return {}
    payload = domain_readings.get(domain, {})
    return payload if isinstance(payload, dict) else {}


def _action_steps(domain: str, payload: dict[str, object]) -> list[str]:
    action_prompt = _normalize_action_step(str(payload.get("action_prompt") or ""))
    takeaway = _normalize_action_step(str(payload.get("customer_takeaway") or payload.get("summary") or ""))
    defaults = {
        "career": ["把职责压力拆成资质、规则和可交付成果", "确认平台或岗位是否能承接这条路径"],
        "wealth": ["区分主动争取、合作分配和保守积累三种财务动作", "先设定风险边界再谈收益节奏"],
        "relationship": ["确认互动模式和反复矛盾的触发点", "提前立住表达、距离和承诺边界"],
        "health": ["把压力来源、作息节律和身体反馈分开记录", "先调整最消耗精力的一项习惯"],
        "timing": ["把大运流年的触发点对应到具体选择", "用年份线索校准变化节奏"],
        "hidden_factor": ["用一个低成本问题确认隐藏线索", "只把已确认回答纳入后续判断"],
    }
    steps = [row for row in [action_prompt, takeaway] if row]
    for row in defaults.get(domain, ["确定一个现实选择", "用后续问答校准风险边界"]):
        if row not in steps:
            steps.append(row)
    return steps[:3]


def _risk_boundary(
    primary: dict[str, object],
    top_claims: list[dict[str, object]],
    feedback_summary: dict[str, object],
) -> str:
    if bool(primary.get("requires_question")):
        return "在关键背景未确认前直接扩大结论"
    if _float(primary.get("feedback_contradiction"), 0.0) > 0:
        return "忽略用户反馈里的反证信号"
    if any(bool(row.get("requires_question")) for row in top_claims[:3]):
        return "把需要追问的候选判断当成固定结论"
    if int(feedback_summary.get("active_signal_count") or 0) <= 0:
        return "没有现实反馈时一次性铺开过多方向"
    return "把单一证据当成全局判断"


def _decision_focus(domain: str, core_claim: str, evidence_handles: list[str]) -> str:
    if domain == "career":
        return "职责压力能否转成资质、平台和可交付成果"
    if domain == "wealth":
        return "赚钱方式、风险边界和分配结构"
    if domain == "relationship":
        return "互动模式、反复矛盾和边界建立"
    if domain == "health":
        return "压力节律、作息承载和可调整习惯"
    if domain == "timing":
        return "触发年份、节奏变化和现实选择"
    if domain == "hidden_factor":
        return "隐藏线索是否足以改变后续判断"
    if evidence_handles:
        return str(evidence_handles[0])
    return core_claim[:24] or "核心主线"


def _normalize_action_step(text: str) -> str:
    clean = text.strip(" 。；;")
    for prefix in ("建议：", "先", "请先"):
        clean = clean.removeprefix(prefix).strip(" ，,")
    return clean


def _evidence_chain(top_claims: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for claim in top_claims[:4]:
        evidence = [row for row in _list(claim.get("path_labels")) if row]
        if not evidence:
            evidence = [row for row in _list(claim.get("portrait_statements")) if row][:2]
        rows.append(
            {
                "claim_id": str(claim.get("claim_id") or ""),
                "domain": str(claim.get("domain") or ""),
                "score": _float(claim.get("score"), 0.0),
                "evidence": evidence[:3],
                "boundary": "evidence_chain_explains_final_synthesis_source_not_raw_trace",
            }
        )
    return rows


def _feedback_summary(feedback_weight_update: dict[str, object]) -> dict[str, object]:
    summary = feedback_weight_update.get("summary") if isinstance(feedback_weight_update, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    return {
        "active_signal_count": int(feedback_weight_update.get("active_signal_count") or 0) if isinstance(feedback_weight_update, dict) else 0,
        "positive_claim_ids": [str(row) for row in _list(summary.get("positive_claim_ids"))][:5],
        "negative_claim_ids": [str(row) for row in _list(summary.get("negative_claim_ids"))][:5],
        "boundary": "feedback_summary_in_final_synthesis_is_weight_context_not_chart_fact",
    }


def _visual_hint(
    *,
    primary: dict[str, object],
    focus_domains: list[str],
    evidence_chain: list[dict[str, object]],
    feedback_summary: dict[str, object],
) -> dict[str, object]:
    primary_domain = str(primary.get("domain") or (focus_domains[0] if focus_domains else "overview"))
    evidence_strength = min(1.0, len(evidence_chain) / 4)
    feedback_count = int(feedback_summary.get("active_signal_count") or 0)
    feedback_strength = min(1.0, feedback_count / 6)
    score = _float(primary.get("score"), 0.0)
    return {
        "version": "v30.final_synthesis_visual_hint.v1",
        "kind": _visual_kind(primary_domain),
        "title": f"{_domain_label(primary_domain)}主线",
        "chips": [
            _domain_label(primary_domain),
            f"证据链 {len(evidence_chain)}",
            f"反馈校准 {feedback_count}",
        ][:4],
        "markers": [
            {"label": "结论强度", "value": score or 0.5},
            {"label": "证据覆盖", "value": evidence_strength},
            {"label": "反馈校准", "value": feedback_strength},
        ],
        "guidance": _visual_guidance(primary_domain),
        "boundary": "final_synthesis_visual_hint_projects_structured_result_not_llm_text_or_raw_trace",
    }


def _visual_kind(domain: str) -> str:
    return {
        "career": "career_path_card",
        "wealth": "wealth_risk_meter",
        "relationship": "relationship_pattern_loop",
        "health": "health_rhythm_marker",
        "timing": "timing_trigger_line",
        "hidden_factor": "hidden_signal_map",
    }.get(domain, "advice_compass")


def _visual_guidance(domain: str) -> str:
    if domain == "career":
        return "先看职责压力能否转成资质、平台或可交付成果。"
    if domain == "wealth":
        return "先看赚钱方式、风险边界和合作分配结构。"
    if domain == "relationship":
        return "先看互动模式、反复矛盾和需要提前立住的边界。"
    if domain == "health":
        return "先看压力节律、作息承载和可调整的生活边界。"
    if domain == "timing":
        return "先看大运流年触发点，不把单一年份直接当定论。"
    return "先围绕当前主线做一个可执行选择，再用问答继续校准。"


def _customer_summary(conclusion: str, advice: str) -> str:
    conclusion_text = conclusion.removeprefix("结论：").strip()
    advice_text = advice.removeprefix("建议：").strip()
    return f"结论：{conclusion_text} 建议：{advice_text}"


def _clean_claim_text(text: str) -> str:
    blocked_fragments = [
        "不作为固定人生结论",
        "不作为具体人生结果断语",
        "只作为结构路径说明",
        "只作为规则投影",
        "不能独立制造事件结论",
        "不是以合冲刑害单点下结论",
    ]
    pieces = []
    for raw in text.replace("；", "。").split("。"):
        sentence = raw.strip()
        if not sentence:
            continue
        if any(fragment in sentence for fragment in blocked_fragments):
            continue
        pieces.append(sentence)
    cleaned = "。".join(pieces).strip(" 。")
    cleaned = _dedupe_label_prefix(cleaned)
    if cleaned.endswith(("：", ":")):
        return ""
    return cleaned


def _dedupe_label_prefix(text: str) -> str:
    for separator in ("：", ":"):
        if separator not in text:
            continue
        label, body = text.split(separator, 1)
        label = label.strip()
        body = body.strip()
        if label and body.startswith(label):
            return f"{label}{separator}{body[len(label):].lstrip()}"
    return text


def _path_label(path: dict[str, object]) -> str:
    label = str(path.get("path_label") or path.get("mechanism") or "")
    if label:
        return label
    chain = _list(path.get("path_chain") or path.get("chain"))
    return " -> ".join(str(row) for row in chain[:4] if row)


def _domain_label(domain: str) -> str:
    return {
        "career": "事业",
        "wealth": "财运",
        "relationship": "关系",
        "health": "健康",
        "timing": "时运",
        "structure": "结构",
        "overview": "整体",
        "hidden_factor": "隐藏线索",
    }.get(domain, domain or "整体")


def _nested(payload: dict[str, object], *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _float(value: object, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _policy_float(payload: dict[str, object], key: str, default: float) -> float:
    try:
        return round(float(payload.get(key, default)), 3)
    except (TypeError, ValueError):
        return default
