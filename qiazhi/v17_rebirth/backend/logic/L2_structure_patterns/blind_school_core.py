from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
)
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor


FINAL_BLIND_THEME_KEYS: List[str] = [
    "contract",
    "is_optional_topic",
    "confidence",
    "target_god",
    "primary_route",
    "body_mode",
    "body_candidates",
    "use_candidates",
    "taboo_candidates",
    "house_roles",
    "runtime_switches",
    "narrative_focus",
    "prompt_digest",
    "authority_bridge_mode",
    "relation_families",
    "origin_type",
]

FINAL_BLIND_BIAS_KEYS: List[str] = [
    "contract",
    "authority_bridge_mode",
    "primary_route",
    "body_mode",
    "origin_type",
    "use_bias",
    "taboo_bias",
    "inside_roles",
    "outside_roles",
    "bridge_roles",
    "runtime_switches",
    "narrative_hint",
    "summary",
]

TEMPORARY_BLIND_THEME_KEYS: List[str] = [
    "blind_route_scores_raw",
    "blind_graph_edges",
    "blind_candidate_traces",
    "blind_runtime_probes",
    "blind_debug_flags",
    "blind_temporary_house_roles",
    "blind_solver_notes",
]

_RELATION_MEMBER_KEYS: Dict[str, str] = {
    "liu_chong": "pair",
    "liu_hai": "pair",
    "liu_po": "pair",
    "liuhe": "pair",
    "anhe": "pair",
    "ban_he": "pair",
    "san_he": "group",
    "san_hui": "group",
    "sanxing": "branches",
}

_RELATION_LABELS: Dict[str, str] = {
    "liu_chong": "六冲",
    "liu_hai": "六害",
    "liu_po": "六破",
    "liuhe": "六合",
    "anhe": "暗合",
    "ban_he": "半合",
    "san_he": "三合",
    "san_hui": "三会",
    "sanxing": "三刑",
}

_BLIND_ORIGIN_PRIORITY: Tuple[str, ...] = (
    "liu_chong",
    "sanxing",
    "san_he",
    "san_hui",
    "ban_he",
    "liuhe",
    "anhe",
    "liu_hai",
    "liu_po",
)

_FOOD_GODS = ("食神", "伤官")
_WEALTH_GODS = ("正财", "偏财")
_OFFICER_GODS = ("正官", "七杀")
_SEAL_GODS = ("正印", "偏印")
_PEER_GODS = ("比肩", "劫财")

_BLIND_GOD_ALIASES: Dict[str, Tuple[str, ...]] = {
    "食伤": ("食神", "伤官"),
    "食神": ("食神",),
    "伤官": ("伤官",),
    "财": ("正财", "偏财"),
    "财星": ("正财", "偏财"),
    "正财": ("正财",),
    "偏财": ("偏财",),
    "官杀": ("正官", "七杀"),
    "官": ("正官",),
    "杀": ("七杀",),
    "正官": ("正官",),
    "七杀": ("七杀",),
    "印": ("正印", "偏印"),
    "印星": ("正印", "偏印"),
    "强印": ("正印", "偏印"),
    "印绶": ("正印", "偏印"),
    "正印": ("正印",),
    "偏印": ("偏印",),
    "比劫": ("比肩", "劫财"),
    "比肩": ("比肩",),
    "劫财": ("劫财",),
}


def _clean_label(value: Any) -> str:
    return str(value or "").strip()


def _clean_str_list(values: Sequence[Any] | None) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        out.append(label)
    return out


def _clean_role_map(values: Dict[str, Any] | None) -> Dict[str, str]:
    if not isinstance(values, dict):
        return {}
    out: Dict[str, str] = {}
    for key, value in values.items():
        god = _clean_label(key)
        role = _clean_label(value)
        if not god or not role:
            continue
        out[god] = role
    return out


def _expand_blind_gods(values: Sequence[Any] | None) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in _clean_str_list(values):
        members = _BLIND_GOD_ALIASES.get(item, (item,))
        for god in members:
            name = _clean_label(god)
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
    return out


