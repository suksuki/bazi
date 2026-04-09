import fs from "node:fs/promises";
import path from "node:path";
import Link from "next/link";

type Props = {
  params: Promise<{ slug: string[] }>;
};

export default async function DocViewerPage({ params }: Props) {
  const { slug } = await params;
  const docsRoot = path.resolve(process.cwd(), "..", "docs");
  const relative = `${slug.join("/")}.md`;
  const resolved = path.resolve(docsRoot, relative);
  const safe = resolved.startsWith(docsRoot);

  let content = "";
  let exists = false;
  if (safe) {
    try {
      content = await fs.readFile(resolved, "utf8");
      exists = true;
    } catch {
      exists = false;
    }
  }

  return (
    <main className="mx-auto min-h-dvh w-full max-w-5xl px-4 py-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">理论手册</h1>
          <p className="text-xs text-zinc-500">{slug.join("/")}</p>
        </div>
        <Link href="/docs" className="text-xs text-amber-300 underline-offset-2 hover:underline">
          返回手册目录
        </Link>
      </header>

      {!safe || !exists ? (
        <div className="rounded-xl border border-rose-600/40 bg-rose-500/10 p-4 text-sm text-rose-200">
          文档不存在或路径非法。
        </div>
      ) : (
        <pre className="overflow-auto rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 text-xs leading-relaxed text-zinc-200 whitespace-pre-wrap">
          {content}
        </pre>
      )}
    </main>
  );
}

