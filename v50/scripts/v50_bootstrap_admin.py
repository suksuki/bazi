from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps"))

from product.product_store import PostgresProductStore  # noqa: E402


DEFAULT_LOCAL_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or repair the single DeepBazi V50 admin account.")
    parser.add_argument("--database-url", default=os.environ.get("V50_DATABASE_URL", DEFAULT_LOCAL_DATABASE_URL))
    parser.add_argument("--email", default=os.environ.get("V50_ADMIN_EMAIL", ""))
    parser.add_argument("--display-name", default=os.environ.get("V50_ADMIN_DISPLAY_NAME", "DeepBazi Admin"))
    args = parser.parse_args()
    password = os.environ.get("V50_ADMIN_PASSWORD", "")
    if not args.email or not password:
        parser.error("V50_ADMIN_EMAIL and V50_ADMIN_PASSWORD are required")
    store = PostgresProductStore(args.database_url)
    account = store.ensure_admin_account(email=args.email, password=password, display_name=args.display_name)
    print(f"admin_ready email={account['email']} user_id={account['user_id']} storage={store.storage_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
