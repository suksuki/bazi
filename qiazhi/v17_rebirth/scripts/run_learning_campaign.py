from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.testing.learning_campaign import (
    LearningCampaignConfig,
    render_learning_campaign_markdown,
    run_learning_campaign,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the V17 automatic learning campaign.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--llm-review", action="store_true", help="Build an LLM review request package when findings exist.")
    parser.add_argument("--max-minutes", type=int, default=180, help="Maximum campaign budget in minutes.")
    parser.add_argument("--max-extended-cases", type=int, default=None, help="Optional cap for extended synthetic cases.")
    parser.add_argument("--write", type=str, default="", help="Optional output path for the rendered report.")
    args = parser.parse_args()

    report = run_learning_campaign(
        LearningCampaignConfig(
            max_duration_seconds=max(1, int(args.max_minutes)) * 60,
            request_llm_review=bool(args.llm_review),
            max_extended_cases=args.max_extended_cases,
        )
    )
    rendered = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        if args.json
        else render_learning_campaign_markdown(report)
    )
    if args.write:
        path = Path(args.write).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()

