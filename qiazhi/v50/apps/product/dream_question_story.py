from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from typing import Any, Iterable, Mapping

from experience.canonical_scene import CanonicalScene
from experience.dream_game import (
    DreamFlowerRevealPolicy,
    DreamLearningQuestion,
    DreamLearningQuestionOption,
    DreamQuestionContentState,
    DreamQuestionDependencyEdge,
    DreamQuestionSet,
    DreamQuestionStoryScript,
    HypothesisNodeOption,
    HypothesisRelationOption,
    ImmutableDreamSourceSnapshot,
    OutcomeOptionId,
    ProblemQuestionRecord,
)


QUESTION_STORY_ENGINE_VERSION = "abu-life-tree-question-story-engine.v1"
QUESTION_BUNDLE_VALIDATOR_VERSION = "dream-question-bundle-validator.v1"
STORY_SCRIPT_VERSION = "dream-story-script-bank.v1"

ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")
ELEMENT_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
HEAVENLY_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")


class QuestionStoryError(ValueError):
    pass


@dataclass(frozen=True)
class KnowledgeAtomSpec:
    atom_ref: str
    version: str
    title: str
    authoritative_inputs: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class QuestionPatternSpec:
    pattern_ref: str
    organ_role: str
    purpose: str
    answer_type: str = "single_choice"


@dataclass(frozen=True)
class StoryScriptSpec:
    script_ref: DreamQuestionStoryScript
    title: str
    scene_reason: str
    abu_prompt: str
    completion_line: str


@dataclass(frozen=True)
class GoldenBundleSpec:
    spec_ref: str
    story_script_ref: DreamQuestionStoryScript
    variant_ref: str
    target_lens: str
    reveal_policy: DreamFlowerRevealPolicy
    required_capability: str


@dataclass(frozen=True)
class RealityRevealTarget:
    target_ref: str
    question_text: str
    known_context: tuple[str, ...]
    outcome_window_start: datetime
    outcome_window_end: datetime
    outcome_options: Mapping[OutcomeOptionId, str]
    resolution_criteria: tuple[str, ...]
    disconfirmation_definition: str
    resolved_option_id: OutcomeOptionId
    evidence_refs: tuple[str, ...]
    outcome_summary: str
    clock_domain: str = "reality.evidence_ledger"


@dataclass(frozen=True)
class FlowerTruth:
    selected_outcome_option_id: OutcomeOptionId
    summary: str
    truth_ref: str
    evidence_refs: tuple[str, ...]
    formal_path_assertion_refs: tuple[str, ...] = ()
    candidate_path_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompiledQuestionStory:
    spec: GoldenBundleSpec
    flower_question: ProblemQuestionRecord
    flower_truth: FlowerTruth
    question_bundle: DreamQuestionSet


@dataclass(frozen=True)
class BundleValidationResult:
    issue_codes: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.issue_codes


@dataclass(frozen=True)
class _Choice:
    value: str
    label: str
    answer_ref_kind: str = "none"
    answer_ref: str = ""


KNOWLEDGE_ATOM_BANK: dict[str, KnowledgeAtomSpec] = {
    "bazi.visible-stem-element.v1": KnowledgeAtomSpec(
        atom_ref="bazi.visible-stem-element.v1",
        version="v1",
        title="可见天干五行",
        authoritative_inputs=("AllowedChartFact.stem", "AllowedChartFact.stem_element"),
        explanation="天干的五行类别由冻结四柱事实直接读取。",
    ),
    "bazi.branch-primary-element.v1": KnowledgeAtomSpec(
        atom_ref="bazi.branch-primary-element.v1",
        version="v1",
        title="地支主五行",
        authoritative_inputs=("AllowedChartFact.branch", "AllowedChartFact.branch_element"),
        explanation="地支主五行由冻结四柱事实读取，不代替藏干与通根判断。",
    ),
    "bazi.five-element-support-direction.v1": KnowledgeAtomSpec(
        atom_ref="bazi.five-element-support-direction.v1",
        version="v1",
        title="五行同类与生扶方向",
        authoritative_inputs=("two element categories",),
        explanation="这里只比较五行类别方向，不升级为 effective 关系或做功路径。",
    ),
    "bazi.canonical-path-membership.v1": KnowledgeAtomSpec(
        atom_ref="bazi.canonical-path-membership.v1",
        version="v1",
        title="正式路径成员",
        authoritative_inputs=("CanonicalPathAssertionView",),
        explanation="路径节点和分段只能来自冻结的正式 PathAssertion。",
    ),
    "bazi.canonical-path-validation.v1": KnowledgeAtomSpec(
        atom_ref="bazi.canonical-path-validation.v1",
        version="v1",
        title="路径连续性与分段验证",
        authoritative_inputs=(
            "CanonicalPathAssertionView.node_refs",
            "CanonicalPathAssertionView.relation_refs",
        ),
        explanation="主脉判断必须同时检查节点连续性与每段正式关系。",
    ),
    "bazi.temporal-pillar.v1": KnowledgeAtomSpec(
        atom_ref="bazi.temporal-pillar.v1",
        version="v1",
        title="时序柱",
        authoritative_inputs=("CanonicalTemporalState",),
        explanation="大运或流年只提供时序上下文，不能自动证明实际生效。",
    ),
    "bazi.temporal-natal-comparison.v1": KnowledgeAtomSpec(
        atom_ref="bazi.temporal-natal-comparison.v1",
        version="v1",
        title="原局与时序比较",
        authoritative_inputs=("CanonicalTemporalState", "AllowedChartFact"),
        explanation="判断时序变化时，需要把时序层与原局锚点放在同一框架内比较。",
    ),
}

QUESTION_PATTERN_BANK: dict[str, QuestionPatternSpec] = {
    "pattern.observe-authoritative-fact.v1": QuestionPatternSpec(
        pattern_ref="pattern.observe-authoritative-fact.v1",
        organ_role="OBSERVATION_LEAF",
        purpose="识别冻结快照中的一个确定结构事实。",
    ),
    "pattern.apply-related-rule.v1": QuestionPatternSpec(
        pattern_ref="pattern.apply-related-rule.v1",
        organ_role="RULE_LEAF",
        purpose="识别与花题有关、但不直接暴露花题结论的规则证据。",
    ),
    "pattern.build-comparison-framework.v1": QuestionPatternSpec(
        pattern_ref="pattern.build-comparison-framework.v1",
        organ_role="TRUNK_FRAMEWORK",
        purpose="同时使用两片叶的证据建立比较框架，不选择最终胜出项。",
    ),
}

