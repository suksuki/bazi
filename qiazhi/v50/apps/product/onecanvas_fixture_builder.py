from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical, CalendarType, Gender
from core.engines.bazi.temporal_service import CanonicalTemporalService
from core.engines.bazi.pillar_cycle import (
    BIRTH_YEAR_MAX,
    BIRTH_YEAR_MIN,
    JIAZI,
    birth_year_options_by_pillar as _birth_year_options_by_pillar,
    hour_pillar_options as _hour_pillar_options,
    linked_hour_pillar as _linked_hour_pillar_for_branch,
    linked_month_pillar as _linked_month_pillar_for_branch,
    month_pillar_options as _month_pillar_options,
)
from product.agent_case_store import PostgresAgentCaseStore
from product.mingli_lab_fixture_builder import (
    DEFAULT_DATABASE_URL,
    build_fixture as build_c2a_fixture,
)
from product.onecanvas_timing_adapter import chart_type_label, project_canonical_timing
from product.projection_refs import anonymous_ref as _anonymous_ref
from product.structural_variant_compiler import (
    compile_onecanvas_structural_variant,
    pillar_nodes,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "apps"
    / "product"
    / "static"
    / "experience"
    / "active"
    / "onecanvas-r1"
    / "fixture.json"
)
NATAL_SLOTS = ("year", "month", "day", "hour")
_TEMPORAL_SERVICE = CanonicalTemporalService()


