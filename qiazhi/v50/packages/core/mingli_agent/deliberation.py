from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import Field

from core.contracts.base import V50Model
from core.life_domains import LifeDomain
from core.mingli_agent.contracts import CaseAssertion, MingliCognitiveRecord
from core.mingli_agent.workspace import (
    CaseCognitiveWorkspace,
    CaseDeliberationRevision,
    CaseDeliberationSelection,
)


StageId = Literal["pattern", "useful_god", "work_path", "ziwei_focus", "domain_assertion"]
SelectionAction = Literal["select", "support", "challenge", "defer", "research_fork"]


class DeliberationOption(V50Model):
    option_id: str
    label: str
    thesis: str
    support_kind: Literal["relative_probability", "independent_support"]
    support_percent: int = Field(ge=0, le=100)
    confidence_band: Literal["low", "medium", "high"]
    support_reasons: list[str] = Field(default_factory=list)
    counter_reasons: list[str] = Field(default_factory=list)
    downstream_impacts: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    system_preferred: bool = False
    professionally_selected: bool = False
    research_forked: bool = False


class DeliberationStage(V50Model):
    stage_id: StageId
    stage_key: str
    title: str
    question: str
    selection_type: Literal["exclusive", "attention", "assessment"]
    prerequisite_stage_keys: list[str] = Field(default_factory=list)
    status: Literal["available", "locked", "completed", "unavailable"]
    blocked_reason: str = ""
    allowed_actions: list[SelectionAction] = Field(default_factory=list)
    options: list[DeliberationOption] = Field(default_factory=list)


class DeliberationView(V50Model):
    version: str = "deepbazi.guided_mingli_deliberation.v1"
    role_mode: Literal["practitioner", "research"]
    active_domain: str = "whole_chart"
    support_disclaimer: str
    progress_completed: int
    progress_total: int
    stages: list[DeliberationStage]
    active_selections: list[CaseDeliberationSelection]
    revisions: list[CaseDeliberationRevision]
    chart_facts_locked: bool = True
    global_update_allowed: bool = False


class DeliberationReceipt(V50Model):
    applied: bool
    selection: CaseDeliberationSelection | None = None
    revision: CaseDeliberationRevision
    next_stage_id: str = ""
    chart_facts_modified: bool = False
    cognitive_record_modified: bool = False
    confidence_modified_without_evidence: bool = False
    global_policy_modified: bool = False
    theory_modified: bool = False


def build_deliberation_view(
    *,
    record: MingliCognitiveRecord,
    workspace: CaseCognitiveWorkspace,
    role_mode: Literal["practitioner", "research"],
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
) -> DeliberationView:
    stages = [
        _pattern_stage(record=record, workspace=workspace, role_mode=role_mode),
        _useful_god_stage(record=record, workspace=workspace, role_mode=role_mode),
        _work_path_stage(record=record, workspace=workspace, role_mode=role_mode),
        _ziwei_stage(record=record, workspace=workspace, role_mode=role_mode),
        _domain_stage(record=record, workspace=workspace, role_mode=role_mode, domain=active_domain),
    ]
    relevant = [stage for stage in stages if stage.status != "unavailable"]
    return DeliberationView(
        role_mode=role_mode,
        active_domain=active_domain.value,
        support_disclaimer="支持度表示当前案例候选之间的相对解释力；选择本身不会提高支持度。",
        progress_completed=sum(stage.status == "completed" for stage in relevant),
        progress_total=len(relevant),
        stages=stages,
        active_selections=[item for item in workspace.deliberation_selections if item.active],
        revisions=workspace.deliberation_revisions[-12:],
        chart_facts_locked=workspace.chart_facts_locked,
        global_update_allowed=workspace.global_update_allowed,
    )


