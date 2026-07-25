from __future__ import annotations

import re
from datetime import datetime

from experience.compiler import canonical_hash
from experience.contracts import (
    ActorTrackItem,
    CameraTrackItem,
    MingliExperienceEnvelope,
    PerformanceAudioTrack,
    PerformanceCueInstance,
    PerformancePackage,
    PerformanceStageSnapshot,
    PerformanceStageTrackItem,
    SubtitleTrackItem,
    VisemeTrackItem,
)


SENTENCE_PATTERN = re.compile(r"[^。！？!?；;]+[。！？!?；;]?|[^。！？!?；;]+$")


def compile_performance_package(
    *,
    package_id: str,
    cue: PerformanceCueInstance,
    envelope: MingliExperienceEnvelope | None,
    audio_uri: str,
    audio_sha256: str,
    duration_ms: int,
    sample_rate: int,
    speech_start_ms: int,
    voice_id: str,
    voice_version: str,
    viseme_track: list[VisemeTrackItem],
    frozen_at: datetime,
) -> PerformancePackage:
    """Compile one immutable, audio-clocked performance without new cognition."""

    claim = _selected_claim(cue=cue, envelope=envelope)
    reasoning_steps = list(envelope.approved_reasoning_steps) if envelope and claim else []
    chart_facts = list(envelope.allowed_chart_facts) if envelope else []
    unresolved_text, unresolved_refs = _unresolved(envelope)
    subtitle_track = _subtitle_track(
        dialogue=cue.final_dialogue,
        claim_refs=cue.claim_refs,
        speech_start_ms=speech_start_ms,
        duration_ms=duration_ms,
    )
    stage_snapshot = PerformanceStageSnapshot(
        chart_facts=chart_facts,
        approved_claim=claim,
        reasoning_steps=reasoning_steps,
        unresolved_text=unresolved_text,
        unresolved_refs=unresolved_refs,
    )
    actor_track = _actor_track(duration_ms=duration_ms, speech_start_ms=speech_start_ms)
    stage_track = _stage_track(
        duration_ms=duration_ms,
        chart_facts=chart_facts,
        reasoning_steps=reasoning_steps,
        claim_ref=claim.claim_ref if claim else "",
        unresolved=bool(unresolved_text),
    )
    camera_track = _camera_track(duration_ms=duration_ms)
    audio = PerformanceAudioTrack(
        uri=audio_uri,
        sha256=audio_sha256,
        duration_ms=duration_ms,
        sample_rate=sample_rate,
        speech_start_ms=speech_start_ms,
        voice_id=voice_id,
        voice_version=voice_version,
    )
    payload = {
        "package_id": package_id,
        "cue_instance_id": cue.cue_instance_id,
        "participant_run_id": cue.participant_run_id,
        "visibility": cue.visibility,
        "dialogue": cue.final_dialogue,
        "audio": audio.model_dump(mode="json"),
        "subtitle_track": [item.model_dump(mode="json") for item in subtitle_track],
        "viseme_track": [item.model_dump(mode="json") for item in viseme_track],
        "actor_track": [item.model_dump(mode="json") for item in actor_track],
        "stage_track": [item.model_dump(mode="json") for item in stage_track],
        "camera_track": [item.model_dump(mode="json") for item in camera_track],
        "stage_snapshot": stage_snapshot.model_dump(mode="json"),
        "actor_renderer_contract_version": "abu-actor-renderer.v1",
        "actor_asset_version": "webp-fallback.v1",
        "envelope_id": cue.envelope_id,
        "envelope_hash": cue.envelope_hash,
        "claim_refs": cue.claim_refs,
        "cue_hash": cue.cue_hash,
        "frozen_at": frozen_at.isoformat(),
    }
    return PerformancePackage(
        **payload,
        package_hash=canonical_hash(payload),
    )


def _selected_claim(*, cue: PerformanceCueInstance, envelope: MingliExperienceEnvelope | None):
    if not envelope or not cue.claim_refs:
        return None
    selected = set(cue.claim_refs)
    return next((item for item in envelope.approved_claims if item.claim_ref in selected), None)


def _unresolved(envelope: MingliExperienceEnvelope | None) -> tuple[str, list[str]]:
    if not envelope:
        return "", []
    if envelope.competing_hypotheses:
        hypothesis = envelope.competing_hypotheses[0]
        text = hypothesis.approved_meaning
        if hypothesis.unresolved_reason:
            text = f"{text}。{hypothesis.unresolved_reason}"
        return text, [hypothesis.hypothesis_ref, *hypothesis.supporting_refs]
    if envelope.uncertainty.reasons:
        return envelope.uncertainty.reasons[0], []
    return "", []


