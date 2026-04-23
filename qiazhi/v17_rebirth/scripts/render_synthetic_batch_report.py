from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.testing.synthetic_batch_lab import build_synthetic_batch_report


def main() -> None:
    report = build_synthetic_batch_report()
    print("# V17 Synthetic Batch Lab Report")
    print()
    print("日期：2026-04-23")
    print()
    print(f"- 协议：`{report['protocol']}`")
    print(f"- 样盘数：{report['case_count']}")
    print(f"- 通过：{report['passed_count']}")
    print(f"- 失败：{report['failed_count']}")
    print(f"- 学习状态：`{report['learning_loop_state']}`")
    print()
    print("## Batch Runs")
    for row in report["runs"]:
        status = "PASS" if row["passed"] else "FAIL"
        print(
            f"- `{row['case_id']}` · {status} · total={row['total']:.2f} · "
            f"top={'/'.join(row['top'][:4]) or '—'}"
        )
    print()
    print("## Anomalies")
    if not report["anomalies"]:
        print("- （无）")
    else:
        for anomaly in report["anomalies"]:
            print(
                f"- `{anomaly['case_id']}` · {anomaly['anomaly_type']} · "
                f"{anomaly['parameter_family']} · {anomaly['message']}"
            )
    print()
    print("## Parameter Candidate Plan")
    if not report["parameter_candidate_plan"]:
        print("- 当前批量样盘未触发调参候选。")
    else:
        for candidate in report["parameter_candidate_plan"]:
            print(
                f"- `{candidate['candidate_id']}` · {candidate['recommended_action']} · "
                f"cases={', '.join(candidate.get('synthetic_cases') or []) or '—'}"
            )


if __name__ == "__main__":
    main()

