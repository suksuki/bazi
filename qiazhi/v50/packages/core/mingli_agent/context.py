from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import Field

from core.contracts.base import V50Model
from core.mingli_agent.contracts import ChartWorldInstance, WorldFact


ContextStage = Literal["baseline", "pattern", "work_path", "ziwei_integration", "prediction", "career", "wealth", "domain", "case_turn"]
AttentionPriority = Literal["critical", "high", "supporting", "context"]


class AttentionItemReceipt(V50Model):
    fact_ref: str
    category: str
    selected: bool
    priority: AttentionPriority
    signal: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class AttentionReceipt(V50Model):
    stage: ContextStage
    items: list[AttentionItemReceipt] = Field(default_factory=list)
    selected_fact_refs: list[str] = Field(default_factory=list)
    omitted_fact_refs: list[str] = Field(default_factory=list)
    critical_omission_refs: list[str] = Field(default_factory=list)
    coverage_by_category: dict[str, dict[str, int]] = Field(default_factory=dict)


class ReasoningContextPack(V50Model):
    stage: ContextStage
    payload: dict[str, Any]
    fact_refs: list[str] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)
    excluded_fact_count: int = 0
    excluded_knowledge_count: int = 0
    attention_receipt: AttentionReceipt
    content_hash: str
    reasoning_phase: Literal["independent_observation", "tool_challenge", "cross_lens", "domain", "case_revision"]
    experimental_tool_refs: list[str] = Field(default_factory=list)


