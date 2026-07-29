import type { RuntimeAssetDelivery } from "../api";
import { BrandMark } from "./BrandMark";

export function RuntimeBoundaryScene({
  brand,
  message,
  status = "loading",
}: {
  brand?: RuntimeAssetDelivery;
  message: string;
  status?: "loading" | "error";
}) {
  return (
    <main className="dream-root v60-shell loading-shell">
      <BrandMark asset={brand} />
      {status === "loading" && (
        <div className="loading-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      )}
      <p className={status === "error" ? "runtime-error" : "loading-line"}>
        {message}
      </p>
    </main>
  );
}
