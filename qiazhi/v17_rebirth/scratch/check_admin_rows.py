
import sys
import os
from pathlib import Path

# Fix python path
ROOT = Path("/Users/liujin/DEV/AIProjects/bazi/qiazhi")
sys.path.append(str(ROOT))

from v17_rebirth.backend.logic.plugin_discovery import registry_rows_for_admin

rows = registry_rows_for_admin()
for r in rows:
    if "sanhe" in r["plugin_id"]:
        print(f"Plugin: {r['plugin_id']}")
        print(f"Layer: {r['layer']}")
        print(f"Kind: {r['kind']}")
        print(f"Params: {list(r.get('declared_params', {}).keys())}")