class MingliContextCompiler:
    """Builds minimum sufficient stage context from the immutable chart world."""

    FACT_LIMITS: dict[ContextStage, dict[str, int]] = {
        "baseline": {
            "graph_relation": 18,
            "candidate_path": 6,
            "candidate_node_role": 6,
            "estimated_sensitivity": 4,
            "tool_salience": 5,
            "ziwei_source_quality": 1,
            "ziwei_palace": 4,
            "ziwei_star": 3,
            "ziwei_four_transformation": 2,
            "ziwei_palace_relation": 2,
        },
        "pattern": {"graph_relation": 28},
        "work_path": {"graph_relation": 8, "candidate_path": 5, "candidate_node_role": 5, "estimated_sensitivity": 4, "tool_salience": 4},
        "ziwei_integration": {
            "ziwei_source_quality": 1,
            "ziwei_palace": 3,
            "ziwei_star": 2,
            "ziwei_four_transformation": 1,
            "ziwei_time_window": 1,
            "ziwei_palace_relation": 1,
        },
        "prediction": {"graph_relation": 4, "candidate_path": 3, "candidate_node_role": 3, "estimated_sensitivity": 2, "tool_salience": 3},
        "career": {"graph_relation": 5, "candidate_path": 4, "candidate_node_role": 4, "estimated_sensitivity": 3, "tool_salience": 3},
        "wealth": {"graph_relation": 5, "candidate_path": 4, "candidate_node_role": 4, "estimated_sensitivity": 3, "tool_salience": 3},
        "domain": {"graph_relation": 5, "candidate_path": 4, "candidate_node_role": 4, "estimated_sensitivity": 3, "tool_salience": 3, "ziwei_palace": 4, "ziwei_star": 3, "ziwei_time_window": 2},
        "case_turn": {"graph_relation": 3, "candidate_path": 2, "candidate_node_role": 2, "estimated_sensitivity": 2, "tool_salience": 2},
    }

    KNOWLEDGE_LIMITS: dict[ContextStage, int] = {
        "baseline": 8,
        "pattern": 6,
        "work_path": 5,
        "ziwei_integration": 3,
        "prediction": 2,
        "career": 4,
        "wealth": 4,
        "domain": 4,
        "case_turn": 2,
    }

    LEDGER_CATEGORIES = {"pillars", "day_master", "month_branch", "visible", "hidden_stems", "root_strength", "branch_relations"}
    DOMAIN_CONTEXT_CATEGORIES = {"timing_material"}

    def compile(
        self,
        *,
        world: ChartWorldInstance,
        stage: ContextStage,
        cognitive_state: dict[str, Any] | None = None,
    ) -> ReasoningContextPack:
        immutable_ledger = _immutable_ledger(world=world, categories=self.LEDGER_CATEGORIES)
        selected_facts, attention_receipt = self._select_facts(world=world, stage=stage)
        reasoning_phase = _reasoning_phase(stage)
        experimental_tool_refs = [
            item.fact_id for item in selected_facts if item.authority == "experimental_tool_observation"
        ]

        knowledge_limit = self.KNOWLEDGE_LIMITS[stage]
        selected_knowledge = world.knowledge[:knowledge_limit]
        payload: dict[str, Any] = {
            "world_id": world.world_id,
            "reasoning_phase": reasoning_phase,
            "pillars": world.pillars,
            "birth_profile": {
                "gender": world.birth_profile.get("gender"),
                "birth_date": world.birth_profile.get("birth_date"),
                "birth_time": world.birth_profile.get("birth_time"),
                "birth_location": _public_birth_location(world.birth_profile.get("birth_location")),
            },
            "immutable_chart_ledger": immutable_ledger,
            "element_role_ledger": _element_role_ledger(immutable_ledger),
            "element_cycles": {
                "generates": ["木生火", "火生土", "土生金", "金生水", "水生木"],
                "controls": ["木克土", "土克水", "水克火", "火克金", "金克木"],
            },
            "attention": [
                {
                    "fact_ref": item.fact_ref,
                    "category": item.category,
                    "priority": item.priority,
                    "reasons": item.reasons,
                }
                for item in attention_receipt.items
                if item.selected and item.priority in {"critical", "high"}
            ],
            "facts": [
                {
                    "id": item.fact_id,
                    "kind": item.kind,
                    "category": item.category,
                    "authority": item.authority,
                    "authority_status": _authority_status(item),
                    "statement": item.statement,
                }
                for item in selected_facts
                if item.category != "research_fixture_prior"
            ],
            "knowledge": [
                {
                    "id": item.knowledge_id,
                    "title": item.title,
                    "summary": item.summary,
                    "conditions": item.conditions,
                    "counter_conditions": item.counter_conditions,
                    "controversy": item.controversy,
                }
                for item in selected_knowledge
            ],
            "timing_context": world.timing_context if stage in {"career", "wealth", "domain", "case_turn"} else {},
            "ziwei_profile": world.ziwei_profile if stage in {"baseline", "ziwei_integration", "domain"} else {},
            "boundaries": world.boundaries,
        }
        if cognitive_state:
            payload["frozen_cognitive_state"] = cognitive_state
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return ReasoningContextPack(
            stage=stage,
            payload=payload,
            fact_refs=[item.fact_id for item in selected_facts],
            knowledge_refs=[item.knowledge_id for item in selected_knowledge],
            excluded_fact_count=max(0, len(world.facts) - len(selected_facts)),
            excluded_knowledge_count=max(0, len(world.knowledge) - len(selected_knowledge)),
            attention_receipt=attention_receipt,
            content_hash=hashlib.sha256(encoded).hexdigest()[:20],
            reasoning_phase=reasoning_phase,
            experimental_tool_refs=experimental_tool_refs,
        )

    def _select_facts(
        self,
        *,
        world: ChartWorldInstance,
        stage: ContextStage,
    ) -> tuple[list[WorldFact], AttentionReceipt]:
        limits = self.FACT_LIMITS[stage]
        candidates: list[tuple[WorldFact, AttentionPriority, float, list[str]]] = []
        excluded: list[AttentionItemReceipt] = []
        for item in world.facts:
            eligible, reason = self._eligible(item=item, stage=stage)
            priority, signal, reasons = _attention_features(item=item, stage=stage)
            if not eligible:
                excluded.append(
                    AttentionItemReceipt(
                        fact_ref=item.fact_id,
                        category=item.category,
                        selected=False,
                        priority=priority,
                        signal=signal,
                        reasons=[reason, *reasons],
                    )
                )
                continue
            candidates.append((item, priority, signal, reasons))

        priority_order = {"critical": 0, "high": 1, "supporting": 2, "context": 3}
        candidates.sort(key=lambda row: (priority_order[row[1]], -row[2], row[0].category, row[0].fact_id))
        counts: dict[str, int] = {}
        selected: list[WorldFact] = []
        receipts: list[AttentionItemReceipt] = []
        for item, priority, signal, reasons in candidates:
            limit = limits.get(item.category)
            within_limit = item.category in self.LEDGER_CATEGORIES or limit is None or counts.get(item.category, 0) < limit
            if within_limit:
                selected.append(item)
                counts[item.category] = counts.get(item.category, 0) + 1
                receipts.append(
                    AttentionItemReceipt(
                        fact_ref=item.fact_id,
                        category=item.category,
                        selected=True,
                        priority=priority,
                        signal=signal,
                        reasons=reasons,
                    )
                )
            else:
                receipts.append(
                    AttentionItemReceipt(
                        fact_ref=item.fact_id,
                        category=item.category,
                        selected=False,
                        priority=priority,
                        signal=signal,
                        reasons=["category_limit_reached", *reasons],
                    )
                )

        all_receipts = [*receipts, *excluded]
        all_receipts.sort(key=lambda item: (not item.selected, priority_order[item.priority], -item.signal, item.fact_ref))
        coverage: dict[str, dict[str, int]] = {}
        for item in all_receipts:
            bucket = coverage.setdefault(item.category, {"selected": 0, "omitted": 0})
            bucket["selected" if item.selected else "omitted"] += 1
        receipt = AttentionReceipt(
            stage=stage,
            items=all_receipts,
            selected_fact_refs=[item.fact_id for item in selected],
            omitted_fact_refs=[item.fact_ref for item in all_receipts if not item.selected],
            critical_omission_refs=[
                item.fact_ref for item in all_receipts if not item.selected and item.priority == "critical" and "stage_not_relevant" not in item.reasons
            ],
            coverage_by_category=coverage,
        )
        return selected, receipt

    def _eligible(self, *, item: WorldFact, stage: ContextStage) -> tuple[bool, str]:
        if item.category == "research_fixture_prior":
            return False, "synthetic_expected_contract_isolated"
        if _reasoning_phase(stage) == "independent_observation" and _authority_status(item) != "production":
            return False, "independent_first_look_authority_isolation"
        if item.category in self.LEDGER_CATEGORIES:
            return True, "immutable_ledger"
        if item.category.startswith("ziwei_"):
            return (stage in {"baseline", "ziwei_integration", "domain"}), "stage_not_relevant"
        if item.category in self.DOMAIN_CONTEXT_CATEGORIES:
            return (stage in {"career", "wealth", "domain", "case_turn"}), "stage_not_relevant"
        return (item.category in self.FACT_LIMITS[stage]), "stage_not_relevant"


