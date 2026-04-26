from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import normalize_blind_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import normalize_climate_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import normalize_xiangfa_theme_meta
from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme_core import (
    normalize_macro_theme_meta,
    resolve_macro_theme,
)
from v17_rebirth.backend.services.physics_layers import read_runtime_scores


WEALTH_PROFILE_CONTRACT = "v17.topic.wealth_profile.v1"

FINAL_WEALTH_PROFILE_KEYS: List[str] = [
    "contract",
    "is_l3_topic_decoder",
    "topic",
    "score",
    "confidence",
    "risk",
    "stance",
    "visibility",
    "usable_state",
    "primary_channels",
    "source_gods",
    "strengths",
    "risks",
    "contradictions",
    "bridge_requirements",
    "timing_hooks",
    "evidence",
    "llm_prompt_focus",
    "assertion_style",
    "learning_hooks",
    "guardrails",
]

TEMPORARY_WEALTH_PROFILE_KEYS: List[str] = [
    "wealth_raw_scores",
    "wealth_channel_trace",
    "wealth_keyword_hits",
]

_WEALTH_GODS = ("正财", "偏财")
_OUTPUT_GODS = ("食神", "伤官")
_OFFICER_GODS = ("正官", "七杀")
_SEAL_GODS = ("正印", "偏印")
_PEER_GODS = ("比肩", "劫财")

_CHANNEL_LABELS: Dict[str, str] = {
    "stable_income": "稳定收入",
    "opportunity_income": "项目机会",
    "output_to_wealth": "技能变现",
    "authority_income": "职位/平台收入",
    "knowledge_asset": "专业资产",
    "resource_integration": "合作资源",
}

_WEALTH_KEYWORDS = (
    "正财格",
    "偏财格",
    "食伤生财",
    "伤官生财",
    "从财",
    "财官",
    "财印",
    "劫财夺财",
    "比劫夺财",
    "现金流",
    "输出换财",
)

_GOD_PUBLIC_LABELS: Dict[str, str] = {
    "正财": "稳定收入",
    "偏财": "项目机会",
    "食神": "稳定输出",
    "伤官": "表达与销售转化",
    "正官": "平台规则",
    "七杀": "高压竞争",
    "正印": "资质信用",
    "偏印": "专业方法",
    "比肩": "同辈合作",
    "劫财": "竞争分利",
}

_KEYWORD_PUBLIC_LABELS: Dict[str, str] = {
    "正财格": "稳定收入线索",
    "偏财格": "项目机会线索",
    "食伤生财": "技能变现线索",
    "伤官生财": "表达/销售变现线索",
    "从财": "市场机会线索",
    "财官": "职位/平台收入线索",
    "财印": "专业资产线索",
    "劫财夺财": "合作分账风险",
    "比劫夺财": "竞争分利风险",
    "现金流": "现金流",
    "输出换财": "技能变现线索",
}

