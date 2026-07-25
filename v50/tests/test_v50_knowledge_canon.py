from __future__ import annotations

import json
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[1]
CANON_DIR = V50_ROOT / "data" / "knowledge" / "canon"


def test_v50_knowledge_cards_are_structured_and_traceable() -> None:
    cards = [
        json.loads(line)
        for line in (CANON_DIR / "knowledge_cards_v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(cards) >= 20
    for card in cards:
        assert card["id"]
        assert card["summary"]
        assert card["definition"]
        assert card["runtime_status"] in {"missing", "partial", "implemented", "tested"}
        assert card["recommended_runtime_priority"] in {"P0", "P1", "P2", "later"}
        assert len(card["sources"]) >= 3
        assert all(source["url"].startswith("https://") for source in card["sources"])
        assert card["notes"]


def test_v50_knowledge_canon_indexes_reference_existing_cards() -> None:
    cards = {
        json.loads(line)["id"]
        for line in (CANON_DIR / "knowledge_cards_v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    for filename in ["bazi_knowledge_canon_v1.json", "ziwei_knowledge_canon_v1.json"]:
        payload = json.loads((CANON_DIR / filename).read_text(encoding="utf-8"))
        for ids in payload["domains"].values():
            for card_id in ids:
                assert card_id in cards

