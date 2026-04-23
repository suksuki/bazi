from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import normalize_blind_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import normalize_climate_theme_meta


FINAL_XIANGFA_THEME_KEYS: List[str] = [
    "contract",
    "is_optional_topic",
    "confidence",
    "semantic_mapping",
    "evidence",
    "narrative_hint",
    "event_framing",
    "prompt_digest",
    "source_topics",
    "authority_bridge_mode",
]

TEMPORARY_XIANGFA_THEME_KEYS: List[str] = [
    "xiangfa_candidate_labels",
    "xiangfa_raw_notes",
    "xiangfa_solver_traces",
]


def _clean_label(value: Any) -> str:
    return str(value or "").strip()


def _clean_str_list(values: Sequence[Any] | None) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    seen: set[str] = set()
    rows: List[str] = []
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
    return rows


def build_xiangfa_theme_contract() -> Dict[str, Any]:
    return {
        "contract": "v17.xiangfa.theme.v1",
        "is_optional_topic": True,
        "authority_bridge_mode": "disabled",
        "final_meta_keys": list(FINAL_XIANGFA_THEME_KEYS),
        "temporary_meta_keys": list(TEMPORARY_XIANGFA_THEME_KEYS),
        "constraints": [
            "象法第一阶段只输出 semantic mapping / evidence / narrative hint / event framing。",
            "不得修改五行能量、十神结构，也不进入 bias 或 authority 主分。",
        ],
    }


@dataclass(frozen=True)
class XiangfaThemeResult:
    confidence: float = 0.0
    semantic_mapping: Sequence[str] = field(default_factory=tuple)
    evidence: Sequence[str] = field(default_factory=tuple)
    narrative_hint: Sequence[str] = field(default_factory=tuple)
    event_framing: Sequence[str] = field(default_factory=tuple)
    prompt_digest: str = ""
    source_topics: Sequence[str] = field(default_factory=tuple)

    def to_meta(self) -> Dict[str, Any]:
        return {
            "contract": "v17.xiangfa.theme.v1",
            "is_optional_topic": True,
            "confidence": round(float(self.confidence), 3),
            "semantic_mapping": _clean_str_list(self.semantic_mapping),
            "evidence": _clean_str_list(self.evidence),
            "narrative_hint": _clean_str_list(self.narrative_hint),
            "event_framing": _clean_str_list(self.event_framing),
            "prompt_digest": _clean_label(self.prompt_digest),
            "source_topics": _clean_str_list(self.source_topics),
            "authority_bridge_mode": "disabled",
        }


def normalize_xiangfa_theme_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, XiangfaThemeResult):
        return value.to_meta()
    if not isinstance(value, dict):
        return {}
    return XiangfaThemeResult(
        confidence=float(value.get("confidence") or 0.0),
        semantic_mapping=tuple(_clean_str_list(value.get("semantic_mapping"))),
        evidence=tuple(_clean_str_list(value.get("evidence"))),
        narrative_hint=tuple(_clean_str_list(value.get("narrative_hint"))),
        event_framing=tuple(_clean_str_list(value.get("event_framing"))),
        prompt_digest=_clean_label(value.get("prompt_digest")),
        source_topics=tuple(_clean_str_list(value.get("source_topics"))),
    ).to_meta()


