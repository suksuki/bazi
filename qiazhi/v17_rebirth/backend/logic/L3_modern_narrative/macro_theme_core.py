from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import normalize_blind_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import normalize_climate_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import normalize_xiangfa_theme_meta
from v17_rebirth.backend.services.physics_layers import read_runtime_scores


FINAL_MACRO_THEME_KEYS: List[str] = [
    "contract",
    "is_l3_macro_topic",
    "confidence",
    "topics",
    "top_topics",
    "prompt_digest",
    "source_topics",
    "llm_guidance",
    "learning_hooks",
    "guardrails",
]

TEMPORARY_MACRO_THEME_KEYS: List[str] = [
    "macro_raw_scores",
    "macro_keyword_hits",
    "macro_source_trace",
]

_WEALTH_GODS = ("正财", "偏财")
_OUTPUT_GODS = ("食神", "伤官")
_OFFICER_GODS = ("正官", "七杀")
_SEAL_GODS = ("正印", "偏印")
_PEER_GODS = ("比肩", "劫财")

_TOPIC_LABELS: Dict[str, str] = {
    "wealth": "财富",
    "career": "事业",
    "relationship": "感情",
    "personality": "性格",
}

_TOPIC_KEYWORDS: Dict[str, tuple[str, ...]] = {
    "wealth": ("财", "食伤生财", "伤官生财", "从财", "资源", "现金流", "输出换财"),
    "career": ("官", "杀", "官印", "财官", "规则", "职位", "责任", "事业", "组织"),
    "relationship": ("感情", "伴侣", "婚", "合", "财官", "家里家外", "关系", "绑定"),
    "personality": ("性格", "比劫", "印", "食伤", "伤官", "体态", "表达", "边界"),
}


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


def _topic_gods(topic_id: str, gender: str = "") -> tuple[str, ...]:
    if topic_id == "wealth":
        return (*_WEALTH_GODS, *_OUTPUT_GODS)
    if topic_id == "career":
        return (*_OFFICER_GODS, *_SEAL_GODS, *_WEALTH_GODS)
    if topic_id == "relationship":
        if gender == "male":
            return (*_WEALTH_GODS, *_OFFICER_GODS)
        if gender == "female":
            return (*_OFFICER_GODS, *_WEALTH_GODS)
        return (*_WEALTH_GODS, *_OFFICER_GODS)
    return (*_PEER_GODS, *_OUTPUT_GODS, *_SEAL_GODS)


def _cluster_shares(scores: Mapping[str, Any]) -> Dict[str, float]:
    total = sum(max(0.0, _safe_float(value, 0.0)) for value in scores.values()) or 1.0
    return {
        "wealth": _share(scores, _WEALTH_GODS, total),
        "output": _share(scores, _OUTPUT_GODS, total),
        "officer": _share(scores, _OFFICER_GODS, total),
        "seal": _share(scores, _SEAL_GODS, total),
        "peer": _share(scores, _PEER_GODS, total),
    }


def _facts_text(physics_tensor: Mapping[str, Any], meta: Mapping[str, Any]) -> str:
    fragments: List[str] = []
    for row in physics_tensor.get("facts") or []:
        if isinstance(row, Mapping):
            plugin_id = _clean_label(row.get("plugin") or row.get("plugin_id"))
            fact_meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
            if plugin_id.startswith("modern.macro.") or fact_meta.get("claim_type") == "macro_theme_observation":
                continue
            fragments.append(_clean_label(row.get("fact"), limit=220))
        else:
            fragments.append(_clean_label(row, limit=220))
    for row in meta.get("plugin_claims") or []:
        if not isinstance(row, Mapping):
            continue
        plugin_id = _clean_label(row.get("plugin_id") or row.get("plugin"))
        claim_type = _clean_label(row.get("claim_type"))
        if plugin_id.startswith("modern.macro.") or claim_type == "macro_theme_observation":
            continue
        fragments.extend(
            _clean_label(row.get(key), limit=120)
            for key in ("claim_text", "pattern_candidate", "pattern_name", "source_event", "plugin_id")
        )
    return " ".join(fragment for fragment in fragments if fragment)


def _keyword_hits(topic_id: str, text: str) -> List[str]:
    return [word for word in _TOPIC_KEYWORDS.get(topic_id, ()) if word and word in text][:5]


