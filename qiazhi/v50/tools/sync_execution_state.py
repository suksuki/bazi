#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "config/v50_execution_state.yaml"
DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "docs/CURRENT_PRODUCT_BASELINE.md",
    ROOT / "docs/CURRENT_IMPLEMENTATION_ROADMAP.md",
)
START = "<!-- V50_EXECUTION_STATE:START -->"
END = "<!-- V50_EXECUTION_STATE:END -->"


def load_state() -> dict:
    return yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))


def render_state(state: dict) -> str:
    digest = hashlib.sha256(STATE_PATH.read_bytes()).hexdigest()[:12]
    gates = state["gates"]
    authorized = state["authorized_now"]
    next_slice = state["next_architecture_slice"]
    blocked = state["blocked"]
    receipts = state["receipts"]

    lines = [
        START,
        "## Machine-Synchronized Execution State",
        "",
        f"> Source: `config/v50_execution_state.yaml` · SHA-256 `{digest}` · Updated `{state['updated_at']}`",
        "",
        "```yaml",
        f"canonical_product_target: {state['product']['canonical_product_target']}",
        f"current_product_surface: {state['product']['current_product_surface']}",
        f"case_workspace_status: {state['product']['case_workspace_status']}",
        f"product_model: {state['product']['product_definition']}",
        f"mingli_world: {state['product']['world_definition']}",
        f"r1_human_product_gate: {gates['r1_human_product_gate']}",
        f"architecture_consolidation_gate: {gates['architecture_consolidation_gate']}",
        f"professional_blind_gate: {gates['professional_blind_gate']}",
        f"public_professional_release: {gates['public_professional_release']}",
        f"full_regression: {receipts['full_regression']}",
        "```",
        "",
        "Authorized now:",
        "",
    ]
    lines.extend(f"- `{item['id']}`: {item['scope']}" for item in authorized)
    lines.extend(
        [
            "",
            f"Next architecture slice: `{next_slice['id']}` after "
            + ", ".join(f"`{condition}`" for condition in next_slice["authorized_when"])
            + ".",
            "",
            "Blocked: " + ", ".join(f"`{item}`" for item in blocked) + ".",
            END,
        ]
    )
    return "\n".join(lines)


def replace_block(document: Path, block: str) -> bool:
    text = document.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise RuntimeError(f"execution_state_markers_missing:{document}")
    prefix, remainder = text.split(START, 1)
    _, suffix = remainder.split(END, 1)
    updated = prefix.rstrip() + "\n\n" + block + "\n\n" + suffix.lstrip()
    if updated == text:
        return False
    document.write_text(updated, encoding="utf-8")
    return True


def expected_document(document: Path, block: str) -> str:
    text = document.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise RuntimeError(f"execution_state_markers_missing:{document}")
    prefix, remainder = text.split(START, 1)
    _, suffix = remainder.split(END, 1)
    return prefix.rstrip() + "\n\n" + block + "\n\n" + suffix.lstrip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    block = render_state(load_state())
    if args.write:
        for document in DOCUMENTS:
            replace_block(document, block)
        return 0

    drifted = [str(path.relative_to(ROOT)) for path in DOCUMENTS if expected_document(path, block) != path.read_text(encoding="utf-8")]
    if drifted:
        raise SystemExit("execution_state_drift:" + ",".join(drifted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
