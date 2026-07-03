from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.brain.contracts import (
    BrainDecisionOutcome,
    BrainDecisionTrace,
    BrainEvidenceGraphSnapshot,
    BrainTrainingExample,
    BrainTrainingExampleSource,
    BrainTrainingInputSnapshot,
    BrainTrainingLabels,
    BrainTrainingSafety,
)

BRAIN_TRAINING_EXAMPLE_BUILDER_VERSION = "v30.brain_training_example_builder.v1"
BRAIN_TRAINING_EXAMPLE_STORE_VERSION = "v30.brain_training_example_store.v1"


@dataclass(frozen=True)
class BrainTrainingExampleStore:
    root_dir: Path

    def append(self, example: BrainTrainingExample, *, split: str = "raw") -> Path:
        path = self._path(split)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(example.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return path

    def read(
        self,
        *,
        split: str = "raw",
        limit: int = 200,
        source: str = "",
        stage_id: str = "",
        min_quality: float | None = None,
        max_template_risk: float | None = None,
    ) -> list[BrainTrainingExample]:
        path = self._path(split)
        if not path.exists():
            return []
        examples: list[BrainTrainingExample] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if len(examples) >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    example = BrainTrainingExample.model_validate(payload)
                except (json.JSONDecodeError, ValueError):
                    continue
                if source and example.source != source:
                    continue
                if stage_id and example.input_stage_id != stage_id:
                    continue
                if min_quality is not None and example.structured_labels.claim_correctness < min_quality:
                    continue
                if max_template_risk is not None and example.structured_labels.template_risk > max_template_risk:
                    continue
                examples.append(example)
        return examples

    def build_splits(
        self,
        *,
        seed: int = 20260628,
        train_ratio: float = 0.7,
        validation_ratio: float = 0.2,
        source: str = "",
        stage_id: str = "",
    ) -> dict[str, Any]:
        examples = self.read(split="raw", limit=100000, source=source, stage_id=stage_id)
        ordered = sorted(examples, key=lambda example: example.example_id)
        rng = random.Random(seed)
        rng.shuffle(ordered)
        total = len(ordered)
        train_count = int(total * max(0.0, min(1.0, train_ratio)))
        validation_count = int(total * max(0.0, min(1.0 - train_ratio, validation_ratio)))
        splits = {
            "train": ordered[:train_count],
            "validation": ordered[train_count:train_count + validation_count],
            "replay": ordered[train_count + validation_count:],
        }
        for split_name, rows in splits.items():
            self._write_split(split_name, rows)
        manifest = {
            "version": "v30.brain_training_split_manifest.v1",
            "seed": seed,
            "source_filter": source,
            "stage_filter": stage_id,
            "raw_count": total,
            "splits": {name: len(rows) for name, rows in splits.items()},
            "chart_fact_mutation_allowed": False,
            "boundary": "brain_training_split_manifest_partitions_policy_examples_without_mutating_chart_facts",
        }
        path = self.root_dir / "training" / "brain_splits" / "latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return manifest

    def summary(self, *, split: str = "raw", include_splits: bool = True) -> dict[str, Any]:
        examples = self.read(split=split, limit=10000)
        by_source: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        by_action: dict[str, int] = {}
        answered = 0
        useful = 0
        quality_total = 0.0
        template_risk_total = 0.0
        overclaim_risk_total = 0.0
        for example in examples:
            by_source[example.source] = by_source.get(example.source, 0) + 1
            by_stage[example.input_stage_id] = by_stage.get(example.input_stage_id, 0) + 1
            by_action[example.decision.selected_action] = by_action.get(example.decision.selected_action, 0) + 1
            if example.outcome.user_answered:
                answered += 1
            if example.outcome.followup_useful is True:
                useful += 1
            quality_total += example.structured_labels.claim_correctness
            template_risk_total += example.structured_labels.template_risk
            overclaim_risk_total += example.structured_labels.overclaim_risk
        count = max(1, len(examples))
        split_manifest = self._read_split_manifest() if include_splits else {}
        return {
            "version": BRAIN_TRAINING_EXAMPLE_STORE_VERSION,
            "split": split,
            "example_count": len(examples),
            "source_counts": by_source,
            "stage_counts": by_stage,
            "action_counts": by_action,
            "answered_count": answered,
            "useful_followup_count": useful,
            "average_claim_correctness": round(quality_total / count, 3) if examples else 0.0,
            "average_template_risk": round(template_risk_total / count, 3) if examples else 0.0,
            "average_overclaim_risk": round(overclaim_risk_total / count, 3) if examples else 0.0,
            "split_manifest": split_manifest,
            "chart_fact_mutation_allowed": False,
            "boundary": "brain_training_example_store_persists_policy_training_data_not_chart_facts",
        }

    def _path(self, split: str) -> Path:
        safe_split = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in split) or "raw"
        return self.root_dir / "training" / "brain_examples" / f"{safe_split}.jsonl"

    def _write_split(self, split: str, examples: list[BrainTrainingExample]) -> None:
        path = self._path(split)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for example in examples:
                handle.write(json.dumps(example.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
                handle.write("\n")

    def _read_split_manifest(self) -> dict[str, Any]:
        path = self.root_dir / "training" / "brain_splits" / "latest.json"
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}


def build_brain_training_example(
    *,
    reading_id: str,
    source: BrainTrainingExampleSource,
    decision: BrainDecisionTrace,
    evidence_graph_snapshot: BrainEvidenceGraphSnapshot | None = None,
    question_outcome: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
    trainable_targets: list[str] | None = None,
    example_id: str | None = None,
) -> BrainTrainingExample:
    graph = evidence_graph_snapshot or decision.belief_state.evidence_graph
    outcome = _decision_outcome(question_outcome or {})
    structured_labels = _training_labels(labels or {}, decision=decision, outcome=outcome)
    input_snapshot = BrainTrainingInputSnapshot(
        stage_id=decision.stage_id,
        evidence_graph_snapshot=graph,
        belief_state=decision.belief_state,
        candidate_claim_ids=[
            claim.claim_id
            for claim in [*decision.belief_state.top_claims, *decision.belief_state.weak_claims, *decision.belief_state.blocked_claims]
        ][:16],
        candidate_question_ids=[question.question_id for question in decision.question_candidates],
        user_goal=decision.belief_state.user_goal,
    )
    safe_targets = _safe_trainable_targets(trainable_targets or decision.training_targets)
    label_payload = {
        "claim_correctness": structured_labels.claim_correctness,
        "question_information_gain": structured_labels.question_information_gain,
        "advice_actionability": structured_labels.advice_actionability,
        "template_risk": structured_labels.template_risk,
        "overclaim_risk": structured_labels.overclaim_risk,
        "user_cost": structured_labels.user_cost,
        "overask": structured_labels.overask,
        "contradiction_found": structured_labels.contradiction_found,
    }
    return BrainTrainingExample(
        example_id=example_id or _example_id(reading_id, decision.stage_id, decision.decision_id),
        reading_id=reading_id,
        source=source,
        source_decision_id=decision.decision_id,
        input_stage_id=decision.stage_id,
        evidence_graph_snapshot=graph,
        input=input_snapshot,
        candidate_claim_ids=input_snapshot.candidate_claim_ids,
        candidate_question_ids=input_snapshot.candidate_question_ids,
        decision=decision,
        outcome=outcome,
        structured_labels=structured_labels,
        labels=label_payload,
        safety=BrainTrainingSafety(),
        trainable_targets=safe_targets,
    )


def _decision_outcome(payload: dict[str, Any]) -> BrainDecisionOutcome:
    status = str(payload.get("status") or "")
    if not status:
        status = _outcome_status(payload)
    claim_delta = payload.get("claim_delta", {})
    claim_delta = claim_delta if isinstance(claim_delta, dict) else {}
    return BrainDecisionOutcome(
        status=status,  # type: ignore[arg-type]
        user_answered=bool(payload) and status not in {"pending", "skipped", "blocked"},
        answer_type=_answer_type(payload),  # type: ignore[arg-type]
        selected_option=str(payload.get("selected_option") or payload.get("answer") or ""),
        structured_payload=payload.get("structured_payload") if isinstance(payload.get("structured_payload"), dict) else {},
        claim_delta={str(key): _float(value) for key, value in claim_delta.items() if _float(value) != 0.0},
        followup_useful=_bool_or_none(payload.get("followup_useful")),
        contradiction_found=bool(payload.get("contradiction_found")) or any(_float(value) < 0 for value in claim_delta.values()),
    )


def _training_labels(payload: dict[str, Any], *, decision: BrainDecisionTrace, outcome: BrainDecisionOutcome) -> BrainTrainingLabels:
    return BrainTrainingLabels(
        claim_correctness=_bounded_float(payload.get("claim_correctness"), _claim_correctness_from_outcome(outcome)),
        question_information_gain=_bounded_float(payload.get("question_information_gain"), decision.feature_vector.get("information_gain", 0.0)),
        advice_actionability=_bounded_float(payload.get("advice_actionability"), _max_claim_actionability(decision)),
        template_risk=_bounded_float(payload.get("template_risk"), 0.0),
        overclaim_risk=_bounded_float(payload.get("overclaim_risk"), _max_claim_overclaim_risk(decision)),
        user_cost=_bounded_float(payload.get("user_cost"), decision.feature_vector.get("user_cost", 0.0)),
        overask=bool(payload.get("overask")) or _bounded_float(payload.get("overask_penalty"), decision.feature_vector.get("overask_penalty", 0.0)) >= 0.5,
        contradiction_found=outcome.contradiction_found,
    )


def _safe_trainable_targets(targets: list[str]) -> list[str]:
    blocked = {"chart_facts", "calendar_conversion", "pillar_calculation", "unconfirmed_hidden_factor_facts"}
    return [target for target in targets if target and target not in blocked]


def _example_id(reading_id: str, stage_id: str, decision_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    safe_stage = stage_id or "reading"
    return f"{reading_id}:{safe_stage}:{decision_id}:example:{stamp}"


def _outcome_status(payload: dict[str, Any]) -> str:
    if not payload:
        return "pending"
    if payload.get("skipped") is True:
        return "skipped"
    if payload.get("blocked") is True:
        return "blocked"
    if payload.get("contradiction_found") is True:
        return "contradicted"
    if payload.get("confirmed") is True:
        return "confirmed"
    return "answered"


def _answer_type(payload: dict[str, Any]) -> str:
    value = str(payload.get("answer_type") or payload.get("answer_shape") or "")
    if value in {"choice", "number", "short_text", "year", "none"}:
        return value
    if payload.get("selected_option"):
        return "choice"
    if payload.get("year"):
        return "year"
    return "none" if not payload else "short_text"


def _claim_correctness_from_outcome(outcome: BrainDecisionOutcome) -> float:
    if outcome.status == "confirmed":
        return 1.0
    if outcome.status == "contradicted" or outcome.contradiction_found:
        return 0.0
    if outcome.user_answered:
        return 0.65
    return 0.0


def _max_claim_actionability(decision: BrainDecisionTrace) -> float:
    claims = [*decision.belief_state.top_claims, *decision.belief_state.weak_claims]
    return max([claim.actionability for claim in claims] or [0.0])


def _max_claim_overclaim_risk(decision: BrainDecisionTrace) -> float:
    claims = [*decision.belief_state.top_claims, *decision.belief_state.weak_claims]
    return max([claim.overclaim_risk for claim in claims] or [0.0])


def _bounded_float(value: Any, default: float) -> float:
    return max(0.0, min(1.0, _float(value, default)))


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