def resolve_xiangfa_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    energy_meta = physics_tensor.get("energy_meta") if isinstance(physics_tensor.get("energy_meta"), dict) else {}
    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    blind = normalize_blind_theme_meta(meta.get("blind_theme"))
    climate = normalize_climate_theme_meta(meta.get("climate_theme"))
    relation_formation = (
        energy_meta.get("relation_formation_summary")
        if isinstance(energy_meta.get("relation_formation_summary"), list)
        else []
    )
    relation_dynamics = (
        energy_meta.get("relation_dynamics_summary")
        if isinstance(energy_meta.get("relation_dynamics_summary"), list)
        else []
    )

    use_gods = _clean_str_list(authority.get("use_gods"))
    taboo_gods = _clean_str_list(authority.get("taboo_gods"))
    source_topics: List[str] = []
    semantic_mapping: List[str] = []
    evidence: List[str] = []
    narrative_hint: List[str] = []
    event_framing: List[str] = []

    if use_gods or taboo_gods:
        source_topics.append("authority")
        if use_gods:
            semantic_mapping.append("体用主轴偏向「" + " / ".join(use_gods[:2]) + "」")
        if taboo_gods:
            semantic_mapping.append("当前主要代价落在「" + " / ".join(taboo_gods[:2]) + "」")
        if use_gods and taboo_gods:
            event_framing.append("主用与代价并存，适合叙述为“机会伴随成本”")
            narrative_hint.append("当前叙事不宜只讲吉凶，应同时描述收益和代价。")
        evidence.append("体用裁决来源：" + " / ".join(use_gods[:2] + taboo_gods[:2]))

    if blind:
        source_topics.append("blind")
        route = _clean_label(blind.get("primary_route"))
        inside_roles = [god for god, role in (blind.get("house_roles") or {}).items() if _clean_label(role) == "inside"]
        outside_roles = [god for god, role in (blind.get("house_roles") or {}).items() if _clean_label(role) == "outside"]
        if route:
            semantic_mapping.append(f"盲派主线为「{route}」")
            evidence.append("盲派体用：" + route)
        if outside_roles and inside_roles:
            semantic_mapping.append("家外「" + " / ".join(outside_roles[:2]) + "」牵动家内「" + " / ".join(inside_roles[:2]) + "」")
            event_framing.append("可叙述为外部动作对内部秩序/结果的穿透")

    if climate:
        source_topics.append("climate")
        state = _clean_label(climate.get("state"))
        favored = _clean_str_list(climate.get("favored_gods"))
        strained = _clean_str_list(climate.get("strained_gods"))
        if state:
            semantic_mapping.append(f"调候落点为「{state}」")
            evidence.append("调候状态：" + state)
        if favored:
            semantic_mapping.append("调候更顺势的十神为「" + " / ".join(favored[:2]) + "」")
        if strained:
            semantic_mapping.append("调候更承压的十神为「" + " / ".join(strained[:2]) + "」")
        if state or favored or strained:
            narrative_hint.append("叙事要带上环境条件，不宜把结构判断写成无条件结论。")

    if relation_formation:
        top = relation_formation[0] if isinstance(relation_formation[0], dict) else {}
        label = _clean_label(top.get("formation_label"))
        percent = float(top.get("formation_percent") or 0.0)
        status = _clean_label(top.get("status"))
        if label:
            source_topics.append("relation_formation")
            evidence.append(f"成局参考：{label} {percent:.1f}%")
            event_framing.append(f"{label}{status or '成局观察'}")

    if relation_dynamics:
        top = relation_dynamics[0] if isinstance(relation_dynamics[0], dict) else {}
        label = _clean_label(top.get("label"))
        axis = _clean_label(top.get("energy_axis"))
        if label:
            source_topics.append("relation_dynamics")
            evidence.append(f"关系动力学：{label} {axis}")
            if axis:
                semantic_mapping.append(f"当前更像「{axis}」而非静态平衡")
                event_framing.append(f"{label} 触发 {axis} 语义")

    confidence = min(
        0.88,
        0.36
        + (0.12 if use_gods or taboo_gods else 0.0)
        + (0.12 if blind else 0.0)
        + (0.12 if climate else 0.0)
        + (0.10 if relation_formation else 0.0)
        + (0.10 if relation_dynamics else 0.0),
    )
    if not semantic_mapping and not evidence and not narrative_hint and not event_framing:
        return {"xiangfa_theme": {}, "confidence": 0.0}

    prompt_digest = "；".join(
        part
        for part in [
            semantic_mapping[0] if semantic_mapping else "",
            event_framing[0] if event_framing else "",
            narrative_hint[0] if narrative_hint else "",
        ]
        if part
    )
    theme = XiangfaThemeResult(
        confidence=confidence,
        semantic_mapping=tuple(semantic_mapping[:4]),
        evidence=tuple(evidence[:4]),
        narrative_hint=tuple(narrative_hint[:3]),
        event_framing=tuple(event_framing[:4]),
        prompt_digest=prompt_digest,
        source_topics=tuple(source_topics[:6]),
    ).to_meta()
    return {
        "contract": theme["contract"],
        "confidence": theme["confidence"],
        "xiangfa_theme": theme,
    }