_PUBLIC_PHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("wealth_profile 判定", ""),
    ("食伤生财", "技能变现"),
    ("伤官生财", "表达/销售变现"),
    ("输出换财", "技能变现"),
    ("正财格", "稳定收入线索"),
    ("偏财格", "项目机会线索"),
    ("财官", "职位/平台收入"),
    ("财印", "专业资产"),
    ("劫财夺财", "合作分账风险"),
    ("比劫夺财", "竞争分利风险"),
    ("从财", "市场机会线索"),
    ("十神财富簇", "财富结构"),
    ("宏观象财富", "财富主题"),
    ("体用状态", "机会状态"),
    ("体用顺侧", "机会比较顺"),
    ("体用忌侧", "机会伴随压力"),
    ("忌侧", "压力侧"),
    ("顺侧", "较顺"),
    ("通关", "需要中间条件"),
    ("桥接神", "中间条件"),
    ("财星落在机会比较顺", "赚钱机会比较容易落地"),
    ("财星在压力侧", "赚钱机会会带来压力"),
    ("财富需要中间条件承接", "需要先靠能力、平台或专业资质把赚钱机会接住"),
    ("比劫贴近财星", "合作与竞争离钱很近"),
    ("食伤强于财星", "能力输出强于直接收入"),
    ("不是现成财库", "不是一来就有现成收益"),
    ("财势显性", "赚钱机会明显"),
    ("财印同显", "短期变现和长期专业积累同时出现"),
    ("伤官与官杀同场", "销售表达和规则压力同时出现"),
    ("调候张力", "环境压力"),
    ("财富表达", "赚钱方式"),
    ("盲派主线", "经验派线索"),
    ("调候条件", "环境条件"),
    ("象法事件", "事件线索"),
    ("运行关系", "阶段变化"),
    ("财星", "赚钱机会"),
    ("食伤", "技能/表达"),
    ("比劫", "合作/竞争"),
    ("官杀", "规则/压力"),
    ("印星", "资质/信用"),
    ("正财", "稳定收入"),
    ("偏财", "项目机会"),
    ("食神", "稳定输出"),
    ("伤官", "表达与销售转化"),
    ("正官", "平台规则"),
    ("七杀", "高压竞争"),
    ("正印", "资质信用"),
    ("偏印", "专业方法"),
    ("比肩", "同辈合作"),
    ("劫财", "竞争分利"),
)


def _clean_label(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_str_list(values: Sequence[Any] | None, *, limit: int = 8) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    rows: List[str] = []
    seen: set[str] = set()
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
        if len(rows) >= limit:
            break
    return rows


def _public_phrase(value: Any, *, limit: int = 180) -> str:
    text = _clean_label(value, limit=limit)
    if not text:
        return ""
    for source, target in _PUBLIC_PHRASE_REPLACEMENTS:
        text = text.replace(source, target)
    while "  " in text:
        text = text.replace("  ", " ")
    text = text.replace("： /", "：").replace("：/", "：").strip(" ，；、")
    return text


def _public_str_list(values: Sequence[Any] | None, *, limit: int = 8) -> List[str]:
    return [_public_phrase(item) for item in _clean_str_list(values, limit=limit) if _public_phrase(item)]


def _public_god_list(gods: Sequence[Any], *, limit: int = 3) -> str:
    labels = []
    for god in _clean_str_list(gods, limit=limit):
        labels.append(_GOD_PUBLIC_LABELS.get(god, god))
    return " / ".join(dict.fromkeys(label for label in labels if label))


def _public_keyword_hits(hits: Sequence[str], *, limit: int = 4) -> List[str]:
    labels = []
    for hit in hits[:limit]:
        labels.append(_KEYWORD_PUBLIC_LABELS.get(hit, hit))
    return list(dict.fromkeys(label for label in labels if label))


def _public_usable_state(value: str) -> str:
    key = str(value or "").strip()
    if key == "wealth_as_use":
        return "赚钱机会比较容易落地"
    if key == "wealth_as_taboo":
        return "赚钱机会伴随压力，需要先管风险"
    if key == "wealth_needs_bridge":
        return "需要先靠能力、平台或专业资质把机会接住"
    return "先观察收入来源是否稳定"


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return next_value


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _score_sum(scores: Mapping[str, Any], gods: Sequence[str]) -> float:
    return sum(max(0.0, _safe_float(scores.get(god), 0.0)) for god in gods)


def _share(scores: Mapping[str, Any], gods: Sequence[str], total: float) -> float:
    return _score_sum(scores, gods) / max(total, 1.0)


def _authority_gods(authority: Mapping[str, Any], key_a: str, key_b: str) -> List[str]:
    value = authority.get(key_a)
    if isinstance(value, str) and value.strip():
        return [_clean_label(value)]
    if isinstance(value, list):
        return _clean_str_list(value, limit=8)
    fallback = authority.get(key_b)
    if isinstance(fallback, str) and fallback.strip():
        return [_clean_label(fallback)]
    return _clean_str_list(fallback, limit=8)


def _facts_text(physics_tensor: Mapping[str, Any], meta: Mapping[str, Any]) -> str:
    fragments: List[str] = []
    for row in physics_tensor.get("facts") or []:
        if isinstance(row, Mapping):
            plugin_id = _clean_label(row.get("plugin") or row.get("plugin_id"))
            fact_meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
            claim_type = _clean_label(fact_meta.get("claim_type"))
            if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
                "macro_theme_observation",
                "topic_profile_observation",
            }:
                continue
            fragments.append(_clean_label(row.get("fact"), limit=220))
        else:
            fragments.append(_clean_label(row, limit=220))
    for row in meta.get("plugin_claims") or []:
        if not isinstance(row, Mapping):
            continue
        plugin_id = _clean_label(row.get("plugin_id") or row.get("plugin"))
        claim_type = _clean_label(row.get("claim_type"))
        if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
            "macro_theme_observation",
            "topic_profile_observation",
        }:
            continue
        fragments.extend(
            _clean_label(row.get(key), limit=120)
            for key in ("claim_text", "pattern_candidate", "pattern_name", "source_event", "plugin_id")
        )
    return " ".join(fragment for fragment in fragments if fragment)


