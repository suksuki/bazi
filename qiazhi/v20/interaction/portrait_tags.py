from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v20.answer.measurement_policy import domain_label


@dataclass(frozen=True)
class PortraitTagProfile:
    domain: str
    axis_tier: str
    label: str
    profile_tag: str
    profile_tags: tuple[str, ...]
    profile_summary: str
    attention_level: str
    portrait_intent_type: str
    calibration_state: str

    def to_dict(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "axis_tier": self.axis_tier,
            "label": self.label,
            "profile_tag": self.profile_tag,
            "profile_tags": self.profile_tags,
            "profile_summary": self.profile_summary,
            "attention_level": self.attention_level,
            "portrait_intent_type": self.portrait_intent_type,
            "calibration_state": self.calibration_state,
        }


PORTRAIT_BLUEPRINTS: dict[str, dict[str, str]] = {
    "strength": {
        "label": "日主承载画像",
        "tag": "承载路径",
        "summary": "这个盘先看日主承载、资源支持和压力分配，用来确定能量主轴。",
        "intent": "capacity_profile",
    },
    "wealth": {
        "label": "财富承接画像",
        "tag": "财务结构",
        "summary": "财富主题从财星来源、承接力和通道连贯性，提炼结构边界。",
        "intent": "wealth_profile",
    },
    "career": {
        "label": "事业角色画像",
        "tag": "角色结构",
        "summary": "事业主题看官杀、伤官、印星和资源分配后的角色运作方式。",
        "intent": "career_profile",
    },
    "relationship": {
        "label": "关系互动画像",
        "tag": "关系结构",
        "summary": "关系主题以地支关系、十神互动与承接边界判断沟通与节奏。",
        "intent": "relationship_profile",
    },
    "health": {
        "label": "身心平衡画像",
        "tag": "健康边界",
        "summary": "健康仅做五行平衡与压力边界，避免具体病理与治疗判断。",
        "intent": "wellbeing_profile",
    },
    "time": {
        "label": "时运触发画像",
        "tag": "岁运牵引",
        "summary": "时运层只看大运流年流月对原局的触发顺序与优先领域。",
        "intent": "timing_profile",
    },
    "useful_god": {
        "label": "调候取向画像",
        "tag": "取用方向",
        "summary": "用神相关转为可执行调节方向，不替代实时证据裁决。",
        "intent": "useful_god_profile",
    },
    "pattern": {
        "label": "格局结构画像",
        "tag": "格局秩序",
        "summary": "格局主题聚焦主轴清晰度与关键动作是否连续。", 
        "intent": "pattern_profile",
    },
    "element": {
        "label": "五行气势画像",
        "tag": "五行配置",
        "summary": "五行主题描述显著/偏弱/失衡与后续承压方向。",
        "intent": "element_profile",
    },
    "branch": {
        "label": "地支互动画像",
        "tag": "关系牵引",
        "summary": "地支主题关注冲合刑害、三合三会和位置关系对其它结构的触发。",
        "intent": "branch_profile",
    },
    "ten_god": {
        "label": "十神角色画像",
        "tag": "十神分工",
        "summary": "十神主题按透出、藏干与制化关系建立角色分工。",
        "intent": "ten_god_profile",
    },
}

PORTRAIT_AXIS_TIER_TAGS: dict[str, tuple[str, ...]] = {
    "micro": ("骨架", "微观结构", "命理内核"),
    "decision": ("裁决", "结构路径", "强度边界"),
    "macro": ("主题投射", "应用画像", "生活场景"),
    "time": ("时序", "触发先后", "阶段排序"),
}

PORTRAIT_DOMAIN_TAGS: dict[str, tuple[str, ...]] = {
    "strength": ("承载", "强弱", "泄耗"),
    "ten_god": ("十神", "显露", "制化"),
    "element": ("五行", "偏枯", "平衡"),
    "branch": ("冲合刑害", "地支关系", "位势"),
    "wealth": ("财星", "承接", "通道"),
    "pattern": ("格局", "主轴", "秩序"),
    "useful_god": ("用神", "取舍", "调候"),
    "career": ("事业", "表达", "角色"),
    "relationship": ("互动", "关系", "承接"),
    "health": ("身心", "压力", "节律"),
    "time": ("大运", "流年", "触发"),
}

DOMAIN_SENTINEL_TOKENS: tuple[str, ...] = (
    "财",
    "官",
    "杀",
    "印",
    "食",
    "伤",
    "比",
    "劫",
    "木",
    "火",
    "土",
    "金",
    "水",
    "冲",
    "合",
    "刑",
    "害",
    "大运",
    "流年",
    "流月",
    "格局",
    "用神",
    "调候",
    "承载",
    "关系",
    "平衡",
)

