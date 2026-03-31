import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-2xl font-light tracking-wide text-mist/90">
        Qiazhi-Bazi
      </h1>
      <p className="mt-2 text-sm text-mist/60">掐指八字 · 独立前端入口</p>
      <Link
        href="/qiazhi"
        className="mt-8 rounded border border-jade/60 px-6 py-3 text-jade transition hover:bg-jade/10"
      >
        进入墓库交互原型
      </Link>
    </main>
  );
}
