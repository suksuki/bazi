from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.real_bazi_product_reading_acceptance import (
    FORBIDDEN_CUSTOMER_INTERNAL_TOKENS,
    FORBIDDEN_GENERIC_PRIMARY_TOKENS,
    REQUIRED_PRODUCT_DOMAINS,
    run_real_bazi_product_reading_acceptance,
)
from v30.validation.synthetic_case import SyntheticValidationSuiteResult, run_synthetic_tier


REAL_BAZI_DISTRIBUTION_REPLAY_VERSION = "v30.real_bazi_distribution_replay.v1"


def run_real_bazi_distribution_replay(
    *,
    real_case_limit: int = 8,
    sample_518k_limit: int = 8,
) -> dict[str, Any]:
    product = run_real_bazi_product_reading_acceptance()
    real_cases = run_synthetic_tier("real_case_calibration_pack")
    return build_real_bazi_distribution_replay(
        product_acceptance=product,
        real_case_synthetic=real_cases,
        real_case_limit=real_case_limit,
        sample_518k_limit=sample_518k_limit,
    )


def build_real_bazi_distribution_replay(
    *,
    product_acceptance: Mapping[str, Any],
    real_case_synthetic: SyntheticValidationSuiteResult | Mapping[str, Any],
    real_case_limit: int = 8,
    sample_518k_limit: int = 8,
) -> dict[str, Any]:
    real_case_payload = (
        real_case_synthetic.model_dump(mode="json")
        if hasattr(real_case_synthetic, "model_dump")
        else dict(real_case_synthetic)
    )
    real_case_rows = _real_case_rows(real_case_payload, limit=max(1, int(real_case_limit or 8)))
    sample_rows = _sample_518k_rows(limit=max(1, int(sample_518k_limit or 8)))
    summary = _summary(product_acceptance, real_case_payload, real_case_rows, sample_rows)
    checks = _checks(summary, real_case_rows, sample_rows)
    decision = _decision(checks)
    return {
        "version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["distribution_replay_ready"] else "blocked",
        "task": {
            "task_id": "RBD-S1.11",
            "title": "Real-Case Distribution Replay For RBD",
            "scope": "lightweight_real_case_and_518k_sample_rbd_acceptance_metrics",
        },
        "product_acceptance_summary": _product_summary(product_acceptance),
        "real_case_summary": summary["real_case"],
        "sample_518k_summary": summary["sample_518k"],
        "real_case_rows": real_case_rows,
        "sample_518k_rows": sample_rows,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "sample_518k_limit": max(1, int(sample_518k_limit or 8)),
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "rbd_distribution_replay_is_lightweight_observation_not_full_corpus_or_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "rbd_s111_replays_distribution_metrics_without_claiming_final_bazi_truth",
    }


def _real_case_rows(payload: Mapping[str, Any], *, limit: int) -> list[dict[str, Any]]:
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        return []
    accepted: list[dict[str, Any]] = []
    pending_count = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        observed = _mapping(row.get("observed"))
        fixture = _mapping(observed.get("real_case_fixture"))
        chart_status = str(fixture.get("chart_status") or _mapping(observed.get("chart_build")).get("status") or "")
        if chart_status != "ready":
            pending_count += 1
            continue
        accepted.append(
            _surface_row(
                source="real_case_calibration_pack",
                case_id=str(row.get("case_id") or ""),
                surface=_mapping(observed.get("customer_reading_surface")),
                admin_diagnosis={},
                answer_panel={},
                metadata={
                    "calendar_type": str(fixture.get("calendar_type") or ""),
                    "chart_status": chart_status,
                    "pending_boundary_count_seen": pending_count,
                },
            )
        )
        if len(accepted) >= limit:
            break
    return accepted


