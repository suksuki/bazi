from abu_v60.db import engine
from abu_v60.mingli.showcases import seed_mingli_showcases
from abu_v60.provenance import canonical_json

if __name__ == "__main__":
    print(canonical_json(seed_mingli_showcases(engine)))
