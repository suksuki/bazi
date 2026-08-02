from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Final, Literal

from abu_v60.mingli.calendar import BirthInput
from abu_v60.provenance import content_hash, stable_ref

SYNTHETIC_EXPERIMENT_CATALOG_VERSION: Final = (
    "v60.mingli-synthetic-experiment-catalog.001"
)
SYNTHETIC_RESEARCH_ACCOUNT_REF: Final = "v60-system-account-mingli-synthetic-lab-v1"
SYNTHETIC_RESEARCH_BATCH_REF: Final = "v60-seed-batch-mingli-synthetic-lab-v1"
SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION: Final = (
    "v60.mingli-synthetic-experiment-evaluator.001"
)

_EXPERIMENT_TITLE: Final = "合法时柱改变后，日主判型是否随证据改变？"
_EXPERIMENT_QUESTION: Final = (
    "只改变合法出生时刻，让时柱从己巳变为丙寅；检查系统是否识别新增的寅中甲根"
    "以及同时发生的时柱十神变化，并守住前三柱、月令等不该漂移的部分。"
)
_MEMBER_A_BIRTH_INPUT: Final = BirthInput(
    calendar_type="solar",
    birth_date=date(2006, 10, 12),
    birth_time=time(9, 0),
    timezone="Asia/Shanghai",
    true_solar_time_policy="not_applied",
)
_MEMBER_B_BIRTH_INPUT: Final = BirthInput(
    calendar_type="solar",
    birth_date=date(2006, 10, 12),
    birth_time=time(3, 0),
    timezone="Asia/Shanghai",
    true_solar_time_policy="not_applied",
)
_MEMBER_A_EXPECTED_PILLARS: Final = ("丙戌", "戊戌", "甲戌", "己巳")
_MEMBER_B_EXPECTED_PILLARS: Final = ("丙戌", "戊戌", "甲戌", "丙寅")

_EXPERIMENT_IDENTITY = {
    "catalog_version": SYNTHETIC_EXPERIMENT_CATALOG_VERSION,
    "suite": "DEV",
    "family": "CONTROLLED_LEGAL_HOUR_PAIR",
    "analysis_date": "2026-08-02",
    "title": _EXPERIMENT_TITLE,
    "question": _EXPERIMENT_QUESTION,
    "blind_protocol": "MEMBERS_INDEPENDENT_GOLD_NOT_IN_AGENT_PACKET",
    "inference_scope": "WHOLE_HOUR_PILLAR_RESPONSE_NOT_ROOT_CAUSAL_ESTIMATE",
    "inference_limit": (
        "该合法时柱对照同时改变时干十神与支藏成员，不能把判型变化单独归因于根气。"
    ),
    "known_collateral_deltas": (
        "时干由己正财变为丙食神",
        "时支藏干由巳中丙戊庚变为寅中甲丙戊",
        "新增甲比肩根候选，同时移除庚七杀成员",
    ),
    "changed_input": {
        "field": "birth_time",
        "A": "09:00:00",
        "B": "03:00:00",
    },
    "controlled_members": {
        "A": {
            "birth_input": _MEMBER_A_BIRTH_INPUT.model_dump(mode="json"),
            "expected_pillars": _MEMBER_A_EXPECTED_PILLARS,
        },
        "B": {
            "birth_input": _MEMBER_B_BIRTH_INPUT.model_dump(mode="json"),
            "expected_pillars": _MEMBER_B_EXPECTED_PILLARS,
        },
    },
}
FIRST_SYNTHETIC_EXPERIMENT_REF: Final = stable_ref(
    "v60-mingli-synthetic-experiment",
    _EXPERIMENT_IDENTITY,
)


@dataclass(frozen=True, slots=True)
class SyntheticExperimentMember:
    variant: Literal["A", "B"]
    member_ref: str
    subject_id: str
    case_ref: str
    profile_ref: str
    display_name: str
    birth_input: BirthInput
    expected_pillars: tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class MingliResearchStageBinding:
    account_ref: str
    case_ref: str
    display_name: str
    narrator_actor_id: Literal["ABU_NARRATOR_V1"] = "ABU_NARRATOR_V1"
    identity_badge: Literal["研究合成命盘"] = "研究合成命盘"
    privacy_scope: Literal["SYNTHETIC_RESEARCH"] = "SYNTHETIC_RESEARCH"


def _member(
    variant: Literal["A", "B"],
    *,
    birth_input: BirthInput,
    expected_pillars: tuple[str, str, str, str],
) -> SyntheticExperimentMember:
    identity = {
        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
        "variant": variant,
    }
    member_ref = stable_ref("v60-mingli-synthetic-member", identity)
    return SyntheticExperimentMember(
        variant=variant,
        member_ref=member_ref,
        subject_id=f"research:{member_ref}",
        case_ref=stable_ref("v60-mingli-synthetic-case", identity),
        profile_ref=stable_ref("v60-mingli-synthetic-profile", identity),
        display_name=f"研究命盘 {variant}",
        birth_input=birth_input,
        expected_pillars=expected_pillars,
    )


FIRST_SYNTHETIC_EXPERIMENT_MEMBERS: Final = (
    _member(
        "A",
        birth_input=_MEMBER_A_BIRTH_INPUT,
        expected_pillars=_MEMBER_A_EXPECTED_PILLARS,
    ),
    _member(
        "B",
        birth_input=_MEMBER_B_BIRTH_INPUT,
        expected_pillars=_MEMBER_B_EXPECTED_PILLARS,
    ),
)
SYNTHETIC_MEMBER_BY_VARIANT: Final = {
    item.variant: item for item in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
}
SYNTHETIC_MEMBER_BY_SUBJECT: Final = {
    item.subject_id: item for item in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
}
SYNTHETIC_MEMBER_BY_CASE: Final = {
    item.case_ref: item for item in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
}
SYNTHETIC_RESEARCH_CASE_REFS: Final = frozenset(SYNTHETIC_MEMBER_BY_CASE)
SYNTHETIC_EXPERIMENT_ANALYSIS_DATE: Final = date(2026, 8, 2)


def resolve_research_stage_subject(
    subject_id: str,
) -> MingliResearchStageBinding | None:
    member = SYNTHETIC_MEMBER_BY_SUBJECT.get(subject_id)
    if member is None:
        return None
    return MingliResearchStageBinding(
        account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
        case_ref=member.case_ref,
        display_name=member.display_name,
    )


def synthetic_experiment_public_definition() -> dict[str, object]:
    identity = {
        **_EXPERIMENT_IDENTITY,
        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
        "members": tuple(
            {
                "variant": item.variant,
                "member_ref": item.member_ref,
                "subject_id": item.subject_id,
            }
            for item in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
        ),
        "full_pillar_delta": {
            "A": list(SYNTHETIC_MEMBER_BY_VARIANT["A"].expected_pillars),
            "B": list(SYNTHETIC_MEMBER_BY_VARIANT["B"].expected_pillars),
            "changed_slots": ["hour"],
            "legal_hour_pillar_change": "己巳 → 丙寅",
        },
    }
    return {
        **identity,
        "definition_hash": content_hash(identity),
    }
