from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from core.life_domains import DOMAIN_PROTOCOLS, DOMAIN_REGISTRY, LifeDomain
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord
from core.mingli_agent.reasoner import review_domain_reading
from product.agent_api import _project_domain_exploration
from product.agent_case_store import PostgresAgentCaseStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the V50 life-domain cognition layer without calling an LLM.")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--database-url", default="postgresql:///qiazhi_v50?host=/tmp")
    parser.add_argument("--output-dir", default="reports/life-domain-system-v1")
    args = parser.parse_args()

    specialized = set(LifeDomain) - {LifeDomain.WHOLE_CHART}
    protocol_issues: list[str] = []
    if len(DOMAIN_REGISTRY) != 12:
        protocol_issues.append("domain_registry_not_12")
    if set(DOMAIN_PROTOCOLS) != specialized:
        protocol_issues.append("specialized_protocol_coverage_incomplete")
    if len({item.probe_goal for item in DOMAIN_PROTOCOLS.values()}) != len(specialized):
        protocol_issues.append("probe_goals_not_distinct")
    for domain, protocol in DOMAIN_PROTOCOLS.items():
        if not protocol.core_questions or not protocol.causal_focus or not protocol.probe_goal:
            protocol_issues.append(f"thin_protocol:{domain.value}")

    case_result: dict[str, object] = {"case_id": args.case_id, "found": False, "explorations": {}}
    if args.case_id:
        row = PostgresAgentCaseStore(args.database_url).get(case_id=args.case_id)
        if row:
            world = ChartWorldInstance.model_validate(row["world"])
            record = MingliCognitiveRecord.model_validate(row["record"])
            explorations: dict[str, object] = {}
            for domain, exploration in record.domain_explorations.items():
                receipt = review_domain_reading(
                    reading=exploration.reading,
                    world=world,
                    model=exploration.review.model,
                )
                guest = _project_domain_exploration(exploration, role_mode="guest")
                member = _project_domain_exploration(exploration, role_mode="member")
                practitioner = _project_domain_exploration(exploration, role_mode="practitioner")
                explorations[domain.value] = {
                    "stored_review_passed": exploration.review.passed,
                    "current_contract_passed": receipt.passed,
                    "causal_step_count": len(exploration.reading.causal_chain),
                    "assertion_count": len(exploration.reading.assertions),
                    "has_domain_probe": exploration.reading.next_probe is not None,
                    "has_context_manifest": bool(exploration.context_manifest),
                    "traceability": receipt.fact_traceability_rate,
                    "issues": [item.model_dump(mode="json") for item in receipt.issues],
                    "role_projection": {
                        "guest_hides_assertions": "assertions" not in guest["reading"],
                        "member_hides_evidence_ids": all(
                            "evidence_refs" not in assertion and "counter_evidence_refs" not in assertion
                            for assertion in member["reading"].get("assertions", [])
                        ),
                        "professional_exposes_review": "review" in practitioner,
                        "professional_exposes_context": "context_manifest" in practitioner,
                    },
                }
            case_result = {"case_id": args.case_id, "found": True, "explorations": explorations}

    passed = not protocol_issues and (
        not args.case_id
        or bool(case_result.get("found"))
    )
    result = {
        "run_name": "V50 Life Domain Cognition Validation v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "domain_count": len(DOMAIN_REGISTRY),
        "specialized_protocol_count": len(DOMAIN_PROTOCOLS),
        "distinct_probe_goal_count": len({item.probe_goal for item in DOMAIN_PROTOCOLS.values()}),
        "protocol_issues": protocol_issues,
        "case_audit": case_result,
        "boundaries": {
            "training_performed": False,
            "weights_modified": False,
            "mingli_algorithm_modified": False,
            "global_theory_modified": False,
            "llm_called": False,
            "audit_only": True,
        },
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "life_domain_validation_v1.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# V50 Life Domain Cognition Validation v1",
        "",
        f"- Status: `{result['status']}`",
        f"- Domain registry: `{result['domain_count']}`",
        f"- Specialized protocols: `{result['specialized_protocol_count']}`",
        f"- Distinct Probe goals: `{result['distinct_probe_goal_count']}`",
        f"- Case: `{args.case_id or 'not supplied'}`",
        "",
        "## Observed Data",
        "",
    ]
    explorations = case_result.get("explorations") or {}
    if explorations:
        for domain, item in explorations.items():
            lines.append(
                f"- `{domain}`: current contract `{item['current_contract_passed']}`, "
                f"4-step chain `{item['causal_step_count']}`, assertions `{item['assertion_count']}`, "
                f"domain probe `{item['has_domain_probe']}`, focused context `{item['has_context_manifest']}`."
            )
            role_projection = item["role_projection"]
            lines.append(
                f"  Role projection: guest hides assertions `{role_projection['guest_hides_assertions']}`, "
                f"member hides evidence ids `{role_projection['member_hides_evidence_ids']}`, "
                f"professional review/context `{role_projection['professional_exposes_review']}`/`{role_projection['professional_exposes_context']}`."
            )
    else:
        lines.append("- No persisted case was audited.")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The registry is complete only when every non-whole-chart domain owns a distinct reasoning and Probe protocol. Persisted legacy explorations may remain readable, but are not cache-valid until they contain a domain Probe and the current focused-context manifest.",
        "",
        "## Boundaries",
        "",
        "```yaml",
        *[f"{key}: {str(value).lower()}" for key, value in result["boundaries"].items()],
        "```",
    ])
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