def _sample_518k_rows(*, limit: int) -> list[dict[str, Any]]:
    stems = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
    luck = ("戊寅", "", "辛巳", "壬午")
    flow = ("庚子", "", "甲辰", "乙巳")
    rows: list[dict[str, Any]] = []
    for index in range(limit):
        runtime = create_smoke_runtime(
            f"rbd-s111-518k-sample-{index}",
            day_master=stems[index % len(stems)],
            luck_pillar=luck[index % len(luck)],
            flow_year_pillar=flow[index % len(flow)],
            hidden_factor_user_calibrated=index % 5 == 0,
            useful_god_path_resolved=index % 7 == 0,
        )
        user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
        admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
        rows.append(
            _surface_row(
                source="generated_518k_sample",
                case_id=f"v30.generated_518k.rbd.{index}",
                surface=_mapping(user_view.get("reading_surface")),
                admin_diagnosis=_mapping(_mapping(admin_view.get("diagnostics")).get("real_bazi_diagnosis")),
                answer_panel=_mapping(user_view.get("answer_panel")),
                metadata={
                    "day_master": stems[index % len(stems)],
                    "sample_index": index,
                    "mode": "sample",
                },
            )
        )
    return rows


def _surface_row(
    *,
    source: str,
    case_id: str,
    surface: Mapping[str, Any],
    admin_diagnosis: Mapping[str, Any],
    answer_panel: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    domain_rows = [_domain_metric(surface, domain) for domain in REQUIRED_PRODUCT_DOMAINS]
    text = str(surface)
    answer_text = str(answer_panel.get("text") or "")
    generic_hits = _generic_hits(text + answer_text)
    internal_hits = [token for token in FORBIDDEN_CUSTOMER_INTERNAL_TOKENS if token in text]
    diagnosis_claims = admin_diagnosis.get("claims", [])
    diagnosis_paths = admin_diagnosis.get("paths", [])
    diagnosis_portraits = admin_diagnosis.get("portraits", [])
    diagnosis_claims = diagnosis_claims if isinstance(diagnosis_claims, list) else []
    diagnosis_paths = diagnosis_paths if isinstance(diagnosis_paths, list) else []
    diagnosis_portraits = diagnosis_portraits if isinstance(diagnosis_portraits, list) else []
    ready_domains = [row["domain"] for row in domain_rows if row["ready"]]
    quality_ready_domains = [row["domain"] for row in domain_rows if row.get("core_claim_quality_ready")]
    answer_rbd_ready = not answer_text or any(
        token in answer_text
        for token in (
            "财官印",
            "官印相生",
            "财星",
            "官杀",
            "印星",
            "食伤",
            "藏干",
            "隐藏因子",
            "放大机制",
            "命局事实",
            "结构压力",
            "寒热燥湿",
        )
    )
    ready = (
        len(ready_domains) >= 4
        and not generic_hits
        and not internal_hits
        and answer_rbd_ready
    )
    return {
        "source": source,
        "case_id": case_id,
        "metadata": dict(metadata),
        "ready": ready,
        "ready_domain_count": len(ready_domains),
        "quality_ready_domain_count": len(quality_ready_domains),
        "required_domain_count": len(REQUIRED_PRODUCT_DOMAINS),
        "failed_domains": [row["domain"] for row in domain_rows if not row["ready"]],
        "failed_quality_domains": [row["domain"] for row in domain_rows if not row.get("core_claim_quality_ready")],
        "domain_rows": domain_rows,
        "generic_hit_count": len(generic_hits),
        "generic_hits": generic_hits,
        "customer_internal_leak_count": len(internal_hits),
        "customer_internal_hits": internal_hits,
        "answer_rbd_ready": answer_rbd_ready,
        "admin_claim_count": len(diagnosis_claims),
        "admin_path_count": len(diagnosis_paths),
        "admin_portrait_count": len(diagnosis_portraits),
        "boundary": "rbd_distribution_row_checks_customer_projection_and_rbd_metrics_not_final_fortune_truth",
    }


def _domain_metric(surface: Mapping[str, Any], domain: str) -> dict[str, Any]:
    card = _domain_card(surface, domain)
    summary = str(card.get("diagnosis_summary") or "")
    claims = card.get("diagnosis_claims", [])
    paths = card.get("diagnosis_paths", [])
    portraits = card.get("portrait_dimensions", [])
    claims = claims if isinstance(claims, list) else []
    paths = paths if isinstance(paths, list) else []
    portraits = portraits if isinstance(portraits, list) else []
    quality = _mapping(card.get("core_claim_quality"))
    quality_ready = (
        quality.get("version") == "v30.core_bazi_claim_quality.v1"
        and quality.get("quality_ready") is True
        and quality.get("uses_traceable_claims") is True
        and quality.get("chart_fact_mutation_allowed") is False
        and quality.get("fixed_event_prediction_allowed") is False
        and not _list(quality.get("generic_language_hits"))
    )
    requires_path = domain != "timing"
    requires_portrait = domain != "timing"
    ready = (
        bool(summary)
        and not _generic_hits(summary)
        and quality_ready
        and len(claims) >= (2 if domain == "timing" else 3)
        and (len(paths) >= 1 if requires_path else True)
        and (len(portraits) >= 1 if requires_portrait else True)
    )
    return {
        "domain": domain,
        "ready": ready,
        "claim_count": len(claims),
        "path_count": len(paths),
        "portrait_count": len(portraits),
        "summary_present": bool(summary),
        "core_claim_quality_ready": quality_ready,
        "core_claim_quality_version": str(quality.get("version") or ""),
        "core_claim_generic_hit_count": len(_list(quality.get("generic_language_hits"))),
    }


def _domain_card(surface: Mapping[str, Any], domain: str) -> Mapping[str, Any]:
    cards = surface.get("domain_cards", [])
    if not isinstance(cards, list):
        return {}
    for card in cards:
        if isinstance(card, Mapping) and card.get("domain") == domain:
            return card
    return {}


def _generic_hits(text: str) -> list[str]:
    return [token for token in FORBIDDEN_GENERIC_PRIMARY_TOKENS if token in text]


def _summary(
    product_acceptance: Mapping[str, Any],
    real_case_payload: Mapping[str, Any],
    real_case_rows: list[Mapping[str, Any]],
    sample_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "product": _product_summary(product_acceptance),
        "real_case": _row_summary(
            real_case_rows,
            source_suite_id=str(real_case_payload.get("suite_id") or ""),
            source_case_count=int(real_case_payload.get("case_count", 0) or 0),
            source_passed=bool(real_case_payload.get("passed")),
        ),
        "sample_518k": _row_summary(
            sample_rows,
            source_suite_id="v30.generated_518k_contract.rbd_sample",
            source_case_count=len(sample_rows),
            source_passed=True,
        ),
    }


def _row_summary(
    rows: list[Mapping[str, Any]],
    *,
    source_suite_id: str,
    source_case_count: int,
    source_passed: bool,
) -> dict[str, Any]:
    ready = [row for row in rows if row.get("ready")]
    generic_hits = sum(int(row.get("generic_hit_count", 0) or 0) for row in rows)
    leaks = sum(int(row.get("customer_internal_leak_count", 0) or 0) for row in rows)
    return {
        "source_suite_id": source_suite_id,
        "source_case_count": source_case_count,
        "source_passed": source_passed,
        "replay_case_count": len(rows),
        "ready_case_count": len(ready),
        "ready_ratio": round(len(ready) / max(1, len(rows)), 3),
        "average_ready_domain_count": round(
            sum(int(row.get("ready_domain_count", 0) or 0) for row in rows) / max(1, len(rows)),
            3,
        ),
        "average_quality_ready_domain_count": round(
            sum(int(row.get("quality_ready_domain_count", 0) or 0) for row in rows) / max(1, len(rows)),
            3,
        ),
        "min_quality_ready_domain_count": min(
            (int(row.get("quality_ready_domain_count", 0) or 0) for row in rows),
            default=0,
        ),
        "generic_language_hit_count": generic_hits,
        "generic_language_rate": round(generic_hits / max(1, len(rows)), 3),
        "customer_internal_leak_count": leaks,
        "answer_rbd_ready_count": sum(1 for row in rows if row.get("answer_rbd_ready")),
        "min_admin_claim_count": min((int(row.get("admin_claim_count", 0) or 0) for row in rows), default=0),
        "min_admin_path_count": min((int(row.get("admin_path_count", 0) or 0) for row in rows), default=0),
        "min_admin_portrait_count": min((int(row.get("admin_portrait_count", 0) or 0) for row in rows), default=0),
    }


def _product_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "ready": bool(decision.get("product_reading_acceptance_ready")),
        "decision_status": str(decision.get("decision_status") or ""),
    }


