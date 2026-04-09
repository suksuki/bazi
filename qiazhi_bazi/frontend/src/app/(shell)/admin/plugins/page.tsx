import Link from "next/link";
import { PluginManagementPanel } from "@/features/admin/components/PluginManagementPanel";

export default function AdminPluginsPage() {
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
        <h2 className="text-xl font-semibold tracking-tight">插件治理工作台</h2>
        <p className="mt-1 text-sm text-zinc-400">插件选拔、挂载、依赖巡检与话语权校准（移动端优先）。</p>
      </div>

      <PluginManagementPanel />
    </div>
  );
}

