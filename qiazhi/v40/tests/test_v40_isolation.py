from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v40_runtime_does_not_import_v30() -> None:
    runtime_files = [
        path
        for path in (ROOT / "v40").rglob("*.py")
        if "__pycache__" not in path.parts
    ]
    assert runtime_files
    offenders: list[str] = []
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        if "import v30" in text or "from v30" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_v40_config_boundaries_are_declared() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.v40.example").read_text(encoding="utf-8")
    spec = (ROOT / "docs" / "V40_SPEC.md").read_text(encoding="utf-8")

    assert "qiazhi_v40" in readme
    assert "v40_" in readme
    assert "v40:" in readme
    assert "V40_DATABASE_URL=postgresql://qiazhi_v40_app" in env_example
    assert "V40_REDIS_PREFIX=v40" in env_example
    assert "V40_RUNTIME_DIR=" in env_example
    assert "V40 runtime 禁止 import `v30.*`" in spec
