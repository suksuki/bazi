from __future__ import annotations

from abu_v60.media import media_library_summary
from abu_v60.provenance import canonical_json

if __name__ == "__main__":
    print(canonical_json(media_library_summary()))