STORY_SCRIPT_BANK: dict[DreamQuestionStoryScript, StoryScriptSpec] = {
    "RECOGNIZE_THIS_TREE": StoryScriptSpec(
        script_ref="RECOGNIZE_THIS_TREE",
        title="识得此树",
        scene_reason="先辨认两处确定结构，再看它们如何进入同一比较。",
        abu_prompt="先看清两片叶各自从哪里长出来。",
        completion_line="两处证据已经接到同一段树干上。",
    ),
    "FIND_MAIN_TRUNK": StoryScriptSpec(
        script_ref="FIND_MAIN_TRUNK",
        title="找到主脉",
        scene_reason="沿正式节点与关系分段，辨认一条路径是否完整。",
        abu_prompt="别急着猜终点，先核对节点和中间那一段。",
        completion_line="主脉的比较框架已经建立，胜出仍留给花来回答。",
    ),
    "SEASONAL_VARIATION": StoryScriptSpec(
        script_ref="SEASONAL_VARIATION",
        title="季候变奏",
        scene_reason="把原局锚点与冻结时序放在一起，观察变化是否得到支持。",
        abu_prompt="先分清原来的树，再看这一季带来了什么。",
        completion_line="原局与时序已经放进同一幅比较里。",
    ),
}

GOLDEN_QUESTION_BUNDLE_SPECS: tuple[GoldenBundleSpec, ...] = (
    GoldenBundleSpec(
        "golden.recognize.day-month.v1",
        "RECOGNIZE_THIS_TREE",
        "day-stem__month-branch",
        "five_element",
        "ASSERTION_REVEAL",
        "chart_facts",
    ),
    GoldenBundleSpec(
        "golden.recognize.day-year.v1",
        "RECOGNIZE_THIS_TREE",
        "day-stem__year-stem",
        "five_element",
        "ASSERTION_REVEAL",
        "chart_facts",
    ),
    GoldenBundleSpec(
        "golden.recognize.day-hour.v1",
        "RECOGNIZE_THIS_TREE",
        "day-stem__hour-stem",
        "five_element",
        "ASSERTION_REVEAL",
        "chart_facts",
    ),
    GoldenBundleSpec(
        "golden.recognize.month-day.v1",
        "RECOGNIZE_THIS_TREE",
        "month-stem__day-stem",
        "five_element",
        "ASSERTION_REVEAL",
        "chart_facts",
    ),
    GoldenBundleSpec(
        "golden.main-trunk.head.v1",
        "FIND_MAIN_TRUNK",
        "path-head",
        "work_path",
        "ASSERTION_REVEAL",
        "committed_path",
    ),
    GoldenBundleSpec(
        "golden.main-trunk.tail.v1",
        "FIND_MAIN_TRUNK",
        "path-tail",
        "work_path",
        "ASSERTION_REVEAL",
        "committed_path",
    ),
    GoldenBundleSpec(
        "golden.main-trunk.bridge.v1",
        "FIND_MAIN_TRUNK",
        "path-bridge",
        "work_path",
        "ASSERTION_REVEAL",
        "committed_path",
    ),
    GoldenBundleSpec(
        "golden.main-trunk.competition.v1",
        "FIND_MAIN_TRUNK",
        "path-competition",
        "work_path",
        "ASSERTION_REVEAL",
        "committed_path",
    ),
    GoldenBundleSpec(
        "golden.season.annual-assertion.v1",
        "SEASONAL_VARIATION",
        "annual-assertion",
        "timing",
        "ASSERTION_REVEAL",
        "annual_timing",
    ),
    GoldenBundleSpec(
        "golden.season.luck-assertion.v1",
        "SEASONAL_VARIATION",
        "luck-assertion",
        "timing",
        "ASSERTION_REVEAL",
        "luck_timing",
    ),
    GoldenBundleSpec(
        "golden.season.annual-reality.v1",
        "SEASONAL_VARIATION",
        "annual-reality",
        "timing",
        "REALITY_REVEAL",
        "annual_reality",
    ),
    GoldenBundleSpec(
        "golden.season.luck-reality.v1",
        "SEASONAL_VARIATION",
        "luck-reality",
        "timing",
        "REALITY_REVEAL",
        "luck_reality",
    ),
)


def select_active_bundle_spec(
    *,
    scene: CanonicalScene,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
) -> GoldenBundleSpec:
    candidates = [
        spec
        for spec in GOLDEN_QUESTION_BUNDLE_SPECS
        if spec.reveal_policy == "ASSERTION_REVEAL"
        and _supports_spec(
            spec,
            scene=scene,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
            reality_target=None,
        )
    ]
    if not candidates:
        raise QuestionStoryError("dream_question_story_no_qualified_bundle")
    ranked = sorted(
        candidates,
        key=lambda item: _hash({
            "scene_source_hash": scene.identity.source_hash,
            "spec_ref": item.spec_ref,
        }),
    )
    return ranked[0]


def compile_flower_for_spec(
    *,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    cutoff_at: datetime,
    reality_target: RealityRevealTarget | None = None,
) -> tuple[ProblemQuestionRecord, FlowerTruth]:
    if spec.story_script_ref == "RECOGNIZE_THIS_TREE":
        return _recognize_flower(scene=scene, spec=spec, cutoff_at=cutoff_at)
    if spec.story_script_ref == "FIND_MAIN_TRUNK":
        return _path_flower(scene=scene, spec=spec, cutoff_at=cutoff_at)
    return _season_flower(
        scene=scene,
        spec=spec,
        cutoff_at=cutoff_at,
        reality_target=reality_target,
    )