PORTRAIT_DOMAIN_MECHANISM_LIBRARY: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "strength": (
        ("承载", ("承载", "承受", "根气", "扶身", "比肩", "劫财", "印")),
        ("泄耗", ("泄耗", "泄", "耗", "压力", "克制", "伤官", "官杀")),
        ("平衡", ("平衡", "协调", "强弱", "失衡")),
        ("时序", ("大运", "流年", "流月", "引动", "触发", "先后")),
    ),
    "wealth": (
        ("财源", ("财星", "财", "偏财", "正财", "财运")),
        ("承接", ("承接", "承载", "承受", "比肩", "劫财", "耗泄")),
        ("通道", ("食伤", "通道", "生财", "财运", "财星")),
        ("竞争", ("竞争", "争财", "夺财", "比肩", "劫财")),
        ("时序", ("大运", "流年", "流月", "触发", "引动")),
    ),
    "career": (
        ("角色", ("官星", "七杀", "伤官", "官杀", "事业", "事业线")),
        ("制化", ("制化", "缓冲", "印", "约束", "冲突")),
        ("节奏", ("表达", "推进", "执行", "主导", "关键")),
        ("时序", ("大运", "流年", "流月", "窗口", "阶段")),
    ),
    "relationship": (
        ("互动", ("互动", "关系", "合", "夫妻", "伴侣")),
        ("承接", ("承接", "响应", "沟通")),
        ("约束", ("约束", "冲突", "竞争", "克制")),
        ("时序", ("大运", "流年", "流月", "阶段")),
    ),
    "health": (
        ("平衡", ("平衡", "失衡", "五行", "偏枯", "压力", "承压")),
        ("节律", ("身心", "恢复", "调理", "耗损")),
        ("时序", ("大运", "流年", "流月", "阶段")),
    ),
    "time": (
        ("牵动", ("大运", "流年", "流月", "触发", "先后", "窗口")),
        ("回归", ("回到原局", "原局", "对照", "对比")),
        ("节奏", ("节奏", "顺序", "阶段")),
    ),
    "useful_god": (
        ("用神", ("用神", "取用", "择用")),
        ("扶泄", ("扶身", "泄秀", "泄", "扶")),
        ("财通", ("财通", "财星", "通道", "引财")),
        ("约束", ("官杀", "印", "约束", "牵制")),
    ),
    "pattern": (
        ("秩序", ("格局", "秩序", "主轴", "结构")),
        ("连贯", ("连续", "链条", "先后", "步骤")),
        ("成败", ("成败", "破局", "成形")),
    ),
    "element": (
        ("五行", ("五行", "偏枯", "偏旺", "偏弱")),
        ("承压", ("承压", "压力", "耗损", "失衡")),
        ("生克", ("相生", "相克", "流通", "循环")),
    ),
    "branch": (
        ("牵引", ("冲", "合", "刑", "害", "三合", "三会")),
        ("位势", ("地支", "藏", "位势", "支位")),
        ("调候", ("调候", "触发", "位势", "节奏")),
    ),
    "ten_god": (
        ("显隐", ("透", "藏干", "显出", "透出", "藏")),
        ("关系", ("生", "克", "制", "印", "比劫", "财", "官", "杀", "伤官")),
        ("协作", ("配合", "主次", "谁先", "谁主")),
    ),
}


def build_portrait_tag_profile(
    domain: str,
    source_rows: list[dict[str, Any]],
    axis_tier: str,
    *,
    score: float,
) -> PortraitTagProfile:
    blueprint = PORTRAIT_BLUEPRINTS.get(domain, {})
    tier = axis_tier or "micro"
    label = blueprint.get("label") or f"{domain_label(domain)}画像"
    base_tag = blueprint.get("tag") or domain_label(domain)
    state_tag = _dominant_profile_state(source_rows)
    mechanism_tags = _extract_mechanism_tags(source_rows, domain=domain)
    detail_tags = _state_summary_tags(source_rows)
    profile_tags = tuple(
        dict.fromkeys(
            (
                base_tag,
                *_axis_tier_tags(tier),
                *_domain_tags(domain),
                *detail_tags,
                *_state_profile_tags(source_rows),
                *mechanism_tags,
            ),
        ),
    )[:7]
    base_summary = blueprint.get("summary") or f"{domain_label(domain)}主题已形成画像定性。"
    if mechanism_tags:
        summary = f"{base_summary} 主要聚焦“{_join_short(mechanism_tags[:3])}”。"
    else:
        summary = base_summary
    return PortraitTagProfile(
        domain=domain,
        axis_tier=tier,
        label=label,
        profile_tag=f"{base_tag}：{state_tag}",
        profile_tags=profile_tags,
        profile_summary=summary,
        attention_level=_attention_level(score, source_rows),
        portrait_intent_type=blueprint.get("intent") or "topic_profile",
        calibration_state=_calibration_state(source_rows),
    )


