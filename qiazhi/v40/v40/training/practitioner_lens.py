from __future__ import annotations

from dataclasses import dataclass

from v40.contracts.base import RoleKey
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, LocalOverlay, TrainingLabelEvent


@dataclass(frozen=True)
class PractitionerLensActionPolicy:
    label: LabelValue
    strength: float
    confidence: float
    reason: str


ACTION_POLICIES: dict[str, PractitionerLensActionPolicy] = {
    "more_like_this": PractitionerLensActionPolicy(
        label=LabelValue.SUPPORTS,
        strength=0.78,
        confidence=0.72,
        reason="命理师认为这一信号更贴近当前盘面或用户反馈，应作为本次测算的支持证据。",
    ),
    "supporting_context": PractitionerLensActionPolicy(
        label=LabelValue.PROBE_HELPFUL,
        strength=0.62,
        confidence=0.58,
        reason="命理师认为这一信号适合作为辅助背景，不直接升格为最终断语。",
    ),
    "do_not_use_now": PractitionerLensActionPolicy(
        label=LabelValue.WEAKENS,
        strength=0.72,
        confidence=0.66,
        reason="命理师认为这一信号当前不宜采用，应在本次测算中降权或保留边界。",
    ),
    "ask_to_confirm": PractitionerLensActionPolicy(
        label=LabelValue.NEEDS_PROBE,
        strength=0.76,
        confidence=0.70,
        reason="命理师认为这一信号需要通过追问确认，不应直接变成结论。",
    ),
    "user_mismatch": PractitionerLensActionPolicy(
        label=LabelValue.MISMATCH,
        strength=0.82,
        confidence=0.74,
        reason="命理师记录用户反馈与该信号不符，应作为后续训练和校准素材。",
    ),
    "note": PractitionerLensActionPolicy(
        label=LabelValue.PROBE_HELPFUL,
        strength=0.54,
        confidence=0.56,
        reason="命理师仅补充本次判断备注，作为后续复核和训练素材，不直接改变结论。",
    ),
}


def build_practitioner_lens_action(
    *,
    action_id: str,
    runtime: RuntimeResult,
    action_key: str,
    target_type: LabelTargetType,
    target_ids: list[str],
    note: str = "",
    created_by_role: RoleKey = "practitioner",
) -> tuple[TrainingLabelEvent, LocalOverlay]:
    if runtime.request.role_key != "practitioner":
        raise ValueError("Practitioner lens action requires a practitioner runtime")
    if created_by_role not in {"practitioner", "admin"}:
        raise ValueError("Practitioner lens action requires practitioner or admin role")
    if action_key not in ACTION_POLICIES:
        raise ValueError("Unknown practitioner lens action_key")
    if not target_ids:
        raise ValueError("Practitioner lens action requires target_ids")
    clean_action_id = action_id.strip()
    if not clean_action_id:
        raise ValueError("Practitioner lens action requires action_id")

    policy = ACTION_POLICIES[action_key]
    event = TrainingLabelEvent(
        event_id=f"label:practitioner_lens:{clean_action_id}",
        reading_id=runtime.reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=target_type,
        target_ids=target_ids,
        label=policy.label,
        strength=policy.strength,
        confidence=policy.confidence,
        reason=_reason_with_note(policy.reason, note),
        evidence_refs=[
            "surface:calibration:practitioner_lens",
            f"runtime:{runtime.reading_id}",
            *target_ids[:6],
        ],
        created_by_role=created_by_role,
        local_only=True,
        chart_fact_mutation_allowed=False,
    )
    overlay = LocalOverlay(
        overlay_id=f"overlay:practitioner_lens:{clean_action_id}",
        reading_id=runtime.reading_id,
        label_event_ids=[event.event_id],
        affected_target_ids=target_ids,
        expires_after_reading=True,
        global_update_allowed=False,
    )
    return event, overlay


def _reason_with_note(reason: str, note: str) -> str:
    clean_note = note.strip()
    if not clean_note:
        return reason
    return f"{reason} 命理师备注：{clean_note}"
