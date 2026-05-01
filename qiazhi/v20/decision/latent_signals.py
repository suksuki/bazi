from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.learning.latent_factor_calibration import latent_factor_calibration_manifest
from v20.measurement.dimensions import dimension_payload


@dataclass(frozen=True)
class HiddenAttribute:
    attribute_key: str
    label: str
    domain: str
    source_layer: str
    evidence: tuple[str, ...]
    activation_paths: tuple[str, ...]
    visibility: str = "latent"
    runtime_verdict: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | dimension_payload(self.domain)


@dataclass(frozen=True)
class AmplificationFactor:
    factor_key: str
    label: str
    domain: str
    reason: str
    multiplier: float
    evidence: tuple[str, ...]
    applies_to: tuple[str, ...]
    runtime_verdict: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | dimension_payload(self.domain)


def build_latent_signal_report(
    facts: ChartFacts,
    core: CoreInference,
    time_context: TimeContext,
    decision_report: dict[str, object] | None = None,
) -> dict[str, object]:
    hidden_attributes = _hidden_attributes(facts, time_context)
    amplifiers = _amplifiers(facts, core, time_context, decision_report or {})
    return {
        "version": "v20.latent_signal_report.v1",
        "status": "ready" if hidden_attributes or amplifiers else "empty",
        "structural_hidden_attribute_count": len(hidden_attributes),
        "amplifier_count": len(amplifiers),
        "structural_hidden_attributes": [row.to_dict() for row in hidden_attributes],
        "chart_attention_amplifiers": [row.to_dict() for row in amplifiers],
        "personal_calibration_factor_manifest": latent_factor_calibration_manifest(),
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURAL_HIDDEN_ATTRIBUTES_ARE_CHART_MATERIAL_NOT_PERSONAL_SETTINGS",
            "CHART_ATTENTION_AMPLIFIERS_ADJUST_ATTENTION_NOT_RULE_TRUTH",
            "P64_LATENT_FACTORS_MODEL_PERSONAL_HIDDEN_SETTINGS_AND_CHANGE_AMPLIFIERS",
            "TIME_LAYER_CAN_ACTIVATE_BUT_NOT_INVENT_FACTS",
            "LLM_MAY_EXPLAIN_LATENT_SIGNALS_NOT_PROMOTE_THEM",
        ],
    }


def _hidden_attributes(facts: ChartFacts, time_context: TimeContext) -> list[HiddenAttribute]:
    rows: list[HiddenAttribute] = []
    hidden_labels = _label_positions(facts.hidden_ten_gods)
    visible_labels = {row.label for row in facts.visible_ten_gods}
    for label, positions in hidden_labels.items():
        if label in visible_labels:
            continue
        domain = _domain_for_ten_god(label)
        rows.append(
            HiddenAttribute(
                attribute_key=f"hidden.ten_god.{label}",
                label=f"{label}藏于地支",
                domain=domain,
                source_layer="hidden_stem",
                evidence=tuple(positions[:4]),
                activation_paths=("透干", "合冲引动", "大运流年同类十神引动"),
            )
        )
    if facts.vault_branches:
        rows.append(
            HiddenAttribute(
                attribute_key="hidden.branch.vault",
                label="墓库/藏气需要开启条件",
                domain="branch",
                source_layer="branch_vault",
                evidence=tuple(facts.vault_branches[:4]),
                activation_paths=("冲开", "合动", "大运流年引动"),
            )
        )
    if time_context.status == "ready":
        time_labels = {layer.ten_god.label for layer in time_context.layers if layer.ten_god.label}
        latent_matches = sorted(time_labels & set(hidden_labels))
        if latent_matches:
            rows.append(
                HiddenAttribute(
                    attribute_key="hidden.time.activates_hidden_ten_god",
                    label="时间层触发藏干十神",
                    domain="time",
                    source_layer="time_to_hidden",
                    evidence=tuple(latent_matches[:4]),
                    activation_paths=("显式大运流年同类十神", "时间层与原局互动"),
                    visibility="activated_context",
                )
            )
    return rows[:12]