def compile_question_bundle(
    *,
    round_id: str,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
    spec: GoldenBundleSpec,
    content_status: DreamQuestionContentState,
    expected_flower_question: ProblemQuestionRecord | None = None,
    reality_target: RealityRevealTarget | None = None,
) -> CompiledQuestionStory:
    if not _supports_spec(
        spec,
        scene=scene,
        allowed_nodes=allowed_nodes,
        allowed_relations=allowed_relations,
        reality_target=reality_target,
    ):
        raise QuestionStoryError(f"dream_question_story_spec_not_supported:{spec.spec_ref}")
    flower_question, flower_truth = compile_flower_for_spec(
        scene=scene,
        spec=spec,
        cutoff_at=snapshot.cutoff_at,
        reality_target=reality_target,
    )
    if expected_flower_question is not None and (
        expected_flower_question.question_id != flower_question.question_id
        or expected_flower_question.question_version != flower_question.question_version
        or expected_flower_question.neutral_question_text
        != flower_question.neutral_question_text
        or expected_flower_question.outcome_options != flower_question.outcome_options
    ):
        raise QuestionStoryError("dream_question_story_flower_binding_mismatch")

    if spec.story_script_ref == "RECOGNIZE_THIS_TREE":
        questions = _recognize_questions(
            snapshot=snapshot,
            scene=scene,
            spec=spec,
        )
    elif spec.story_script_ref == "FIND_MAIN_TRUNK":
        questions = _path_questions(
            snapshot=snapshot,
            scene=scene,
            spec=spec,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
        )
    else:
        questions = _season_questions(
            snapshot=snapshot,
            scene=scene,
            spec=spec,
        )

    first, second, trunk = questions
    bundle_id = (
        "dream-question-bundle-"
        + _hash({
            "round_id": round_id,
            "snapshot_id": snapshot.source_snapshot_id,
            "spec_ref": spec.spec_ref,
            "engine": QUESTION_STORY_ENGINE_VERSION,
        })[:40]
    )
    dependency_edges = [
        DreamQuestionDependencyEdge(
            source_question_id=first.question_id,
            target_question_id=trunk.question_id,
            dependency_kind="EVIDENCE_REQUIRED",
        ),
        DreamQuestionDependencyEdge(
            source_question_id=second.question_id,
            target_question_id=trunk.question_id,
            dependency_kind="EVIDENCE_REQUIRED",
        ),
        DreamQuestionDependencyEdge(
            source_question_id=trunk.question_id,
            target_question_id=flower_question.question_id,
            dependency_kind="FRAMEWORK_REQUIRED",
        ),
    ]
    payload: dict[str, Any] = {
        "question_set_id": bundle_id,
        "round_id": round_id,
        "source_snapshot_id": snapshot.source_snapshot_id,
        "cutoff_at": snapshot.cutoff_at,
        "source_version": snapshot.source_scene_version,
        "source_hash": snapshot.source_hash,
        "question_set_version": QUESTION_STORY_ENGINE_VERSION,
        "questions": questions,
        "domain": "BAZI",
        "content_status": content_status,
        "story_script_ref": spec.story_script_ref,
        "target_lens": spec.target_lens,
        "flower_question_id": flower_question.question_id,
        "flower_target_ref": flower_truth.truth_ref,
        "reveal_policy": spec.reveal_policy,
        "evidence_requirements": sorted({
            *first.evidence_refs,
            *second.evidence_refs,
        }),
        "truth_refs": sorted({
            first.truth_ref,
            second.truth_ref,
            trunk.truth_ref,
            flower_truth.truth_ref,
        }),
        "dependency_edges": dependency_edges,
        "story_script_version": STORY_SCRIPT_VERSION,
        "bundle_validator_version": QUESTION_BUNDLE_VALIDATOR_VERSION,
        "immutable_hash": "0" * 64,
    }
    payload["immutable_hash"] = _immutable_hash(payload)
    bundle = DreamQuestionSet.model_validate(payload)
    validation = validate_question_bundle(bundle, flower_question=flower_question)
    if not validation.passed:
        raise QuestionStoryError(
            "dream_question_story_bundle_invalid:" + ",".join(validation.issue_codes)
        )
    return CompiledQuestionStory(
        spec=spec,
        flower_question=flower_question,
        flower_truth=flower_truth,
        question_bundle=bundle,
    )


def compile_active_question_story(
    *,
    round_id: str,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
    expected_flower_question: ProblemQuestionRecord | None = None,
) -> CompiledQuestionStory:
    spec = select_active_bundle_spec(
        scene=scene,
        allowed_nodes=allowed_nodes,
        allowed_relations=allowed_relations,
    )
    return compile_question_bundle(
        round_id=round_id,
        snapshot=snapshot,
        scene=scene,
        allowed_nodes=allowed_nodes,
        allowed_relations=allowed_relations,
        spec=spec,
        content_status="ACTIVE",
        expected_flower_question=expected_flower_question,
    )


def compile_golden_question_catalog(
    *,
    round_id_prefix: str,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
    reality_target: RealityRevealTarget,
) -> list[CompiledQuestionStory]:
    compiled: list[CompiledQuestionStory] = []
    unsupported: list[str] = []
    for index, spec in enumerate(GOLDEN_QUESTION_BUNDLE_SPECS, start=1):
        if not _supports_spec(
            spec,
            scene=scene,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
            reality_target=reality_target,
        ):
            unsupported.append(spec.spec_ref)
            continue
        compiled.append(compile_question_bundle(
            round_id=f"{round_id_prefix}-{index:02d}",
            snapshot=snapshot,
            scene=scene,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
            spec=spec,
            content_status="GOLDEN",
            reality_target=reality_target,
        ))
    if unsupported:
        raise QuestionStoryError(
            "dream_question_story_golden_catalog_incomplete:" + ",".join(unsupported)
        )
    return compiled


