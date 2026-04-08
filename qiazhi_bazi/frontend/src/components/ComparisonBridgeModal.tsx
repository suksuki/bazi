"use client";

type Props = {
  open: boolean;
  onClose: () => void;
  result?: Record<string, unknown> | null;
  currentGender?: string;
};

function pct(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value * 100)));
}

export function ComparisonBridgeModal({ open, onClose, result, currentGender = "" }: Props) {
  if (!open) return null;
  const maleWork = Number(result?.male_work_net || 0);
  const femaleWork = Number(result?.female_work_net || 0);
  const deltaWork = femaleWork - maleWork;
  const maleAbs = Number(result?.male_peak_abs || 0);
  const femaleAbs = Number(result?.female_peak_abs || 0);
  const maleBreak = Number(result?.male_path_break_score || 0);
  const femaleBreak = Number(result?.female_path_break_score || 0);
  const maleTheme = String(result?.male_theme_color || "#1A1A1A");
  const femaleTheme = String(result?.female_theme_color || "#2D4F1E");
  const summary = String(result?.summary || "");
  const socialHint = currentGender === "female"
    ? "坤造语义：官杀轴与关系压力需优先联审。"
    : "乾造语义：财星轴与资源压力需优先联审。";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-3xl rounded-xl border border-zinc-700 bg-zinc-950 p-4 shadow-2xl">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-100">乾坤 AB 对比桥</h3>
          <button type="button" onClick={onClose} className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800">
            关闭
          </button>
        </div>
        <div className="grid grid-cols-1 gap-2 text-xs md:grid-cols-2">
          <div className="rounded border border-zinc-700 p-2 text-zinc-200" style={{ background: `linear-gradient(135deg, ${maleTheme}66, #111827)` }}>
            男盘 Work_Net: {maleWork.toFixed(2)}
          </div>
          <div className="rounded border border-zinc-700 p-2 text-zinc-200" style={{ background: `linear-gradient(135deg, ${femaleTheme}66, #111827)` }}>
            女盘 Work_Net: {femaleWork.toFixed(2)}
          </div>
          <div className="rounded border border-zinc-700 p-2 text-zinc-200" style={{ background: `linear-gradient(135deg, ${maleTheme}40, #111827)` }}>
            男盘 Peak Abs: {maleAbs.toFixed(2)}
          </div>
          <div className="rounded border border-zinc-700 p-2 text-zinc-200" style={{ background: `linear-gradient(135deg, ${femaleTheme}40, #111827)` }}>
            女盘 Peak Abs: {femaleAbs.toFixed(2)}
          </div>
          <div className="rounded border border-zinc-700 bg-zinc-900 p-2 text-cyan-300 md:col-span-2">
            ΔWork_Net (女-男): {deltaWork >= 0 ? "+" : ""}{deltaWork.toFixed(2)}
          </div>
        </div>
        <div className="mt-3 space-y-2 rounded border border-zinc-700 bg-zinc-900 p-3">
          <p className="text-xs text-zinc-300">子午冲路径损毁度（红灯越高越危险）</p>
          <div>
            <div className="mb-1 flex items-center justify-between text-[11px] text-zinc-400">
              <span>男盘</span><span>{pct(maleBreak)}%</span>
            </div>
            <div className="h-2 rounded bg-zinc-800">
              <div className="h-full rounded bg-rose-500" style={{ width: `${pct(maleBreak)}%` }} />
            </div>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between text-[11px] text-zinc-400">
              <span>女盘</span><span>{pct(femaleBreak)}%</span>
            </div>
            <div className="h-2 rounded bg-zinc-800">
              <div className="h-full rounded bg-rose-500" style={{ width: `${pct(femaleBreak)}%` }} />
            </div>
          </div>
        </div>
        <p className="mt-3 rounded border border-fuchsia-500/30 bg-fuchsia-500/10 p-2 text-xs text-fuchsia-200">
          {summary || "已完成乾坤路径对比。"}
        </p>
        <p className="mt-2 text-[11px] text-zinc-400">{socialHint}</p>
      </div>
    </div>
  );
}
