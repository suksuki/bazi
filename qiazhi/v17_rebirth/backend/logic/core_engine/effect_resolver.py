from __future__ import annotations

from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.core_engine.work_path_engine import WorkPath


_PATH_ROLE_BONUS = {
    "promote": 1.02,
    "restrain": 0.98,
    "bridge": 1.05,
    "transfer": 1.0,
    "intercept": 0.92,
    "unknown": 1.0,
}

_FAMILY_BONUS = {
    "convergence": 1.04,
    "transmuter": 1.06,
    "bridge": 1.05,
    "conflict": 0.98,
    "drain": 0.95,
    "risk": 0.9,
    "intercept": 0.9,
    "dynamic_work": 1.0,
    "static": 1.0,
}

_CONTEST_FAMILIES = {"risk", "conflict", "intercept", "drain"}
_BRIDGE_FAMILIES = {"bridge", "convergence", "transmuter"}


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _to_god(value: Any) -> str:
    return str(value or "").strip()


def _normalize_gods(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, tuple):
        values = list(values)
    if isinstance(values, set):
        values = sorted(values)
    if isinstance(values, list):
        out: List[str] = []
        for item in values:
            god = _to_god(item)
            if god and god not in out:
                out.append(god)
        return out
    if isinstance(values, str):
        value = values.strip()
        if value:
            return [value]
    god = _to_god(values)
    return [god] if god else []


def _path_weight(path: WorkPath) -> float:
    family = str(path.path_family or "dynamic_work").strip().lower()
    role = str(path.path_role or "unknown").strip().lower()
    family_weight = _FAMILY_BONUS.get(family, 1.0)
    role_weight = _PATH_ROLE_BONUS.get(role, 1.0)
    return family_weight * role_weight


def _path_style(path: WorkPath) -> str:
    family = str(path.path_family or "").strip().lower()
    role = str(path.path_role or "").strip().lower()
    if family in _BRIDGE_FAMILIES or role == "bridge":
        return "bridge"
    if family in _CONTEST_FAMILIES or role in {"restrain", "intercept", "transfer"}:
        return "contest"
    return "synergy"


def _evidence(path: WorkPath) -> Dict[str, Any]:
    raw = path.evidence
    return raw if isinstance(raw, dict) else {}


def _counterpart_gods(path: WorkPath) -> List[str]:
    e = _evidence(path)
    target = _to_god(path.target_god)
    out = _normalize_gods(e.get("counterpart_gods"))
    if not out:
        out = _normalize_gods(e.get("targets"))
    if not out:
        out = _normalize_gods(e.get("participants"))
    if target and out:
        out = [god for god in out if god and god != target]
    return out


def _build_contest_edges(paths: List[WorkPath], known_gods: set[str]) -> Dict[Tuple[str, str], float]:
    edges: Dict[Tuple[str, str], float] = {}
    for path in paths:
        target = _to_god(path.target_god)
        if not target:
            continue
        style = _path_style(path)
        if style == "bridge":
            base_factor = 0.2
        elif style == "contest":
            base_factor = 1.0
        else:
            continue

        base = abs(_safe_float(path.net_effect, 0.0))
        if base <= 0.0:
            continue

        for counterpart in _counterpart_gods(path):
            if not counterpart or counterpart not in known_gods or counterpart == target:
                continue
            key = tuple(sorted((target, counterpart)))
            add = base * _path_weight(path) * base_factor
            edges[key] = edges.get(key, 0.0) + add
    return edges


def _resolve_scores(
    scores: Dict[str, Dict[str, float]],
    contest_pressure: Dict[str, float],
    release_pressure: Dict[str, float],
) -> None:
    for god, row in scores.items():
        raw_benefit = _safe_float(row.get("raw_benefit"), 0.0)
        raw_harm = _safe_float(row.get("raw_harm"), 0.0)
        raw_total = raw_benefit + raw_harm

        contest = _safe_float(contest_pressure.get(god), 0.0)
        release = _safe_float(release_pressure.get(god), 0.0)

        contest_ratio = contest / max(raw_total, 1.0)
        release_ratio = release / max(raw_total, 1.0)

        # 约束阻尼：高竞争路径会降低单边极值，但不让数值归零。
        contest_damp = 1.0 / (1.0 + min(2.2, contest_ratio * 1.5))
        # 通关/桥接路径可局部释放约束压力，提升最终稳定效应。
        release_boost = 1.0 + min(0.35, release_ratio * 0.8)

        resolved_net = (raw_benefit - raw_harm) * contest_damp * release_boost
        if raw_total > 0.0:
            if resolved_net >= 0:
                resolved_net += raw_total * 0.03
            else:
                resolved_net -= raw_total * 0.03

        row["contest_pressure"] = round(contest, 4)
        row["release_pressure"] = round(release, 4)
        row["resolved_utility"] = round(resolved_net, 4)
        row["net_utility"] = round(
            _safe_float(raw_benefit) * contest_damp - _safe_float(raw_harm) * (contest_damp * 0.92),
            4,
        )