def _keyword_hits(text: str) -> List[str]:
    return [word for word in _WEALTH_KEYWORDS if word and word in text][:8]


def _macro_wealth_topic(pt: Dict[str, Any], meta: Mapping[str, Any]) -> Dict[str, Any]:
    macro = normalize_macro_theme_meta(meta.get("macro_theme"))
    if not macro:
        macro = normalize_macro_theme_meta(resolve_macro_theme(pt).get("macro_theme"))
    rows = macro.get("topics") if isinstance(macro.get("topics"), list) else []
    for row in rows:
        if isinstance(row, Mapping) and str(row.get("id") or "").strip() == "wealth":
            return dict(row)
    return {}


def _channel(
    channel_id: str,
    score: float,
    evidence: Sequence[str],
) -> "WealthChannel":
    return WealthChannel(
        id=channel_id,
        label=_CHANNEL_LABELS.get(channel_id, channel_id),
        score=_clamp(score),
        evidence=tuple(_clean_str_list(evidence, limit=5)),
    )


def build_wealth_profile_contract() -> Dict[str, Any]:
    return {
        "contract": WEALTH_PROFILE_CONTRACT,
        "is_l3_topic_decoder": True,
        "topic": "wealth",
        "final_meta_keys": list(FINAL_WEALTH_PROFILE_KEYS),
        "temporary_meta_keys": list(TEMPORARY_WEALTH_PROFILE_KEYS),
        "read_only_sources": [
            "ten_gods_runtime",
            "god_ring_authority",
            "macro_theme",
            "plugin_claims",
            "blind_theme",
            "xiangfa_theme",
            "climate_theme",
            "relation_dynamics_summary",
            "practitioner_override_context",
        ],
        "constraints": [
            "财富画像属于 L3 专题解码层，只读微观材料，不回写物理能量、格局候选、体用裁决或参数。",
            "财富画像先解出财富来源、可用状态、承载与风险；LLM 只能基于画像写财富断言。",
            "不得把财星强等同于必发财，也不得把财星弱等同于不能赚钱。",
        ],
    }


@dataclass(frozen=True)
class WealthChannel:
    id: str
    label: str
    score: float
    evidence: Sequence[str] = field(default_factory=tuple)

    def to_meta(self) -> Dict[str, Any]:
        return {
            "id": _clean_label(self.id),
            "label": _public_phrase(self.label),
            "score": round(_clamp(self.score), 3),
            "evidence": _public_str_list(self.evidence, limit=5),
        }


