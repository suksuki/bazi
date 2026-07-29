from __future__ import annotations

from typing import Any

from abu_v60.context import ExperienceContextEnvelope, ExperienceUnit
from abu_v60.decision import (
    CognitiveDecisionKernel,
    DecisionCandidate,
    DecisionKind,
    DecisionRequest,
)
from abu_v60.mingli import StructuralCandidateCompiler
from abu_v60.provenance import stable_ref


class LabProjector:
    """Expose inspectable evidence and uncertainty without promoting a conclusion."""

    def __init__(
        self,
        candidate_compiler: StructuralCandidateCompiler | None = None,
        decision_kernel: CognitiveDecisionKernel | None = None,
    ) -> None:
        self._candidate_compiler = candidate_compiler or StructuralCandidateCompiler()
        self._decision_kernel = decision_kernel or CognitiveDecisionKernel()

    def project(
        self,
        *,
        context: ExperienceContextEnvelope,
    ) -> dict[str, Any]:
        chart_version_ref = context.lineage.chart_version_ref
        facts = [fact.model_dump(mode="json") for fact in context.facts]
        candidates = self._candidate_compiler.compile(
            chart_version_ref=chart_version_ref,
            facts=facts,
        )
        request = DecisionRequest(
            request_id=stable_ref(
                "v60-lab-candidate-route",
                {
                    "chart_version_ref": chart_version_ref,
                    "candidate_refs": [item.candidate_ref for item in candidates],
                },
            ),
            decision_kind=DecisionKind.INTERPRETATION,
            subject_ref=chart_version_ref,
            evidence_refs=tuple(
                evidence_ref for candidate in candidates for evidence_ref in candidate.evidence_refs
            ),
            candidates=tuple(
                DecisionCandidate(
                    candidate_ref=candidate.candidate_ref,
                    evidence_refs=candidate.evidence_refs,
                    qualified=candidate.selection_qualified,
                )
                for candidate in candidates
            ),
            llm_allowed=False,
            human_required=False,
            correlation_id=chart_version_ref,
            causation_id=chart_version_ref,
        )
        route = self._decision_kernel.route(request)
        return {
            "context_ref": context.context_ref,
            "disclosure": context.disclosure_for(ExperienceUnit.LAB).model_dump(mode="json"),
            "chart_version_ref": chart_version_ref,
            "pillars": dict(context.pillars),
            "facts": facts,
            "candidate_paths": [candidate.model_dump(mode="json") for candidate in candidates],
            "qualification_summary": {
                "profile_ref": self._candidate_compiler.qualification_profile_ref,
                "structure_evidence_satisfied": sum(
                    candidate.structure_evidence_status.value == "SATISFIED"
                    for candidate in candidates
                ),
                "selection_qualified": sum(
                    candidate.selection_qualified for candidate in candidates
                ),
            },
            "candidate_projection_status": (
                "STRUCTURE_CANDIDATES_AVAILABLE" if candidates else "NO_ADMITTED_RELATION_CANDIDATE"
            ),
            "decision_route": route.model_dump(mode="json"),
            "interpretation_status": "STRUCTURE_CONTEXT_ONLY",
            "effect_status": "UNRESOLVED",
            "capacity_status": "UNRESOLVED",
            "professional_admission_status": "UNRESOLVED",
            "canonical_write_allowed": False,
        }