def _relation_risk(energy_meta: Mapping[str, Any], topic_id: str) -> tuple[float, List[str]]:
    rows = energy_meta.get("relation_dynamics_summary") if isinstance(energy_meta.get("relation_dynamics_summary"), list) else []
    if not rows:
        return 0.0, []
    risk = 0.0
    evidence: List[str] = []
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        stability_delta = _safe_float(row.get("stability_delta_ratio"), 0.0)
        label = _clean_label(row.get("label"))
        axis = _clean_label(row.get("energy_axis"))
        if stability_delta < -0.05:
            factor = 0.05 if topic_id in {"relationship", "career"} else 0.03
            risk += min(0.16, abs(stability_delta) * factor * 5)
            if label:
                evidence.append(f"关系动力：{label}{axis or '承压'}")
    return min(0.22, risk), evidence[:2]


def _macro_summary(topic_id: str, score: float, risk: float, top_gods: Sequence[str], hits: Sequence[str]) -> str:
    label = _TOPIC_LABELS.get(topic_id, topic_id)
    god_text = " / ".join(top_gods[:2]) if top_gods else "结构信号"
    if topic_id == "personality":
        if "伤官" in top_gods or "食神" in top_gods:
            base = "表达、输出和主观判断更容易成为性格外显面"
        elif "正印" in top_gods or "偏印" in top_gods:
            base = "学习、防御和内在秩序更容易成为性格底色"
        elif "比肩" in top_gods or "劫财" in top_gods:
            base = "自我边界、竞争感和同辈牵引更明显"
        else:
            base = "性格画像仍需结合更多专题信号"
        return f"{label}：{base}；主信号 {god_text}。"
    state = "可展开" if score >= 0.66 and risk < 0.38 else "需审慎推进" if score >= 0.52 else "处在潜伏观察位"
    if risk >= 0.42:
        state = "机会与波动并存"
    hit_text = f"；命中 {' / '.join(hits[:2])}" if hits else ""
    return f"{label}：当前主题{state}，主信号 {god_text}{hit_text}。"


def build_macro_theme_contract() -> Dict[str, Any]:
    return {
        "contract": "v17.macro.theme.v1",
        "is_l3_macro_topic": True,
        "authority_bridge_mode": "read_only",
        "final_meta_keys": list(FINAL_MACRO_THEME_KEYS),
        "temporary_meta_keys": list(TEMPORARY_MACRO_THEME_KEYS),
        "topics": list(_TOPIC_LABELS.keys()),
        "constraints": [
            "宏观象属于 L3 主题层，只读 L0/L1/L2/authority/optional topic，不回写物理能量或参数。",
            "财富、事业、感情、性格输出的是主题激活度、机会/风险和证据链，不是无条件吉凶定论。",
            "LLM 只能基于 macro_theme 组织表达，不得自行改写置信度、来源或系统体用裁决。",
        ],
    }


@dataclass(frozen=True)
class MacroTopicResult:
    id: str
    label: str
    score: float
    confidence: float
    risk: float
    stance: str
    summary: str
    source_gods: Sequence[str] = field(default_factory=tuple)
    source_topics: Sequence[str] = field(default_factory=tuple)
    evidence: Sequence[str] = field(default_factory=tuple)
    opportunities: Sequence[str] = field(default_factory=tuple)
    risks: Sequence[str] = field(default_factory=tuple)
    llm_focus: Sequence[str] = field(default_factory=tuple)

    def to_meta(self) -> Dict[str, Any]:
        return {
            "id": _clean_label(self.id),
            "label": _clean_label(self.label),
            "score": round(_clamp(self.score), 3),
            "confidence": round(_clamp(self.confidence), 3),
            "risk": round(_clamp(self.risk), 3),
            "stance": _clean_label(self.stance),
            "summary": _clean_label(self.summary, limit=260),
            "source_gods": _clean_str_list(self.source_gods, limit=8),
            "source_topics": _clean_str_list(self.source_topics, limit=8),
            "evidence": _clean_str_list(self.evidence, limit=6),
            "opportunities": _clean_str_list(self.opportunities, limit=5),
            "risks": _clean_str_list(self.risks, limit=5),
            "llm_focus": _clean_str_list(self.llm_focus, limit=5),
        }


@dataclass(frozen=True)
class MacroThemeResult:
    confidence: float = 0.0
    topics: Sequence[MacroTopicResult] = field(default_factory=tuple)
    source_topics: Sequence[str] = field(default_factory=tuple)
    prompt_digest: str = ""

    def to_meta(self) -> Dict[str, Any]:
        topic_rows = [topic.to_meta() for topic in self.topics if topic.id]
        ranked = sorted(topic_rows, key=lambda row: float(row.get("score") or 0.0), reverse=True)
        return {
            "contract": "v17.macro.theme.v1",
            "is_l3_macro_topic": True,
            "confidence": round(_clamp(self.confidence), 3),
            "topics": topic_rows,
            "top_topics": [str(row.get("id") or "") for row in ranked[:3] if str(row.get("id") or "")],
            "prompt_digest": _clean_label(self.prompt_digest, limit=360),
            "source_topics": _clean_str_list(self.source_topics, limit=10),
            "llm_guidance": [
                "先按 macro_theme 的主题激活度排序，再写财富、事业、感情、性格。",
                "每个宏观象必须保留证据、机会、风险和条件，不得把弱主题写成强断语。",
                "命理师覆盖格局/用忌时，宏观象叙事应跟随本次覆盖前提，但不改系统主题分数。",
            ],
            "learning_hooks": [
                "macro.wealth.calibration",
                "macro.career.calibration",
                "macro.relationship.calibration",
                "macro.personality.calibration",
            ],
            "guardrails": build_macro_theme_contract()["constraints"],
        }


