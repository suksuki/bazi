from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.agent_counterfactuals import (
    reversal_is_actionable,
    reversal_row_ref,
)


class AgentDecisionSide(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rationale: str = Field(min_length=16, max_length=260)
    decisive_checks: tuple[str, ...] = Field(min_length=1, max_length=4)


class AgentReversalTest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str = Field(min_length=12, max_length=180)
    winner_signal: str = Field(
        min_length=8,
        max_length=160,
        description="若与主解释一致的观察出现，则明确维持 PRIMARY。",
    )
    loser_signal: str = Field(
        min_length=8,
        max_length=160,
        description="若相反观察出现，则明确翻转为 ALTERNATIVE；禁止写维持 PRIMARY。",
    )
    decision_row_ref: str | None = Field(
        default=None,
        min_length=4,
        max_length=180,
        exclude_if=lambda value: value is None,
        description="逐字选择绑定 PRIMARY 与 ALTERNATIVE 方法卡、维持与翻转动作的回执。",
    )

    @model_validator(mode="after")
    def signals_are_distinct(self) -> AgentReversalTest:
        if not self.question.rstrip().endswith(("？", "?")):
            raise ValueError("mingli_agent_reversal_question_missing_mark")
        if self.winner_signal.strip() == self.loser_signal.strip():
            raise ValueError("mingli_agent_reversal_signals_not_distinct")
        return self


class AgentHypothesisDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    winner_id: Literal["H1", "H2"]
    loser_id: Literal["H1", "H2"]
    winner: AgentDecisionSide
    loser: AgentDecisionSide
    reversal: AgentReversalTest

    @model_validator(mode="after")
    def ids_are_distinct(self) -> AgentHypothesisDecision:
        if self.winner_id == self.loser_id:
            raise ValueError("mingli_agent_decision_ids_not_distinct")
        return self


def normalize_hypothesis_decision(
    value: Any,
    *,
    normalized: list[dict[str, Any]],
    identity_repaired: set[int],
    preserve_valid: bool,
) -> tuple[dict[str, Any], bool]:
    raw = value if isinstance(value, dict) else {}
    primary = next(item for item in normalized if item["role"] == "PRIMARY")
    alternative = next(item for item in normalized if item["role"] == "ALTERNATIVE")

    if (
        preserve_valid
        and not identity_repaired
        and _decision_matches_hypotheses(
            raw,
            primary=primary,
            alternative=alternative,
        )
    ):
        preserved = dict(raw)
        preserved_reversal = dict(preserved["reversal"])
        if not isinstance(preserved_reversal.get("decision_row_ref"), str):
            preserved_reversal["decision_row_ref"] = reversal_row_ref(
                primary_method_card_ref=str(primary["method_card_ref"]),
                alternative_method_card_ref=str(alternative["method_card_ref"]),
            )
        preserved["reversal"] = preserved_reversal
        return preserved, False

    def side(item: dict[str, Any], label: str) -> dict[str, Any]:
        preferred = (
            ("SUPPORTS", "CONDITIONAL", "UNRESOLVED", "OPPOSES")
            if label == "主解释"
            else ("OPPOSES", "UNRESOLVED", "CONDITIONAL", "SUPPORTS")
        )
        selected = list(
            dict.fromkeys(
                ruling["check_code"]
                for status in preferred
                for ruling in item["method_rulings"]
                if ruling["ruling"] == status
            )
        )[:2]
        decisive = next(
            ruling for ruling in item["method_rulings"] if ruling["check_code"] == selected[0]
        )
        counts = {
            status: sum(ruling["ruling"] == status for ruling in item["method_rulings"])
            for status in ("SUPPORTS", "CONDITIONAL", "UNRESOLVED", "OPPOSES")
        }
        rationale = (
            f"{item.get('name', label)}"
            f"{'暂列主线' if label == '主解释' else '暂不列主线'}："
            f"{counts['SUPPORTS']}项支持、{counts['CONDITIONAL']}项有条件、"
            f"{counts['UNRESOLVED']}项未决、{counts['OPPOSES']}项反对；"
            f"{decisive['rationale']}"
        )[:260]
        return {"rationale": rationale, "decisive_checks": selected[:4]}

    reversal = raw.get("reversal")
    reversal = reversal if isinstance(reversal, dict) else {}
    question = reversal.get("question")
    if not isinstance(question, str) or len(question.strip()) < 12:
        question = "现实中更常先出现成果转化，还是先出现责任压力？"
    if not question.rstrip().endswith(("？", "?")):
        question = f"{question.rstrip('。！!')}？"
    raw_winner_id = raw.get("winner_id")
    raw_loser_id = raw.get("loser_id")
    signal_by_hypothesis: dict[str, Any] = {}
    if (
        raw_winner_id in {"H1", "H2"}
        and raw_loser_id in {"H1", "H2"}
        and raw_winner_id != raw_loser_id
    ):
        signal_by_hypothesis = {
            str(raw_winner_id): reversal.get("winner_signal"),
            str(raw_loser_id): reversal.get("loser_signal"),
        }
    repaired_ids = {f"H{index + 1}" for index in identity_repaired}
    winner_signal = (
        None
        if primary["hypothesis_id"] in repaired_ids
        else signal_by_hypothesis.get(primary["hypothesis_id"])
    )
    if not isinstance(winner_signal, str) or len(winner_signal.strip()) < 8:
        winner_signal = f"若更符合{primary.get('name', '主解释')}，维持当前判断。"
    elif primary.get("name") not in winner_signal:
        winner_signal = f"更符合{primary['name']}：{winner_signal}"
    loser_signal = (
        None
        if alternative["hypothesis_id"] in repaired_ids
        else signal_by_hypothesis.get(alternative["hypothesis_id"])
    )
    if not isinstance(loser_signal, str) or len(loser_signal.strip()) < 8:
        loser_signal = f"若更符合{alternative.get('name', '替代解释')}，就翻转主次。"
    elif alternative.get("name") not in loser_signal:
        loser_signal = f"更符合{alternative['name']}：{loser_signal}"
    return {
        "winner_id": primary["hypothesis_id"],
        "loser_id": alternative["hypothesis_id"],
        "winner": side(primary, "主解释"),
        "loser": side(alternative, "替代解释"),
        "reversal": {
            "question": question,
            "winner_signal": winner_signal[:160],
            "loser_signal": loser_signal[:160],
            "decision_row_ref": reversal_row_ref(
                primary_method_card_ref=str(primary["method_card_ref"]),
                alternative_method_card_ref=str(alternative["method_card_ref"]),
            ),
        },
    }, preserve_valid


def _decision_matches_hypotheses(
    raw: dict[str, Any],
    *,
    primary: dict[str, Any],
    alternative: dict[str, Any],
) -> bool:
    try:
        decision = AgentHypothesisDecision.model_validate(raw)
    except ValueError:
        return False
    if (
        decision.winner_id != primary["hypothesis_id"]
        or decision.loser_id != alternative["hypothesis_id"]
    ):
        return False
    for side, hypothesis in (
        (decision.winner, primary),
        (decision.loser, alternative),
    ):
        allowed = {item["check_code"] for item in hypothesis["method_rulings"]}
        if not set(side.decisive_checks).issubset(allowed):
            return False
    return reversal_is_actionable(
        winner_signal=decision.reversal.winner_signal,
        loser_signal=decision.reversal.loser_signal,
        primary_name=primary.get("name"),
        alternative_name=alternative.get("name"),
    ) and (
        decision.reversal.decision_row_ref is None
        or decision.reversal.decision_row_ref
        == reversal_row_ref(
            primary_method_card_ref=str(primary["method_card_ref"]),
            alternative_method_card_ref=str(alternative["method_card_ref"]),
        )
    )
