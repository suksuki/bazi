from __future__ import annotations

import hashlib

from v20.learning.artifact_registry import ArtifactRecord
from v20.learning.activation_policy import activation_policy
from v20.learning.proposal import LearningProposal
from v20.validation.suite import run_synthetic_suite

SUPPORTED_POLICY_TYPES = ("question_ranking", "knowledge_retrieval", "confidence_calibration")


def review_policy_proposal(
    *,
    policy_type: str,
    policy_payload: dict[str, object],
    source: str,
    eval_report_id: str = "",
) -> dict[str, object]:
    if policy_type not in SUPPORTED_POLICY_TYPES:
        raise ValueError(f"Unsupported policy type: {policy_type}")
    policy_hash = _policy_hash(policy_type, policy_payload, source)
    validation = run_synthetic_suite()
    proposal = LearningProposal(
        proposal_id=f"v20.policy.proposal.{policy_hash}",
        proposal_type=f"{policy_type}_policy_review",
        summary=f"Review {policy_type} policy draft from {source}.",
        risk=_risk_for(policy_type, policy_payload),
    )
    artifact = ArtifactRecord(
        artifact_id=f"v20.policy.artifact.{policy_hash}",
        artifact_type=f"{policy_type}_policy",
        dataset_version="v20.synthetic_suite.current",
        code_version="v20.0.prealpha",
        eval_report_id=eval_report_id or ("v20.synthetic_suite.pass" if validation["ok"] else ""),
        production_eligible=True,
    )
    gate = activation_policy(artifact)
    return {
        "version": "v20.policy_review_report.v1",
        "policy_type": policy_type,
        "policy_hash": policy_hash,
        "proposal": proposal.to_dict(),
        "artifact": artifact.to_dict(),
        "validation": {
            "ok": validation["ok"],
            "case_count": validation["case_count"],
            "failures": validation["failures"],
        },
        "activation_policy": gate,
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_REVIEW_FEEDS_ACTIVE_ITERATION",
            "ARTIFACT_CAN_FEED_ACTIVE_ITERATION",
            "DECISION_RECORD_OPTIONAL_FOR_ITERATION",
            "POLICY_ACTIVATION_RECORDED",
        ],
    }


def policy_review_manifest() -> dict[str, object]:
    return {
        "version": "v20.policy_review_manifest.v1",
        "supported_policy_types": list(SUPPORTED_POLICY_TYPES),
        "required_flow": [
            "draft_policy_payload",
            "synthetic_suite",
            "artifact_record",
            "decision_record",
            "activation_policy",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_REVIEW_IS_ACTIVE_ITERATION",
            "ACTIVE_POLICY_ITERATION",
            "ROLLBACK_RECORDED_FOR_ACTIVE_POLICY",
        ],
    }


def _policy_hash(policy_type: str, payload: dict[str, object], source: str) -> str:
    raw = f"{policy_type}|{source}|{sorted(payload.items(), key=lambda row: row[0])}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _risk_for(policy_type: str, payload: dict[str, object]) -> str:
    if policy_type == "confidence_calibration" and payload:
        return "medium"
    if policy_type == "knowledge_retrieval" and payload:
        return "medium"
    return "low"
