"use client";

type Props = {
  tag: string;
};

export function SnapshotBanner({ tag }: Props) {
  const safe = tag.trim();
  if (!safe) return null;

  return (
    <div className="mt-1 flex flex-wrap items-center gap-2">
      <span className="inline-flex items-center rounded-full border border-[#A855F7]/70 bg-fuchsia-500/10 px-2 py-0.5 text-[10px] text-fuchsia-200">
        Snapshot: {safe}
      </span>
    </div>
  );
}
