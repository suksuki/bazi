import { Suspense } from "react";
import { StreamBoard } from "@/components/StreamBoard";

export default function HomePage() {
  return (
    <Suspense fallback={<div className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4 text-sm text-zinc-500">加载中...</div>}>
      <StreamBoard />
    </Suspense>
  );
}
