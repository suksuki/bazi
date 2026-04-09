import Link from "next/link";
import { EngineRoomPanel } from "@/features/admin/EngineRoomPanel";
import { WaterfallTopology } from "@/features/admin/components/WaterfallTopology";

export default function AdminHomePage() {
  return (
    <div className="space-y-5">
      <nav className="flex flex-wrap gap-2">
        <Link href="/admin" className="rounded-lg border border-zinc-700 bg-zinc-800/70 px-3 py-1.5 text-xs text-zinc-200">
          系统设置
        </Link>
        <Link href="/admin/plugins" className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-200">
          插件管理
        </Link>
      </nav>

      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/50 p-5">
        <h2 className="text-xl font-semibold tracking-tight">管理端总览 · 机房</h2>
        <p className="mt-1 text-sm text-zinc-400">物理参数与插件与主实验室共享同一会话状态（LabConfig）。</p>
      </div>

      <WaterfallTopology />

      <EngineRoomPanel />

      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Infrastructure</p>
          <h3 className="mt-2 text-base font-medium">DB + LLM Settings</h3>
          <p className="mt-2 text-sm text-zinc-400">连接检测、建表、Prompt 游乐场、多语言一致性测试。</p>
          <Link
            href="/admin/settings"
            className="mt-4 inline-flex rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-amber-400"
          >
            打开设置面板
          </Link>
        </article>
        <article className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Next</p>
          <h3 className="mt-2 text-base font-medium">逻辑插件准备</h3>
          <p className="mt-2 text-sm text-zinc-400">建议先接入“墓库开闭”插件，优先打通规则解释与决策回放。</p>
          <div className="mt-4 text-xs text-zinc-500">完成基础设施测试后即可进入插件联调。</div>
        </article>
      </div>
    </div>
  );
}