def apply_deliberation_selection(
    *,
    record: MingliCognitiveRecord,
    workspace: CaseCognitiveWorkspace,
    role_mode: Literal["practitioner", "research"],
    actor_id: str,
    stage_id: StageId,
    option_id: str,
    action: SelectionAction,
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
    rationale: str = "",
) -> tuple[CaseCognitiveWorkspace, DeliberationReceipt]:
    view = build_deliberation_view(record=record, workspace=workspace, role_mode=role_mode, active_domain=active_domain)
    stage = next((item for item in view.stages if item.stage_id == stage_id), None)
    if stage is None or stage.status == "unavailable":
        raise ValueError("deliberation_stage_unavailable")
    if stage.status == "locked":
        raise ValueError("deliberation_prerequisite_not_satisfied")
    option = next((item for item in stage.options if item.option_id == option_id), None)
    if option is None:
        raise ValueError("deliberation_option_stale")
    if action not in stage.allowed_actions:
        raise ValueError("deliberation_action_not_allowed")
    if action == "research_fork" and role_mode != "research":
        raise ValueError("research_fork_requires_research_mode")

    now = datetime.now(timezone.utc).isoformat()
    selection = CaseDeliberationSelection(
        selection_id=f"selection-{uuid4().hex[:16]}",
        stage_key=stage.stage_key,
        stage_id=stage.stage_id,
        option_id=option.option_id,
        action=action,
        role_mode=role_mode,
        actor_id=actor_id,
        domain=active_domain.value,
        rationale=rationale.strip(),
        selected_at=now,
        support_before=option.support_percent,
    )
    selections = list(workspace.deliberation_selections)
    if action != "research_fork":
        selections = [
            item.model_copy(update={"active": False})
            if item.active and item.stage_key == stage.stage_key and item.action != "research_fork"
            else item
            for item in selections
        ]
    selections.append(selection)
    changed_surfaces = _changed_surfaces(stage_id)
    revision = CaseDeliberationRevision(
        revision_id=f"deliberation-revision-{uuid4().hex[:16]}",
        selection_id=selection.selection_id,
        stage_key=stage.stage_key,
        summary=_selection_summary(stage=stage, option=option, action=action),
        changed_surfaces=changed_surfaces,
        created_at=now,
    )
    active_hypothesis_id = workspace.active_hypothesis_id
    if stage_id == "pattern" and action == "select":
        active_hypothesis_id = option.option_id.removeprefix("hypothesis:")
    updated = workspace.model_copy(update={
        "active_hypothesis_id": active_hypothesis_id,
        "deliberation_selections": selections,
        "deliberation_revisions": [*workspace.deliberation_revisions, revision],
        "revision_count": workspace.revision_count + 1,
    })
    next_view = build_deliberation_view(record=record, workspace=updated, role_mode=role_mode, active_domain=active_domain)
    next_stage = next((item.stage_id for item in next_view.stages if item.status == "available"), "")
    return updated, DeliberationReceipt(applied=True, selection=selection, revision=revision, next_stage_id=next_stage)


def undo_deliberation_selection(
    *,
    record: MingliCognitiveRecord,
    workspace: CaseCognitiveWorkspace,
    role_mode: Literal["practitioner", "research"],
    actor_id: str,
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
) -> tuple[CaseCognitiveWorkspace, DeliberationReceipt]:
    target = next((item for item in reversed(workspace.deliberation_selections) if item.active), None)
    if target is None:
        raise ValueError("deliberation_nothing_to_undo")
    selections = [item.model_copy(update={"active": False}) if item.selection_id == target.selection_id else item for item in workspace.deliberation_selections]
    if target.action != "research_fork":
        previous = next((
            item
            for item in reversed(selections)
            if item.selection_id != target.selection_id and item.stage_key == target.stage_key and item.action != "research_fork"
        ), None)
        if previous is not None:
            selections = [item.model_copy(update={"active": True}) if item.selection_id == previous.selection_id else item for item in selections]
    active_pattern = next((item for item in reversed(selections) if item.active and item.stage_id == "pattern" and item.action == "select"), None)
    active_hypothesis_id = active_pattern.option_id.removeprefix("hypothesis:") if active_pattern else record.cognition.selected_hypothesis_id
    now = datetime.now(timezone.utc).isoformat()
    revision = CaseDeliberationRevision(
        revision_id=f"deliberation-revision-{uuid4().hex[:16]}",
        selection_id=target.selection_id,
        stage_key=target.stage_key,
        kind="undo",
        summary="已撤销最近一次案例研判选择；系统原始判断保持不变。",
        changed_surfaces=_changed_surfaces(target.stage_id),
        created_at=now,
    )
    updated = workspace.model_copy(update={
        "active_hypothesis_id": active_hypothesis_id,
        "deliberation_selections": selections,
        "deliberation_revisions": [*workspace.deliberation_revisions, revision],
        "revision_count": workspace.revision_count + 1,
    })
    next_view = build_deliberation_view(record=record, workspace=updated, role_mode=role_mode, active_domain=active_domain)
    next_stage = next((item.stage_id for item in next_view.stages if item.status == "available"), "")
    return updated, DeliberationReceipt(applied=True, revision=revision, next_stage_id=next_stage)


