from abu_v60.db.engine import engine
from abu_v60.media import load_verified_media_catalog, sync_assets

if __name__ == "__main__":
    load_verified_media_catalog()
    count = sync_assets(engine)
    print(f"Verified media lineage and registered {count} V60 assets.")
