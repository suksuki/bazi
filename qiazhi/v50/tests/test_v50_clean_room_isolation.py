from __future__ import annotations

from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[1]
V50_CODE_ROOTS = [V50_ROOT / "apps", V50_ROOT / "packages"]


def test_v50_package_does_not_import_v30_or_v40() -> None:
    offenders: list[str] = []
    forbidden = [
        "import v30",
        "from v30",
        "import v40",
        "from v40",
    ]
    for root in V50_CODE_ROOTS:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in forbidden):
                offenders.append(str(path.relative_to(V50_ROOT)))

    assert offenders == []


def test_v50_schema_uses_only_v50_prefixed_tables() -> None:
    schema = (V50_ROOT / "deploy" / "postgres_v50_schema.sql").read_text(encoding="utf-8")
    executable_lines = "\n".join(
        line for line in schema.splitlines() if not line.strip().startswith("--")
    )
    assert "v50_schema_version" in schema
    assert "v40_" not in executable_lines.lower()
    assert "v30_" not in executable_lines.lower()
    assert "V40_DATABASE_URL" not in executable_lines
    assert "V30_DATABASE_URL" not in executable_lines
