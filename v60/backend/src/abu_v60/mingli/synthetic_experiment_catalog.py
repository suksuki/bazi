from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any, Final, Literal

from abu_v60.mingli.calendar import BirthInput
from abu_v60.provenance import content_hash, stable_ref

SYNTHETIC_EXPERIMENT_CATALOG_VERSION: Final = "v60.mingli-synthetic-experiment-catalog.006"
SYNTHETIC_EXPERIMENT_DEFINITION_VERSION: Final = "v60.mingli-synthetic-experiment-catalog.001"
SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2: Final = "v60.mingli-synthetic-experiment-catalog.002"
SYNTHETIC_RESEARCH_ACCOUNT_REF: Final = "v60-system-account-mingli-synthetic-lab-v1"
SYNTHETIC_RESEARCH_BATCH_REF: Final = "v60-seed-batch-mingli-synthetic-lab-v1"
SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION: Final = "v60.mingli-synthetic-experiment-evaluator.008"


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
class SyntheticExperimentDefinition:
    experiment_ref: str
    seed_id: str
    seed_batch_ref: str
    analysis_date: date
    identity: dict[str, Any]
    members: tuple[SyntheticExperimentMember, SyntheticExperimentMember]
    legal_hour_pillar_change: str

    @property
    def member_by_variant(self) -> dict[str, SyntheticExperimentMember]:
        return {item.variant: item for item in self.members}

    def public_definition(self) -> dict[str, object]:
        members = self.member_by_variant
        identity = {
            **self.identity,
            "experiment_ref": self.experiment_ref,
            "members": tuple(
                {
                    "variant": item.variant,
                    "member_ref": item.member_ref,
                    "subject_id": item.subject_id,
                }
                for item in self.members
            ),
            "full_pillar_delta": {
                "A": list(members["A"].expected_pillars),
                "B": list(members["B"].expected_pillars),
                "changed_slots": ["hour"],
                "legal_hour_pillar_change": self.legal_hour_pillar_change,
            },
        }
        return {**identity, "definition_hash": content_hash(identity)}


@dataclass(frozen=True, slots=True)
class MingliResearchStageBinding:
    account_ref: str
    case_ref: str
    display_name: str
    narrator_actor_id: Literal["ABU_NARRATOR_V1"] = "ABU_NARRATOR_V1"
    identity_badge: Literal["研究合成命盘"] = "研究合成命盘"
    privacy_scope: Literal["SYNTHETIC_RESEARCH"] = "SYNTHETIC_RESEARCH"


def _member(
    experiment_ref: str,
    variant: Literal["A", "B"],
    *,
    birth_input: BirthInput,
    expected_pillars: tuple[str, str, str, str],
) -> SyntheticExperimentMember:
    identity = {"experiment_ref": experiment_ref, "variant": variant}
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


