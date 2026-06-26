from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


QUESTION_DAG_STAGES: tuple[str, ...] = (
    "entry",
    "focus",
    "structure",
    "timing",
    "review",
    "observe",
    "advice",
    "closure",
)


@dataclass(frozen=True)
class ChoiceOption:
    option_key: str
    label: str
    next_stage: str
    learning_signal: str = "choice"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NextQuestionRule:
    rule_key: str
    next_stage: str
    condition_key: str = ""
    priority: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuestionNode:
    question_id: str
    question_key: str
    role_target: str
    stage: str
    domain: str
    title: str
    choice_options: tuple[ChoiceOption, ...] = field(default_factory=tuple)
    next_question_rules: tuple[NextQuestionRule, ...] = field(default_factory=tuple)
    answer_mode: str = "hybrid"
    learning_signal: str = "interaction_signal"
    visibility: str = "public_guided"
    source: str = "runtime_question_candidate"
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "QUESTION_NODE_IS_INTERACTION_LAYER",
        "NO_CORE_FACT_MUTATION",
        "NO_RULE_TRUTH_MUTATION",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_question_nodes(
    questions: tuple[object, ...] | list[object],
    *,
    role_key: str,
) -> tuple[QuestionNode, ...]:
    return tuple(question_node_from_candidate(row, role_key=role_key) for row in questions)


def question_node_from_candidate(question: object, *, role_key: str) -> QuestionNode:
    row = _object_payload(question)
    domain = str(row.get("domain") or "")
    stage = infer_question_stage(row, role_key=role_key)
    question_key = str(row.get("question_key") or "")
    question_id = str(row.get("question_id") or question_key)
    return QuestionNode(
        question_id=question_id,
        question_key=question_key,
        role_target=normalize_question_role(role_key),
        stage=stage,
        domain=domain,
        title=str(row.get("title") or question_key or "继续看当前主题"),
        choice_options=default_choice_options(stage, role_key=role_key),
        next_question_rules=default_next_question_rules(stage, role_key=role_key),
        answer_mode="llm" if normalize_question_role(role_key) in {"guest", "user"} else "hybrid",
        learning_signal=learning_signal_for_role(role_key),
        visibility=visibility_for_role(role_key),
    )


def infer_question_stage(question: dict[str, Any], *, role_key: str) -> str:
    role = normalize_question_role(role_key)
    role_view_level = str(question.get("role_view_level") or "")
    if role == "admin":
        return "observe"
    if role == "analyst":
        return "review" if _review_domain(str(question.get("domain") or "")) else "structure"
    if role_view_level == "entry":
        return "entry"
    domain = str(question.get("domain") or "")
    if domain == "time":
        return "timing"
    if domain in {"wealth", "career", "relationship", "health"}:
        return "focus"
    if domain in {"strength", "ten_god", "element", "branch", "useful_god", "pattern"}:
        return "structure"
    return "focus" if role == "user" else "entry"


def default_choice_options(stage: str, *, role_key: str) -> tuple[ChoiceOption, ...]:
    role = normalize_question_role(role_key)
    if role == "admin":
        return (
            ChoiceOption("view_replay", "查看回放", "observe"),
            ChoiceOption("view_policy", "查看策略", "observe"),
            ChoiceOption("review_question", "审核问题", "review"),
        )
    if role == "analyst":
        return (
            ChoiceOption("accept", "认可", "review", "calibration_signal"),
            ChoiceOption("downrank", "降权", "review", "calibration_signal"),
            ChoiceOption("insufficient_evidence", "证据不足", "review", "calibration_signal"),
        )
    if stage == "entry":
        return (
            ChoiceOption("career", "事业", "focus"),
            ChoiceOption("wealth", "财运", "focus"),
            ChoiceOption("relationship", "感情", "focus"),
        )
    if stage == "focus":
        return (
            ChoiceOption("reason", "看原因", "structure"),
            ChoiceOption("timing", "看时间", "timing"),
            ChoiceOption("advice", "看建议", "advice"),
        )
    if stage == "timing":
        return (
            ChoiceOption("advice", "看建议", "advice"),
            ChoiceOption("another_topic", "换主题", "entry"),
        )
    return (
        ChoiceOption("continue", "继续看", "advice"),
        ChoiceOption("close", "先收束", "closure"),
    )


def default_next_question_rules(stage: str, *, role_key: str) -> tuple[NextQuestionRule, ...]:
    path = role_default_dag_path(role_key)
    if stage not in path:
        return ()
    index = path.index(stage)
    if index + 1 >= len(path):
        return ()
    return (
        NextQuestionRule(
            rule_key=f"next.{normalize_question_role(role_key)}.{stage}.{path[index + 1]}",
            next_stage=path[index + 1],
            condition_key=f"stage_completed:{stage}",
            priority=1.0,
        ),
    )


def role_default_dag_path(role_key: str) -> tuple[str, ...]:
    role = normalize_question_role(role_key)
    if role == "guest":
        return ("entry", "focus", "advice", "closure")
    if role == "analyst":
        return ("structure", "review", "timing", "closure")
    if role == "admin":
        return ("observe", "review", "closure")
    return ("entry", "focus", "structure", "timing", "advice", "closure")


def learning_signal_for_role(role_key: str) -> str:
    role = normalize_question_role(role_key)
    if role == "analyst":
        return "calibration_signal"
    if role == "admin":
        return "validation_signal"
    return "interaction_signal"


def visibility_for_role(role_key: str) -> str:
    role = normalize_question_role(role_key)
    return {
        "guest": "public_entry",
        "user": "public_guided",
        "analyst": "technical_review",
        "admin": "system_observation",
    }.get(role, "public_guided")


def normalize_question_role(role_key: str) -> str:
    role = str(role_key or "user")
    if role in {"guest", "user", "analyst", "admin"}:
        return role
    if role == "lab":
        return "admin"
    return "user"


def question_dag_manifest() -> dict[str, Any]:
    return {
        "version": "v20.question_dag_manifest.v1",
        "stages": QUESTION_DAG_STAGES,
        "role_paths": {
            role: role_default_dag_path(role)
            for role in ("guest", "user", "analyst", "admin")
        },
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_IS_INTERACTION_LAYER",
            "NO_CORE_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def _review_domain(domain: str) -> bool:
    return domain in {"strength", "ten_god", "branch", "useful_god", "pattern", "time"}


def _object_payload(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        return payload if isinstance(payload, dict) else {}
    return {
        key: getattr(value, key)
        for key in (
            "question_id",
            "question_key",
            "domain",
            "title",
            "measurement_stage",
            "role_view_level",
        )
        if hasattr(value, key)
    }