def normalize_macro_theme_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, MacroThemeResult):
        return value.to_meta()
    if not isinstance(value, dict):
        return {}
    topics: List[MacroTopicResult] = []
    raw_topics = value.get("topics") if isinstance(value.get("topics"), list) else []
    for row in raw_topics:
        if not isinstance(row, Mapping):
            continue
        topic_id = _clean_label(row.get("id"))
        if not topic_id:
            continue
        topics.append(
            MacroTopicResult(
                id=topic_id,
                label=_clean_label(row.get("label")) or _TOPIC_LABELS.get(topic_id, topic_id),
                score=_safe_float(row.get("score"), 0.0),
                confidence=_safe_float(row.get("confidence"), 0.0),
                risk=_safe_float(row.get("risk"), 0.0),
                stance=_clean_label(row.get("stance")),
                summary=_clean_label(row.get("summary"), limit=260),
                source_gods=tuple(_clean_str_list(row.get("source_gods"), limit=8)),
                source_topics=tuple(_clean_str_list(row.get("source_topics"), limit=8)),
                evidence=tuple(_clean_str_list(row.get("evidence"), limit=6)),
                opportunities=tuple(_clean_str_list(row.get("opportunities"), limit=5)),
                risks=tuple(_clean_str_list(row.get("risks"), limit=5)),
                llm_focus=tuple(_clean_str_list(row.get("llm_focus"), limit=5)),
            )
        )
    return MacroThemeResult(
        confidence=_safe_float(value.get("confidence"), 0.0),
        topics=tuple(topics),
        source_topics=tuple(_clean_str_list(value.get("source_topics"), limit=10)),
        prompt_digest=_clean_label(value.get("prompt_digest"), limit=360),
    ).to_meta()