@dataclass(frozen=True)
class WealthProfileResult:
    score: float = 0.0
    confidence: float = 0.0
    risk: float = 0.0
    stance: str = "latent"
    visibility: str = "weak_signal"
    usable_state: str = "unclear"
    primary_channels: Sequence[WealthChannel] = field(default_factory=tuple)
    source_gods: Mapping[str, Sequence[str]] = field(default_factory=dict)
    strengths: Sequence[str] = field(default_factory=tuple)
    risks: Sequence[str] = field(default_factory=tuple)
    contradictions: Sequence[str] = field(default_factory=tuple)
    bridge_requirements: Sequence[str] = field(default_factory=tuple)
    timing_hooks: Sequence[str] = field(default_factory=tuple)
    evidence: Sequence[str] = field(default_factory=tuple)
    llm_prompt_focus: Sequence[str] = field(default_factory=tuple)
    assertion_style: Mapping[str, Any] = field(default_factory=dict)

    def to_meta(self) -> Dict[str, Any]:
        return {
            "contract": WEALTH_PROFILE_CONTRACT,
            "is_l3_topic_decoder": True,
            "topic": "wealth",
            "score": round(_clamp(self.score), 3),
            "confidence": round(_clamp(self.confidence), 3),
            "risk": round(_clamp(self.risk), 3),
            "stance": _clean_label(self.stance),
            "visibility": _clean_label(self.visibility),
            "usable_state": _clean_label(self.usable_state),
            "primary_channels": [channel.to_meta() for channel in self.primary_channels[:6]],
            "source_gods": {
                _clean_label(key, limit=40): _clean_str_list(value, limit=6)
                for key, value in dict(self.source_gods or {}).items()
                if _clean_label(key, limit=40)
            },
            "strengths": _public_str_list(self.strengths, limit=8),
            "risks": _public_str_list(self.risks, limit=8),
            "contradictions": _public_str_list(self.contradictions, limit=8),
            "bridge_requirements": _public_str_list(self.bridge_requirements, limit=8),
            "timing_hooks": _public_str_list(self.timing_hooks, limit=6),
            "evidence": _public_str_list(self.evidence, limit=10),
            "llm_prompt_focus": _public_str_list(self.llm_prompt_focus, limit=8),
            "assertion_style": {
                "tone": _clean_label((self.assertion_style or {}).get("tone")),
                "must_include": _public_str_list((self.assertion_style or {}).get("must_include"), limit=8),
                "must_avoid": _clean_str_list((self.assertion_style or {}).get("must_avoid"), limit=8),
            },
            "learning_hooks": [
                "topic.wealth.channel.calibration",
                "topic.wealth.usable_state.calibration",
                "topic.wealth.risk.calibration",
            ],
            "guardrails": build_wealth_profile_contract()["constraints"],
        }


def normalize_wealth_profile_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, WealthProfileResult):
        return value.to_meta()
    if not isinstance(value, dict):
        return {}
    raw_channels = value.get("primary_channels") if isinstance(value.get("primary_channels"), list) else []
    channels: List[WealthChannel] = []
    for row in raw_channels:
        if not isinstance(row, Mapping):
            continue
        channel_id = _clean_label(row.get("id"))
        if not channel_id:
            continue
        channels.append(
            WealthChannel(
                id=channel_id,
                label=_clean_label(row.get("label")) or _CHANNEL_LABELS.get(channel_id, channel_id),
                score=_safe_float(row.get("score"), 0.0),
                evidence=tuple(_clean_str_list(row.get("evidence"), limit=5)),
            )
        )
    source_gods = value.get("source_gods") if isinstance(value.get("source_gods"), Mapping) else {}
    return WealthProfileResult(
        score=_safe_float(value.get("score"), 0.0),
        confidence=_safe_float(value.get("confidence"), 0.0),
        risk=_safe_float(value.get("risk"), 0.0),
        stance=_clean_label(value.get("stance")) or "latent",
        visibility=_clean_label(value.get("visibility")) or "weak_signal",
        usable_state=_clean_label(value.get("usable_state")) or "unclear",
        primary_channels=tuple(channels),
        source_gods={str(key): _clean_str_list(raw, limit=6) for key, raw in dict(source_gods).items()},
        strengths=tuple(_clean_str_list(value.get("strengths"), limit=8)),
        risks=tuple(_clean_str_list(value.get("risks"), limit=8)),
        contradictions=tuple(_clean_str_list(value.get("contradictions"), limit=8)),
        bridge_requirements=tuple(_clean_str_list(value.get("bridge_requirements"), limit=8)),
        timing_hooks=tuple(_clean_str_list(value.get("timing_hooks"), limit=6)),
        evidence=tuple(_clean_str_list(value.get("evidence"), limit=10)),
        llm_prompt_focus=tuple(_clean_str_list(value.get("llm_prompt_focus"), limit=8)),
        assertion_style=value.get("assertion_style") if isinstance(value.get("assertion_style"), Mapping) else {},
    ).to_meta()


