"use client";

import React from "react";

type ResumeAction = "confirm_conflict" | "adjust_energy" | "ignore_warning";

export type InterruptResumePayload = {
  action: ResumeAction;
  user_intention_id: string;
  wealth_weight_delta: number;
  /** V13.01：一键采纳 Inbox 最高分插件倾向（写入 Resume 反馈流水） */
  preferred_plugin_id?: string;
};

/** V12.93：reason_code → 简短说明（仅当 probe_query 为空时使用） */
function fallbackExplainReasonCode(reasonCode: string): string {
  const rc = String(reasonCode || "").trim();
  if (!rc) return "系统需要您确认本轮逻辑断点后再继续。";
  if (rc === "high_lock" || rc.includes("stagnation") || rc.includes("high_lock")) {
    return "当前盘面提示「高能闭锁」倾向：能量淤积而输出路径受阻，常与精神内耗或怀才不遇感相关，请确认是否与您的主观体验一致。";
  }
  if (rc === "marriage_clash" || rc.includes("harm") || rc.includes("寅巳")) {
    return "当前盘面提示婚姻/亲密关系轴存在结构性张力，请确认是否作为本轮推演的主轴。";
  }
  if (rc === "system_stress" || rc.includes("子午")) {
    return "当前盘面提示系统负载与对冲张力偏高，请确认您更关注事业、健康还是关系维度的取舍。";
  }
  if (rc.startsWith("M3_")) {
    return "系统检测到关键逻辑冲突临界态，请先确认冲突分支与处置策略，再继续终判。";
  }
  if (rc === "PROBE_PENDING" || rc === "INTERRUPT_PENDING") {
    return "系统检测到逻辑断点，请确认后再继续终判。";
  }
  return `系统需要您确认本轮逻辑断点（原因码：${rc}）后再继续。`;
}

export function InterruptOverlay(props: {
  interruptRequest: Record<string, unknown>;
  locked: boolean;
  /** V12.96：父级物理防抖（例如 Resume 后 2s 内禁止重复点击） */
  submitCooldown?: boolean;
  /** M3 高压：Decision Inbox 当前最高分插件，用于「AI 路由建议」一键确认 */
  m3ArbiterTopMatch?: { plugin_id: string; score: number } | null;
  onResume: (payload: InterruptResumePayload) => Promise<void>;
}) {
  const { interruptRequest, locked, submitCooldown = false, m3ArbiterTopMatch = null, onResume } = props;
  const controlsLocked = locked || submitCooldown;
  const [resumeIntention, setResumeIntention] = React.useState("seek_fame");
  const [resumeWealthDelta, setResumeWealthDelta] = React.useState(0);
  const [resumeBusy, setResumeBusy] = React.useState(false);
  const [resumeErr, setResumeErr] = React.useState("");

  const reasonCode = String((interruptRequest.reason_code as string) || "").trim() || "INTERRUPT_PENDING";
  const probeQuery = String((interruptRequest.probe_query as string) || "").trim();
  const bodyText = probeQuery || fallbackExplainReasonCode(reasonCode);

  const fireResume = async (action: ResumeAction, preferredPluginId?: string) => {
    setResumeErr("");
    setResumeBusy(true);
    try {
      await onResume({
        action,
        user_intention_id: resumeIntention,
        wealth_weight_delta: resumeWealthDelta,
        ...(preferredPluginId ? { preferred_plugin_id: preferredPluginId } : {}),
      });
    } catch (e) {
      setResumeErr(e instanceof Error ? e.message : "Resume 失败");
    } finally {
      setResumeBusy(false);
    }
  };

  return (
    <div className="mb-3 rounded-xl border-2 border-rose-500/55 bg-gradient-to-br from-rose-950/55 via-zinc-950/60 to-violet-950/35 p-3 shadow-[0_0_32px_rgba(244,63,94,0.12)]">
      <p className="text-sm font-semibold text-rose-50">强阻断 · Active Probing</p>
      <p className="mt-2 text-sm leading-relaxed text-rose-100/95">{bodyText}</p>
      <p className="mt-1 text-[11px] text-rose-200/75">
        中断码：<span className="font-mono text-rose-100/90">{reasonCode}</span>
        {String((interruptRequest.source as string) || "").trim() ? (
          <>
            {" · "}
            来源：<span className="font-mono">{String(interruptRequest.source)}</span>
          </>
        ) : null}
      </p>
      {reasonCode === "M3_HIGH_TENSION_PENDING" && m3ArbiterTopMatch?.plugin_id ? (
        <div className="mt-2 rounded-lg border border-cyan-700/50 bg-cyan-950/35 p-2">
          <p className="text-[11px] font-semibold text-cyan-100">AI 路由建议（按偏好 / match_score）</p>
          <p className="mt-1 text-[11px] text-cyan-50/95">
            建议优先按插件 <span className="font-mono text-cyan-200">{m3ArbiterTopMatch.plugin_id}</span> 处置（score≈
            {m3ArbiterTopMatch.score.toFixed(2)}）。可与下方意志选择一并提交。
          </p>
          <button
            type="button"
            disabled={controlsLocked || resumeBusy}
            onClick={() => void fireResume("confirm_conflict", m3ArbiterTopMatch.plugin_id)}
            className="mt-2 w-full rounded border border-cyan-500/55 bg-cyan-600/25 px-2 py-1.5 text-xs font-medium text-cyan-50 disabled:opacity-60"
          >
            一键采纳建议并确认冲突
          </button>
        </div>
      ) : null}
      <pre className="mt-2 max-h-28 overflow-auto rounded border border-rose-900/60 bg-zinc-950/75 p-2 text-[10px] leading-snug text-rose-100/85">
        {JSON.stringify(interruptRequest, null, 2)}
      </pre>
      <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-3">
        <select
          className="rounded border border-rose-700/60 bg-zinc-950/80 px-2 py-1 text-xs text-rose-100"
          value={resumeIntention}
          onChange={(e) => setResumeIntention(e.target.value)}
          disabled={controlsLocked || resumeBusy}
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
            disabled={controlsLocked || resumeBusy}
          />
          <span>{resumeWealthDelta.toFixed(1)}</span>
        </label>
        <span className="rounded border border-rose-700/60 bg-zinc-950/60 px-2 py-1 text-xs text-rose-100">
          {resumeBusy ? "提交中…" : controlsLocked ? "等待解锁…" : "可提交 Resume"}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3">
        <button
          type="button"
          disabled={controlsLocked || resumeBusy}
          onClick={() => void fireResume("confirm_conflict")}
          className="rounded border border-rose-500/60 bg-rose-600/25 px-2 py-1 text-xs text-rose-50 disabled:opacity-60"
        >
          {resumeBusy ? "处理中…" : "确认冲突"}
        </button>
        <button
          type="button"
          disabled={controlsLocked || resumeBusy}
          onClick={() => void fireResume("adjust_energy")}
          className="rounded border border-amber-500/60 bg-amber-600/25 px-2 py-1 text-xs text-amber-50 disabled:opacity-60"
        >
          {resumeBusy ? "处理中…" : "修正能量"}
        </button>
        <button
          type="button"
          disabled={controlsLocked || resumeBusy}
          onClick={() => void fireResume("ignore_warning")}
          className="rounded border border-zinc-500/60 bg-zinc-600/25 px-2 py-1 text-xs text-zinc-100 disabled:opacity-60"
        >
          {resumeBusy ? "处理中…" : "忽略警告"}
        </button>
      </div>
      {resumeErr ? <p className="mt-2 text-xs text-rose-200">{resumeErr}</p> : null}
    </div>
  );
}
