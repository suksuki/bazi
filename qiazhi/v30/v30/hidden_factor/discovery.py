from __future__ import annotations

from pydantic import Field

from v30.contracts import ChartContext, FeatureEvidence, V30Model


class HiddenFactorProbe(V30Model):
    probe_id: str
    context_id: str
    hypothesis: str
    status: str = "needs_dialogue"
    evidence_ids: list[str] = Field(default_factory=list)
    required_feedback: list[str] = Field(default_factory=list)
    boundary: str = "hypothesis_only_not_deterministic_chart_conclusion"


def build_hidden_factor_probes(
    context: ChartContext,
    evidence: list[FeatureEvidence],
) -> list[HiddenFactorProbe]:
    hidden_evidence = [
        row for row in evidence
        if row.domain == "ten_god" and row.kind == "hidden_stem"
    ]
    if not hidden_evidence:
        return []
    return [
        HiddenFactorProbe(
            probe_id=f"{context.context_id}:hidden_factor:amplifier_probe",
            context_id=context.context_id,
            hypothesis="Hidden stems may amplify behavior only after user-confirmed boundary years or repeated states.",
            evidence_ids=[row.evidence_id for row in hidden_evidence],
            required_feedback=[
                "special_event_year",
                "repeated_state_pattern",
                "luck_or_flow_context_if_available",
            ],
        )
    ]
