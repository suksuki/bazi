"use client";

type EvolutionLogEntryLite = {
  id?: string;
  timestamp?: string;
  ten_god?: string;
  delta?: number;
  plugin_id?: string;
  step?: string;
  reason?: string;
};

type Props = {
  evolutionLogs: EvolutionLogEntryLite[];
  asNumber: (value: unknown, fallback?: number) => number;
  loadEvolution: () => Promise<void>;
};

export function V17_AdminEvolutionPanel({
  evolutionLogs,
  asNumber,
  loadEvolution,
}: Props) {
  return (
    <div className="min-w-0 space-y-4">
      <div className="flex flex-col gap-3 border-b border-zinc-800 pb-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-bold">演化账本（因果轨迹）</h2>
          <p className="mt-1 text-[11px] text-zinc-500">追踪插件驱动下每一次十神位移与原因。</p>
        </div>
        <button onClick={() => void loadEvolution()} className="w-full rounded-full border border-sky-500/30 bg-sky-950/20 px-3 py-1 text-xs text-sky-300 sm:w-auto">
          刷新
        </button>
      </div>

      <div className="grid gap-3 sm:hidden">
        {evolutionLogs.map((log) => {
          const evolutionTime = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "—";
          const deltaValue = asNumber(log.delta, 0);
          const deltaText = `${deltaValue > 0 ? "+" : ""}${deltaValue.toFixed(2)}`;
          return (
            <article key={log.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">{evolutionTime}</p>
                  <h3 className="mt-1 text-base font-semibold text-zinc-100">{log.ten_god || "—"}</h3>
                </div>
                <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${deltaValue > 0 ? "border-emerald-500/25 bg-emerald-950/20 text-emerald-300" : "border-rose-500/25 bg-rose-950/20 text-rose-300"}`}>
                  {deltaText}
                </span>
              </div>
              <div className="mt-3 rounded-xl border border-zinc-800 bg-black/25 p-2 text-[11px] leading-5 text-zinc-400">
                <p className="break-all text-sky-300">{log.plugin_id || "—"}</p>
                <p className="text-zinc-500">{log.step || "—"}</p>
                <p className="mt-2 break-words text-zinc-300">{log.reason || "—"}</p>
              </div>
            </article>
          );
        })}
        {!evolutionLogs.length ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5 text-sm text-zinc-500">
            暂无演化日志。
          </div>
        ) : null}
      </div>

      <div className="hidden overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-950 sm:block">
        <table className="min-w-[720px] w-full text-left text-xs">
          <thead className="bg-zinc-900/80 text-[10px] font-bold uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3">时间</th>
              <th className="px-4 py-3">十神</th>
              <th className="px-4 py-3">位移</th>
              <th className="px-4 py-3">插件 / 步骤</th>
              <th className="px-4 py-3">原因</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {evolutionLogs.map((log) => {
              const evolutionTime = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "—";
              const deltaValue = asNumber(log.delta, 0);
              const deltaText = `${deltaValue > 0 ? "+" : ""}${deltaValue.toFixed(2)}`;
              return (
                <tr key={log.id} className="hover:bg-zinc-800/20">
                  <td className="px-4 py-3 text-zinc-500">{evolutionTime}</td>
                  <td className="px-4 py-3 font-bold text-zinc-200">{log.ten_god}</td>
                  <td className={`px-4 py-3 font-mono ${deltaValue > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {deltaText}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sky-400">{log.plugin_id}</span>
                    <div className="text-[9px] text-zinc-600">{log.step}</div>
                  </td>
                  <td className="max-w-[320px] px-4 py-3 text-zinc-400">
                    {log.reason}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
