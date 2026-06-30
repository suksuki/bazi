from __future__ import annotations

from v40.contracts.output import ConversationTurn
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent


def build_training_label_from_conversation_turn(
    *,
    event_id: str,
    turn: ConversationTurn,
    seed_id: str = "",
) -> TrainingLabelEvent:
    target_type, target_ids = _target(turn)
    return TrainingLabelEvent(
        event_id=event_id,
        reading_id=turn.reading_id,
        source=LabelSource.PROBE_ANSWER if turn.source_probe_ids else LabelSource.USER_ANSWER,
        target_type=target_type,
        target_ids=target_ids,
        label=LabelValue.PROBE_HELPFUL if turn.source_seed_id or turn.source_probe_ids else LabelValue.NEEDS_PROBE,
        strength=0.64 if turn.accepted else 0.38,
        confidence=0.58 if turn.accepted else 0.42,
        reason=_reason(turn=turn, seed_id=seed_id),
        evidence_refs=_evidence_refs(turn=turn, seed_id=seed_id),
        created_by_role=turn.role_key,
        local_only=True,
    )


def _target(turn: ConversationTurn) -> tuple[LabelTargetType, list[str]]:
    if turn.source_probe_ids:
        return LabelTargetType.PROBE, turn.source_probe_ids
    if turn.source_verdict_ids:
        return LabelTargetType.VERDICT, turn.source_verdict_ids
    if turn.source_advice_ids:
        return LabelTargetType.ADVICE, turn.source_advice_ids
    return LabelTargetType.LLM_OUTPUT, [turn.turn_id]


def _reason(*, turn: ConversationTurn, seed_id: str) -> str:
    if turn.source_seed_id or seed_id:
        return "用户点击推荐问题进入一轮对话，可作为该追问种子的有效性反馈。"
    return "用户直接输入追问，可作为后续种子问题生成和主题路由的反馈。"


def _evidence_refs(*, turn: ConversationTurn, seed_id: str) -> list[str]:
    refs = [turn.turn_id]
    if turn.source_seed_id:
        refs.append(turn.source_seed_id)
    elif seed_id:
        refs.append(seed_id)
    return refs
