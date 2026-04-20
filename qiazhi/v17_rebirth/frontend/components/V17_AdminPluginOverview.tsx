"use client";

import { V17_ClassicalPatternAtlas } from "@/components/V17_ClassicalPatternAtlas";

type PluginLite = {
  plugin_id: string;
  causal_tier: number;
  display_name?: string;
  definition_text?: string;
};

type RuntimeLite = {
  fact_count?: number;
  status?: string;
};

type PluginOverviewRow = {
  plugin: PluginLite;
  runtime?: RuntimeLite;
};

type Props = {
  scannedPluginCount: number;
  hitPluginRows: PluginOverviewRow[];
  inboxPluginRows: PluginOverviewRow[];
  visiblePluginRows: PluginOverviewRow[];
  l2PatternCount: number;
  pluginCardTitle: (plugin: PluginLite) => string;
  runtimeStatusLabel: (status?: string) => string;
};

export function V17_AdminPluginOverview({
  scannedPluginCount,
  hitPluginRows,
  inboxPluginRows,
  visiblePluginRows,
  l2PatternCount,
  pluginCardTitle,
  runtimeStatusLabel,
}: Props) {
  return (
    <>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="text-[11px] font-semibold text-zinc-300">扫描层</div>
          <div className="mt-1 text-[10px] text-zinc-500">插件注册表中被扫描到的总量。</div>
          <div className="mt-3 text-2xl font-semibold text-zinc-100">{scannedPluginCount}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="text-[11px] font-semibold text-zinc-300">命中层</div>
          <div className="mt-1 text-[10px] text-zinc-500">本轮确实产出事实 / 物理位移建议 / 主张的插件。</div>
          <div className="mt-3 text-2xl font-semibold text-emerald-300">{hitPluginRows.length}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="text-[11px] font-semibold text-zinc-300">入队层</div>
          <div className="mt-1 text-[10px] text-zinc-500">已经进入手动、自动或上下文队列的插件。</div>
          <div className="mt-3 text-2xl font-semibold text-amber-300">{inboxPluginRows.length}</div>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 text-[11px] font-semibold text-zinc-300">扫描到的插件</div>
          <div className="space-y-1 text-[10px] text-zinc-500">
            {visiblePluginRows.slice(0, 12).map((row) => (
              <div key={`scan_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                <span className="text-zinc-700">L{row.plugin.causal_tier}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 text-[11px] font-semibold text-zinc-300">命中并产出事实</div>
          <div className="space-y-1 text-[10px] text-zinc-500">
            {hitPluginRows.slice(0, 12).map((row) => (
              <div key={`hit_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                <span>{Number(row.runtime?.fact_count || 0)} 事实</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 text-[11px] font-semibold text-zinc-300">已入队列表</div>
          <div className="space-y-1 text-[10px] text-zinc-500">
            {inboxPluginRows.slice(0, 12).map((row) => (
              <div key={`inbox_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                <span>{runtimeStatusLabel(row.runtime?.status)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-3">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-zinc-100">L2 古典格局系统</h3>
            <p className="mt-1 text-[11px] text-zinc-500">用于浏览古典格局定义、定义条件与系统挂接状态。</p>
          </div>
          <div className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] text-cyan-200">
            L2 插件 {l2PatternCount}
          </div>
        </div>
        <V17_ClassicalPatternAtlas
          title="L2 古典格局总览"
          subtitle="L2 古典格局全集目录、定义条件与系统挂接状态"
          compact
        />
      </div>
    </>
  );
}
