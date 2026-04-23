from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.testing.practitioner_benchmarks import (
    PRACTITIONER_BENCHMARK_CASES,
    practitioner_dynamic_snapshot,
    practitioner_relation_snapshot,
    practitioner_top_scores,
    run_practitioner_case,
)


def fmt_pct(value: object) -> str:
    try:
        return f"{float(value or 0.0):.1f}%"
    except Exception:
        return "0.0%"


def main() -> None:
    print("# V17 命理师校盘基准报告")
    print()
    print("日期：2026-04-23")
    print()
    for case in PRACTITIONER_BENCHMARK_CASES:
        run = run_practitioner_case(case)
        print(f"## {case.case_id}")
        print()
        print(f"- 描述：{case.description}")
        print(f"- 审计重点：{' / '.join(case.audit_focus)}")
        print(f"- 当前主轴：{' / '.join(run.top)}")
        print(
            "- Top Scores："
            + " · ".join(f"{god} {score:.2f}" for god, score in practitioner_top_scores(run, limit=6))
        )
        print(f"- Reviewer Note：{case.reviewer_note}")
        print()
        print("### Relation Formation")
        formation_rows = practitioner_relation_snapshot(run)
        if not formation_rows:
            print("- （无）")
        else:
            for row in formation_rows:
                print(
                    f"- {row.get('family_key')}: {fmt_pct(row.get('formation_percent'))} · "
                    f"{str(row.get('summary') or '').strip() or '—'}"
                )
        print()
        print("### Relation Dynamics")
        dynamics_rows = practitioner_dynamic_snapshot(run)
        if not dynamics_rows:
            print("- （无）")
        else:
            for row in dynamics_rows[:8]:
                print(
                    f"- {row.get('family_key')}: "
                    f"E={float(row.get('energy_effect_ratio') or 0.0):.3f} · "
                    f"S={float(row.get('stability_delta_ratio') or 0.0):.3f}"
                )
        print()


if __name__ == "__main__":
    main()
