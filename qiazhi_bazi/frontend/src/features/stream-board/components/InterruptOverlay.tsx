"use client";

import React from "react";

type ResumeAction = "confirm_conflict" | "adjust_energy" | "ignore_warning";

export function InterruptOverlay(props: {
  interruptRequest: Record<string, unknown>;
  locked: boolean;
  onResume: (payload: { action: ResumeAction; user_intention_id: string; wealth_weight_delta: number }) => Promise<void>;
}) {
  const { interruptRequest, locked, onResume } = props;
  const [resumeIntention, setResumeIntention] = React.useState("seek_fame");
  const [resumeWealthDelta, setResumeWealthDelta] = React.useState(0);
  const [resumeBusy, setResumeBusy] = React.useState(false);
  const [resumeErr, setResumeErr] = React.useState("");

  const fireResume = async (action: ResumeAction) => {
    setResumeErr("");
    setResumeBusy(true);
    try {
      await onResume({
        action,
        user_intention_id: resumeIntention,
        wealth_weight_delta: resumeWealthDelta,
      });
    } catch (e) {
      setResumeErr(e instanceof Error ? e.message : "Resume 失败");
    } finally {
      setResumeBusy(false);
    }
  };

  return (
    <div className="mb-3 rounded-xl border border-rose-500/45 bg-rose-950/40 p-3">
      <p className="text-sm font-semibold text-rose-100">InterruptOverlay（阻塞）</p>
      <p className="mt-1 text-xs text-rose-200/90">
        探测到 [寅巳穿害] 导致婚姻宫能量损耗，是否需要注入补偿偏置？
        （中断码：{String((interruptRequest.reason_code as string) || "INTERRUPT_PENDING")}）
      </p>
      <pre className="mt-2 max-h-36 overflow-auto rounded border border-rose-900/70 bg-zinc-950/70 p-2 text-[11px] text-rose-100">
        {JSON.stringify(interruptRequest, null, 2)}
      </pre>
      <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-3">
        <select
          className="rounded border border-rose-700/60 bg-zinc-950/80 px-2 py-1 text-xs text-rose-100"
          value={resumeIntention}
          onChange={(e) => setResumeIntention(e.target.value)}
          disabled={locked || resumeBusy}
        >
          <option value="seek_stability">偏稳态（seek_stability）</option>
          <option value="seek_wealth">偏财轴（seek_wealth）</option>
          <option value="seek_fame">偏官誉（seek_fame）</option>
        </select>
        <label className="flex items-center gap-2 rounded border border-rose-700/60 bg-zinc-950/60 px-2 py-1 text-xs text-rose-100">
          财星权重偏移
          <input
            type="range"
            min={-1}
            max={1}
            step={0.1}
            value={resumeWealthDelta}
            onChange={(e) => setResumeWealthDelta(Number(e.target.value))}
            disabled={locked || resumeBusy}
          />
          <span>{resumeWealthDelta.toFixed(1)}</span>
        </label>
        <span className="rounded border border-rose-700/60 bg-zinc-950/60 px-2 py-1 text-xs text-rose-100">
          {locked ? "等待下一脉冲..." : "可执行 Resume"}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3">
        <button
          type="button"
          disabled={locked || resumeBusy}
          onClick={() => void fireResume("confirm_conflict")}
          className="rounded border border-rose-500/60 bg-rose-600/25 px-2 py-1 text-xs text-rose-50 disabled:opacity-60"
        >
          确认冲突
        </button>
        <button
          type="button"
          disabled={locked || resumeBusy}
          onClick={() => void fireResume("adjust_energy")}
          className="rounded border border-amber-500/60 bg-amber-600/25 px-2 py-1 text-xs text-amber-50 disabled:opacity-60"
        >
          修正能量
        </button>
        <button
          type="button"
          disabled={locked || resumeBusy}
          onClick={() => void fireResume("ignore_warning")}
          className="rounded border border-zinc-500/60 bg-zinc-600/25 px-2 py-1 text-xs text-zinc-100 disabled:opacity-60"
        >
          忽略警告
        </button>
      </div>
      {resumeErr ? <p className="mt-2 text-xs text-rose-200">{resumeErr}</p> : null}
    </div>
  );
}
