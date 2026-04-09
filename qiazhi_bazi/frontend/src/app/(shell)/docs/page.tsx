import Link from "next/link";

const DOCS = [
  { title: "物理核心", slug: "engine/PHYSICS_CORE" },
  { title: "逻辑宪法", slug: "engine/LOGIC_CONSTITUTION" },
  { title: "盲派百科", slug: "knowledge_base/BLIND_SCHOOL_ENCYCLOPEDIA" },
  { title: "盲派系统", slug: "knowledge_base/BLIND_SCHOOL_SYSTEM" },
];

export default function DocsIndexPage() {
  return (
    <main className="mx-auto min-h-dvh w-full max-w-4xl px-4 py-6">
      <h1 className="text-xl font-semibold">理论手册</h1>
      <p className="mt-1 text-sm text-zinc-400">用于 Admin 插件治理与审计溯源。</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {DOCS.map((doc) => (
          <Link key={doc.slug} href={`/docs/${doc.slug}`} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 text-sm text-zinc-200 hover:border-amber-500/40">
            {doc.title}
          </Link>
        ))}
      </div>
    </main>
  );
}

