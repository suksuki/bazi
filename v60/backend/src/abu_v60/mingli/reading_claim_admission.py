from __future__ import annotations

from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.agent_method_cards import FALLBACK_METHOD_CARD_REF
from abu_v60.mingli.agent_method_distillation import exact_role_paths


def domain_method_assessment_codes(
    *,
    semantic_key: str,
    prose: str,
) -> tuple[str, ...]:
    """Reject unqualified life stories without suppressing the whole reading."""

    issues: list[str] = []
    shortcut_story = any(
        term in prose
        for term in (
            "精神共鸣",
            "精神交流",
            "精神依恋",
            "精神滋养",
            "精神慰藉",
            "情感安全",
        )
    ) and any(term in prose for term in ("偏印", "正印", "印星"))
    if shortcut_story:
        issues.append("TEN_GOD_TO_LIFE_STORY_SHORTCUT")

    if semantic_key in {"DOMAIN_RELATIONSHIP", "DOMAIN_FAMILY"}:
        # The output contract has no typed axis selection or admitted positive
        # domain rule. Keywords cannot substitute for that missing method.
        issues.append("DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED")
    return tuple(issues)


def exact_role_path_assessment_codes(
    *,
    hypothesis: object,
    packet: MingliAgentCasePacket,
) -> tuple[str, ...]:
    """Require a distilled mechanism to name one chart-bound ten-god path."""

    method_card_ref = str(getattr(hypothesis, "method_card_ref", ""))
    if method_card_ref == FALLBACK_METHOD_CARD_REF:
        return ()
    observation = next(
        (item for item in packet.mechanism_observations if item.evidence_id == method_card_ref),
        None,
    )
    if observation is None:
        return ("EXACT_ROLE_PATH_MISSING",)
    occurrences: dict[str, list[str]] = {}
    for pillar in packet.pillars:
        occurrences.setdefault(pillar.visible_ten_god, []).append(f"{pillar.slot}干{pillar.stem}")
        for hidden_stem, ten_god in zip(
            pillar.hidden_stems,
            pillar.hidden_ten_gods,
            strict=True,
        ):
            occurrences.setdefault(ten_god, []).append(f"{pillar.slot}支藏{hidden_stem}")
    paths = exact_role_paths(observation.pattern_ref, occurrences)
    if not paths:
        return ()
    prose = "\n".join(
        (
            str(getattr(hypothesis, "name", "")),
            str(getattr(hypothesis, "thesis", "")),
            *(
                f"{ruling.rationale}\n{ruling.condition_or_falsifier}"
                for ruling in getattr(hypothesis, "method_rulings", ())
            ),
        )
    )
    if any(
        str(path["source"]["ten_god"]) in prose and str(path["target"]["ten_god"]) in prose
        for path in paths
    ):
        return ()
    return ("EXACT_ROLE_PATH_MISSING",)
