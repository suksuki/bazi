from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.review_queue import CORE_DOMAIN_PRIORITY
from v20.knowledge.rule_proposal import build_knowledge_rule_proposals
from v20.knowledge.schema import KnowledgeUnit
from v20.llm.provider import llm_provider_readiness_report
from v20.llm.tasks import draft_rule_extraction_from_knowledge, draft_rule_extraction_with_llm
from v20.measurement.domain_alignment import align_rule_candidate


@dataclass(frozen=True)
class ExtractedRuleAtom:
    atom_id: str
    atom_type: str
    source_knowledge_id: str
    domain: str
    operator: str
    value: str
    evidence_role: str
    confidence: float
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "ATOM_FROM_REVIEWED_KNOWLEDGE",
            "ATOM_IS_CONDITION_OR_BOUNDARY_NOT_VERDICT",
        ]
        return payload


@dataclass(frozen=True)
class ExtractedRuleCandidate:
    rule_id: str
    domain: str
    source_knowledge_id: str
    title: str
    summary: str
    condition_atoms: tuple[ExtractedRuleAtom, ...]
    emits_feature_hooks: tuple[str, ...]
    supports_question_hooks: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    boundary: str
    rule_graph_projection: dict[str, object]
    llm_draft_lane: dict[str, object]
    corpus_validation_signal: dict[str, object]
    derived_subrules: tuple[dict[str, object], ...] = field(default_factory=tuple)
    extraction_method: tuple[str, ...] = (
        "reviewed_knowledge_contract",
        "deterministic_hook_and_boundary_parser",
    )
    source_authority: str = "reviewed_bazi_knowledge_base"
    runtime_allowed: bool = True
    active_training_allowed: bool = True
    llm_draft_allowed: bool = True
    status: str = "active_ready"
    guardrails: tuple[str, ...] = (
        "KNOWLEDGE_BASE_IS_RULE_SOURCE",
        "CORPUS_VALIDATES_DOES_NOT_AUTHOR_RULES",
        "LLM_DRAFTS_REQUIRE_VALIDATOR_TRACE",
        "USER_VISIBLE_RUNTIME_ALLOWED_WITH_EVIDENCE",
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["condition_atoms"] = [row.to_dict() for row in self.condition_atoms]
        payload["bazi_alignment"] = align_rule_candidate(
            domain=self.domain,
            emits_feature_hooks=self.emits_feature_hooks,
            supports_question_hooks=self.supports_question_hooks,
            title=self.title,
            summary=self.summary,
            boundary=self.boundary,
        ).to_dict()
        return payload


def build_rule_extraction_report(
    domain: str = "",
    *,
    limit: int = 0,
    subrule_limit: int = 4,
    units: tuple[KnowledgeUnit, ...] | None = None,
) -> dict[str, object]:
    rows = _selected_reviewed_units(domain, limit=limit, units=units or default_knowledge_units())
    proposals = _proposal_index(domain, limit=limit, units=rows)
    corpus_training = _read_corpus_training_artifacts()
    validation_index = _corpus_rule_validation_index(corpus_training)
    candidates = tuple(
        _extract_candidate(
            unit,
            proposals.get(unit.knowledge_id, {}),
            validation_index.get(_proposal_id_for_unit(unit), {}),
            subrule_limit=subrule_limit,
        )
        for unit in rows
    )
    return {
        "version": "v20.knowledge_rule_extraction.v1",
        "status": "ready" if candidates else "empty",
        "domain": domain.strip(),
        "source_authority": "reviewed_bazi_knowledge_base",
        "corpus_role": "coverage_validation_and_refinement_only",
        "llm_role": "candidate_atom_drafting_only_validator_required",
        "candidate_count": len(candidates),
        "atom_count": sum(len(row.condition_atoms) for row in candidates),
        "derived_subrule_count": sum(len(row.derived_subrules) for row in candidates),
        "candidates": [row.to_dict() for row in candidates],
        "algorithm_policy": {
            "active": [
                "deterministic_knowledge_contract_extraction",
                "corpus_support_quality_review",
                "active_rule_graph_projection",
            ],
            "llm_allowed": [
                "draft_condition_atoms_from_reviewed_knowledge_text",
                "summarize_missing_rule_conditions",
                "suggest_subrule_names",
            ],
            "llm_forbidden": [
                "create_chart_facts",
                "override_core_inference",
                "activate_runtime_rule",
                "write_user_visible_fortune_verdict",
            ],
            "deferred": [
                "embedding_similarity_for_rule_dedup",
                "gnn_rule_graph_path_rerank",
                "learning_to_rank_rule_paths",
            ],
        },
        "runtime_mutation": False,
        "guardrails": [
            "RULE_EXTRACTION_IS_KNOWLEDGE_FIRST",
            "CORPUS_IS_VALIDATION_NOT_SOURCE",
            "LLM_IS_DRAFT_ASSISTANT_NOT_AUTHORITY",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
        ],
    }


def validate_rule_extraction_report(domain: str = "", *, limit: int = 12) -> dict[str, object]:
    report = build_rule_extraction_report(domain, limit=limit)
    failures: list[str] = []
    if report["source_authority"] != "reviewed_bazi_knowledge_base":
        failures.append("source_authority_must_be_knowledge_base")
    if report["corpus_role"] != "coverage_validation_and_refinement_only":
        failures.append("corpus_must_not_author_rules")
    if report["status"] == "empty":
        failures.append("no_rule_candidates_extracted")
    for candidate in report["candidates"]:
        if not isinstance(candidate, dict):
            continue
        rule_id = str(candidate.get("rule_id", ""))
        if candidate.get("runtime_allowed") is not True:
            failures.append(f"runtime_blocked:{rule_id}")
        if not candidate.get("condition_atoms"):
            failures.append(f"missing_condition_atoms:{rule_id}")
        if candidate.get("source_authority") != "reviewed_bazi_knowledge_base":
            failures.append(f"candidate_source_authority_mismatch:{rule_id}")
        if not candidate.get("boundary"):
            failures.append(f"missing_boundary:{rule_id}")
        alignment = candidate.get("bazi_alignment", {})
        if not isinstance(alignment, dict) or alignment.get("ok") is not True:
            failures.append(f"bazi_alignment_failed:{rule_id}")
    return {
        "version": "v20.knowledge_rule_extraction_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain": domain.strip(),
        "candidate_count": report["candidate_count"],
        "atom_count": report["atom_count"],
        "derived_subrule_count": report["derived_subrule_count"],
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "KNOWLEDGE_FIRST_RULE_SOURCE_REQUIRED",
            "NO_RUNTIME_MUTATION",
        ],
    }


