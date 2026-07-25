from __future__ import annotations

import re
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from core.contracts.base import V50Model
from core.life_domains import LifeDomain, domain_access_allowed, domain_definition


class AbuCapability(V50Model):
    capability_id: str
    action_type: str
    executor: Literal["client_ui", "birth_intake", "mingli_agent", "product_api"]
    requires_case: bool = False
    requires_account: bool = False
    confirmation_required: bool = False
    allowed_results: list[str] = Field(default_factory=list)


class AbuRuntimeContext(V50Model):
    has_case: bool = False
    has_profile: bool = False
    has_account: bool = False
    active_mode: Literal["guest", "member", "practitioner", "research"] = "guest"
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART


class AbuCommandPlan(V50Model):
    version: str = "deepbazi.abu_command_plan.v1"
    plan_id: str
    intent: str
    capability_id: str
    action_type: str
    confidence: Literal["low", "medium", "high"]
    slots: dict[str, Any] = Field(default_factory=dict)
    missing_requirements: list[str] = Field(default_factory=list)
    confirmation_required: bool = False
    executor: str
    abu_message: str
    suggested_actions: list[str] = Field(default_factory=list)


class AbuCapabilityRegistry:
    def __init__(self) -> None:
        self._items = {item.capability_id: item for item in _default_capabilities()}

    def get(self, capability_id: str) -> AbuCapability:
        return self._items[capability_id]

    def manifest(self) -> list[dict[str, Any]]:
        return [self._items[key].model_dump(mode="json") for key in sorted(self._items)]


def resolve_abu_command(
    *,
    message: str,
    context: AbuRuntimeContext,
    registry: AbuCapabilityRegistry | None = None,
) -> AbuCommandPlan:
    registry = registry or AbuCapabilityRegistry()
    normalized = message.strip()
    lowered = normalized.lower()

    capability_id, intent, slots, confidence = _match_intent(normalized, lowered, context)
    capability = registry.get(capability_id)
    missing: list[str] = []
    if capability.requires_case and not context.has_case:
        missing.append("confirmed_chart")
    if capability.requires_account and not context.has_account:
        missing.append("authenticated_account")
    if capability_id == "reading.select_domain":
        requested_domain = str(slots.get("domain") or LifeDomain.WHOLE_CHART.value)
        if not domain_access_allowed(requested_domain, role_mode=context.active_mode):
            missing.append("capability_boundary")
    message_text, suggestions = _guidance_for(
        capability_id=capability_id,
        missing=missing,
        slots=slots,
        context=context,
    )
    return AbuCommandPlan(
        plan_id=f"abu-plan-{uuid4().hex[:20]}",
        intent=intent,
        capability_id=capability_id,
        action_type=capability.action_type,
        confidence=confidence,
        slots=slots,
        missing_requirements=missing,
        confirmation_required=capability.confirmation_required or bool(missing),
        executor=capability.executor,
        abu_message=message_text,
        suggested_actions=suggestions,
    )


def _match_intent(
    message: str,
    lowered: str,
    context: AbuRuntimeContext,
) -> tuple[str, str, dict[str, Any], Literal["low", "medium", "high"]]:
    has_birth_shape = bool(
        re.search(r"(?:19|20)\d{2}\s*年?\s*\d{1,2}\s*月\s*\d{1,2}\s*[日号]", message)
        or re.search(r"(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}", message)
    )
    if has_birth_shape or any(token in message for token in ("出生于", "出生时间", "我的生日", "生辰")):
        return "profile.create", "provide_birth_information", {"raw_birth_statement": message}, "high"
    if any(token in message for token in ("新建档案", "添加档案", "新增命盘")):
        return "profile.create", "create_profile_form", {"open_form": True}, "high"
    if any(token in message for token in ("注册", "建立账户", "创建账户")):
        return "account.register", "register_account", {}, "high"
    if any(token in message for token in ("登录", "登入")):
        return "account.login", "login_account", {}, "high"
    if any(token in message for token in ("退出登录", "登出")):
        return "account.logout", "logout_account", {}, "high"
    if any(token in message for token in ("我的档案", "命理档案", "档案列表", "切换命盘", "编辑档案", "修改档案", "档案管理")):
        return "profile.list", "open_profile_archive", {}, "high"
    if any(token in lowered for token in ("切换到英文", "切换英文", "英文版", "english", "language")):
        return "interface.language", "select_language", {"language": "en"}, "high"
    if any(token in message for token in ("上个月", "这个月", "本月", "下个月", "选择月份")):
        period = "previous_month" if "上个月" in message else "next_month" if "下个月" in message else "current_month"
        return "timeline.select_period", "select_timeline_period", {"period": period}, "high"
    if any(token in message for token in ("记录昨天", "记录一件", "记录发生", "记下发生", "现实事件")):
        return "reality.record", "record_reality_event", {"raw_event": message}, "high"
    if any(token in message for token in ("开始测算", "开始看盘", "算八字", "排八字")):
        return "reading.start", "start_reading", {}, "high"
    if "紫微" in message or "星盘" in message or "十二宫" in message:
        return "reading.select_lens", "select_lens", {"lens": "ziwei"}, "high"
    if "八字" in message or "四柱" in message:
        return "reading.select_lens", "select_lens", {"lens": "bazi"}, "high"
    if any(token in message for token in ("综合看", "一起看", "双盘")):
        return "reading.select_lens", "select_lens", {"lens": "overview"}, "high"
    domain = _match_life_domain(message)
    if domain is not None:
        return "reading.select_domain", "select_domain", {"domain": domain.value}, "high"
    if any(token in message for token in ("继续上次", "继续探索", "接着看", "继续刚才")):
        return "reading.resume", "resume_reading", {}, "high"
    if any(token in message for token in ("为什么", "依据", "怎么看出来", "证据")):
        return "reading.explain", "explain_reading", {"domain": context.active_domain}, "high"
    if context.has_case:
        return "reading.ask", "ask_case_question", {"question": message}, "medium"
    return "conversation.clarify", "clarify_next_job", {}, "low"