def _attention_level(score: float, source_rows: list[dict[str, Any]]) -> str:
    states = _states(source_rows)
    if score >= 0.74 or states & {"confirmed", "chain_review", "volatile"}:
        return "high"
    if score >= 0.56 or states & {"mixed", "candidate", "weak_candidate"}:
        return "medium"
    return "normal"


def _dominant_profile_state(source_rows: list[dict[str, Any]]) -> str:
    states = _states(source_rows)
    if "volatile" in states:
        return "触发明显"
    if "confirmed" in states and ("chain_review" in states or "mixed" in states):
        return "主线成形"
    if "confirmed" in states:
        return "成立可用"
    if "requires_review" in states:
        return "低置信定向"
    if "mixed" in states:
        return "主次并存"
    if "weak_candidate" in states:
        return "偏弱成立"
    if "candidate" in states:
        return "结构入局"
    return "结构定性"


def _state_profile_tags(source_rows: list[dict[str, Any]]) -> tuple[str, ...]:
    states = _states(source_rows)
    tags: list[str] = []
    if "confirmed" in states:
        tags.append("已成结构")
    if "chain_review" in states:
        tags.append("链条成形")
    if "weak_candidate" in states:
        tags.append("偏弱成立")
    if "candidate" in states:
        tags.append("候选路径")
    if "mixed" in states:
        tags.append("主次并存")
    if "volatile" in states:
        tags.append("时运引动")
    if "requires_review" in states:
        tags.append("低置信定向")
    if not tags:
        tags.append("结构定性")
    return tuple(tags)


def _state_summary_tags(source_rows: list[dict[str, Any]]) -> tuple[str, ...]:
    states = _states(source_rows)
    tags: list[str] = []
    if "confirmed" in states:
        tags.append("已成立")
    if "chain_review" in states:
        tags.append("链式成形")
    if "mixed" in states:
        tags.append("主次并存")
    if "volatile" in states:
        tags.append("岁运触动")
    if "weak_candidate" in states:
        tags.append("偏弱成立")
    if "countered" in states:
        tags.append("受反制")
    if "requires_review" in states:
        tags.append("低置信定向")
    if not tags:
        tags.append("结构定性")
    return tuple(tags)


def _extract_mechanism_tags(source_rows: list[dict[str, Any]], domain: str) -> tuple[str, ...]:
    text = _merge_row_text(source_rows)
    library = PORTRAIT_DOMAIN_MECHANISM_LIBRARY.get(domain, ())
    selected: list[str] = []
    for tag, tokens in library:
        for token in tokens:
            if token in text:
                selected.append(tag)
                break
    if not selected:
        selected.extend(_domain_tags(domain))
    return tuple(dict.fromkeys(selected[:4]))


def _merge_row_text(source_rows: list[dict[str, Any]]) -> str:
    return " ".join(
        str(item)
        for row in source_rows
        for item in (
            _safe_text(row.get("label", "")),
            _safe_text(row.get("profile_tag", "")),
            _safe_text(row.get("summary", "")),
            _safe_text(row.get("boundary", "")),
            _safe_text(row.get("axis_state", "")),
            _safe_text(row.get("state", "")),
            _safe_text(row.get("structural_anchor", "")),
        )
        if item
    )


def _safe_text(value: object) -> str:
    return str(value or "").replace("：", " ").replace("；", " ").replace("，", " ").replace("。", " ").strip()


def _states(source_rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("state") or row.get("status", ""))
        for row in source_rows
        if row.get("state") or row.get("status")
    }


def _calibration_state(source_rows: list[dict[str, Any]]) -> str:
    states = sorted(_states(source_rows))
    if "volatile" in states:
        return "profile_decision:timing_triggered"
    if "confirmed" in states:
        return "profile_decision:decided"
    if states:
        return "profile_decision:system_selected"
    return "profile_decision:available"


def _join_short(items: tuple[str, ...], max_count: int = 3) -> str:
    return "、".join(items[:max_count])


def _axis_tier_tags(axis_tier: str) -> tuple[str, ...]:
    return PORTRAIT_AXIS_TIER_TAGS.get(axis_tier, ("结构视角",))


def _domain_tags(domain: str) -> tuple[str, ...]:
    return PORTRAIT_DOMAIN_TAGS.get(domain, (domain_label(domain),))