def build_fixture(*, database_url: str, case_id: str, user_id: str) -> dict[str, Any]:
    c2a = build_c2a_fixture(database_url=database_url, case_id=case_id, user_id=user_id)
    store = PostgresAgentCaseStore(database_url)
    row = store.get(case_id=case_id, user_id=user_id)
    if not row or not isinstance(row.get("birth_input"), dict):
        raise ValueError("onecanvas_birth_input_missing")
    birth = BirthInputCanonical.model_validate(row["birth_input"])
    if birth.calendar_type != CalendarType.SOLAR:
        raise ValueError("onecanvas_prototype_requires_solar_calendar_case")

    formal = c2a["formal"]
    baseline_pillars = list(formal["pillars"])
    baseline_variant = c2a["variants"][c2a["baseline_variant_index"]]
    baseline_relations = baseline_variant["relations"]
    analysis_year = int(formal["analysis_year"])

    baseline_timing = _baseline_timing_fixture(
        birth=birth,
        analysis_year=analysis_year,
        formal_luck_pillar=str(formal["luck_pillar"] or ""),
        formal_luck_range=list(formal["luck_year_range"] or []),
    )
    baseline_timing["formal_reference"] = {
        "luck_pillar": str(formal["luck_pillar"] or ""),
        "luck_year_range": list(formal["luck_year_range"] or []),
    }
    candidate_families = {
        "year": _cycle_axis_candidates(
            axis="year",
            birth=birth,
            baseline_pillars=baseline_pillars,
            baseline_relations=baseline_relations,
            formal_path=formal["path"],
            analysis_year=analysis_year,
            baseline_timing=baseline_timing,
        ),
        "day": _cycle_axis_candidates(
            axis="day",
            birth=birth,
            baseline_pillars=baseline_pillars,
            baseline_relations=baseline_relations,
            formal_path=formal["path"],
            analysis_year=analysis_year,
            baseline_timing=baseline_timing,
        ),
    }
    baseline_match = {
        axis: next(
            index
            for index, candidate in enumerate(candidates)
            if candidate["pillars"] == baseline_pillars
        )
        for axis, candidates in candidate_families.items()
    }
    baseline_variant = candidate_families["day"][baseline_match["day"]]
    year_dial = [
        {
            **item,
            "calendar_context": {
                "disclosure_mode": "gregorian_year",
                "gregorian_year": int(item["year"]),
                "timezone": birth.timezone,
                "calendar_type": birth.calendar_type.value,
                "raw_birth_datetime_in_fixture": False,
            },
            "nodes": pillar_nodes(
                pillar=str(item["pillar"]),
                slot="annual",
                day_stem=baseline_pillars[2][0],
                source_mode=str(item["source_mode"]),
                source_refs=[
                    _anonymous_ref(
                        f"annual:{item['year']}:{item['pillar']}",
                        "timing-source",
                    )
                ],
            ),
        }
        for item in c2a["year_dial"]
    ]

    return {
        "schema_version": "deepbazi.mingli_onecanvas_c2ar_fixture.v1",
        "prototype": "Mingli OneCanvas / 六柱一图",
        "source": {
            **c2a["source"],
            "calendar_anchor_ref": _anonymous_ref(
                f"{birth.birth_date}T{birth.birth_time}:{birth.calendar_type.value}",
                "calendar-anchor",
            ),
            "contains_raw_birth_datetime": False,
        },
        "formal": {
            **formal,
            "timing_recalculation": baseline_timing,
            "nodes": baseline_variant["nodes"],
            "relations": baseline_variant["relations"],
        },
        "structural_context": {
            "gender": birth.gender.value,
            "chart_type": chart_type_label(birth.gender),
            "gender_required_for_luck": birth.gender == Gender.UNKNOWN,
            "birth_year_hint": None,
            "selection_semantics": "hypothetical_pillar_structure_not_real_birth_datetime",
        },
        "selection_catalogs": {
            "year": list(JIAZI),
            "month_by_year": {
                pillar: _month_pillar_options(year_pillar=pillar)
                for pillar in JIAZI
            },
            "day": list(JIAZI),
            "hour_by_day": {
                pillar: _hour_pillar_options(day_pillar=pillar)
                for pillar in JIAZI
            },
            "birth_year_by_year_pillar": _birth_year_options_by_pillar(),
            "birth_year_range": [BIRTH_YEAR_MIN, BIRTH_YEAR_MAX],
            "gender_options": [
                {"value": Gender.MALE.value, "label": "乾造"},
                {"value": Gender.FEMALE.value, "label": "坤造"},
            ],
        },
        "candidate_families": candidate_families,
        "baseline_candidate_index": baseline_match,
        "year_dial": year_dial,
        "r1_contract": {
            "schema_version": "deepbazi.onecanvas_r1_authority.v2",
            "selection_mode": "sexagenary_cycle_structural",
            "candidate_authority": "server_side_pillar_target_solver",
            "candidate_disclosure": "structural_cycle_only",
            "recompute_statuses": [
                "recalculated_changed",
                "recalculated_unchanged",
                "recalculation_unavailable",
            ],
            "slot_capabilities": {
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
                    "candidate_scope": "twelve_legal_month_pillars_for_selected_year",
                    "depends_on": "year",
                    "option_count": 12,
                    "derivation": "five_tigers_candidate_set",
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
                    "candidate_scope": "twelve_legal_hour_pillars_for_selected_day",
                    "depends_on": "day",
                    "option_count": 12,
                    "derivation": "five_rats_candidate_set",
                },
                "luck": {"editable_in_experiment": False, "switchable": True, "derived": True},
                "annual": {
                    "editable_in_experiment": False,
                    "switchable": True,
                    "derived": True,
                    "independent_observation": True,
                },
            },
        },
        "constraint_profiles": {
            "year": {
                "locked_slots": ["day"],
                "linked_slots": ["month"],
                "option_count": 60,
                "explanation": "年柱从完整六十甲子中选择；确认后，月柱候选更新为该年干对应的十二个合法整柱。",
            },
            "month": {
                "locked_slots": ["year", "day"],
                "linked_slots": [],
                "editable": True,
                "depends_on": "year",
                "option_count": 12,
                "explanation": "月柱可选择，但只能从当前年干按五虎遁生成的十二个合法月柱中选择。",
            },
            "day": {
                "locked_slots": ["year", "month"],
                "linked_slots": ["hour"],
                "option_count": 60,
                "explanation": "日柱从完整六十甲子中选择；确认后，时柱候选更新为该日干对应的十二个合法整柱。",
            },
            "hour": {
                "locked_slots": ["year", "month", "day"],
                "linked_slots": [],
                "editable": True,
                "depends_on": "day",
                "option_count": 12,
                "explanation": "时柱可选择，但只能从当前日干按五鼠遁生成的十二个合法时柱中选择。",
            },
        },
        "interaction_contract": {
            "primary_node_count": 12,
            "semantic_slots": [*NATAL_SLOTS, "luck", "annual"],
            "comparison_mode": "same_space_crossfade",
            "path_support_dimensions": [
                "relation_availability",
                "continuity_status",
                "timing_material_status",
                "closure_status",
            ],
        },
        "boundaries": [
            "年柱与日柱各自从完整六十甲子选择；月柱与时柱分别从十二个合法依赖候选中选择",
            "结构实验不声称对应真实公历出生日期",
            "大运在结构候选完成后派生，不由用户或前端手工指定",
            "实验副本不修改正式命盘或 LifeCase",
            "变体 Graph 是候选结构证据，不自动升级为正式主路径",
            "用户路径始终是 PathDraft",
            "没有 typed temporal path effect 时，流年只作为时间信号",
            "原型不调用 LLM、TTS，不部署到生产环境",
        ],
    }