def build_llm_rule_extraction_report(
    domain: str = "",
    *,
    limit: int = 0,
    units: tuple[KnowledgeUnit, ...] | None = None,
    execute_llm: bool = True,
) -> dict[str, object]:
    rows = _selected_reviewed_units(domain, limit=limit, units=units or default_knowledge_units())
    corpus_training = _read_corpus_training_artifacts()
    validation_index = _corpus_rule_validation_index(corpus_training)
    drafts = []
    for unit in rows:
        corpus_signal = _corpus_signal_view(validation_index.get(_proposal_id_for_unit(unit), {}))
        drafts.append(
            {
                "source_knowledge_id": unit.knowledge_id,
                "domain": unit.domain,
                "corpus_validation_signal": corpus_signal,
                "draft_result": (
                    draft_rule_extraction_with_llm(
                        unit,
                        corpus_validation_signal=corpus_signal,
                    )
                    if execute_llm
                    else _deterministic_llm_rule_extraction_fallback(unit)
                ),
            }
        )
    accepted_count = sum(1 for row in drafts if row["draft_result"]["status"] == "accepted")
    fallback_count = sum(1 for row in drafts if row["draft_result"]["status"] == "fallback")
    return {
        "version": "v20.llm_rule_extraction_report.v1",
        "status": "ready" if drafts else "empty",
        "domain": domain.strip(),
        "provider_readiness": llm_provider_readiness_report(),
        "source_authority": "reviewed_bazi_knowledge_base",
        "llm_role": "structured_rule_atom_draft_only",
        "candidate_count": len(drafts),
        "accepted_count": accepted_count,
        "fallback_count": fallback_count,
        "drafts": drafts,
        "runtime_mutation": False,
        "guardrails": [
            "LLM_RULE_EXTRACTION_IS_DRAFT_ONLY",
            "REVIEWED_KNOWLEDGE_IS_SOURCE",
            "VALIDATOR_DECIDES_ACCEPTANCE",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
            *(("LLM_EXECUTION_DISABLED_FOR_STATUS_VIEW",) if not execute_llm else ()),
        ],
    }


