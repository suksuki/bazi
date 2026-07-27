from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from experience.compiler import canonical_hash
from experience.contracts import ExperienceModel, TopicExploration
from experience.relation_work_projection import RelationWorkProjectionView


LIFE_TREE_QUESTION_BANK_VERSION = "deepbazi.life-tree-question-bank.p1.v1"
QuestionCategory = Literal[
    "factual_observation",
    "candidate_comparison",
    "discriminating",
    "temporal_change",
    "counterfactual",
    "life_observation",
]
QuestionPurpose = Literal["lab_learning", "life_observation"]
QuestionRevealPolicy = Literal["NONE", "REALITY_FEEDBACK"]


class QuestionOptionBlueprint(ExperienceModel):
    option_id: str = Field(min_length=1, max_length=100)
    label_template: str = Field(min_length=1, max_length=300)
    exploration_meaning: str = Field(min_length=1, max_length=500)


class QuestionEvidenceRequirement(ExperienceModel):
    relation_families: list[str] = Field(default_factory=list)
    fact_states: list[
        Literal[
            "RELATION_CANDIDATE",
            "RELATION_STRUCTURALLY_PRESENT",
            "TARGETS_IDENTIFIED",
        ]
    ] = Field(default_factory=list)
    activation_states: list[
        Literal["not_activated", "natal_present", "temporally_activated"]
    ] = Field(default_factory=list)
    path_labels: list[str] = Field(default_factory=list)
    minimum_path_count: int = Field(default=0, ge=0, le=6)
    minimum_competing_path_count: int = Field(default=0, ge=0, le=6)
    requires_unresolved_effect: bool = False
    requires_counterfactual_subject: bool = False


class QuestionBlueprint(ExperienceModel):
    schema_version: Literal[
        "deepbazi.life-tree-question-blueprint.p0.v1"
    ] = "deepbazi.life-tree-question-blueprint.p0.v1"
    blueprint_id: str = Field(min_length=1, max_length=140)
    version: str = LIFE_TREE_QUESTION_BANK_VERSION
    category: QuestionCategory
    purpose: QuestionPurpose = "lab_learning"
    title: str = Field(min_length=1, max_length=120)
    prompt_template: str = Field(min_length=1, max_length=500)
    answer_type: Literal["single_choice"] = "single_choice"
    options: list[QuestionOptionBlueprint] = Field(min_length=2, max_length=4)
    requirements: QuestionEvidenceRequirement
    relevance_reason: str = Field(min_length=1, max_length=700)
    distinguishes: list[str] = Field(min_length=1)
    permitted_exploration_writes: list[
        Literal[
            "selected_option",
            "observation",
            "open_question",
            "candidate_preference",
        ]
    ] = Field(min_length=1)
    prohibited_truth_writes: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    life_domain: str = Field(default="structure_learning", min_length=1, max_length=80)
    observation_window: str = Field(default="", max_length=300)
    reveal_policy: QuestionRevealPolicy = "NONE"
    future_evidence_requirements: list[str] = Field(default_factory=list)
    professional_status: Literal[
        "STRUCTURAL_LEARNING",
        "STRUCTURAL_CANDIDATE_ONLY",
    ] = "STRUCTURAL_LEARNING"
    baseline_credit_allowed: Literal[False] = False
    writes_life_case: Literal[False] = False
    upgrades_relation_effect: Literal[False] = False
    upgrades_work_path: Literal[False] = False
    declares_main_work: Literal[False] = False

    @model_validator(mode="after")
    def validate_blueprint(self) -> "QuestionBlueprint":
        option_ids = [item.option_id for item in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("life_tree_question_duplicate_option")
        if not (
            self.requirements.relation_families
            or self.requirements.fact_states
            or self.requirements.activation_states
            or self.requirements.path_labels
            or self.requirements.minimum_path_count
        ):
            raise ValueError("life_tree_question_requires_chart_evidence")
        if self.purpose == "life_observation":
            if self.category != "life_observation":
                raise ValueError("life_observation_requires_matching_category")
            if self.reveal_policy != "REALITY_FEEDBACK":
                raise ValueError("life_observation_requires_reality_feedback")
            if not self.observation_window:
                raise ValueError("life_observation_requires_window")
            if len(self.future_evidence_requirements) < 2:
                raise ValueError("life_observation_requires_future_evidence")
        return self


class LifeTreeQuestionInstance(ExperienceModel):
    schema_version: Literal[
        "deepbazi.life-tree-question-instance.p0.v1"
    ] = "deepbazi.life-tree-question-instance.p0.v1"
    instance_id: str = Field(min_length=1, max_length=180)
    blueprint_id: str = Field(min_length=1, max_length=140)
    blueprint_version: str = Field(min_length=1, max_length=120)
    category: QuestionCategory
    purpose: QuestionPurpose
    title: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=500)
    options: list[QuestionOptionBlueprint] = Field(min_length=2, max_length=4)
    why_this_question: str = Field(min_length=1, max_length=700)
    distinguished_hypothesis_refs: list[str] = Field(min_length=1)
    distinguished_hypotheses: list[str] = Field(min_length=1)
    relation_fact_revision_refs: list[str] = Field(default_factory=list)
    work_path_candidate_refs: list[str] = Field(default_factory=list)
    counterfactual_subject_refs: list[str] = Field(default_factory=list)
    source_foundation_ref: str = Field(min_length=1, max_length=220)
    source_foundation_hash: str = Field(min_length=64, max_length=64)
    provenance_refs: list[str] = Field(min_length=1)
    life_domain: str = Field(min_length=1, max_length=80)
    observation_window: str = Field(default="", max_length=300)
    reveal_policy: QuestionRevealPolicy
    future_evidence_requirements: list[str] = Field(default_factory=list)
    professional_status: Literal[
        "STRUCTURAL_LEARNING",
        "STRUCTURAL_CANDIDATE_ONLY",
    ]
    baseline_credit_allowed: Literal[False] = False
    permitted_write_owner: Literal["TopicExploration"] = "TopicExploration"
    writes_life_case: Literal[False] = False