def _subtitle_track(
    *,
    dialogue: str,
    claim_refs: list[str],
    speech_start_ms: int,
    duration_ms: int,
) -> list[SubtitleTrackItem]:
    segments = [match.group(0).strip() for match in SENTENCE_PATTERN.finditer(dialogue) if match.group(0).strip()]
    if not segments:
        segments = [dialogue]
    speech_end_ms = max(speech_start_ms + 1, duration_ms - 280)
    available = max(1, speech_end_ms - speech_start_ms)
    weights = [max(3, len(re.sub(r"\s+", "", item))) for item in segments]
    total_weight = sum(weights)
    cursor = speech_start_ms
    rows: list[SubtitleTrackItem] = []
    for index, (text, weight) in enumerate(zip(segments, weights, strict=True)):
        if index == len(segments) - 1:
            end = speech_end_ms
        else:
            end = cursor + max(240, round(available * weight / total_weight))
            end = min(end, speech_end_ms - (len(segments) - index - 1))
        rows.append(
            SubtitleTrackItem(
                start_ms=cursor,
                end_ms=max(cursor + 1, end),
                text=text,
                claim_refs=claim_refs,
            )
        )
        cursor = rows[-1].end_ms
    return rows


def _actor_track(*, duration_ms: int, speech_start_ms: int) -> list[ActorTrackItem]:
    return [
        ActorTrackItem(at_ms=0, action="enter", expression="welcoming"),
        ActorTrackItem(at_ms=speech_start_ms, action="speak", expression="warm"),
        ActorTrackItem(at_ms=round(duration_ms * 0.24), action="push_report", expression="gentle"),
        ActorTrackItem(at_ms=round(duration_ms * 0.36), action="point_chart", expression="focused", target="chart"),
        ActorTrackItem(at_ms=round(duration_ms * 0.54), action="point_path", expression="explaining", target="approved-path"),
        ActorTrackItem(at_ms=round(duration_ms * 0.76), action="serious", expression="serious", target="unresolved"),
        ActorTrackItem(at_ms=round(duration_ms * 0.91), action="listen", expression="attentive", target="participant"),
    ]


def _stage_track(
    *,
    duration_ms: int,
    chart_facts,
    reasoning_steps,
    claim_ref: str,
    unresolved: bool,
) -> list[PerformanceStageTrackItem]:
    rows = [PerformanceStageTrackItem(at_ms=0, action="reset")]
    chart_start = round(duration_ms * 0.35)
    for index, fact in enumerate(chart_facts):
        rows.append(
            PerformanceStageTrackItem(
                at_ms=chart_start + index * 260,
                action="reveal_chart_fact",
                target_ref=fact.fact_ref,
                visual_anchor=fact.visual_anchor,
            )
        )
    path_start = round(duration_ms * 0.53)
    for index, step in enumerate(reasoning_steps):
        rows.append(
            PerformanceStageTrackItem(
                at_ms=path_start + index * 520,
                action="reveal_reasoning_step",
                target_ref=step.step_ref,
                visual_anchor=step.visual_anchor,
            )
        )
    if claim_ref:
        rows.append(
            PerformanceStageTrackItem(
                at_ms=round(duration_ms * 0.69),
                action="highlight_approved_path",
                target_ref=claim_ref,
                visual_anchor="approved-path",
            )
        )
    if unresolved:
        rows.append(
            PerformanceStageTrackItem(
                at_ms=round(duration_ms * 0.76),
                action="show_unresolved_condition",
                visual_anchor="unresolved-condition",
            )
        )
    return sorted(rows, key=lambda item: item.at_ms)


def _camera_track(*, duration_ms: int) -> list[CameraTrackItem]:
    return [
        CameraTrackItem(at_ms=0, framing="wide"),
        CameraTrackItem(at_ms=round(duration_ms * 0.10), framing="actor"),
        CameraTrackItem(at_ms=round(duration_ms * 0.34), framing="chart"),
        CameraTrackItem(at_ms=round(duration_ms * 0.52), framing="path"),
        CameraTrackItem(at_ms=round(duration_ms * 0.90), framing="choice"),
    ]