def validate_llm_rule_extraction_report(domain: str = "", *, limit: int = 3, execute_llm: bool = True) -> dict[str, object]:
    report = build_llm_rule_extraction_report(domain, limit=limit, execute_llm=execute_llm)
    failures: list[str] = []
    for row in report["drafts"]:
        if not isinstance(row, dict):
            continue
        result = row.get("draft_result", {})
        if not isinstance(result, dict):
            failures.append("malformed_draft_result")
            continue
        if result.get("runtime_mutation") is True:
            failures.append(f"runtime_mutation:{row.get('source_knowledge_id', '')}")
        llm_call = result.get("llm_call", {})
        if isinstance(llm_call, dict) and llm_call.get("status") == "accepted":
            validation = llm_call.get("validation", {})
            if not isinstance(validation, dict) or validation.get("ok") is not True:
                failures.append(f"accepted_without_validation:{row.get('source_knowledge_id', '')}")
    return {
        "version": "v20.llm_rule_extraction_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain": domain.strip(),
        "candidate_count": report["candidate_count"],
        "accepted_count": report["accepted_count"],
        "fallback_count": report["fallback_count"],
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "FALLBACK_IS_ALLOWED_WHEN_PROVIDER_DISABLED",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
        ],
    }


def _deterministic_llm_rule_extraction_fallback(unit: KnowledgeUnit) -> dict[str, object]:
    fallback = draft_rule_extraction_from_knowledge(unit)
    return {
        "version": "v20.llm_rule_extraction_execution.v1",
        "status": "fallback",
        "source": "deterministic_fallback",
        "contract": "rule_extraction_draft",
        "locale": "zh",
        "draft": fallback["draft"],
        "llm_call": {
            "status": "fallback",
            "task_name": "rule_extraction_draft",
            "fallback_reason": "llm_execution_disabled_for_status_view",
            "executed": False,
            "runtime_mutation": False,
        },
        "fallback": fallback["draft"],
        "runtime_mutation": False,
        "guardrails": [
            "LLM_NOT_EXECUTED",
            "DETERMINISTIC_FALLBACK_USED",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
        ],
    }


def _selected_reviewed_units(
    domain: str,
    *,
    limit: int,
    units: tuple[KnowledgeUnit, ...],
) -> tuple[KnowledgeUnit, ...]:
    normalized = domain.strip()
    rows = [
        unit
        for unit in units
        if unit.status == "reviewed" and (not normalized or unit.domain == normalized)
    ]
    sorted_rows = sorted(
        rows,
        key=lambda unit: (
            _domain_priority(unit.domain),
            _knowledge_unit_contract_preference(unit.knowledge_id),
            unit.knowledge_id,
        ),
    )
    return tuple(sorted_rows if limit <= 0 else sorted_rows[:limit])


def _knowledge_unit_contract_preference(knowledge_id: str) -> int:
    if str(knowledge_id).startswith("v20."):
        return 0
    return 1