def select_life_tree_questions(
    *,
    projection: RelationWorkProjectionView,
    blueprints: list[QuestionBlueprint],
    limit: int = 30,
) -> list[LifeTreeQuestionInstance]:
    if projection.audience != "dream":
        raise ValueError("life_tree_questions_require_dream_projection")
    selected: list[LifeTreeQuestionInstance] = []
    for blueprint in sorted(blueprints, key=lambda item: item.blueprint_id):
        context = _selection_context(projection, blueprint)
        if context is None:
            continue
        payload = {
            "blueprint_id": blueprint.blueprint_id,
            "blueprint_version": blueprint.version,
            "foundation_ref": projection.foundation_ref,
            "relation_fact_revision_refs": context["fact_refs"],
            "work_path_candidate_refs": context["path_refs"],
            "counterfactual_subject_refs": context["counterfactual_refs"],
        }
        instance_id = f"life-tree-question:{canonical_hash(payload)}"
        selected.append(
            LifeTreeQuestionInstance(
                instance_id=instance_id,
                blueprint_id=blueprint.blueprint_id,
                blueprint_version=blueprint.version,
                category=blueprint.category,
                purpose=blueprint.purpose,
                title=blueprint.title,
                prompt=_render(blueprint.prompt_template, context),
                options=[
                    option.model_copy(
                        update={
                            "label_template": _render(
                                option.label_template,
                                context,
                            )
                        }
                    )
                    for option in blueprint.options
                ],
                why_this_question=_render(
                    blueprint.relevance_reason,
                    context,
                ),
                distinguished_hypothesis_refs=context["hypothesis_refs"],
                distinguished_hypotheses=context["hypothesis_labels"],
                relation_fact_revision_refs=context["fact_refs"],
                work_path_candidate_refs=context["path_refs"],
                counterfactual_subject_refs=context["counterfactual_refs"],
                source_foundation_ref=projection.foundation_ref,
                source_foundation_hash=projection.foundation_content_hash,
                provenance_refs=[
                    *blueprint.provenance_refs,
                    *context["fact_refs"],
                    *context["path_refs"],
                ],
                life_domain=blueprint.life_domain,
                observation_window=blueprint.observation_window,
                reveal_policy=blueprint.reveal_policy,
                future_evidence_requirements=(
                    blueprint.future_evidence_requirements
                ),
                professional_status=blueprint.professional_status,
                baseline_credit_allowed=blueprint.baseline_credit_allowed,
            )
        )
        if len(selected) >= limit:
            break
    return selected


def exploration_from_life_tree_answer(
    *,
    question: LifeTreeQuestionInstance,
    participant_run_id: str,
    selected_option_id: str,
    created_at,
) -> TopicExploration:
    option = next(
        (item for item in question.options if item.option_id == selected_option_id),
        None,
    )
    if option is None:
        raise ValueError("life_tree_question_option_not_available")
    identity = {
        "participant_run_id": participant_run_id,
        "question_instance_id": question.instance_id,
        "selected_option_id": selected_option_id,
    }
    return TopicExploration(
        exploration_id=f"exploration:{canonical_hash(identity)}",
        participant_run_id=participant_run_id,
        topic_id=question.blueprint_id,
        responses={question.instance_id: selected_option_id},
        capsule_message=(
            "这次选择已作为现实观察封存；当前命盘只提供观察缘由，"
            "不计作未来结果证据。"
            if question.purpose == "life_observation"
            else "这次选择只作为探索记录，不改变命盘事实。"
        ),
        experiment_kind="life_tree_relation_work_question",
        scene_id=question.source_foundation_ref,
        scene_source_hash=question.source_foundation_hash,
        base_snapshot_ref=question.source_foundation_ref,
        base_snapshot_hash=question.source_foundation_hash,
        selected_node_ids=list(question.counterfactual_subject_refs),
        sandbox_result_refs=[
            *question.relation_fact_revision_refs,
            *question.work_path_candidate_refs,
        ],
        observations=[
            option.exploration_meaning,
            f"distinguishes:{','.join(question.distinguished_hypothesis_refs)}",
            f"question_purpose:{question.purpose}",
            f"reveal_policy:{question.reveal_policy}",
            "baseline_credit_allowed:false",
        ],
        open_question=question.prompt,
        restored_original=True,
        capability_trace=["visual_only", "deterministic_structure"],
        life_case_version_observed=question.blueprint_version,
        case_local_only=True,
        created_at=created_at,
    )


