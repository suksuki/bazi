from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from v20.storage.local_jsonl import local_jsonl_store_from_env


QUESTION_ATOM_REGISTRY_VERSION = "v20.question_atom_registry.v1"
NEXT_QUESTION_PLAN_VERSION = "v20.next_question_plan.v1"

ROLE_STAGE_JOURNEYS: dict[str, tuple[str, ...]] = {
    "guest": ("entry", "focus", "advice"),
    "user": ("entry", "focus", "structure", "timing", "advice", "closure"),
    "analyst": ("structure", "review", "timing", "advice"),
    "practitioner": ("structure", "review", "timing", "advice"),
    "admin": ("observe",),
}


@dataclass(frozen=True)
class QuestionAtom:
    atom_id: str
    question_key: str
    domain: str
    topic: str
    stage: str
    role_targets: tuple[str, ...]
    template_zh: str
    evidence_requirements: tuple[str, ...] = field(default_factory=tuple)
    context_requirements: tuple[str, ...] = field(default_factory=tuple)
    followup_targets: tuple[str, ...] = field(default_factory=tuple)
    cooldown_scope: str = "question_key"
    max_depth: int = 2
    source: str = "curated_bazi_question_atom"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuestionSessionState:
    answered_question_ids: tuple[str, ...] = ()
    answered_question_keys: tuple[str, ...] = ()
    answered_topics: tuple[str, ...] = ()
    last_question_id: str = ""
    last_question_key: str = ""
    last_atom_id: str = ""
    last_domain: str = ""
    last_stage: str = ""
    topic_depth: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