def validate_question_bundle(
    bundle: DreamQuestionSet | Mapping[str, Any],
    *,
    flower_question: ProblemQuestionRecord | None = None,
) -> BundleValidationResult:
    raw = (
        bundle.model_dump(mode="json")
        if isinstance(bundle, DreamQuestionSet)
        else dict(bundle)
    )
    issues: list[str] = []
    questions = [
        item if isinstance(item, Mapping) else {}
        for item in raw.get("questions", [])
    ]
    by_kind = {str(item.get("kind")): item for item in questions}
    required_kinds = {
        "LEAF_BASIC_01",
        "LEAF_BASIC_02",
        "TRUNK_BACKBONE_01",
    }
    if set(by_kind) != required_kinds:
        issues.append("required_organs_missing")
        return BundleValidationResult(tuple(issues))

    first = by_kind["LEAF_BASIC_01"]
    second = by_kind["LEAF_BASIC_02"]
    trunk = by_kind["TRUNK_BACKBONE_01"]
    first_id = str(first.get("question_id") or "")
    second_id = str(second.get("question_id") or "")
    trunk_id = str(trunk.get("question_id") or "")
    flower_id = str(raw.get("flower_question_id") or "")
    if set(trunk.get("depends_on") or []) != {first_id, second_id}:
        issues.append("trunk_dependencies_incomplete")
    first_evidence = set(first.get("evidence_refs") or [])
    second_evidence = set(second.get("evidence_refs") or [])
    trunk_evidence = set(trunk.get("evidence_refs") or [])
    if not first_evidence or not second_evidence:
        issues.append("leaf_evidence_missing")
    if first_evidence & second_evidence:
        issues.append("leaf_evidence_not_distinct")
    if not (first_evidence | second_evidence).issubset(trunk_evidence):
        issues.append("trunk_evidence_gap")

    edges = {
        (
            str(item.get("source_question_id") or ""),
            str(item.get("target_question_id") or ""),
            str(item.get("dependency_kind") or ""),
        )
        for item in raw.get("dependency_edges", [])
        if isinstance(item, Mapping)
    }
    expected_edges = {
        (first_id, trunk_id, "EVIDENCE_REQUIRED"),
        (second_id, trunk_id, "EVIDENCE_REQUIRED"),
        (trunk_id, flower_id, "FRAMEWORK_REQUIRED"),
    }
    if not expected_edges.issubset(edges):
        issues.append("dependency_graph_incomplete")

    target_lens = raw.get("target_lens")
    reveal_policy = raw.get("reveal_policy")
    flower_target_ref = str(raw.get("flower_target_ref") or "")
    for item in (first, second, trunk):
        options = item.get("options") or []
        if not 2 <= len(options) <= 4:
            issues.append("question_option_count_invalid")
        if item.get("target_lens") != target_lens:
            issues.append("question_lens_mismatch")
        if item.get("reveal_policy") != reveal_policy:
            issues.append("question_reveal_policy_mismatch")
        if not item.get("truth_ref") or not item.get("evidence_refs"):
            issues.append("question_truth_trace_missing")
        if item.get("truth_ref") == flower_target_ref:
            issues.append("flower_answer_leaked_by_prerequisite")
        if flower_target_ref in set(item.get("evidence_refs") or []):
            issues.append("flower_target_exposed_as_prerequisite_evidence")
        correct_option_id = item.get("correct_option_id")
        if correct_option_id not in {
            option.get("option_id")
            for option in options
            if isinstance(option, Mapping)
        }:
            issues.append("question_correct_option_missing")

    if flower_question is not None and flower_question.question_id != flower_id:
        issues.append("flower_question_binding_mismatch")
    if reveal_policy not in {"ASSERTION_REVEAL", "REALITY_REVEAL"}:
        issues.append("flower_reveal_policy_invalid")
    return BundleValidationResult(tuple(dict.fromkeys(issues)))


def validate_prompt_rewrite(
    original: DreamLearningQuestion,
    rewritten: DreamLearningQuestion,
) -> bool:
    return (
        original.question_id == rewritten.question_id
        and original.kind == rewritten.kind
        and original.answer_commitment_hash == rewritten.answer_commitment_hash
        and original.correct_option_id == rewritten.correct_option_id
        and original.evidence_refs == rewritten.evidence_refs
        and original.truth_ref == rewritten.truth_ref
        and [
            (item.option_id, item.answer_ref_kind, item.answer_ref)
            for item in original.options
        ]
        == [
            (item.option_id, item.answer_ref_kind, item.answer_ref)
            for item in rewritten.options
        ]
    )


def _recognize_questions(
    *,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
) -> list[DreamLearningQuestion]:
    left, right = _recognize_fact_pair(scene, spec.variant_ref)
    left_fact, left_component, left_label = left
    right_fact, right_component, right_label = right
    left_value = _fact_element(left_fact, left_component)
    right_value = _fact_element(right_fact, right_component)
    first = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_01",
        organ_role="OBSERVATION_LEAF",
        title="叶片一｜识别结构",
        prompt=f"{left_label}在冻结命盘中属于哪一种五行？",
        choices=_element_choices(left_value),
        correct_value=left_value,
        evidence_refs=[left_fact.fact_ref],
        truth_ref=f"{left_fact.fact_ref}#{left_component}_element",
        knowledge_atom_refs=[
            (
                "bazi.branch-primary-element.v1"
                if left_component == "branch"
                else "bazi.visible-stem-element.v1"
            )
        ],
        question_pattern_ref="pattern.observe-authoritative-fact.v1",
        explanation="这个答案直接来自同一份冻结四柱事实。",
        success_message="这片叶对应的结构事实已经确认。",
        retry_message="回到命盘镜核对这一柱；这里只读取冻结事实。",
    )
    second = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_02",
        organ_role="RULE_LEAF",
        title="叶片二｜补齐证据",
        prompt=f"{right_label}在冻结命盘中属于哪一种五行？",
        choices=_element_choices(right_value),
        correct_value=right_value,
        evidence_refs=[right_fact.fact_ref],
        truth_ref=f"{right_fact.fact_ref}#{right_component}_element",
        knowledge_atom_refs=[
            (
                "bazi.branch-primary-element.v1"
                if right_component == "branch"
                else "bazi.visible-stem-element.v1"
            )
        ],
        question_pattern_ref="pattern.apply-related-rule.v1",
        explanation="第二片叶提供另一项独立证据，不判断花题结论。",
        success_message="第二项必要证据已经确认。",
        retry_message="再核对对应柱位；不要用第一片叶替代这一项证据。",
    )
    pair_value = f"{left_fact.fact_ref}|{right_fact.fact_ref}"
    pair_choices = _comparison_choices(
        correct_value=pair_value,
        correct_label=f"{left_label}与{right_label}",
        scene=scene,
        excluded_refs={left_fact.fact_ref, right_fact.fact_ref},
    )
    trunk = _question(
        snapshot=snapshot,
        spec=spec,
        kind="TRUNK_BACKBONE_01",
        organ_role="TRUNK_FRAMEWORK",
        title="树干｜建立比较",
        prompt="要回答花朵的正式命题，必须把哪两项证据放进同一比较框架？",
        choices=pair_choices,
        correct_value=pair_value,
        evidence_refs=[left_fact.fact_ref, right_fact.fact_ref],
        truth_ref=(
            "comparison:"
            + _hash({"left": left_fact.fact_ref, "right": right_fact.fact_ref})[:32]
        ),
        knowledge_atom_refs=["bazi.five-element-support-direction.v1"],
        question_pattern_ref="pattern.build-comparison-framework.v1",
        explanation="树干只建立比较框架，不提前宣布同类、生扶或制化结论。",
        success_message="两片叶的证据已接到同一段树干上。",
        retry_message="树干需要同时使用两片叶；缺少任何一项都不能进入花题。",
        depends_on=[first.question_id, second.question_id],
        difficulty="INTERMEDIATE",
    )
    return [first, second, trunk]