def resolve_effect_scores(paths: List[WorkPath]) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {}
    for path in paths:
        target = _to_god(path.target_god)
        if not target:
            continue

        bucket = scores.setdefault(
            target,
            {
                "benefit_score": 0.0,
                "harm_score": 0.0,
                "raw_benefit": 0.0,
                "raw_harm": 0.0,
                "activation_score": 0.0,
                "stability_score": 0.0,
                "contest_pressure": 0.0,
                "release_pressure": 0.0,
                "contest_pairs": [],
                "path_style": "synergy",
                "net_utility": 0.0,
                "resolved_utility": 0.0,
            },
        )

        path_weight = _path_weight(path)
        style = _path_style(path)
        if style == "bridge":
            bucket["path_style"] = "bridge"
        elif style == "contest":
            bucket["path_style"] = "contest"
        else:
            bucket["path_style"] = "synergy"

        weighted = _safe_float(path.net_effect, 0.0) * path_weight
        benefit = max(weighted, 0.0)
        harm = (max(-weighted, 0.0) + max(path.loss, 0.0)) / max(1.0, path_weight)
        bucket["raw_benefit"] += benefit
        bucket["raw_harm"] += harm
        bucket["benefit_score"] += benefit
        bucket["harm_score"] += harm
        bucket["activation_score"] = max(bucket["activation_score"], _safe_float(path.activation, 0.0) * path_weight)
        bucket["stability_score"] = max(bucket["stability_score"], _safe_float(path.stability, 0.0) * path_weight)

    known_gods = set(scores.keys())
    contest_edges = _build_contest_edges(paths, known_gods)
    contest_pressure = {god: 0.0 for god in known_gods}
    release_pressure = {god: 0.0 for god in known_gods}

    for (left, right), intensity in contest_edges.items():
        contest_pressure[left] = contest_pressure.get(left, 0.0) + intensity
        contest_pressure[right] = contest_pressure.get(right, 0.0) + intensity
        scores.setdefault(left, {
            "benefit_score": 0.0,
            "harm_score": 0.0,
            "raw_benefit": 0.0,
            "raw_harm": 0.0,
            "activation_score": 0.0,
            "stability_score": 0.0,
            "contest_pressure": 0.0,
            "release_pressure": 0.0,
            "contest_pairs": [],
            "path_style": "synergy",
            "net_utility": 0.0,
            "resolved_utility": 0.0,
        })
        scores.setdefault(right, {
            "benefit_score": 0.0,
            "harm_score": 0.0,
            "raw_benefit": 0.0,
            "raw_harm": 0.0,
            "activation_score": 0.0,
            "stability_score": 0.0,
            "contest_pressure": 0.0,
            "release_pressure": 0.0,
            "contest_pairs": [],
            "path_style": "synergy",
            "net_utility": 0.0,
            "resolved_utility": 0.0,
        })
        scores[left]["contest_pairs"].append(f"{left}-{right}")
        scores[right]["contest_pairs"].append(f"{left}-{right}")

    for path in paths:
        target = _to_god(path.target_god)
        if not target:
            continue
        if _path_style(path) == "bridge":
            bridge_weight = _path_weight(path)
            release_pressure[target] = release_pressure.get(target, 0.0) + abs(_safe_float(path.net_effect, 0.0)) * bridge_weight

    _resolve_scores(scores, contest_pressure, release_pressure)

    for row in scores.values():
        row["contest_pairs"] = sorted(set(_normalize_gods(row.get("contest_pairs", []))))
        row["contest_weight"] = round(_safe_float(row.get("contest_pressure", 0.0)), 4)
        row["release_weight"] = round(_safe_float(row.get("release_pressure", 0.0)), 4)
        row["benefit_score"] = round(_safe_float(row.get("benefit_score")), 4)
        row["harm_score"] = round(_safe_float(row.get("harm_score")), 4)
        row["raw_benefit"] = round(_safe_float(row.get("raw_benefit")), 4)
        row["raw_harm"] = round(_safe_float(row.get("raw_harm")), 4)
        row["activation_score"] = round(_safe_float(row.get("activation_score")), 4)
        row["stability_score"] = round(_safe_float(row.get("stability_score")), 4)
        row["net_utility"] = round(_safe_float(row.get("net_utility")), 4)
        row["resolved_utility"] = round(_safe_float(row.get("resolved_utility")), 4)

    return scores