def _guidance_for(
    *,
    capability_id: str,
    missing: list[str],
    slots: dict[str, Any],
    context: AbuRuntimeContext,
) -> tuple[str, list[str]]:
    if "confirmed_chart" in missing:
        if context.has_profile:
            return (
                "当前命理档案已经确认，不需要再次填写出生信息。先用这份档案开始看盘，再进入具体问题。",
                ["用当前档案开始看盘", "切换命理档案"],
            )
        return (
            "开始这一步前，我需要先确认你的出生信息并建立命盘。你可以直接用一句话告诉我出生年月日、时间、地点和性别。",
            ["直接告诉你出生信息", "精确填写出生信息"],
        )
    if "authenticated_account" in missing:
        return "这一步需要先登录，登录后我会接着当前探索继续。", ["登录", "注册"]
    messages: dict[str, tuple[str, list[str]]] = {
        "profile.create": ("我会先整理你说的出生信息，再请你确认；确认前不会排盘或保存。", ["改用精确填写"]),
        "account.register": ("可以。先建立账户，完成后当前探索会自动保存。", []),
        "account.login": ("可以。登录后我会恢复你的命理档案与最近探索。", []),
        "account.logout": ("我会退出当前账户；页面上的当前内容仍保留，但不会继续写入账户。", []),
        "profile.list": ("我来打开命理档案，你可以继续旧探索或选择另一张命盘。", []),
        "reading.resume": ("我会从最近一份已完成的认知记录继续，不重新编造一份结论。", []),
        "interface.language": ("当前公开版本先把中文体验做完整，英文界面还没有开放。我不会为了响应这句话而调用命理模型或伪装成已经切换。", []),
        "timeline.select_period": ("我会切换当前查看月份。页面、我的解释和新现实记录会使用同一个月份；整盘基线不会因此改变。", []),
        "reality.record": ("我会先把这件事保存为你的现实自述，不会立刻把它解释成命理结论。月度复盘时再与原先判断比较。", []),
        "reading.start": (
            "当前档案已经准备好。我会直接用这份命盘形成一次整盘基线认知，不再重复询问出生信息。"
            if context.has_profile
            else "命盘已经具备时，我会用一次完整推理形成整盘基线，再由你选择专题。",
            [],
        ),
        "reading.explain": ("我会展开当前判断引用的盘面重心、竞争解释与反证。", []),
        "reading.select_lens": ("我会切换当前观察视角，不重新计算命盘，也不会制造新的结论。", []),
        "reading.ask": ("我会把这个问题交给当前案例的命理认知 Agent，并保留它对假设造成的变化。", []),
        "conversation.clarify": (
            "当前命理档案已经准备好。你可以直接开始看盘、切换另一份档案，或告诉我这次最想理解的人生问题。"
            if context.has_profile
            else "我还不能确定你现在想完成哪件事。你可以先建立命盘，或从整盘、事业、财富开始。",
            ["用当前档案开始看盘", "切换命理档案"]
            if context.has_profile
            else ["建立我的命盘", "我想先理解自己", "看看人生阶段"],
        ),
    }
    if capability_id == "reading.select_domain":
        definition = domain_definition(str(slots.get("domain")))
        if not domain_access_allowed(definition.domain, role_mode=context.active_mode):
            return (
                f"{definition.name_zh}已经在 DeepBazi 的完整命理领域里，但当前还没有达到可以负责任公开断言的程度。Abu 可以先从整盘重心出发，说明这个领域需要哪些证据，而不会套用通用答案。",
                ["先看整盘重心", "这个领域还缺什么证据"],
            )
        return f"我会切换到{definition.name_zh}，但仍沿用同一份整盘认知，不会另套一份领域模板。", ["回答一个区分问题", "回到整盘"]
    return messages[capability_id]


