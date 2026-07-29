import type { RuntimeAssetDelivery } from "../api";

export function BrandMark({ asset }: { asset?: RuntimeAssetDelivery }) {
  return (
    <div className="brand-lockup" aria-label="阿布知命 V60">
      {asset ? (
        <img
          className="brand-logo"
          data-asset-ref={asset.asset_ref}
          src={asset.url}
          alt="AbuKnows 阿布知命"
        />
      ) : (
        <strong className="brand-text-fallback">AbuKnows · 阿布知命</strong>
      )}
      <small>V60 · 生命智能</small>
    </div>
  );
}