def pick_god_candidates(effect_scores: Dict[str, Dict[str, float]]) -> Dict[str, object]:
    valid_rows = {
        god: row
        for god, row in effect_scores.items()
        if god and isinstance(row, dict) and not god.startswith("_")
    }

    def _use_candidate_score(row: Dict[str, float]) -> float:
        resolved_flux = _safe_float(row.get("resolved_utility_flux", row.get("resolved_utility", row.get("net_utility", 0.0))), 0.0)
        stability = _safe_float(row.get("stability_score"), 0.0)
        outbound_support = _safe_float(row.get("flux_out_support"), 0.0)
        reinforce_load = _safe_float(row.get("flux_reinforce_load"), 0.0)
        tension_load = _safe_float(row.get("flux_tension_load"), 0.0)
        contest_weight = _safe_float(row.get("contest_weight"), 0.0)
        return (
            resolved_flux
            + stability * 0.18
            + outbound_support * 0.16
            + reinforce_load * 0.36
            - tension_load * 0.44
            - contest_weight * 0.10
        )

    def _taboo_candidate_score(row: Dict[str, float]) -> float:
        harm = _safe_float(row.get("harm_score"), 0.0)
        flux_harm = _safe_float(row.get("flux_harm"), 0.0)
        outbound_resist = _safe_float(row.get("flux_out_resist"), 0.0)
        tension_load = _safe_float(row.get("flux_tension_load"), 0.0)
        contest_weight = _safe_float(row.get("contest_weight"), 0.0)
        reinforce_load = _safe_float(row.get("flux_reinforce_load"), 0.0)
        return (
            harm
            + flux_harm * 0.42
            + outbound_resist * 0.18
            + tension_load * 0.52
            + contest_weight * 0.14
            - reinforce_load * 0.12
        )

    ranked_use = sorted(valid_rows.items(), key=lambda item: _use_candidate_score(item[1]), reverse=True)
    ranked_taboo = sorted(valid_rows.items(), key=lambda item: _taboo_candidate_score(item[1]), reverse=True)

    use_candidates = [
        {
            "god": god,
            "score": round(_use_candidate_score(row), 4),
            "resolved_flux": round(_safe_float(row.get("resolved_utility_flux", row.get("resolved_utility", 0.0))), 4),
            "tension_load": round(_safe_float(row.get("flux_tension_load"), 0.0), 4),
            "reinforce_load": round(_safe_float(row.get("flux_reinforce_load"), 0.0), 4),
        }
        for god, row in ranked_use[:3]
        if _use_candidate_score(row) > 0
    ]
    taboo_candidates = [
        {
            "god": god,
            "score": round(_taboo_candidate_score(row), 4),
            "harm": round(_safe_float(row.get("harm_score"), 0.0), 4),
            "flux_harm": round(_safe_float(row.get("flux_harm"), 0.0), 4),
            "tension_load": round(_safe_float(row.get("flux_tension_load"), 0.0), 4),
        }
        for god, row in ranked_taboo[:3]
        if _taboo_candidate_score(row) > 0
    ]
    dual_role = [
        {
            "god": god,
            "benefit": row.get("benefit_score", 0.0),
            "risk": row.get("harm_score", 0.0),
            "raw_benefit": row.get("raw_benefit", 0.0),
            "raw_harm": row.get("raw_harm", 0.0),
            "contest_weight": row.get("contest_weight", 0.0),
            "release_weight": row.get("release_weight", 0.0),
            "tension_load": row.get("flux_tension_load", 0.0),
            "reinforce_load": row.get("flux_reinforce_load", 0.0),
        }
        for god, row in valid_rows.items()
        if (
            row.get("benefit_score", 0.0) > 0 and row.get("harm_score", 0.0) > 0
        ) or _safe_float(row.get("flux_tension_load"), 0.0) > 0.12
    ]

    return {
        "use_candidates": use_candidates,
        "taboo_candidates": taboo_candidates,
        "dual_role_candidates": sorted(dual_role, key=lambda item: max(item["benefit"], item["risk"]), reverse=True)[:3],
    }