def _cycle_axis_candidates(
    *,
    axis: str,
    birth: BirthInputCanonical,
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
    analysis_year: int,
    baseline_timing: dict[str, Any],
) -> list[dict[str, Any]]:
    if axis not in {"year", "day"}:
        raise ValueError(f"onecanvas_cycle_axis_not_independent:{axis}")
    output: list[dict[str, Any]] = []
    for index, selected_pillar in enumerate(JIAZI):
        pillars = list(baseline_pillars)
        if axis == "year":
            pillars[0] = selected_pillar
            pillars[1] = _linked_month_pillar(
                year_pillar=selected_pillar,
                retained_month_branch=baseline_pillars[1][1],
            )
        else:
            pillars[2] = selected_pillar
            pillars[3] = _linked_hour_pillar(
                day_pillar=selected_pillar,
                retained_hour_branch=baseline_pillars[3][1],
            )
        candidate_birth = _structural_birth(birth=birth, pillars=pillars)
        canonical_timing = _TEMPORAL_SERVICE.resolve_structural_dayun(
            pillars=pillars,
            gender=birth.gender,
            analysis_year=analysis_year,
            timezone=birth.timezone,
            limit=10,
            baseline=baseline_timing,
        )
        source_mode = "derived" if pillars == baseline_pillars else "hypothetical"
        timing = project_canonical_timing(
            canonical=canonical_timing,
            day_stem=pillars[2][0],
            baseline_timing=baseline_timing,
            source_mode=source_mode,
            source_ref_transform=lambda value: _anonymous_ref(value, "timing-source"),
            observation_ref_factory=lambda item: _anonymous_ref(
                f"structural:{item['sequence_index']}:{item['pillar']}:{canonical_timing['direction']}",
                "luck-observation",
            ),
        )
        for item in timing.get("luck_sequence") or []:
            item["derivation"] = {
                "mode": "structural_sequence_only",
                "direction": canonical_timing["direction"],
                "phase_anchor": "unresolved_without_real_datetime",
                "start_age_recalculated": False,
            }
        output.append(compile_onecanvas_structural_variant(
            axis=axis,
            index=index,
            birth=candidate_birth,
            baseline_pillars=baseline_pillars,
            baseline_relations=baseline_relations,
            formal_path=formal_path,
            timing_recalculation=timing,
        ))
    return output


def _structural_birth(*, birth: BirthInputCanonical, pillars: list[str]) -> BirthInputCanonical:
    return birth.model_copy(update={
        "year_pillar": pillars[0],
        "month_pillar": pillars[1],
        "day_pillar": pillars[2],
        "hour_pillar": pillars[3],
        "input_quality": "sexagenary_cycle_structural_sandbox",
        "pillar_fact_source": "structurally_legal_hypothetical",
    })


def _linked_month_pillar(*, year_pillar: str, retained_month_branch: str) -> str:
    return _linked_month_pillar_for_branch(
        year_pillar=year_pillar,
        month_branch=retained_month_branch,
    )


def _linked_hour_pillar(*, day_pillar: str, retained_hour_branch: str) -> str:
    return _linked_hour_pillar_for_branch(
        day_pillar=day_pillar,
        hour_branch=retained_hour_branch,
    )




def _baseline_timing_fixture(
    *,
    birth: BirthInputCanonical,
    analysis_year: int,
    formal_luck_pillar: str,
    formal_luck_range: list[Any],
) -> dict[str, Any]:
    baseline = {
        "luck_pillar": formal_luck_pillar,
        "luck_year_range": list(formal_luck_range),
    }
    canonical = _TEMPORAL_SERVICE.resolve_exact_dayun(
        birth_input=birth,
        analysis_year=analysis_year,
        baseline=baseline,
    )
    return project_canonical_timing(
        canonical=canonical,
        day_stem=birth.day_pillar[0] if birth.day_pillar else "",
        baseline_timing=baseline,
        source_mode="derived",
        source_ref_transform=lambda value: _anonymous_ref(value, "timing-source"),
        observation_ref_factory=lambda item: _anonymous_ref(
            f"{item['sequence_index']}:{item['pillar']}:{item.get('start_year')}:{item.get('end_year')}",
            "luck-observation",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the anonymized Mingli OneCanvas C2A-R fixture.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture(database_url=args.database_url, case_id=args.case_id, user_id=args.user_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(fixture, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "onecanvas_fixture_ready",
        "output": str(args.output),
        "case_ref": fixture["source"]["case_ref"],
        "candidate_counts": {
            axis: len(items)
            for axis, items in fixture["candidate_families"].items()
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
