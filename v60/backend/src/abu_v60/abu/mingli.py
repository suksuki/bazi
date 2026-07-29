from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from abu_v60.mingli.explanation_contracts import MingliExplanationEnvelope
from abu_v60.mingli.mechanism_qualification_contracts import (
    MingliMechanismQualificationEnvelope,
)
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.provenance import content_hash, stable_ref


class MingliAbuExpression(BaseModel):
    """Abu's bounded expression of one existing Mingli Reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expression_ref: str = Field(min_length=1)
    expression_hash: str = Field(min_length=64, max_length=64)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    explanation_ref: str | None = None
    explanation_hash: str | None = Field(default=None, min_length=64, max_length=64)
    qualification_ref: str | None = None
    qualification_hash: str | None = Field(default=None, min_length=64, max_length=64)
    authority: Literal["EXPRESSION_ONLY"]
    summary: str = Field(min_length=1)
    known: str = Field(min_length=1)
    boundary: str = Field(min_length=1)
    next_attention: str = Field(min_length=1)
    evidence_gap_summary: str = Field(min_length=1)
    fact_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    confirmed_claim_count: int = Field(ge=0)
    candidate_claim_count: int = Field(ge=0)
    observation_claim_count: int = Field(ge=0)
    fact_creation: Literal[False]
    decision_creation: Literal[False]


class MingliAbuExpressionProjector:
    """Turn a Reading into native Abu copy without running a second analysis."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        explanation: MingliExplanationEnvelope | None = None,
        qualification: MingliMechanismQualificationEnvelope | None = None,
    ) -> MingliAbuExpression:
        fact_count = len(reading.fact_refs)
        candidate_count = len(reading.candidate_refs)
        if candidate_count:
            boundary = (
                f"我看见 {candidate_count} 处值得追查的结构联系；"
                "它们现在只是线索，还不能直接当成已经成立的做功。"
            )
            next_attention = "下一步要核对根、透、时运与真实经历是否共同支持这些联系。"
        else:
            boundary = "当前基础事实里，还没有形成可安全展示的结构联系。"
            next_attention = "先保留空白，等新的正式事实或规则进入后再继续读。"
        payload = {
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
            "explanation_ref": (explanation.explanation_ref if explanation is not None else None),
            "explanation_hash": (explanation.explanation_hash if explanation is not None else None),
            "qualification_ref": (
                qualification.qualification_ref if qualification is not None else None
            ),
            "qualification_hash": (
                qualification.qualification_hash if qualification is not None else None
            ),
            "authority": "EXPRESSION_ONLY",
            "summary": (
                "我会把已经确认、值得追查和仍不知道的部分分开陪你看。"
                if explanation is not None
                else "阿布正在陪你读同一份命理结果。"
            ),
            "known": (
                f"这次读取有 {explanation.confirmed_count} 组确定结论、"
                f"{explanation.candidate_count} 条候选解释和"
                f"{explanation.observation_count} 个现实观察窗口。"
                if explanation is not None
                else f"这次读取确认了四柱与 {fact_count} 条有来源的基础事实。"
            ),
            "boundary": boundary,
            "next_attention": next_attention,
            "evidence_gap_summary": (
                qualification.summary
                if qualification is not None
                else "当前没有生成同源的机制证据缺口清单。"
            ),
            "fact_refs": reading.fact_refs,
            "candidate_refs": reading.candidate_refs,
            "confirmed_claim_count": (
                explanation.confirmed_count if explanation is not None else 0
            ),
            "candidate_claim_count": (
                explanation.candidate_count if explanation is not None else candidate_count
            ),
            "observation_claim_count": (
                explanation.observation_count if explanation is not None else 0
            ),
            "fact_creation": False,
            "decision_creation": False,
        }
        return MingliAbuExpression(
            expression_ref=stable_ref("v60-mingli-abu-expression", payload),
            expression_hash=content_hash(payload),
            **payload,
        )
