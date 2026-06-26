from __future__ import annotations

from v30.expression.contracts import NarrativePlan, RenderedNarrative


def render_narrative(plan: NarrativePlan) -> RenderedNarrative:
    frames = _visible_frames(plan)
    text = _render_zh(frames, plan.style_profile.voice)
    diagnostics = _diagnostics(text, plan)
    return RenderedNarrative(
        narrative_id=f"{plan.plan_id}:rendered",
        plan_id=plan.plan_id,
        role_key=plan.style_profile.role_key,
        locale=plan.style_profile.locale,
        client=plan.style_profile.client,
        text=text,
        source_frame_ids=[frame.frame_id for frame in frames],
        boundary="expression_preserves_runtime_facts_and_boundaries",
        diagnostics=diagnostics,
    )


def _visible_frames(plan: NarrativePlan):
    if plan.style_profile.role_key in {"guest", "user"}:
        return [frame for frame in plan.frames if frame.kind != "portrait_projection"][:4]
    if plan.style_profile.role_key == "practitioner":
        return plan.frames[:5]
    return plan.frames


def _render_zh(frames, voice: str) -> str:
    mainline = next((frame for frame in frames if frame.kind == "mainline_summary"), None)
    question = next((frame for frame in frames if frame.kind == "question_recommendation"), None)
    diagnosis = next((frame for frame in frames if frame.kind == "real_bazi_diagnosis"), None)
    boundary = next((frame for frame in frames if frame.kind == "answer_boundary"), None)
    portraits = [frame for frame in frames if frame.kind == "portrait_projection"]

    parts: list[str] = []
    if mainline is not None:
        parts.append(mainline.user_meaning)
    if question is not None:
        parts.append(question.user_meaning)
    if diagnosis is not None:
        parts.append(diagnosis.user_meaning)
    if portraits:
        parts.append("；".join(frame.user_meaning for frame in portraits[:3]))
    if boundary is not None:
        parts.append(boundary.user_meaning)
    if voice in {"traceable_bazi_analyst", "diagnostic_operator", "validation_researcher"}:
        parts.append("以上文字由表达层生成，来源仍以结构、证据、画像投射和边界为准。")
    return "".join(parts)


def _diagnostics(text: str, plan: NarrativePlan) -> dict[str, object]:
    forbidden_hits = [
        token
        for token in plan.style_profile.forbidden_tokens
        if token and token.lower() in text.lower()
    ]
    return {
        "framework_version": "v30.expression.framework.v1",
        "forbidden_token_hits": forbidden_hits,
        "frame_count": len(plan.frames),
        "visible_frame_count": len(_visible_frames(plan)),
    }