def _experiment(
    *,
    definition_version: str = SYNTHETIC_EXPERIMENT_DEFINITION_VERSION,
    seed_id: str,
    seed_batch_ref: str,
    analysis_date: date,
    family: str,
    title: str,
    question: str,
    inference_scope: str,
    inference_limit: str,
    known_collateral_deltas: tuple[str, ...],
    birth_date: date,
    member_a_time: time,
    member_b_time: time,
    member_a_pillars: tuple[str, str, str, str],
    member_b_pillars: tuple[str, str, str, str],
    legal_hour_pillar_change: str,
) -> SyntheticExperimentDefinition:
    member_a_birth = BirthInput(
        calendar_type="solar",
        birth_date=birth_date,
        birth_time=member_a_time,
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )
    member_b_birth = member_a_birth.model_copy(update={"birth_time": member_b_time})
    identity = {
        # This field is part of the sealed experiment identity.  Keep the
        # definition schema stable while the surrounding catalog transport
        # advances independently.
        "catalog_version": definition_version,
        "suite": "DEV",
        "family": family,
        "analysis_date": analysis_date.isoformat(),
        "title": title,
        "question": question,
        "blind_protocol": "MEMBERS_INDEPENDENT_GOLD_NOT_IN_AGENT_PACKET",
        "inference_scope": inference_scope,
        "inference_limit": inference_limit,
        "known_collateral_deltas": known_collateral_deltas,
        "changed_input": {
            "field": "birth_time",
            "A": member_a_time.isoformat(),
            "B": member_b_time.isoformat(),
        },
        "controlled_members": {
            "A": {
                "birth_input": member_a_birth.model_dump(mode="json"),
                "expected_pillars": member_a_pillars,
            },
            "B": {
                "birth_input": member_b_birth.model_dump(mode="json"),
                "expected_pillars": member_b_pillars,
            },
        },
    }
    experiment_ref = stable_ref("v60-mingli-synthetic-experiment", identity)
    return SyntheticExperimentDefinition(
        experiment_ref=experiment_ref,
        seed_id=seed_id,
        seed_batch_ref=seed_batch_ref,
        analysis_date=analysis_date,
        identity=identity,
        members=(
            _member(
                experiment_ref,
                "A",
                birth_input=member_a_birth,
                expected_pillars=member_a_pillars,
            ),
            _member(
                experiment_ref,
                "B",
                birth_input=member_b_birth,
                expected_pillars=member_b_pillars,
            ),
        ),
        legal_hour_pillar_change=legal_hour_pillar_change,
    )


FIRST_SYNTHETIC_EXPERIMENT: Final = _experiment(
    seed_id="v60.mingli-synthetic-lab.first-pair.001",
    seed_batch_ref=SYNTHETIC_RESEARCH_BATCH_REF,
    analysis_date=date(2026, 8, 2),
    family="CONTROLLED_LEGAL_HOUR_PAIR",
    title="合法时柱改变后，日主判型是否随证据改变？",
    question=(
        "只改变合法出生时刻，让时柱从己巳变为丙寅；检查系统是否识别新增的寅中甲根"
        "以及同时发生的时柱十神变化，并守住前三柱、月令等不该漂移的部分。"
    ),
    inference_scope="WHOLE_HOUR_PILLAR_RESPONSE_NOT_ROOT_CAUSAL_ESTIMATE",
    inference_limit="该合法时柱对照同时改变时干十神与支藏成员，不能把判型变化单独归因于根气。",
    known_collateral_deltas=(
        "时干由己正财变为丙食神",
        "时支藏干由巳中丙戊庚变为寅中甲丙戊",
        "新增甲比肩根候选，同时移除庚七杀成员",
    ),
    birth_date=date(2006, 10, 12),
    member_a_time=time(9, 0),
    member_b_time=time(3, 0),
    member_a_pillars=("丙戌", "戊戌", "甲戌", "己巳"),
    member_b_pillars=("丙戌", "戊戌", "甲戌", "丙寅"),
    legal_hour_pillar_change="己巳 → 丙寅",
)

ROOT_IDENTITY_SYNTHETIC_EXPERIMENT: Final = _experiment(
    seed_id="v60.mingli-synthetic-lab.root-identity-pair.001",
    seed_batch_ref="v60-seed-batch-mingli-synthetic-root-identity-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_ROOT_IDENTITY_PAIR",
    title="同为木根候选，乙木与甲木能否得到相同裁决？",
    question=(
        "只改变合法出生时刻，让时柱从丁卯变为丙寅；检查系统是否区分卯中乙木的"
        "同元素候选，与寅中甲木的日主同字候选。两盘时间均避开时辰边界。"
    ),
    inference_scope="NATAL_ROOT_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL",
    inference_limit=(
        "本实验只验证最低阻从门中的同字条件；不证明卯中乙无根、不可用，"
        "也不把整盘强弱变化单独归因于时支。"
    ),
    known_collateral_deltas=(
        "时干由丁伤官变为丙食神",
        "时支藏干由卯中乙变为寅中甲丙戊",
        "两盘都有木根候选，但只有 B 与甲日主同字",
        "出生时刻会改变大运起止边界；Timing 保存但不参与本组评分",
    ),
    birth_date=date(1989, 6, 3),
    member_a_time=time(6, 0),
    member_b_time=time(4, 0),
    member_a_pillars=("己巳", "己巳", "甲午", "丁卯"),
    member_b_pillars=("己巳", "己巳", "甲午", "丙寅"),
    legal_hour_pillar_change="丁卯 → 丙寅",
)

HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT: Final = _experiment(
    definition_version=SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2,
    seed_id="v60.mingli-synthetic-lab.hidden-rank-primary-secondary.001",
    seed_batch_ref="v60-seed-batch-mingli-hidden-rank-primary-secondary-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_HIDDEN_RANK_PRIMARY_SECONDARY_PAIR",
    title="同为乙木根候选，第一与第二藏干如何进入最低门？",
    question=(
        "只改变合法出生时刻，让乙木从卯中第一藏干移到辰中第二藏干；检查系统是否"
        "识别位阶与最低阻从门变化，同时保留完整时柱带来的其他差异。"
    ),
    inference_scope="NATAL_HIDDEN_RANK_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL",
    inference_limit=(
        "本实验只验证乙木第一／第二藏干身份与最低门；不提供位阶权重，"
        "也不把整盘判型、机制或岁运差异单独归因于藏干位置。"
    ),
    known_collateral_deltas=(
        "时干由己偏财变为庚正官",
        "时支藏干由卯中乙变为辰中戊乙癸",
        "辰中同时新增正财与偏印成员，不能作为纯位阶单变量",
        "起运边界与岁运关系成员会变化；Timing 保存但不参与本组评分",
    ),
    birth_date=date(1980, 6, 1),
    member_a_time=time(6, 0),
    member_b_time=time(8, 0),
    member_a_pillars=("庚申", "辛巳", "乙巳", "己卯"),
    member_b_pillars=("庚申", "辛巳", "乙巳", "庚辰"),
    legal_hour_pillar_change="己卯 → 庚辰",
)

HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT: Final = _experiment(
    definition_version=SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2,
    seed_id="v60.mingli-synthetic-lab.hidden-rank-secondary-tertiary.001",
    seed_batch_ref="v60-seed-batch-mingli-hidden-rank-secondary-tertiary-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_HIDDEN_RANK_SECONDARY_TERTIARY_PAIR",
    title="最低门未裁定时，第二与第三藏干会被误判成无根吗？",
    question=(
        "只改变合法出生时刻，让乙木从辰中第二藏干移到未中第三藏干；检查系统是否"
        "准确保存位阶，并避免在没有失效证据时把任一候选判成无根。"
    ),
    inference_scope="NATAL_HIDDEN_RANK_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL",
    inference_limit=(
        "本实验只验证第二／第三藏干身份与不自动失效；不要求两盘最终判型翻转，"
        "也不预设第三藏干必然弱、无效或不可用。"
    ),
    known_collateral_deltas=(
        "时干由庚正官变为癸偏印",
        "时支藏干由辰中戊乙癸变为未中己丁乙",
        "财、印与食神载体以及机制候选同时改变，不能作为纯位阶单变量",
        "起运边界与岁运关系成员会变化；Timing 保存但不参与本组评分",
    ),
    birth_date=date(1980, 6, 1),
    member_a_time=time(8, 0),
    member_b_time=time(14, 0),
    member_a_pillars=("庚申", "辛巳", "乙巳", "庚辰"),
    member_b_pillars=("庚申", "辛巳", "乙巳", "癸未"),
    legal_hour_pillar_change="庚辰 → 癸未",
)

HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT: Final = _experiment(
    definition_version=SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2,
    seed_id="v60.mingli-synthetic-lab.hidden-rank-cross-day-master.001",
    seed_batch_ref="v60-seed-batch-mingli-hidden-rank-cross-day-master-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_PAIR",
    title="换成丙火日主，第一与第二藏干还能得到同一套裁决吗？",
    question=(
        "只改变合法出生时刻，让丙火从巳中第一藏干移到寅中第二藏干；检查模型"
        "是否真正掌握跨日主的位阶方法，而不是记住乙木、卯辰未这组旧盘答案。"
    ),
    inference_scope="NATAL_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION",
    inference_limit=(
        "本实验只复核已经准入的最低阻从门能否跨日主泛化；完整时柱同时改变时干"
        "十神与全部藏干，不能把整盘强弱、机制或应事变化单独归因于位阶。"
    ),
    known_collateral_deltas=(
        "前三柱固定为庚辰、己卯、丙子，且没有其他丙火根候选或明干火同类",
        "时干由癸正官变为庚偏财",
        "时支藏干由巳中丙戊庚变为寅中甲丙戊",
        "偏印、食神、偏财载体与岁运边界同时变化，不作单一位阶因果",
    ),
    birth_date=date(2000, 3, 19),
    member_a_time=time(10, 0),
    member_b_time=time(4, 0),
    member_a_pillars=("庚辰", "己卯", "丙子", "癸巳"),
    member_b_pillars=("庚辰", "己卯", "丙子", "庚寅"),
    legal_hour_pillar_change="癸巳 → 庚寅",
)

REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT: Final = _experiment(
    definition_version=SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2,
    seed_id="v60.mingli-synthetic-lab.regime-work-path-generalization.001",
    seed_batch_ref="v60-seed-batch-mingli-regime-work-path-generalization-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_REGIME_WORK_PATH_GENERALIZATION_PAIR",
    title="换成戊土日主后，判型与主路径能否一起重算？",
    question=(
        "只改变合法出生时刻，让无根、无比、无印的辛酉时变为戌中戊土第一藏干"
        "取得最低有效根且同时出现丁印的壬戌时；检查模型是否重做整盘裁决、候选"
        "比较与主路径绑定，而不是只修正一个根位字段。"
    ),
    inference_scope="WHOLE_HOUR_PILLAR_RESPONSE_NOT_ROOT_CAUSAL_ESTIMATE",
    inference_limit=(
        "完整时柱同时改变时干、全部藏干、结构成员与起运边界；本实验只能检验整盘"
        "响应和决策自洽，不能把强弱、机制或应事变化单独归因于根位。"
    ),
    known_collateral_deltas=(
        "前三柱固定为癸酉、甲子、戊子，且没有其他戊土根、明干比劫或印星",
        "时干由辛伤官变为壬偏财",
        "时支由酉变为戌，藏干由辛变为戊辛丁",
        "B 新增戊土第一藏干最低有效根、伤官与正印成员",
        "机制候选集合与起运边界同时变化；Timing 保存但不参与本组评分",
    ),
    birth_date=date(1994, 1, 2),
    member_a_time=time(18, 0),
    member_b_time=time(20, 0),
    member_a_pillars=("癸酉", "甲子", "戊子", "辛酉"),
    member_b_pillars=("癸酉", "甲子", "戊子", "壬戌"),
    legal_hour_pillar_change="辛酉 → 壬戌",
)

CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT: Final = _experiment(
    definition_version=SYNTHETIC_EXPERIMENT_DEFINITION_VERSION_V2,
    seed_id="v60.mingli-synthetic-lab.candidate-partition-falsifier-generalization.001",
    seed_batch_ref="v60-seed-batch-mingli-candidate-partition-falsifier-v1",
    analysis_date=date(2026, 8, 3),
    family="CONTROLLED_DECISION_DISCIPLINE_GENERALIZATION_PAIR",
    title="换成庚金日主后，候选账本与反证能否一起闭合？",
    question=(
        "两盘保持食伤生财、食伤制官与财生官杀三个候选不变；合法时柱从壬午"
        "变为甲申后，检查模型能否重做无根／有根判型、只选两张不同机制、精确"
        "排除剩余一张，并写出真正能够推翻每项判断与主次选择的条件。"
    ),
    inference_scope="WHOLE_CHART_DECISION_DISCIPLINE_WITH_FULL_HOUR_COLLATERAL",
    inference_limit=(
        "完整时柱同时改变时干、全部藏干、来源载体、印星位置、同支成员关系与起运"
        "边界；本实验只检验整盘响应、候选账本和反证自洽，不预选机制胜者，也不把"
        "任何结论单独归因于申中庚根。"
    ),
    known_collateral_deltas=(
        "前三柱固定为乙亥、壬午、庚辰；两盘均有相同的三张机制候选",
        "时干由壬食神变为甲偏财，输出与财富的明透载体同时变化",
        "时支藏干由午中丁己变为申中庚壬戊，根、输出与印载体同时变化",
        "A 的月支午与时支午有同支成员，B 换申后该成员消失；两盘均无原局六冲或六合",
        "起运边界与岁运坐标同时变化；Timing 保存但不参与本组评分",
    ),
    birth_date=date(1995, 6, 18),
    member_a_time=time(12, 0),
    member_b_time=time(16, 0),
    member_a_pillars=("乙亥", "壬午", "庚辰", "壬午"),
    member_b_pillars=("乙亥", "壬午", "庚辰", "甲申"),
    legal_hour_pillar_change="壬午 → 甲申",
)

SYNTHETIC_EXPERIMENTS: Final = (
    FIRST_SYNTHETIC_EXPERIMENT,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT,
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT,
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT,
)
SYNTHETIC_EXPERIMENT_BY_REF: Final = {item.experiment_ref: item for item in SYNTHETIC_EXPERIMENTS}
FIRST_SYNTHETIC_EXPERIMENT_REF: Final = FIRST_SYNTHETIC_EXPERIMENT.experiment_ref
FIRST_SYNTHETIC_EXPERIMENT_MEMBERS: Final = FIRST_SYNTHETIC_EXPERIMENT.members
ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF: Final = ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.experiment_ref
ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_MEMBERS: Final = ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.members
HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF: Final = (
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT.experiment_ref
)
HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF: Final = (
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT.experiment_ref
)
HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF: Final = (
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT.experiment_ref
)
REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF: Final = (
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT.experiment_ref
)
CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF: Final = (
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT.experiment_ref
)
SYNTHETIC_MEMBER_BY_SUBJECT: Final = {
    item.subject_id: item for experiment in SYNTHETIC_EXPERIMENTS for item in experiment.members
}
SYNTHETIC_MEMBER_BY_CASE: Final = {
    item.case_ref: item for experiment in SYNTHETIC_EXPERIMENTS for item in experiment.members
}
SYNTHETIC_RESEARCH_CASE_REFS: Final = frozenset(SYNTHETIC_MEMBER_BY_CASE)
SYNTHETIC_EXPERIMENT_ANALYSIS_DATE: Final = FIRST_SYNTHETIC_EXPERIMENT.analysis_date
SYNTHETIC_MEMBER_BY_VARIANT: Final = FIRST_SYNTHETIC_EXPERIMENT.member_by_variant


def resolve_synthetic_experiment(experiment_ref: str) -> SyntheticExperimentDefinition:
    try:
        return SYNTHETIC_EXPERIMENT_BY_REF[experiment_ref]
    except KeyError as exc:
        raise ValueError("mingli_synthetic_experiment_not_found") from exc


def resolve_research_stage_subject(subject_id: str) -> MingliResearchStageBinding | None:
    member = SYNTHETIC_MEMBER_BY_SUBJECT.get(subject_id)
    if member is None:
        return None
    return MingliResearchStageBinding(
        account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
        case_ref=member.case_ref,
        display_name=member.display_name,
    )


def synthetic_experiment_public_definition(
    experiment_ref: str = FIRST_SYNTHETIC_EXPERIMENT_REF,
) -> dict[str, object]:
    return resolve_synthetic_experiment(experiment_ref).public_definition()


def synthetic_experiment_public_definitions() -> tuple[dict[str, object], ...]:
    return tuple(item.public_definition() for item in SYNTHETIC_EXPERIMENTS)