def _pattern_stage(*, record: MingliCognitiveRecord, workspace: CaseCognitiveWorkspace, role_mode: str) -> DeliberationStage:
    hypotheses = record.cognition.hypotheses
    raw_scores = [_hypothesis_raw_score(item.confidence, len(item.supporting_evidence_refs), len(item.counter_evidence_refs), _belief_direction(workspace, item.hypothesis_id)) for item in hypotheses]
    normalized = _normalize(raw_scores)
    active = _active_selection(workspace, "pattern")
    forks = _fork_ids(workspace, "pattern")
    options = [
        DeliberationOption(
            option_id=f"hypothesis:{item.hypothesis_id}",
            label=item.name,
            thesis=item.thesis,
            support_kind="relative_probability",
            support_percent=normalized[index],
            confidence_band=_band(normalized[index]),
            support_reasons=[*item.success_conditions[:2], f"引用 {len(item.supporting_evidence_refs)} 条结构证据"],
            counter_reasons=[*item.failure_conditions[:2], *([item.rejection_reason] if item.rejection_reason else [])],
            downstream_impacts=["体用与用神", "主做功", "领域判断"],
            evidence_refs=item.supporting_evidence_refs if role_mode == "research" else [],
            system_preferred=item.hypothesis_id == record.cognition.selected_hypothesis_id,
            professionally_selected=bool(active and active.option_id == f"hypothesis:{item.hypothesis_id}"),
            research_forked=f"hypothesis:{item.hypothesis_id}" in forks,
        )
        for index, item in enumerate(hypotheses)
    ]
    return _stage(
        stage_id="pattern",
        title="整体命局假设",
        question="哪一个解释最适合作为这张盘的当前主线？",
        selection_type="exclusive",
        options=options,
        workspace=workspace,
        role_mode=role_mode,
    )


def _useful_god_stage(*, record: MingliCognitiveRecord, workspace: CaseCognitiveWorkspace, role_mode: str) -> DeliberationStage:
    options = []
    active = _active_selection(workspace, "useful_god")
    forks = _fork_ids(workspace, "useful_god")
    for index, item in enumerate(record.cognition.useful_god_reasoning):
        support = max(20, min(88, 54 + len(item.evidence_refs) * 4 + len(item.applicable_conditions) * 3 - len(item.invalidating_conditions) * 4))
        option_id = f"useful_god:{index}"
        options.append(DeliberationOption(
            option_id=option_id,
            label=f"{item.candidate} · {item.role}",
            thesis=item.why_useful,
            support_kind="independent_support",
            support_percent=support,
            confidence_band=_band(support),
            support_reasons=item.applicable_conditions[:3] or [item.why_useful],
            counter_reasons=item.invalidating_conditions[:3] or [item.when_harmful],
            downstream_impacts=["做功闭合条件", "事业与财富解释", "时序喜忌"],
            evidence_refs=item.evidence_refs if role_mode == "research" else [],
            system_preferred=index == 0,
            professionally_selected=bool(active and active.option_id == option_id),
            research_forked=option_id in forks,
        ))
    return _stage(
        stage_id="useful_god",
        title="体用与用神逻辑",
        question="当前哪一种力量最能帮助主路径完成转化？",
        selection_type="exclusive",
        options=options,
        workspace=workspace,
        role_mode=role_mode,
        prerequisites=["pattern"],
    )


def _work_path_stage(*, record: MingliCognitiveRecord, workspace: CaseCognitiveWorkspace, role_mode: str) -> DeliberationStage:
    path = record.cognition.work_path
    support = {"closed": 82, "conditional": 64, "broken": 34, "uncertain": 44}[path.closure]
    support = max(15, min(90, support + min(8, len(path.evidence_refs) * 2) - min(12, len(path.failure_conditions) * 2)))
    option_id = "work_path:current"
    active = _active_selection(workspace, "work_path")
    return _stage(
        stage_id="work_path",
        title="主做功审阅",
        question="这条主做功是否足以承接整盘判断？",
        selection_type="assessment",
        options=[DeliberationOption(
            option_id=option_id,
            label="系统当前主做功",
            thesis=path.path_statement,
            support_kind="independent_support",
            support_percent=support,
            confidence_band=_band(support),
            support_reasons=path.success_conditions[:3] or path.transformations[:3],
            counter_reasons=path.failure_conditions[:3],
            downstream_impacts=["领域因果链", "现实方向", "时序验证"],
            evidence_refs=path.evidence_refs if role_mode == "research" else [],
            system_preferred=True,
            professionally_selected=bool(active and active.option_id == option_id),
            research_forked=option_id in _fork_ids(workspace, "work_path"),
        )],
        workspace=workspace,
        role_mode=role_mode,
        prerequisites=["pattern", "useful_god"],
    )


