from __future__ import annotations

import os

from product.dream_store_contracts import DreamStore, DreamStoreConflict
from product.dream_store_memory import MemoryDreamStore
from product.dream_store_postgres import PostgresDreamStore


def build_dream_store() -> DreamStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresDreamStore(database_url) if database_url else MemoryDreamStore()


__all__ = [
    "DreamStore",
    "DreamStoreConflict",
    "MemoryDreamStore",
    "PostgresDreamStore",
    "build_dream_store",
]
