from __future__ import annotations

import os

from product.product_profile import (
    birth_input_from_profile,
    deduplicate_profile_archive as _deduplicate_profile_archive,
)
from product.product_store_contracts import ProductStore, ProductStoreError
from product.product_store_memory import MemoryProductStore
from product.product_store_postgres import PostgresProductStore


def build_product_store() -> ProductStore:
    database_url = os.environ.get("V50_DATABASE_URL", "").strip()
    if not database_url:
        return MemoryProductStore()
    return PostgresProductStore(database_url)


__all__ = [
    "MemoryProductStore",
    "PostgresProductStore",
    "ProductStore",
    "ProductStoreError",
    "_deduplicate_profile_archive",
    "birth_input_from_profile",
    "build_product_store",
]