def _selection_context(
    projection: RelationWorkProjectionView,
    blueprint: QuestionBlueprint,
) -> dict[str, object] | None:
    requirement = blueprint.requirements
    facts = [
        item
        for item in projection.factual_view
        if (
            not requirement.relation_families
            or item.relation_family in requirement.relation_families
        )
        and (
            not requirement.fact_states
            or item.fact_state in requirement.fact_states
        )
        and (
            not requirement.activation_states
            or item.activation_state in requirement.activation_states
        )
        and (
            not requirement.requires_unresolved_effect
            or item.effect_status == "effect_unresolved"
        )
    ]
    if requirement.relation_families and not facts:
        return None
    paths = [
        item
        for item in projection.candidate_path_view
        if not requirement.path_labels or item.label in requirement.path_labels
    ]
    if requirement.path_labels and {
        item.label for item in paths
    } != set(requirement.path_labels):
        return None
    if len(paths) < requirement.minimum_path_count:
        return None
    competition_groups: dict[str, list[object]] = {}
    for item in paths:
        if item.competing_path_group_ref:
            competition_groups.setdefault(
                item.competing_path_group_ref,
                [],
            ).append(item)
    competing = max(competition_groups.values(), key=len, default=[])
    if len(competing) < requirement.minimum_competing_path_count:
        return None
    if requirement.minimum_competing_path_count:
        paths = list(competing)

    fact_refs = [item.fact_revision_ref for item in facts]
    path_refs = [item.work_path_candidate_ref for item in paths]
    participants: dict[str, dict[str, str]] = {}
    for item in [*facts, *paths]:
        for coordinate in item.participant_coordinates:
            participants[coordinate["node_ref"]] = coordinate
    ordered_participants = sorted(
        participants.values(),
        key=lambda item: (
            _scope_order(item["scope"]),
            _slot_order(item["slot"]),
            item["level"],
            item["component"],
        ),
    )
    path_labels = [item.label for item in paths]
    relation_families = [item.relation_family for item in facts]
    counterfactual_refs = (
        [item["node_ref"] for item in ordered_participants[:1]]
        if requirement.requires_counterfactual_subject
        else []
    )
    hypotheses = path_refs or fact_refs
    if not hypotheses:
        return None
    return {
        "fact_refs": fact_refs,
        "path_refs": path_refs,
        "counterfactual_refs": counterfactual_refs,
        "hypothesis_refs": hypotheses,
        "hypothesis_labels": (
            path_labels
            or [
                f"{_relation_label(item.relation_family)}关系："
                f"{_coordinate_label(item.participant_coordinates[0])}"
                for item in facts
            ]
        ),
        "path_a": path_labels[0] if path_labels else "当前结构候选",
        "path_b": path_labels[1] if len(path_labels) > 1 else "另一种结构解释",
        "relation_family": _relation_label(
            relation_families[0] if relation_families else ""
        ),
        "participant_a": _coordinate_label(
            ordered_participants[0] if ordered_participants else None
        ),
        "participant_b": _coordinate_label(
            ordered_participants[1] if len(ordered_participants) > 1 else None
        ),
        "temporal_stage": (
            facts[0].temporal_stage if facts else paths[0].valid_from_stage
        ),
    }


def _render(template: str, context: dict[str, object]) -> str:
    return template.format_map({key: str(value) for key, value in context.items()})


def _coordinate_label(coordinate: dict[str, str] | None) -> str:
    if coordinate is None:
        return "当前节点"
    scope = {
        "natal": "原局",
        "luck": "大运",
        "year": "流年",
        "month": "流月",
    }.get(coordinate["scope"], coordinate["scope"])
    level = {
        "stem": "干",
        "branch": "支",
        "hidden_stem": "藏干",
    }.get(coordinate["level"], coordinate["level"])
    slot = {
        "year": "年",
        "month": "月",
        "day": "日",
        "hour": "时",
    }.get(coordinate["slot"], coordinate["slot"])
    return f"{scope}{slot}{level}{coordinate['component']}"


def _relation_label(value: str) -> str:
    return {
        "generates": "生",
        "controls": "克",
        "clashes": "冲",
    }.get(value, value or "关系")


def _scope_order(value: str) -> int:
    return {"natal": 0, "luck": 1, "year": 2, "month": 3}.get(value, 9)


def _slot_order(value: str) -> int:
    return {"year": 0, "month": 1, "day": 2, "hour": 3}.get(value, 9)


__all__ = [
    "LIFE_TREE_QUESTION_BANK_VERSION",
    "LifeTreeQuestionInstance",
    "QuestionBlueprint",
    "QuestionEvidenceRequirement",
    "QuestionOptionBlueprint",
    "exploration_from_life_tree_answer",
    "select_life_tree_questions",
]
