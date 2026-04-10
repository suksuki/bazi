"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";

export function SnapshotBanner() {
  const searchParams = useSearchParams();

  const tag = useMemo(() => {
    const raw = (searchParams?.get("tag") || "").trim();
    if (!raw) return "";
    return raw.replace(/[^\w\-:.]/g, "").slice(0, 48);
  }, [searchParams]);

  const identityChip = tag ? (
    <span className="inline-flex items-center rounded-full border border-[#A855F7]/70 bg-fuchsia-500/10 px-2 py-0.5 text-[10px] text-fuchsia-200">
      Snapshot: {tag}
    </span>
  ) : null;

  if (!identityChip) return null;

  return (
    <div className="mt-1 flex flex-wrap items-center gap-2">
      {identityChip}
    </div>
  );
}