def resolve_wealth_profile(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    energy_meta = pt.get("energy_meta") if isinstance(pt.get("energy_meta"), dict) else {}
    scores = read_runtime_scores(pt)
    if not scores:
        scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    if not scores:
        return {"wealth_profile": {}, "confidence": 0.0}

    total = sum(max(0.0, _safe_float(value, 0.0)) for value in scores.values()) or 1.0
    wealth_share = _share(scores, _WEALTH_GODS, total)
    output_share = _share(scores, _OUTPUT_GODS, total)
    officer_share = _share(scores, _OFFICER_GODS, total)
    seal_share = _share(scores, _SEAL_GODS, total)
    peer_share = _share(scores, _PEER_GODS, total)
    zhengcai_share = _share(scores, ("正财",), total)
    piancai_share = _share(scores, ("偏财",), total)
    shishen_share = _share(scores, ("食神",), total)
    shangguan_share = _share(scores, ("伤官",), total)

    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    use_gods = _authority_gods(authority, "use_gods", "god_of_use")
    taboo_gods = _authority_gods(authority, "taboo_gods", "god_of_taboo")
    tongguan_gods = _authority_gods(authority, "tongguan_gods", "god_of_tongguan")
    wealth_use = [god for god in _WEALTH_GODS if god in use_gods]
    wealth_taboo = [god for god in _WEALTH_GODS if god in taboo_gods]
    bridge_gods = [god for god in (*_OUTPUT_GODS, *_OFFICER_GODS, *_SEAL_GODS) if god in use_gods or god in tongguan_gods]

    text = _facts_text(pt, meta)
    hits = _keyword_hits(text)
    macro_wealth = _macro_wealth_topic(pt, meta)
    blind = normalize_blind_theme_meta(meta.get("blind_theme"))
    climate = normalize_climate_theme_meta(meta.get("climate_theme"))
    xiangfa = normalize_xiangfa_theme_meta(meta.get("xiangfa_theme"))

    evidence: List[str] = [
        (
            "财富结构："
            f"直接收入{_score_sum(scores, _WEALTH_GODS):.1f}"
            f" / 技能转化{_score_sum(scores, _OUTPUT_GODS):.1f}"
            f" / 合作竞争{_score_sum(scores, _PEER_GODS):.1f}"
            f" / 平台规则{_score_sum(scores, _OFFICER_GODS):.1f}"
            f" / 专业信用{_score_sum(scores, _SEAL_GODS):.1f}"
        )
    ]
    if macro_wealth:
        evidence.append(
            f"财富主题：{round(_safe_float(macro_wealth.get('score'), 0.0) * 100)}%，"
            f"风险{round(_safe_float(macro_wealth.get('risk'), 0.0) * 100)}%"
        )
    if use_gods or taboo_gods or tongguan_gods:
        favorable_text = _public_god_list(use_gods[:3])
        pressure_text = _public_god_list(taboo_gods[:3])
        bridge_text = _public_god_list(tongguan_gods[:3])
        evidence.append((
            "机会状态："
            + (f"适合发挥 {favorable_text} " if favorable_text else "")
            + (f"需要小心 {pressure_text} " if pressure_text else "")
            + (f"中间条件 {bridge_text}" if bridge_text else "")
        ).strip())
    if hits:
        evidence.append("财富路径线索：" + " / ".join(_public_keyword_hits(hits[:4])))

    stable_score = 0.18 + zhengcai_share * 2.2 + officer_share * 0.16
    opportunity_score = 0.16 + piancai_share * 2.2 + shangguan_share * 0.28
    output_score = 0.16 + output_share * 0.92 + wealth_share * 0.72
    authority_score = 0.13 + officer_share * 0.86 + wealth_share * 0.58
    knowledge_score = 0.12 + seal_share * 0.82 + wealth_share * 0.45
    integration_score = 0.12 + piancai_share * 0.84 + peer_share * 0.48

    if "正财格" in hits:
        stable_score += 0.16
    if "偏财格" in hits:
        opportunity_score += 0.16
    if any(hit in hits for hit in ("食伤生财", "伤官生财", "输出换财")):
        output_score += 0.18
    if "财官" in hits:
        authority_score += 0.16
    if "财印" in hits:
        knowledge_score += 0.14
    if "从财" in hits:
        opportunity_score += 0.1
        integration_score += 0.16
    if wealth_use:
        stable_score += 0.06 if "正财" in wealth_use else 0.0
        opportunity_score += 0.06 if "偏财" in wealth_use else 0.0
    if any(god in bridge_gods for god in _OUTPUT_GODS):
        output_score += 0.11
    if any(god in bridge_gods for god in _OFFICER_GODS):
        authority_score += 0.1
    if any(god in bridge_gods for god in _SEAL_GODS):
        knowledge_score += 0.1

    channels = [
        _channel("stable_income", stable_score, ["适合稳定收入、长期客户和固定现金流", *(["稳定收入线索明显"] if "正财格" in hits else [])]),
        _channel("opportunity_income", opportunity_score, ["适合项目机会、市场波动和资源撮合", *(["项目/市场机会线索明显"] if {"偏财格", "从财"} & set(hits) else [])]),
        _channel("output_to_wealth", output_score, ["适合把技能、内容、产品或表达转成收入", *(["技能变现线索明显"] if {"食伤生财", "伤官生财", "输出换财"} & set(hits) else [])]),
        _channel("authority_income", authority_score, ["收入更依赖平台、职位、规则和合同", *(["职位/平台收入线索明显"] if "财官" in hits else [])]),
        _channel("knowledge_asset", knowledge_score, ["适合靠知识、资质、IP 或专业壁垒赚钱", *(["专业资产线索明显"] if "财印" in hits else [])]),
        _channel("resource_integration", integration_score, ["钱容易从资源整合、合伙项目和分利中出现", *(["资源合作线索明显"] if "从财" in hits else [])]),
    ]
    ranked_channels = sorted(channels, key=lambda row: row.score, reverse=True)
    primary_channels = tuple(channel for channel in ranked_channels if channel.score >= 0.26)[:4] or tuple(ranked_channels[:2])

    if wealth_share >= 0.22 or _score_sum(scores, _WEALTH_GODS) >= 35.0:
        visibility = "explicit_wealth"
    elif output_share >= 0.22 and _score_sum(scores, _WEALTH_GODS) >= 6.0:
        visibility = "hidden_wealth"
    elif officer_share + seal_share >= 0.34 or any(hit in hits for hit in ("财官", "财印")):
        visibility = "indirect_wealth"
    else:
        visibility = "weak_signal"

    if wealth_taboo:
        usable_state = "wealth_as_taboo"
    elif wealth_use:
        usable_state = "wealth_as_use"
    elif bridge_gods:
        usable_state = "wealth_needs_bridge"
    else:
        usable_state = "unclear"

    strengths: List[str] = []
    for channel in primary_channels[:3]:
        strengths.append(f"{channel.label}：{round(channel.score * 100)}%")
    if wealth_use:
        strengths.append("赚钱机会比较容易落地：" + _public_god_list(wealth_use[:2]))
    if bridge_gods:
        strengths.append("需要先靠这些条件把机会接住：" + _public_god_list(bridge_gods[:3]))

    risks: List[str] = []
    contradictions: List[str] = []
    bridge_requirements: List[str] = []
    risk = 0.1

    if wealth_taboo:
        risk += 0.22
        risks.append("赚钱机会会带来压力，越有机会越要控制承诺、预算和判断节奏")
        contradictions.append("机会很明显，但压力也会跟着变大")
    if wealth_share > 0.18 and peer_share >= wealth_share * 0.72:
        risk += 0.16
        risks.append("合作、竞争和分账容易影响收入，合伙项目尤其要先算清楚")
        contradictions.append("财富机会与同辈竞争同时出现")
        bridge_requirements.append("合伙、分账和资源边界必须先写清")
    if output_share >= 0.24 and wealth_share < 0.16:
        contradictions.append("能力和表达很强，但钱要靠产品、服务或持续交付转出来，不是一开始就有现成收益")
        bridge_requirements.append("先把技能、产品或表达做成可持续交付")
    if wealth_share >= 0.26 and peer_share + seal_share < 0.16:
        risk += 0.12
        risks.append("赚钱机会明显，但承载能力偏弱，机会越多越容易被消耗")
        bridge_requirements.append("先控制节奏、现金流和承载边界")
    if wealth_share >= 0.18 and seal_share >= 0.18:
        risk += 0.08
        risks.append("短期变现和长期口碑/资质都重要，不能只追快钱")
        contradictions.append("资源变现与知识/资质积累存在拉扯")
    if shangguan_share >= 0.16 and officer_share >= 0.14:
        risk += 0.09
        risks.append("销售表达和规则压力同时出现，越会卖越要注意合同、合规和边界")
        bridge_requirements.append("项目、合同、合规和对外表达需要同框管理")

    relation_rows = energy_meta.get("relation_dynamics_summary") if isinstance(energy_meta.get("relation_dynamics_summary"), list) else []
    timing_hooks: List[str] = []
    for row in relation_rows[:4]:
        if not isinstance(row, Mapping):
            continue
        stability_delta = _safe_float(row.get("stability_delta_ratio"), 0.0)
        label = _clean_label(row.get("label"))
        axis = _clean_label(row.get("energy_axis"))
        if label:
            timing_hooks.append(f"阶段变化：{label}{axis or '触发'}，容易影响收入节奏")
        if stability_delta < -0.05:
            risk += min(0.14, abs(stability_delta) * 0.55)
            risks.append(f"{label or '阶段变化'}会降低稳定度，现金流或合作节奏需防波动")
            break

    blind_route = _clean_label(blind.get("primary_route")) if blind else ""
    if blind_route:
        evidence.append("经验派线索：" + _public_phrase(blind_route))
    climate_state = _clean_label(climate.get("state")) if climate else ""
    climate_tension = _safe_float(climate.get("climate_tension"), 0.0) if climate else 0.0
    if climate_state:
        evidence.append("环境条件：" + _public_phrase(climate_state))
    if climate_tension > 0.65:
        risk += 0.05
        risks.append(f"环境压力{climate_tension:.2f}，赚钱方式要先看现实条件能不能接住")
    xiangfa_frames = xiangfa.get("event_framing") if isinstance(xiangfa.get("event_framing"), list) else []
    if xiangfa_frames:
        evidence.append("事件线索：" + " / ".join(_public_str_list(xiangfa_frames, limit=2)))

    top_channel = primary_channels[0] if primary_channels else ranked_channels[0]
    bridge_requirements.extend(
        {
            "stable_income": ["把固定收入、预算和长期经营节奏先稳住"],
            "opportunity_income": ["机会型收入必须配风控、退出条件和现金流缓冲"],
            "output_to_wealth": ["先把技能、内容或产品做成服务与可复购交付"],
            "authority_income": ["用平台、合同、职位和规则承接财富机会"],
            "knowledge_asset": ["用资质、知识产权、方法论或专业壁垒承接财富"],
            "resource_integration": ["资源整合要先定义权责、分利和边界"],
        }.get(top_channel.id, [])
    )

    macro_score = _safe_float(macro_wealth.get("score"), 0.0) if macro_wealth else 0.0
    raw_score = max(top_channel.score, macro_score * 0.92, 0.2 + wealth_share * 1.25 + output_share * 0.28)
    score = _clamp(raw_score, 0.08, 0.96)
    risk = _clamp(risk, 0.02, 0.86)
    stance = "active" if score >= 0.66 and risk < 0.38 else "volatile" if score >= 0.56 and risk >= 0.38 else "watch" if score >= 0.45 else "latent"
    source_count = 1 + int(bool(authority)) + int(bool(hits)) + int(bool(macro_wealth)) + int(bool(blind)) + int(bool(climate)) + int(bool(xiangfa)) + int(bool(relation_rows))
    confidence = _clamp(0.36 + min(source_count, 7) * 0.065 + score * 0.14 - risk * 0.05, 0.35, 0.91)

    if not risks and risk >= 0.32:
        risks.append("财富机会伴随结构波动，需要带条件解释")
    if not strengths:
        strengths.append("赚钱信号偏弱，先观察收入来源是否稳定")

    if pt.get("luck_pillar") or pt.get("flow_pillar") or pt.get("flow_year"):
        timing_hooks.append("十年阶段和年度变化可以作为收入机会窗口观察，但这里先不直接下年份断语")

    tone = "risk_first" if risk >= 0.48 else "cautious" if usable_state == "wealth_as_taboo" or risk >= 0.36 else "opportunity" if score >= 0.66 else "practical"
    must_include = [
        f"主要赚钱方式：{top_channel.label}",
        f"机会状态：{_public_usable_state(usable_state)}",
        "同时写钱怎么来、哪里会漏钱、要先做到什么",
    ]
    if risks:
        must_include.append("最需要避开的坑：" + risks[0])
    assertion_style = {
        "tone": tone,
        "must_include": must_include,
        "must_avoid": ["必发财", "无财", "破产", "把财星强等同于钱多", "虚构金额或确定时间点"],
    }

    profile = WealthProfileResult(
        score=score,
        confidence=confidence,
        risk=risk,
        stance=stance,
        visibility=visibility,
        usable_state=usable_state,
        primary_channels=primary_channels,
        source_gods={
            "wealth": [god for god in _WEALTH_GODS if _safe_float(scores.get(god), 0.0) > 0.0],
            "output": [god for god in _OUTPUT_GODS if _safe_float(scores.get(god), 0.0) > 0.0],
            "peer": [god for god in _PEER_GODS if _safe_float(scores.get(god), 0.0) > 0.0],
            "authority": [god for god in _OFFICER_GODS if _safe_float(scores.get(god), 0.0) > 0.0],
            "seal": [god for god in _SEAL_GODS if _safe_float(scores.get(god), 0.0) > 0.0],
        },
        strengths=tuple(strengths),
        risks=tuple(risks),
        contradictions=tuple(contradictions),
        bridge_requirements=tuple(dict.fromkeys(bridge_requirements)),
        timing_hooks=tuple(dict.fromkeys(timing_hooks)),
        evidence=tuple(dict.fromkeys(evidence)),
        llm_prompt_focus=(
            "写给普通用户，只讲财富语言，不讲命理术语。",
            f"先写主要赚钱方式：{top_channel.label}",
            f"再写机会状态：{_public_usable_state(usable_state)}",
            "最后写现金流风险、要避开的坑和下一步行动。",
        ),
        assertion_style=assertion_style,
    ).to_meta()
    return {
        "contract": profile["contract"],
        "confidence": profile["confidence"],
        "wealth_profile": profile,
    }
