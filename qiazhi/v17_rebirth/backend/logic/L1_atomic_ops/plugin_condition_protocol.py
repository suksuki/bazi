from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    ELEMENT_CYCLE,
    STEM_ELEMENT,
    _collect_root_strengths,
    _parse_gz,
)


_NATAL_PILLARS = {"year", "month", "day", "hour"}
_RUNTIME_PILLARS = {"luck", "flow"}


BRANCH_RELATION_FAMILIES = {
    "liu_chong",
    "liu_hai",
    "liu_po",
    "liu_he",
    "ban_he",
    "an_he",
    "san_he",
    "sanhui",
    "san_hui",
    "muku",
    "sanxing",
}

STEM_RELATION_FAMILIES = {"stem_fusion"}
HIDDEN_RELATION_FAMILIES = {"hidden_bridge", "hidden_root"}
CROSS_LAYER_FAMILIES = {"status_machine", "officer_hurt", "owl_food", "blade_clash", "risk_matrix"}


def _normalize_members(row: Any) -> set[str]:
    if not isinstance(row, dict):
        return set()
    out: set[str] = set()
    for key in ("pair", "group", "branches", "matched_branches", "branch"):
        values = row.get(key)
        if isinstance(values, (list, tuple, set)):
            out.update({str(v).strip() for v in values if str(v).strip()})
        elif str(values or "").strip():
            out.add(str(values).strip())
    return out


def detect_interaction_layer(
    row: Mapping[str, Any] | None,
    *,
    relation_family: str | None = None,
    member_key: str | None = None,
) -> str:
    if row and isinstance(row, Mapping):
        explicit = str(row.get("interaction_layer") or "").strip().lower()
        if explicit in {"stem", "branch", "hidden", "cross_layer", "unknown"}:
            return explicit

    family = str(relation_family or "").strip().lower()
    if family in STEM_RELATION_FAMILIES:
        return "stem"
    if family in HIDDEN_RELATION_FAMILIES:
        return "hidden"
    if family in CROSS_LAYER_FAMILIES:
        return "cross_layer"

    if family in BRANCH_RELATION_FAMILIES or (member_key in {"pair", "group", "branches", "matched_branches", "branch"}):
        return "branch"

    return "unknown"


def infer_manifestation_state(
    rows: List[Dict[str, Any]],
    *,
    relation_family: str,
    member_set: Iterable[str] | None = None,
    origin_types: Iterable[str] | None = None,
) -> str:
    family = str(relation_family or "").strip().lower()
    candidates = [row for row in rows if isinstance(row, dict)]
    if not candidates:
        return "latent"

    normalized_origin = {str(item).strip().lower() for item in (origin_types or []) if str(item or "").strip()}
    if any(item == "natal" for item in normalized_origin):
        return "manifested"

    if family in {"stem_fusion", "stem_interlock"}:
        for row in candidates:
            mode = str(row.get("mode") or "").strip().lower()
            manifestation_mode = str(row.get("manifestation_mode") or "").strip()
            if mode == "transformed":
                return "manifested" if manifestation_mode != "暗化" else "supported"
            if mode == "activated":
                return "supported"

    if family in BRANCH_RELATION_FAMILIES:
        # 地支关系默认先成立于显化链路，若同时有完整成员或高强度才算强显化。
        target_members = {str(item).strip() for item in (member_set or []) if str(item).strip()}
        has_full_membership = bool(target_members)
        for row in candidates:
            members = _normalize_members(row)
            if has_full_membership and target_members.issubset(members):
                return "manifested"
            strength = float(
                row.get("strength")
                if row.get("strength") is not None
                else row.get("stress")
                if row.get("stress") is not None
                else row.get("pivot_factor")
                if row.get("pivot_factor") is not None
                else 0.0
            )
            if strength >= 1.1:
                return "manifested"
            if strength >= 0.95:
                return "supported"
            if any(str(item).strip() in members for item in {"巳", "酉", "丑", "申", "子"}):
                return "supported"

    return "supported"



