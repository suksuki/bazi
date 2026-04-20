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
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-lg font-bold">演化账本（因果轨迹）</h2>
          <p className="mt-1 text-[11px] text-zinc-500">追踪插件驱动下每一次十神位移与原因。</p>
        </div>
        <button onClick={() => void loadEvolution()} className="rounded-full border border-sky-500/30 bg-sky-950/20 px-3 py-1 text-xs text-sky-300">
          刷新
        </button>
      </div>

      <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950">
        <table className="w-full text-left text-xs">
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
                  <td className="max-w-[320px] overflow-hidden px-4 py-3 text-ellipsis whitespace-nowrap text-zinc-400">
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