def _interaction_v2(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2")
    return iv2 if isinstance(iv2, dict) else {}


def _present_relation_rows(iv2: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    rows_by_family: Dict[str, List[Dict[str, Any]]] = {}
    for family, _member_key in _RELATION_MEMBER_KEYS.items():
        raw = iv2.get(family)
        if not isinstance(raw, list):
            continue
        rows = [row for row in raw if isinstance(row, dict)]
        if rows:
            rows_by_family[family] = rows
    return rows_by_family


def _origin_type_from_rows(rows_by_family: Dict[str, List[Dict[str, Any]]]) -> str:
    origin_types: List[str] = []
    families = [family for family in _BLIND_ORIGIN_PRIORITY if family in rows_by_family]
    if not families:
        families = list(rows_by_family.keys())
    for family in families[:1]:
        member_key = _RELATION_MEMBER_KEYS.get(family)
        if not member_key:
            continue
        origin_types.extend(collect_origin_types_from_rows(rows_by_family.get(family) or [], member_key=member_key))
    if not origin_types:
        for family, rows in rows_by_family.items():
            member_key = _RELATION_MEMBER_KEYS.get(family)
            if not member_key:
                continue
            origin_types.extend(collect_origin_types_from_rows(rows, member_key=member_key))
    return choose_dominant_origin_type(origin_types)


def _cluster_strength(scores: Dict[str, float], gods: Sequence[str]) -> float:
    return sum(float(scores.get(god) or 0.0) for god in gods)


def _sorted_members(scores: Dict[str, float], gods: Sequence[str]) -> List[str]:
    rows = [(god, float(scores.get(god) or 0.0)) for god in gods if float(scores.get(god) or 0.0) > 0.0]
    rows.sort(key=lambda item: item[1], reverse=True)
    return [god for god, _value in rows]


def _route_relation_bonus(route_id: str, families: Sequence[str]) -> float:
    present = set(_clean_str_list(families))
    bonus = 0.0
    if route_id in {"food_control_officer", "officer_seal_cycle"}:
        if "san_he" in present or "san_hui" in present:
            bonus += 0.08
        if "ban_he" in present or "liuhe" in present or "anhe" in present:
            bonus += 0.04
    if route_id in {"food_generate_wealth", "wealth_officer_flow"}:
        if "san_he" in present or "san_hui" in present:
            bonus += 0.05
        if "ban_he" in present or "liuhe" in present:
            bonus += 0.04
    if "liu_chong" in present:
        bonus += 0.03
    if "sanxing" in present:
        bonus += 0.02
    return bonus


def _origin_bonus(origin_type: str) -> float:
    origin = _clean_label(origin_type)
    if origin == "natal":
        return 0.0
    if origin in {"luck", "flow"}:
        return 0.05
    return 0.07


def _route_score_rows(scores: Dict[str, float], families: Sequence[str], origin_type: str) -> List[Tuple[str, str, float, List[str]]]:
    total = max(sum(float(value or 0.0) for value in scores.values()), 1.0)
    food = _cluster_strength(scores, _FOOD_GODS) / total
    wealth = _cluster_strength(scores, _WEALTH_GODS) / total
    officer = _cluster_strength(scores, _OFFICER_GODS) / total
    seal = _cluster_strength(scores, _SEAL_GODS) / total
    peer = _cluster_strength(scores, _PEER_GODS) / total
    bonus = _origin_bonus(origin_type)

    rows: List[Tuple[str, str, float, List[str]]] = []
    food_control = food * 0.92 + officer * 0.56 + _route_relation_bonus("food_control_officer", families) + bonus * 0.4
    if food >= 0.16 and officer >= 0.08:
        rows.append(("food_control_officer", "食伤制杀", min(0.98, food_control), ["食伤外放", "官杀受制"]))

    food_wealth = food * 0.88 + wealth * 0.54 + _route_relation_bonus("food_generate_wealth", families) + bonus * 0.72
    if food >= 0.14 and wealth >= 0.06:
        rows.append(("food_generate_wealth", "食伤生财", min(0.98, food_wealth), ["输出换财", "结果落地"]))

    officer_seal_label = "杀印相生" if float(scores.get("七杀") or 0.0) >= float(scores.get("正官") or 0.0) else "官印相生"
    officer_seal = officer * 0.8 + seal * 0.6 + _route_relation_bonus("officer_seal_cycle", families) + bonus * 0.35
    if officer >= 0.1 and seal >= 0.06:
        rows.append(("officer_seal_cycle", officer_seal_label, min(0.98, officer_seal), ["规则承接", "印绶回路"]))

    wealth_officer = wealth * 0.68 + officer * 0.52 + _route_relation_bonus("wealth_officer_flow", families) + bonus * 0.25
    if wealth >= 0.08 and officer >= 0.08:
        rows.append(("wealth_officer_flow", "财官同流", min(0.98, wealth_officer), ["财承规则", "家内成事"]))

    if not rows and scores:
        top_god = max(scores.items(), key=lambda item: float(item[1] or 0.0))[0]
        top_score = min(0.72, max(0.32, float(scores.get(top_god) or 0.0) / total))
        rows.append(("single_god_anchor", f"{top_god}主轴", top_score, ["单轴显化"]))
    rows.sort(key=lambda item: item[2], reverse=True)
    return rows


def _route_house_roles(route_id: str, members: Dict[str, List[str]]) -> Dict[str, str]:
    roles: Dict[str, str] = {}
    food = members["food"]
    wealth = members["wealth"]
    officer = members["officer"]
    seal = members["seal"]
    peer = members["peer"]

    if route_id == "food_control_officer":
        for god in food:
            roles[god] = "outside"
        for god in officer[:2]:
            roles[god] = "inside"
        for god in wealth[:1]:
            roles.setdefault(god, "inside")
        for god in seal[:1]:
            roles.setdefault(god, "bridge")
    elif route_id == "food_generate_wealth":
        for god in food:
            roles[god] = "outside"
        for god in wealth[:2]:
            roles[god] = "inside"
        for god in peer[:1]:
            roles.setdefault(god, "bridge")
        for god in officer[:1]:
            roles.setdefault(god, "inside")
    elif route_id == "officer_seal_cycle":
        for god in officer[:2]:
            roles[god] = "inside"
        for god in seal[:2]:
            roles.setdefault(god, "bridge")
        for god in food[:1]:
            roles.setdefault(god, "outside")
        for god in wealth[:1]:
            roles.setdefault(god, "inside")
    elif route_id == "wealth_officer_flow":
        for god in wealth[:2]:
            roles[god] = "inside"
        for god in officer[:2]:
            roles.setdefault(god, "inside")
        for god in food[:1]:
            roles.setdefault(god, "outside")
        for god in seal[:1]:
            roles.setdefault(god, "bridge")
    else:
        for god in food[:1]:
            roles[god] = "outside"
        for god in wealth[:1]:
            roles.setdefault(god, "inside")
        for god in officer[:1]:
            roles.setdefault(god, "inside")
        for god in seal[:1]:
            roles.setdefault(god, "bridge")
    return roles


def _route_use_taboo(route_id: str, members: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
    food = members["food"]
    wealth = members["wealth"]
    officer = members["officer"]
    seal = members["seal"]
    peer = members["peer"]
    if route_id == "food_control_officer":
        use = food[:2] + officer[:1]
        taboo = seal[:1] + peer[:1]
    elif route_id == "food_generate_wealth":
        use = food[:2] + wealth[:2]
        taboo = seal[:1] + officer[:1]
    elif route_id == "officer_seal_cycle":
        use = officer[:1] + seal[:2]
        taboo = food[:2]
    elif route_id == "wealth_officer_flow":
        use = wealth[:2] + officer[:1]
        taboo = food[:1] + seal[:1]
    else:
        use = food[:1] + wealth[:1] + officer[:1]
        taboo = seal[:1]
    return _clean_str_list(use), _clean_str_list(taboo)


def _body_mode(
    candidates: Sequence[BlindBodyCandidate],
    families: Sequence[str],
    origin_type: str,
) -> str:
    if not candidates:
        return "single_body"
    if len(candidates) >= 2:
        gap = float(candidates[0].score) - float(candidates[1].score)
        if float(candidates[1].score) >= 0.32 and gap <= 0.08:
            if origin_type != "natal":
                return "shifted_body"
            return "dual_body"
    if origin_type != "natal" or "liu_chong" in families or "sanxing" in families:
        return "disturbed_body"
    return "single_body"


def _origin_label(origin_type: str) -> str:
    origin = _clean_label(origin_type)
    if origin == "luck":
        return "大运"
    if origin == "flow":
        return "流年"
    if origin in {"runtime", "mixed", "luck_flow", "runtime_cascade"}:
        return "运流"
    return "原局"


def _runtime_switches(
    candidates: Sequence[BlindBodyCandidate],
    body_mode: str,
    origin_type: str,
    relation_families: Sequence[str],
) -> List[str]:
    switches: List[str] = []
    origin_label = _origin_label(origin_type)
    if body_mode == "shifted_body" and len(candidates) >= 2:
        switches.append(f"{origin_label}中{candidates[1].label}抢权")
    elif body_mode == "disturbed_body" and candidates:
        switches.append(f"{origin_label}中{candidates[0].label}扰体未换体")
    elif body_mode == "dual_body" and len(candidates) >= 2:
        switches.append(f"{candidates[0].label}与{candidates[1].label}并行")
    if "liu_chong" in relation_families:
        switches.append("冲起结构，先动后判")
    if "sanxing" in relation_families:
        switches.append("刑压加重，先看代价")
    return _clean_str_list(switches)


def _narrative_focus(
    primary_route: str,
    body_mode: str,
    relation_families: Sequence[str],
) -> List[str]:
    lines: List[str] = []
    if primary_route == "食伤制杀":
        lines.append("先看做功，再看规则是否被压住。")
    elif primary_route == "食伤生财":
        lines.append("先看输出如何变现，再看结果是否入库。")
    elif primary_route in {"官印相生", "杀印相生"}:
        lines.append("先看家内承接，再看印是否回护结构。")
    elif primary_route == "财官同流":
        lines.append("先看家内承接与规则协同。")
    else:
        lines.append("先看主结构，再看断事入口。")
    if body_mode == "disturbed_body":
        lines.append("当前体被扰动，主线未必失效，但稳定性下降。")
    elif body_mode == "shifted_body":
        lines.append("当前存在主线抢权，需并行看旧体与新体。")
    if "liu_chong" in relation_families:
        lines.append("冲象入场，事件触发速度更快。")
    elif "san_he" in relation_families or "liuhe" in relation_families or "ban_he" in relation_families:
        lines.append("合势入场，更多看绑定与资源归并。")
    return _clean_str_list(lines)


@dataclass(frozen=True)
class BlindBodyCandidate:
    route_id: str
    label: str
    score: float
    status: str = "candidate"
    relation_families: Sequence[str] = field(default_factory=tuple)
    notes: Sequence[str] = field(default_factory=tuple)

    def to_meta(self) -> Dict[str, Any]:
        return {
            "route_id": _clean_label(self.route_id),
            "label": _clean_label(self.label),
            "score": round(float(self.score or 0.0), 4),
            "status": _clean_label(self.status) or "candidate",
            "relation_families": _clean_str_list(self.relation_families),
            "notes": _clean_str_list(self.notes),
        }


@dataclass(frozen=True)
class BlindThemeResult:
    primary_route: str = ""
    body_mode: str = "single_body"
    confidence: float = 0.0
    target_god: str = ""
    relation_families: Sequence[str] = field(default_factory=tuple)
    origin_type: str = "natal"
    body_candidates: Sequence[BlindBodyCandidate] = field(default_factory=tuple)
    use_candidates: Sequence[str] = field(default_factory=tuple)
    taboo_candidates: Sequence[str] = field(default_factory=tuple)
    house_roles: Dict[str, str] = field(default_factory=dict)
    runtime_switches: Sequence[str] = field(default_factory=tuple)
    narrative_focus: Sequence[str] = field(default_factory=tuple)
    prompt_digest: str = ""
    authority_bridge_mode: str = "bias_only"

    def to_meta(self) -> Dict[str, Any]:
        candidates = [candidate.to_meta() for candidate in self.body_candidates if isinstance(candidate, BlindBodyCandidate)]
        digest = _clean_label(self.prompt_digest)
        role_map = _clean_role_map(self.house_roles)
        if not digest:
            fragments: List[str] = []
            if self.primary_route:
                fragments.append(f"主线{self.primary_route}")
            if self.body_mode:
                fragments.append(f"体态{self.body_mode}")
            inside = [god for god, role in role_map.items() if role == "inside"]
            outside = [god for god, role in role_map.items() if role == "outside"]
            if inside:
                fragments.append("家里" + "/".join(inside[:2]))
            if outside:
                fragments.append("家外" + "/".join(outside[:2]))
            switches = _clean_str_list(self.runtime_switches)
            if switches:
                fragments.append("换挡" + "；".join(switches[:2]))
            digest = "；".join(fragments)
        return {
            "contract": "v17.blind.theme.v1",
            "is_optional_topic": True,
            "confidence": round(float(self.confidence or 0.0), 4),
            "target_god": _clean_label(self.target_god),
            "primary_route": _clean_label(self.primary_route),
            "body_mode": _clean_label(self.body_mode) or "single_body",
            "body_candidates": candidates,
            "use_candidates": _clean_str_list(self.use_candidates),
            "taboo_candidates": _clean_str_list(self.taboo_candidates),
            "house_roles": role_map,
            "runtime_switches": _clean_str_list(self.runtime_switches),
            "narrative_focus": _clean_str_list(self.narrative_focus),
            "prompt_digest": digest,
            "authority_bridge_mode": _clean_label(self.authority_bridge_mode) or "bias_only",
            "relation_families": _clean_str_list(self.relation_families),
            "origin_type": _clean_label(self.origin_type) or "natal",
        }


def build_blind_theme_contract() -> Dict[str, Any]:
    return {
        "contract": "v17.blind.theme.v1",
        "is_optional_topic": True,
        "coexists_with": ["ziping", "pattern_specializations", "risk_matrix"],
        "final_meta_keys": list(FINAL_BLIND_THEME_KEYS),
        "final_bias_keys": list(FINAL_BLIND_BIAS_KEYS),
        "temporary_meta_keys": list(TEMPORARY_BLIND_THEME_KEYS),
        "authority_bridge_mode": "bias_only",
        "prompt_channels": ["blind_topic_contract", "blind_topic_summary"],
    }


def build_blind_bias_protocol(theme_value: Any) -> Dict[str, Any]:
    theme = normalize_blind_theme_meta(theme_value)
    if not theme:
        return {}

    confidence = max(0.0, min(0.98, float(theme.get("confidence") or 0.0)))
    body_mode = _clean_label(theme.get("body_mode")) or "single_body"
    origin_type = _clean_label(theme.get("origin_type")) or "natal"
    primary_route = _clean_label(theme.get("primary_route"))
    authority_bridge_mode = _clean_label(theme.get("authority_bridge_mode")) or "bias_only"
    house_roles = _clean_role_map(theme.get("house_roles"))
    runtime_switches = _clean_str_list(theme.get("runtime_switches"))

    use_candidates = _expand_blind_gods(theme.get("use_candidates"))
    taboo_candidates = _expand_blind_gods(theme.get("taboo_candidates"))

    body_mode_factor = {
        "single_body": 1.0,
        "dual_body": 0.9,
        "disturbed_body": 0.82,
        "shifted_body": 0.76,
    }.get(body_mode, 0.88)
    origin_factor = {
        "natal": 1.0,
        "luck": 0.92,
        "flow": 0.88,
        "runtime": 0.86,
        "mixed": 0.84,
    }.get(origin_type, 0.86)

    use_base = (0.08 + confidence * 0.12) * body_mode_factor * origin_factor
    taboo_base = (0.07 + confidence * 0.11) * body_mode_factor * origin_factor
    weights = (1.0, 0.72, 0.54, 0.42)

    use_bias: Dict[str, float] = {}
    taboo_bias: Dict[str, float] = {}
    for idx, god in enumerate(use_candidates[:4]):
        use_bias[god] = round(use_base * weights[idx], 3)
    for idx, god in enumerate(taboo_candidates[:4]):
        taboo_bias[god] = round(taboo_base * weights[idx], 3)

    inside_roles = [god for god, role in house_roles.items() if role == "inside"]
    outside_roles = [god for god, role in house_roles.items() if role == "outside"]
    bridge_roles = [god for god, role in house_roles.items() if role == "bridge"]
    narrative_hint = str(theme.get("prompt_digest") or "").strip()

    return {
        "contract": "v17.blind.bias.v1",
        "authority_bridge_mode": authority_bridge_mode,
        "primary_route": primary_route,
        "body_mode": body_mode,
        "origin_type": origin_type,
        "use_bias": {god: value for god, value in use_bias.items() if value > 0.0},
        "taboo_bias": {god: value for god, value in taboo_bias.items() if value > 0.0},
        "inside_roles": inside_roles,
        "outside_roles": outside_roles,
        "bridge_roles": bridge_roles,
        "runtime_switches": runtime_switches,
        "narrative_hint": narrative_hint,
        "summary": {
            "confidence": round(confidence, 4),
            "use_total": round(sum(use_bias.values()), 3),
            "taboo_total": round(sum(taboo_bias.values()), 3),
            "use_count": len(use_bias),
            "taboo_count": len(taboo_bias),
            "switch_count": len(runtime_switches),
            "inside_count": len(inside_roles),
            "outside_count": len(outside_roles),
            "bridge_count": len(bridge_roles),
        },
    }


def resolve_blind_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    scores = deity_scores_from_tensor(pt)
    if not scores:
        return {}
    iv2 = _interaction_v2(pt)
    rows_by_family = _present_relation_rows(iv2)
    relation_families = list(rows_by_family.keys())
    origin_type = _origin_type_from_rows(rows_by_family)
    route_rows = _route_score_rows(scores, relation_families, origin_type)
    members = {
        "food": _sorted_members(scores, _FOOD_GODS),
        "wealth": _sorted_members(scores, _WEALTH_GODS),
        "officer": _sorted_members(scores, _OFFICER_GODS),
        "seal": _sorted_members(scores, _SEAL_GODS),
        "peer": _sorted_members(scores, _PEER_GODS),
    }
    candidates = [
        BlindBodyCandidate(
            route_id=route_id,
            label=label,
            score=score,
            status="primary" if idx == 0 else "candidate",
            relation_families=tuple(relation_families),
            notes=tuple(notes),
        )
        for idx, (route_id, label, score, notes) in enumerate(route_rows)
    ]
    body_mode = _body_mode(candidates, relation_families, origin_type)
    primary = candidates[0] if candidates else BlindBodyCandidate("single_god_anchor", "单轴显化", 0.0)
    use_candidates, taboo_candidates = _route_use_taboo(primary.route_id, members)
    target_god = use_candidates[0] if use_candidates else max(scores.items(), key=lambda item: float(item[1] or 0.0))[0]
    theme = BlindThemeResult(
        primary_route=primary.label,
        body_mode=body_mode,
        confidence=max(0.0, min(0.98, float(primary.score))),
        target_god=target_god,
        relation_families=tuple(relation_families),
        origin_type=origin_type,
        body_candidates=tuple(candidates[:4]),
        use_candidates=tuple(use_candidates),
        taboo_candidates=tuple(taboo_candidates),
        house_roles=_route_house_roles(primary.route_id, members),
        runtime_switches=tuple(_runtime_switches(candidates, body_mode, origin_type, relation_families)),
        narrative_focus=tuple(_narrative_focus(primary.label, body_mode, relation_families)),
        authority_bridge_mode="bias_only",
    )
    meta = theme.to_meta()
    interaction_layer = "branch" if relation_families else "unknown"
    if "liu_chong" in relation_families or "sanxing" in relation_families:
        manifestation_state = "contested"
    elif relation_families:
        manifestation_state = "supported"
    else:
        manifestation_state = "manifested"
    return {
        "blind_theme": meta,
        "scores": scores,
        "relation_families": relation_families,
        "origin_type": origin_type,
        "target_god": target_god,
        "top_god": max(scores.items(), key=lambda item: float(item[1] or 0.0))[0],
        "interaction_layer": interaction_layer,
        "manifestation_state": manifestation_state,
        "match_ratio_hint": round(max(0.42, min(0.94, 0.45 + float(meta.get("confidence") or 0.0) * 0.42 + len(relation_families) * 0.02)), 3),
        "relation_labels": [_RELATION_LABELS.get(name, name) for name in relation_families],
    }


def normalize_blind_theme_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, BlindThemeResult):
        return value.to_meta()
    if not isinstance(value, dict):
        return {}
    payload = BlindThemeResult(
        primary_route=_clean_label(value.get("primary_route")),
        body_mode=_clean_label(value.get("body_mode")) or "single_body",
        confidence=float(value.get("confidence") or 0.0),
        target_god=_clean_label(value.get("target_god")),
        relation_families=tuple(_clean_str_list(value.get("relation_families"))),
        origin_type=_clean_label(value.get("origin_type")) or "natal",
        body_candidates=tuple(
            BlindBodyCandidate(
                route_id=_clean_label(item.get("route_id")),
                label=_clean_label(item.get("label")),
                score=float(item.get("score") or 0.0),
                status=_clean_label(item.get("status")) or "candidate",
                relation_families=tuple(_clean_str_list(item.get("relation_families"))),
                notes=tuple(_clean_str_list(item.get("notes"))),
            )
            for item in (value.get("body_candidates") or [])
            if isinstance(item, dict)
        ),
        use_candidates=tuple(_clean_str_list(value.get("use_candidates"))),
        taboo_candidates=tuple(_clean_str_list(value.get("taboo_candidates"))),
        house_roles=_clean_role_map(value.get("house_roles")),
        runtime_switches=tuple(_clean_str_list(value.get("runtime_switches"))),
        narrative_focus=tuple(_clean_str_list(value.get("narrative_focus"))),
        prompt_digest=_clean_label(value.get("prompt_digest")),
        authority_bridge_mode=_clean_label(value.get("authority_bridge_mode")) or "bias_only",
    )
    meta = payload.to_meta()
    if isinstance(value.get("contract"), str) and value.get("contract"):
        meta["contract"] = str(value.get("contract"))
    return meta