QUESTION_ATOMS: tuple[QuestionAtom, ...] = (
    QuestionAtom(
        atom_id="atom.guest.entry.overview",
        question_key="q_structure_overview",
        domain="structure",
        topic="structure_dynamics",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="这个八字最值得先看的主线是什么？",
        evidence_requirements=("primary_dynamic_chain",),
        followup_targets=("atom.user.focus.career_pressure", "atom.user.focus.wealth_channel", "atom.user.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.guest.entry.life_area",
        question_key="q_time_layer_context",
        domain="time",
        topic="timing_trigger",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="近几年更该先看工作变化、财运机会，还是关系状态？",
        context_requirements=("luck_or_flow_year",),
        followup_targets=("atom.user.timing.trigger", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.guest.entry.career",
        question_key="q_career_structure",
        domain="career",
        topic="career_structure",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="这盘事业上更该先看稳定平台、个人发挥，还是外部规则压力？",
        evidence_requirements=("career_signal",),
        followup_targets=("atom.user.focus.career_pressure", "atom.user.structure.output_authority"),
    ),
    QuestionAtom(
        atom_id="atom.guest.entry.wealth",
        question_key="q_income_factors",
        domain="wealth",
        topic="wealth_channel",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="财运这块，是先看机会从哪里来，还是先看自己能不能接住？",
        evidence_requirements=("wealth_signal",),
        followup_targets=("atom.user.focus.wealth_channel", "atom.user.structure.wealth_capacity"),
    ),
    QuestionAtom(
        atom_id="atom.guest.entry.relationship",
        question_key="q_relationship_structure",
        domain="relationship",
        topic="relationship_pattern",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="关系里更值得先看相处节奏、现实承接，还是边界压力？",
        evidence_requirements=("relationship_signal",),
        followup_targets=("atom.user.focus.relationship", "atom.user.timing.relationship_window"),
    ),
    QuestionAtom(
        atom_id="atom.guest.entry.health",
        question_key="q_health_balance_boundary",
        domain="health",
        topic="health_balance",
        stage="entry",
        role_targets=("guest", "user"),
        template_zh="健康和状态上，先看精力消耗、压力节奏，还是五行偏枯？",
        evidence_requirements=("element_balance",),
        followup_targets=("atom.user.focus.health_balance", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.user.focus.career_pressure",
        question_key="q_career_structure",
        domain="career",
        topic="career_structure",
        stage="focus",
        role_targets=("user",),
        template_zh="这盘事业压力，是来自规则约束、竞争，还是自己的表达方式？",
        evidence_requirements=("authority_or_output",),
        followup_targets=("atom.user.structure.output_authority", "atom.user.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.user.structure.output_authority",
        question_key="q_career_structure",
        domain="career",
        topic="career_structure",
        stage="structure",
        role_targets=("user", "analyst"),
        template_zh="事业这条线里，食伤表达、官杀压力和印星缓冲谁更主导？",
        evidence_requirements=("output_authority_resource_chain",),
        followup_targets=("atom.user.timing.trigger", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.user.focus.wealth_channel",
        question_key="q_income_factors",
        domain="wealth",
        topic="wealth_channel",
        stage="focus",
        role_targets=("user",),
        template_zh="财运更像稳定收入、项目机会，还是合作分账带来的波动？",
        evidence_requirements=("wealth_or_output",),
        followup_targets=("atom.user.structure.wealth_capacity", "atom.user.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.user.structure.wealth_capacity",
        question_key="q_income_stability",
        domain="wealth",
        topic="wealth_channel",
        stage="structure",
        role_targets=("user", "analyst"),
        template_zh="财星出现后，关键是机会更多，还是日主承接和比劫竞争更重要？",
        evidence_requirements=("wealth_channel_or_peer_competition",),
        followup_targets=("atom.user.timing.trigger", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.user.focus.relationship",
        question_key="q_relationship_structure",
        domain="relationship",
        topic="relationship_pattern",
        stage="focus",
        role_targets=("user",),
        template_zh="关系里更核心的是相处方式、现实承接，还是冲突边界？",
        evidence_requirements=("relationship_signal",),
        followup_targets=("atom.user.timing.trigger", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.user.timing.relationship_window",
        question_key="q_time_relation_triggers",
        domain="time",
        topic="relationship_pattern",
        stage="timing",
        role_targets=("user", "analyst"),
        template_zh="关系主题如果要看时间点，是大运先铺底，还是流年先触发互动变化？",
        context_requirements=("luck_or_flow_year",),
        evidence_requirements=("relationship_signal", "time_context"),
        followup_targets=("atom.user.advice.choice_boundary",),
    ),
    QuestionAtom(
        atom_id="atom.user.focus.health_balance",
        question_key="q_health_balance_boundary",
        domain="health",
        topic="health_balance",
        stage="focus",
        role_targets=("user",),
        template_zh="这盘状态压力，更像火土燥、金水不足，还是日主承接节奏的问题？",
        evidence_requirements=("element_balance", "health_signal"),
        followup_targets=("atom.user.advice.choice_boundary",),
    ),
    QuestionAtom(
        atom_id="atom.user.focus.useful_god",
        question_key="q_useful_god_candidates",
        domain="useful_god",
        topic="useful_god",
        stage="focus",
        role_targets=("user", "analyst"),
        template_zh="这个盘的用神和调节方向是什么，为什么这样取？",
        evidence_requirements=("useful_god_candidates", "primary_dynamic_chain"),
        followup_targets=("atom.analyst.review.useful_god_gap", "atom.user.advice.choice_boundary"),
    ),
    QuestionAtom(
        atom_id="atom.user.structure.strength",
        question_key="q_strength_assessment",
        domain="strength",
        topic="day_master_strength",
        stage="structure",
        role_targets=("user", "analyst"),
        template_zh="日主强弱要先看根气、帮扶、泄耗，还是岁运带来的承接变化？",
        evidence_requirements=("day_master_strength",),
        followup_targets=("atom.user.focus.useful_god", "atom.user.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.user.structure.branch_relation",
        question_key="q_branch_relation_detail",
        domain="branch",
        topic="branch_relation",
        stage="structure",
        role_targets=("user", "analyst"),
        template_zh="地支互动里，当前更关键的是冲合刑害哪条关系？",
        evidence_requirements=("branch_relations",),
        followup_targets=("atom.user.timing.natal_separation", "atom.user.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.user.structure.ten_god",
        question_key="q_ten_god_focus",
        domain="ten_god",
        topic="ten_god_focus",
        stage="structure",
        role_targets=("user", "analyst"),
        template_zh="十神里先看明透的角色，还是藏干里真正做功的线索？",
        evidence_requirements=("ten_god_distribution",),
        followup_targets=("atom.analyst.review.hidden_stem",),
    ),
    QuestionAtom(
        atom_id="atom.user.timing.trigger",
        question_key="q_time_relation_triggers",
        domain="time",
        topic="timing_trigger",
        stage="timing",
        role_targets=("user", "analyst"),
        template_zh="当前大运流年，会先牵动事业、财运还是关系？",
        context_requirements=("luck_or_flow_year",),
        followup_targets=("atom.user.advice.choice_boundary",),
    ),
    QuestionAtom(
        atom_id="atom.user.timing.natal_separation",
        question_key="q_time_vs_natal_relation",
        domain="time",
        topic="timing_trigger",
        stage="timing",
        role_targets=("user", "analyst"),
        template_zh="这一步要分清楚：是原局自带的问题，还是大运流年新触发出来的？",
        context_requirements=("luck_or_flow_year",),
        evidence_requirements=("time_context", "natal_chain"),
        followup_targets=("atom.user.advice.choice_boundary",),
    ),
    QuestionAtom(
        atom_id="atom.user.advice.choice_boundary",
        question_key="q_structure_overview",
        domain="structure",
        topic="choice_boundary",
        stage="advice",
        role_targets=("guest", "user"),
        template_zh="如果只看下一步现实选择，哪些事该放大，哪些事要先收住？",
        evidence_requirements=("primary_mainline",),
        followup_targets=("atom.user.closure.summary",),
    ),
    QuestionAtom(
        atom_id="atom.user.closure.summary",
        question_key="q_structure_overview",
        domain="structure",
        topic="closure",
        stage="closure",
        role_targets=("guest", "user"),
        template_zh="这一轮先收束成哪三条重点最合适？",
        evidence_requirements=("primary_mainline",),
    ),
    QuestionAtom(
        atom_id="atom.analyst.structure.primary_chain",
        question_key="q_pattern_structure",
        domain="pattern",
        topic="structure_dynamics",
        stage="structure",
        role_targets=("analyst", "practitioner"),
        template_zh="当前结构主链是否闭合，承接点和阻断点分别在哪里？",
        evidence_requirements=("primary_dynamic_chain", "candidate_paths"),
        followup_targets=("atom.analyst.review.counter_evidence", "atom.analyst.timing.trigger"),
    ),
    QuestionAtom(
        atom_id="atom.analyst.review.counter_evidence",
        question_key="q_useful_god_evidence_gaps",
        domain="useful_god",
        topic="practitioner_review",
        stage="review",
        role_targets=("analyst", "practitioner"),
        template_zh="这条主链还需要哪些反证，才能排除相邻结构误判？",
        evidence_requirements=("semantic_candidates", "rule_hits"),
        followup_targets=("atom.analyst.timing.trigger",),
    ),
    QuestionAtom(
        atom_id="atom.analyst.review.useful_god_gap",
        question_key="q_useful_god_evidence_gaps",
        domain="useful_god",
        topic="useful_god",
        stage="review",
        role_targets=("analyst", "practitioner"),
        template_zh="用神候选是什么，证据、反证和取舍边界分别在哪里？",
        evidence_requirements=("useful_god_candidates", "counter_evidence"),
        followup_targets=("atom.analyst.timing.trigger",),
    ),
    QuestionAtom(
        atom_id="atom.analyst.review.hidden_stem",
        question_key="q_hidden_stem_role",
        domain="ten_god",
        topic="ten_god_focus",
        stage="review",
        role_targets=("analyst", "practitioner"),
        template_zh="藏干里的十神是否只是背景，还是已经参与主链做功？",
        evidence_requirements=("hidden_stems", "ten_god_distribution"),
        followup_targets=("atom.analyst.review.counter_evidence",),
    ),
    QuestionAtom(
        atom_id="atom.analyst.timing.trigger",
        question_key="q_time_relation_triggers",
        domain="time",
        topic="timing_trigger",
        stage="timing",
        role_targets=("analyst", "practitioner"),
        template_zh="当前大运流年触发的是原局主链，还是形成新的阻断边？",
        context_requirements=("luck_or_flow_year",),
    ),
    QuestionAtom(
        atom_id="atom.admin.observe.source",
        question_key="q_structure_overview",
        domain="system",
        topic="admin_observe",
        stage="observe",
        role_targets=("admin", "lab"),
        template_zh="这个问题由哪些结构动态、规则命中和画像轴触发？",
        evidence_requirements=("question_source_ranking",),
        followup_targets=("atom.admin.observe.suppression", "atom.admin.observe.scoring"),
    ),
    QuestionAtom(
        atom_id="atom.admin.observe.suppression",
        question_key="q_structure_overview",
        domain="system",
        topic="admin_observe",
        stage="observe",
        role_targets=("admin", "lab"),
        template_zh="已问问题 suppression 是否正确生效？",
        evidence_requirements=("question_agent_state",),
        followup_targets=("atom.admin.observe.scoring",),
    ),
    QuestionAtom(
        atom_id="atom.admin.observe.scoring",
        question_key="q_structure_overview",
        domain="system",
        topic="admin_observe",
        stage="observe",
        role_targets=("admin", "lab"),
        template_zh="下一问排序中，角色权重、主链连续性和时间层权重分别是多少？",
        evidence_requirements=("next_question_plan",),
    ),
)


def question_atom_registry_manifest() -> dict[str, Any]:
    return {
        "version": QUESTION_ATOM_REGISTRY_VERSION,
        "atom_count": len(QUESTION_ATOMS),
        "roles": {
            role: len(question_atoms_for_role(role))
            for role in ("guest", "user", "analyst", "practitioner", "admin")
        },
        "topics": sorted({atom.topic for atom in QUESTION_ATOMS}),
        "stages": sorted({atom.stage for atom in QUESTION_ATOMS}),
        "atoms": [atom.to_dict() for atom in QUESTION_ATOMS],
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_ATOMS_ARE_CURATED_CANDIDATES",
            "ATOMS_REQUIRE_BAZI_CONTEXT_BEFORE_RUNTIME_USE",
            "NO_WEB_TEXT_IS_COPIED_VERBATIM",
            "LLM_MAY_REWRITE_STYLE_NOT_FACTS",
        ],
    }


def question_atoms_for_role(role_key: str) -> tuple[QuestionAtom, ...]:
    role = normalize_question_role(role_key)
    aliases = {role}
    if role == "analyst":
        aliases.add("practitioner")
    if role == "admin":
        aliases.add("lab")
    return tuple(atom for atom in QUESTION_ATOMS if aliases.intersection(atom.role_targets))


def question_atom_by_id() -> dict[str, QuestionAtom]:
    return {atom.atom_id: atom for atom in QUESTION_ATOMS}


def question_atoms_by_key(question_key: str, *, role_key: str = "user") -> tuple[QuestionAtom, ...]:
    key = str(question_key or "")
    return tuple(atom for atom in question_atoms_for_role(role_key) if atom.question_key == key)


def build_next_question_plan(
    *,
    role_key: str,
    session_state: QuestionSessionState,
    primary_domain: str = "",
    primary_stage: str = "",
    has_time_context: bool = False,
    limit: int = 8,
    runtime_policy: dict[str, object] | None = None,
) -> dict[str, Any]:
    scored = []
    suppressed = []
    active_policy = _active_next_question_plan_policy() if runtime_policy is None else runtime_policy
    role = normalize_question_role(role_key)
    previous_targets = _previous_followup_targets(session_state, role_key=role)
    role_journey = _role_journey_target_stages(role, session_state)
    for atom in question_atoms_for_role(role_key):
        score, reasons = _score_atom(
            atom,
            role_key=role,
            session_state=session_state,
            primary_domain=primary_domain,
            primary_stage=primary_stage,
            has_time_context=has_time_context,
            previous_targets=previous_targets,
            role_journey=role_journey,
            runtime_policy=active_policy,
        )
        if score <= 0:
            suppressed.append({
                "atom_id": atom.atom_id,
                "question_key": atom.question_key,
                "topic": atom.topic,
                "reason": reasons[-1] if reasons else "suppressed",
            })
            continue
        scored.append((score, atom, reasons))
    scored.sort(key=lambda row: (row[0], row[1].stage, row[1].atom_id), reverse=True)
    recommended_atoms = [
        atom.to_dict() | {"score": round(score, 3), "score_reasons": reasons}
        for score, atom, reasons in scored[:limit]
    ]
    return {
        "version": NEXT_QUESTION_PLAN_VERSION,
        "status": "ready",
        "role_key": normalize_question_role(role_key),
        "primary_domain": primary_domain,
        "primary_stage": primary_stage,
        "has_time_context": has_time_context,
        "recommended_atoms": recommended_atoms,
        "followup_edges": _followup_edges(recommended_atoms),
        "active_followup_targets": tuple(sorted(previous_targets)),
        "role_journey": {
            "role_key": role,
            "stage_order": ROLE_STAGE_JOURNEYS.get(role, ROLE_STAGE_JOURNEYS["user"]),
            "target_stages": tuple(role_journey),
        },
        "session_memory": _session_memory_summary(session_state),
        "policy_trace": _policy_trace(active_policy),
        "suppressed_atoms": suppressed[:20],
        "suppressed_count": len(suppressed),
        "runtime_mutation": False,
        "guardrails": [
            "NEXT_QUESTION_PLAN_IS_EXPLAINABLE",
            "ANSWERED_QUESTIONS_ARE_NOT_RECOMMENDED",
            "FOLLOWUP_CONTINUITY_IS_PREFERRED",
            "NO_CORE_FACT_MUTATION",
        ],
    }


def normalize_question_role(role_key: str) -> str:
    role = str(role_key or "user")
    if role in {"guest", "user", "analyst", "practitioner", "admin", "lab"}:
        return "admin" if role == "lab" else role
    return "user"


def _score_atom(
    atom: QuestionAtom,
    *,
    role_key: str,
    session_state: QuestionSessionState,
    primary_domain: str,
    primary_stage: str,
    has_time_context: bool,
    previous_targets: set[str],
    role_journey: tuple[str, ...],
    runtime_policy: dict[str, object] | None = None,
) -> tuple[float, list[str]]:
    answered_ids = {str(row) for row in session_state.answered_question_ids if str(row)}
    answered_keys = {str(row) for row in session_state.answered_question_keys if str(row)}
    if atom.atom_id in answered_ids or atom.question_key in answered_keys:
        return 0.0, ["已问过，隐藏"]
    depth = int(session_state.topic_depth.get(atom.topic, 0) or 0)
    if depth >= atom.max_depth:
        return 0.0, [f"{atom.topic} 已达到追问深度上限"]
    if "luck_or_flow_year" in atom.context_requirements and not has_time_context:
        return 0.0, ["缺少大运或流年，不推荐时间追问"]

    score = 0.42
    reasons = ["基础候选"]
    primary_aliases = _primary_domain_aliases(primary_domain)
    if atom.domain == primary_domain or atom.topic == primary_domain or atom.topic in primary_aliases:
        score += 0.18
        reasons.append("贴合当前主线领域")
    if atom.stage == primary_stage:
        score += 0.08
        reasons.append("贴合当前问题阶段")
    if _role_specific_fit(atom, role_key):
        score += 0.08
        reasons.append("贴合当前角色深度")
    if atom.stage in role_journey:
        score += 0.1
        reasons.append("符合当前角色追问节奏")
    if atom.atom_id in previous_targets:
        score += 0.2
        reasons.append("承接上一问合法链路")
    if session_state.last_domain and atom.domain == session_state.last_domain:
        score += 0.1
        reasons.append("延续上一问领域")
    last_stage = _normalize_atom_stage(session_state.last_stage)
    if last_stage and _stage_follows(last_stage, atom.stage):
        score += 0.12
        reasons.append("符合追问顺序")
    if has_time_context and last_stage in {"focus", "structure"} and atom.stage == "timing":
        score += 0.18
        reasons.append("承接上一问进入时间层")
    if session_state.last_question_key and atom.question_key != session_state.last_question_key:
        score += 0.04
        reasons.append("避免同一问题键连续重复")
    if last_stage and _stage_regresses(last_stage, atom.stage) and atom.atom_id not in previous_targets:
        score -= 0.1
        reasons.append("避免回退到已过阶段")
    if has_time_context and atom.stage == "timing":
        score += 0.12
        reasons.append("当前有大运流年上下文")
    policy = runtime_policy or {}
    stage_boosts = policy.get("stage_boosts", {}) if isinstance(policy.get("stage_boosts", {}), dict) else {}
    topic_boosts = policy.get("topic_boosts", {}) if isinstance(policy.get("topic_boosts", {}), dict) else {}
    atom_boosts = policy.get("atom_boosts", {}) if isinstance(policy.get("atom_boosts", {}), dict) else {}
    atom_penalties = policy.get("atom_penalties", {}) if isinstance(policy.get("atom_penalties", {}), dict) else {}
    stage_boost = _policy_float(stage_boosts.get(atom.stage))
    topic_boost = _policy_float(topic_boosts.get(atom.topic))
    atom_boost = _policy_float(atom_boosts.get(atom.atom_id))
    atom_penalty = _policy_float(atom_penalties.get(atom.atom_id))
    if stage_boost:
        score += stage_boost
        reasons.append("训练指针增强阶段排序")
    if topic_boost:
        score += topic_boost
        reasons.append("训练指针增强专题排序")
    if atom_boost:
        score += atom_boost
        reasons.append("交互反馈增强此问题")
    if atom_penalty:
        score += atom_penalty
        reasons.append("交互反馈降低此问题")
    if atom.topic in set(session_state.answered_topics):
        score -= 0.12
        reasons.append("同专题已问过，降权")
    if depth > 0:
        score -= min(0.12, 0.04 * depth)
        reasons.append("同专题已推进，降低重复")
    return max(0.01, score), reasons


def _active_next_question_plan_policy() -> dict[str, object]:
    path = local_jsonl_store_from_env().runtime_dir / "training" / "question_policy_versions" / "active_pointer.json"
    if not path.exists():
        return {}
    try:
        pointer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if pointer.get("version") != "v20.question_runtime_active_pointer.v1" or pointer.get("status") != "candidate_active":
        return {}
    payload = pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return {}
    policy = payload.get("next_question_plan_policy", {})
    if not isinstance(policy, dict) or policy.get("status") != "active":
        return {}
    return dict(policy) | {
        "active_policy_version": str(pointer.get("active_policy_version", "")),
        "active_pointer_source": str(pointer.get("source", "")),
    }


def _policy_float(value: object) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0


def _stage_follows(previous: str, current: str) -> bool:
    if previous == "structure" and current == "review":
        return True
    order = ("entry", "focus", "structure", "timing", "advice", "closure")
    if previous not in order or current not in order:
        return False
    return order.index(current) == min(len(order) - 1, order.index(previous) + 1)


def _stage_regresses(previous: str, current: str) -> bool:
    order = ("entry", "focus", "structure", "review", "timing", "advice", "closure")
    if previous not in order or current not in order:
        return False
    return order.index(current) < order.index(previous)


def _role_journey_target_stages(role_key: str, session_state: QuestionSessionState) -> tuple[str, ...]:
    role = normalize_question_role(role_key)
    order = ROLE_STAGE_JOURNEYS.get(role, ROLE_STAGE_JOURNEYS["user"])
    if role == "admin":
        return ("observe",)
    last_stage = _normalize_atom_stage(session_state.last_stage)
    if not last_stage or last_stage not in order:
        return order[:2]
    index = order.index(last_stage)
    current_stage = order[index]
    next_stage = order[min(len(order) - 1, index + 1)]
    if current_stage == next_stage:
        return (current_stage,)
    return (current_stage, next_stage)


def _session_memory_summary(session_state: QuestionSessionState) -> dict[str, object]:
    topic_depth = {
        str(topic): int(depth or 0)
        for topic, depth in session_state.topic_depth.items()
        if str(topic) and int(depth or 0) > 0
    }
    return {
        "answered_question_id_count": len(tuple(row for row in session_state.answered_question_ids if str(row))),
        "answered_question_key_count": len(tuple(row for row in session_state.answered_question_keys if str(row))),
        "answered_topics": tuple(sorted({str(row) for row in session_state.answered_topics if str(row)})),
        "topic_depth": topic_depth,
        "last_question_id": session_state.last_question_id,
        "last_question_key": session_state.last_question_key,
        "last_atom_id": session_state.last_atom_id,
        "last_domain": session_state.last_domain,
        "last_stage": session_state.last_stage,
        "normalized_last_stage": _normalize_atom_stage(session_state.last_stage),
    }


def _policy_trace(policy: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(policy, dict) or not policy:
        return {
            "status": "baseline",
            "source": "",
            "policy_id": "",
            "active_policy_version": "",
            "active_pointer_source": "",
            "atom_boost_count": 0,
            "atom_penalty_count": 0,
            "topic_boost_count": 0,
            "stage_boost_count": 0,
        }
    atom_boosts = policy.get("atom_boosts", {}) if isinstance(policy.get("atom_boosts", {}), dict) else {}
    atom_penalties = policy.get("atom_penalties", {}) if isinstance(policy.get("atom_penalties", {}), dict) else {}
    topic_boosts = policy.get("topic_boosts", {}) if isinstance(policy.get("topic_boosts", {}), dict) else {}
    stage_boosts = policy.get("stage_boosts", {}) if isinstance(policy.get("stage_boosts", {}), dict) else {}
    return {
        "status": str(policy.get("status", "active")),
        "source": str(policy.get("source", "")),
        "policy_id": str(policy.get("policy_id", "")),
        "active_policy_version": str(policy.get("active_policy_version", "")),
        "active_pointer_source": str(policy.get("active_pointer_source", "")),
        "atom_boost_count": len(atom_boosts),
        "atom_penalty_count": len(atom_penalties),
        "topic_boost_count": len(topic_boosts),
        "stage_boost_count": len(stage_boosts),
    }


def _normalize_atom_stage(stage: str) -> str:
    value = str(stage or "")
    return {
        "foundation": "entry",
        "domain_reading": "focus",
        "arbitration": "review",
        "time_context": "timing",
        "decision": "review",
        "calibration": "review",
    }.get(value, value)


def _primary_domain_aliases(primary_domain: str) -> set[str]:
    return {
        "career": {"career_structure"},
        "wealth": {"wealth_channel"},
        "relationship": {"relationship_pattern"},
        "health": {"health_balance"},
        "strength": {"day_master_strength"},
        "useful_god": {"useful_god"},
        "branch": {"branch_relation"},
        "ten_god": {"ten_god_focus"},
        "time": {"timing_trigger"},
        "structure": {"structure_dynamics", "choice_boundary"},
        "pattern": {"structure_dynamics"},
    }.get(str(primary_domain or ""), set())


def _role_specific_fit(atom: QuestionAtom, role_key: str) -> bool:
    targets = set(atom.role_targets)
    if role_key in {"analyst", "practitioner"}:
        return bool(targets.intersection({"analyst", "practitioner"}) and "user" not in targets)
    if role_key == "admin":
        return bool(targets.intersection({"admin", "lab"}))
    if role_key == "guest":
        return targets == {"guest", "user"} or targets == {"guest"}
    return "user" in targets


def _previous_followup_targets(session_state: QuestionSessionState, *, role_key: str) -> set[str]:
    atom_index = question_atom_by_id()
    previous_atoms = []
    if session_state.last_atom_id:
        atom = atom_index.get(str(session_state.last_atom_id))
        if atom:
            previous_atoms.append(atom)
    if not previous_atoms and session_state.last_question_key:
        previous_atoms.extend(question_atoms_by_key(session_state.last_question_key, role_key=role_key))
    targets = {
        target
        for atom in previous_atoms
        for target in atom.followup_targets
        if target in atom_index
    }
    return targets


def _followup_edges(recommended_atoms: list[dict[str, Any]]) -> tuple[dict[str, object], ...]:
    atom_ids = {str(row.get("atom_id", "")) for row in recommended_atoms}
    rows = []
    for atom in recommended_atoms:
        source = str(atom.get("atom_id", ""))
        targets = [
            str(target)
            for target in atom.get("followup_targets", ())
            if str(target) in atom_ids
        ]
        if not targets:
            continue
        rows.append(
            {
                "from_atom_id": source,
                "from_question_key": str(atom.get("question_key", "")),
                "to_atom_ids": tuple(targets),
                "edge_count": len(targets),
            }
        )
    return tuple(rows)