def detect_relation_origin_type(pillars: List[str] | None) -> str:
    scoped = {str(x).strip().lower() for x in (pillars or []) if str(x).strip()}
    has_natal = bool(scoped & _NATAL_PILLARS)
    has_luck = "luck" in scoped
    has_flow = "flow" in scoped
    if has_natal and has_luck and has_flow:
        return "mixed"
    if has_natal and has_luck:
        return "luck_background"
    if has_natal and has_flow:
        return "flow_trigger"
    if has_luck and has_flow:
        return "runtime_pair"
    if has_luck:
        return "luck_only"
    if has_flow:
        return "flow_only"
    if has_natal:
        return "natal"
    return "unknown"


def relation_origin_multiplier(origin_type: str) -> float:
    value = str(origin_type or "").strip().lower()
    if value == "mixed":
        return 0.94
    if value == "luck_background":
        return 0.98
    if value == "luck_only":
        return 0.98
    if value == "natal":
        return 1.0
    if value == "runtime_pair":
        return 0.95
    if value == "flow_trigger":
        return 0.9
    if value == "flow_only":
        return 0.78
    return 0.85


def choose_dominant_origin_type(origins: Iterable[str]) -> str:
    cleaned = [str(item or "").strip().lower() for item in origins if str(item or "").strip()]
    if not cleaned:
        return "unknown"
    return sorted(cleaned, key=lambda item: relation_origin_multiplier(item), reverse=True)[0]


def collect_origin_types_from_rows(
    rows: List[Dict[str, Any]],
    *,
    member_key: str,
    members: Iterable[str] | None = None,
) -> List[str]:
    member_filter = {str(item) for item in (members or []) if str(item).strip()}
    origins: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_members = {str(item) for item in (row.get(member_key) or []) if str(item).strip()}
        if member_filter and not (member_filter & row_members):
            continue
        origin = str(row.get("origin_type") or "").strip()
        if origin:
            origins.append(origin)
            continue
        pillars = row.get("pillars") if isinstance(row.get("pillars"), list) else []
        inferred = detect_relation_origin_type(pillars)
        if inferred != "unknown":
            origins.append(inferred)
    return origins