def _ziwei_stage(*, record: MingliCognitiveRecord, workspace: CaseCognitiveWorkspace, role_mode: str) -> DeliberationStage:
    dual = record.cognition.dual_lens
    if dual is None or not dual.palace_observations:
        return DeliberationStage(
            stage_id="ziwei_focus",
            stage_key="ziwei_focus",
            title="紫微交叉重心",
            question="哪条紫微观察最值得进入本轮判断？",
            selection_type="attention",
            status="unavailable",
            blocked_reason="当前命盘没有可用的紫微交叉证据。",
        )
    raw = [1 + len(item.evidence_refs) for item in dual.palace_observations]
    supports = _normalize(raw)
    active = _active_selection(workspace, "ziwei_focus")
    forks = _fork_ids(workspace, "ziwei_focus")
    options = []
    for index, item in enumerate(dual.palace_observations):
        option_id = f"ziwei:{item.observation_id}"
        options.append(DeliberationOption(
            option_id=option_id,
            label=_short_label(item.claim),
            thesis=f"{item.claim} {item.why_it_matters}",
            support_kind="relative_probability",
            support_percent=supports[index],
            confidence_band=_band(supports[index]),
            support_reasons=[f"引用 {len(item.evidence_refs)} 条紫微事实"],
            counter_reasons=item.counter_conditions[:3],
            downstream_impacts=[item.domain, "八字与紫微交叉解释"],
            evidence_refs=item.evidence_refs if role_mode == "research" else [],
            system_preferred=index == 0,
            professionally_selected=bool(active and active.option_id == option_id),
            research_forked=option_id in forks,
        ))
    return _stage(
        stage_id="ziwei_focus",
        title="紫微交叉重心",
        question="哪条紫微观察最值得作为本轮交叉证据？",
        selection_type="attention",
        options=options,
        workspace=workspace,
        role_mode=role_mode,
        prerequisites=["pattern"],
    )


def _domain_stage(*, record: MingliCognitiveRecord, workspace: CaseCognitiveWorkspace, role_mode: str, domain: LifeDomain) -> DeliberationStage:
    reading = None
    if domain in record.domain_explorations:
        reading = record.domain_explorations[domain].reading
    elif domain is LifeDomain.CAREER:
        reading = record.cognition.career
    elif domain is LifeDomain.WEALTH:
        reading = record.cognition.wealth
    if reading is None or not reading.assertions:
        return DeliberationStage(
            stage_id="domain_assertion",
            stage_key=f"domain_assertion:{domain.value}",
            title="领域断言审阅",
            question="哪条领域断言最值得进入当前结论？",
            selection_type="assessment",
            status="unavailable",
            blocked_reason="先打开并完成一个具体人生主题。",
        )
    stage_key = f"domain_assertion:{domain.value}"
    active = _active_selection(workspace, stage_key)
    forks = _fork_ids(workspace, stage_key)
    options = [_assertion_option(item, active=active, forks=forks, role_mode=role_mode) for item in reading.assertions]
    return _stage(
        stage_id="domain_assertion",
        stage_key=stage_key,
        title=f"{_domain_label(domain)}断言审阅",
        question="哪条判断足以作为这个领域的当前结论？",
        selection_type="assessment",
        options=options,
        workspace=workspace,
        role_mode=role_mode,
        prerequisites=["work_path"],
    )


def _assertion_option(item: CaseAssertion, *, active: CaseDeliberationSelection | None, forks: set[str], role_mode: str) -> DeliberationOption:
    base = {"supported": 74, "partially_supported": 54, "unresolved": 34}[item.epistemic_status]
    support = max(15, min(90, base + min(10, len(item.evidence_refs) * 2) - min(15, len(item.counter_evidence_refs) * 4)))
    option_id = f"assertion:{item.assertion_id}"
    return DeliberationOption(
        option_id=option_id,
        label=_short_label(item.claim),
        thesis=f"{item.claim} {item.rationale}",
        support_kind="independent_support",
        support_percent=support,
        confidence_band=_band(support),
        support_reasons=item.conditions[:3] or [item.rationale],
        counter_reasons=item.falsifiers[:3],
        downstream_impacts=["领域结论", "客户解释", "下一条 Probe"],
        evidence_refs=item.evidence_refs if role_mode == "research" else [],
        system_preferred=item.epistemic_status == "supported",
        professionally_selected=bool(active and active.option_id == option_id),
        research_forked=option_id in forks,
    )


