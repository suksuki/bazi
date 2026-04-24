"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  mode: "login" | "register";
  nextPath?: string;
};

function tone(active: boolean) {
  return active
    ? "border-cyan-400/40 bg-cyan-950/40 text-cyan-50"
    : "border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200";
}

export function V17_AuthScreen({ mode, nextPath }: Props) {
  const router = useRouter();
  const next = nextPath && nextPath.startsWith("/") ? nextPath : "/v17/oracle";
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (mode === "register" && password !== confirmPassword) {
      setError("两次密码输入不一致。");
      return;
    }
    setLoading(true);
    try {
      const payload =
        mode === "register"
          ? {
              username,
              display_name: displayName || username,
              email,
              password,
            }
          : {
              identifier: username,
              password,
            };
      const resp = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = (await resp.json().catch(() => ({}))) as Record<string, unknown>;
      if (!resp.ok) {
        setError(String(data.detail || "认证失败。"));
        return;
      }
      setMessage(mode === "register" ? "注册成功，正在进入系统。" : "登录成功，正在进入系统。");
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "认证失败。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_22%),linear-gradient(180deg,#09090b_0%,#111827_100%)] px-4 py-10 text-zinc-100">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[28px] border border-cyan-500/15 bg-[linear-gradient(145deg,rgba(17,24,39,0.92),rgba(9,9,11,0.98))] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.45)]">
          <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">掐指一算</div>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-zinc-50">登录系统</h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
            系统已经接入数据库账号体系。`admin` 拥有完整后台，`manager` 负责核心/辅助/观测页面与协作权限，`user`
            使用核心与辅助页面。
          </p>
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {[
              ["admin", "全量后台、数据库、LLM、学习与用户权限管理"],
              ["manager", "核心/辅助/观测页面，可维护普通账号与经理账号，不进入管理后台"],
              ["user", "核心判盘与辅助解释页面，隐藏观测页与后台"],
            ].map(([title, desc]) => (
              <div key={title} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">{title}</div>
                <p className="mt-3 text-sm leading-6 text-zinc-300">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[28px] border border-zinc-800 bg-[linear-gradient(180deg,rgba(24,24,27,0.8),rgba(9,9,11,0.96))] p-6 shadow-[0_24px_70px_rgba(0,0,0,0.32)]">
          <div className="flex gap-2">
            <Link href={next && next !== "/v17/oracle" ? `/login?next=${encodeURIComponent(next)}` : "/login"} className={`flex-1 rounded-xl border px-4 py-3 text-center text-sm transition ${tone(mode === "login")}`}>
              登录
            </Link>
            <Link href={next && next !== "/v17/oracle" ? `/register?next=${encodeURIComponent(next)}` : "/register"} className={`flex-1 rounded-xl border px-4 py-3 text-center text-sm transition ${tone(mode === "register")}`}>
              注册
            </Link>
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                {mode === "login" ? "用户名 / 邮箱" : "用户名"}
              </span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                placeholder={mode === "login" ? "输入用户名或邮箱" : "至少 3 个字符"}
                required
              />
            </label>

            {mode === "register" ? (
              <>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">显示名</span>
                  <input
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                    placeholder="可留空，默认使用用户名"
                  />
                </label>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">邮箱</span>
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                    placeholder="用于登录和识别，可留空"
                  />
                </label>
              </>
            ) : null}

            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">密码</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                placeholder="至少 8 个字符"
                required
              />
            </label>

            {mode === "register" ? (
              <label className="block">
                <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">确认密码</span>
                <input
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  type="password"
                  className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                  placeholder="再次输入密码"
                  required
                />
              </label>
            ) : null}

            {error ? <p className="rounded-xl border border-rose-500/25 bg-rose-950/25 px-4 py-3 text-sm text-rose-200">{error}</p> : null}
            {message ? <p className="rounded-xl border border-emerald-500/25 bg-emerald-950/25 px-4 py-3 text-sm text-emerald-200">{message}</p> : null}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl border border-cyan-400/40 bg-cyan-300 px-4 py-3 text-sm font-semibold text-black transition disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "处理中..." : mode === "login" ? "登录系统" : "注册并进入"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
