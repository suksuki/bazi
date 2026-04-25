from __future__ import annotations

from typing import Any


CHOICE_CANDIDATES_CONTRACT = "v17.practitioner.choice_candidates.v1"
OVERRIDE_CONTEXT_CONTRACT = "v17.practitioner.override_context.v1"


def build_practitioner_choice_candidates(
    *,
    raw_physics: dict[str, Any],
    god_ring_authority: dict[str, Any],
    plugin_rows: list[dict[str, Any]],
    plugin_claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return system-computed candidates that practitioners may choose for one reading."""

    pt = raw_physics if isinstance(raw_physics, dict) else {}
    authority = god_ring_authority if isinstance(god_ring_authority, dict) else {}
    claims = plugin_claims if isinstance(plugin_claims, list) else []
    rows = plugin_rows if isinstance(plugin_rows, list) else []

    selections = {
        "pattern": _pattern_candidates([*claims, *rows]),
        "use_god": _god_candidates(
            kind="use_god",
            source="core_use_candidates",
            rows=authority.get("core_use_candidates"),
            selected_names=_clean_names(authority.get("god_of_use")),
            authority_confidence=_safe_float(authority.get("confidence")),
        ),
        "taboo_god": _god_candidates(
            kind="taboo_god",
            source="core_taboo_candidates",
            rows=authority.get("core_taboo_candidates"),
            selected_names=_clean_names(authority.get("god_of_taboo")),
            authority_confidence=_safe_float(authority.get("confidence")),
        ),
    }
    return {
        "contract": CHOICE_CANDIDATES_CONTRACT,
        "generated_by": "system_runtime",
        "physics_fingerprint": str(pt.get("physics_fingerprint") or ""),
        "selections": selections,
        "summary": {key: len(value) for key, value in selections.items()},
        "guardrails": [
            "candidates are computed by the system runtime",
            "practitioner choices only override the current narrative reading",
            "choices do not modify runtime parameters or learning governance state",
        ],
    }


def normalize_practitioner_override_context(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    selections = raw.get("selections") if isinstance(raw.get("selections"), dict) else {}
    normalized = {
        "contract": OVERRIDE_CONTEXT_CONTRACT,
        "source": str(raw.get("source") or "oracle_six_pillars_panel").strip(),
        "selections": {
            "pattern": _normalize_selected_candidate(selections.get("pattern"), "pattern"),
            "use_god": _normalize_selected_candidate(selections.get("use_god"), "use_god"),
            "taboo_god": _normalize_selected_candidate(selections.get("taboo_god"), "taboo_god"),
        },
        "guardrails": [
            "override applies to this narrative generation only",
            "system parameters and candidate rankings remain unchanged",
        ],
    }
    normalized["has_override"] = any(
        bool(row.get("name")) for row in normalized["selections"].values() if isinstance(row, dict)
    )
    return normalized


def practitioner_override_prompt_lines(context: dict[str, Any]) -> list[str]:
    normalized = normalize_practitioner_override_context(context)
    if not normalized.get("has_override"):
        return []
    selections = normalized.get("selections") if isinstance(normalized.get("selections"), dict) else {}
    parts: list[str] = []
    pattern = selections.get("pattern") if isinstance(selections.get("pattern"), dict) else {}
    use_god = selections.get("use_god") if isinstance(selections.get("use_god"), dict) else {}
    taboo_god = selections.get("taboo_god") if isinstance(selections.get("taboo_god"), dict) else {}
    if pattern.get("name"):
        parts.append(f"格局={pattern.get('name')}({int(_safe_float(pattern.get('confidence')) * 100)}%)")
    if use_god.get("name"):
        parts.append(f"用神={use_god.get('name')}({int(_safe_float(use_god.get('confidence')) * 100)}%)")
    if taboo_god.get("name"):
        parts.append(f"忌神={taboo_god.get('name')}({int(_safe_float(taboo_god.get('confidence')) * 100)}%)")
    if not parts:
        return []
    return [
        "命理师本次选定前提：" + "；".join(parts) + "。",
        "叙事生成必须按上述命理师选定前提解释，不得重新改选格局、用神或忌神；该前提只影响本次断语，不修改系统参数。",
    ]


def selected_override_gods(context: dict[str, Any]) -> tuple[list[str], list[str]]:
    normalized = normalize_practitioner_override_context(context)
    selections = normalized.get("selections") if isinstance(normalized.get("selections"), dict) else {}
    use_row = selections.get("use_god") if isinstance(selections.get("use_god"), dict) else {}
    taboo_row = selections.get("taboo_god") if isinstance(selections.get("taboo_god"), dict) else {}
    use_name = str(use_row.get("name") or "").strip()
    taboo_name = str(taboo_row.get("name") or "").strip()
    return ([use_name] if use_name else [], [taboo_name] if taboo_name else [])


def _pattern_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("pattern_candidate") or row.get("pattern_name") or "").strip()
        if not name:
            continue
        target = str(row.get("target_god") or "").strip()
        key = f"{name}::{target or 'na'}"
        confidence = _normalize_confidence(
            row.get("pattern_confidence_percent")
            if row.get("pattern_confidence_percent") is not None
            else row.get("pattern_confidence")
            if row.get("pattern_confidence") is not None
            else row.get("match_ratio")
            if row.get("match_ratio") is not None
            else row.get("confidence")
        )
        current = candidates.get(key)
        if current and _safe_float(current.get("confidence")) >= confidence:
            continue
        candidates[key] = {
            "id": f"pattern:{key}",
            "kind": "pattern",
            "name": name,
            "label": name,
            "target_god": target,
            "confidence": round(confidence, 3),
            "confidence_percent": int(round(confidence * 100)),
            "selected_by_system": False,
            "source": str(row.get("plugin_id") or row.get("source") or "").strip(),
            "status": str(row.get("manifestation_state") or row.get("candidate_status") or "").strip(),
            "scope": str(row.get("pattern_scope_label") or row.get("pattern_scope") or "").strip(),
            "evidence_id": str(row.get("evidence_id") or row.get("claim_id") or row.get("id") or "").strip(),
            "reason": str(row.get("pattern_gate_reason") or row.get("summary") or row.get("fact") or "").strip()[:240],
        }
    out = sorted(candidates.values(), key=lambda item: _safe_float(item.get("confidence")), reverse=True)[:8]
    if out:
        out[0]["selected_by_system"] = True
    return out


def _god_candidates(
    *,
    kind: str,
    source: str,
    rows: Any,
    selected_names: list[str],
    authority_confidence: float,
) -> list[dict[str, Any]]:
    raw_rows = rows if isinstance(rows, list) else []
    by_name: dict[str, dict[str, Any]] = {}
    max_score = max([_safe_float((row or {}).get("score")) for row in raw_rows if isinstance(row, dict)] + [0.0])
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        god = str(row.get("god") or row.get("name") or "").strip()
        if not god:
            continue
        score = _safe_float(row.get("score"))
        confidence = _candidate_confidence(score=score, max_score=max_score, authority_confidence=authority_confidence)
        by_name[god] = {
            "id": f"{kind}:{god}",
            "kind": kind,
            "name": god,
            "label": god,
            "confidence": confidence,
            "confidence_percent": int(round(confidence * 100)),
            "selected_by_system": god in selected_names,
            "score": round(score, 4),
            "source": source,
            "reason": str(row.get("authority_reason") or row.get("authority_profile") or "").strip(),
            "metrics": {
                key: row.get(key)
                for key in (
                    "resolved_flux",
                    "harm",
                    "flux_harm",
                    "authority_energy",
                    "authority_stability",
                    "authority_volatility",
                    "authority_climate_fit",
                    "tension_load",
                    "reinforce_load",
                )
                if row.get(key) is not None
            },
        }
    for name in selected_names:
        if name in by_name:
            by_name[name]["selected_by_system"] = True
            continue
        confidence = _normalize_confidence(authority_confidence)
        by_name[name] = {
            "id": f"{kind}:{name}",
            "kind": kind,
            "name": name,
            "label": name,
            "confidence": confidence,
            "confidence_percent": int(round(confidence * 100)),
            "selected_by_system": True,
            "score": 0.0,
            "source": "god_ring_authority",
            "reason": "system selected",
            "metrics": {},
        }
    return sorted(
        by_name.values(),
        key=lambda item: (1 if item.get("selected_by_system") else 0, _safe_float(item.get("confidence"))),
        reverse=True,
    )[:8]


def _normalize_selected_candidate(value: Any, kind: str) -> dict[str, Any]:
    row = value if isinstance(value, dict) else {}
    name = str(row.get("name") or row.get("label") or "").strip()
    confidence = _normalize_confidence(row.get("confidence"))
    fallback_id = f"{kind}:{name}" if name else ""
    return {
        "id": str(row.get("id") or fallback_id).strip(),
        "kind": kind,
        "name": name,
        "label": str(row.get("label") or name).strip(),
        "confidence": confidence,
        "confidence_percent": int(round(confidence * 100)),
        "source": str(row.get("source") or "").strip(),
        "selected_by_system": bool(row.get("selected_by_system")),
    }


def _clean_names(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = str(value or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _candidate_confidence(*, score: float, max_score: float, authority_confidence: float) -> float:
    base = authority_confidence if 0 < authority_confidence <= 1 else 0.72
    if score <= 0:
        return round(max(0.0, min(1.0, base)), 3)
    if max_score > 0:
        return round(max(0.01, min(0.99, (score / max_score) * base)), 3)
    return round(max(0.01, min(0.99, score if score <= 1 else 0.99)), 3)


def _normalize_confidence(value: Any) -> float:
    raw = _safe_float(value)
    if raw > 1:
        raw = raw / 100
    return max(0.0, min(1.0, raw))


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0
