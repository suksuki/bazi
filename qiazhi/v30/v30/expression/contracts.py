from __future__ import annotations

from typing import Literal

from pydantic import Field

from v30.contracts import ClientKey, LocaleKey, RoleKey, V30Model


ExpressionKind = Literal[
    "mainline_summary",
    "question_recommendation",
    "real_bazi_diagnosis",
    "answer_boundary",
    "portrait_projection",
]


class StyleProfile(V30Model):
    style_profile_id: str
    role_key: RoleKey
    locale: LocaleKey
    client: ClientKey
    voice: str
    density: str
    allowed_terms: list[str] = Field(default_factory=list)
    forbidden_tokens: list[str] = Field(default_factory=list)


class ExpressionFrame(V30Model):
    frame_id: str
    kind: ExpressionKind
    source_ids: list[str] = Field(default_factory=list)
    semantic_intent: str
    bazi_terms: list[str] = Field(default_factory=list)
    user_meaning: str
    boundary: str | None = None


class NarrativePlan(V30Model):
    plan_id: str
    style_profile: StyleProfile
    frames: list[ExpressionFrame]
    output_channel: str


class RenderedNarrative(V30Model):
    narrative_id: str
    plan_id: str
    role_key: RoleKey
    locale: LocaleKey
    client: ClientKey
    text: str
    source_frame_ids: list[str]
    boundary: str | None = None
    diagnostics: dict[str, object] = Field(default_factory=dict)