def _match_life_domain(message: str) -> LifeDomain | None:
    vocabulary = (
        (LifeDomain.SELF, ("性格", "自己", "自我", "人生主线", "命局")),
        (LifeDomain.TALENT_LEARNING, ("学习", "学业", "考试", "天赋", "能力")),
        (LifeDomain.CAREER, ("事业", "工作", "职业", "升职", "转型", "创业")),
        (LifeDomain.WEALTH, ("财富", "财运", "收入", "资源", "投资")),
        (LifeDomain.RELATIONSHIP, ("感情", "恋爱", "婚姻", "伴侣", "关系")),
        (LifeDomain.FAMILY, ("家庭", "父母", "原生家庭", "兄弟姐妹")),
        (LifeDomain.CHILDREN_LEGACY, ("子女", "孩子", "生育", "传承")),
        (LifeDomain.HEALTH_VITALITY, ("健康", "身体", "精力", "疾病")),
        (LifeDomain.SOCIAL_NETWORK, ("社交", "朋友", "人脉", "合作", "团队")),
        (LifeDomain.MIGRATION_ENVIRONMENT, ("迁移", "出国", "搬家", "城市", "环境")),
        (LifeDomain.LIFE_TIMING, ("大运", "流年", "时机", "阶段", "什么时候")),
    )
    return next((domain for domain, terms in vocabulary if any(term in message for term in terms)), None)


def _default_capabilities() -> list[AbuCapability]:
    specs = [
        ("profile.create", "CREATE_PROFILE", "birth_intake", False, False, True, ["birth_draft", "clarification"]),
        ("profile.edit", "EDIT_PROFILE", "birth_intake", False, False, True, ["birth_draft"]),
        ("profile.list", "OPEN_PROFILE_ARCHIVE", "client_ui", False, True, False, ["profile_archive"]),
        ("profile.select", "SELECT_PROFILE", "product_api", False, True, True, ["selected_profile"]),
        ("chart.preview", "PREVIEW_CHART", "product_api", False, False, True, ["chart_preview"]),
        ("chart.confirm", "CONFIRM_CHART", "product_api", False, False, True, ["confirmed_chart"]),
        ("chart.compute", "COMPUTE_CHART_FACTS", "product_api", False, False, True, ["chart_facts"]),
        ("reading.start", "START_BASELINE", "mingli_agent", False, False, False, ["cognitive_job"]),
        ("reading.resume", "CONTINUE_LAST_EXPLORATION", "client_ui", False, False, False, ["reading"]),
        ("reading.select_domain", "OPEN_DOMAIN", "client_ui", True, False, False, ["domain_view"]),
        ("reading.select_lens", "OPEN_LENS", "client_ui", True, False, False, ["lens_view"]),
        ("reading.explain", "OPEN_EVIDENCE", "client_ui", True, False, False, ["evidence_view"]),
        ("reading.ask", "ASK_CASE_QUESTION", "mingli_agent", True, False, False, ["case_turn"]),
        ("probe.present", "OPEN_PROBE", "client_ui", True, False, False, ["probe_plan"]),
        ("probe.respond", "RECORD_PROBE_RESPONSE", "product_api", True, False, True, ["case_belief_update"]),
        ("probe.explain_reason", "EXPLAIN_PROBE", "client_ui", True, False, False, ["probe_purpose"]),
        ("case.save", "SAVE_CASE", "product_api", True, True, False, ["saved_case"]),
        ("case.history", "OPEN_CASE_HISTORY", "client_ui", False, True, False, ["case_history"]),
        ("case.switch", "SWITCH_CASE", "client_ui", False, True, True, ["selected_case"]),
        ("account.login", "OPEN_LOGIN", "client_ui", False, False, False, ["auth_dialog"]),
        ("account.register", "OPEN_REGISTER", "client_ui", False, False, False, ["auth_dialog"]),
        ("account.logout", "LOG_OUT", "product_api", False, True, True, ["logged_out"]),
        ("workspace.claim", "CLAIM_WORKSPACE", "product_api", True, True, False, ["claimed_workspace"]),
        ("interface.language", "SET_LANGUAGE", "client_ui", False, False, False, ["language_boundary"]),
        ("timeline.select_period", "OPEN_TIMELINE_PERIOD", "client_ui", True, False, False, ["timeline_boundary"]),
        ("reality.record", "OPEN_REALITY_EVENT", "client_ui", True, False, False, ["reality_boundary"]),
        ("conversation.clarify", "CLARIFY_INTENT", "client_ui", False, False, False, ["clarification"]),
    ]
    return [
        AbuCapability(
            capability_id=capability_id,
            action_type=action_type,
            executor=executor,
            requires_case=requires_case,
            requires_account=requires_account,
            confirmation_required=confirmation_required,
            allowed_results=allowed_results,
        )
        for capability_id, action_type, executor, requires_case, requires_account, confirmation_required, allowed_results in specs
    ]
