from __future__ import annotations

from v20.knowledge.review_packet import build_first_wave_review_packets, build_knowledge_review_packet


def review_packet_approval_preflight(packet: dict[str, object]) -> dict[str, object]:
    failures = []
    proposed_units = tuple(row for row in packet.get("proposed_units", ()) if isinstance(row, dict))
    if not proposed_units:
        failures.append("no_proposed_units")
    for row in proposed_units:
        knowledge_id = str(row.get("knowledge_id", ""))
        if not row.get("summary"):
            failures.append(f"missing_summary:{knowledge_id}")
        if not row.get("evidence_template"):
            failures.append(f"missing_evidence_template:{knowledge_id}")
        if not row.get("boundary"):
            failures.append(f"missing_boundary:{knowledge_id}")
        if not row.get("source_refs"):
            failures.append(f"missing_source_refs:{knowledge_id}")
        if not row.get("feature_hooks"):
            failures.append(f"missing_feature_hooks:{knowledge_id}")
        if not row.get("question_hooks"):
            failures.append(f"missing_question_hooks:{knowledge_id}")
        if row.get("status") != "draft_review_required":
            failures.append(f"unexpected_status:{knowledge_id}")
    if packet.get("runtime_mutation") is not False:
        failures.append("packet_must_be_read_only")
    return {
        "version": "v20.knowledge_review_packet_approval_preflight.v1",
        "domain": packet.get("domain", ""),
        "status": "blocked" if failures else "ready_for_decision_review",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "required_decision": "DecisionRegistry approval required before release.",
        "runtime_mutation": False,
        "guardrails": [
            "APPROVAL_PREFLIGHT_ONLY",
            "NO_STATUS_PROMOTION",
            "NO_DATABASE_WRITE",
            "REVIEWED_RELEASE_REQUIRES_DECISION_RECORD",
        ],
    }


def build_knowledge_approval_preflight(domain: str) -> dict[str, object]:
    return review_packet_approval_preflight(build_knowledge_review_packet(domain))


def build_first_wave_approval_preflight() -> dict[str, object]:
    packets = build_first_wave_review_packets()
    reports = [review_packet_approval_preflight(packet) for packet in packets["packets"]]
    return {
        "version": "v20.knowledge_first_wave_approval_preflight.v1",
        "status": "ready_for_decision_review" if reports and all(row["ok"] for row in reports) else "blocked",
        "ok": bool(reports) and all(row["ok"] for row in reports),
        "domain_count": len(reports),
        "blocked_domain_count": sum(1 for row in reports if not row["ok"]),
        "reports": reports,
        "runtime_mutation": False,
        "guardrails": [
            "FIRST_WAVE_APPROVAL_PREFLIGHT_ONLY",
            "NO_AUTOMATIC_REVIEWED_STATUS",
            "NO_RUNTIME_KNOWLEDGE_ACTIVATION",
        ],
    }
