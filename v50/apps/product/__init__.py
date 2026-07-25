from typing import Any


def create_product_app(*args: Any, **kwargs: Any):
    # Schema migration tooling imports product.database_schema. Keep package
    # initialization free of application startup and database version checks.
    from .app import create_product_app as build

    return build(*args, **kwargs)

__all__ = ["create_product_app"]
