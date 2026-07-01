from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:9040/v40/ui"
DEFAULT_OUTPUT_DIR = ROOT / ".runtime" / "visual_qa" / "phase50"
FORBIDDEN_VISIBLE_TERMS = [
    "/admin/v40",
    "provider",
    "model",
    "prompt",
    "acceptance",
    "policy",
    "debug",
    "telemetry",
    "TrainingLabelEvent",
    "LocalOverlay",
    "AnswerSignal",
    "HiddenAttributeUpdate",
    "ProbeAnswerResult",
]


@dataclass(frozen=True)
class Scenario:
    name: str
    width: int
    height: int
    role_header: str = ""
    expected_role_text: str = "普通用户"
    expect_lens_visible: bool = False
    mobile: bool = False


SCENARIOS = [
    Scenario(name="desktop_user", width=1440, height=960),
    Scenario(
        name="desktop_practitioner",
        width=1440,
        height=960,
        role_header="practitioner",
        expected_role_text="命理师视角",
        expect_lens_visible=True,
    ),
    Scenario(name="mobile_user", width=390, height=844, mobile=True),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V40 user UI visual QA with Playwright.")
    parser.add_argument("--url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(json.dumps({"passed": False, "error": f"Playwright is not installed: {exc}"}, ensure_ascii=False, indent=2))
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for scenario in SCENARIOS:
                results.append(_run_scenario(browser, args.url, output_dir, scenario))
        finally:
            browser.close()

    passed = all(not result["issues"] for result in results)
    report = {
        "version": "v40.phase50_user_ui_visual_qa_report.v1",
        "passed": passed,
        "base_url": args.url,
        "output_dir": str(output_dir),
        "scenarios": results,
        "boundary": "visual_qa_observes_user_surface_without_runtime_or_weight_mutation",
    }
    report_path = output_dir / "visual_qa_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def _run_scenario(browser: Any, url: str, output_dir: Path, scenario: Scenario) -> dict[str, Any]:
    headers = {}
    if scenario.role_header:
        headers["x-v40-user-role"] = scenario.role_header
    context = browser.new_context(
        viewport={"width": scenario.width, "height": scenario.height},
        device_scale_factor=2 if scenario.mobile else 1,
        is_mobile=scenario.mobile,
        has_touch=scenario.mobile,
        extra_http_headers=headers,
    )
    page = context.new_page()
    screenshot_path = output_dir / f"{scenario.name}.png"
    issues: list[str] = []
    try:
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("text=掐指一算", timeout=5000)
        page.wait_for_function(
            "(expected) => document.getElementById('roleChip')?.textContent?.includes(expected)",
            arg=scenario.expected_role_text,
            timeout=5000,
        )
        page.screenshot(path=str(screenshot_path), full_page=True)
        issues.extend(_check_required_elements(page))
        issues.extend(_check_visible_terms(page))
        issues.extend(_check_role_surface(page, scenario))
        issues.extend(_check_overflow(page, scenario))
    except Exception as exc:
        issues.append(f"scenario failed: {exc}")
    finally:
        context.close()
    return {
        "name": scenario.name,
        "viewport": {"width": scenario.width, "height": scenario.height},
        "role_header": scenario.role_header or "default",
        "screenshot": str(screenshot_path),
        "issues": issues,
    }


def _check_required_elements(page: Any) -> list[str]:
    issues = []
    required = {
        "#readingForm": "reading form missing",
        "#submitButton": "submit button missing",
        "#roleChip": "role chip missing",
        "#heroTitle": "hero title missing",
        "#followupQuestion": "follow-up input missing",
    }
    for selector, message in required.items():
        if not page.locator(selector).count():
            issues.append(message)
    return issues


def _check_visible_terms(page: Any) -> list[str]:
    text = page.locator("body").inner_text(timeout=5000)
    lower_text = text.lower()
    return [f"visible engineering term leaked: {term}" for term in FORBIDDEN_VISIBLE_TERMS if term.lower() in lower_text]


def _check_role_surface(page: Any, scenario: Scenario) -> list[str]:
    issues = []
    role_text = page.locator("#roleChip").inner_text(timeout=5000)
    if scenario.expected_role_text not in role_text:
        issues.append(f"expected role text {scenario.expected_role_text}, got {role_text}")
    lens_visible = page.locator("#lensDrawer").is_visible(timeout=5000)
    if scenario.expect_lens_visible and not lens_visible:
        issues.append("practitioner lens should be visible")
    if not scenario.expect_lens_visible and lens_visible:
        issues.append("practitioner lens should be hidden")
    return issues


def _check_overflow(page: Any, scenario: Scenario) -> list[str]:
    overflow = page.evaluate(
        """() => {
            const root = document.documentElement;
            const interactive = Array.from(document.querySelectorAll('button, input, select, textarea, .metric, .role-chip'));
            const bad = interactive
              .filter((el) => el.scrollWidth > el.clientWidth + 3)
              .slice(0, 8)
              .map((el) => ({
                tag: el.tagName.toLowerCase(),
                id: el.id || '',
                text: (el.textContent || el.value || '').trim().slice(0, 40),
                scrollWidth: el.scrollWidth,
                clientWidth: el.clientWidth
              }));
            return {scrollWidth: root.scrollWidth, innerWidth: window.innerWidth, bad};
        }"""
    )
    issues = []
    if scenario.mobile and overflow["scrollWidth"] > overflow["innerWidth"] + 4:
        issues.append(f"mobile horizontal overflow: {overflow['scrollWidth']} > {overflow['innerWidth']}")
    if overflow["bad"]:
        issues.append(f"text overflow in controls: {overflow['bad']}")
    return issues


if __name__ == "__main__":
    sys.exit(main())