def resolve_macro_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    energy_meta = pt.get("energy_meta") if isinstance(pt.get("energy_meta"), dict) else {}
    scores = read_runtime_scores(pt)
    if not scores:
        scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    if not scores:
        return {"macro_theme": {}, "confidence": 0.0}

    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    blind = normalize_blind_theme_meta(meta.get("blind_theme"))
    climate = normalize_climate_theme_meta(meta.get("climate_theme"))
    xiangfa = normalize_xiangfa_theme_meta(meta.get("xiangfa_theme"))
    gender = _clean_label(pt.get("gender") or meta.get("gender")).lower()
    use_gods = _authority_gods(authority, "use_gods", "god_of_use")
    taboo_gods = _authority_gods(authority, "taboo_gods", "god_of_taboo")
    text = _facts_text(pt, meta)
    shares = _cluster_shares(scores)
    total = sum(max(0.0, _safe_float(value, 0.0)) for value in scores.values()) or 1.0
    source_topics = ["ten_gods"]
    if authority:
        source_topics.append("authority")
    if blind:
        source_topics.append("blind")
    if climate:
        source_topics.append("climate")
    if xiangfa:
        source_topics.append("xiangfa")
    if energy_meta.get("relation_dynamics_summary"):
        source_topics.append("relation_dynamics")

    topic_results: List[MacroTopicResult] = []
    for topic_id, label in _TOPIC_LABELS.items():
        topic_gods = _topic_gods(topic_id, gender)
        raw_share = _share(scores, topic_gods, total)
        if topic_id == "wealth":
            raw_share = shares["wealth"] * 0.72 + shares["output"] * 0.38
        elif topic_id == "career":
            raw_share = shares["officer"] * 0.7 + shares["seal"] * 0.24 + shares["wealth"] * 0.16
        elif topic_id == "relationship":
            raw_share = shares["wealth"] * 0.38 + shares["officer"] * 0.38 + shares["peer"] * 0.12
        elif topic_id == "personality":
            raw_share = max(shares.values()) * 0.82 + shares["peer"] * 0.14 + shares["output"] * 0.12

        score = 0.26 + raw_share * 1.42
        risk = 0.08
        evidence: List[str] = []
        opportunities: List[str] = []
        risks: List[str] = []
        topic_sources = ["ten_gods"]
        topic_score_rows = sorted(
            ((god, _safe_float(scores.get(god), 0.0)) for god in topic_gods),
            key=lambda item: item[1],
            reverse=True,
        )
        top_gods = [god for god, value in topic_score_rows if value > 0.0][:4]
        if top_gods:
            evidence.append("十神主信号：" + " / ".join(f"{god}{_safe_float(scores.get(god), 0.0):.1f}" for god in top_gods[:3]))

        use_hits = [god for god in top_gods if god in use_gods]
        taboo_hits = [god for god in top_gods if god in taboo_gods]
        if use_hits:
            score += 0.08 + 0.025 * min(2, len(use_hits))
            topic_sources.append("authority")
            opportunities.append("体用顺侧：" + " / ".join(use_hits[:2]))
        if taboo_hits:
            risk += 0.12 + 0.035 * min(2, len(taboo_hits))
            topic_sources.append("authority")
            risks.append("体用代价：" + " / ".join(taboo_hits[:2]))

        hits = _keyword_hits(topic_id, text)
        if hits:
            score += min(0.12, 0.035 * len(hits))
            topic_sources.append("plugin_collision")
            evidence.append("插件碰撞：" + " / ".join(hits[:3]))

        blind_route = _clean_label(blind.get("primary_route")) if blind else ""
        if blind_route and any(word in blind_route for word in _TOPIC_KEYWORDS.get(topic_id, ())):
            score += 0.06
            topic_sources.append("blind")
            opportunities.append("盲派主线：" + blind_route)

        xiangfa_frames = _clean_str_list(xiangfa.get("event_framing"), limit=4) if xiangfa else []
        xiangfa_hits = [frame for frame in xiangfa_frames if any(word in frame for word in _TOPIC_KEYWORDS.get(topic_id, ()))]
        if xiangfa_hits:
            score += 0.04
            topic_sources.append("xiangfa")
            evidence.append("象法事件：" + xiangfa_hits[0])

        climate_tension = _safe_float(climate.get("climate_tension"), 0.0) if climate else 0.0
        climate_state = _clean_label(climate.get("state")) if climate else ""
        if climate_state:
            topic_sources.append("climate")
            evidence.append("环境条件：" + climate_state)
        if climate_tension > 0.65:
            risk += 0.06
            risks.append(f"调候张力{climate_tension:.2f}")

        relation_extra_risk, relation_evidence = _relation_risk(energy_meta, topic_id)
        if relation_evidence:
            topic_sources.append("relation_dynamics")
            evidence.extend(relation_evidence)
            risk += relation_extra_risk

        score = _clamp(score, 0.08, 0.96)
        risk = _clamp(risk, 0.02, 0.86)
        if topic_id == "personality":
            score = _clamp(max(score, 0.52), 0.08, 0.96)
        stance = "active" if score >= 0.66 and risk < 0.38 else "volatile" if score >= 0.58 and risk >= 0.38 else "watch" if score >= 0.5 else "latent"
        source_count = len(set(topic_sources))
        confidence = _clamp(0.38 + source_count * 0.075 + score * 0.15 - risk * 0.06, 0.35, 0.91)
        summary = _macro_summary(topic_id, score, risk, top_gods, hits)
        if score >= 0.55 and not opportunities:
            opportunities.append("主题可作为叙事主线观察")
        if risk >= 0.36 and not risks:
            risks.append("机会伴随结构波动，需带条件解释")

        topic_results.append(
            MacroTopicResult(
                id=topic_id,
                label=label,
                score=score,
                confidence=confidence,
                risk=risk,
                stance=stance,
                summary=summary,
                source_gods=tuple(top_gods[:4]),
                source_topics=tuple(dict.fromkeys(topic_sources)),
                evidence=tuple(evidence[:6]),
                opportunities=tuple(opportunities[:4]),
                risks=tuple(risks[:4]),
                llm_focus=(
                    f"{label}先写{stance}",
                    "必须同时给出机会和风险",
                    "不得脱离体用、格局和运行条件",
                ),
            )
        )

    topic_results.sort(key=lambda row: row.score, reverse=True)
    confidence = _clamp(sum(topic.confidence for topic in topic_results) / max(1, len(topic_results)), 0.0, 0.92)
    digest = "；".join(f"{topic.label}{round(topic.score * 100)}%/{topic.stance}" for topic in topic_results[:4])
    theme = MacroThemeResult(
        confidence=confidence,
        topics=tuple(topic_results),
        source_topics=tuple(dict.fromkeys(source_topics)),
        prompt_digest=digest,
    ).to_meta()
    return {
        "contract": theme["contract"],
        "confidence": theme["confidence"],
        "macro_theme": theme,
    }
