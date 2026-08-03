from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from abu_v60.mingli.synthetic_experiment_catalog import (
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF,
    resolve_synthetic_experiment,
)
from abu_v60.provenance import content_hash, stable_ref

SYNTHETIC_SUITE_CATALOG_VERSION: Final = "v60.mingli-synthetic-suite-catalog.004"
SYNTHETIC_SUITE_DEFINITION_VERSION: Final = "v60.mingli-synthetic-suite-definition.001"
SYNTHETIC_SUITE_RUNNER_VERSION: Final = "v60.mingli-synthetic-suite-runner.002"

SyntheticSuiteMode = Literal["DEV", "QUALIFICATION", "HOLDOUT"]
SyntheticSuiteAvailability = Literal["ACTIVE", "LOCKED_OWNER_GATE"]


@dataclass(frozen=True, slots=True)
class SyntheticSuiteDefinition:
    suite_ref: str
    mode: SyntheticSuiteMode
    availability: SyntheticSuiteAvailability
    title: str
    question: str
    experiment_refs: tuple[str, ...]
    execution_policy: str
    inference_limit: str

    def public_definition(self) -> dict[str, object]:
        experiments = tuple(
            resolve_synthetic_experiment(experiment_ref).public_definition()
            for experiment_ref in self.experiment_refs
        )
        identity = {
            "suite_definition_version": SYNTHETIC_SUITE_DEFINITION_VERSION,
            "suite_ref": self.suite_ref,
            "mode": self.mode,
            "availability": self.availability,
            "title": self.title,
            "question": self.question,
            "experiment_refs": self.experiment_refs,
            "experiment_definition_hashes": tuple(
                {
                    "experiment_ref": item["experiment_ref"],
                    "definition_hash": item["definition_hash"],
                }
                for item in experiments
            ),
            "execution_policy": self.execution_policy,
            "inference_limit": self.inference_limit,
        }
        return {**identity, "suite_definition_hash": content_hash(identity)}


def _suite(
    *,
    mode: SyntheticSuiteMode,
    availability: SyntheticSuiteAvailability,
    title: str,
    question: str,
    experiment_refs: tuple[str, ...],
    execution_policy: str,
    inference_limit: str,
) -> SyntheticSuiteDefinition:
    if not experiment_refs or len(experiment_refs) != len(set(experiment_refs)):
        raise ValueError("mingli_synthetic_suite_experiments_invalid")
    identity = {
        "suite_definition_version": SYNTHETIC_SUITE_DEFINITION_VERSION,
        "mode": mode,
        "availability": availability,
        "title": title,
        "question": question,
        "experiment_refs": experiment_refs,
        "experiment_definition_hashes": tuple(
            {
                "experiment_ref": experiment_ref,
                "definition_hash": resolve_synthetic_experiment(experiment_ref).public_definition()[
                    "definition_hash"
                ],
            }
            for experiment_ref in experiment_refs
        ),
        "execution_policy": execution_policy,
        "inference_limit": inference_limit,
    }
    suite_ref = stable_ref("v60-mingli-synthetic-suite", identity)
    return SyntheticSuiteDefinition(
        suite_ref=suite_ref,
        mode=mode,
        availability=availability,
        title=title,
        question=question,
        experiment_refs=experiment_refs,
        execution_policy=execution_policy,
        inference_limit=inference_limit,
    )


HIDDEN_RANK_DEV_SUITE: Final = _suite(
    mode="DEV",
    availability="ACTIVE",
    title="藏干位阶训练 · 第一至第三藏干",
    question=(
        "同一个乙木根候选处在第一、第二、第三藏干时，系统与候选模型能否准确保存"
        "位置事实、执行最低门，并避免把较后位阶自动判成无根？"
    ),
    experiment_refs=(
        HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    ),
    execution_policy="SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL",
    inference_limit=(
        "Suite 只汇总两个 DEV 实验；模型失败不等于执行失败，批次结果不自动发布"
        "方法、Gold、Prompt 或正式命理结论。"
    ),
)

HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE: Final = _suite(
    mode="DEV",
    availability="ACTIVE",
    title="藏干位阶泛化 · 丙火陌生命盘",
    question=(
        "换成从未进入训练目录的丙火命盘后，模型能否把同一套第一／第二藏干方法"
        "正确迁移，而不是复述乙木旧样本？"
    ),
    experiment_refs=(HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,),
    execution_policy="SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL",
    inference_limit=(
        "本 Suite 是 DEV 泛化检查，只能发现当前候选是否套用旧盘捷径；"
        "一次通过不解锁 Qualification、HOLDOUT 或正式模型能力声明。"
    ),
)

REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE: Final = _suite(
    mode="DEV",
    availability="ACTIVE",
    title="整盘判型与主路径泛化 · 戊土陌生命盘",
    question=(
        "从无根无比无印的辛酉时切换到戌中戊土最低有效根与丁印同时出现的壬戌时，"
        "模型能否重做判型、候选覆盖、主次裁决与主路径绑定？"
    ),
    experiment_refs=(REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF,),
    execution_policy="SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL",
    inference_limit=(
        "本 Suite 只做 DEV 盲测；完整时柱有伴随变化，Gold 不指定哪张机制卡必须胜出，"
        "一次通过不解锁 Qualification、HOLDOUT 或正式能力声明。"
    ),
)

CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE: Final = _suite(
    mode="DEV",
    availability="ACTIVE",
    title="整盘决策纪律泛化 · 庚金三候选",
    question=(
        "换成全新的庚金命盘，且 A／B 始终保留三张机制候选后，模型能否执行正确"
        "判型出口、闭合候选账本，并写出能够真正翻转逐项裁决与主次选择的反证？"
    ),
    experiment_refs=(CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF,),
    execution_policy="SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL",
    inference_limit=(
        "本 Suite 只做 DEV 盲测；Gold 不指定机制胜者，完整时柱存在多项伴随变化。"
        "一次通过不解锁 Qualification、HOLDOUT 或正式高级命理师能力声明。"
    ),
)

SYNTHETIC_SUITES: Final = (
    HIDDEN_RANK_DEV_SUITE,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE,
    REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE,
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE,
)
SYNTHETIC_SUITE_BY_REF: Final = {item.suite_ref: item for item in SYNTHETIC_SUITES}
HIDDEN_RANK_DEV_SUITE_REF: Final = HIDDEN_RANK_DEV_SUITE.suite_ref
HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE_REF: Final = (
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE.suite_ref
)
REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE_REF: Final = (
    REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE.suite_ref
)
CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE_REF: Final = (
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE.suite_ref
)

SYNTHETIC_SUITE_MODE_CATALOG: Final = (
    {
        "mode": "DEV",
        "availability": "ACTIVE",
        "description": "用于发现方法与错误；结果只进入研发复核。",
    },
    {
        "mode": "QUALIFICATION",
        "availability": "LOCKED_OWNER_GATE",
        "description": "待冻结方法与整组盲评合同后由 Owner 开启。",
    },
    {
        "mode": "HOLDOUT",
        "availability": "LOCKED_OWNER_GATE",
        "description": "待建立物理隔离的盲跑与揭晓链路后由 Owner 开启。",
    },
)


def resolve_synthetic_suite(suite_ref: str) -> SyntheticSuiteDefinition:
    try:
        return SYNTHETIC_SUITE_BY_REF[suite_ref]
    except KeyError as exc:
        raise ValueError("mingli_synthetic_suite_not_found") from exc
