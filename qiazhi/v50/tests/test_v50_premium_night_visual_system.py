from fastapi.testclient import TestClient

from product.app import create_product_app
from product.product_store import MemoryProductStore


def test_public_ui_uses_premium_day_night_paper_visual_hierarchy() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    css = client.get("/styles.css").text

    assert 'content="#ffffff"' in html
    assert "20260717-thinking-chart-v1" in html
    assert "--night: #10231e;" in css
    assert "--warm-paper: #f4f1e9;" in css
    assert ".conversation-pane {\n  color: var(--night-ink);" in css
    assert "background: var(--night);" in css
    assert ".topbar {\n  height: var(--topbar);" in css
    assert "background: #fff;" in css
    assert ".task-canvas { background: var(--warm-paper); }" in css


def test_mobile_keeps_abu_companion_space_dark_and_reading_warm() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    css = client.get("/styles.css").text

    assert "@media (max-width: 960px)" in css
    assert ".conversation-pane { border-right: 0; background: var(--night); }" in css
    assert ".task-canvas { background: var(--warm-paper); }" in css
    assert ".abu-presence { min-height: 108px; background: var(--night-soft); }" in css