def _amplifiers(
    facts: ChartFacts,
    core: CoreInference,
    time_context: TimeContext,
    decision_report: dict[str, object],
) -> list[AmplificationFactor]:
    rows: list[AmplificationFactor] = []
    labels = [row.label for row in (*facts.visible_ten_gods, *facts.hidden_ten_gods) if row.label]
    for label, count in Counter(labels).most_common(5):
        if count >= 3:
            rows.append(
                AmplificationFactor(
                    factor_key=f"amplifier.ten_god.repeat.{label}",
                    label=f"{label}重复出现",
                    domain=_domain_for_ten_god(label),
                    reason="同类十神在明透或藏干中重复出现，需要提高关注度。",
                    multiplier=round(1.0 + min(0.35, count * 0.06), 2),
                    evidence=(f"count={count}",),
                    applies_to=("portrait_ranking", "question_ranking", "llm_context"),
                )
            )
    if facts.relation_hits:
        rows.append(
            AmplificationFactor(
                factor_key="amplifier.branch.relation_density",
                label="地支互动密度",
                domain="branch",
                reason="原局存在冲合刑害等互动，结构牵动性上升。",
                multiplier=round(1.0 + min(0.3, len(facts.relation_hits) * 0.05), 2),
                evidence=tuple(f"{row.relation_type}:{'/'.join(row.branches)}" for row in facts.relation_hits[:5]),
                applies_to=("portrait_ranking", "question_ranking"),
            )
        )
    if time_context.status == "ready":
        rows.append(
            AmplificationFactor(
                factor_key="amplifier.time.explicit_context",
                label="显式时间层参与",
                domain="time",
                reason="用户提供了大运或流年，时间触发维度的关注度提高。",
                multiplier=round(1.0 + min(0.35, len(time_context.layers) * 0.08 + len(time_context.relation_hits) * 0.05), 2),
                evidence=tuple(layer.pillar.display for layer in time_context.layers[:4]),
                applies_to=("question_ranking", "answer_context"),
            )
        )
    spread = abs(core.support_score - core.pressure_score)
    if spread >= 0.2:
        rows.append(
            AmplificationFactor(
                factor_key="amplifier.strength.support_pressure_spread",
                label="扶助压力差距",
                domain="strength",
                reason="扶助与压力差距明显，日主承载维度需要提前说明。",
                multiplier=round(1.0 + min(0.28, spread * 0.2), 2),
                evidence=(f"support={core.support_score}", f"pressure={core.pressure_score}"),
                applies_to=("portrait_ranking", "answer_context"),
            )
        )
    decision_domains = Counter(
        str(row.get("domain", ""))
        for row in decision_report.get("decisions", ())
        if isinstance(row, dict)
    )
    for domain, count in decision_domains.most_common(3):
        if count >= 3 and domain:
            rows.append(
                AmplificationFactor(
                    factor_key=f"amplifier.decision.density.{domain}",
                    label=f"{_domain_label(domain)}裁决密度",
                    domain=domain,
                    reason="同一维度下多条动态裁决同时出现，应提升为当前盘的关注主题。",
                    multiplier=round(1.0 + min(0.24, count * 0.04), 2),
                    evidence=(f"decision_count={count}",),
                    applies_to=("portrait_ranking", "question_ranking", "llm_context"),
                )
            )
    return rows[:12]


def _label_positions(rows: tuple[object, ...]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for row in rows:
        label = str(getattr(row, "label", ""))
        if label:
            output.setdefault(label, []).append(f"{label}@{getattr(row, 'pillar', '')}藏干")
    return output


def _domain_for_ten_god(label: str) -> str:
    if label in {"正财", "偏财"}:
        return "wealth"
    if label in {"正官", "七杀", "食神", "伤官", "正印", "偏印"}:
        return "career"
    if label in {"比肩", "劫财"}:
        return "strength"
    return "ten_god"


def _domain_label(domain: str) -> str:
    return {
        "strength": "强弱",
        "ten_god": "十神",
        "branch": "地支",
        "time": "时间",
        "wealth": "财运",
        "career": "事业",
        "relationship": "关系",
        "health": "健康",
        "pattern": "格局",
        "useful_god": "用神",
    }.get(domain, domain)
