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
    "stable_income": "稳定现金流",
    "opportunity_income": "机会型收入",
    "output_to_wealth": "输出变现",
    "authority_income": "平台/职位收入",
    "knowledge_asset": "知识资产",
    "resource_integration": "资源整合",
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
            "label": _clean_label(self.label),
            "score": round(_clamp(self.score), 3),
            "evidence": _clean_str_list(self.evidence, limit=5),
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
            "strengths": _clean_str_list(self.strengths, limit=8),
            "risks": _clean_str_list(self.risks, limit=8),
            "contradictions": _clean_str_list(self.contradictions, limit=8),
            "bridge_requirements": _clean_str_list(self.bridge_requirements, limit=8),
            "timing_hooks": _clean_str_list(self.timing_hooks, limit=6),
            "evidence": _clean_str_list(self.evidence, limit=10),
            "llm_prompt_focus": _clean_str_list(self.llm_prompt_focus, limit=8),
            "assertion_style": {
                "tone": _clean_label((self.assertion_style or {}).get("tone")),
                "must_include": _clean_str_list((self.assertion_style or {}).get("must_include"), limit=8),
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
            "十神财富簇："
            f"财{_score_sum(scores, _WEALTH_GODS):.1f}"
            f" / 食伤{_score_sum(scores, _OUTPUT_GODS):.1f}"
            f" / 比劫{_score_sum(scores, _PEER_GODS):.1f}"
            f" / 官杀{_score_sum(scores, _OFFICER_GODS):.1f}"
            f" / 印{_score_sum(scores, _SEAL_GODS):.1f}"
        )
    ]
    if macro_wealth:
        evidence.append(
            f"宏观象财富：{round(_safe_float(macro_wealth.get('score'), 0.0) * 100)}%，"
            f"风险{round(_safe_float(macro_wealth.get('risk'), 0.0) * 100)}%"
        )
    if use_gods or taboo_gods or tongguan_gods:
        evidence.append((
            "体用状态："
            + (f"用 {'/'.join(use_gods[:3])} " if use_gods else "")
            + (f"忌 {'/'.join(taboo_gods[:3])} " if taboo_gods else "")
            + (f"通关 {'/'.join(tongguan_gods[:3])}" if tongguan_gods else "")
        ).strip())
    if hits:
        evidence.append("结构命中：" + " / ".join(hits[:4]))

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
        _channel("stable_income", stable_score, ["正财主稳定收入与长期现金流", *(["正财格候选"] if "正财格" in hits else [])]),
        _channel("opportunity_income", opportunity_score, ["偏财主项目、市场与流动机会", *(["偏财/从财结构命中"] if {"偏财格", "从财"} & set(hits) else [])]),
        _channel("output_to_wealth", output_score, ["食伤把技能、产品、表达转成财富", *(["食伤生财/伤官生财命中"] if {"食伤生财", "伤官生财", "输出换财"} & set(hits) else [])]),
        _channel("authority_income", authority_score, ["财官看平台、职位、规则与合同承接", *(["财官结构命中"] if "财官" in hits else [])]),
        _channel("knowledge_asset", knowledge_score, ["财印看知识、资质、IP 与专业壁垒", *(["财印结构命中"] if "财印" in hits else [])]),
        _channel("resource_integration", integration_score, ["偏财与比劫牵动资源整合、合伙与分利", *(["从财或资源场命中"] if "从财" in hits else [])]),
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
        strengths.append("财星落在体用顺侧：" + " / ".join(wealth_use[:2]))
    if bridge_gods:
        strengths.append("财富需要桥接神承接：" + " / ".join(bridge_gods[:3]))

    risks: List[str] = []
    contradictions: List[str] = []
    bridge_requirements: List[str] = []
    risk = 0.1

    if wealth_taboo:
        risk += 0.22
        risks.append("财星在忌侧，财富强也可能带压力、牵扯或判断失衡")
        contradictions.append("财富显性与体用忌侧并存")
    if wealth_share > 0.18 and peer_share >= wealth_share * 0.72:
        risk += 0.16
        risks.append("比劫贴近财星，合伙、竞争、分利和破财风险抬高")
        contradictions.append("财富机会与同辈竞争同时出现")
        bridge_requirements.append("合伙、分账和资源边界必须先写清")
    if output_share >= 0.24 and wealth_share < 0.16:
        contradictions.append("食伤强于财星，财富更像输出转化路径，不是现成财库")
        bridge_requirements.append("先把技能、产品或表达做成可持续交付")
    if wealth_share >= 0.26 and peer_share + seal_share < 0.16:
        risk += 0.12
        risks.append("财势显性但承载侧偏弱，机会越多消耗越明显")
        bridge_requirements.append("先控制节奏、现金流和承载边界")
    if wealth_share >= 0.18 and seal_share >= 0.18:
        risk += 0.08
        risks.append("财印同显，短期资源与长期资质/口碑之间需要取舍")
        contradictions.append("资源变现与知识/资质积累存在拉扯")
    if shangguan_share >= 0.16 and officer_share >= 0.14:
        risk += 0.09
        risks.append("伤官与官杀同场，销售表达和规则风控要同步处理")
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
            timing_hooks.append(f"运行关系：{label}{axis or '触发'}")
        if stability_delta < -0.05:
            risk += min(0.14, abs(stability_delta) * 0.55)
            risks.append(f"{label or '运行关系'}降低稳定度，现金流或合作节奏需防波动")
            break

    blind_route = _clean_label(blind.get("primary_route")) if blind else ""
    if blind_route:
        evidence.append("盲派主线：" + blind_route)
    climate_state = _clean_label(climate.get("state")) if climate else ""
    climate_tension = _safe_float(climate.get("climate_tension"), 0.0) if climate else 0.0
    if climate_state:
        evidence.append("调候条件：" + climate_state)
    if climate_tension > 0.65:
        risk += 0.05
        risks.append(f"调候张力{climate_tension:.2f}，财富表达需先看环境承接")
    xiangfa_frames = xiangfa.get("event_framing") if isinstance(xiangfa.get("event_framing"), list) else []
    if xiangfa_frames:
        evidence.append("象法事件：" + " / ".join(_clean_str_list(xiangfa_frames, limit=2)))

    top_channel = primary_channels[0] if primary_channels else ranked_channels[0]
    bridge_requirements.extend(
        {
            "stable_income": ["把稳定现金流、预算和长期经营节奏作为主承接"],
            "opportunity_income": ["机会型收入必须配风控、退出条件和现金流缓冲"],
            "output_to_wealth": ["先把输出做成产品、服务或可复购交付"],
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
        strengths.append("财富信号偏弱，暂以观察和条件解释为主")

    if pt.get("luck_pillar") or pt.get("flow_pillar") or pt.get("flow_year"):
        timing_hooks.append("大运/流年可作为财富触发窗口观察，但本画像不直接下时间断语")

    tone = "risk_first" if risk >= 0.48 else "cautious" if usable_state == "wealth_as_taboo" or risk >= 0.36 else "opportunity" if score >= 0.66 else "practical"
    must_include = [
        f"主财富渠道：{top_channel.label}",
        f"可用状态：{usable_state}",
        "同时写机会、风险和承接条件",
    ]
    if risks:
        must_include.append("首要风险：" + risks[0])
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
            "财富断言只基于 wealth_profile，不直接自由解释原始八字。",
            f"先写财富来源：{top_channel.label}",
            f"再写可用状态：{usable_state}",
            "最后写风险、承接条件和行动建议。",
        ),
        assertion_style=assertion_style,
    ).to_meta()
    return {
        "contract": profile["contract"],
        "confidence": profile["confidence"],
        "wealth_profile": profile,
    }
