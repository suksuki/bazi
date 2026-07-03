from __future__ import annotations

import json
from pathlib import Path

from v30.dialogue_chain.contracts import BaziDialogueSession


class LocalJsonDialogueStore:
    def __init__(self, root: Path):
        self._root = root

    def save_session(self, session: BaziDialogueSession) -> None:
        path = self._session_path(session.reading_id, session.dialogue_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(session.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_session(self, reading_id: str, dialogue_id: str) -> BaziDialogueSession | None:
        path = self._session_path(reading_id, dialogue_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return BaziDialogueSession.model_validate(payload) if isinstance(payload, dict) else None

    def list_sessions(self, reading_id: str, *, limit: int = 20) -> list[BaziDialogueSession]:
        root = self._reading_path(reading_id)
        if not root.exists():
            return []
        rows: list[BaziDialogueSession] = []
        for path in sorted(root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                rows.append(BaziDialogueSession.model_validate(payload))
        rows.sort(key=lambda row: row.updated_at, reverse=True)
        return rows[: max(1, min(limit, 100))]

    def _reading_path(self, reading_id: str) -> Path:
        return self._root / _safe_file_id(reading_id)

    def _session_path(self, reading_id: str, dialogue_id: str) -> Path:
        return self._reading_path(reading_id) / f"{_safe_file_id(dialogue_id)}.json"


def build_dialogue_store(root: Path) -> LocalJsonDialogueStore:
    return LocalJsonDialogueStore(root)


def _safe_file_id(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")
