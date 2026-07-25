from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def audit_model_routing(*, registry_path: Path, env_path: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    environment = _read_env(env_path)
    rows = []
    for role, policy in (registry.get("roles") or {}).items():
        model_env = str(policy.get("model_env") or "")
        if not model_env:
            continue
        qualified_model = str(policy.get("model") or "")
        actual_model = environment.get(model_env, qualified_model)
        rows.append({
            "role": role,
            "model_env": model_env,
            "qualified_model": qualified_model,
            "actual_model": actual_model,
            "status": "matched" if actual_model == qualified_model else "drifted",
        })
    drift = [row for row in rows if row["status"] == "drifted"]
    return {
        "version": "deepbazi.model_routing_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not drift else "blocked",
        "registry_version": registry.get("version"),
        "env_file": str(env_path),
        "routes": rows,
        "drift": drift,
        "deployment_allowed": not drift,
        "note": "A candidate model must first pass the sealed cognitive benchmark and expert blind review, then update the registry explicitly.",
    }


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Block deployment when runtime model routing drifts from the qualified registry.")
    parser.add_argument("--registry", default=str(ROOT / "config/model_registry.json"))
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    report = audit_model_routing(registry_path=Path(args.registry), env_path=Path(args.env_file))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["deployment_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
