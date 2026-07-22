from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from product.app import create_product_app
from product.product_store import MemoryProductStore


ROOT = Path(__file__).resolve().parents[1]
EXPERIENCE = ROOT / "apps/product/static/experience"
RUNTIME_ROOTS = (
    EXPERIENCE / "active",
    EXPERIENCE / "internal-tools",
    EXPERIENCE / "shared",
)
REFERENCE_PATTERNS = (
    re.compile(r"(?:src|href)=[\"']([^\"']+)[\"']"),
    re.compile(r"\bfrom\s+[\"']([^\"']+)[\"']"),
    re.compile(r"\bfetch\(\s*[\"']([^\"']+)[\"']"),
    re.compile(r"url\(\s*[\"']?([^\"')]+)"),
)


def test_runtime_experience_surface_has_no_legacy_prototype_directory() -> None:
    assert not (EXPERIENCE / "prototypes").exists()
    assert (EXPERIENCE / "active/onecanvas-r1/index.html").is_file()
    assert (EXPERIENCE / "active/xiangfa-generation-v1/index.html").is_file()


def test_runtime_experience_relative_static_references_resolve() -> None:
    broken: list[str] = []
    for root in RUNTIME_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".css", ".html", ".js", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in REFERENCE_PATTERNS:
                for raw_ref in pattern.findall(text):
                    parsed = urlsplit(raw_ref)
                    if (
                        not parsed.path
                        or parsed.scheme
                        or parsed.path.startswith(("/", "#"))
                        or "${" in parsed.path
                    ):
                        continue
                    target = (path.parent / parsed.path).resolve()
                    if not target.exists():
                        broken.append(f"{path.relative_to(ROOT)} -> {raw_ref}")
    assert broken == []


def test_runtime_serves_only_the_converged_experience_paths() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    for path in (
        "/experience-static/active/onecanvas-r1/index.html",
        "/experience-static/active/xiangfa-generation-v1/index.html",
        "/experience-static/internal-tools/abu-says-mingli-s0-v12/index.html",
        "/experience-static/internal-tools/abu-motion-gallery-v1/index.html",
    ):
        assert client.get(path).status_code == 200
    assert (
        client.get("/experience-static/prototypes/mingli-onecanvas-c2ar/index.html").status_code
        == 404
    )


def test_abu_theater_has_a_stable_entry_and_legacy_bookmark_redirects() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    product_entry = client.get("/", follow_redirects=False)
    assert product_entry.status_code == 307
    assert product_entry.headers["location"] == "/abu-theater"
    app = client.get("/app", follow_redirects=False)
    assert app.status_code == 308
    assert app.headers["location"] == "/experience"

    stable = client.get("/abu-theater", follow_redirects=False)
    assert stable.status_code == 307
    assert stable.headers["location"] == (
        "/experience-static/internal-tools/abu-says-mingli-s0-v12/index.html"
    )

    legacy = client.get(
        "/experience-static/prototypes/abu-says-mingli-s0-v12/index.html",
        follow_redirects=False,
    )
    assert legacy.status_code == 308
    assert legacy.headers["location"] == "/abu-theater"
    assert client.get(legacy.headers["location"]).status_code == 200


def test_abu_theater_entry_can_continue_into_the_product_without_a_route_loop() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    theater = client.get(
        "/experience-static/internal-tools/abu-says-mingli-s0-v12/index.html"
    )

    assert theater.status_code == 200
    assert 'href="/experience" aria-label="进入 DeepBazi"' in theater.text
    assert 'class="scene-link" href="/experience">进入 DeepBazi</a>' in theater.text
    assert 'class="entry-system" href="/experience">直接进入 DeepBazi</a>' in theater.text
    assert 'class="finale-link" href="/experience">开始探索我的命局</a>' in theater.text
