from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.validation.synthetic_schema import SyntheticCase


@dataclass(frozen=True)
class MatrixSpec:
    base_case_count: int
    stems: tuple[str, ...] = (
        "甲",
        "乙",
        "丙",
        "丁",
        "戊",
        "己",
        "庚",
        "辛",
        "壬",
        "癸",
    )
    branches: tuple[str, ...] = (
        "子",
        "丑",
        "寅",
        "卯",
        "辰",
        "巳",
        "午",
        "未",
        "申",
        "酉",
        "戌",
        "亥",
    )
    stem_stride: int = 1
    branch_stride: int = 7

    def pair(self, index: int) -> str:
        stem = self.stems[(index * self.stem_stride) % len(self.stems)]
        branch = self.branches[(index * self.branch_stride + index // len(self.stems)) % len(self.branches)]
        return f"{stem}{branch}"


_HEXAGON_FEATURE_DOMAINS: tuple[str, ...] = (
    "strength",
    "ten_god",
    "branch",
    "element",
    "wealth",
    "career",
    "relationship",
    "health",
    "useful_god",
    "pattern",
    "time",
)


def build_regression_golden_cases(
    case_count: int = 120,
    *,
    seed: int = 2026,
    with_question_keys: bool = False,
    with_feature_domains: bool = False,
    stems: tuple[str, ...] | None = None,
    branches: tuple[str, ...] | None = None,
) -> tuple[SyntheticCase, ...]:
    resolved_stems = stems or MatrixSpec(base_case_count=0).stems
    resolved_branches = branches or MatrixSpec(base_case_count=0).branches
    spec = MatrixSpec(base_case_count=0, stems=resolved_stems, branches=resolved_branches)
    rows: list[SyntheticCase] = []
    for index in range(case_count):
        seq_index = seed + index
        rows.append(
            SyntheticCase(
                case_id=f"v20.synthetic.golden.matrix.{seq_index:05d}",
                pillar_displays=_matrix_pillars(seq_index, spec=spec),
                expected_feature_domains=_expected_feature_domains(seq_index) if with_feature_domains else (),
                expected_question_keys=_expected_question_keys(seq_index) if with_question_keys else (),
            )
        )
    return tuple(rows)


def build_regression_rule_synthetic_case_payloads(
    case_count: int,
    *,
    seed: int = 4000,
    stems: tuple[str, ...] | None = None,
    branches: tuple[str, ...] | None = None,
) -> tuple[dict[str, object], ...]:
    resolved_stems = stems or MatrixSpec(base_case_count=0).stems
    resolved_branches = branches or MatrixSpec(base_case_count=0).branches
    spec = MatrixSpec(base_case_count=0, stems=resolved_stems, branches=resolved_branches)
    rows: list[dict[str, object]] = []

    for index in range(case_count):
        seq_index = seed + index
        rows.append(
            {
                "case_id": f"v20.rule.synthetic.matrix.{seq_index:05d}",
                "pillar_displays": _matrix_pillars(seq_index, spec=spec),
                "expected_rule_domains": (),
                "expected_feature_prefixes": (),
                "expected_question_keys": (),
                "question_key": "",
                "notes": "matrix-scale synthetic rule coverage",
            }
        )

    return tuple(rows)


def matrix_golden_manifest(
    *, case_count: int, seed: int = 2026
) -> dict[str, Any]:
    spec = MatrixSpec(base_case_count=0)
    return {
        "spec": asdict(spec),
        "case_count": int(case_count),
        "seed": int(seed),
        "default_domain_coverage": ["strength", "ten_god", "branch", "element", "wealth", "career", "health"],
        "synthesis_formula": "deterministic_stem_branch_matrix_with_stride",
    }


def _matrix_pillars(seed: int, *, spec: MatrixSpec) -> tuple[str, str, str, str]:
    year = spec.pair(seed + 0)
    month = spec.pair(seed + 11)
    day = spec.pair(seed + 23)
    hour = spec.pair(seed + 37)
    return year, month, day, hour


def _expected_feature_domains(index: int) -> tuple[str, ...]:
    domain = _feature_domain_for_index(index)
    return tuple(dict.fromkeys((domain, "strength", "ten_god")))


def _expected_question_keys(index: int) -> tuple[str, ...]:
    domain = _feature_domain_for_index(index)
    mapping = {
        "strength": ("q_strength_assessment",),
        "ten_god": ("q_hidden_stem_role",),
        "branch": ("q_branch_relation_detail",),
        "element": ("q_element_balance",),
        "wealth": ("q_income_stability",),
        "career": ("q_career_structure",),
        "relationship": ("q_relationship_structure",),
        "health": ("q_health_balance_boundary",),
        "useful_god": ("q_useful_god_candidates",),
        "pattern": ("q_pattern_structure",),
        "time": ("q_time_layer_context",),
    }
    return mapping.get(domain, ())


def _feature_domain_for_index(index: int) -> str:
    return _HEXAGON_FEATURE_DOMAINS[index % len(_HEXAGON_FEATURE_DOMAINS)]