def summarize_relation_conditions(
    *,
    relation_family: str,
    pair_or_group: List[str],
    interaction_v2: Mapping[str, Any],
) -> Dict[str, Any]:
    liu_chong = interaction_v2.get("liu_chong") if isinstance(interaction_v2.get("liu_chong"), list) else []
    liu_hai = interaction_v2.get("liu_hai") if isinstance(interaction_v2.get("liu_hai"), list) else []
    liu_po = interaction_v2.get("liu_po") if isinstance(interaction_v2.get("liu_po"), list) else []
    sanxing = interaction_v2.get("sanxing") if isinstance(interaction_v2.get("sanxing"), list) else []

    relation_members = {str(x) for x in pair_or_group if str(x).strip()}

    origin_type = "unknown"
    for rows, key in ((interaction_v2.get(relation_family), "pair"),):
        _ = rows, key

    def _touches(rows: List[Dict[str, Any]], key: str) -> bool:
        for row in rows:
            if not isinstance(row, dict):
                continue
            members = {str(x) for x in (row.get(key) or []) if str(x).strip()}
            if relation_members & members:
                return True
        return False

    blockers: List[str] = []
    if relation_family in {"sanhe", "sanhui", "liuhe", "stem_fusion", "muku"} and _touches(liu_chong, "pair"):
        blockers.append("liu_chong")
    if relation_family in {"sanhe", "sanhui", "liuhe"} and _touches(liu_hai, "pair"):
        blockers.append("liu_hai")
    if relation_family in {"sanhe", "sanhui", "liuhe"} and _touches(liu_po, "pair"):
        blockers.append("liu_po")
    if relation_family in {"sanhe", "sanhui", "muku"} and _touches(sanxing, "branches"):
        blockers.append("sanxing")

    origin_candidates: List[str] = []
    relation_keys = {
        "liu_chong": ("liu_chong", "pair"),
        "liuhai": ("liu_hai", "pair"),
        "liu_po": ("liu_po", "pair"),
        "liuhe": ("liu_he", "pair"),
        "sanhe": ("san_he", "group"),
        "sanhui": ("san_hui", "group"),
        "san_hui": ("san_hui", "group"),
        "banhe": ("ban_he", "pair"),
        "muku": ("liu_chong", "pair"),
    }
    v2_key, member_key = relation_keys.get(relation_family, ("", "pair"))
    rows = interaction_v2.get(v2_key) if v2_key and isinstance(interaction_v2.get(v2_key), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        members = {str(x) for x in (row.get(member_key) or []) if str(x).strip()}
        if relation_members and not (relation_members & members):
            continue
        origin_candidates.append(detect_relation_origin_type(row.get("pillars") if isinstance(row.get("pillars"), list) else []))
    if origin_candidates:
        origin_type = choose_dominant_origin_type(origin_candidates)

    return {
        "relation_family": relation_family,
        "relation_members": sorted(relation_members),
        "blockers": blockers,
        "condition_state": "supported" if not blockers else "contested",
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def summarize_stem_fusion_conditions(case: Mapping[str, Any]) -> Dict[str, Any]:
    month_supports = bool(case.get("month_stem_supports"))
    branch_hua_ratio = float(case.get("branch_root_ratio") or case.get("branch_hua_ratio") or 0.0)
    mode = str(case.get("mode") or "").strip()
    manifestation_mode = str(case.get("manifestation_mode") or ("明化" if month_supports else "暗化")).strip()
    support_origin = str(case.get("support_origin") or "").strip()
    visible_support_strength = float(case.get("visible_support_strength") or (1.0 if month_supports else 0.0))
    support_score = float(
        case.get("effective_support_score")
        if case.get("effective_support_score") is not None
        else case.get("support_score")
        if case.get("support_score") is not None
        else visible_support_strength * 0.62 + branch_hua_ratio * 0.38
    )
    branch_disturbance_score = float(case.get("branch_disturbance_score") or 0.0)
    stem_competition_score = float(case.get("stem_competition_score") or 0.0)
    interference_score = float(case.get("interference_score") or 0.0)
    if mode == "transformed":
        if support_origin == "month_visible" or month_supports:
            trigger = "month_support"
        elif support_origin == "day_visible":
            trigger = "day_support"
        elif support_origin.endswith("_visible"):
            trigger = "visible_support"
        elif manifestation_mode == "暗化":
            trigger = "latent_root_support"
        else:
            trigger = "branch_support"
    else:
        trigger = "interference_blocked" if interference_score >= 0.24 and support_score >= 0.18 else "insufficient_support"
    return {
        "condition_state": "formed" if mode == "transformed" else "stuck",
        "condition_trigger": trigger,
        "month_supports": month_supports,
        "branch_hua_ratio": round(branch_hua_ratio, 4),
        "branch_root_ratio": round(branch_hua_ratio, 4),
        "manifestation_mode": manifestation_mode,
        "support_origin": support_origin,
        "visible_support_strength": round(visible_support_strength, 4),
        "support_score": round(max(0.0, min(1.0, support_score)), 4),
        "branch_disturbance_score": round(max(0.0, min(1.0, branch_disturbance_score)), 4),
        "stem_competition_score": round(max(0.0, min(1.0, stem_competition_score)), 4),
        "interference_score": round(max(0.0, min(1.0, interference_score)), 4),
        "origin_type": detect_relation_origin_type(case.get("pillars") if isinstance(case.get("pillars"), list) else []),
        "origin_multiplier": relation_origin_multiplier(
            detect_relation_origin_type(case.get("pillars") if isinstance(case.get("pillars"), list) else [])
        ),
    }


def relation_effect_multiplier(condition_state: str) -> float:
    state = str(condition_state or "").strip().lower()
    if state in {"supported", "formed"}:
        return 1.0
    if state in {"contested", "stuck"}:
        return 0.65
    return 0.85


def _day_master_from_tensor(physics_tensor: Mapping[str, Any]) -> str:
    stem = str(physics_tensor.get("day_master_stem") or "").strip()
    if stem:
        return stem
    fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(fp.get("day") or "").strip()
    return day_gz[0] if len(day_gz) >= 2 else ""


def _god_to_element(day_master: str) -> Dict[str, str]:
    dm_el = STEM_ELEMENT.get(day_master, "")
    if dm_el not in ELEMENT_CYCLE:
        return {}
    dm_idx = ELEMENT_CYCLE.index(dm_el)
    mapping: Dict[str, str] = {}
    for idx in range(5):
        el = ELEMENT_CYCLE[(dm_idx + idx) % 5]
        gods = (
            ["比肩", "劫财"] if idx == 0 else
            ["食神", "伤官"] if idx == 1 else
            ["正财", "偏财"] if idx == 2 else
            ["正官", "七杀"] if idx == 3 else
            ["正印", "偏印"]
        )
        for god in gods:
            mapping[god] = el
    return mapping


def _visible_stems_with_scope(physics_tensor: Mapping[str, Any]) -> List[Dict[str, str]]:
    fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    rows = [
        ("year", str(fp.get("year") or "").strip()),
        ("month", str(fp.get("month") or "").strip()),
        ("day", str(fp.get("day") or "").strip()),
        ("hour", str(fp.get("hour") or "").strip()),
        ("luck", str(physics_tensor.get("luck_pillar") or "").strip()),
        ("flow", str(physics_tensor.get("flow_pillar") or "").strip()),
    ]
    visible: List[Dict[str, str]] = []
    for scope, gz in rows:
        stem, branch = _parse_gz(gz)
        if stem:
            visible.append({"scope": scope, "stem": stem, "branch": branch})
    return visible


def build_static_basis(
    *,
    physics_tensor: Mapping[str, Any],
    target_god: str,
    relation_family: str,
    relation_members: Iterable[str] | None = None,
) -> Dict[str, Any]:
    scores = physics_tensor.get("ten_gods_base_l0")
    if not isinstance(scores, dict):
        scores = physics_tensor.get("ten_gods_absolute")
    scores = scores if isinstance(scores, dict) else {}
    runtime_scores = physics_tensor.get("ten_gods_runtime") if isinstance(physics_tensor.get("ten_gods_runtime"), dict) else {}
    meta = physics_tensor.get("energy_meta") if isinstance(physics_tensor.get("energy_meta"), dict) else {}
    day_master = _day_master_from_tensor(physics_tensor)
    god_to_el = _god_to_element(day_master)
    target_element = str(god_to_el.get(target_god) or "")

    fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    luck_pillar = str(physics_tensor.get("luck_pillar") or "").strip()
    flow_pillar = str(physics_tensor.get("flow_pillar") or "").strip()
    root_strengths = _collect_root_strengths(fp, luck_pillar, flow_pillar) if fp else {}

    visible_rows = _visible_stems_with_scope(physics_tensor)
    visible_support = [
        row for row in visible_rows
        if target_element and STEM_ELEMENT.get(str(row.get("stem") or "")) == target_element
    ]
    member_set = {str(item) for item in (relation_members or []) if str(item).strip()}
    relation_support_rows = []
    if member_set:
        for row in visible_rows:
            if str(row.get("branch") or "") in member_set:
                relation_support_rows.append(row)

    top_scores = sorted(
        ((str(god), float(value or 0.0)) for god, value in scores.items() if str(god).strip()),
        key=lambda item: (-item[1], item[0]),
    )[:4]
    structural_bonuses = meta.get("structural_bonuses") if isinstance(meta.get("structural_bonuses"), list) else []
    related_bonus = next(
        (
            row for row in structural_bonuses
            if isinstance(row, dict) and member_set and member_set <= {str(x) for x in (row.get("group") or []) if str(x).strip()}
        ),
        None,
    )

    return {
        "relation_family": relation_family,
        "target_god": target_god,
        "target_element": target_element,
        "base_score": round(float(scores.get(target_god, 0.0) or 0.0), 2),
        "runtime_score": round(float(runtime_scores.get(target_god, scores.get(target_god, 0.0)) or 0.0), 2),
        "month_command_god": str(meta.get("month_command_god") or ""),
        "top_l0_gods": [{"god": god, "score": round(score, 2)} for god, score in top_scores],
        "visible_support": [
            {
                "scope": str(row.get("scope") or ""),
                "stem": str(row.get("stem") or ""),
                "branch": str(row.get("branch") or ""),
            }
            for row in visible_support
        ],
        "relation_support_rows": [
            {
                "scope": str(row.get("scope") or ""),
                "stem": str(row.get("stem") or ""),
                "branch": str(row.get("branch") or ""),
            }
            for row in relation_support_rows
        ],
        "root_strengths": {
            stem: round(float(root_strengths.get(stem, 0.0) or 0.0), 3)
            for stem in sorted(root_strengths.keys())
            if target_element and STEM_ELEMENT.get(stem) == target_element
        },
        "related_structural_bonus": dict(related_bonus) if isinstance(related_bonus, dict) else None,
    }