def _proposal_index(domain: str, *, limit: int, units: tuple[KnowledgeUnit, ...]) -> dict[str, dict[str, object]]:
    report = build_knowledge_rule_proposals(domain, limit=limit, units=units)
    rows = {}
    for proposal in report["proposals"]:
        if isinstance(proposal, dict):
            rows[str(proposal["source_knowledge_id"])] = proposal
    return rows


def _extract_candidate(
    unit: KnowledgeUnit,
    proposal: dict[str, object],
    corpus_signal: dict[str, object],
    *,
    subrule_limit: int,
) -> ExtractedRuleCandidate:
    atoms = _extract_atoms(unit)
    rule_id = f"v20.extracted_rule.{_safe_id(unit.knowledge_id)}"
    return ExtractedRuleCandidate(
        rule_id=rule_id,
        domain=unit.domain,
        source_knowledge_id=unit.knowledge_id,
        title=f"Extracted rule from {unit.title}",
        summary=unit.summary,
        condition_atoms=atoms,
        emits_feature_hooks=unit.feature_hooks,
        supports_question_hooks=unit.question_hooks,
        evidence_refs=unit.source_refs,
        boundary=unit.boundary,
        rule_graph_projection={
            "path_id": rule_id.replace("v20.extracted_rule", "candidate.rulepath"),
            "domain": unit.domain,
            "title": unit.title,
            "evidence_refs": list(unit.feature_hooks),
            "boundary": unit.boundary,
            "runtime_allowed": True,
            "projection_only": True,
        },
        llm_draft_lane={
            "task": "rule_extraction_draft",
            "status": "available_for_reviewed_knowledge_only",
            "allowed_inputs": [
                "reviewed_knowledge_unit",
                "feature_hook_contracts",
                "question_hook_contracts",
                "corpus_validation_signal",
            ],
            "required_outputs": [
                "condition_atoms",
                "emits_feature_hooks",
                "supports_question_hooks",
                "boundary",
                "risk_notes",
            ],
            "deterministic_validator": "validate_rule_extraction_report",
            "fallback": "deterministic_knowledge_rule_extractor",
            "forbidden_outputs": [
                "chart_fact_generation",
                "runtime_rule_activation",
                "core_rule_truth_override",
                "fortune_verdict",
            ],
        },
        corpus_validation_signal=_corpus_signal_view(corpus_signal),
        derived_subrules=_derived_subrules(unit, corpus_signal, subrule_limit=subrule_limit),
        extraction_method=(
            "reviewed_knowledge_contract",
            "deterministic_hook_and_boundary_parser",
            "proposal_contract_reuse" if proposal else "direct_unit_extraction",
        ),
    )


def _extract_atoms(unit: KnowledgeUnit) -> tuple[ExtractedRuleAtom, ...]:
    atoms: list[ExtractedRuleAtom] = []
    for index, hook in enumerate(unit.feature_hooks):
        atoms.append(
            ExtractedRuleAtom(
                atom_id=f"atom.{_safe_id(unit.knowledge_id)}.feature_hook.{index}",
                atom_type="feature_hook_prefix",
                source_knowledge_id=unit.knowledge_id,
                domain=unit.domain,
                operator="prefix_match",
                value=hook,
                evidence_role="condition",
                confidence=0.74,
            )
        )
    for index, question_hook in enumerate(unit.question_hooks):
        atoms.append(
            ExtractedRuleAtom(
                atom_id=f"atom.{_safe_id(unit.knowledge_id)}.question_hook.{index}",
                atom_type="question_hook_support",
                source_knowledge_id=unit.knowledge_id,
                domain=unit.domain,
                operator="supports",
                value=question_hook,
                evidence_role="routing_effect",
                confidence=0.66,
            )
        )
    if unit.evidence_template:
        atoms.append(
            ExtractedRuleAtom(
                atom_id=f"atom.{_safe_id(unit.knowledge_id)}.evidence_template",
                atom_type="evidence_template_required",
                source_knowledge_id=unit.knowledge_id,
                domain=unit.domain,
                operator="requires_language",
                value=unit.evidence_template,
                evidence_role="evidence_binding",
                confidence=0.82,
            )
        )
    if unit.boundary:
        atoms.append(
            ExtractedRuleAtom(
                atom_id=f"atom.{_safe_id(unit.knowledge_id)}.boundary",
                atom_type="boundary_guard",
                source_knowledge_id=unit.knowledge_id,
                domain=unit.domain,
                operator="forbids_overreach",
                value=unit.boundary,
                evidence_role="safety_boundary",
                confidence=0.9,
                boundary=unit.boundary,
            )
        )
    return tuple(atoms)