def _checks(
    summary: Mapping[str, Any],
    real_case_rows: list[Mapping[str, Any]],
    sample_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    product = _mapping(summary.get("product"))
    real_case = _mapping(summary.get("real_case"))
    sample = _mapping(summary.get("sample_518k"))
    return [
        {
            "check_id": "s110_product_acceptance_ready",
            "passed": product.get("ready") is True
            and product.get("decision_status") == "rbd_s110_product_reading_accepted",
            "observed": product,
        },
        {
            "check_id": "real_case_replay_ready",
            "passed": real_case.get("source_passed") is True
            and int(real_case.get("replay_case_count", 0) or 0) >= 8
            and float(real_case.get("ready_ratio", 0.0) or 0.0) >= 1.0,
            "observed": real_case,
        },
        {
            "check_id": "sample_518k_replay_ready",
            "passed": int(sample.get("replay_case_count", 0) or 0) >= 8
            and float(sample.get("ready_ratio", 0.0) or 0.0) >= 1.0
            and int(sample.get("min_admin_claim_count", 0) or 0) >= 45
            and int(sample.get("min_admin_path_count", 0) or 0) >= 8
            and int(sample.get("min_admin_portrait_count", 0) or 0) >= 20,
            "observed": sample,
        },
        {
            "check_id": "generic_language_and_customer_leak_rate_clean",
            "passed": real_case.get("generic_language_hit_count") == 0
            and sample.get("generic_language_hit_count") == 0
            and real_case.get("customer_internal_leak_count") == 0
            and sample.get("customer_internal_leak_count") == 0,
            "observed": {
                "real_case_generic_hits": real_case.get("generic_language_hit_count"),
                "sample_518k_generic_hits": sample.get("generic_language_hit_count"),
                "real_case_internal_leaks": real_case.get("customer_internal_leak_count"),
                "sample_518k_internal_leaks": sample.get("customer_internal_leak_count"),
            },
        },
        {
            "check_id": "core_claim_quality_replay_ready",
            "passed": int(real_case.get("min_quality_ready_domain_count", 0) or 0) >= 5
            and int(sample.get("min_quality_ready_domain_count", 0) or 0) >= 5,
            "observed": {
                "real_case_min_quality_ready_domain_count": real_case.get("min_quality_ready_domain_count"),
                "sample_518k_min_quality_ready_domain_count": sample.get("min_quality_ready_domain_count"),
                "real_case_average_quality_ready_domain_count": real_case.get("average_quality_ready_domain_count"),
                "sample_518k_average_quality_ready_domain_count": sample.get("average_quality_ready_domain_count"),
            },
        },
        {
            "check_id": "full_518k_remains_explicit",
            "passed": True,
            "observed": {
                "full_518k_required": False,
                "sample_518k_only": True,
                "synthetic_all_required": False,
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "distribution_replay_ready": ready,
        "decision_status": "rbd_s111_distribution_replay_ready" if ready else "rbd_s111_distribution_replay_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blockers": ["distribution_replay_checks_failed"] if failed else [],
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "chart_fact_mutation_allowed": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("distribution_replay_ready"):
        return {
            "task_id": "RBD-S1.12",
            "title": "RBD Training Signal And Calibration Queue",
            "selected_track": "real_bazi_diagnosis",
            "scope": [
                "turn accepted replay metrics into training signal candidates",
                "queue only evidence-backed RBD calibration items",
                "do not mutate chart facts or promote pointers by default",
            ],
        }
    return {
        "task_id": "RBD-S1.11-FR",
        "title": "RBD Distribution Replay Failure Review",
        "selected_track": "real_bazi_diagnosis",
        "scope": ["repair failed replay metrics before training queue work"],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
