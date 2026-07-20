from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v50_lean_inventory.py"


def test_lean_inventory_emits_machine_outputs_without_mutating_runtime(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            str(ROOT / ".runtime" / "venv" / "bin" / "python"),
            str(SCRIPT),
            "--phase",
            "before",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    response = json.loads(result.stdout)
    assert response["phase"] == "before"

    expected = {
        "machine_inventory.json",
        "active_route_inventory.json",
        "asset_dedup_report.json",
        "dependency_graph.json",
        "dependency_graph.dot",
        "document_status_inventory.json",
        "test_ownership_matrix.json",
        "before_metrics.json",
        "LEAN_EXECUTION_SUMMARY.md",
    }
    assert expected == {path.name for path in tmp_path.iterdir()}

    inventory = json.loads((tmp_path / "machine_inventory.json").read_text(encoding="utf-8"))
    assert inventory["boundary"]["read_only_inventory"] is True
    assert inventory["boundary"]["candidate_unreferenced_is_deletion_authority"] is False
    assert inventory["classification_vocabulary"] == [
        "PRESERVE",
        "EXTRACT",
        "ADAPT",
        "REBUILD",
        "RETIRE",
    ]
    assert any(route["path"] == "/health" for route in inventory["routes"])
    assert any(row["id"] == "onecanvas-r1" for row in inventory["prototypes"])
