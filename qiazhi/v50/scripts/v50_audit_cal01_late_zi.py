from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from lunar_python import Solar

from core.contracts import BirthInputCanonical
from core.engines import resolve_birth_input_pillars
from core.engines.bazi.chart_constraints import validate_four_pillars
from core.engines.birth_calendar import BIRTH_PILLAR_ENGINE_VERSION, FORMAL_HOUR_RULE_VERSION


ROOT = Path(__file__).resolve().parents[1]
RA0_SUMMARY = (
    ROOT
    / "reports/v50-lean-consolidation/ra0-518k-realizability-v1"
    / "ra0_518k_execution_summary_v1.json"
)
DEFAULT_OUTPUT = (
    ROOT
    / "reports/v50-lean-consolidation/cal01-late-zi-v1"
    / "cal01_late_zi_audit_v1.json"
)


def audit_late_zi(*, start: date, end: date) -> dict[str, Any]:
    if end <= start:
        raise ValueError("end_must_be_after_start")
    frozen_ra0 = json.loads(RA0_SUMMARY.read_text(encoding="utf-8"))["semantic_summary"]
    digest = hashlib.sha256()
    samples: list[dict[str, Any]] = []
    total_days = 0
    dependency_mismatch_count = 0
    formal_invalid_count = 0
    current = start
    while current < end:
        raw = _dependency_pillars(current)
        formal = _formal_pillars(current)
        raw_reasons = [item.code for item in validate_four_pillars(raw)]
        formal_reasons = [item.code for item in validate_four_pillars(formal)]
        dependency_mismatch_count += bool(raw_reasons)
        formal_invalid_count += bool(formal_reasons)
        row = {
            "date": current.isoformat(),
            "dependency_pillars": list(raw),
            "formal_pillars": list(formal),
            "dependency_invalid_reasons": raw_reasons,
            "formal_invalid_reasons": formal_reasons,
        }
        digest.update(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        )
        digest.update(b"\n")
        if raw_reasons and len(samples) < 12:
            samples.append(row)
        total_days += 1
        current += timedelta(days=1)

    result = {
        "schema_version": "v50.cal01_late_zi_audit.v1",
        "status": "PASS" if formal_invalid_count == 0 else "FAIL",
        "range": {"start_inclusive": start.isoformat(), "end_exclusive": end.isoformat()},
        "formal_policy": {
            "calendar_profile": "lunar_python.sect2.v1",
            "day_rollover": "midnight",
            "birth_pillar_engine_version": BIRTH_PILLAR_ENGINE_VERSION,
            "hour_rule_version": FORMAL_HOUR_RULE_VERSION,
        },
        "counts": {
            "calendar_days": total_days,
            "dependency_late_zi_mismatches": dependency_mismatch_count,
            "formal_invalid_outputs": formal_invalid_count,
        },
        "retained_ra0_evidence": {
            "visited_late_zi_dependency_mismatches": frozen_ra0["calendar_forward_scan"][
                "canonical_raw_late_zi_invalid_count"
            ],
            "universe_sha256": frozen_ra0["reconstructed_universe"]["content_sha256"],
            "historical_artifact_modified": False,
        },
        "representative_dependency_mismatches": samples,
        "scan_sha256": digest.hexdigest(),
        "llm_used": False,
        "temporal_policy_changed": False,
    }
    return result


def _dependency_pillars(value: date) -> tuple[str, str, str, str]:
    eight_char = Solar.fromYmdHms(value.year, value.month, value.day, 23, 30, 0).getLunar().getEightChar()
    eight_char.setSect(2)
    return (
        eight_char.getYear(),
        eight_char.getMonth(),
        eight_char.getDay(),
        eight_char.getTime(),
    )


def _formal_pillars(value: date) -> tuple[str, str, str, str]:
    resolved = resolve_birth_input_pillars(
        BirthInputCanonical(
            birth_input_id=f"cal01:{value.isoformat()}:23:30",
            gender="unknown",
            calendar_type="solar",
            birth_date=value.isoformat(),
            birth_time="23:30",
            timezone="Asia/Shanghai",
            input_quality="cal01_deterministic_audit",
        )
    )
    return (
        resolved.year_pillar,
        resolved.month_pillar,
        resolved.day_pillar,
        resolved.hour_pillar,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit formal late-Zi Five-Rats consistency")
    parser.add_argument("--start", type=date.fromisoformat, default=date(1900, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2101, 1, 1))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = audit_late_zi(start=args.start, end=args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "counts": result["counts"],
        "scan_sha256": result["scan_sha256"],
        "output": str(args.output),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
