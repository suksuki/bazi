
import sys
import os
from pathlib import Path

# Fix python path
ROOT = Path("/Users/liujin/DEV/AIProjects/bazi/qiazhi")
sys.path.append(str(ROOT))

from v17_rebirth.backend.logic.spec_validator import SpecValidator

results = SpecValidator.scan_all_plugins()
for r in results:
    if "op_status" in str(r.get("id") or ""):
        print(f"Found Plugin: {r.get('id')}")
        print(f"Valid: {r.get('valid')}")
        print(f"Params: {r.get('params')}")
        print(f"Errors: {r.get('errors')}")
