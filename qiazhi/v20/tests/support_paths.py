from __future__ import annotations

from pathlib import Path


V20_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = V20_ROOT.parent
FRONTEND_DIR = V20_ROOT / "frontend"


def v20_path(*parts: str) -> Path:
    return V20_ROOT.joinpath(*parts)


def read_v20_text(*parts: str) -> str:
    return v20_path(*parts).read_text(encoding="utf-8")


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def read_repo_text(*parts: str) -> str:
    return repo_path(*parts).read_text(encoding="utf-8")
