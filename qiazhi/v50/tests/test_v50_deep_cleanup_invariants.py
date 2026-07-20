from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_retired_product_labs_placeholders_and_asset_generations_stay_removed() -> None:
    retired = [
        "apps/admin",
        "apps/web",
        "packages/auth",
        "packages/i18n",
        "packages/ui",
        "apps/product/static/l5/abu-motion.html",
        "apps/product/static/l5/abu-motion.css",
        "apps/product/static/l5/abu-motion.js",
        "apps/product/static/l5/assets/abu/v1",
        "apps/product/static/l5/assets/abu/v2-handpainted",
        "apps/product/static/l5/assets/abu/v3-stylized",
        "scripts/v50_prepare_abu_asset.py",
    ]
    assert [path for path in retired if (ROOT / path).exists()] == []

    packs = {path.name for path in (ROOT / "apps/product/static/l5/assets/abu").iterdir() if path.is_dir()}
    assert packs == {
        "v4-video-derived",
        "v5-designer-welcome",
        "v6-designer-sleep",
        "v6-designer-play",
        "v7-designer-run-jump",
        "v8-designer-divination",
        "v9-designer-taoist-divination",
        "v9-designer-breakdance",
        "v10-opening-scene",
        "v11-designer-sad-tears",
        "v12-actor-pass",
    }


def test_current_product_code_does_not_reference_retired_cognition_objects() -> None:
    forbidden = (
        "core.brain",
        "core.product_mode",
        "core.reading",
        "core.expression",
        "CoreReadingBundle",
        "ChartStatePanel",
        "ModeRequestContext",
        "EvidenceLinkedReadingDraft",
    )
    offenders: list[str] = []
    for base in (ROOT / "apps", ROOT / "packages", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in forbidden):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_current_markdown_has_no_broken_repository_file_references() -> None:
    pattern = re.compile(
        r"(?<![\w/])((?:docs|data|reports|scripts|config|packages|apps)/"
        r"[A-Za-z0-9_./-]+(?:\.[A-Za-z0-9]+)?)"
    )
    broken: list[str] = []
    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        for reference in set(pattern.findall(path.read_text(encoding="utf-8"))):
            reference = reference.rstrip(".,:;)`")
            if "${" in reference or "*" in reference:
                continue
            if not (ROOT / reference).exists():
                broken.append(f"{path.relative_to(ROOT)} -> {reference}")
    assert broken == []
