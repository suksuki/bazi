#!/usr/bin/env python3
"""将 physics_rules 出厂常量写入 L0 三表（幂等 Upsert）。

与主应用启动时一致：调用 `init_db()`（内含 `create_all`、`sync_l0_from_defaults` 等）。

用法：

  cd qiazhi_bazi/backend && DATABASE_URL=postgresql://... python3 scripts/migrate_l0_defaults.py
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    if not os.getenv("DATABASE_URL", "").strip():
        raise SystemExit("请设置环境变量 DATABASE_URL")

    from app.db.session import init_db

    init_db()
    print("[migrate_l0_defaults] init_db OK（已含 l0_element_registry / l0_branch_hidden_schema / l0_resonance_rules 同步）")


if __name__ == "__main__":
    main()
