from __future__ import annotations

import argparse
import json
from pathlib import Path

from product.onecanvas_structural import selection_catalog_payload


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = (
    ROOT
    / "apps"
    / "product"
    / "static"
    / "experience"
    / "active"
    / "onecanvas-r1"
    / "fixture.json"
)


def upgrade_fixture(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    catalog = selection_catalog_payload()
    payload["selection_catalogs"] = {
        key: value
        for key, value in catalog.items()
        if key in {
            "schema_version", "authority", "year", "month_by_year", "day", "hour_by_day",
            "stems", "branches", "branches_by_stem", "stems_by_branch", "gender_options",
            "cycle_year_anchor_by_year_pillar", "actual_birth_year_candidates_by_year_pillar",
            "birth_year_by_year_pillar", "birth_year_range", "annual_observations",
        }
    }
    payload.setdefault("structural_context", {
        "gender": "unknown",
        "selection_semantics": "hypothetical_pillar_structure_not_real_birth_datetime",
    })
    payload["r1_contract"]["candidate_authority"] = "server_side_pillar_target_solver"
    payload["r1_contract"]["selection_contract_version"] = "v5"
    payload["r1_contract"]["legacy_precompiled_candidate_families_used_by_runtime"] = False
    payload["r1_contract"]["gender_authority"] = "explicit_birth_fact_or_explicit_sandbox_choice"
    payload["r1_contract"]["unknown_gender_luck_policy"] = "unavailable_never_inferred"
    payload["r1_contract"]["slot_capabilities"].update({
        "year": {
            "editable_in_experiment": True,
            "switchable": False,
            "derived": False,
            "independent_cycle_choice": True,
            "option_count": 60,
        },
        "month": {
            "editable_in_experiment": True,
            "switchable": False,
            "derived": False,
            "depends_on": "year",
            "option_count": 12,
        },
        "day": {
            "editable_in_experiment": True,
            "switchable": False,
            "derived": False,
            "independent_cycle_choice": True,
            "option_count": 60,
        },
        "hour": {
            "editable_in_experiment": True,
            "switchable": False,
            "derived": False,
            "depends_on": "day",
            "option_count": 12,
        },
    })
    payload["constraint_profiles"] = {
        "year": {
            "locked_slots": ["day"],
            "linked_slots": ["month"],
            "option_count": 60,
            "explanation": "年柱从六十甲子中选择；月柱候选随年干更新。",
        },
        "month": {
            "locked_slots": ["year", "day"],
            "linked_slots": [],
            "option_count": 12,
            "depends_on": "year",
            "explanation": "月柱从当前年干对应的十二个合法整柱中选择。",
        },
        "day": {
            "locked_slots": ["year", "month"],
            "linked_slots": ["hour"],
            "option_count": 60,
            "explanation": "日柱从六十甲子中选择；时柱候选随日干更新。",
        },
        "hour": {
            "locked_slots": ["year", "month", "day"],
            "linked_slots": [],
            "option_count": 12,
            "depends_on": "day",
            "explanation": "时柱从当前日干对应的十二个合法整柱中选择。",
        },
    }
    structural_context = payload.setdefault("structural_context", {})
    structural_context.setdefault("birth_year_hint", None)
    gender = str(structural_context.get("gender") or "unknown")
    structural_context["chart_type"] = "乾造" if gender == "male" else "坤造" if gender == "female" else "命造未定"
    structural_context["gender_required_for_luck"] = gender not in {"male", "female"}
    if structural_context["gender_required_for_luck"]:
        _remove_unowned_luck_projection(payload)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "onecanvas_fixture_upgraded",
        "path": str(path),
        "selection_contract_version": "v5",
        "year_options": len(payload["selection_catalogs"]["year"]),
        "month_options_per_year": len(next(iter(payload["selection_catalogs"]["month_by_year"].values()))),
        "day_options": len(payload["selection_catalogs"]["day"]),
        "hour_options_per_day": len(next(iter(payload["selection_catalogs"]["hour_by_day"].values()))),
        "gender": gender,
        "luck_available": gender in {"male", "female"},
    }


def _remove_unowned_luck_projection(payload: dict[str, object]) -> None:
    formal = payload.get("formal")
    if not isinstance(formal, dict):
        return
    analysis_year = int(formal.get("analysis_year") or 0)
    formal["luck_pillar"] = ""
    formal["luck_year_range"] = []
    formal["nodes"] = _without_luck_nodes(formal.get("nodes"))
    formal["relations"] = _without_luck_relations(formal.get("relations"))
    formal["timing_recalculation"] = _gender_unavailable_timing(
        formal.get("timing_recalculation"),
        analysis_year=analysis_year,
    )
    families = payload.get("candidate_families")
    if not isinstance(families, dict):
        return
    for candidates in families.values():
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            candidate["nodes"] = _without_luck_nodes(candidate.get("nodes"))
            candidate["relations"] = _without_luck_relations(candidate.get("relations"))
            candidate["timing_recalculation"] = _gender_unavailable_timing(
                candidate.get("timing_recalculation"),
                analysis_year=analysis_year,
            )


def _without_luck_nodes(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if not isinstance(item, dict) or not str(item.get("node_key") or "").startswith("luck_")
    ]


def _without_luck_relations(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    output: list[object] = []
    for item in value:
        if not isinstance(item, dict):
            output.append(item)
            continue
        from_key = str(item.get("from_key") or item.get("from_anchor") or "")
        to_key = str(item.get("to_key") or item.get("to_anchor") or "")
        if from_key.startswith("luck_") or to_key.startswith("luck_"):
            continue
        output.append(item)
    return output


def _gender_unavailable_timing(value: object, *, analysis_year: int) -> dict[str, object]:
    timing = value if isinstance(value, dict) else {}
    return {
        "status": "recalculation_unavailable",
        "gender": "unknown",
        "chart_type": "命造未定",
        "current_luck_status": "unresolved",
        "luck_pillar": "",
        "luck_year_range": [],
        "luck_age_range": [None, None],
        "annual_pillar": str(timing.get("annual_pillar") or ""),
        "analysis_year": analysis_year,
        "confidence": 0.0,
        "missing_inputs": ["gender_required_for_luck_direction"],
        "calculation_refs": list(timing.get("calculation_refs") or []),
        "luck_sequence": [],
        "formal_reference": {"luck_pillar": "", "luck_year_range": []},
        "calculation_mode": "gender_required",
        "exact_timing_status": "unavailable",
        "direction": "unresolved",
        "failure_reason": "需先确认乾造或坤造，才能确定大运顺逆与序列",
        "limitations": ["性别缺失时不得推断、继承或猜测大运顺逆"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade the checked-in OneCanvas fixture to selection contract v2.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    print(json.dumps(upgrade_fixture(args.fixture), ensure_ascii=False))


if __name__ == "__main__":
    main()
