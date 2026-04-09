import Link from "next/link";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto min-h-dvh w-full max-w-7xl px-3 py-3 md:px-6 md:py-6">
      <div className="overflow-hidden rounded-3xl border border-zinc-800/80 bg-zinc-950/70 shadow-2xl shadow-black/40">
        <div className="flex min-h-[86dvh]">
          <aside className="hidden w-72 border-r border-zinc-800/80 bg-gradient-to-b from-zinc-900 to-zinc-950 p-5 md:block">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-4">
              <h1 className="text-base font-semibold tracking-tight text-zinc-100">Qiazhi Admin</h1>
              <p className="mt-1 text-xs text-zinc-400">透明 · 可控 · 高信息密度</p>
            </div>
            <nav className="mt-5 space-y-2 text-sm">
              <Link
                href="/admin"
                className="block rounded-xl border border-zinc-800/80 bg-zinc-900/50 px-4 py-3 text-zinc-200 transition hover:border-zinc-700 hover:bg-zinc-800/60"
              >
                驾驶舱总览
              </Link>
              <Link
                href="/admin/settings"
                className="block rounded-xl border border-zinc-800/80 bg-zinc-900/50 px-4 py-3 text-zinc-200 transition hover:border-amber-500/40 hover:bg-zinc-800/60"
              >
                规则中心
              </Link>
              <Link
                href="/admin/plugins"
                className="block rounded-xl border border-zinc-800/80 bg-zinc-900/50 px-4 py-3 text-zinc-200 transition hover:border-cyan-500/40 hover:bg-zinc-800/60"
              >
                插件治理
              </Link>
              <Link
                href="/docs"
                className="block rounded-xl border border-zinc-800/80 bg-zinc-900/50 px-4 py-3 text-zinc-200 transition hover:border-violet-500/40 hover:bg-zinc-800/60"
              >
                理论库
              </Link>
            </nav>
            <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs text-zinc-400">
              用户端入口仍在 `/`，管理端专注监控、调试与审计。
            </div>
          </aside>

          <section className="flex-1 bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900/70">
            <header className="border-b border-zinc-800/80 px-4 py-3 md:px-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-zinc-500">Admin Console</p>
                  <p className="text-sm text-zinc-300">Infrastructure & Audit Workspace</p>
                  <div className="mt-2 flex flex-wrap gap-1 md:hidden">
                    <Link href="/admin" className="rounded-md border border-violet-500/40 bg-violet-500/10 px-2 py-1 text-[11px] text-violet-200">
                      驾驶舱
                    </Link>
                    <Link href="/admin/plugins" className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
                      插件
                    </Link>
                    <Link href="/admin/settings" className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
                      规则
                    </Link>
                    <Link href="/docs" className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
                      文档
                    </Link>
                  </div>
                </div>
                <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                  实时联调模式
                </div>
              </div>
            </header>
            <div className="p-4 md:p-6">{children}</div>
          </section>
        </div>
      </div>
    </main>
  );
}