def _corpus_rule_validation_index(corpus_training: dict[str, object]) -> dict[str, dict[str, object]]:
    rule_training = corpus_training.get("rule_proposal_training", {})
    if not isinstance(rule_training, dict):
        return {}
    rows = {}
    for proposal in rule_training.get("proposals", ()):
        if isinstance(proposal, dict):
            rows[str(proposal.get("proposal_id", ""))] = proposal
    return rows


def _read_corpus_training_artifacts() -> dict[str, object]:
    from v20.corpus.artifacts import read_corpus_training_artifacts

    return read_corpus_training_artifacts()


def _corpus_signal_view(signal: dict[str, object]) -> dict[str, object]:
    if not signal:
        return {
            "status": "not_available",
            "role": "coverage_validation_not_rule_source",
            "runtime_mutation": False,
        }
    return {
        "status": "available",
        "role": "coverage_validation_not_rule_source",
        "support_count": signal.get("support_count", 0),
        "support_ratio": signal.get("support_ratio", 0),
        "support_quality": signal.get("support_quality", ""),
        "next_training_action": signal.get("next_training_action", ""),
        "top_matched_feature_ids": signal.get("top_matched_feature_ids", [])[:8],
        "runtime_mutation": False,
    }


def _derived_subrules(unit: KnowledgeUnit, signal: dict[str, object], *, subrule_limit: int) -> tuple[dict[str, object], ...]:
    if not signal:
        return ()
    if signal.get("support_quality") != "too_broad_needs_subconditions":
        return ()
    rows = []
    for index, signature in enumerate(signal.get("top_exact_feature_signatures", [])[:subrule_limit]):
        if not isinstance(signature, dict) or not signature.get("value"):
            continue
        feature_ids = tuple(str(item) for item in str(signature["value"]).split("|") if item)
        rows.append(
            {
                "subrule_id": f"v20.extracted_subrule.{_safe_id(unit.knowledge_id)}.{index:02d}",
                "source_knowledge_id": unit.knowledge_id,
                "source_rule": "knowledge_rule_with_corpus_validation_refinement",
                "condition_model": {
                    "type": "exact_feature_signature_refinement",
                    "all_of_feature_ids": list(feature_ids),
                },
                "support_count": signature.get("count", 0),
                "support_weight": signature.get("weight", 0),
                "status": "active_refinement_ready",
                "runtime_allowed": True,
                "guardrails": [
                    "SUBRULE_REFINEMENT_FROM_CORPUS_SUPPORT",
                    "KNOWLEDGE_UNIT_REMAINS_AUTHORITY",
                    "RUNTIME_ACTIVATION_ALLOWED_WITH_TRACE",
                ],
            }
        )
    return tuple(rows)


def _proposal_id_for_unit(unit: KnowledgeUnit) -> str:
    return f"v20.rule_proposal.{_safe_id(unit.knowledge_id)}"


def _domain_priority(domain: str) -> tuple[int, str]:
    try:
        return (CORE_DOMAIN_PRIORITY.index(domain), domain)
    except ValueError:
        return (len(CORE_DOMAIN_PRIORITY), domain)


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