def _path_questions(
    *,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
) -> list[DreamLearningQuestion]:
    path = _committed_path(scene)
    segment_index = _path_segment_index(path.relation_refs, spec.variant_ref)
    node_index = min(segment_index, len(path.node_refs) - 1)
    node_ref = path.node_refs[node_index]
    relation_ref = path.relation_refs[segment_index]
    node_options = _node_choices(
        correct_ref=node_ref,
        allowed_nodes=allowed_nodes,
    )
    relation_options = _relation_choices(
        correct_ref=relation_ref,
        allowed_relations=allowed_relations,
    )
    first = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_01",
        organ_role="OBSERVATION_LEAF",
        title="叶片一｜路径节点",
        prompt="哪一个正式 NodeRef 位于本轮需要核对的主脉分段？",
        choices=node_options,
        correct_value=node_ref,
        evidence_refs=[node_ref],
        truth_ref=f"path-node-membership:{node_ref}",
        knowledge_atom_refs=["bazi.canonical-path-membership.v1"],
        question_pattern_ref="pattern.observe-authoritative-fact.v1",
        explanation="节点成员来自冻结 PathAssertion，不由前端或文案猜测。",
        success_message="这一处正式路径节点已经确认。",
        retry_message="请在做功镜中核对正式节点；候选或潜在节点不能代替它。",
    )
    second = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_02",
        organ_role="RULE_LEAF",
        title="叶片二｜路径分段",
        prompt="哪一条正式关系属于同一主脉分段？",
        choices=relation_options,
        correct_value=relation_ref,
        evidence_refs=[relation_ref],
        truth_ref=f"path-relation-membership:{relation_ref}",
        knowledge_atom_refs=["bazi.canonical-path-membership.v1"],
        question_pattern_ref="pattern.apply-related-rule.v1",
        explanation="关系分段必须引用冻结的正式 RelationKey。",
        success_message="这一段正式关系已经确认。",
        retry_message="再核对做功镜中的分段；潜在关系不能代替正式关系。",
    )
    trunk = _question(
        snapshot=snapshot,
        spec=spec,
        kind="TRUNK_BACKBONE_01",
        organ_role="TRUNK_FRAMEWORK",
        title="树干｜主脉框架",
        prompt="比较主脉是否成立时，哪一组证据必须同时保留？",
        choices=[
            _Choice("node-and-relation", "节点连续性＋分段关系有效性"),
            _Choice("node-only", "只看节点名称"),
            _Choice("text-only", "只看自然语言描述"),
            _Choice("distance-only", "只看柱位距离"),
        ],
        correct_value="node-and-relation",
        evidence_refs=[node_ref, relation_ref],
        truth_ref=f"path-framework:{path.assertion_ref}:{segment_index}",
        knowledge_atom_refs=["bazi.canonical-path-validation.v1"],
        question_pattern_ref="pattern.build-comparison-framework.v1",
        explanation="树干建立连续性与分段验证框架，但不提前宣布花题胜出项。",
        success_message="节点与关系已经进入同一个主脉比较框架。",
        retry_message="主脉不能只凭节点、距离或自然语言成立。",
        depends_on=[first.question_id, second.question_id],
        difficulty="ADVANCED",
    )
    return [first, second, trunk]


def _season_questions(
    *,
    snapshot: ImmutableDreamSourceSnapshot,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
) -> list[DreamLearningQuestion]:
    pillar, pillar_label = _season_pillar(scene, spec.variant_ref)
    temporal_ref = scene.temporal_state.source_refs[0]
    day_fact = _fact(scene, "day")
    first = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_01",
        organ_role="OBSERVATION_LEAF",
        title="叶片一｜时序来客",
        prompt=f"冻结快照中的{pillar_label}，可见天干是哪一项？",
        choices=_symbol_choices(pillar[0], HEAVENLY_STEMS, "node", temporal_ref),
        correct_value=pillar[0],
        evidence_refs=[temporal_ref],
        truth_ref=f"{temporal_ref}#{pillar_label}-stem",
        knowledge_atom_refs=["bazi.temporal-pillar.v1"],
        question_pattern_ref="pattern.observe-authoritative-fact.v1",
        explanation="时序柱来自冻结 TemporalState，不由当前现实时间重算。",
        success_message="这一季的可见天干已经确认。",
        retry_message="请在时运镜核对冻结时序柱。",
    )
    second = _question(
        snapshot=snapshot,
        spec=spec,
        kind="LEAF_BASIC_02",
        organ_role="RULE_LEAF",
        title="叶片二｜原局锚点",
        prompt="与这一季比较时，原局日主天干属于哪一种五行？",
        choices=_element_choices(day_fact.stem_element),
        correct_value=day_fact.stem_element,
        evidence_refs=[day_fact.fact_ref],
        truth_ref=f"{day_fact.fact_ref}#stem_element",
        knowledge_atom_refs=["bazi.visible-stem-element.v1"],
        question_pattern_ref="pattern.apply-related-rule.v1",
        explanation="时序判断仍须回到原局锚点，不能把时运当作新命盘。",
        success_message="原局比较锚点已经确认。",
        retry_message="回到日柱核对原局日主五行。",
    )
    trunk = _question(
        snapshot=snapshot,
        spec=spec,
        kind="TRUNK_BACKBONE_01",
        organ_role="TRUNK_FRAMEWORK",
        title="树干｜季候比较",
        prompt="判断这一季是否改变主脉时，应使用哪一种比较框架？",
        choices=[
            _Choice("natal-and-timing", f"原局日主＋{pillar_label}时序"),
            _Choice("timing-only", f"只看{pillar_label}"),
            _Choice("natal-only", "只看原局"),
            _Choice("name-only", "只看事件名称"),
        ],
        correct_value="natal-and-timing",
        evidence_refs=[temporal_ref, day_fact.fact_ref],
        truth_ref=f"temporal-framework:{temporal_ref}:{day_fact.fact_ref}",
        knowledge_atom_refs=["bazi.temporal-natal-comparison.v1"],
        question_pattern_ref="pattern.build-comparison-framework.v1",
        explanation="树干只建立原局与时序的比较，不把“出现”自动升级为 effective。",
        success_message="原局与时序已经进入同一比较框架。",
        retry_message="时序变化必须与原局锚点共同判断。",
        depends_on=[first.question_id, second.question_id],
        difficulty="ADVANCED",
    )
    return [first, second, trunk]


