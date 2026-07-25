from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from experience.compiler import canonical_hash
from experience.contracts import (
    CueTemplate,
    FinalActorCommand,
    MingliExperienceEnvelope,
    PerformanceCueInstance,
)


PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


class CueRenderError(ValueError):
    pass


def freeze_performance_cue(
    *,
    template: CueTemplate,
    participant_run_id: str | None,
    envelope: MingliExperienceEnvelope | None = None,
    public_bindings: dict[str, str] | None = None,
) -> PerformanceCueInstance:
    if template.visibility == "participant_private" and envelope is None:
        raise CueRenderError("private_cue_requires_envelope")
    if template.visibility == "public" and envelope is not None:
        raise CueRenderError("public_cue_must_not_receive_envelope")

    bindings = dict(public_bindings or {})
    claim_refs: list[str] = []
    if envelope:
        bindings.update(_envelope_bindings(template=template, envelope=envelope))
        claim_refs = _claim_refs(template=template, envelope=envelope)

    final_dialogue = _normalize_typography(_render(template.dialogue_template, bindings))
    final_subtitle = _normalize_typography(_render(template.subtitle_template, bindings))
    if envelope:
        for prohibited in envelope.must_not_say:
            if prohibited and (prohibited in final_dialogue or prohibited in final_subtitle):
                raise CueRenderError(f"must_not_say_violation:{prohibited}")

    frozen_at = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "template_id": template.template_id,
        "participant_run_id": participant_run_id,
        "visibility": template.visibility,
        "final_dialogue": final_dialogue,
        "final_subtitle": final_subtitle,
        "actor": template.actor.model_dump(mode="json"),
        "stage": [item.model_dump(mode="json") for item in template.stage],
        "audio": template.voice.audio_asset,
        "claim_refs": claim_refs,
        "envelope_id": envelope.envelope_id if envelope else None,
        "envelope_hash": canonical_hash(envelope) if envelope else None,
        "frozen_at": frozen_at.isoformat(),
    }
    return PerformanceCueInstance(
        cue_instance_id=f"cue-{uuid4().hex[:20]}",
        template_id=template.template_id,
        participant_run_id=participant_run_id,
        visibility=template.visibility,
        final_dialogue=final_dialogue,
        final_subtitle=final_subtitle,
        final_actor_commands=[
            FinalActorCommand(
                expression=template.actor.expression,
                motion_asset=template.actor.motion_asset,
                loop=template.actor.loop,
            )
        ],
        final_stage_commands=template.stage,
        final_audio_asset=template.voice.audio_asset,
        claim_refs=claim_refs,
        envelope_id=envelope.envelope_id if envelope else None,
        envelope_hash=canonical_hash(envelope) if envelope else None,
        phrase_policy_version=f"{template.phrase_policy}.v1",
        frozen_at=frozen_at,
        cue_hash=canonical_hash(payload),
    )


def _claim_refs(*, template: CueTemplate, envelope: MingliExperienceEnvelope) -> list[str]:
    if not template.required_claim_category:
        return []
    return [
        claim.claim_ref
        for claim in envelope.approved_claims
        if claim.category == template.required_claim_category
    ][:1]


def _envelope_bindings(*, template: CueTemplate, envelope: MingliExperienceEnvelope) -> dict[str, str]:
    facts = " · ".join(item.display_value for item in envelope.allowed_chart_facts)
    matching_claims = [
        claim
        for claim in envelope.approved_claims
        if not template.required_claim_category or claim.category == template.required_claim_category
    ]
    claim = matching_claims[0] if matching_claims else None
    if template.required_claim_category and claim is None:
        raise CueRenderError(f"required_claim_unavailable:{template.required_claim_category}")
    hypothesis = envelope.competing_hypotheses[0] if envelope.competing_hypotheses else None
    uncertainty = "；".join(envelope.uncertainty.reasons) or "仍保留必要的不确定性"
    return {
        "four_pillars": facts or "这份命盘尚未开放",
        "approved_claim": claim.approved_meaning if claim else "这部分仍待进一步确认",
        "approved_claim_spoken": (
            claim.spoken_summary or claim.approved_meaning
            if claim
            else "这部分仍待进一步确认"
        ),
        "approved_claim_subtitle": (
            claim.subtitle_summary or claim.approved_meaning
            if claim
            else "这部分仍待进一步确认"
        ),
        "claim_conditions": "；".join(claim.conditions) if claim and claim.conditions else "仍需结合现实验证",
        "competing_hypothesis": hypothesis.approved_meaning if hypothesis else "目前没有需要展开的竞争解释",
        "unresolved_condition": (
            hypothesis.approved_meaning
            if hypothesis
            else uncertainty
        ),
        "uncertainty": uncertainty,
    }


def _render(template: str, bindings: dict[str, str]) -> str:
    missing = sorted({match.group(1) for match in PLACEHOLDER_PATTERN.finditer(template)} - set(bindings))
    if missing:
        raise CueRenderError(f"missing_bindings:{','.join(missing)}")
    return PLACEHOLDER_PATTERN.sub(lambda match: bindings[match.group(1)], template).strip()


def _normalize_typography(text: str) -> str:
    text = re.sub(r"。{2,}", "。", text)
    text = re.sub(r"；{2,}", "；", text)
    text = re.sub(r"，{2,}", "，", text)
    text = re.sub(r"[；，]+。", "。", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()