def _stage(
    *,
    stage_id: StageId,
    title: str,
    question: str,
    selection_type: Literal["exclusive", "attention", "assessment"],
    options: list[DeliberationOption],
    workspace: CaseCognitiveWorkspace,
    role_mode: str,
    prerequisites: list[str] | None = None,
    stage_key: str | None = None,
) -> DeliberationStage:
    key = stage_key or stage_id
    prerequisite_keys = prerequisites or []
    missing = [item for item in prerequisite_keys if _active_selection(workspace, item) is None]
    active = _active_selection(workspace, key)
    status: Literal["available", "locked", "completed", "unavailable"] = "completed" if active else "locked" if missing else "available"
    actions: list[SelectionAction] = ["select"] if selection_type in {"exclusive", "attention"} else ["support", "challenge", "defer"]
    if role_mode == "research":
        actions.append("research_fork")
    return DeliberationStage(
        stage_id=stage_id,
        stage_key=key,
        title=title,
        question=question,
        selection_type=selection_type,
        prerequisite_stage_keys=prerequisite_keys,
        status=status,
        blocked_reason=f"请先完成：{'、'.join(missing)}" if missing else "",
        allowed_actions=actions,
        options=options,
    )


def _active_selection(workspace: CaseCognitiveWorkspace, stage_key: str) -> CaseDeliberationSelection | None:
    return next((item for item in reversed(workspace.deliberation_selections) if item.active and item.stage_key == stage_key and item.action != "research_fork"), None)


def _fork_ids(workspace: CaseCognitiveWorkspace, stage_key: str) -> set[str]:
    return {item.option_id for item in workspace.deliberation_selections if item.active and item.stage_key == stage_key and item.action == "research_fork"}


def _belief_direction(workspace: CaseCognitiveWorkspace, hypothesis_id: str) -> str:
    belief = next((item for item in workspace.hypothesis_beliefs if item.hypothesis_id == hypothesis_id), None)
    return belief.current_direction if belief else "unchanged"


def _hypothesis_raw_score(confidence: str, support_count: int, counter_count: int, direction: str) -> float:
    score = {"high": 0.72, "medium": 0.48, "low": 0.26}.get(confidence, 0.4)
    score += min(0.14, support_count * 0.025)
    score -= min(0.18, counter_count * 0.05)
    score += 0.08 if direction == "strengthened" else -0.08 if direction == "weakened" else 0
    return max(0.08, score)


def _normalize(values: list[float | int]) -> list[int]:
    if not values:
        return []
    total = float(sum(values)) or 1.0
    result = [max(1, round(float(item) / total * 100)) for item in values]
    result[-1] += 100 - sum(result)
    return result


def _band(value: int) -> Literal["low", "medium", "high"]:
    return "high" if value >= 65 else "medium" if value >= 40 else "low"


def _changed_surfaces(stage_id: str) -> list[str]:
    return {
        "pattern": ["case_hypothesis", "useful_god_review", "work_path_review", "domain_reading"],
        "useful_god": ["useful_god_review", "work_path_review", "domain_reading", "timing_review"],
        "work_path": ["work_path_review", "domain_reading", "client_explanation"],
        "ziwei_focus": ["cross_lens_focus", "domain_reading"],
        "domain_assertion": ["domain_reading", "client_explanation", "next_probe"],
    }.get(stage_id, ["effective_case_reading"])


def _selection_summary(*, stage: DeliberationStage, option: DeliberationOption, action: str) -> str:
    verb = {
        "select": "设为当前案例分支",
        "support": "标记为当前支持",
        "challenge": "标记为需要重审",
        "defer": "保留为未决",
        "research_fork": "保留为研究分支",
    }[action]
    return f"{option.label}已{verb}。支持度未因选择本身改变。"


def _domain_label(domain: LifeDomain) -> str:
    return {
        LifeDomain.SELF: "自我与性情",
        LifeDomain.TALENT_LEARNING: "天赋与学习",
        LifeDomain.CAREER: "事业",
        LifeDomain.WEALTH: "财富",
        LifeDomain.RELATIONSHIP: "关系",
        LifeDomain.FAMILY: "家庭",
        LifeDomain.CHILDREN_LEGACY: "子女与传承",
        LifeDomain.HEALTH_VITALITY: "健康与生命力",
        LifeDomain.SOCIAL_NETWORK: "合作",
        LifeDomain.MIGRATION_ENVIRONMENT: "迁移与环境",
        LifeDomain.LIFE_TIMING: "人生阶段",
    }.get(domain, "领域")


def _short_label(value: str, limit: int = 46) -> str:
    clean = value.strip()
    first = next((part.strip() for part in clean.replace("；", "。").split("。") if part.strip()), clean)
    return first if len(first) <= limit else f"{first[:limit].rstrip('，,：:')}…"