def _recognize_flower(
    *,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    cutoff_at: datetime,
) -> tuple[ProblemQuestionRecord, FlowerTruth]:
    left, right = _recognize_fact_pair(scene, spec.variant_ref)
    focus_fact, focus_component, focus_label = left
    context_fact, context_component, context_label = right
    focus = _fact_element(focus_fact, focus_component)
    context = _fact_element(context_fact, context_component)
    supportive = context == focus or ELEMENT_GENERATES[context] == focus
    selected: OutcomeOptionId = "yes" if supportive else "no"
    truth_ref = (
        "derived-five-element-direction:"
        + _hash({
            "focus": f"{focus_fact.fact_ref}:{focus_component}:{focus}",
            "context": f"{context_fact.fact_ref}:{context_component}:{context}",
            "rule": "bazi.five-element-support-direction.v1",
        })[:40]
    )
    question = _flower_question(
        scene=scene,
        spec=spec,
        cutoff_at=cutoff_at,
        neutral_question_text=(
            f"只按冻结的五行类别，{context_label}对{focus_label}"
            "是否构成同类或生扶方向？"
        ),
        known_context=[
            "只比较两项冻结五行类别。",
            "该结论不等于 effective RelationAssertion，也不等于正式做功路径。",
        ],
        outcome_options={
            "yes": "构成同类或生扶方向",
            "no": "不构成同类或生扶方向",
            "partial_or_unclear": "冻结证据不足",
        },
        resolution_criteria=[
            "两者同类，或背景五行生扶焦点五行时为“是”。",
            "其余类别方向为“否”；缺少冻结事实时不得发布题组。",
        ],
        disconfirmation_definition="任一四柱事实或五行类别引用失效时，本题不得揭盲。",
    )
    summary = (
        f"冻结类别中，{context_label}（{ELEMENT_LABELS[context]}）"
        f"{'可以' if supportive else '不能'}按同类或相生方向支持"
        f"{focus_label}（{ELEMENT_LABELS[focus]}）。"
    )
    return question, FlowerTruth(
        selected_outcome_option_id=selected,
        summary=summary,
        truth_ref=truth_ref,
        evidence_refs=(
            focus_fact.fact_ref,
            context_fact.fact_ref,
            "bazi.five-element-support-direction.v1",
        ),
    )


def _path_flower(
    *,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    cutoff_at: datetime,
) -> tuple[ProblemQuestionRecord, FlowerTruth]:
    committed = [
        item for item in scene.path_assertions if item.status == "committed"
    ]
    legacy = [
        item for item in scene.path_assertions if item.status == "legacy_unresolved"
    ]
    if committed:
        selected: OutcomeOptionId = "yes"
        summary = "冻结快照中存在可验证、可投影的 committed PathAssertion。"
        truth_ref = committed[0].assertion_ref
    elif legacy:
        selected = "partial_or_unclear"
        summary = "冻结快照中只有 legacy_unresolved 路径记录，不能作为正式主脉。"
        truth_ref = legacy[0].assertion_ref
    else:
        selected = "no"
        summary = "冻结快照中当前暂无已确认主路径。"
        truth_ref = f"path-status:{scene.identity.source_hash}"
    question = _flower_question(
        scene=scene,
        spec=spec,
        cutoff_at=cutoff_at,
        neutral_question_text="沿刚才建立的节点与分段框架，这条候选主脉是否已正式提交？",
        known_context=[
            "NodeRef 与 RelationKey 只能来自冻结 CanonicalScene。",
            "自然语言描述、候选路径和 legacy_unresolved 均不等于 committed。",
        ],
        outcome_options={
            "yes": "已形成 committed PathAssertion",
            "no": "当前暂无已确认主路径",
            "partial_or_unclear": "只有 legacy_unresolved 路径记录",
        },
        resolution_criteria=[
            "存在 committed PathAssertion 时为“是”。",
            "只有 legacy_unresolved 时为“部分或不确定”。",
            "两者均不存在时为“否”。",
        ],
        disconfirmation_definition="路径状态、节点或分段引用失效时，本题不得揭盲。",
    )
    return question, FlowerTruth(
        selected_outcome_option_id=selected,
        summary=summary,
        truth_ref=truth_ref,
        evidence_refs=tuple(
            item.assertion_ref for item in [*committed, *legacy]
        ) or (f"source_snapshot:{scene.identity.source_hash}",),
        formal_path_assertion_refs=tuple(item.assertion_ref for item in committed),
        candidate_path_refs=tuple(item.assertion_ref for item in legacy),
    )


def _season_flower(
    *,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    cutoff_at: datetime,
    reality_target: RealityRevealTarget | None,
) -> tuple[ProblemQuestionRecord, FlowerTruth]:
    if spec.reveal_policy == "REALITY_REVEAL":
        if reality_target is None:
            raise QuestionStoryError("dream_question_story_reality_target_required")
        question = _flower_question(
            scene=scene,
            spec=spec,
            cutoff_at=cutoff_at,
            neutral_question_text=reality_target.question_text,
            known_context=list(reality_target.known_context),
            outcome_options=dict(reality_target.outcome_options),
            resolution_criteria=list(reality_target.resolution_criteria),
            disconfirmation_definition=reality_target.disconfirmation_definition,
            outcome_window_start=reality_target.outcome_window_start,
            outcome_window_end=reality_target.outcome_window_end,
            clock_domain=reality_target.clock_domain,
        )
        return question, FlowerTruth(
            selected_outcome_option_id=reality_target.resolved_option_id,
            summary=reality_target.outcome_summary,
            truth_ref=reality_target.target_ref,
            evidence_refs=reality_target.evidence_refs,
        )

    temporal = scene.temporal_state
    selected: OutcomeOptionId = (
        "yes"
        if temporal.publicly_supported
        else "partial_or_unclear"
        if temporal.source_refs
        else "no"
    )
    truth_ref = (
        "temporal-public-support:"
        + _hash({
            "scene": scene.identity.source_hash,
            "source_refs": temporal.source_refs,
            "publicly_supported": temporal.publicly_supported,
            "validation_status": temporal.validation_status,
        })[:40]
    )
    question = _flower_question(
        scene=scene,
        spec=spec,
        cutoff_at=cutoff_at,
        neutral_question_text="截至冻结快照，这一时序层是否已有公开支持，可进入主脉变化判断？",
        known_context=[
            "时运出现只提供激活、增强、削弱或阻断的可能。",
            "公开支持不等于自动升级为 effective 关系。",
        ],
        outcome_options={
            "yes": "已有公开支持的时序状态",
            "no": "当前没有可引用的时序状态",
            "partial_or_unclear": "有时序记录，但尚未公开支持",
        },
        resolution_criteria=[
            "TemporalState.publicly_supported=true 时为“是”。",
            "有来源但未公开支持时为“部分或不确定”。",
            "无时序来源时为“否”。",
        ],
        disconfirmation_definition="时序来源、版本或公开支持状态失效时不得揭盲。",
    )
    return question, FlowerTruth(
        selected_outcome_option_id=selected,
        summary=(
            "冻结时序状态"
            + ("已有公开支持。" if selected == "yes" else "尚未形成公开支持。")
        ),
        truth_ref=truth_ref,
        evidence_refs=tuple(temporal.source_refs) or (truth_ref,),
    )


