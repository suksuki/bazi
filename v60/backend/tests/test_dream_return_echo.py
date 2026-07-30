from __future__ import annotations

from pathlib import Path

import pytest
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.return_echo import DreamReturnEchoProjector
from abu_v60.dream.return_echo_contracts import (
    DREAM_RETURN_ECHO_VERSION,
    DreamReturnEcho,
    DreamReturnEchoAbuRecap,
    DreamReturnEchoJudgment,
    DreamReturnEchoLineage,
    DreamReturnEchoOpenObservation,
    DreamReturnEchoWorldResponse,
)
from abu_v60.provenance import content_hash
from pydantic import ValidationError


def _issue_echo() -> DreamReturnEcho:
    return DreamReturnEcho.issue(
        encounter_ref="v60-encounter-return-echo-test",
        public_alias="闻溪",
        episode_title="共同修复，共同署名",
        judgment=DreamReturnEchoJudgment(
            choice_label="保留试案",
            summary="你当时把「保留试案」作为那一刻的判断。",
        ),
        world_response=DreamReturnEchoWorldResponse(
            summary="后来共同小组完成了修复。",
            evidence_summaries=(
                "馆方把修复安排交给共同小组。",
                "完成记录同时留下两个人的名字。",
            ),
        ),
        still_to_observe=DreamReturnEchoOpenObservation(
            summary="下一次仍把当下证据和后来结果分开核对。",
        ),
        abu_recap=DreamReturnEchoAbuRecap(
            meaning="这次只说明后来事实支持了当时判断。",
            boundary="它不能说明主人的命理关系。",
            next_attention="继续观察下一段梦中生命自己的证据。",
        ),
        lineage=DreamReturnEchoLineage(
            question_ref="v60-question-return-echo-test",
            episode_ref="v60-episode-return-echo-test",
            episode_version=1,
            answer_seal_ref="v60-answer-seal-return-echo-test",
            answer_seal_hash="1" * 64,
            reveal_ref="v60-reveal-return-echo-test",
            reveal_hash="2" * 64,
            world_event_ref="v60-world-event-return-echo-test",
            reconciliation_result="SUPPORTED",
            committed_evidence_refs=(
                "v60-evidence-return-echo-a",
                "v60-evidence-return-echo-b",
            ),
            committed_evidence_hashes=("3" * 64, "4" * 64),
        ),
    )


def test_return_echo_contract_is_stable_and_locks_non_authority() -> None:
    first = _issue_echo()
    replay = DreamReturnEcho.issue(
        **first.model_dump(
            mode="python",
            exclude={"echo_ref", "echo_hash"},
        )
    )

    assert first == replay
    assert first.contract_version == DREAM_RETURN_ECHO_VERSION
    assert first.echo_hash == content_hash(
        first.model_dump(
            mode="json",
            exclude={"echo_ref", "echo_hash"},
        )
    )
    assert first.semantics == "DREAM_LIFE_RETURN_ECHO_ONLY"
    assert first.owner_mingli_evidence_allowed is False
    assert first.dream_outcome_admitted_as_owner_evidence is False
    assert first.tree_candidate_set_or_order_changed is False
    assert first.mingli_write_allowed is False
    assert first.decision_write_allowed is False
    assert first.knowledge_write_allowed is False
    assert first.canonical_write_allowed is False
    assert first.read_only is True


def test_return_echo_contract_rejects_identity_and_evidence_drift() -> None:
    echo = _issue_echo()
    payload = echo.model_dump(mode="python")
    with pytest.raises(ValidationError, match="dream_return_echo_hash_mismatch"):
        DreamReturnEcho.model_validate(
            {
                **payload,
                "judgment": {
                    **payload["judgment"],
                    "summary": "漂移后的总结",
                },
            }
        )

    lineage = echo.lineage.model_dump(mode="python")
    with pytest.raises(
        ValidationError,
        match="dream_return_echo_evidence_refs_not_ordered_unique",
    ):
        DreamReturnEchoLineage.model_validate(
            {
                **lineage,
                "committed_evidence_refs": tuple(
                    reversed(lineage["committed_evidence_refs"])
                ),
            }
        )


def test_return_echo_projector_has_no_canonical_write_path() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "abu_v60"
        / "dream"
        / "return_echo.py"
    ).read_text(encoding="utf-8")
    normalized = source.upper()

    for forbidden in (
        "INSERT INTO",
        "UPDATE DREAM.",
        "UPDATE MINGLI.",
        "UPDATE COGNITION.",
        "UPDATE KNOWLEDGE.",
        "DELETE FROM",
    ):
        assert forbidden not in normalized
    for forbidden_import in (
        "FROM ABU_V60.DECISION",
        "FROM ABU_V60.KNOWLEDGE",
        "FROM ABU_V60.MINGLI",
    ):
        assert forbidden_import not in normalized


def test_return_echo_uses_admitted_actor_name_for_pre_grove_episode() -> None:
    actor_identity = {
        "actor_ref": "v60-actor-yanzhou-v1",
        "world_ref": "v60-world-canonical",
        "case_ref": "v60-case-yanzhou-v1",
        "actor_kind": "SYNTHETIC_LIFE",
        "display_name": "砚舟",
        "branch": "canonical_world",
    }
    actor_manifest = {
        "admission_version": "v60.world-actor-admission.001",
        **actor_identity,
        "identity_hash": content_hash(actor_identity),
    }
    sources = {
        "world_actor_ref": actor_identity["actor_ref"],
        "actor_world_ref": actor_identity["world_ref"],
        "actor_case_ref": actor_identity["case_ref"],
        "actor_kind": actor_identity["actor_kind"],
        "actor_display_name": actor_identity["display_name"],
        "actor_branch": actor_identity["branch"],
        "actor_admission_manifest_json": actor_manifest,
        "actor_admission_manifest_hash": content_hash(actor_manifest),
        "life_case_case_ref": actor_identity["case_ref"],
        "source_question_ref": "v60-question-yanzhou-water-record-v1",
        "candidate_json": None,
        "candidate_hash": None,
    }
    encounter = {
        "actor_ref": actor_identity["actor_ref"],
        "tree_ref": "v60-tree-yanzhou-v1",
        "question_ref": sources["source_question_ref"],
    }

    assert (
        DreamReturnEchoProjector._validated_public_alias(
            encounter=encounter,
            sources=sources,
        )
        == "砚舟"
    )
    with pytest.raises(
        DreamStateError,
        match="dream_return_echo_source_candidate_missing",
    ):
        DreamReturnEchoProjector._validated_public_alias(
            encounter=encounter,
            sources={
                **sources,
                "source_question_ref": "v60-question-materialized",
            },
        )