def _attention_features(*, item: WorldFact, stage: ContextStage) -> tuple[AttentionPriority, float, list[str]]:
    payload = item.payload
    if item.category in MingliContextCompiler.LEDGER_CATEGORIES:
        return "critical", 1.0, ["immutable_chart_fact"]

    signal = 0.0
    reasons: list[str] = []
    numeric_keys = {
        "candidate_path": ("tool_score",),
        "candidate_node_role": ("confidence",),
        "estimated_sensitivity": ("state_delta",),
        "tool_salience": ("tool_score", "bridge", "criticality", "season"),
    }.get(item.category, ())
    values = [abs(float(payload[key])) for key in numeric_keys if isinstance(payload.get(key), (int, float))]
    if values:
        signal = min(1.0, max(values))
        reasons.append(f"tool_signal:{signal:.3f}")
    if item.category == "candidate_node_role" and payload.get("role") in {"bridge", "converter", "anchor", "single_failure"}:
        signal = min(1.0, signal + 0.12)
        reasons.append(f"structural_role:{payload.get('role')}")
    if item.category == "estimated_sensitivity":
        reasons.extend(["estimated_not_true_ablation", "experimental_tool_observation"])
    if item.category == "candidate_path":
        reasons.append("candidate_causal_path")
    if item.category == "timing_material":
        signal = 0.75
        reasons.append("domain_timing_context")
    if item.category.startswith("ziwei_"):
        signal = max(signal, 0.65 if stage == "ziwei_integration" else 0.5)
        reasons.append("cross_lens_material")
    priority: AttentionPriority
    if signal >= 0.7 or item.category in {"candidate_path", "estimated_sensitivity"}:
        priority = "high"
    elif signal >= 0.4 or item.category in {"candidate_node_role", "tool_salience"}:
        priority = "supporting"
    else:
        priority = "context"
    return priority, round(signal, 4), reasons or ["context_support"]


def _reasoning_phase(stage: ContextStage) -> Literal["independent_observation", "tool_challenge", "cross_lens", "domain", "case_revision"]:
    if stage in {"baseline", "pattern"}:
        return "independent_observation"
    if stage in {"work_path", "prediction"}:
        return "tool_challenge"
    if stage == "ziwei_integration":
        return "cross_lens"
    if stage in {"career", "wealth", "domain"}:
        return "domain"
    return "case_revision"


def _authority_status(item: WorldFact) -> Literal["production", "experimental", "research"]:
    if item.authority == "experimental_tool_observation":
        return "experimental"
    if item.authority == "research_prior":
        return "research"
    if item.authority in {"deterministic_fact", "neutral_relation"}:
        return "production"
    raise ValueError(f"unsupported_world_fact_authority:{item.authority}")


def _public_birth_location(value: Any) -> str:
    text = str(value or "")
    if any(token in text.lower() for token in ("v20", "v30", "legacy", "import", "导入")):
        return "未记录"
    return text


def _immutable_ledger(*, world: ChartWorldInstance, categories: set[str]) -> dict[str, Any]:
    ledger: dict[str, Any] = {}
    for item in sorted(world.facts, key=lambda fact: fact.fact_id):
        if item.kind != "fact" or item.category not in categories:
            continue
        existing = ledger.setdefault(item.category, {})
        if isinstance(existing, dict) and isinstance(item.payload, dict):
            existing.update(item.payload)
        else:
            ledger[item.category] = item.payload
    return ledger


def _element_role_ledger(ledger: dict[str, Any]) -> dict[str, str]:
    day_master = ledger.get("day_master") or {}
    day_element = str(day_master.get("day_element") or day_master.get("element") or "")
    if not day_element:
        return {}
    generates = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
    controls = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}
    generated_by = next((source for source, target in generates.items() if target == day_element), "")
    controlled_by = next((source for source, target in controls.items() if target == day_element), "")
    return {
        day_element: "比劫/同类",
        generates.get(day_element, ""): "食伤/输出",
        controls.get(day_element, ""): "财星/资源结果",
        controlled_by: "官杀/规则压力",
        generated_by: "印星/支持输入",
    }