def _flower_question(
    *,
    scene: CanonicalScene,
    spec: GoldenBundleSpec,
    cutoff_at: datetime,
    neutral_question_text: str,
    known_context: list[str],
    outcome_options: Mapping[OutcomeOptionId, str],
    resolution_criteria: list[str],
    disconfirmation_definition: str,
    outcome_window_start: datetime | None = None,
    outcome_window_end: datetime | None = None,
    clock_domain: str = "v50.canonical_scene.source_updated_at",
) -> ProblemQuestionRecord:
    question_id = (
        "dream-story-flower-"
        + _hash({
            "scene": scene.identity.scene_id,
            "source_hash": scene.identity.source_hash,
            "spec_ref": spec.spec_ref,
        })[:32]
    )
    start = outcome_window_start or cutoff_at
    end = outcome_window_end or cutoff_at + timedelta(microseconds=1)
    return ProblemQuestionRecord(
        question_id=question_id,
        question_version=spec.spec_ref,
        subject_label="匿名生命树",
        neutral_question_text=neutral_question_text,
        known_context=known_context,
        knowledge_cutoff=cutoff_at,
        clock_domain=clock_domain,
        outcome_window_start=start,
        outcome_window_end=end,
        outcome_options=dict(outcome_options),
        resolution_criteria=resolution_criteria,
        disconfirmation_definition=disconfirmation_definition,
        liuyao_permitted=False,
    )


def _question(
    *,
    snapshot: ImmutableDreamSourceSnapshot,
    spec: GoldenBundleSpec,
    kind: str,
    organ_role: str,
    title: str,
    prompt: str,
    choices: Iterable[_Choice],
    correct_value: str,
    evidence_refs: list[str],
    truth_ref: str,
    knowledge_atom_refs: list[str],
    question_pattern_ref: str,
    explanation: str,
    success_message: str,
    retry_message: str,
    depends_on: list[str] | None = None,
    difficulty: str = "FOUNDATION",
) -> DreamLearningQuestion:
    choice_list = list(choices)
    if not 2 <= len(choice_list) <= 4:
        raise QuestionStoryError("dream_question_story_option_count_invalid")
    options: list[DreamLearningQuestionOption] = []
    correct_option_id = ""
    for choice in choice_list:
        option_id = (
            "dream-option-"
            + _hash({
                "snapshot": snapshot.source_snapshot_id,
                "spec": spec.spec_ref,
                "kind": kind,
                "choice": choice.value,
            })[:24]
        )
        options.append(DreamLearningQuestionOption(
            option_id=option_id,
            label=choice.label,
            answer_ref_kind=choice.answer_ref_kind,
            answer_ref=choice.answer_ref,
        ))
        if choice.value == correct_value:
            correct_option_id = option_id
    if not correct_option_id:
        raise QuestionStoryError("dream_question_story_correct_option_missing")
    question_id = (
        "dream-learning-question-"
        + _hash({
            "snapshot": snapshot.source_snapshot_id,
            "spec": spec.spec_ref,
            "kind": kind,
        })[:32]
    )
    answer_commitment_hash = _hash({
        "question_id": question_id,
        "source_snapshot_id": snapshot.source_snapshot_id,
        "correct_option_id": correct_option_id,
        "evidence_refs": evidence_refs,
        "truth_ref": truth_ref,
        "option_semantics": [
            {
                "option_id": option.option_id,
                "answer_ref_kind": option.answer_ref_kind,
                "answer_ref": option.answer_ref,
            }
            for option in options
        ],
    })
    payload: dict[str, Any] = {
        "question_id": question_id,
        "kind": kind,
        "title": title,
        "prompt": prompt,
        "target_lens": spec.target_lens,
        "options": options,
        "correct_option_id": correct_option_id,
        "answer_commitment_hash": answer_commitment_hash,
        "evidence_refs": evidence_refs,
        "organ_role": organ_role,
        "depends_on": depends_on or [],
        "truth_ref": truth_ref,
        "knowledge_atom_refs": knowledge_atom_refs,
        "question_pattern_ref": question_pattern_ref,
        "explanation": explanation,
        "difficulty": difficulty,
        "reveal_policy": spec.reveal_policy,
        "success_message": success_message,
        "retry_message": retry_message,
        "immutable_hash": "0" * 64,
    }
    payload["immutable_hash"] = _immutable_hash(payload)
    return DreamLearningQuestion.model_validate(payload)


def _supports_spec(
    spec: GoldenBundleSpec,
    *,
    scene: CanonicalScene,
    allowed_nodes: list[HypothesisNodeOption],
    allowed_relations: list[HypothesisRelationOption],
    reality_target: RealityRevealTarget | None,
) -> bool:
    if spec.required_capability == "chart_facts":
        return len(scene.chart_facts) == 4
    if spec.required_capability == "committed_path":
        try:
            path = _committed_path(scene)
        except QuestionStoryError:
            return False
        return (
            bool(path.node_refs)
            and bool(path.relation_refs)
            and any(item.node_ref in path.node_refs for item in allowed_nodes)
            and any(
                item.relation_ref in path.relation_refs and item.formal
                for item in allowed_relations
            )
        )
    if spec.required_capability == "annual_timing":
        return bool(
            scene.temporal_state.annual_pillar
            and scene.temporal_state.source_refs
        )
    if spec.required_capability == "luck_timing":
        return bool(
            scene.temporal_state.luck_pillar
            and scene.temporal_state.source_refs
        )
    if spec.required_capability == "annual_reality":
        return bool(
            reality_target
            and scene.temporal_state.annual_pillar
            and scene.temporal_state.source_refs
        )
    if spec.required_capability == "luck_reality":
        return bool(
            reality_target
            and scene.temporal_state.luck_pillar
            and scene.temporal_state.source_refs
        )
    return False


def _recognize_fact_pair(scene: CanonicalScene, variant_ref: str):
    selectors = {
        "day-stem__month-branch": (("day", "stem"), ("month", "branch")),
        "day-stem__year-stem": (("day", "stem"), ("year", "stem")),
        "day-stem__hour-stem": (("day", "stem"), ("hour", "stem")),
        "month-stem__day-stem": (("month", "stem"), ("day", "stem")),
    }
    try:
        left, right = selectors[variant_ref]
    except KeyError as exc:
        raise QuestionStoryError("dream_question_story_recognize_variant_invalid") from exc
    return (
        (_fact(scene, left[0]), left[1], _fact_component_label(left[0], left[1])),
        (_fact(scene, right[0]), right[1], _fact_component_label(right[0], right[1])),
    )


def _fact(scene: CanonicalScene, slot: str):
    try:
        return next(item for item in scene.chart_facts if item.pillar_slot == slot)
    except StopIteration as exc:
        raise QuestionStoryError(f"dream_question_story_fact_missing:{slot}") from exc


def _fact_component_label(slot: str, component: str) -> str:
    slot_label = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }[slot]
    return f"{slot_label}{'天干' if component == 'stem' else '地支'}"


def _fact_element(fact, component: str) -> str:
    value = fact.stem_element if component == "stem" else fact.branch_element
    if value not in ELEMENT_LABELS:
        raise QuestionStoryError("dream_question_story_fact_element_missing")
    return value


def _element_choices(correct_value: str) -> list[_Choice]:
    values = [correct_value, *[item for item in ELEMENT_ORDER if item != correct_value][:3]]
    return [_Choice(value=item, label=ELEMENT_LABELS[item]) for item in values]


def _symbol_choices(
    correct_value: str,
    domain: tuple[str, ...],
    answer_ref_kind: str,
    answer_ref: str,
) -> list[_Choice]:
    values = [correct_value, *[item for item in domain if item != correct_value][:3]]
    return [
        _Choice(
            value=item,
            label=item,
            answer_ref_kind=answer_ref_kind if item == correct_value else "none",
            answer_ref=answer_ref if item == correct_value else "",
        )
        for item in values
    ]


def _comparison_choices(
    *,
    correct_value: str,
    correct_label: str,
    scene: CanonicalScene,
    excluded_refs: set[str],
) -> list[_Choice]:
    remaining = [
        item for item in scene.chart_facts if item.fact_ref not in excluded_refs
    ]
    distractors = []
    for index, item in enumerate(remaining[:3], start=1):
        distractors.append(_Choice(
            value=f"distractor-{index}:{item.fact_ref}",
            label=f"{item.pillar_label or item.pillar_slot}与单一文本描述",
        ))
    defaults = [
        _Choice("distance-only", "只比较柱位距离"),
        _Choice("name-only", "只比较干支名称"),
        _Choice("timing-only", "只比较当前现实时间"),
    ]
    return [_Choice(correct_value, correct_label), *(distractors + defaults)[:3]]


def _node_choices(
    *,
    correct_ref: str,
    allowed_nodes: list[HypothesisNodeOption],
) -> list[_Choice]:
    matching = next(
        (item for item in allowed_nodes if item.node_ref == correct_ref),
        None,
    )
    if matching is None:
        raise QuestionStoryError("dream_question_story_path_node_not_disclosed")
    others = [item for item in allowed_nodes if item.node_ref != correct_ref]
    values = [matching, *others[:3]]
    return [
        _Choice(
            value=item.node_ref,
            label=(
                f"{item.pillar_label}·{item.label}"
                if item.pillar_label
                else item.label
            ),
            answer_ref_kind="node" if item.node_ref == correct_ref else "none",
            answer_ref=item.node_ref if item.node_ref == correct_ref else "",
        )
        for item in values
    ]


def _relation_choices(
    *,
    correct_ref: str,
    allowed_relations: list[HypothesisRelationOption],
) -> list[_Choice]:
    matching = next(
        (
            item
            for item in allowed_relations
            if item.relation_ref == correct_ref and item.formal
        ),
        None,
    )
    if matching is None:
        raise QuestionStoryError("dream_question_story_path_relation_not_disclosed")
    others = [
        item for item in allowed_relations
        if item.relation_ref != correct_ref and item.formal
    ]
    choices = [
        _Choice(
            value=matching.relation_ref,
            label=matching.label,
            answer_ref_kind="relation",
            answer_ref=matching.relation_ref,
        ),
        *[
            _Choice(value=item.relation_ref, label=item.label)
            for item in others[:2]
        ],
    ]
    if len(choices) < 2:
        choices.append(_Choice("no-formal-segment", "当前没有可引用的正式分段"))
    return choices[:4]


def _committed_path(scene: CanonicalScene):
    try:
        return next(item for item in scene.path_assertions if item.status == "committed")
    except StopIteration as exc:
        raise QuestionStoryError("dream_question_story_committed_path_missing") from exc


def _path_segment_index(relation_refs: list[str], variant_ref: str) -> int:
    if not relation_refs:
        raise QuestionStoryError("dream_question_story_path_segment_missing")
    if variant_ref == "path-head":
        return 0
    if variant_ref == "path-tail":
        return len(relation_refs) - 1
    if variant_ref == "path-bridge":
        return len(relation_refs) // 2
    if variant_ref == "path-competition":
        return min(1, len(relation_refs) - 1)
    raise QuestionStoryError("dream_question_story_path_variant_invalid")


def _season_pillar(scene: CanonicalScene, variant_ref: str) -> tuple[str, str]:
    if variant_ref.startswith("annual-"):
        pillar = scene.temporal_state.annual_pillar
        label = "流年"
    else:
        pillar = scene.temporal_state.luck_pillar
        label = "大运"
    if (
        len(pillar) != 2
        or pillar[0] not in HEAVENLY_STEMS
        or pillar[1] not in EARTHLY_BRANCHES
    ):
        raise QuestionStoryError("dream_question_story_temporal_pillar_invalid")
    return pillar, label


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _jsonable(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _immutable_hash(payload: Mapping[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("immutable_hash", None)
    return _hash(clean)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


__all__ = [
    "BundleValidationResult",
    "CompiledQuestionStory",
    "GOLDEN_QUESTION_BUNDLE_SPECS",
    "GoldenBundleSpec",
    "KNOWLEDGE_ATOM_BANK",
    "QUESTION_BUNDLE_VALIDATOR_VERSION",
    "QUESTION_PATTERN_BANK",
    "QUESTION_STORY_ENGINE_VERSION",
    "QuestionStoryError",
    "RealityRevealTarget",
    "STORY_SCRIPT_BANK",
    "STORY_SCRIPT_VERSION",
    "compile_active_question_story",
    "compile_flower_for_spec",
    "compile_golden_question_catalog",
    "compile_question_bundle",
    "select_active_bundle_spec",
    "validate_prompt_rewrite",
    "validate_question_bundle",
]
